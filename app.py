import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import streamlit as st

# ── Constants ─────────────────────────────────────────────────────────────────
EPS = 1e-9
LINE_COLOR  = "#cc2200"
PORT_COLOR  = "#009900"
GRID_COLOR  = "#aaaaaa"
ZONE_COLORS = {
    "chair_left":  "#fde9a2",
    "chair_right": "#fde9a2",
    "table":       "#d0e8d0",
    "shelf":       "#ac2e2e",
    "filler":      "#e0e0e0",
}

# ── Module Library ────────────────────────────────────────────────────────────
# Local coordinates: origin at bottom-left of module, x→right, y→up, 1 unit = 1 cell.
# segments : list of polylines [(x,y), ...] — for drawing only
# ports     : dict edge → [(x,y)] — boundary midpoints where lines exit the module

MODULES: Dict[str, dict] = {
   "chair_left_h2_v1": {
        "id": "chair_left_h2_v1",
        "w": 2, "h": 2,
        "zone": "chair_left",
        "segments": [
            [(0.5, 2.0), (0.5, 1.5)],                           # stem
            [(0.5, 1.5), (1.5, 1.5), (1.5, 0.5),
             (0.5, 0.5), (0.5, 1.5)],                           # seat rectangle (closed)
            [(1.5, 0.5), (2.0, 0.5)],                           # leg → right port
        ],
        "ports": {
            "top":    [(0.5, 2.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
    "chair_left_h2_v2": {
        "id": "chair_left_h2_v2",
        "w": 2, "h": 2,
        "zone": "chair_left",
        "segments": [
            [(0.5, 2.0), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (2.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 2.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
     "chair_left_h2_v3": {
        "id": "chair_left_h2_v3",
        "w": 2, "h": 2,
        "zone": "chair_left",
        "segments": [
            [(0.5, 2.0), (0.5, 1.5), (1.5, 1.5), (1.0, 0.5), (2.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 2.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
   
    "chair_left_h3_v1": {
        "id": "chair_left_h3_v1",
        "w": 2, "h": 3,
        "zone": "chair_left",
        "segments": [
            [(0.5, 3.0), (0.5, 1.5)],                           # stem
            [(0.5, 2.5), (1.5, 2.5), (1.5, 0.5),
             (0.5, 0.5), (0.5, 2.5)],                         # seat rectangle (closed)
            [(1.5, 0.5), (2.0, 0.5)],                           # leg → right port
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
    "chair_left_h3_v2": {
        "id": "chair_left_h3_v2",
        "w": 2, "h": 3,
        "zone": "chair_left",
        "segments": [
            [(0.5, 3.0), (0.5, 1.5)],                           # stem
            [(0.5, 2.0), (1.5, 2.0), (1.5, 0.5),
             (0.5, 0.5), (0.5, 2.0)],                         # seat rectangle (closed)
            [(1.5, 0.5), (2.0, 0.5)],                           # leg → right port
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
    
     "chair_left_h3_v3": {
        "id": "chair_left_h3_v3",
        "w": 2, "h": 3,
        "zone": "chair_left",
        "segments": [
            [(0.5, 3.0), (0.5, 2.5), (1.5, 2.5), (1.5, 0.5), (2.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
        },
    "chair_left_h3_v4": {
        "id": "chair_left_h3_v4",
        "w": 2, "h": 3,
        "zone": "chair_left",
        "segments": [
            [(0.5, 3.0), (0.5, 2.0), (1.5, 2.0), (1.5, 0.5), (2.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },

    },
    "chair_left_h3_v5": {
        "id": "chair_left_h3_v5",
        "w": 2, "h": 3,
        "zone": "chair_left",
        "segments": [
            [(0.5, 3.0), (0.5, 2.5), (1.5, 2.5), (1.0, 0.5), (2.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
    "chair_left_h3_v6": {
        "id": "chair_left_h3_v6",
        "w": 2, "h": 3,
        "zone": "chair_left",
        "segments": [
            [(0.5, 3.0), (0.5, 2.0), (1.5, 2.0), (1.0, 0.5), (2.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(2.0, 0.5)],
        },
    },
        
    "chair_right_h3_v1": {
        "id": "chair_right_h3_v1",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "segments": [
            [(1.5, 3.0), (1.5, 2.5)],                           # stem
            [(1.5, 2.5), (0.5, 2.5), (0.5, 0.5),
             (1.5, 0.5), (1.5, 2.5)],                           # seat rectangle (closed)
            [(0.5, 0.5), (0.0, 0.5)],                           # leg → left port
        ],
        "ports": {
            "top":    [(1.5, 3.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "chair_right_h2_v1": {
        "id": "chair_right_h2_v1",
        "w": 2, "h": 2,
        "zone": "chair_right",
        "segments": [
            [(1.5, 2.0), (1.5, 1.5)],                           # stem
            [(1.5, 1.5), (0.5, 1.5), (0.5, 0.5),
             (1.5, 0.5), (1.5, 1.5)],                           # seat rectangle (closed)
            [(0.5, 0.5), (0.0, 0.5)],                           # leg → left port
        ],
        "ports": {
            "top":    [(1.5, 2.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "table_h3_v1": {
        "id": "table_h3_v1",
        "w": 2, "h": 3,
        "zone": "table",
        "segments": [
            [(0.5, 2.5), (1.5, 2.5)],   # top horizontal bar
            [(0.5, 2.5), (1.0, 0.5)],   # left diagonal to tip
            [(1.5, 2.5), (1.0, 0.5)],   # right diagonal to tip
            [(1.0, 0.5), (0.0, 0.5)],   # left leg → left port
            [(1.0, 0.5), (2.0, 0.5)],   # right leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },
    "shelf_h3_v1": {
        "id": "shelf_h3_v1",
        "w": 6, "h": 3,
        "zone": "shelf",
        "segments": [
            [(0.5, 0.0), (0.5, 2.5)],   # left stem up
            [(5.5, 0.0), (5.5, 2.5)],   # right stem up
            [(0.5, 2.5), (5.5, 2.5)],   # horizontal bar
        ],
        "ports": {
            "top":    [],
            "bottom": [(0.5, 0.0), (5.5, 0.0)],
            "left":   [],
            "right":  [],
        },
    },

    # ── 1×1 filler tiles ──────────────────────────────────────────────────────
    "filler_empty": {
        "id": "filler_empty", "w": 1, "h": 1, "zone": "filler",
        "segments": [],
        "ports": {"top": [], "bottom": [], "left": [], "right": []},
    },
    "filler_pass_v": {
        "id": "filler_pass_v", "w": 1, "h": 1, "zone": "filler",
        "segments": [[(0.5, 0.0), (0.5, 1.0)]],
        "ports": {"top": [(0.5, 1.0)], "bottom": [(0.5, 0.0)], "left": [], "right": []},
    },
    "filler_pass_h": {
        "id": "filler_pass_h", "w": 1, "h": 1, "zone": "filler",
        "segments": [[(0.0, 0.5), (1.0, 0.5)]],
        "ports": {"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(1.0, 0.5)]},
    },
    # "filler_corner_br": {
    #     "id": "filler_corner_br", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 0.0), (0.5, 0.5), (1.0, 0.5)]],
    #     "ports": {"top": [], "bottom": [(0.5, 0.0)], "left": [], "right": [(1.0, 0.5)]},
    # },
    # "filler_corner_bl": {
    #     "id": "filler_corner_bl", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]],
    #     "ports": {"top": [], "bottom": [(0.5, 0.0)], "left": [(0.0, 0.5)], "right": []},
    # },
    # "filler_corner_tr": {
    #     "id": "filler_corner_tr", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 1.0), (0.5, 0.5), (1.0, 0.5)]],
    #     "ports": {"top": [(0.5, 1.0)], "bottom": [], "left": [], "right": [(1.0, 0.5)]},
    # },
    # "filler_corner_tl": {
    #     "id": "filler_corner_tl", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 1.0), (0.5, 0.5), (0.0, 0.5)]],
    #     "ports": {"top": [(0.5, 1.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []},
    # },
    # "filler_t_up": {
    #     "id": "filler_t_up", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.0, 0.5), (1.0, 0.5)], [(0.5, 0.5), (0.5, 1.0)]],
    #     "ports": {"top": [(0.5, 1.0)], "bottom": [], "left": [(0.0, 0.5)], "right": [(1.0, 0.5)]},
    # },
    # "filler_t_down": {
    #     "id": "filler_t_down", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.0, 0.5), (1.0, 0.5)], [(0.5, 0.5), (0.5, 0.0)]],
    #     "ports": {"top": [], "bottom": [(0.5, 0.0)], "left": [(0.0, 0.5)], "right": [(1.0, 0.5)]},
    # },
    # "filler_t_left": {
    #     "id": "filler_t_left", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 0.0), (0.5, 1.0)], [(0.5, 0.5), (0.0, 0.5)]],
    #     "ports": {"top": [(0.5, 1.0)], "bottom": [(0.5, 0.0)], "left": [(0.0, 0.5)], "right": []},
    # },
    # "filler_t_right": {
    #     "id": "filler_t_right", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 0.0), (0.5, 1.0)], [(0.5, 0.5), (1.0, 0.5)]],
    #     "ports": {"top": [(0.5, 1.0)], "bottom": [(0.5, 0.0)], "left": [], "right": [(1.0, 0.5)]},
    # },
    # "filler_cross": {
    #     "id": "filler_cross", "w": 1, "h": 1, "zone": "filler",
    #     "segments": [[(0.5, 0.0), (0.5, 1.0)], [(0.0, 0.5), (1.0, 0.5)]],
    #     "ports": {"top": [(0.5, 1.0)], "bottom": [(0.5, 0.0)], "left": [(0.0, 0.5)], "right": [(1.0, 0.5)]},
    # },
}

# ── Zone definitions ──────────────────────────────────────────────────────────
# x_rule / y_rule: arrays of "first N" / "last N" / "middle N" strings.
# Having multiple rules per axis means the solver can choose among different sizes.

ZONES = [
    {
        "id":      "chair_left",
        "x_rule":  ["first 2"],
        "y_rule":  ["first 3", "first 2"],
        "modules": [
            "chair_left_h3_v1", "chair_left_h3_v2", "chair_left_h3_v3",
            "chair_left_h3_v4", "chair_left_h3_v5",
            "chair_left_h2_v1", "chair_left_h2_v2",
        ],
    },
    {
        "id":      "table",
        "x_rule":  ["middle 2"],
        "y_rule":  ["first 3"],
        "modules": ["table_h3_v1"],
    },
    {
        "id":      "chair_right",
        "x_rule":  ["last 2"],
        "y_rule":  ["first 3", "first 2"],
        "modules": ["chair_right_h3_v1", "chair_right_h2_v1"],
    },
    {
        "id":      "shelf",
        "x_rule":  ["full"],     # spans full section width — module created at solve time
        "y_rule":  ["last 3"],
        "modules": [],           # populated dynamically inside solve()
    },
]

# Required zones for a valid section
SECTION_RULES = ["chair_left", "table", "chair_right", "shelf"]

# ── Zone resolver ─────────────────────────────────────────────────────────────

def resolve_rule(rule: str, dim: int) -> Tuple[int, int]:
    """Parse 'first N' / 'last N' / 'middle N' / 'full' → (start, end)."""
    parts = rule.strip().split()
    if parts[0] == "full":
        return (0, dim)
    n = int(parts[1])
    if parts[0] == "first":
        return (0, n)
    if parts[0] == "last":
        return (dim - n, dim)
    if parts[0] == "middle":
        s = (dim - n) // 2
        return (s, s + n)
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

# ── Adjacency checker ─────────────────────────────────────────────────────────

def _ports_in_range(mod: dict, edge: str, x_off: float, y_off: float,
                    lo: float, hi: float) -> frozenset:
    """Return section-coord ports on `edge` whose position along the edge is in [lo, hi]."""
    pts = set()
    for px, py in mod["ports"][edge]:
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
        for b in placed[i + 1:]:
            mb = MODULES[b["module_id"]]
            ax0, ay0 = a["x_off"], a["y_off"]
            bx0, by0 = b["x_off"], b["y_off"]

            # A's right edge coincides with B's left edge
            if abs((ax0 + ma["w"]) - bx0) < EPS:
                y_lo = max(ay0, by0)
                y_hi = min(ay0 + ma["h"], by0 + mb["h"])
                if y_hi > y_lo:
                    if (_ports_in_range(ma, "right", ax0, ay0, y_lo, y_hi) !=
                            _ports_in_range(mb, "left",  bx0, by0, y_lo, y_hi)):
                        return False

            # B's right edge coincides with A's left edge
            if abs((bx0 + mb["w"]) - ax0) < EPS:
                y_lo = max(ay0, by0)
                y_hi = min(ay0 + ma["h"], by0 + mb["h"])
                if y_hi > y_lo:
                    if (_ports_in_range(mb, "right", bx0, by0, y_lo, y_hi) !=
                            _ports_in_range(ma, "left",  ax0, ay0, y_lo, y_hi)):
                        return False

            # A's top edge coincides with B's bottom edge
            if abs((ay0 + ma["h"]) - by0) < EPS:
                x_lo = max(ax0, bx0)
                x_hi = min(ax0 + ma["w"], bx0 + mb["w"])
                if x_hi > x_lo:
                    if (_ports_in_range(ma, "top",    ax0, ay0, x_lo, x_hi) !=
                            _ports_in_range(mb, "bottom", bx0, by0, x_lo, x_hi)):
                        return False

            # B's top edge coincides with A's bottom edge
            if abs((by0 + mb["h"]) - ay0) < EPS:
                x_lo = max(ax0, bx0)
                x_hi = min(ax0 + ma["w"], bx0 + mb["w"])
                if x_hi > x_lo:
                    if (_ports_in_range(mb, "top",    bx0, by0, x_lo, x_hi) !=
                            _ports_in_range(ma, "bottom", ax0, ay0, x_lo, x_hi)):
                        return False

    return True

# ── Circuit validator ─────────────────────────────────────────────────────────

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
        for seg in mod["segments"]:
            pts = [(round(x + xo, 9), round(y + yo, 9)) for x, y in seg]
            for k in range(len(pts) - 1):
                degree[pts[k]]     += 1
                degree[pts[k + 1]] += 1

    return all(d != 1 for d in degree.values())

# ── Solver ────────────────────────────────────────────────────────────────────

def _gap_cells(placed_so_far: List[dict], W: int, H: int) -> List[Tuple[int, int]]:
    """Return all (col, row) cells in the W×H grid not covered by any placed module."""
    covered: set = set()
    for p in placed_so_far:
        m = MODULES[p["module_id"]]
        for col in range(int(p["x_off"]), int(p["x_off"]) + m["w"]):
            for row in range(int(p["y_off"]), int(p["y_off"]) + m["h"]):
                covered.add((col, row))
    return [(col, row) for row in range(H) for col in range(W)
            if (col, row) not in covered]


def solve(W: int, H: int, seed: int) -> Optional[List[dict]]:
    """
    Two-phase backtracking solver.
    Phase 1: place named zone modules (chair, table, shelf, …).
    Phase 2: fill every remaining cell with a 1×1 filler tile so the
             full W×H grid is covered and the closed-circuit rule is met.
    """
    rng = random.Random(seed)
    filler_ids = [mid for mid, m in MODULES.items() if m["zone"] == "filler"]

    # Ensure a shelf module exists for this exact width
    shelf_id = f"shelf_h3_w{W}_v1"
    if shelf_id not in MODULES:
        MODULES[shelf_id] = {
            "id": shelf_id, "w": W, "h": 3, "zone": "shelf",
            "segments": [
                [(0.5, 0.0), (0.5, 2.5)],
                [(W - 0.5, 0.0), (W - 0.5, 2.5)],
                [(0.5, 2.5), (W - 0.5, 2.5)],
            ],
            "ports": {
                "top":    [],
                "bottom": [(0.5, 0.0), (W - 0.5, 0.0)],
                "left":   [],
                "right":  [],
            },
        }

    # Build a local zones list with the shelf pointing at the right module
    zones = [
        z if z["id"] != "shelf" else {**z, "modules": [shelf_id]}
        for z in ZONES
    ]

    # Phase 1 candidates — one option list per named zone
    reg_candidates: List[List[dict]] = []
    for zone in zones:
        options: List[dict] = []
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                res = resolve_zone_position(zone, W, H, xr, yr)
                w, h = res["w"], res["h"]
                for mid in zone["modules"]:
                    if MODULES[mid]["w"] == w and MODULES[mid]["h"] == h:
                        options.append({
                            "module_id": mid,
                            "x_off": res["x_off"],
                            "y_off": res["y_off"],
                            "w": w, "h": h,
                        })
        rng.shuffle(options)
        reg_candidates.append(options)

    placed: List[dict] = []

    def solve_gaps() -> bool:
        """Phase 2: backtrack over every uncovered cell with filler tiles."""
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
            del placed[n_before:]   # clean up any partial gap placements
        return ok

    def bt_reg(i: int) -> bool:
        if i == len(reg_candidates):
            return solve_gaps()
        for opt in reg_candidates[i]:
            placed.append(opt)
            if check_adjacency(placed):
                if bt_reg(i + 1):
                    return True
            placed.pop()
        return False

    return placed if bt_reg(0) else None

# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_grid(ax, ox: float, oy: float, w: int, h: int) -> None:
    for i in range(w + 1):
        lw = 1.2 if i in (0, w) else 0.3
        ax.plot([ox + i, ox + i], [oy, oy + h], color=GRID_COLOR, lw=lw, zorder=1)
    for j in range(h + 1):
        lw = 1.2 if j in (0, h) else 0.3
        ax.plot([ox, ox + w], [oy + j, oy + j], color=GRID_COLOR, lw=lw, zorder=1)


def _draw_module(ax, mod: dict, x_off: float, y_off: float,
                 show_grid: bool = True, show_ports: bool = True) -> None:
    w, h = mod["w"], mod["h"]

    if show_grid:
        fc = ZONE_COLORS.get(mod.get("zone", ""), "#ffffff")
        ax.add_patch(patches.Rectangle(
            (x_off, y_off), w, h,
            facecolor=fc, alpha=0.25, zorder=0, linewidth=0,
        ))
        _draw_grid(ax, x_off, y_off, w, h)

    for seg in mod["segments"]:
        xs = [p[0] + x_off for p in seg]
        ys = [p[1] + y_off for p in seg]
        ax.plot(xs, ys, color=LINE_COLOR, lw=2.2, zorder=3,
                solid_capstyle="round", solid_joinstyle="round")

    if show_ports:
        for pts in mod["ports"].values():
            for px, py in pts:
                ax.plot(px + x_off, py + y_off, "o",
                        color=PORT_COLOR, ms=6, zorder=4)

# ── Section plot ──────────────────────────────────────────────────────────────

def plot_section(placed: List[dict], W: int, H: int) -> plt.Figure:
    scale = max(1.2, 8.0 / W)
    fig, ax = plt.subplots(figsize=(W * scale, H * scale))

    for p in placed:
        mod = MODULES[p["module_id"]]
        _draw_module(ax, mod, p["x_off"], p["y_off"])
        cx = p["x_off"] + mod["w"] / 2
        cy = p["y_off"] + mod["h"] / 2
        ax.text(cx, cy, mod["zone"].replace("_", "\n"),
                ha="center", va="center", fontsize=7, color="#666666", alpha=0.7)

    ax.set_xlim(-0.3, W + 0.3)
    ax.set_ylim(-0.3, H + 0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Nomadic Engine — Section  {W} × {H}", fontsize=12, pad=10)
    fig.tight_layout()
    return fig

# ── Module library plot ───────────────────────────────────────────────────────

ZONE_ORDER = ["chair_left", "chair_right", "table", "shelf", "filler"]


def plot_module_library() -> plt.Figure:
    mods = sorted(
        MODULES.values(),
        key=lambda m: (
            ZONE_ORDER.index(m["zone"]) if m["zone"] in ZONE_ORDER else 99,
            m["id"],
        ),
    )

    n_cols = 4
    n_rows = math.ceil(len(mods) / n_cols)
    pad = 0.8

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4.0, n_rows * 3.5),
                             squeeze=False)
    flat = axes.flatten()

    prev_zone = None
    for i, mod in enumerate(mods):
        ax = flat[i]
        w, h = mod["w"], mod["h"]
        _draw_module(ax, mod, 0.0, 0.0, show_grid=True, show_ports=True)
        ax.set_xlim(-pad, w + pad)
        ax.set_ylim(-pad, h + pad)
        ax.set_aspect("equal")
        ax.axis("off")

        # Short display name: strip "filler_" prefix for filler tiles
        short = mod["id"].replace("filler_", "")
        ax.set_title(f'{short}\n{w}w × {h}h', fontsize=8, pad=4)

        # Zone group label above the first tile of each new zone
        if mod["zone"] != prev_zone:
            fc = ZONE_COLORS.get(mod["zone"], "#e0e0e0")
            label = mod["zone"].replace("_", " ").upper()
            ax.annotate(
                label,
                xy=(0.0, 1.0), xycoords="axes fraction",
                xytext=(0.0, 1.14), textcoords="axes fraction",
                ha="left", va="bottom", annotation_clip=False,
                fontsize=8.5, fontweight="bold", color="#333333",
                bbox=dict(boxstyle="round,pad=0.2", fc=fc, ec="none", alpha=0.7),
            )
            prev_zone = mod["zone"]

    for j in range(len(mods), len(flat)):
        flat[j].axis("off")

    fig.suptitle("Nomadic Engine — Module Library", fontsize=13, y=1.01)
    fig.tight_layout()
    return fig

# ── Streamlit UI ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Nomadic Engine", layout="wide")
st.title("Nomadic Engine")

tab_lib, tab_sec = st.tabs(["Module Library", "Section"])

with tab_lib:
    st.caption(
        "All module variants at unit scale (1 cell = 1 unit).  "
        "Red lines = geometry.  Green dots = ports (boundary midpoints where lines exit).  "
        "Coloured fill = zone type."
    )
    st.pyplot(plot_module_library())

with tab_sec:
    st.caption("Prototype: W=6, H=6.  Solver places chair-left, table, chair-right, shelf.")
    c1, c2, c3 = st.columns(3)
    with c1:
        seed = int(st.number_input("Seed", min_value=0, max_value=1_000_000, value=42, step=1))
    with c2:
        W = int(st.number_input("Width W", min_value=6, max_value=20, value=6, step=1,
                                help="Shelf auto-scales to full width; gaps between zones filled automatically"))
    with c3:
        H = int(st.number_input("Height H", min_value=6, max_value=20, value=6, step=1,
                                help="Extra rows above zones are auto-filled with filler tiles"))

    with st.spinner("Solving…"):
        result = solve(W, H, seed)

    if result is None:
        st.error("No valid section found — circuit cannot be closed with current modules.")
    else:
        st.pyplot(plot_section(result, W, H))

        with st.expander("Placement details"):
            for p in result:
                st.write(
                    f"**{p['module_id']}** — "
                    f"offset ({p['x_off']:.0f}, {p['y_off']:.0f})  "
                    f"size {p['w']}w × {p['h']}h"
                )

        with st.expander("Circuit validation"):
            ok_adj = check_adjacency(result)
            ok_cir = check_circuit(result)
            st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
            st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")
