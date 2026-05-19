"""
3D solver — mirrors solver.py's structure with the depth axis added.

Key differences vs. the 2D solver:
  • Adjacency has 6 face-pair cases (not 4): the original 4 plus front↔back.
  • Shared adjacency region is a 2D rectangle on a face (not a 1D interval).
  • Circuit vertices are 3-tuples (x, y, z).
  • Each placement carries (x_off, y_off, z_off, w, h, d).
  • Zones gain a z_rule; v1 always uses ``"full"`` so every zone spans depth D.
  • Gap-filling iterates the (W × H) column grid — each gap column is filled
    by a single 1×1×D extruded filler module (consistent with full-depth zones).

Reuses 1-D ``resolve_rule`` and the seat-y helper from solver.py unchanged.
"""
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import modules as _m2d
from modules import EPS
from modules3d import (
    MODULES_3D,
    ZONES_3D,
    ZONES_3D_CORR_RIGHT, ZONES_3D_CORR_LEFT,
    ZONES_3D_CORR_RIGHT_NARROW, ZONES_3D_CORR_LEFT_NARROW,
    _TABLE_COMPACT_3D, _TABLE_SPACIOUS_3D,
    _SHELF_CATEGORY,
    EXT_SUFFIX,
    FILLER_IDS_3D,
    get_segments_3d, get_ports_3d,
)
from solver import resolve_rule, _seat_y as _seat_y_2d


# ── Zone position resolver ────────────────────────────────────────────────────

def resolve_zone_position_3d(zone: dict, W: int, H: int, D: int,
                             x_rule: str, y_rule: str, z_rule: str) -> dict:
    cs, ce = resolve_rule(x_rule, W)
    rs, re = resolve_rule(y_rule, H)
    ds, de = resolve_rule(z_rule, D)
    return {
        "zone_id":   zone["id"],
        "col_start": cs, "col_end": ce,
        "row_start": rs, "row_end": re,
        "dep_start": ds, "dep_end": de,
        "w": ce - cs, "h": re - rs, "d": de - ds,
        "x_off": float(cs), "y_off": float(rs), "z_off": float(ds),
    }


# ── Port-set lookup on a shared face rectangle ────────────────────────────────

# For each face, the two in-plane axes used to compute the adjacency overlap.
# Convention matches FACES_3D: (axis_a_name, axis_b_name) where ranges
# (a_lo, a_hi, b_lo, b_hi) bound the shared rectangle.
_FACE_INPLANE_AXES = {
    "left":   ("y", "z"),
    "right":  ("y", "z"),
    "bottom": ("x", "z"),
    "top":    ("x", "z"),
    "front":  ("x", "y"),
    "back":   ("x", "y"),
}


def _ports_in_rect(mod: dict, face: str,
                   x_off: float, y_off: float, z_off: float,
                   a_lo: float, a_hi: float, b_lo: float, b_hi: float,
                   w: int, h: int, d: int) -> frozenset:
    """Section-coord ports on ``face`` lying inside the in-plane rectangle
    [a_lo, a_hi] × [b_lo, b_hi] (in the face's two in-plane axes)."""
    a_name, b_name = _FACE_INPLANE_AXES[face]
    pts = set()
    for px, py, pz in get_ports_3d(mod, w, h, d)[face]:
        sx, sy, sz = px + x_off, py + y_off, pz + z_off
        a = {"x": sx, "y": sy, "z": sz}[a_name]
        b = {"x": sx, "y": sy, "z": sz}[b_name]
        if a_lo - EPS <= a <= a_hi + EPS and b_lo - EPS <= b <= b_hi + EPS:
            pts.add((round(sx, 9), round(sy, 9), round(sz, 9)))
    return frozenset(pts)


# ── Adjacency ─────────────────────────────────────────────────────────────────

def check_adjacency_3d(placed: List[dict]) -> bool:
    """For every pair of placed modules sharing any face area, verify their
    ports on the shared rectangle are identical."""
    for i, a in enumerate(placed):
        ma = MODULES_3D[a["module_id"]]
        aw, ah, ad = a["w"], a["h"], a["d"]
        ax0, ay0, az0 = a["x_off"], a["y_off"], a["z_off"]
        for b in placed[i + 1:]:
            mb = MODULES_3D[b["module_id"]]
            bw, bh, bd = b["w"], b["h"], b["d"]
            bx0, by0, bz0 = b["x_off"], b["y_off"], b["z_off"]

            # right(a) ↔ left(b): shared rect in (y, z)
            if abs((ax0 + aw) - bx0) < EPS:
                y_lo, y_hi = max(ay0, by0), min(ay0 + ah, by0 + bh)
                z_lo, z_hi = max(az0, bz0), min(az0 + ad, bz0 + bd)
                if y_hi > y_lo and z_hi > z_lo:
                    if (_ports_in_rect(ma, "right", ax0, ay0, az0,
                                       y_lo, y_hi, z_lo, z_hi, aw, ah, ad) !=
                        _ports_in_rect(mb, "left",  bx0, by0, bz0,
                                       y_lo, y_hi, z_lo, z_hi, bw, bh, bd)):
                        return False
            # left(a) ↔ right(b)
            if abs((bx0 + bw) - ax0) < EPS:
                y_lo, y_hi = max(ay0, by0), min(ay0 + ah, by0 + bh)
                z_lo, z_hi = max(az0, bz0), min(az0 + ad, bz0 + bd)
                if y_hi > y_lo and z_hi > z_lo:
                    if (_ports_in_rect(mb, "right", bx0, by0, bz0,
                                       y_lo, y_hi, z_lo, z_hi, bw, bh, bd) !=
                        _ports_in_rect(ma, "left",  ax0, ay0, az0,
                                       y_lo, y_hi, z_lo, z_hi, aw, ah, ad)):
                        return False
            # top(a) ↔ bottom(b)
            if abs((ay0 + ah) - by0) < EPS:
                x_lo, x_hi = max(ax0, bx0), min(ax0 + aw, bx0 + bw)
                z_lo, z_hi = max(az0, bz0), min(az0 + ad, bz0 + bd)
                if x_hi > x_lo and z_hi > z_lo:
                    if (_ports_in_rect(ma, "top",    ax0, ay0, az0,
                                       x_lo, x_hi, z_lo, z_hi, aw, ah, ad) !=
                        _ports_in_rect(mb, "bottom", bx0, by0, bz0,
                                       x_lo, x_hi, z_lo, z_hi, bw, bh, bd)):
                        return False
            # bottom(a) ↔ top(b)
            if abs((by0 + bh) - ay0) < EPS:
                x_lo, x_hi = max(ax0, bx0), min(ax0 + aw, bx0 + bw)
                z_lo, z_hi = max(az0, bz0), min(az0 + ad, bz0 + bd)
                if x_hi > x_lo and z_hi > z_lo:
                    if (_ports_in_rect(mb, "top",    bx0, by0, bz0,
                                       x_lo, x_hi, z_lo, z_hi, bw, bh, bd) !=
                        _ports_in_rect(ma, "bottom", ax0, ay0, az0,
                                       x_lo, x_hi, z_lo, z_hi, aw, ah, ad)):
                        return False
            # back(a) ↔ front(b): shared rect in (x, y)
            if abs((az0 + ad) - bz0) < EPS:
                x_lo, x_hi = max(ax0, bx0), min(ax0 + aw, bx0 + bw)
                y_lo, y_hi = max(ay0, by0), min(ay0 + ah, by0 + bh)
                if x_hi > x_lo and y_hi > y_lo:
                    if (_ports_in_rect(ma, "back",  ax0, ay0, az0,
                                       x_lo, x_hi, y_lo, y_hi, aw, ah, ad) !=
                        _ports_in_rect(mb, "front", bx0, by0, bz0,
                                       x_lo, x_hi, y_lo, y_hi, bw, bh, bd)):
                        return False
            # front(a) ↔ back(b)
            if abs((bz0 + bd) - az0) < EPS:
                x_lo, x_hi = max(ax0, bx0), min(ax0 + aw, bx0 + bw)
                y_lo, y_hi = max(ay0, by0), min(ay0 + ah, by0 + bh)
                if x_hi > x_lo and y_hi > y_lo:
                    if (_ports_in_rect(mb, "back",  bx0, by0, bz0,
                                       x_lo, x_hi, y_lo, y_hi, bw, bh, bd) !=
                        _ports_in_rect(ma, "front", ax0, ay0, az0,
                                       x_lo, x_hi, y_lo, y_hi, aw, ah, ad)):
                        return False
    return True


# ── Closed-circuit ────────────────────────────────────────────────────────────

def check_circuit_3d(placed: List[dict]) -> bool:
    """Degree-1-free graph over all 3D segment endpoints in the assembled section."""
    degree: Dict[Tuple[float, float, float], int] = defaultdict(int)
    for p in placed:
        mod = MODULES_3D[p["module_id"]]
        xo, yo, zo = p["x_off"], p["y_off"], p["z_off"]
        for seg in get_segments_3d(mod, p["w"], p["h"], p["d"]):
            pts = [(round(x + xo, 9), round(y + yo, 9), round(z + zo, 9))
                   for x, y, z in seg]
            for k in range(len(pts) - 1):
                degree[pts[k]]     += 1
                degree[pts[k + 1]] += 1
    return all(deg != 1 for deg in degree.values())


# ── Gap columns (full-depth filler strips) ────────────────────────────────────

def _gap_columns_3d(placed_so_far: List[dict], W: int, H: int) -> List[Tuple[int, int]]:
    """Return (col, row) pairs not covered by any placed module. Phase 1 zones
    span the full depth, so each gap is a 1×1×D column."""
    covered: set = set()
    for p in placed_so_far:
        for col in range(int(p["x_off"]), int(p["x_off"]) + p["w"]):
            for row in range(int(p["y_off"]), int(p["y_off"]) + p["h"]):
                covered.add((col, row))
    return [(col, row) for row in range(H) for col in range(W)
            if (col, row) not in covered]


# ── Chair seat-height check (reuses 2D _seat_y on the source module) ──────────

def _chairs_same_height_3d(placed: List[dict]) -> bool:
    cl = next((p for p in placed
               if MODULES_3D[p["module_id"]]["zone"] == "chair_left"),  None)
    cr = next((p for p in placed
               if MODULES_3D[p["module_id"]]["zone"] == "chair_right"), None)
    if cl is None or cr is None:
        return True
    ml, mr = MODULES_3D[cl["module_id"]], MODULES_3D[cr["module_id"]]
    src_l_id = ml.get("source_2d_id")
    src_r_id = mr.get("source_2d_id")
    if src_l_id is None or src_r_id is None:
        return True  # native 3D modules — revisit at Phase 6
    return (cl["h"] == cr["h"]
            and _seat_y_2d(_m2d.MODULES[src_l_id])
                == _seat_y_2d(_m2d.MODULES[src_r_id]))


# ── Module candidate eligibility ──────────────────────────────────────────────

def _module_fits(mod3d: dict, w: int, h: int) -> bool:
    """Whether a 3D module variant is eligible at zone-resolved (w, h)."""
    return ((mod3d.get("scalable_w") or mod3d["w"] == w) and
            (mod3d.get("scalable_h") or mod3d["h"] == h))


# ── solve3d ───────────────────────────────────────────────────────────────────

def solve3d(W: int, H: int, D: int, seed: int,
            corridor: str = "none", corridor_w: int = 2,
            dining_style: str = "compact", roof_style: str = "any"
            ) -> Optional[List[dict]]:
    """Two-phase backtracking, same shape as solver.solve, with depth D added."""
    rng = random.Random(seed)

    if corridor == "corridor_right":
        inner_W, x_offset = W - corridor_w, 0
        placed: List[dict] = [{
            "module_id": "corridor_right" + EXT_SUFFIX,
            "x_off": float(W - corridor_w), "y_off": 0.0, "z_off": 0.0,
            "w": corridor_w, "h": H, "d": D,
        }]
        active_zones = ZONES_3D_CORR_RIGHT if inner_W >= 6 else ZONES_3D_CORR_RIGHT_NARROW
    elif corridor == "corridor_left":
        inner_W, x_offset = W - corridor_w, corridor_w
        placed = [{
            "module_id": "corridor_left" + EXT_SUFFIX,
            "x_off": 0.0, "y_off": 0.0, "z_off": 0.0,
            "w": corridor_w, "h": H, "d": D,
        }]
        active_zones = ZONES_3D_CORR_LEFT if inner_W >= 6 else ZONES_3D_CORR_LEFT_NARROW
    else:
        inner_W, x_offset = W, 0
        placed = []
        active_zones = ZONES_3D

    # Table-style filter
    table_mods = _TABLE_COMPACT_3D if dining_style == "compact" else _TABLE_SPACIOUS_3D
    active_zones = [
        {**z, "modules": table_mods} if z.get("id") == "table" else z
        for z in active_zones
    ]

    # Roof-style filter on the shelf zone
    if roof_style != "any":
        def _shelf_ok(mid: str) -> bool:
            base = (mid.replace(EXT_SUFFIX, "")
                       .replace("_corr_r", "")
                       .replace("_corr_l", ""))
            return _SHELF_CATEGORY.get(base, "any") == roof_style
        active_zones = [
            {**z, "modules": [m for m in z["modules"] if _shelf_ok(m)]}
            if z.get("id") == "shelf" else z
            for z in active_zones
        ]

    # Pre-compute candidate options per zone
    reg_candidates: List[List[dict]] = []
    for zone in active_zones:
        options: List[dict] = []
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                for zr in zone.get("z_rule", ["full"]):
                    res = resolve_zone_position_3d(zone, inner_W, H, D, xr, yr, zr)
                    w, h, d = res["w"], res["h"], res["d"]
                    for mid in zone["modules"]:
                        m = MODULES_3D[mid]
                        if _module_fits(m, w, h):
                            options.append({
                                "module_id": mid,
                                "x_off": res["x_off"] + x_offset,
                                "y_off": res["y_off"],
                                "z_off": res["z_off"],
                                "w": w, "h": h, "d": d,
                            })
        rng.shuffle(options)
        reg_candidates.append(options)

    # ── Gap fill pass (after all zones placed) ────────────────────────────────
    def solve_gaps() -> bool:
        gaps = _gap_columns_3d(placed, W, H)
        gap_candidates: List[List[dict]] = []
        for col, row in gaps:
            opts = [
                {"module_id": mid,
                 "x_off": float(col), "y_off": float(row), "z_off": 0.0,
                 "w": 1, "h": 1, "d": D}
                for mid in FILLER_IDS_3D
            ]
            rng.shuffle(opts)
            gap_candidates.append(opts)

        n_before = len(placed)

        def bt_gap(i: int) -> bool:
            if i == len(gap_candidates):
                return check_circuit_3d(placed)
            for opt in gap_candidates[i]:
                placed.append(opt)
                if check_adjacency_3d(placed):
                    if bt_gap(i + 1):
                        return True
                placed.pop()
            return False

        ok = bt_gap(0)
        if not ok:
            del placed[n_before:]
        return ok

    # ── Backtracking over named zones ─────────────────────────────────────────
    def bt_reg(i: int) -> bool:
        if i == len(reg_candidates):
            return solve_gaps()
        for opt in reg_candidates[i]:
            placed.append(opt)
            if check_adjacency_3d(placed) and _chairs_same_height_3d(placed):
                if bt_reg(i + 1):
                    return True
            placed.pop()
        return False

    return placed if bt_reg(0) else None
