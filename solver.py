import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from modules import (
    MODULES, EPS, ZONES,
    ZONES_FULL_ROOF_CORR_RIGHT, ZONES_FULL_ROOF_CORR_LEFT,
    ZONES_FULL_ROOF_CORR_RIGHT_1CHAIR, ZONES_FULL_ROOF_CORR_LEFT_1CHAIR,
    _TABLE_COMPACT, _TABLE_SPACIOUS, _SHELF_CATEGORY,
    KITCHEN_ZONES_INNER,
    LIVING_ZONES, LIVING_ZONES_CORR_RIGHT, LIVING_ZONES_CORR_LEFT,
    LIVING_ZONES_INNER, LIVING_ZONES_INNER_CORR_RIGHT, LIVING_ZONES_INNER_CORR_LEFT,
    _TABLE_COMPACT_LIVING, _TABLE_SPACIOUS_LIVING,
    LIVING_ZONES_SOFA_TV, LIVING_ZONES_SOFA_TV_CORR_RIGHT, LIVING_ZONES_SOFA_TV_INNER_CORR_RIGHT,
    BED_ZONES_INNER,
)


def get_segments(mod: dict, w: int, h: int = None) -> List:
    if "wh_segments_fn" in mod:
        return mod["wh_segments_fn"](w, h if h is not None else mod["h"])
    if "segments_fn" in mod:
        return mod["segments_fn"](w)
    if "h_segments_fn" in mod:
        return mod["h_segments_fn"](h if h is not None else mod["h"])
    return mod["segments"]


def get_ports(mod: dict, w: int, h: int = None) -> dict:
    if "wh_ports_fn" in mod:
        return mod["wh_ports_fn"](w, h if h is not None else mod["h"])
    if "ports_fn" in mod:
        return mod["ports_fn"](w)
    if "h_ports_fn" in mod:
        return mod["h_ports_fn"](h if h is not None else mod["h"])
    return mod["ports"]


def _seat_y(mod: dict) -> float:
    """Highest segment y-coord below the top port — the effective seat level."""
    segs = mod.get("segments", [])
    top_ys = {py for _, py in mod.get("ports", {}).get("top", [])}
    top_y = max(top_ys) if top_ys else float("inf")
    ys = [p[1] for seg in segs for p in seg if p[1] < top_y - EPS]
    return max(ys) if ys else 0.0


def resolve_rule(rule: str, dim: int) -> Tuple[int, int]:
    """Parse placement rules → (start, end).
    Supported: 'full', 'first N', 'last N', 'middle N', 'from N size M', 'skip last N'.
    """
    parts = rule.strip().split()
    if parts[0] == "full":
        return (0, dim)
    if parts[0] == "first":
        return (0, int(parts[1]))
    if parts[0] == "last":
        return (dim - int(parts[1]), dim)
    if parts[0] == "middle":
        n = int(parts[1])
        s = (dim - n) // 2
        return (s, s + n)
    if parts[0] == "from":
        start = int(parts[1])
        if len(parts) >= 5 and parts[2] == "to" and parts[3] == "last":
            # "from N to last M" → (N, dim-M)
            return (start, dim - int(parts[4]))
        # "from N size M" → absolute position
        return (start, start + int(parts[3]))
    if parts[0] == "skip":
        # "skip last N" → (0, dim-N)
        return (0, dim - int(parts[2]))
    raise ValueError(f"Unknown rule keyword: {parts[0]!r}")


def resolve_zone_position(zone: dict, W: int, H: int, x_rule: str, y_rule: str) -> dict:
    cs, ce = resolve_rule(x_rule, W)
    rs, re = resolve_rule(y_rule, H)
    return {
        "zone_id":   zone["id"],
        "col_start": cs, "col_end": ce,
        "row_start": rs, "row_end": re,
        "w": ce - cs,    "h": re - rs,
        "x_off": float(cs),
        "y_off": float(rs),
    }


def _ports_in_range(mod: dict, edge: str, x_off: float, y_off: float,
                    lo: float, hi: float, w: int = None, h: int = None) -> frozenset:
    """Return section-coord ports on `edge` whose position along the edge is in [lo, hi]."""
    pts = set()
    ports = get_ports(mod, w if w is not None else mod["w"], h if h is not None else mod["h"])
    for px, py in ports[edge]:
        sx, sy = px + x_off, py + y_off
        along = sx if edge in ("top", "bottom") else sy
        if lo - EPS <= along <= hi + EPS:
            pts.add((round(sx, 9), round(sy, 9)))
    return frozenset(pts)


def check_adjacency(placed: List[dict]) -> bool:
    """
    For every pair of placed modules that share a boundary segment,
    verify that their port sets on that segment are identical.
    """
    for i, a in enumerate(placed):
        ma = MODULES[a["module_id"]]
        aw, ah = a["w"], a["h"]
        for b in placed[i + 1:]:
            mb = MODULES[b["module_id"]]
            bw, bh = b["w"], b["h"]
            ax0, ay0 = a["x_off"], a["y_off"]
            bx0, by0 = b["x_off"], b["y_off"]

            if abs((ax0 + aw) - bx0) < EPS:
                y_lo = max(ay0, by0)
                y_hi = min(ay0 + ah, by0 + bh)
                if y_hi > y_lo:
                    if (_ports_in_range(ma, "right", ax0, ay0, y_lo, y_hi, aw, ah) !=
                            _ports_in_range(mb, "left",  bx0, by0, y_lo, y_hi, bw, bh)):
                        return False

            if abs((bx0 + bw) - ax0) < EPS:
                y_lo = max(ay0, by0)
                y_hi = min(ay0 + ah, by0 + bh)
                if y_hi > y_lo:
                    if (_ports_in_range(mb, "right", bx0, by0, y_lo, y_hi, bw, bh) !=
                            _ports_in_range(ma, "left",  ax0, ay0, y_lo, y_hi, aw, ah)):
                        return False

            if abs((ay0 + ah) - by0) < EPS:
                x_lo = max(ax0, bx0)
                x_hi = min(ax0 + aw, bx0 + bw)
                if x_hi > x_lo:
                    if (_ports_in_range(ma, "top",    ax0, ay0, x_lo, x_hi, aw, ah) !=
                            _ports_in_range(mb, "bottom", bx0, by0, x_lo, x_hi, bw, bh)):
                        return False

            if abs((by0 + bh) - ay0) < EPS:
                x_lo = max(ax0, bx0)
                x_hi = min(ax0 + aw, bx0 + bw)
                if x_hi > x_lo:
                    if (_ports_in_range(mb, "top",    bx0, by0, x_lo, x_hi, bw, bh) !=
                            _ports_in_range(ma, "bottom", ax0, ay0, x_lo, x_hi, aw, ah)):
                        return False

    return True


def check_last_adjacency(placed: List[dict]) -> bool:
    """Check only the last placed module against all previously placed ones. O(n) not O(n²)."""
    if len(placed) < 2:
        return True
    new = placed[-1]
    mn = MODULES[new["module_id"]]
    nw, nh = new["w"], new["h"]
    nx0, ny0 = new["x_off"], new["y_off"]

    for old in placed[:-1]:
        mo = MODULES[old["module_id"]]
        ow, oh = old["w"], old["h"]
        ox0, oy0 = old["x_off"], old["y_off"]

        if abs((ox0 + ow) - nx0) < EPS:
            y_lo = max(oy0, ny0); y_hi = min(oy0 + oh, ny0 + nh)
            if y_hi > y_lo:
                if (_ports_in_range(mo, "right", ox0, oy0, y_lo, y_hi, ow, oh) !=
                        _ports_in_range(mn, "left",  nx0, ny0, y_lo, y_hi, nw, nh)):
                    return False

        if abs((nx0 + nw) - ox0) < EPS:
            y_lo = max(oy0, ny0); y_hi = min(oy0 + oh, ny0 + nh)
            if y_hi > y_lo:
                if (_ports_in_range(mn, "right", nx0, ny0, y_lo, y_hi, nw, nh) !=
                        _ports_in_range(mo, "left",  ox0, oy0, y_lo, y_hi, ow, oh)):
                    return False

        if abs((oy0 + oh) - ny0) < EPS:
            x_lo = max(ox0, nx0); x_hi = min(ox0 + ow, nx0 + nw)
            if x_hi > x_lo:
                if (_ports_in_range(mo, "top",    ox0, oy0, x_lo, x_hi, ow, oh) !=
                        _ports_in_range(mn, "bottom", nx0, ny0, x_lo, x_hi, nw, nh)):
                    return False

        if abs((ny0 + nh) - oy0) < EPS:
            x_lo = max(ox0, nx0); x_hi = min(ox0 + ow, nx0 + nw)
            if x_hi > x_lo:
                if (_ports_in_range(mn, "top",    nx0, ny0, x_lo, x_hi, nw, nh) !=
                        _ports_in_range(mo, "bottom", ox0, oy0, x_lo, x_hi, ow, oh)):
                    return False

    return True


def check_circuit(placed: List[dict]) -> bool:
    """
    Build a degree map over all segment edge-vertices in the assembled section.
    Valid iff no vertex has degree 1 (no dangling ends).
    T-junctions (degree 3) are allowed.
    """
    degree: Dict[Tuple[float, float], int] = defaultdict(int)

    for p in placed:
        mod = MODULES[p["module_id"]]
        xo, yo = p["x_off"], p["y_off"]
        for seg in get_segments(mod, p["w"], p["h"]):
            pts = [(round(x + xo, 9), round(y + yo, 9)) for x, y in seg]
            for k in range(len(pts) - 1):
                degree[pts[k]]     += 1
                degree[pts[k + 1]] += 1

    return all(d != 1 for d in degree.values())


def _gap_cells(placed_so_far: List[dict], W: int, H: int) -> List[Tuple[int, int]]:
    """Return all (col, row) cells in the W×H grid not covered by any placed module."""
    covered: set = set()
    for p in placed_so_far:
        for col in range(int(p["x_off"]), int(p["x_off"]) + p["w"]):
            for row in range(int(p["y_off"]), int(p["y_off"]) + p["h"]):
                covered.add((col, row))
    return [(col, row) for row in range(H) for col in range(W)
            if (col, row) not in covered]


def _make_full_roof_shelf(shelf_mid: str, W: int, x_post: float) -> str:
    """
    Return a module_id for a full-W shelf with an extra support post at x=x_post.
    The post runs from y=0 to the shelf's lowest geometry crossing x_post, splitting
    any crossed segment so the circuit closes at the new bottom port.
    Result is cached in MODULES so repeated calls are free.
    """
    mod_id = f"_frs_{shelf_mid}_{W}_{round(x_post * 2)}"
    if mod_id in MODULES:
        return mod_id

    base = MODULES[shelf_mid]
    orig_segs = get_segments(base, W)
    orig_ports = get_ports(base, W)

    # Find the lowest y where a non-vertical segment crosses x = x_post
    best_y = None
    for seg in orig_segs:
        for i in range(len(seg) - 1):
            x1, y1 = seg[i]
            x2, y2 = seg[i + 1]
            if abs(x2 - x1) < 1e-9:
                continue  # vertical — skip
            if not (min(x1, x2) - 1e-9 <= x_post <= max(x1, x2) + 1e-9):
                continue
            t = (x_post - x1) / (x2 - x1)
            y_int = y1 + t * (y2 - y1)
            if best_y is None or y_int < best_y:
                best_y = y_int

    if best_y is None:
        return shelf_mid  # no crossing found — return unchanged

    best_y = round(best_y, 9)

    # Rebuild segments: insert (x_post, best_y) as split point in any segment
    # that crosses x_post at that y (only if not already a vertex there)
    new_segs = []
    for seg in orig_segs:
        new_poly = [seg[0]]
        for i in range(len(seg) - 1):
            x1, y1 = seg[i]
            x2, y2 = seg[i + 1]
            if (abs(x2 - x1) > 1e-9
                    and min(x1, x2) - 1e-9 <= x_post <= max(x1, x2) + 1e-9):
                t = (x_post - x1) / (x2 - x1)
                y_int = round(y1 + t * (y2 - y1), 9)
                if (abs(y_int - best_y) < 1e-9
                        and abs(x_post - x1) > 1e-9
                        and abs(x_post - x2) > 1e-9):
                    new_poly.append((x_post, best_y))
            new_poly.append(seg[i + 1])
        new_segs.append(new_poly)

    # Add vertical post from bottom edge to the crossing point
    new_segs.append([(x_post, 0.0), (x_post, best_y)])

    # Add bottom port at x_post so the filler chain above chair can terminate here
    new_bottom = list(orig_ports.get("bottom", [])) + [(x_post, 0.0)]
    new_ports = {**orig_ports, "bottom": new_bottom}

    new_mod = {
        **base,
        "id": mod_id,
        "w": W,
        "h": base["h"],
        "scalable": False,
        "h_scalable": False,
        "segments": new_segs,
        "ports": new_ports,
    }
    for key in ("segments_fn", "ports_fn", "wh_segments_fn", "wh_ports_fn",
                "h_segments_fn", "h_ports_fn"):
        new_mod.pop(key, None)
    MODULES[mod_id] = new_mod
    return mod_id


def solve(W: int, H: int, seed: int, corridor: str = "none", corridor_w: int = 2,
          dining_style: str = "compact", roof_style: str = "any",
          section: str = "dining",
          preferred_tags: list | None = None,
          living_combo: str = "full") -> Optional[List[dict]]:
    """
    Two-phase backtracking solver.
    Phase 1: place named zone modules (chair, table, shelf, …).
    Phase 2: fill every remaining cell with a 1×1 filler tile so the
             full W×H grid is covered and the closed-circuit rule is met.

    In pitched roof + corridor mode the solver randomly picks a combo so that
    at least one of the two elements is slanted:
      • shelf only  — standard corridor + pitched shelf
      • corridor only — lean-to corridor + any shelf
      • both         — lean-to corridor + pitched shelf
    """
    rng = random.Random(seed)
    filler_ids = [mid for mid, m in MODULES.items() if m["zone"] == "filler"]

    if section == "kitchen":
        # Corridor always on the right — same full-roof approach as dining.
        inner_W, x_offset = W - corridor_w, 0
        spacious_k = corridor_w >= 4

        shelf_pool = [mid for mid, m in MODULES.items()
                      if m["zone"] == "shelf"
                      and not mid.startswith("_frs_")
                      and not mid.endswith(("_corr_r", "_corr_l"))
                      and "narrow" not in mid]
        if roof_style != "any":
            shelf_pool = [m for m in shelf_pool if _SHELF_CATEGORY.get(m) == roof_style]
        rng.shuffle(shelf_pool)
        by_h_k: dict = {}
        for mid in shelf_pool:
            sh = MODULES[mid]["h"]
            if H - sh >= 4:
                by_h_k.setdefault(sh, []).append(mid)
        if not by_h_k:
            return None
        shelf_h = rng.choice(list(by_h_k.keys()))
        shelf_mid = rng.choice(by_h_k[shelf_h])
        if inner_W >= 6:
            shelf_mid = _make_full_roof_shelf(shelf_mid, W, float(inner_W) - 0.5)
        H_solve_k = H - shelf_h

        corr_mid_k = "corridor_right_spacious_short" if spacious_k else "corridor_right_short"

        _wide_k = rng.choice([True, False])
        _lower_k = "kitchen_lower_w3_h4_v3" if _wide_k else "kitchen_lower_w3_h4_v2"
        _upper_k = (["kitchen_upper_w2_h1_wide", "kitchen_upper_w2_h2_wide", "kitchen_upper_w2_h3_wide", "kitchen_upper_w2_h4_wide"]
                    if _wide_k else
                    ["kitchen_upper_w2_h1", "kitchen_upper_w2_h2", "kitchen_upper_w2_h3", "kitchen_upper_w2_h4"])

        def _pair_k(scenario):
            return [
                {**z, "modules": [_lower_k]}  if z["id"] == "lower_cabinet" else
                {**z, "modules": _upper_k}    if z["id"] == "upper_cabinet"  else
                z for z in scenario
                if z["id"] != "kitchen_wall"
            ]

        active_zones_k = _pair_k(KITCHEN_ZONES_INNER)
        placed: List[dict] = [
            {"module_id": corr_mid_k,
             "x_off": float(inner_W), "y_off": 0.0, "w": corridor_w, "h": H_solve_k},
            {"module_id": shelf_mid,
             "x_off": 0.0, "y_off": float(H_solve_k), "w": W, "h": shelf_h},
        ]

        reg_candidates: List[List[dict]] = []
        for zone in active_zones_k:
            options: List[dict] = []
            for xr in zone["x_rule"]:
                for yr in zone["y_rule"]:
                    res = resolve_zone_position(zone, inner_W, H_solve_k, xr, yr)
                    w, h = res["w"], res["h"]
                    for mid in zone["modules"]:
                        m = MODULES[mid]
                        if (m.get("scalable") or m["w"] == w) and (m.get("h_scalable") or m["h"] == h):
                            options.append({
                                "module_id": mid,
                                "x_off": res["x_off"] + x_offset,
                                "y_off": res["y_off"],
                                "w": w, "h": h,
                            })
            rng.shuffle(options)
            reg_candidates.append(options)

        def solve_gaps_k() -> bool:
            gaps = _gap_cells(placed, W, H)
            gap_candidates = [
                [{"module_id": mid, "x_off": float(col), "y_off": float(row), "w": 1, "h": 1}
                 for mid in filler_ids]
                for col, row in gaps
            ]
            for opts in gap_candidates:
                rng.shuffle(opts)
            n_before = len(placed)

            def bt_gap(i: int) -> bool:
                if i == len(gap_candidates):
                    return check_circuit(placed)
                for opt in gap_candidates[i]:
                    placed.append(opt)
                    if check_last_adjacency(placed):
                        if bt_gap(i + 1):
                            return True
                    placed.pop()
                return False

            ok = bt_gap(0)
            if not ok:
                del placed[n_before:]
            return ok

        def bt_k(i: int) -> bool:
            if i == len(reg_candidates):
                return solve_gaps_k()
            for opt in reg_candidates[i]:
                placed.append(opt)
                if check_last_adjacency(placed):
                    if bt_k(i + 1):
                        return True
                placed.pop()
            return False

        return placed if bt_k(0) else None

    if section == "bed":
        if corridor == "corridor_right":
            inner_W, x_offset = W - corridor_w, 0
        elif corridor == "corridor_left":
            inner_W, x_offset = W - corridor_w, corridor_w
        else:
            inner_W, x_offset = W, 0

        shelf_pool_b = [mid for mid, m in MODULES.items()
                        if m["zone"] == "shelf"
                        and not mid.startswith("_frs_")
                        and not mid.endswith(("_corr_r", "_corr_l"))
                        and "narrow" not in mid]
        if roof_style != "any":
            shelf_pool_b = [m for m in shelf_pool_b if _SHELF_CATEGORY.get(m) == roof_style]
        rng.shuffle(shelf_pool_b)
        by_h_b: dict = {}
        for mid in shelf_pool_b:
            sh = MODULES[mid]["h"]
            if H - sh >= 3:
                by_h_b.setdefault(sh, []).append(mid)
        if not by_h_b:
            return None
        shelf_h_b = rng.choice(list(by_h_b.keys()))
        shelf_mid_b = rng.choice(by_h_b[shelf_h_b])
        H_solve_b = H - shelf_h_b

        placed: List[dict] = [
            {"module_id": shelf_mid_b, "x_off": 0.0, "y_off": float(H_solve_b), "w": W, "h": shelf_h_b},
        ]
        if corridor == "corridor_right":
            cm_b = "corridor_right_spacious_short" if corridor_w >= 4 else "corridor_right_short"
            placed.insert(0, {"module_id": cm_b, "x_off": float(inner_W), "y_off": 0.0, "w": corridor_w, "h": H_solve_b})
        elif corridor == "corridor_left":
            cm_b = "corridor_left_spacious_short" if corridor_w >= 4 else "corridor_left_short"
            placed.insert(0, {"module_id": cm_b, "x_off": 0.0, "y_off": 0.0, "w": corridor_w, "h": H_solve_b})

        reg_candidates_b: List[List[dict]] = []
        for zone in BED_ZONES_INNER:
            options: List[dict] = []
            for xr in zone["x_rule"]:
                for yr in zone["y_rule"]:
                    res = resolve_zone_position(zone, inner_W, H_solve_b, xr, yr)
                    w, h = res["w"], res["h"]
                    for mid in zone["modules"]:
                        m = MODULES[mid]
                        if (m.get("scalable") or m["w"] == w) and (m.get("h_scalable") or m["h"] == h):
                            options.append({
                                "module_id": mid,
                                "x_off": res["x_off"] + x_offset,
                                "y_off": res["y_off"],
                                "w": w, "h": h,
                            })
            rng.shuffle(options)
            reg_candidates_b.append(options)

        def solve_gaps_b() -> bool:
            gaps = _gap_cells(placed, W, H)
            gap_candidates = [
                [{"module_id": mid, "x_off": float(col), "y_off": float(row), "w": 1, "h": 1}
                 for mid in filler_ids]
                for col, row in gaps
            ]
            for opts in gap_candidates:
                rng.shuffle(opts)
            n_before = len(placed)
            def bt_gap(i: int) -> bool:
                if i == len(gap_candidates):
                    return check_circuit(placed)
                for opt in gap_candidates[i]:
                    placed.append(opt)
                    if check_last_adjacency(placed):
                        if bt_gap(i + 1):
                            return True
                    placed.pop()
                return False
            ok = bt_gap(0)
            if not ok:
                del placed[n_before:]
            return ok

        def bt_b(i: int) -> bool:
            if i == len(reg_candidates_b):
                return solve_gaps_b()
            for opt in reg_candidates_b[i]:
                placed.append(opt)
                if check_last_adjacency(placed):
                    if bt_b(i + 1):
                        return True
                placed.pop()
            return False

        return placed if bt_b(0) else None

    if section == "bath":
        # Bath has no furniture zones — just shelf + optional corridor + fillers.
        if corridor == "corridor_right":
            inner_W, x_offset = W - corridor_w, 0
        elif corridor == "corridor_left":
            inner_W, x_offset = W - corridor_w, corridor_w
        else:
            inner_W, x_offset = W, 0

        shelf_pool_ba = [mid for mid, m in MODULES.items()
                         if m["zone"] == "shelf"
                         and not mid.startswith("_frs_")
                         and not mid.endswith(("_corr_r", "_corr_l"))
                         and "narrow" not in mid]
        if roof_style != "any":
            shelf_pool_ba = [m for m in shelf_pool_ba if _SHELF_CATEGORY.get(m) == roof_style]
        rng.shuffle(shelf_pool_ba)
        by_h_ba: dict = {}
        for mid in shelf_pool_ba:
            sh = MODULES[mid]["h"]
            if H - sh >= 3:
                by_h_ba.setdefault(sh, []).append(mid)
        if not by_h_ba:
            return None
        shelf_h_ba = rng.choice(list(by_h_ba.keys()))
        shelf_mid_ba = rng.choice(by_h_ba[shelf_h_ba])
        H_solve_ba = H - shelf_h_ba

        placed: List[dict] = [
            {"module_id": shelf_mid_ba, "x_off": 0.0, "y_off": float(H_solve_ba), "w": W, "h": shelf_h_ba},
        ]
        if corridor == "corridor_right":
            cm_ba = "corridor_right_spacious_short" if corridor_w >= 4 else "corridor_right_short"
            placed.insert(0, {"module_id": cm_ba, "x_off": float(inner_W), "y_off": 0.0,
                               "w": corridor_w, "h": H_solve_ba})
        elif corridor == "corridor_left":
            cm_ba = "corridor_left_spacious_short" if corridor_w >= 4 else "corridor_left_short"
            placed.insert(0, {"module_id": cm_ba, "x_off": 0.0, "y_off": 0.0,
                               "w": corridor_w, "h": H_solve_ba})

        def solve_gaps_ba() -> bool:
            gaps = _gap_cells(placed, W, H)
            gap_candidates = [
                [{"module_id": mid, "x_off": float(col), "y_off": float(row), "w": 1, "h": 1}
                 for mid in filler_ids]
                for col, row in gaps
            ]
            for opts in gap_candidates:
                rng.shuffle(opts)
            n_before = len(placed)
            def bt_gap(i: int) -> bool:
                if i == len(gap_candidates):
                    return check_circuit(placed)
                for opt in gap_candidates[i]:
                    placed.append(opt)
                    if check_last_adjacency(placed):
                        if bt_gap(i + 1):
                            return True
                    placed.pop()
                return False
            ok = bt_gap(0)
            if not ok:
                del placed[n_before:]
            return ok

        return placed if solve_gaps_ba() else None

    if section == "living":
        # ── shared shelf-filter helper ─────────────────────────────────────────
        def _filter_shelf(zones):
            if roof_style == "any":
                return list(zones)
            def _ok(mid):
                return _SHELF_CATEGORY.get(mid.replace("_corr_r","").replace("_corr_l",""), "any") == roof_style
            return [{**z, "modules": [m for m in z["modules"] if _ok(m)]}
                    if z.get("id") == "shelf" else z for z in zones]

        # ── shared corridor-path helper (full-roof + fallback) ─────────────────
        def _living_corridor_right(inner_z, full_z, add_post: bool = True):
            """Returns (placed, active_zones, inner_W) for corridor_right path."""
            nonlocal H
            iW = W - corridor_w
            shelf_pool = [mid for mid, m in MODULES.items()
                          if m["zone"] == "shelf"
                          and not mid.startswith("_frs_")
                          and not mid.endswith(("_corr_r", "_corr_l"))
                          and "narrow" not in mid]
            if roof_style != "any":
                sp = [m for m in shelf_pool if _SHELF_CATEGORY.get(m) == roof_style]
                if sp:
                    shelf_pool = sp
            rng.shuffle(shelf_pool)
            by_h: dict = {}
            for mid in shelf_pool:
                sh = MODULES[mid]["h"]
                if H - sh >= 3:
                    by_h.setdefault(sh, []).append(mid)
            if by_h:
                sh_h = rng.choice(list(by_h.keys()))
                sh_mid = rng.choice(by_h[sh_h])
                if add_post:
                    sh_mid = _make_full_roof_shelf(sh_mid, W, float(iW) - 0.5)
                H_s = H - sh_h
                spacious = corridor_w >= 4
                cm = "corridor_right_spacious_short" if spacious else "corridor_right_short"
                pl = [{"module_id": cm,  "x_off": float(iW), "y_off": 0.0, "w": corridor_w, "h": H_s},
                      {"module_id": sh_mid, "x_off": 0.0, "y_off": float(H_s), "w": W, "h": sh_h}]
                H = H_s
                return pl, _filter_shelf(inner_z), iW
            else:
                cm = "corridor_right_spacious" if corridor_w >= 4 else "corridor_right"
                pl = [{"module_id": cm, "x_off": float(W - corridor_w), "y_off": 0.0, "w": corridor_w, "h": H}]
                return pl, _filter_shelf(full_z), iW

        # ── sub-combo: sofa+tv ────────────────────────────────────────────────
        if living_combo == "sofa_tv":
            if corridor == "corridor_right":
                placed, active_zones, inner_W = _living_corridor_right(
                    LIVING_ZONES_SOFA_TV_INNER_CORR_RIGHT,
                    LIVING_ZONES_SOFA_TV_CORR_RIGHT)
                x_offset = 0
            else:
                inner_W, x_offset = W, 0
                placed = []
                active_zones = _filter_shelf(LIVING_ZONES_SOFA_TV)

        # ── full combo: sofa + table + tv_table ────────────────────────────────
        else:
            is_compact_l = dining_style == "compact"
            table_x_l    = "from 3 size 2" if is_compact_l else "from 4 size 2"
            table_mods_l = _TABLE_COMPACT_LIVING if is_compact_l else _TABLE_SPACIOUS_LIVING

            def _patch_l(zones):
                out = []
                for z in zones:
                    if z.get("id") == "table":
                        z = {**z, "x_rule": [table_x_l], "modules": table_mods_l}
                    out.append(z)
                return _filter_shelf(out)

            if corridor in ("corridor_right", "corridor_left"):
                inner_W = W - corridor_w
                x_offset = 0 if corridor == "corridor_right" else corridor_w
                shelf_pool_l = [mid for mid, m in MODULES.items()
                                if m["zone"] == "shelf"
                                and not mid.startswith("_frs_")
                                and not mid.endswith(("_corr_r", "_corr_l"))
                                and "narrow" not in mid]
                if roof_style != "any":
                    shelf_pool_l = [m for m in shelf_pool_l if _SHELF_CATEGORY.get(m) == roof_style]
                rng.shuffle(shelf_pool_l)
                by_h_l: dict = {}
                for mid in shelf_pool_l:
                    sh = MODULES[mid]["h"]
                    if H - sh >= 3:
                        by_h_l.setdefault(sh, []).append(mid)
                if by_h_l:
                    shelf_h = rng.choice(list(by_h_l.keys()))
                    shelf_mid_l = rng.choice(by_h_l[shelf_h])
                    x_post_l = float(inner_W) - 0.5 if corridor == "corridor_right" else float(corridor_w) + 0.5
                    shelf_mid_l = _make_full_roof_shelf(shelf_mid_l, W, x_post_l)
                    H_solve_l = H - shelf_h
                    spacious_l = corridor_w >= 4
                    if corridor == "corridor_right":
                        corr_mid = "corridor_right_spacious_short" if spacious_l else "corridor_right_short"
                        active_zones = _patch_l(LIVING_ZONES_INNER_CORR_RIGHT)
                    else:
                        corr_mid = "corridor_left_spacious_short" if spacious_l else "corridor_left_short"
                        active_zones = _patch_l(LIVING_ZONES_INNER_CORR_LEFT)
                    placed = [
                        {"module_id": corr_mid,
                         "x_off": float(W - corridor_w) if corridor == "corridor_right" else 0.0,
                         "y_off": 0.0, "w": corridor_w, "h": H_solve_l},
                        {"module_id": shelf_mid_l,
                         "x_off": 0.0, "y_off": float(H_solve_l), "w": W, "h": shelf_h},
                    ]
                    H = H_solve_l
                else:
                    if corridor == "corridor_right":
                        corr_mid = "corridor_right_spacious" if corridor_w >= 4 else "corridor_right"
                        placed = [{"module_id": corr_mid, "x_off": float(W - corridor_w),
                                   "y_off": 0.0, "w": corridor_w, "h": H}]
                        active_zones = _patch_l(LIVING_ZONES_CORR_RIGHT)
                    else:
                        corr_mid = "corridor_left_spacious" if corridor_w >= 4 else "corridor_left"
                        placed = [{"module_id": corr_mid, "x_off": 0.0,
                                   "y_off": 0.0, "w": corridor_w, "h": H}]
                        active_zones = _patch_l(LIVING_ZONES_CORR_LEFT)
            else:
                inner_W, x_offset = W, 0
                placed = []
                active_zones = _patch_l(LIVING_ZONES)
    else:
        effective_roof = roof_style

        if corridor == "corridor_right":
            inner_W, x_offset = W - corridor_w, 0
            placed = []
            active_zones = (ZONES_FULL_ROOF_CORR_RIGHT if inner_W >= 6
                            else ZONES_FULL_ROOF_CORR_RIGHT_1CHAIR)
        elif corridor == "corridor_left":
            inner_W, x_offset = W - corridor_w, corridor_w
            placed = []
            active_zones = (ZONES_FULL_ROOF_CORR_LEFT if inner_W >= 6
                            else ZONES_FULL_ROOF_CORR_LEFT_1CHAIR)
        else:
            inner_W, x_offset = W, 0
            placed = []
            active_zones = ZONES

    if section != "living":
        table_mods = _TABLE_COMPACT if dining_style == "compact" else _TABLE_SPACIOUS
        active_zones = [
            {**z, "modules": table_mods} if z.get("id") == "table" else z
            for z in active_zones
        ]

        if corridor != "none":
            spacious = corridor_w >= 4
            # Full-roof: pick shelf, place short corridor below it.
            shelf_pool = [mid for mid, m in MODULES.items()
                          if m["zone"] == "shelf"
                          and not mid.startswith("_frs_")
                          and not mid.endswith(("_corr_r", "_corr_l"))]
            if effective_roof != "any":
                shelf_pool = [m for m in shelf_pool if _SHELF_CATEGORY.get(m) == effective_roof]
            rng.shuffle(shelf_pool)
            by_h: dict = {}
            for mid in shelf_pool:
                sh = MODULES[mid]["h"]
                if H - sh >= 3:
                    by_h.setdefault(sh, []).append(mid)
            if not by_h:
                return None
            shelf_h = rng.choice(list(by_h.keys()))
            shelf_mid = rng.choice(by_h[shelf_h])
            if inner_W >= 6:
                x_post = float(inner_W) - 0.5 if corridor == "corridor_right" else float(corridor_w) + 0.5
                shelf_mid = _make_full_roof_shelf(shelf_mid, W, x_post)
            H_solve = H - shelf_h
            if corridor == "corridor_right":
                corr_mid = "corridor_right_spacious_short" if spacious else "corridor_right_short"
                placed[:] = [
                    {"module_id": corr_mid,
                     "x_off": float(W - corridor_w), "y_off": 0.0, "w": corridor_w, "h": H_solve},
                    {"module_id": shelf_mid,
                     "x_off": 0.0, "y_off": float(H_solve), "w": W, "h": shelf_h},
                ]
            else:
                corr_mid = "corridor_left_spacious_short" if spacious else "corridor_left_short"
                placed[:] = [
                    {"module_id": corr_mid,
                     "x_off": 0.0, "y_off": 0.0, "w": corridor_w, "h": H_solve},
                    {"module_id": shelf_mid,
                     "x_off": 0.0, "y_off": float(H_solve), "w": W, "h": shelf_h},
                ]
        else:
            if effective_roof != "any":
                def _shelf_ok(mid: str) -> bool:
                    base = mid.replace("_corr_r", "").replace("_corr_l", "")
                    return _SHELF_CATEGORY.get(base, "any") == effective_roof
                active_zones = [
                    {**z, "modules": [m for m in z["modules"] if _shelf_ok(m)]}
                    if z.get("id") == "shelf" else z
                    for z in active_zones
                ]
            H_solve = H
    else:
        H_solve = H

    _ZONE_TAG_MAP: dict = {
        "low_furniture":  {"chair_left": "h2", "chair_right": "h2", "table": "h2"},
        "tall_furniture": {"chair_left": "h3", "chair_right": "h3", "table": "h3"},
        "low_chairs":     {"chair_left": "h2", "chair_right": "h2"},
        "tall_chairs":    {"chair_left": "h3", "chair_right": "h3"},
        "low_table":      {"table": "h2"},
        "tall_table":     {"table": "h3"},
    }

    def _zone_require_tag(zone_id: str) -> str | None:
        for t in (preferred_tags or []):
            req = _ZONE_TAG_MAP.get(t, {}).get(zone_id)
            if req:
                return req
        return None

    def _build_options(zone: dict) -> List[dict]:
        opts: List[dict] = []
        zone_id    = zone.get("id", "")
        req_tag    = _zone_require_tag(zone_id)
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                res = resolve_zone_position(zone, inner_W, H_solve, xr, yr)
                w, h = res["w"], res["h"]
                for mid in zone["modules"]:
                    m = MODULES[mid]
                    if (m.get("scalable") or m["w"] == w) and (m.get("h_scalable") or m["h"] == h):
                        if req_tag and req_tag not in m.get("tags", []):
                            continue
                        opts.append({
                            "module_id": mid,
                            "x_off": res["x_off"] + x_offset,
                            "y_off": res["y_off"],
                            "w": w, "h": h,
                        })
        return opts

    def _build_options_unfiltered(zone: dict) -> List[dict]:
        opts: List[dict] = []
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                res = resolve_zone_position(zone, inner_W, H_solve, xr, yr)
                w, h = res["w"], res["h"]
                for mid in zone["modules"]:
                    m = MODULES[mid]
                    if (m.get("scalable") or m["w"] == w) and (m.get("h_scalable") or m["h"] == h):
                        opts.append({
                            "module_id": mid,
                            "x_off": res["x_off"] + x_offset,
                            "y_off": res["y_off"],
                            "w": w, "h": h,
                        })
        return opts

    reg_candidates: List[List[dict]] = []
    for zone in active_zones:
        options = _build_options(zone)
        if not options and _zone_require_tag(zone.get("id", "")):
            options = _build_options_unfiltered(zone)  # fallback
        rng.shuffle(options)
        reg_candidates.append(options)

    def solve_gaps() -> bool:
        gaps = _gap_cells(placed, W, H)
        gap_candidates = []
        for col, row in gaps:
            opts = [
                {"module_id": mid, "x_off": float(col), "y_off": float(row), "w": 1, "h": 1}
                for mid in filler_ids
            ]
            rng.shuffle(opts)
            gap_candidates.append(opts)

        n_before = len(placed)

        def bt_gap(i: int) -> bool:
            if i == len(gap_candidates):
                return check_circuit(placed)
            for opt in gap_candidates[i]:
                placed.append(opt)
                if check_last_adjacency(placed):
                    if bt_gap(i + 1):
                        return True
                placed.pop()
            return False

        ok = bt_gap(0)
        if not ok:
            del placed[n_before:]
        return ok

    def _chairs_same_height() -> bool:
        cl = next((p for p in placed if MODULES[p["module_id"]]["zone"] in ("chair_left", "sofa")),  None)
        cr = next((p for p in placed if MODULES[p["module_id"]]["zone"] in ("chair_right", "tv_table")), None)
        if cl is None or cr is None:
            return True
        # sofa+tv_table are distinct furniture types — no height/style match required
        if (MODULES[cl["module_id"]]["zone"] == "sofa"
                or MODULES[cr["module_id"]]["zone"] == "tv_table"):
            return True
        ml, mr = MODULES[cl["module_id"]], MODULES[cr["module_id"]]
        return (cl["h"] == cr["h"]
                and _seat_y(ml) == _seat_y(mr)
                and set(ml["tags"]) == set(mr["tags"]))

    def bt_reg(i: int) -> bool:
        if i == len(reg_candidates):
            return solve_gaps()
        for opt in reg_candidates[i]:
            placed.append(opt)
            if check_last_adjacency(placed) and _chairs_same_height():
                if bt_reg(i + 1):
                    return True
            placed.pop()
        return False

    return placed if bt_reg(0) else None
