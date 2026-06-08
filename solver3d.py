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

from modules import EPS
from modules3d import (
    MODULES_3D,
    ZONES_3D,
    ZONES_3D_CORR_RIGHT, ZONES_3D_CORR_LEFT,
    ZONES_3D_FULL_ROOF_CORR_RIGHT, ZONES_3D_FULL_ROOF_CORR_LEFT,
    ZONES_3D_FULL_ROOF_CORR_RIGHT_1CHAIR, ZONES_3D_FULL_ROOF_CORR_LEFT_1CHAIR,
    KITCHEN_ZONES_3D, KITCHEN_ZONES_SHELF_H2_3D, KITCHEN_ZONES_SHELF_H3_3D,
    FILLER_IDS_3D, _SHELF_CAT_3D,
    _TABLE_COMPACT_3D, _TABLE_SPACIOUS_3D,
    get_segments_3d, get_ports_3d,
    _lift2d, _ports_lift,
)
from solver import resolve_rule


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


# ── Chair seat-height check ───────────────────────────────────────────────────

def _chair_style_3d(mid: str) -> str:
    """Extract visual style class from a 3D chair module ID.
    Strips zone prefix (chair_left_/chair_right_), height class (h2_/h3_),
    and corridor suffix (_corr_r/_corr_l) so paired variants compare equal.
    Examples: 'chair_left_h3_v1' → 'v1', 'chair_right_h2_v3_corr_r' → 'v3'.
    """
    s = mid.replace("_corr_r", "").replace("_corr_l", "")
    for prefix in ("chair_left_h3_", "chair_left_h2_", "chair_left_",
                   "chair_right_h3_", "chair_right_h2_", "chair_right_"):
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


def _chairs_same_height_3d(placed: List[dict]) -> bool:
    cl = next((p for p in placed
               if MODULES_3D[p["module_id"]]["zone"] == "chair_left"),  None)
    cr = next((p for p in placed
               if MODULES_3D[p["module_id"]]["zone"] == "chair_right"), None)
    if cl is None or cr is None:
        return True
    return (cl["h"] == cr["h"]
            and _chair_style_3d(cl["module_id"]) == _chair_style_3d(cr["module_id"]))


# ── Module candidate eligibility ──────────────────────────────────────────────

def _module_fits(mod3d: dict, w: int, h: int, d: int = 3) -> bool:
    """Whether a 3D module variant is eligible at zone-resolved (w, h, d)."""
    d_ok = (mod3d.get("scalable_d") or "whd_segments_fn" in mod3d or mod3d.get("d", 3) == d)
    return ((mod3d.get("scalable_w") or mod3d["w"] == w) and
            (mod3d.get("scalable_h") or mod3d["h"] == h) and
            d_ok)


# ── Full-roof shelf injection (3D) ────────────────────────────────────────────

def _make_full_roof_shelf_3d(shelf_mid: str, W: int, x_post: float, D: int = 3) -> str:
    """
    3D equivalent of solver._make_full_roof_shelf.
    Inserts a vertical post at x=x_post in the 2D cross-section (at z=1 and z=D-1),
    splits crossed horizontal segments, and adds bottom ports at the post base.
    Result is cached in MODULES_3D.
    """
    mod_id = f"_frs3d_{shelf_mid}_{W}_{round(x_post * 2)}_{D}"
    if mod_id in MODULES_3D:
        return mod_id

    base = MODULES_3D[shelf_mid]
    orig_segs = get_segments_3d(base, W, base["h"], D)
    orig_ports = get_ports_3d(base, W, base["h"], D)

    # Reconstruct 2D cross-section segs by looking at z=0.5 plane (front face)
    z0 = 0.5
    segs_2d = []
    for seg in orig_segs:
        if all(abs(pt[2] - z0) < 1e-9 for pt in seg):
            segs_2d.append([(pt[0], pt[1]) for pt in seg])

    # Find lowest y where a non-vertical 2D segment crosses x=x_post
    best_y = None
    for seg in segs_2d:
        for i in range(len(seg) - 1):
            x1, y1 = seg[i]; x2, y2 = seg[i + 1]
            if abs(x2 - x1) < 1e-9:
                continue
            if not (min(x1, x2) - 1e-9 <= x_post <= max(x1, x2) + 1e-9):
                continue
            t = (x_post - x1) / (x2 - x1)
            y_int = y1 + t * (y2 - y1)
            if best_y is None or y_int < best_y:
                best_y = y_int

    if best_y is None:
        return shelf_mid

    best_y = round(best_y, 9)

    # Split crossing 2D segments
    new_segs_2d = []
    for seg in segs_2d:
        new_poly = [seg[0]]
        for i in range(len(seg) - 1):
            x1, y1 = seg[i]; x2, y2 = seg[i + 1]
            if (abs(x2 - x1) > 1e-9
                    and min(x1, x2) - 1e-9 <= x_post <= max(x1, x2) + 1e-9):
                t = (x_post - x1) / (x2 - x1)
                y_int = round(y1 + t * (y2 - y1), 9)
                if (abs(y_int - best_y) < 1e-9
                        and abs(x_post - x1) > 1e-9
                        and abs(x_post - x2) > 1e-9):
                    new_poly.append((x_post, best_y))
            new_poly.append(seg[i + 1])
        new_segs_2d.append(new_poly)

    new_segs_2d.append([(x_post, 0.0), (x_post, best_y)])

    new_segs_3d = _lift2d(new_segs_2d, d=D)
    # Keep any non-z0-plane segments from original (e.g. z-connectors) would be
    # regenerated by _lift2d — we only re-lift the 2D cross-section.

    z1 = float(D) - 0.5
    new_bottom = list(orig_ports.get("bottom", [])) + [
        (x_post, 0.0, z0), (x_post, 0.0, z1)
    ]
    new_ports = {**orig_ports, "bottom": new_bottom}

    new_mod = {
        **base,
        "id": mod_id,
        "w": W,
        "h": base["h"],
        "scalable_w": False,
        "scalable_h": False,
        "segments": new_segs_3d,
        "ports": new_ports,
    }
    for key in ("whd_segments_fn", "whd_ports_fn"):
        new_mod.pop(key, None)
    MODULES_3D[mod_id] = new_mod
    return mod_id


# ── solve3d ───────────────────────────────────────────────────────────────────

def solve3d(W: int, H: int, D: int, seed: int,
            corridor: str = "none", corridor_w: int = 2,
            dining_style: str = "compact", roof_style: str = "any",
            section: str = "dining",
            preferred_tags: list | None = None,
            zone_overrides: dict | None = None,
            ) -> Optional[List[dict]]:
    """Two-phase backtracking, same shape as solver.solve, with depth D added."""
    rng = random.Random(seed)

    if section == "kitchen":
        placed: List[dict] = []
        scenario_pool = [KITCHEN_ZONES_3D]
        if H >= 6:
            scenario_pool.append(KITCHEN_ZONES_SHELF_H2_3D)
        if H >= 7:
            scenario_pool.append(KITCHEN_ZONES_SHELF_H3_3D)
        if roof_style != "any":
            filtered = []
            for scenario in scenario_pool:
                flt = [{**z, "modules": [m for m in z["modules"]
                                          if _SHELF_CAT_3D.get(m, "any") == roof_style]}
                       if z.get("id") == "shelf" else z
                       for z in scenario]
                if all(z["modules"] for z in flt if z.get("id") == "shelf"):
                    filtered.append(flt)
            if filtered:
                scenario_pool = filtered
        active_zones_k = rng.choice(scenario_pool)

        reg_candidates_k: List[List[dict]] = []
        for zone in active_zones_k:
            options: List[dict] = []
            for xr in zone["x_rule"]:
                for yr in zone["y_rule"]:
                    for zr in zone.get("z_rule", ["full"]):
                        res = resolve_zone_position_3d(zone, W, H, D, xr, yr, zr)
                        w, h, d = res["w"], res["h"], res["d"]
                        for mid in zone["modules"]:
                            m = MODULES_3D[mid]
                            if _module_fits(m, w, h, d):
                                options.append({
                                    "module_id": mid,
                                    "x_off": res["x_off"], "y_off": res["y_off"],
                                    "z_off": res["z_off"],
                                    "w": w, "h": h, "d": d,
                                })
            rng.shuffle(options)
            reg_candidates_k.append(options)

        def solve_gaps_k() -> bool:
            gaps = _gap_columns_3d(placed, W, H)
            gap_candidates = []
            for col, row in gaps:
                opts = [{"module_id": mid, "x_off": float(col), "y_off": float(row),
                         "z_off": 0.0, "w": 1, "h": 1, "d": D}
                        for mid in FILLER_IDS_3D]
                rng.shuffle(opts)
                gap_candidates.append(opts)
            n_before = len(placed)

            def bt_gap_k(i: int) -> bool:
                if i == len(gap_candidates):
                    return check_circuit_3d(placed)
                for opt in gap_candidates[i]:
                    placed.append(opt)
                    if check_adjacency_3d(placed):
                        if bt_gap_k(i + 1):
                            return True
                    placed.pop()
                return False

            ok = bt_gap_k(0)
            if not ok:
                del placed[n_before:]
            return ok

        def bt_k(i: int) -> bool:
            if i == len(reg_candidates_k):
                return solve_gaps_k()
            for opt in reg_candidates_k[i]:
                placed.append(opt)
                if check_adjacency_3d(placed):
                    if bt_k(i + 1):
                        return True
                placed.pop()
            return False

        return placed if bt_k(0) else None

    if corridor in ("corridor_right", "corridor_left"):
        inner_W  = W - corridor_w
        x_offset = 0 if corridor == "corridor_right" else corridor_w
    else:
        inner_W  = W
        x_offset = 0

    if corridor in ("corridor_right", "corridor_left"):
        # Full-roof: pick shelf, place short corridor beneath it.
        shelf_pool = [mid for mid, m in MODULES_3D.items()
                      if m.get("zone") == "shelf"
                      and not mid.endswith(("_corr_r", "_corr_l"))
                      and "frs3d" not in mid]
        if roof_style != "any":
            shelf_pool = [m for m in shelf_pool if _SHELF_CAT_3D.get(m, "any") == roof_style]
        rng.shuffle(shelf_pool)
        by_h: dict = {}
        for mid in shelf_pool:
            sh = MODULES_3D[mid]["h"]
            if H - sh >= 3:
                by_h.setdefault(sh, []).append(mid)
        if not by_h:
            return None
        shelf_h = rng.choice(list(by_h.keys()))
        shelf_mid = rng.choice(by_h[shelf_h])
        if inner_W >= 6:
            x_post = float(inner_W) - 0.5 if corridor == "corridor_right" else float(corridor_w) + 0.5
            shelf_mid = _make_full_roof_shelf_3d(shelf_mid, W, x_post, D)
        H_solve = H - shelf_h
        if corridor == "corridor_right":
            placed: List[dict] = [
                {"module_id": "corridor_right_3d_short",
                 "x_off": float(inner_W), "y_off": 0.0, "z_off": 0.0,
                 "w": corridor_w, "h": H_solve, "d": D},
                {"module_id": shelf_mid,
                 "x_off": 0.0, "y_off": float(H_solve), "z_off": 0.0,
                 "w": W, "h": shelf_h, "d": D},
            ]
            active_zones = list(ZONES_3D_FULL_ROOF_CORR_RIGHT if inner_W >= 6
                                else ZONES_3D_FULL_ROOF_CORR_RIGHT_1CHAIR)
        else:
            placed: List[dict] = [
                {"module_id": "corridor_left_3d_short",
                 "x_off": 0.0, "y_off": 0.0, "z_off": 0.0,
                 "w": corridor_w, "h": H_solve, "d": D},
                {"module_id": shelf_mid,
                 "x_off": 0.0, "y_off": float(H_solve), "z_off": 0.0,
                 "w": W, "h": shelf_h, "d": D},
            ]
            active_zones = list(ZONES_3D_FULL_ROOF_CORR_LEFT if inner_W >= 6
                                else ZONES_3D_FULL_ROOF_CORR_LEFT_1CHAIR)
        H_inner = H_solve
    else:
        placed: List[dict] = []
        active_zones = list(ZONES_3D)
        H_inner = H

        # For no-corridor path, filter shelf by roof_style
        if roof_style != "any":
            active_zones = [
                {**z, "modules": [m for m in z["modules"]
                                   if _SHELF_CAT_3D.get(m, "any") == roof_style]}
                if z.get("id") == "shelf" else z
                for z in active_zones
            ]

    # Apply dining_style: compact uses narrow-top tables, spacious uses wide-top tables.
    table_mods_3d = _TABLE_COMPACT_3D if dining_style == "compact" else _TABLE_SPACIOUS_3D
    active_zones = [
        {**z, "modules": table_mods_3d} if z.get("id") == "table" else z
        for z in active_zones
    ]

    # Pre-compute candidate options per zone
    _ZONE_TAG_MAP: dict = {
        "low_furniture":  {"chair_left": "h2", "chair_right": "h2", "table": "h2"},
        "tall_furniture": {"chair_left": "h3", "chair_right": "h3", "table": "h3"},
        "low_chairs":     {"chair_left": "h2", "chair_right": "h2"},
        "tall_chairs":    {"chair_left": "h3", "chair_right": "h3"},
        "low_table":      {"table": "h2"},
        "tall_table":     {"table": "h3"},
    }

    def _zone_require_tag_3d(zone_id: str) -> str | None:
        for t in (preferred_tags or []):
            req = _ZONE_TAG_MAP.get(t, {}).get(zone_id)
            if req:
                return req
        return None

    def _build_options_3d(zone: dict) -> List[dict]:
        opts: List[dict] = []
        zone_id = zone.get("id", "")
        req_tag = _zone_require_tag_3d(zone_id)
        override = (zone_overrides or {}).get(zone_id)
        mods = [override] if override and override in MODULES_3D else zone["modules"]
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                for zr in zone.get("z_rule", ["full"]):
                    res = resolve_zone_position_3d(zone, inner_W, H_inner, D, xr, yr, zr)
                    w, h, d = res["w"], res["h"], res["d"]
                    for mid in mods:
                        m = MODULES_3D[mid]
                        if _module_fits(m, w, h, d):
                            if not override and req_tag and req_tag not in m.get("tags", []):
                                continue
                            opts.append({
                                "module_id": mid,
                                "x_off": res["x_off"] + x_offset,
                                "y_off": res["y_off"],
                                "z_off": res["z_off"],
                                "w": w, "h": h, "d": d,
                            })
        return opts

    def _build_options_3d_unfiltered(zone: dict) -> List[dict]:
        opts: List[dict] = []
        override = (zone_overrides or {}).get(zone.get("id", ""))
        mods = [override] if override and override in MODULES_3D else zone["modules"]
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                for zr in zone.get("z_rule", ["full"]):
                    res = resolve_zone_position_3d(zone, inner_W, H_inner, D, xr, yr, zr)
                    w, h, d = res["w"], res["h"], res["d"]
                    for mid in mods:
                        m = MODULES_3D[mid]
                        if _module_fits(m, w, h, d):
                            opts.append({
                                "module_id": mid,
                                "x_off": res["x_off"] + x_offset,
                                "y_off": res["y_off"],
                                "z_off": res["z_off"],
                                "w": w, "h": h, "d": d,
                            })
        return opts

    reg_candidates: List[List[dict]] = []
    for zone in active_zones:
        options = _build_options_3d(zone)
        if not options and _zone_require_tag_3d(zone.get("id", "")):
            options = _build_options_3d_unfiltered(zone)  # fallback
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
