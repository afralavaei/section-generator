import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from modules import (
    MODULES, EPS, ZONES,
    ZONES_CORR_RIGHT, ZONES_CORR_LEFT,
    ZONES_CORR_RIGHT_NARROW, ZONES_CORR_LEFT_NARROW,
    _TABLE_COMPACT, _TABLE_SPACIOUS, _SHELF_CATEGORY,
    KITCHEN_ZONES, KITCHEN_ZONES_CORR_RIGHT, KITCHEN_ZONES_CORR_LEFT,
    KITCHEN_ZONES_SHELF_H2, KITCHEN_ZONES_SHELF_H3,
    KITCHEN_ZONES_CORR_RIGHT_SHELF_H2, KITCHEN_ZONES_CORR_LEFT_SHELF_H2,
    KITCHEN_ZONES_CORR_RIGHT_SHELF_H3, KITCHEN_ZONES_CORR_LEFT_SHELF_H3,
    LIVING_ZONES, LIVING_ZONES_CORR_RIGHT, LIVING_ZONES_CORR_LEFT,
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


def solve(W: int, H: int, seed: int, corridor: str = "none", corridor_w: int = 2,
          dining_style: str = "compact", roof_style: str = "any",
          section: str = "dining") -> Optional[List[dict]]:
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
        if corridor == "corridor_right":
            inner_W, x_offset = W - corridor_w, 0
            corr_mid = "corridor_right_spacious" if corridor_w == 4 else "corridor_right"
            placed: List[dict] = [{"module_id": corr_mid,
                                    "x_off": float(inner_W), "y_off": 0.0,
                                    "w": corridor_w, "h": H}]
            scenario_pool = [KITCHEN_ZONES_CORR_RIGHT]
            if H >= 8:
                scenario_pool.append(KITCHEN_ZONES_CORR_RIGHT_SHELF_H2)
            if H >= 9:
                scenario_pool.append(KITCHEN_ZONES_CORR_RIGHT_SHELF_H3)
        elif corridor == "corridor_left":
            inner_W, x_offset = W - corridor_w, corridor_w
            corr_mid = "corridor_left_spacious" if corridor_w == 4 else "corridor_left"
            placed = [{"module_id": corr_mid,
                       "x_off": 0.0, "y_off": 0.0,
                       "w": corridor_w, "h": H}]
            scenario_pool = [KITCHEN_ZONES_CORR_LEFT]
            if H >= 8:
                scenario_pool.append(KITCHEN_ZONES_CORR_LEFT_SHELF_H2)
            if H >= 9:
                scenario_pool.append(KITCHEN_ZONES_CORR_LEFT_SHELF_H3)
        else:
            inner_W, x_offset = W, 0
            placed = []
            scenario_pool = [KITCHEN_ZONES]
            if H >= 8:
                scenario_pool.append(KITCHEN_ZONES_SHELF_H2)
            if H >= 9:
                scenario_pool.append(KITCHEN_ZONES_SHELF_H3)
        active_zones = rng.choice(scenario_pool)

        reg_candidates: List[List[dict]] = []
        for zone in active_zones:
            options: List[dict] = []
            for xr in zone["x_rule"]:
                for yr in zone["y_rule"]:
                    res = resolve_zone_position(zone, inner_W, H, xr, yr)
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
                    if check_adjacency(placed):
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
                if check_adjacency(placed):
                    if bt_k(i + 1):
                        return True
                placed.pop()
            return False

        return placed if bt_k(0) else None

    if section == "living":
        if corridor == "corridor_right":
            inner_W, x_offset = W - corridor_w, 0
            corr_mid = "corridor_right_spacious" if corridor_w == 4 else "corridor_right"
            placed = [{"module_id": corr_mid,
                       "x_off": float(W - corridor_w), "y_off": 0.0, "w": corridor_w, "h": H}]
            active_zones = LIVING_ZONES_CORR_RIGHT
        elif corridor == "corridor_left":
            inner_W, x_offset = W - corridor_w, corridor_w
            corr_mid = "corridor_left_spacious" if corridor_w == 4 else "corridor_left"
            placed = [{"module_id": corr_mid,
                       "x_off": 0.0, "y_off": 0.0, "w": corridor_w, "h": H}]
            active_zones = LIVING_ZONES_CORR_LEFT
        else:
            inner_W, x_offset = W, 0
            placed = []
            active_zones = LIVING_ZONES
    else:
        _LEAN_RIGHT = ["corridor_right_lean_v1", "corridor_right_lean_v2", "corridor_right_lean_v3"]
        _LEAN_LEFT  = ["corridor_left_lean_v1",  "corridor_left_lean_v2",  "corridor_left_lean_v3"]

        # effective_roof controls shelf filtering; may differ from roof_style when
        # a lean-to corridor already provides the pitched element.
        effective_roof = roof_style

        if corridor == "corridor_right":
            inner_W, x_offset = W - corridor_w, 0
            if corridor_w == 4:
                corr_mid = "corridor_right_spacious"
            elif roof_style == "pitched":
                combo = rng.choice(["shelf_only", "corr_only", "both"])
                if combo == "corr_only":
                    corr_mid = rng.choice(_LEAN_RIGHT)
                    effective_roof = "any"
                elif combo == "both":
                    corr_mid = rng.choice(_LEAN_RIGHT)
                else:
                    corr_mid = "corridor_right"
            else:
                corr_mid = "corridor_right"
            placed = [{"module_id": corr_mid,
                       "x_off": float(W - corridor_w), "y_off": 0.0, "w": corridor_w, "h": H}]
            active_zones = ZONES_CORR_RIGHT if inner_W >= 6 else ZONES_CORR_RIGHT_NARROW
        elif corridor == "corridor_left":
            inner_W, x_offset = W - corridor_w, corridor_w
            if corridor_w == 4:
                corr_mid = "corridor_left_spacious"
            elif roof_style == "pitched":
                combo = rng.choice(["shelf_only", "corr_only", "both"])
                if combo == "corr_only":
                    corr_mid = rng.choice(_LEAN_LEFT)
                    effective_roof = "any"
                elif combo == "both":
                    corr_mid = rng.choice(_LEAN_LEFT)
                else:
                    corr_mid = "corridor_left"
            else:
                corr_mid = "corridor_left"
            placed = [{"module_id": corr_mid,
                       "x_off": 0.0, "y_off": 0.0, "w": corridor_w, "h": H}]
            active_zones = ZONES_CORR_LEFT if inner_W >= 6 else ZONES_CORR_LEFT_NARROW
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

        if effective_roof != "any":
            def _shelf_ok(mid: str) -> bool:
                base = mid.replace("_corr_r", "").replace("_corr_l", "")
                return _SHELF_CATEGORY.get(base, "any") == effective_roof
            active_zones = [
                {**z, "modules": [m for m in z["modules"] if _shelf_ok(m)]}
                if z.get("id") == "shelf" else z
                for z in active_zones
            ]

    reg_candidates: List[List[dict]] = []
    for zone in active_zones:
        options: List[dict] = []
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                res = resolve_zone_position(zone, inner_W, H, xr, yr)
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
                if check_adjacency(placed):
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
        ml, mr = MODULES[cl["module_id"]], MODULES[cr["module_id"]]
        return cl["h"] == cr["h"] and _seat_y(ml) == _seat_y(mr)

    def bt_reg(i: int) -> bool:
        if i == len(reg_candidates):
            return solve_gaps()
        for opt in reg_candidates[i]:
            placed.append(opt)
            if check_adjacency(placed) and _chairs_same_height():
                if bt_reg(i + 1):
                    return True
            placed.pop()
        return False

    return placed if bt_reg(0) else None
