"""
3D module library — auto-extrudes every 2D module from ``modules.py`` into a 3D
counterpart suffixed with ``__ext``.

Extrusion rule (see NOMADIC_ENGINE.md §19):

1. **Slice copies.** Copy each 2D polyline to z = 0.5, 1.5, …, d-0.5 — one
   copy per depth-cell midpoint.
2. **Depth-wires (interior only).** For every UNIQUE 2D vertex (x, y) that does
   NOT lie on a module face (i.e. ``x ∉ {0, w} AND y ∉ {0, h}``), connect
   consecutive slices with a wire ``[(x, y, k+0.5), (x, y, k+1.5)]`` for
   k=0..d-2. Boundary vertices are intentionally skipped — this preserves the
   2D closed-circuit self-enforcement (ports stay degree-1 inside the module
   and must be matched by neighbours).
3. **Ports.** Each 2D port on edge E becomes d 3D ports on face E at
   z=0.5, …, d-0.5. The front (z=0) and back (z=d) faces get no ports —
   extruded modules are "depth-opaque" along z.

The 3D library never mutates the 2D dicts. Geometry is materialized lazily via
``get_segments_3d`` / ``get_ports_3d`` so a single extruded module variant can
adapt to any zone-resolved (w, h, d).
"""
from typing import Dict, List, Tuple

import modules as _m2d
from modules import EPS

# Six 3D face names, in a stable order
FACES_3D: Tuple[str, ...] = ("left", "right", "bottom", "top", "front", "back")

# Suffix attached to every auto-extruded 3D module id
EXT_SUFFIX = "__ext"


# ── 2D materialization (helper, runs before extrusion) ────────────────────────

def _materialize_2d_segments(mod: dict, w: int, h: int) -> list:
    """Materialize a 2D module's segments for a given (w, h), handling all three
    scaling modes (wh_segments_fn / segments_fn / h_segments_fn / plain segments)."""
    if "wh_segments_fn" in mod:
        return mod["wh_segments_fn"](w, h)
    if "segments_fn" in mod:
        return mod["segments_fn"](w)
    if "h_segments_fn" in mod:
        return mod["h_segments_fn"](h)
    return mod["segments"]


def _materialize_2d_ports(mod: dict, w: int, h: int) -> dict:
    if "wh_ports_fn" in mod:
        return mod["wh_ports_fn"](w, h)
    if "ports_fn" in mod:
        return mod["ports_fn"](w)
    if "h_ports_fn" in mod:
        return mod["h_ports_fn"](h)
    return mod["ports"]


# ── Core extrusion ────────────────────────────────────────────────────────────

def _is_port_vertex_2d(x: float, y: float, ports2d: dict) -> bool:
    """True iff (x, y) is listed as a port on any of the four 2D edges.

    Port vertices skip the depth-wire — they must stay degree-1 inside the
    module so the closed-circuit rule self-enforces the section outer boundary.
    Non-port boundary tangents (e.g. the table's top-bar endpoints, a pitched
    roof's apex) are NOT skipped — they get depth-wires like interior vertices.
    """
    for pts in ports2d.values():
        for (px, py) in pts:
            if abs(x - px) < EPS and abs(y - py) < EPS:
                return True
    return False


def extrude_segments(seg2d: list, ports2d: dict, d: int) -> list:
    """Apply the 3D extrusion rule to 2D segments. See module docstring."""
    seg3d: list = []

    # Slice copies
    for k in range(d):
        z = k + 0.5
        for poly in seg2d:
            seg3d.append([(x, y, z) for (x, y) in poly])

    # Depth-wires — every unique 2D vertex that is NOT a declared port
    eligible: set = set()
    for poly in seg2d:
        for (x, y) in poly:
            if not _is_port_vertex_2d(x, y, ports2d):
                eligible.add((round(x, 9), round(y, 9)))
    for (x, y) in eligible:
        for k in range(d - 1):
            seg3d.append([(x, y, k + 0.5), (x, y, k + 1.5)])

    return seg3d


def extrude_ports(ports2d: dict, d: int) -> dict:
    """Apply the 3D extrusion rule to 2D ports → 3D ports (4 edges → 6 faces)."""
    out: Dict[str, list] = {face: [] for face in FACES_3D}
    for edge in ("left", "right", "bottom", "top"):
        for (px, py) in ports2d.get(edge, []):
            for k in range(d):
                z = k + 0.5
                out[edge].append((px, py, z))
    # front / back stay empty — extruded modules are depth-opaque
    return out


# ── MODULES_3D — auto-built from MODULES (2D) ─────────────────────────────────

def _make_extruded(mod2d: dict) -> dict:
    """Wrap a 2D module as a 3D module. Geometry materialized lazily."""
    return {
        "id":            mod2d["id"] + EXT_SUFFIX,
        "w":             mod2d["w"],
        "h":             mod2d["h"],
        "zone":          mod2d["zone"],
        "description":   mod2d.get("description", "") + " — auto-extruded.",
        "tags":          list(mod2d.get("tags", [])) + ["extruded"],
        "source_2d_id":  mod2d["id"],
        "scalable_w":    bool(mod2d.get("scalable",   False)),
        "scalable_h":    bool(mod2d.get("h_scalable", False)),
        "scalable_d":    True,
    }


MODULES_3D: Dict[str, dict] = {
    mid + EXT_SUFFIX: _make_extruded(m) for mid, m in _m2d.MODULES.items()
}


# ── Public materialization API ────────────────────────────────────────────────

def get_segments_3d(mod: dict, w: int, h: int, d: int) -> list:
    """3D segments for a placed module at (w, h, d)."""
    src = mod.get("source_2d_id")
    if src is not None:
        mod2d = _m2d.MODULES[src]
        seg2d   = _materialize_2d_segments(mod2d, w, h)
        ports2d = _materialize_2d_ports(mod2d, w, h)
        return extrude_segments(seg2d, ports2d, d)
    # Native 3D module (Phase 6+): same lambda pattern as 2D
    if "whd_segments_fn" in mod:
        return mod["whd_segments_fn"](w, h, d)
    return mod["segments"]


def get_ports_3d(mod: dict, w: int, h: int, d: int) -> dict:
    """3D ports for a placed module at (w, h, d)."""
    src = mod.get("source_2d_id")
    if src is not None:
        mod2d = _m2d.MODULES[src]
        ports2d = _materialize_2d_ports(mod2d, w, h)
        return extrude_ports(ports2d, d)
    if "whd_ports_fn" in mod:
        return mod["whd_ports_fn"](w, h, d)
    return mod["ports"]


# ── 3D Zone definitions ───────────────────────────────────────────────────────

def _zones_2d_to_3d(zones_2d: list) -> list:
    """Mirror a 2D zone list to 3D. Adds z_rule=['full']; rewrites module ids."""
    out = []
    for z in zones_2d:
        nz = dict(z)
        nz["z_rule"] = ["full"]
        nz["modules"] = [mid + EXT_SUFFIX for mid in z["modules"]]
        out.append(nz)
    return out


ZONES_3D                   = _zones_2d_to_3d(_m2d.ZONES)
ZONES_3D_CORR_RIGHT        = _zones_2d_to_3d(_m2d.ZONES_CORR_RIGHT)
ZONES_3D_CORR_LEFT         = _zones_2d_to_3d(_m2d.ZONES_CORR_LEFT)
ZONES_3D_CORR_RIGHT_NARROW = _zones_2d_to_3d(_m2d.ZONES_CORR_RIGHT_NARROW)
ZONES_3D_CORR_LEFT_NARROW  = _zones_2d_to_3d(_m2d.ZONES_CORR_LEFT_NARROW)


# ── Filter helpers — mirror modules.py ────────────────────────────────────────

_TABLE_COMPACT_3D  = [m + EXT_SUFFIX for m in _m2d._TABLE_COMPACT]
_TABLE_SPACIOUS_3D = [m + EXT_SUFFIX for m in _m2d._TABLE_SPACIOUS]

# Re-export the shelf category dict (keys are 2D ids without _corr_* or __ext)
_SHELF_CATEGORY = _m2d._SHELF_CATEGORY

FILLER_IDS_3D = [mid for mid, m in MODULES_3D.items() if m["zone"] == "filler"]


# ── Self-check (cheap; runs at import) ────────────────────────────────────────

def _self_check() -> None:
    """Sanity-check the extrusion at module-load time. Logs nothing on success."""
    # Round-trip: the 0.5-slice of an extruded module must equal the 2D source.
    mid = "chair_left_h3_v1"
    mod3d = MODULES_3D[mid + EXT_SUFFIX]
    src = _m2d.MODULES[mid]
    w, h, d = src["w"], src["h"], 2
    seg2d   = _materialize_2d_segments(src, w, h)
    seg3d   = get_segments_3d(mod3d, w, h, d)
    # The first len(seg2d) polylines should be the z=0.5 slice copy
    front_slice = seg3d[:len(seg2d)]
    for poly3d, poly2d in zip(front_slice, seg2d):
        assert len(poly3d) == len(poly2d), "slice polyline length mismatch"
        for (x3, y3, z3), (x2, y2) in zip(poly3d, poly2d):
            assert abs(x3 - x2) < EPS, "x mismatch in z=0.5 slice"
            assert abs(y3 - y2) < EPS, "y mismatch in z=0.5 slice"
            assert abs(z3 - 0.5) < EPS, "z != 0.5 in front slice"
    # Port-count formula upper bound: 2(wh + hd + wd)
    ports3d = get_ports_3d(mod3d, w, h, d)
    total = sum(len(v) for v in ports3d.values())
    upper = 2 * (w*h + h*d + w*d)
    assert total <= upper, f"port count {total} exceeds upper bound {upper}"


_self_check()
