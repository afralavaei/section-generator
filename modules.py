from typing import Dict

# ── Constants ─────────────────────────────────────────────────────────────────
EPS = 1e-9
LINE_COLOR  = "#010605"   # dark teal-sage — clean, no red
PORT_COLOR  = "#009900"   # 009900
GRID_COLOR  = "#8a9088"   # mid sage-gray, visible against zone fills
ZONE_COLORS = {
    "chair_left":     "#A6B4B4",  # Sage −20%
    "chair_right":    "#A6B4B4",  # Sage −20%
    "sofa":           "#D6D7CF",  # Stack −20%
    "tv_table":       "#DADEBB",  # Morning Blue −20%
    "table":          "#D9D9D9",  # Sour Dough −20% (warm surface)
    "shelf":          "#A5B3A2",  # Sour Dough −30%
    "lower_cabinet":  "#E3DDC8",  # Sour Dough −30%
    "upper_cabinet":  "#C8BEB5",  # Sour Dough −40%
    "kitchen_wall":   "#DBE3E5",  # Slate Gray −20%
    "bed":            "#CCCCCC",  # Morning Blue deeper
    "corridor_left":  "#DBE3E5",  # Cararra −25%
    "corridor_right": "#DBE3E5",  # Cararra −25%
    "filler":         "#FFFFFFFF",  # Cararra −15%
}

ZONE_ALPHAS = {
    "filler":         0.08,
    "table":          0.20,
    "corridor_left":  0.20,
    "corridor_right": 0.20,
    "chair_left":     0.20,
    "chair_right":    0.20,
}

# ── Module Library ────────────────────────────────────────────────────────────
# Local coordinates: origin at bottom-left of module, x→right, y→up, 1 unit = 1 cell.
# segments : list of polylines [(x,y), ...] — for drawing only
# ports     : dict edge → [(x,y)] — boundary midpoints where lines exit the module


def _spacious_segs(w: int, H: int, side: str) -> list:
    """
    Circuit-valid segments for a spacious corridor.
    Outer 1.5-wide strip has horizontal shelves; inner zone is open circulation.
    Segments are split at every junction so all endpoints are degree 2 or 3.
    """
    shelf_ys = sorted(y for y in (k * 1.5 for k in range(1, H + 1)) if 0.5 < y < H - 0.5)

    if side == "right":
        outer_x = w - 0.5
        dx      = outer_x - 1.5
        inner_x = 0.0
    else:
        outer_x = 0.5
        dx      = outer_x + 1.5
        inner_x = float(w)

    segs = []
    # Bottom arm — split at divider x
    segs.append([(inner_x, 0.5), (dx, 0.5)])
    segs.append([(dx, 0.5),      (outer_x, 0.5)])
    # Top arm — split at divider x
    segs.append([(outer_x, H - 0.5), (dx, H - 0.5)])
    segs.append([(dx, H - 0.5),      (inner_x, H - 0.5)])
    # Outer arm — split at each shelf_y
    for a, b in zip([0.5] + shelf_ys, shelf_ys + [H - 0.5]):
        segs.append([(outer_x, a), (outer_x, b)])
    # Vertical divider — split at each shelf_y
    for a, b in zip([0.5] + shelf_ys, shelf_ys + [H - 0.5]):
        segs.append([(dx, a), (dx, b)])
    # Horizontal shelves
    lo, hi = min(dx, outer_x), max(dx, outer_x)
    for y in shelf_ys:
        segs.append([(lo, y), (hi, y)])
    return segs


def _spacious_short_segs(w: int, H: int, side: str) -> list:
    """
    Like _spacious_segs but without the top arm — used for the short spacious
    corridor beneath a full-width shelf.  The outer wall rises to y=H (the
    corridor module top) so its endpoint connects to the shelf bottom port.
    A horizontal stub joins the divider top to the outer wall so no dangling ends.
    """
    shelf_ys = sorted(y for y in (k * 1.5 for k in range(1, H + 1)) if 0.5 < y < H - 0.5)

    if side == "right":
        outer_x = w - 0.5
        dx      = outer_x - 1.5
        inner_x = 0.0
    else:
        outer_x = 0.5
        dx      = outer_x + 1.5
        inner_x = float(w)

    segs = []
    # Bottom arm — split at divider x
    lo_x, hi_x = min(inner_x, dx), max(inner_x, dx)
    segs.append([(inner_x, 0.5), (dx, 0.5)])
    segs.append([(dx, 0.5),      (outer_x, 0.5)])
    # Outer arm — from 0.5 up to H-0.5, split at shelf_ys
    for a, b in zip([0.5] + shelf_ys, shelf_ys + [H - 0.5]):
        segs.append([(outer_x, a), (outer_x, b)])
    # Extension from H-0.5 to H (top port that meets the shelf)
    segs.append([(outer_x, H - 0.5), (outer_x, H)])
    # Top stub — connects divider top to outer wall (closes degree at divider top)
    segs.append([(dx, H - 0.5), (outer_x, H - 0.5)])
    # Vertical divider — split at shelf_ys
    for a, b in zip([0.5] + shelf_ys, shelf_ys + [H - 0.5]):
        segs.append([(dx, a), (dx, b)])
    # Horizontal shelves
    lo, hi = min(dx, outer_x), max(dx, outer_x)
    for y in shelf_ys:
        segs.append([(lo, y), (hi, y)])
    return segs


MODULES: Dict[str, dict] = {

    #-------Left_Chair_Modules------------------------------------------------------

   "chair_left_h2_v1": {
        "id": "chair_left_h2_v1",
        "w": 2, "h": 2,
        "zone": "chair_left",
        "description": "Left-facing chair, height 2. Closed rectangular seat with stem and right leg connecting to the table.",
        "tags": ["rectilinear", "closed-seat", "high-detail", "h2"],
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
        "description": "Left-facing chair, height 2. Single polyline from backrest top to right leg. Minimal, fast read.",
        "tags": ["minimal", "single-line", "h2"],
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
        "description": "Left-facing chair, height 2. Diagonal with a central V-inflection at the seat base.",
        "tags": ["angled", "v-tip", "h2"],
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
        "description": "Left-facing chair, height 3. Tall closed rectangular seat with explicit stem and right leg. High geometric detail.",
        "tags": ["rectilinear", "closed-seat", "high-detail", "h3"],
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
        "description": "Left-facing chair, height 3. Closed seat set lower, leaving more visible backrest space.",
        "tags": ["rectilinear", "closed-seat", "h3"],
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
        "description": "Left-facing chair, height 3. Single line from backrest through seat top-right corner to the right leg.",
        "tags": ["diagonal", "compact", "h3"],
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
        "description": "Left-facing chair, height 3. Diagonal from backrest to a lower seat position and right leg.",
        "tags": ["diagonal", "compact", "h3"],
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
        "description": "Left-facing chair, height 3. High seat with a V-tip at the base leading to the right leg.",
        "tags": ["angled", "v-tip", "h3"],
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
        "description": "Left-facing chair, height 3. Lower seat with a V-tip at the base leading to the right leg.",
        "tags": ["angled", "v-tip", "h3"],
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

    #-------Right_Chair_Modules------------------------------------------------------

      "chair_right_h2_v1": {
        "id": "chair_right_h2_v1",
        "w": 2, "h": 2,
        "zone": "chair_right",
        "description": "Right-facing chair, height 2. Closed rectangular seat with stem and left leg connecting to the table.",
        "tags": ["rectilinear", "closed-seat", "high-detail", "h2"],
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
       "chair_right_h2_v2": {
        "id": "chair_right_h2_v2",
        "w": 2, "h": 2,
        "zone": "chair_right",
        "description": "Right-facing chair, height 2. Single polyline from backrest top to left leg. Minimal, fast read.",
        "tags": ["minimal", "single-line", "h2"],
        "segments": [
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 2.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
     "chair_right_h2_v3": {
        "id": "chair_right_h2_v3",
        "w": 2, "h": 2,
        "zone": "chair_right",
        "description": "Right-facing chair, height 2. Diagonal with a central V-inflection at the seat base.",
        "tags": ["angled", "v-tip", "h2"],
        "segments": [
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (1.0, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 2.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },

    "chair_right_h3_v1": {
        "id": "chair_right_h3_v1",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "description": "Right-facing chair, height 3. Tall closed rectangular seat with explicit stem and left leg. High geometric detail.",
        "tags": ["rectilinear", "closed-seat", "high-detail", "h3"],
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
    "chair_right_h3_v2": {
        "id": "chair_right_h3_v2",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "description": "Right-facing chair, height 3. Closed seat set lower, leaving more visible backrest space.",
        "tags": ["rectilinear", "closed-seat", "h3"],
        "segments": [
            [(1.5, 3.0), (1.5, 2.0)],                           # stem
            [(1.5, 2.0), (0.5, 2.0), (0.5, 0.5),
             (1.5, 0.5), (1.5, 2.0)],                           # seat rectangle (closed)
            [(0.5, 0.5), (0.0, 0.5)],                           # leg → left port
        ],
        "ports": {
            "top":    [(1.5, 3.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "chair_right_h3_v3": {
        "id": "chair_right_h3_v3",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "description": "Right-facing chair, height 3. Single line from backrest through seat top-left corner to the left leg.",
        "tags": ["diagonal", "compact", "h3"],
        "segments": [
            [(1.5, 3.0), (1.5, 2.5), (0.5, 2.5), (0.5, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 3.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "chair_right_h3_v4": {
        "id": "chair_right_h3_v4",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "description": "Right-facing chair, height 3. Diagonal from backrest to a lower seat position and left leg.",
        "tags": ["diagonal", "compact", "h3"],
        "segments": [
            [(1.5, 3.0), (1.5, 2.0), (0.5, 2.0), (0.5, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 3.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
     "chair_right_h3_v5": {
        "id": "chair_right_h3_v5",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "description": "Right-facing chair, height 3. High seat with a V-tip at the base leading to the left leg.",
        "tags": ["angled", "v-tip", "h3"],
        "segments": [
            [(1.5, 3.0), (1.5, 2.5), (0.5, 2.5), (1.0, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 3.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "chair_right_h3_v6": {
        "id": "chair_right_h3_v6",
        "w": 2, "h": 3,
        "zone": "chair_right",
        "description": "Right-facing chair, height 3. Lower seat with a V-tip at the base leading to the left leg.",
        "tags": ["angled", "v-tip", "h3"],
        "segments": [
            [(1.5, 3.0), (1.5, 2.0), (0.5, 2.0), (1.0, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 3.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },

    #-------Table_Modules------------------------------------------------------

    "table_h2_v1": {
        "id": "table_h2_v1",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Coffee table, height 2. Two diagonals meet at a central V-tip below a mid-height horizontal bar.",
        "tags": ["v-tip", "symmetric", "h2", "coffee-table"],
        "segments": [
            [(0.5, 1.5), (1.5, 1.5)],   # top horizontal bar
            [(0.5, 1.5), (1.0, 0.5)],   # left diagonal to tip
            [(1.5, 1.5), (1.0, 0.5)],   # right diagonal to tip
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
     "table_h2_v2": {
        "id": "table_h2_v2",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Coffee table, height 2. V-tip legs reach up to a horizontal bar near the top.",
        "tags": ["v-tip", "tall-bar", "h2", "coffee-table"],
        "segments": [
            [(0.5, 2.0), (1.5, 2.0)],   # top horizontal bar
            [(0.5, 2.0), (1.0, 0.5)],   # left diagonal to tip
            [(1.5, 2.0), (1.0, 0.5)],   # right diagonal to tip
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
    "table_h2_v3": {
        "id": "table_h2_v3",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Coffee table, height 2. Rectangular frame with two straight vertical legs, each foot running to the side port.",
        "tags": ["rectilinear", "h2", "coffee-table"],
        "segments": [
            [(0.5, 1.5), (1.5, 1.5)],            # top horizontal bar
            [(0.5, 1.5), (0.5, 0.5), (0.0, 0.5)],  # left leg → left port
            [(1.5, 1.5), (1.5, 0.5), (2.0, 0.5)],  # right leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },
     "table_h2_v4": {
        "id": "table_h2_v4",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Coffee table, height 2. Tall rectangular frame with the top bar at maximum height, legs run to side ports.",
        "tags": ["rectilinear", "tall-bar", "h2", "coffee-table"],
        "segments": [
            [(0.5, 2.0), (1.5, 2.0)],            # top horizontal bar
            [(0.5, 2.0), (0.5, 0.5), (0.0, 0.5)],  # left leg → left port
            [(1.5, 2.0), (1.5, 0.5), (2.0, 0.5)],  # right leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },
    "table_h2_v5": {
        "id": "table_h2_v5",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Coffee table, height 2. Full-width top bar with inward-diagonal legs that splay back out to the side ports.",
        "tags": ["diagonal", "wide-top", "h2", "coffee-table"],
        "segments": [
            [(0.0, 1.5), (2.0, 1.5)],                # top horizontal bar
            [(0.0, 1.5), (0.5, 0.5), (0.0, 0.5)],    # left diagonal leg → left port
            [(2.0, 1.5), (1.5, 0.5), (2.0, 0.5)],    # right diagonal leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },
    "table_h2_v6": {
        "id": "table_h2_v6",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Coffee table, height 2. Full-width top bar at maximum height with diagonal legs splaying to side ports.",
        "tags": ["diagonal", "wide-top", "tall-bar", "h2", "coffee-table"],
        "segments": [
            [(0.0, 2.0), (2.0, 2.0)],                # top horizontal bar
            [(0.0, 2.0), (0.5, 0.5), (0.0, 0.5)],    # left diagonal leg → left port
            [(2.0, 2.0), (1.5, 0.5), (2.0, 0.5)],    # right diagonal leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },

    "table_h3_v1": {
        "id": "table_h3_v1",
        "w": 2, "h": 3,
        "zone": "table",
        "description": "Table, height 3. Two diagonals converge at a central V-tip below a raised horizontal bar.",
        "tags": ["v-tip", "symmetric", "h3"],
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
     "table_h3_v2": {
        "id": "table_h3_v2",
        "w": 2, "h": 3,
        "zone": "table",
        "description": "Table, height 3. Full-width top bar with diagonal legs splaying to side ports.",
        "tags": ["diagonal", "wide-top", "h3"],
        "segments": [
            [(0.0, 2.5), (2.0, 2.5)],                # top horizontal bar
            [(0.0, 2.5), (0.5, 0.5), (0.0, 0.5)],    # left diagonal leg → left port
            [(2.0, 2.5), (1.5, 0.5), (2.0, 0.5)],    # right diagonal leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },
    "table_h3_v3": {
        "id": "table_h3_v3",
        "w": 2, "h": 3,
        "zone": "table",
        "description": "Table, height 3. Tall rectangular frame with vertical legs, each foot running to the side port.",
        "tags": ["rectilinear", "h3"],
        "segments": [
            [(0.5, 2.5), (1.5, 2.5)],            # top horizontal bar
            [(0.5, 2.5), (0.5, 0.5), (0.0, 0.5)],  # left leg → left port
            [(1.5, 2.5), (1.5, 0.5), (2.0, 0.5)],  # right leg → right port
        ],
        "ports": {
            "top":    [],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [(2.0, 0.5)],
        },
    },

    #-------Sofa_Modules_(Living)---------------------------------------------

    "sofa_h3_v4": {
        "id": "sofa_h3_v4",
        "w": 4, "h": 3,
        "zone": "sofa",
        "description": "Sofa v4, w=4 h=3 -- organic curved shape with rounded armrests. 2D front face of sofa_h3_v4_3d.",
        "tags": ["sofa", "h3", "living", "organic", "curved", "w4"],
        "segments": [
            # front face main arc
            [(1.124,1.111),(1.251,0.740),(1.579,0.521),(1.979,0.5),(2.380,0.5),(2.781,0.507),(3.131,0.689),(3.298,1.046),(3.302,1.448),(3.302,1.849),(3.281,2.249),(3.062,2.577),(2.689,2.704)],
            # upper-left arc
            [(0.5,2.090),(0.536,2.298),(0.640,2.481),(0.800,2.618),(0.997,2.692),(1.208,2.704),(1.419,2.704),(1.631,2.704),(1.842,2.704),(2.054,2.704),(2.265,2.704),(2.477,2.704),(2.689,2.704)],
            # top stem
            [(0.5,2.090),(0.5,3.0)],
            # right exit
            [(2.689,0.5),(4.0,0.5)],
            # closing: lower-left straight (mirrors back face arc endpoint)
            [(1.124,1.111),(1.738,0.5)],
            # closing: floor line
            [(1.738,0.5),(2.689,0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(4.0, 0.5)],
        },
    },

    "sofa_h3_v3": {
        "id": "sofa_h3_v3",
        "w": 3, "h": 3,
        "zone": "sofa",
        "description": "Sofa v3, w=3 h=3 -- rounded hexagonal profile with curved backrest. 2D front face of sofa_h3_v3_3d.",
        "tags": ["sofa", "h3", "living", "rounded", "curved"],
        "segments": [
            [(0.5,0.5),(0.5,1.5),(1.0,2.0),(2.0,2.0),(2.5,1.5),(2.5,0.5),(0.5,0.5)],
            [(0.5,2.5),(1.0,1.5),(2.5,1.5)],
            [(2.5,0.5),(3.0,0.5)],
            [(0.5,2.5),(0.5,3.0)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(3.0, 0.5)],
        },
    },

    "sofa_h3_v2": {
        "id": "sofa_h3_v2",
        "w": 3, "h": 3,
        "zone": "sofa",
        "description": "Sofa v2, w=3 h=3 -- diagonal backrest with cross-rail. 2D front face of sofa_h3_v2_3d.",
        "tags": ["sofa", "h3", "living", "diagonal", "native"],
        "segments": [
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 0.5), (2.5, 0.5), (2.5, 1.5)],
            [(2.5, 1.5), (0.5, 1.5)],
            [(0.5, 1.5), (0.5, 2.5)],
            [(0.5, 0.5), (1.5, 2.5), (0.5, 2.5)],
            [(2.5, 0.5), (3.0, 0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(3.0, 0.5)],
        },
    },

    "sofa_h3_v1": {
        "id": "sofa_h3_v1",
        "w": 3, "h": 3,
        "zone": "sofa",
        "description": "Sofa, height 3. Single polyline — backrest top through seat to right leg.",
        "tags": ["diagonal", "compact", "h3", "living"],
       "segments": [
            [(0.5, 3.0), (0.5, 2.5)], [(0.5, 2.5), (1.0, 2.5), (1.0, 1.5), (2.5, 1.5),
             (2.5, 0.5), (0.5, 0.5), (0.5, 2.5)],  [(2.5, 0.5), (3.0, 0.5)],  # single polyline with a loop for the seat
        ],
        "ports": {
            "top":    [(0.5, 3.0)],
            "bottom": [],
            "left":   [],
            "right":  [(3.0, 0.5)]
        },
    },

    #-------TV_Table_Modules_(Living) — h2 only --------------------------------

    "tv_table_h2_v1": {
        "id": "tv_table_h2_v1",
        "w": 2, "h": 2,
        "zone": "tv_table",
        "description": "TV table, height 2. Closed rectangular cabinet with stem and left leg.",
        "tags": ["rectilinear", "closed", "high-detail", "h2", "living"],
        "segments": [
            [(1.5, 2.0), (1.5, 1.5)],
            [(1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (1.5, 0.5), (1.5, 1.5)],
            [(0.5, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 2.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "tv_table_h2_v2": {
        "id": "tv_table_h2_v2",
        "w": 2, "h": 2,
        "zone": "tv_table",
        "description": "TV table, height 2. Single polyline from top through shelf to left leg.",
        "tags": ["minimal", "single-line", "h2", "living"],
        "segments": [
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 2.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },
    "tv_table_h2_v3": {
        "id": "tv_table_h2_v3",
        "w": 2, "h": 2,
        "zone": "tv_table",
        "description": "TV table, height 2. Diagonal with a V-inflection at the base.",
        "tags": ["angled", "v-tip", "h2", "living"],
        "segments": [
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (1.0, 0.5), (0.0, 0.5)],
        ],
        "ports": {
            "top":    [(1.5, 2.0)],
            "bottom": [],
            "left":   [(0.0, 0.5)],
            "right":  [],
        },
    },

    #-------Shelf_Modules------------------------------------------------------

    "shelf_h1_v1": {
        "id": "shelf_h1_v1", "w": 6, "h": 1, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 1. Simple U-bracket: two side posts and a top bar. Minimal open storage profile.",
        "tags": ["minimal", "u-bracket", "open"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 0.5)],
            [(W-0.5, 0.0), (W-0.5, 0.5)],
            [(0.5, 0.5), (W-0.5, 0.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h2_v1": {
        "id": "shelf_h2_v1", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 2. Simple U-bracket: two side posts and a top bar. Minimal open storage profile.",
        "tags": ["minimal", "u-bracket", "open"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 0.5), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 0.5), (W-0.5, 1.5)],
            [(0.5, 1.5), (W-0.5, 1.5)],
            [(0.5, 0.5), (W-0.5, 0.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v1": {
        "id": "shelf_h3_v1", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. U-bracket split by a central vertical divider into two equal bays.",
        "tags": ["u-bracket", "divided", "symmetric"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0), (0.5, 2.5)],
            [(W-0.5, 0.0), (W-0.5, 1.0), (W-0.5, 2.5)],
            [(0.5, 1.0), (W/2, 1.0), (W-0.5, 1.0)],
            [(0.5, 2.5), (W/2, 2.5), (W-0.5, 2.5)],
            [(W/2, 1.0), (W/2, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h2_v2": {
        "id": "shelf_h2_v2", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 2. Asymmetric: tall left post, shorter right post, connected by a diagonal top bar.",
        "tags": ["asymmetric", "diagonal"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 0.5)],
            [(0.5, 1.5), (W-0.5, 0.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h2_v3": {
        "id": "shelf_h2_v3", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 2. Asymmetric: short left post, taller right post, connected by a diagonal top bar.",
        "tags": ["asymmetric", "diagonal"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 0.5)],
            [(W-0.5, 0.0), (W-0.5, 1.5)],
            [(0.5, 0.5), (W-0.5, 1.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h2_v4": {
        "id": "shelf_h2_v4", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 2. U-bracket with two horizontal shelves — three storage levels.",
        "tags": ["u-bracket", "three-level", "detailed"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 0.5), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 0.5), (W-0.5, 1.5)],
            [(0.5, 0.5), (W-0.5, 0.5)],
            [(0.5, 1.5), (W-0.5, 1.5)],[(W/2, 0.5), (W/2, 1.5)]
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h2_v5": {
        "id": "shelf_h2_v5", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 2. Small compartment on the left, multiple evenly-spaced bays filling the right section.",
        "tags": ["divided", "multi-bay", "complex"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 0.5)],
            [(W-0.5, 0.0), (W-0.5, 0.5)],
            [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)],
            [(1.5+i, 0.5) for i in range(W-1)] + [(W-0.5-i, 1.5) for i in range(W-1)] + [(1.5, 0.5)],
        ] + [[(1.5+i, 0.5), (1.5+i, 1.5)] for i in range(1, W-2)],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v2": {
        "id": "shelf_h3_v2", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. Closed frame with diagonal hatch lines suggesting densely packed storage.",
        "tags": ["hatched", "dense", "complex"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5+i, 1.0) for i in range(W)] + [(W-0.5-i, 2.5) for i in range(W)] + [(0.5, 1.0)],
        ] + [[(0.5+i, 1.0), (1.5+i, 2.5)] for i in range(1, W-2)],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },

    # ── Pitched roof shelf modules ───────────────────────────────────────────
    # h=4: eave at local y=3.0 (= section y=6 for H=7), ridge above that.
    # Posts run y=0→3.0 (no split at y=2.5) so _build_corridor_variants() skips
    # them — pitched roofs are dining-zone-only, no corr variants generated.
    # Peak positions: sym=W/2, left=W/3, right=2W/3.
    # Peak heights: v1=y=4.0 (steep), v2=y=3.5 (gentle).

    "shelf_pitched_sym_v1": {
        "id": "shelf_pitched_sym_v1", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, centred ridge, steep slope. Eave at y=3, ridge at y=4.",
        "tags": ["pitched", "symmetric", "steep"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5, 1.0), (W/2, 2.0), (W-0.5, 1.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_sym_v2": {
        "id": "shelf_pitched_sym_v2", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, centred ridge, gentle slope. Eave at y=3, ridge at y=3.5.",
        "tags": ["pitched", "symmetric", "gentle"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5, 1.0), (W/2, 1.5), (W-0.5, 1.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_left_v1": {
        "id": "shelf_pitched_left_v1", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, left-biased ridge, steep slope.",
        "tags": ["pitched", "left-biased", "steep"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5, 1.0), (W/3, 2.0), (W-0.5, 1.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_left_v2": {
        "id": "shelf_pitched_left_v2", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, left-biased ridge, gentle slope.",
        "tags": ["pitched", "left-biased", "gentle"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5, 1.0), (W/3, 1.5), (W-0.5, 1.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_right_v1": {
        "id": "shelf_pitched_right_v1", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, right-biased ridge, steep slope.",
        "tags": ["pitched", "right-biased", "steep"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5, 1.0), (2*W/3, 2.0), (W-0.5, 1.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_right_v2": {
        "id": "shelf_pitched_right_v2", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, right-biased ridge, gentle slope.",
        "tags": ["pitched", "right-biased", "gentle"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5, 1.0), (2*W/3, 1.5), (W-0.5, 1.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },

    # ── Divided-slanted shelf modules ─────────────────────────────────────────
    # Slanted (lean-to) outer profile + one horizontal shelf line inside.
    # Used when roof_style == "divided_slanted" (slanted site + corridor added).
    "shelf_divided_slanted_left_v1": {
        "id": "shelf_divided_slanted_left_v1", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Lean-to roof biased left (steep) with one horizontal shelf division.",
        "tags": ["slanted", "left-biased", "steep", "divided"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 1.0), (W-0.5, 1.5)],
            [(0.5, 1.0), (W/3, 2.0), (W-0.5, 1.0)],
            [(0.5, 1.5), (W-0.5, 1.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_divided_slanted_left_v2": {
        "id": "shelf_divided_slanted_left_v2", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Lean-to roof biased left (gentle) with one horizontal shelf division.",
        "tags": ["slanted", "left-biased", "gentle", "divided"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0), (0.5, 1.25)],
            [(W-0.5, 0.0), (W-0.5, 1.0), (W-0.5, 1.25)],
            [(0.5, 1.0), (W/3, 1.5), (W-0.5, 1.0)],
            [(0.5, 1.25), (W-0.5, 1.25)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_divided_slanted_right_v1": {
        "id": "shelf_divided_slanted_right_v1", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Lean-to roof biased right (steep) with one horizontal shelf division.",
        "tags": ["slanted", "right-biased", "steep", "divided"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 1.0), (W-0.5, 1.5)],
            [(0.5, 1.0), (2*W/3, 2.0), (W-0.5, 1.0)],
            [(0.5, 1.5), (W-0.5, 1.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_divided_slanted_right_v2": {
        "id": "shelf_divided_slanted_right_v2", "w": 6, "h": 2, "zone": "shelf", "scalable": True,
        "description": "Lean-to roof biased right (gentle) with one horizontal shelf division.",
        "tags": ["slanted", "right-biased", "gentle", "divided"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0), (0.5, 1.25)],
            [(W-0.5, 0.0), (W-0.5, 1.0), (W-0.5, 1.25)],
            [(0.5, 1.0), (2*W/3, 1.5), (W-0.5, 1.0)],
            [(0.5, 1.25), (W-0.5, 1.25)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },

    # ── Corridor modules ──────────────────────────────────────────────────────
    "corridor_right": {
        "id": "corridor_right", "w": 2, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Corridor on the right side. U-bracket spanning the full section height, opening inward.",
        "tags": ["corridor", "circulation", "h-scalable", "w-scalable", "right-side"],
        "wh_segments_fn": lambda w, H: [[(0.0, 0.5), (w - 0.5, 0.5), (w - 0.5, H - 0.5), (0.0, H - 0.5)]],
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [(0.0, 0.5), (0.0, H - 0.5)], "right": []},
    },
    "corridor_left": {
        "id": "corridor_left", "w": 2, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Corridor on the left side. U-bracket spanning the full section height, opening inward.",
        "tags": ["corridor", "circulation", "h-scalable", "w-scalable", "left-side"],
        "wh_segments_fn": lambda w, H: [[(w, 0.5), (0.5, 0.5), (0.5, H - 0.5), (w, H - 0.5)]],
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [], "right": [(w, 0.5), (w, H - 0.5)]},
    },
    "corridor_right_spacious": {
        "id": "corridor_right_spacious", "w": 4, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Corridor right — spacious (4-col). Outer 1.5-wide shelf strip; inner zone open circulation.",
        "tags": ["corridor", "circulation", "h-scalable", "right-side", "spacious"],
        "wh_segments_fn": lambda w, H: _spacious_segs(w, H, "right"),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [(0.0, 0.5), (0.0, H - 0.5)], "right": []},
    },
    "corridor_left_spacious": {
        "id": "corridor_left_spacious", "w": 4, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Corridor left — spacious (4-col). Outer 1.5-wide shelf strip; inner zone open circulation.",
        "tags": ["corridor", "circulation", "h-scalable", "left-side", "spacious"],
        "wh_segments_fn": lambda w, H: _spacious_segs(w, H, "left"),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [], "right": [(w, 0.5), (w, H - 0.5)]},
    },
    # Short spacious — same internal shelf structure but no top arm; outer wall rises
    # to y=H (module height = H_solve) to connect to the full-width shelf above.
    "corridor_right_spacious_short": {
        "id": "corridor_right_spacious_short", "w": 4, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Spacious short corridor right — internal shelves + outer wall to shelf; left port at y=0.5.",
        "tags": ["corridor", "h-scalable", "right-side", "spacious", "short"],
        "wh_segments_fn": lambda w, H: _spacious_short_segs(w, H, "right"),
        "wh_ports_fn":    lambda w, H: {"top": [(w - 0.5, H)], "bottom": [], "left": [(0.0, 0.5)], "right": []},
    },
    "corridor_left_spacious_short": {
        "id": "corridor_left_spacious_short", "w": 4, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Spacious short corridor left — internal shelves + outer wall to shelf; right port at y=0.5.",
        "tags": ["corridor", "h-scalable", "left-side", "spacious", "short"],
        "wh_segments_fn": lambda w, H: _spacious_short_segs(w, H, "left"),
        "wh_ports_fn":    lambda w, H: {"top": [(0.5, H)], "bottom": [], "left": [], "right": [(w, 0.5)]},
    },
    # Short corridor variants — L-shaped wall: floor arm connects to chair, right/left
    # outer wall rises to shelf. chair_right_corr / chair_left_corr variants supply
    # the matching port on the inner zone side.
    "corridor_right_short": {
        "id": "corridor_right_short", "w": 2, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Short corridor right — floor + right wall; left port connects to chair_right_corr.",
        "tags": ["corridor", "h-scalable", "right-side", "short"],
        "wh_segments_fn": lambda w, H: [[(0.0, 0.5), (w - 0.5, 0.5), (w - 0.5, H)]],
        "wh_ports_fn":    lambda w, H: {"top": [(w - 0.5, H)], "bottom": [], "left": [(0.0, 0.5)], "right": []},
    },
    "corridor_left_short": {
        "id": "corridor_left_short", "w": 2, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Short corridor left — floor + left wall; right port connects to chair_left_corr.",
        "tags": ["corridor", "h-scalable", "left-side", "short"],
        "wh_segments_fn": lambda w, H: [[(w, 0.5), (0.5, 0.5), (0.5, H)]],
        "wh_ports_fn":    lambda w, H: {"top": [(0.5, H)], "bottom": [], "left": [], "right": [(w, 0.5)]},
    },

    # ── Kitchen: lower cabinet ────────────────────────────────────────────────
    "kitchen_lower_w3_h4_v2": {
        "id": "kitchen_lower_w3_h4_v2", "w": 3, "h": 3, "zone": "lower_cabinet",
        "description": "Kitchen lower cabinet, 3 wide × 3 tall — narrow body (cols 0–1) with right exit.",
        "tags": ["kitchen", "lower-cabinet", "w3", "h4", "right-exit"],
        "segments": [
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 2.5), (2.0, 2.5), (2.0, 0.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(1.5, 0.5), (3.0, 0.5)],
        ],
        "ports": {"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []},
    },
    "kitchen_lower_w3_h4_v3": {
        "id": "kitchen_lower_w3_h4_v3", "w": 3, "h": 3, "zone": "lower_cabinet",
        "description": "Kitchen lower cabinet, 3 wide × 3 tall — wider body (cols 0–2) with right exit.",
        "tags": ["kitchen", "lower-cabinet", "w3", "h4", "right-exit", "wide"],
        "segments": [
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 2.5), (2.5, 2.5), (2.5, 0.5), (2.0, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(2.0, 0.5), (3.0, 0.5)],
        ],
        "ports": {"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []},
    },
    # Through-counter — left exit joins left bank, right exit joins corridor, top at x=2.5
    # so the filler chain at col 5 can reach the FRS shelf's post port at x=5.5.
    "kitchen_lower_w3_h4_through": {
        "id": "kitchen_lower_w3_h4_through", "w": 3, "h": 3, "zone": "lower_cabinet",
        "description": "Kitchen right-bank counter — through variant with left + right exits for W=8 double-counter.",
        "tags": ["kitchen", "lower-cabinet", "w3", "h4", "through"],
        "segments": [
            [(2.5, 3.0), (2.5, 2.5)],
            [(2.5, 2.5), (0.5, 2.5), (0.5, 0.5), (1.0, 0.5), (2.5, 0.5), (2.5, 2.5)],
            [(0.0, 0.5), (0.5, 0.5)],
            [(1.0, 0.5), (3.0, 0.5)],
        ],
        "ports": {"top": [(2.5, 3.0)], "left": [(0.0, 0.5)], "right": [(3.0, 0.5)], "bottom": []},
    },

    # ── Kitchen: upper cabinet — fixed-height variants (narrow + wide body) ─────
    "kitchen_upper_w2_h1": {
        "id": "kitchen_upper_w2_h1", "w": 2, "h": 1, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 1 tall — shelf: post + closed floating bracket.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h1"],
        "segments": [
            [(0.5, 0.0), (0.5, 1.0)],
            [(0.5, 0.2), (1.5, 0.2), (1.5, 0.8), (0.5, 0.8), (0.5, 0.2)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 1.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h1_wide": {
        "id": "kitchen_upper_w2_h1_wide", "w": 2, "h": 1, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 1 tall — wide shelf: post + wide closed bracket.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h1", "wide"],
        "segments": [
            [(0.5, 0.0), (0.5, 1.0)],
            [(0.5, 0.2), (2.0, 0.2), (2.0, 0.8), (0.5, 0.8), (0.5, 0.2)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 1.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h2": {
        "id": "kitchen_upper_w2_h2", "w": 2, "h": 2, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 2 tall.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h2"],
        "segments": [
            [(0.5, 0.0), (0.5, 0.5)],
            [(0.5, 1.5), (0.5, 2.0)],
            [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 2.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h2_wide": {
        "id": "kitchen_upper_w2_h2_wide", "w": 2, "h": 2, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 2 tall — wide body.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h2", "wide"],
        "segments": [
            [(0.5, 0.0), (0.5, 0.5)],
            [(0.5, 1.5), (0.5, 2.0)],
            [(0.5, 0.5), (2.0, 0.5), (2.0, 1.5), (0.5, 1.5), (0.5, 0.5)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 2.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h3": {
        "id": "kitchen_upper_w2_h3", "w": 2, "h": 3, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 3 tall.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h3"],
        "segments": [
            [(0.5, 0.0), (0.5, 0.5)],
            [(0.5, 2.5), (0.5, 3.0)],
            [(0.5, 0.5), (1.5, 0.5), (1.5, 2.5), (0.5, 2.5), (0.5, 0.5)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 3.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h3_wide": {
        "id": "kitchen_upper_w2_h3_wide", "w": 2, "h": 3, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 3 tall — wide body.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h3", "wide"],
        "segments": [
            [(0.5, 0.0), (0.5, 0.5)],
            [(0.5, 2.5), (0.5, 3.0)],
            [(0.5, 0.5), (2.0, 0.5), (2.0, 2.5), (0.5, 2.5), (0.5, 0.5)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 3.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h4": {
        "id": "kitchen_upper_w2_h4", "w": 2, "h": 4, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 4 tall.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h4"],
        "segments": [
            [(0.5, 0.0), (0.5, 0.5)],
            [(0.5, 3.5), (0.5, 4.0)],
            [(0.5, 0.5), (1.5, 0.5), (1.5, 3.5), (0.5, 3.5), (0.5, 0.5)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 4.0)], "left": [], "right": []},
    },
    "kitchen_upper_w2_h4_wide": {
        "id": "kitchen_upper_w2_h4_wide", "w": 2, "h": 4, "zone": "upper_cabinet",
        "description": "Kitchen upper cabinet, 2 wide × 4 tall — wide body.",
        "tags": ["kitchen", "upper-cabinet", "w2", "h4", "wide"],
        "segments": [
            [(0.5, 0.0), (0.5, 0.5)],
            [(0.5, 3.5), (0.5, 4.0)],
            [(0.5, 0.5), (2.0, 0.5), (2.0, 3.5), (0.5, 3.5), (0.5, 0.5)],
        ],
        "ports": {"bottom": [(0.5, 0.0)], "top": [(0.5, 4.0)], "left": [], "right": []},
    },

    # ── Kitchen: wall (h-scalable, last 2 cols) ──────────────────────────────
    "kitchen_wall": {
        "id": "kitchen_wall", "w": 2, "h": 7, "zone": "kitchen_wall",
        "h_scalable": True,
        "description": "Kitchen wall — 2 wide, full-height. Vertical line in right column, horizontal leg to left port at bottom.",
        "tags": ["kitchen", "wall", "h-scalable"],
        "h_segments_fn": lambda h: [[(1.5, h), (1.5, 0.5), (0.0, 0.5)]],
        "h_ports_fn":    lambda h: {"top": [(1.5, h)], "left": [(0.0, 0.5)], "bottom": [], "right": []},
    },

    # ── Bed modules ───────────────────────────────────────────────────────────
    # w=4: fills the full inner zone so the right port connects directly to
    # the corridor (no filler gap between bed and corridor).
    "bed_v1": {
        "id": "bed_v1", "w": 3, "h": 2, "zone": "bed",
        "description": "Compact single bed, 80cm wide — front view cross-section with headboard and right corridor exit.",
        "tags": ["bed", "single", "compact", "80cm", "front-view"],
        "segments": [
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (2.5, 1.5), (2.5, 0.5), (2.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
            [(2.5, 0.5), (3.0, 0.5)],
        ],
        "ports": {"top": [(0.5, 2.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []},
    },
    "bed_v2": {
        "id": "bed_v2", "w": 3, "h": 2, "zone": "bed",
        "description": "Spacious single bed, 100cm wide — front view cross-section with headboard and right corridor exit.",
        "tags": ["bed", "single", "spacious", "100cm", "front-view"],
        "segments": [
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (3.0, 1.5), (3.0, 0.5), (0.5, 0.5), (0.5, 1.5)],
            
        ],
        "ports": {"top": [(0.5, 2.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []},
    },
    "bed_v3": {
        "id": "bed_v3", "w": 4, "h": 2, "zone": "bed",
        "description": "Queen bed, 120cm wide — front view cross-section with headboard and right corridor exit.",
        "tags": ["bed", "queen", "120cm", "front-view"],
        "segments": [
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (3.5, 1.5), (3.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
        
            [(3.5, 0.5), (4.0, 0.5)],
        ],
        "ports": {"top": [(0.5, 2.0)], "right": [(4.0, 0.5)], "bottom": [], "left": []},
    },
    "bed_v4": {
        "id": "bed_v4", "w": 5, "h": 2, "zone": "bed",
        "description": "King bed, 160cm wide — front view cross-section with headboard and right corridor exit.",
        "tags": ["bed", "king", "160cm", "front-view"],
        "segments": [
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (4.5, 1.5), (4.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
            [(5.0, 0.5), (4.5, 0.5)],
        ],
        "ports": {"top": [(0.5, 2.0)], "right": [(5.0, 0.5)], "bottom": [], "left": []},
    },
    "bed_v5": {
        "id": "bed_v5", "w": 6, "h": 2, "zone": "bed",
        "description": "Bed side view — 2D lateral cross-section shared by all 4 bed width variants.",
        "tags": ["bed", "side-view"],
        "segments": [
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (5.5, 1.5), (5.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
            [(6.0, 0.5), (5.5, 0.5)],
        ],
        "ports": {"top": [(0.5, 2.0)], "right": [(6.0, 0.5)], "bottom": [], "left": []},
    },

    # ── 1×1 filler tiles ──────────────────────────────────────────────────────
    "filler_empty": {
        "id": "filler_empty", "w": 1, "h": 1, "zone": "filler",
        "description": "Empty filler tile. No geometry.",
        "tags": ["filler", "empty", "invisible"],
        "segments": [],
        "ports": {"top": [], "bottom": [], "left": [], "right": []},
    },
    "filler_pass_v": {
        "id": "filler_pass_v", "w": 1, "h": 1, "zone": "filler",
        "description": "Vertical pass-through filler.",
        "tags": ["filler", "vertical", "pass-through"],
        "segments": [[(0.5, 0.0), (0.5, 1.0)]],
        "ports": {"top": [(0.5, 1.0)], "bottom": [(0.5, 0.0)], "left": [], "right": []},
    },
    "filler_pass_h": {
        "id": "filler_pass_h", "w": 1, "h": 1, "zone": "filler",
        "description": "Horizontal pass-through filler.",
        "tags": ["filler", "horizontal", "pass-through"],
        "segments": [[(0.0, 0.5), (1.0, 0.5)]],
        "ports": {"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(1.0, 0.5)]},
    },
    "filler_corner_tr": {
        "id": "filler_corner_tr", "w": 1, "h": 1, "zone": "filler",
        "description": "Top-right corner filler — L-segment connecting vertical chain (top) to horizontal chain (right). No floor port.",
        "tags": ["filler", "corner", "top-right"],
        "segments": [[(0.5, 1.0), (0.5, 0.5), (1.0, 0.5)]],
        "ports": {"top": [(0.5, 1.0)], "right": [(1.0, 0.5)], "bottom": [], "left": []},
    },
    "filler_corner_tl": {
        "id": "filler_corner_tl", "w": 1, "h": 1, "zone": "filler",
        "description": "Top-left corner filler — L-segment connecting vertical chain (top) to horizontal chain (left). No floor port.",
        "tags": ["filler", "corner", "top-left"],
        "segments": [[(0.5, 1.0), (0.5, 0.5), (0.0, 0.5)]],
        "ports": {"top": [(0.5, 1.0)], "left": [(0.0, 0.5)], "bottom": [], "right": []},
    },
}

# ── Zone definitions ──────────────────────────────────────────────────────────

ZONES = [
    {
        "id":          "chair_left",
        "description": "Left seating zone. First 2 columns.",
        "tags":        ["seating", "left", "boundary"],
        "x_rule":      ["first 2"],
        "y_rule":      ["first 3", "first 2"],
        "modules": [
            "chair_left_h3_v1", "chair_left_h3_v2", "chair_left_h3_v3",
            "chair_left_h3_v4", "chair_left_h3_v5", "chair_left_h3_v6",
            "chair_left_h2_v1", "chair_left_h2_v2", "chair_left_h2_v3",
        ],
    },
    {
        "id":          "table",
        "description": "Central table zone. Middle 2 columns.",
        "tags":        ["table", "central", "connector"],
        "x_rule":      ["middle 2"],
        "y_rule":      ["first 3", "first 2"],
        "modules": ["table_h3_v1", "table_h3_v2", "table_h3_v3",
                    "table_h2_v1", "table_h2_v2", "table_h2_v3", "table_h2_v4", "table_h2_v5", "table_h2_v6"],
    },
    {
        "id":          "chair_right",
        "description": "Right seating zone. Last 2 columns.",
        "tags":        ["seating", "right", "boundary"],
        "x_rule":      ["last 2"],
        "y_rule":      ["first 3", "first 2"],
        "modules": [
            "chair_right_h3_v1", "chair_right_h3_v2", "chair_right_h3_v3",
            "chair_right_h3_v4", "chair_right_h3_v5", "chair_right_h3_v6",
            "chair_right_h2_v1", "chair_right_h2_v2", "chair_right_h2_v3",
        ],
    },
    {
        "id":          "shelf",
        "description": "Full-width storage zone. h=3 variants occupy last 3 rows; h=4 pitched variants occupy last 4 rows.",
        "tags":        ["shelf", "storage", "full-width", "top"],
        "x_rule":      ["full"],
        "y_rule":      ["last 1", "last 2","last 3", "last 4"],
        "modules": [
            "shelf_h1_v1",
            "shelf_h2_v1", "shelf_h2_v2", "shelf_h2_v3", "shelf_h2_v4", "shelf_h2_v5",
            "shelf_h3_v1", "shelf_h3_v2",
            "shelf_pitched_sym_v1",   "shelf_pitched_sym_v2",
            "shelf_pitched_left_v1",  "shelf_pitched_left_v2",
            "shelf_pitched_right_v1", "shelf_pitched_right_v2",
            "shelf_divided_slanted_left_v1",  "shelf_divided_slanted_left_v2",
            "shelf_divided_slanted_right_v1", "shelf_divided_slanted_right_v2",
        ],
    },
]

# ── Corridor variant factory ──────────────────────────────────────────────────

def _has_endpoint(segments, pt, eps=1e-9):
    return any(
        (abs(seg[0][0] - pt[0]) < eps and abs(seg[0][1] - pt[1]) < eps) or
        (abs(seg[-1][0] - pt[0]) < eps and abs(seg[-1][1] - pt[1]) < eps)
        for seg in segments if seg
    )


def _build_corridor_variants() -> None:
    to_add = {}
    for key, m in list(MODULES.items()):
        if m["zone"] in ("chair_right", "tv_table"):
            xs_at_05 = [p[0] for seg in m["segments"] for p in seg if abs(p[1] - 0.5) < 1e-9]
            if xs_at_05:
                rx = max(xs_at_05)
                if rx < float(m["w"]) - 1e-9:
                    prefix = "chair_right_" if m["zone"] == "chair_right" else "tv_table_"
                    corr_prefix = "chair_right_corr_" if m["zone"] == "chair_right" else "tv_table_corr_"
                    nid = key.replace(prefix, corr_prefix)
                    to_add[nid] = {
                        **m, "id": nid,
                        "segments": m["segments"] + [[(rx, 0.5), (float(m["w"]), 0.5)]],
                        "ports":    {**m["ports"], "right": [(float(m["w"]), 0.5)]},
                    }
        elif m["zone"] in ("chair_left", "sofa"):
            xs_at_05 = [p[0] for seg in m["segments"] for p in seg if abs(p[1] - 0.5) < 1e-9]
            if xs_at_05:
                lx = min(xs_at_05)
                if lx > 0.0 + 1e-9:
                    prefix = "chair_left_" if m["zone"] == "chair_left" else "sofa_"
                    corr_prefix = "chair_left_corr_" if m["zone"] == "chair_left" else "sofa_corr_"
                    nid = key.replace(prefix, corr_prefix)
                    to_add[nid] = {
                        **m, "id": nid,
                        "segments": m["segments"] + [[(lx, 0.5), (0.0, 0.5)]],
                        "ports":    {**m["ports"], "left": [(0.0, 0.5)]},
                    }
        elif m["zone"] == "shelf":
            ref_W  = m["w"]
            ref_segs = m["segments_fn"](ref_W)
            h_top  = m["h"] - 0.5
            if _has_endpoint(ref_segs, (ref_W - 0.5, h_top)):
                nid_r = key + "_corr_r"
                sfn, pfn = m["segments_fn"], m["ports_fn"]
                to_add[nid_r] = {
                    **m, "id": nid_r,
                    "segments_fn": lambda W, _s=sfn, _h=h_top: _s(W) + [[(W - 0.5, _h), (W, _h)]],
                    "ports_fn":    lambda W, _p=pfn, _h=h_top: {**_p(W), "right": [(W, _h)]},
                }
            if _has_endpoint(ref_segs, (0.5, h_top)):
                nid_l = key + "_corr_l"
                sfn, pfn = m["segments_fn"], m["ports_fn"]
                to_add[nid_l] = {
                    **m, "id": nid_l,
                    "segments_fn": lambda W, _s=sfn, _h=h_top: _s(W) + [[(0.5, _h), (0.0, _h)]],
                    "ports_fn":    lambda W, _p=pfn, _h=h_top: {**_p(W), "left": [(0.0, _h)]},
                }
    MODULES.update(to_add)


_build_corridor_variants()


def _build_kitchen_corridor_variants() -> None:
    """
    Build corridor-ready variants of kitchen modules.
    kitchen_wall_corr_r: wall with right stub at y=0.5 (faces corridor_right).
    kitchen_lower_w3_h4_v2: lower cabinet with left stub (faces corridor_left).
    Shelf corridor variants are handled automatically by _build_corridor_variants().
    """
    kw = MODULES["kitchen_wall"]
    kl = MODULES["kitchen_lower_w3_h4_v2"]
    sfn_w = kw["h_segments_fn"]
    pfn_w = kw["h_ports_fn"]

    MODULES["kitchen_wall_corr_r"] = {
        **kw, "id": "kitchen_wall_corr_r",
        "h_segments_fn": lambda h, _s=sfn_w: _s(h) + [[(1.5, 0.5), (2.0, 0.5)]],
        "h_ports_fn":    lambda h, _p=pfn_w: {**_p(h), "right": [(2.0, 0.5)]},
    }


_build_kitchen_corridor_variants()

# ── Corridor zone configurations ──────────────────────────────────────────────

_CL_CORR   = [m.replace("chair_left_",  "chair_left_corr_")  for m in ZONES[0]["modules"]
               if m.replace("chair_left_",  "chair_left_corr_")  in MODULES]
_CR_CORR   = [m.replace("chair_right_", "chair_right_corr_") for m in ZONES[2]["modules"]
               if m.replace("chair_right_", "chair_right_corr_") in MODULES]
_SH_CORR_R = [m + "_corr_r" for m in ZONES[3]["modules"] if m + "_corr_r" in MODULES]
_SH_CORR_L = [m + "_corr_l" for m in ZONES[3]["modules"] if m + "_corr_l" in MODULES]

# ── Full-roof corridor zone configs ───────────────────────────────────────────
# Shelf is placed separately by the solver (full section width, above the short
# corridor). chair_right_corr / chair_left_corr variants have the extra stub that
# matches the short corridor's boundary port.
ZONES_FULL_ROOF_CORR_RIGHT = [ZONES[0], ZONES[1], {**ZONES[2], "modules": _CR_CORR}]
ZONES_FULL_ROOF_CORR_LEFT  = [{**ZONES[0], "modules": _CL_CORR}, ZONES[1], ZONES[2]]

# 1-chair variants: single chair + table, no second chair; table shifted flush
# against the corridor boundary.
ZONES_FULL_ROOF_CORR_RIGHT_1CHAIR = [
    ZONES[0],                            # chair_left at "first 2"
    {**ZONES[1], "x_rule": ["last 2"]},  # table at "last 2" (adj to corridor)
]
ZONES_FULL_ROOF_CORR_LEFT_1CHAIR = [
    {**ZONES[1], "x_rule": ["first 2"]}, # table at "first 2" (adj to corridor)
    ZONES[2],                            # chair_right at "last 2"
]

# No-corridor 1-chair variant: chair_left + table + shelf, table shifted to "last 2"
# so chair and table don't share columns (needed when inner_W < 6, e.g. W=4 solo).
ZONES_1CHAIR = [
    ZONES[0],                            # chair_left at "first 2"
    {**ZONES[1], "x_rule": ["last 2"]},  # table at "last 2"
    ZONES[3],                            # shelf at "full"
]

# ── Table module groups ───────────────────────────────────────────────────────
# Compact (no wide-top): chairs flush against table, dining zone = 6 cols.
# Spacious (wide-top):   1-col filler gap each side, dining zone = 8 cols.
_TABLE_COMPACT  = [m for m in ZONES[1]["modules"] if "wide-top" not in MODULES[m]["tags"]]
_TABLE_SPACIOUS = [m for m in ZONES[1]["modules"] if "wide-top"     in MODULES[m]["tags"]]

# Living coffee-table groups — same wide-top split, applied to LIVING_ZONES table zone.
# Compact (inner_W=7): sofa+table+tv_table flush, table at "from 3 size 2".
# Spacious (inner_W=9): 1-col gap each side, table at "from 4 size 2".

# ── Shelf style groups (for roof_style filter) ───────────────────────────────
# plain:   flat horizontal bar — dry/arid climates
# divided: internal subdivisions or hatching — temperate/moderate climates
# pitched: symmetric gable ridge — cold/snowy/polar/alpine climates
# slanted: lean-to directional — rainy/oceanic/tropical climates
_SHELF_PLANE   = ["shelf_h1_v1", "shelf_h2_v1"]
_SHELF_DIVIDED = ["shelf_h3_v1", "shelf_h3_v2", "shelf_h2_v4", "shelf_h2_v5"]
_SHELF_PITCHED = [
    "shelf_pitched_sym_v1",
]
_SHELF_SLANTED = []
_SHELF_DIVIDED_SLANTED = [
    "shelf_divided_slanted_left_v1",  "shelf_divided_slanted_left_v2",
    "shelf_divided_slanted_right_v1", "shelf_divided_slanted_right_v2",
]

# Maps base module ID (without _corr_r/_corr_l) → category string
_SHELF_CATEGORY: dict = {
    **{m: "plain"           for m in _SHELF_PLANE},
    **{m: "divided"         for m in _SHELF_DIVIDED},
    **{m: "pitched"         for m in _SHELF_PITCHED},
    **{m: "slanted"         for m in _SHELF_SLANTED},
    **{m: "divided_slanted" for m in _SHELF_DIVIDED_SLANTED},
}

# ── Kitchen zone configurations ───────────────────────────────────────────────

# Inner zones (no shelf) — used in full-roof corridor path.
# upper_cabinet uses "from 3 to last 0" so it adapts to any H_solve.
# kitchen_wall uses "full" so it spans all of H_solve.
KITCHEN_ZONES_INNER = [
    {"id": "lower_cabinet", "x_rule": ["first 3"], "y_rule": ["first 3"],          "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"]},
    {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 0"], "modules": ["kitchen_upper_w2_h1", "kitchen_upper_w2_h1_wide", "kitchen_upper_w2_h2", "kitchen_upper_w2_h2_wide", "kitchen_upper_w2_h3", "kitchen_upper_w2_h3_wide", "kitchen_upper_w2_h4", "kitchen_upper_w2_h4_wide"]},
    {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["full"],              "modules": ["corridor_right_short"]},
]

KITCHEN_ZONES_INNER_CORR_RIGHT = [
    KITCHEN_ZONES_INNER[0],
    KITCHEN_ZONES_INNER[1],
    {**KITCHEN_ZONES_INNER[2], "modules": ["corridor_right_short"]},
]

# W=8 variant (inner_W=6): double-sided counter — left bank + right bank (through).
# Left bank: right exit at x=3.0 joins right bank left exit. Right bank through-module
# also exits right to corridor at x=6.0. Top port at x=2.5 starts filler chain to FRS shelf.
KITCHEN_ZONES_INNER_W6 = [
    {"id": "lower_cabinet",   "x_rule": ["first 3"],       "y_rule": ["first 3"],          "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"]},
    {"id": "lower_cabinet_r", "x_rule": ["from 3 size 3"], "y_rule": ["first 3"],          "modules": ["kitchen_lower_w3_h4_through"]},
    {"id": "upper_cabinet",   "x_rule": ["first 2"],       "y_rule": ["from 3 to last 0"], "modules": ["kitchen_upper_w2_h1", "kitchen_upper_w2_h1_wide", "kitchen_upper_w2_h2", "kitchen_upper_w2_h2_wide", "kitchen_upper_w2_h3", "kitchen_upper_w2_h3_wide", "kitchen_upper_w2_h4", "kitchen_upper_w2_h4_wide"]},
]

KITCHEN_ZONES_INNER_CORR_LEFT = [
    {**KITCHEN_ZONES_INNER[0], "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"]},
    KITCHEN_ZONES_INNER[1],
    KITCHEN_ZONES_INNER[2],
]

KITCHEN_ZONES = [
    {
        "id":      "shelf",
        "x_rule":  ["full"],
        "y_rule":  ["last 1"],
        "modules": ["shelf_h1_v1"],
    },
    {
        "id":      "lower_cabinet",
        "x_rule":  ["first 3"],
        "y_rule":  ["first 3"],
        "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"],
    },
    {
        "id":      "upper_cabinet",
        "x_rule":  ["first 2"],
        "y_rule":  ["from 3 size 3"],
        "modules": ["kitchen_upper_w2_h1", "kitchen_upper_w2_h1_wide", "kitchen_upper_w2_h2", "kitchen_upper_w2_h2_wide", "kitchen_upper_w2_h3", "kitchen_upper_w2_h3_wide", "kitchen_upper_w2_h4", "kitchen_upper_w2_h4_wide"],
    },
    {
        "id":      "kitchen_wall",
        "x_rule":  ["last 2"],
        "y_rule":  ["skip last 1"],
        "modules": ["corridor_right_short"],
    },
]

KITCHEN_ZONES_CORR_RIGHT = [
    {**KITCHEN_ZONES[0], "modules": ["shelf_h1_v1_corr_r"]},
    KITCHEN_ZONES[1],
    KITCHEN_ZONES[2],
    {**KITCHEN_ZONES[3], "modules": ["corridor_right_short"]},
]

KITCHEN_ZONES_CORR_LEFT = [
    {**KITCHEN_ZONES[0], "modules": ["shelf_h1_v1_corr_l"]},
    {**KITCHEN_ZONES[1], "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"]},
    KITCHEN_ZONES[2],
    KITCHEN_ZONES[3],
]

# ── Kitchen shelf scenario configurations (taller variants per seed/height) ───
# H>=8: h=2 shelves (lean, pitched, asymmetric) in last 2 rows.
# H>=9: h=3 shelves (divided, steep lean) in last 3 rows.
_KZ_LOWER       = KITCHEN_ZONES[1]
_KZ_UPPER_TO_H2 = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 2"], "modules": ["kitchen_upper_w2_h1", "kitchen_upper_w2_h1_wide", "kitchen_upper_w2_h2", "kitchen_upper_w2_h2_wide", "kitchen_upper_w2_h3", "kitchen_upper_w2_h3_wide", "kitchen_upper_w2_h4", "kitchen_upper_w2_h4_wide"]}
_KZ_UPPER_TO_H3 = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 3"], "modules": ["kitchen_upper_w2_h1", "kitchen_upper_w2_h1_wide", "kitchen_upper_w2_h2", "kitchen_upper_w2_h2_wide", "kitchen_upper_w2_h3", "kitchen_upper_w2_h3_wide", "kitchen_upper_w2_h4", "kitchen_upper_w2_h4_wide"]}
_KZ_WALL_H2     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 2"],       "modules": ["corridor_right_short"]}
_KZ_WALL_H3     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 3"],       "modules": ["corridor_right_short"]}

_KITCHEN_SHELF_H2 = [
    "shelf_h2_v1", "shelf_h2_v2", "shelf_h2_v3", "shelf_h2_v4",
    "shelf_pitched_sym_v1", "shelf_pitched_sym_v2",
    "shelf_pitched_left_v1", "shelf_pitched_left_v2",
    "shelf_pitched_right_v1", "shelf_pitched_right_v2",
]
_KITCHEN_SHELF_H3 = ["shelf_h3_v1", "shelf_h3_v2"]

_KITCHEN_SHELF_H2_CORR_R = [m + "_corr_r" for m in _KITCHEN_SHELF_H2 if m + "_corr_r" in MODULES]
_KITCHEN_SHELF_H2_CORR_L = [m + "_corr_l" for m in _KITCHEN_SHELF_H2 if m + "_corr_l" in MODULES]
_KITCHEN_SHELF_H3_CORR_R = [m + "_corr_r" for m in _KITCHEN_SHELF_H3 if m + "_corr_r" in MODULES]
_KITCHEN_SHELF_H3_CORR_L = [m + "_corr_l" for m in _KITCHEN_SHELF_H3 if m + "_corr_l" in MODULES]

KITCHEN_ZONES_SHELF_H2 = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 2"], "modules": _KITCHEN_SHELF_H2},
    _KZ_LOWER, _KZ_UPPER_TO_H2, _KZ_WALL_H2,
]
KITCHEN_ZONES_SHELF_H3 = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 3"], "modules": _KITCHEN_SHELF_H3},
    _KZ_LOWER, _KZ_UPPER_TO_H3, _KZ_WALL_H3,
]
KITCHEN_ZONES_CORR_RIGHT_SHELF_H2 = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 2"], "modules": _KITCHEN_SHELF_H2_CORR_R},
    _KZ_LOWER, _KZ_UPPER_TO_H2, {**_KZ_WALL_H2, "modules": ["corridor_right_short"]},
]
KITCHEN_ZONES_CORR_LEFT_SHELF_H2 = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 2"], "modules": _KITCHEN_SHELF_H2_CORR_L},
    {**_KZ_LOWER, "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"]}, _KZ_UPPER_TO_H2, _KZ_WALL_H2,
]
KITCHEN_ZONES_CORR_RIGHT_SHELF_H3 = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 3"], "modules": _KITCHEN_SHELF_H3_CORR_R},
    _KZ_LOWER, _KZ_UPPER_TO_H3, {**_KZ_WALL_H3, "modules": ["corridor_right_short"]},
]
KITCHEN_ZONES_CORR_LEFT_SHELF_H3 = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 3"], "modules": _KITCHEN_SHELF_H3_CORR_L},
    {**_KZ_LOWER, "modules": ["kitchen_lower_w3_h4_v2", "kitchen_lower_w3_h4_v3"]}, _KZ_UPPER_TO_H3, _KZ_WALL_H3,
]

# ── Living zone configurations ────────────────────────────────────────────────
# sofa ≡ chair_left (left zone), tv_table ≡ chair_right (right zone).
# Living is 8 cols wide; sofa/table/tv_table each occupy 2 cols with filler gaps.
_SOFA_CORR_L    = [m for m in ["sofa_corr_h3_v1"] if m in MODULES]
_TV_CORR_R      = [m for m in MODULES if m.startswith("tv_table_corr_")]

LIVING_ZONES = [
    {
        "id": "sofa", "x_rule": ["first 4", "first 3", "first 2"], "y_rule": ["first 3", "first 2"],
        "modules": ["sofa_h3_v4", "sofa_h3_v3", "sofa_h3_v2", "sofa_h3_v1"],
    },
    {
        "id": "table", "x_rule": ["middle 2"], "y_rule": ["first 2"],
        "modules": [
                    "table_h2_v1", "table_h2_v2", "table_h2_v3",
                    "table_h2_v4", "table_h2_v5", "table_h2_v6"],
    },
    {
        "id": "tv_table", "x_rule": ["last 2"], "y_rule": ["first 2"],
        "modules": ["tv_table_h2_v1", "tv_table_h2_v2", "tv_table_h2_v3"],
    },
    {
        "id": "shelf", "x_rule": ["full"], "y_rule": ["last 1", "last 2", "last 3", "last 4"],
        "modules": ZONES[3]["modules"],
    },
]

_TABLE_COMPACT_LIVING  = [m for m in LIVING_ZONES[1]["modules"] if "wide-top" not in MODULES[m]["tags"]]
_TABLE_SPACIOUS_LIVING = [m for m in LIVING_ZONES[1]["modules"] if "wide-top"     in MODULES[m]["tags"]]

LIVING_ZONES_CORR_RIGHT = [
    LIVING_ZONES[0],
    LIVING_ZONES[1],
    {**LIVING_ZONES[2], "modules": _TV_CORR_R or ["tv_table_h2_v1"]},
    {**LIVING_ZONES[3], "modules": _SH_CORR_R},
]

LIVING_ZONES_CORR_LEFT = [
    {**LIVING_ZONES[0], "modules": _SOFA_CORR_L or ["sofa_h3_v1"]},
    LIVING_ZONES[1],
    LIVING_ZONES[2],
    {**LIVING_ZONES[3], "modules": _SH_CORR_L},
]

# Inner zones (no shelf) — for full-roof corridor path.
LIVING_ZONES_INNER = [LIVING_ZONES[0], LIVING_ZONES[1], LIVING_ZONES[2]]

LIVING_ZONES_INNER_CORR_RIGHT = [
    LIVING_ZONES[0],  # sofa
    LIVING_ZONES[1],  # table; no tv_table — overlaps table at inner_W=6
]

LIVING_ZONES_INNER_CORR_LEFT = [
    {**LIVING_ZONES[0], "modules": _SOFA_CORR_L or ["sofa_h3_v1"]},
    LIVING_ZONES[1],  # table; no tv_table
]

# ── Living sub-combination zone configs ──────────────────────────────────────

_LZ_SOFA  = LIVING_ZONES[0]
_LZ_SHELF = LIVING_ZONES[3]

# sofa + tv_table (no corridor) — tv_table has no right port, works at last 2
LIVING_ZONES_SOFA_TV = [
    _LZ_SOFA,
    {"id": "tv_table", "x_rule": ["last 2"], "y_rule": ["first 2"],
     "modules": ["tv_table_h2_v1", "tv_table_h2_v2", "tv_table_h2_v3"]},
    _LZ_SHELF,
]

# sofa + tv_table with corridor right — tv_table corr_r absorbs corridor left port
LIVING_ZONES_SOFA_TV_CORR_RIGHT = [
    _LZ_SOFA,
    {"id": "tv_table", "x_rule": ["last 2"], "y_rule": ["first 2"],
     "modules": _TV_CORR_R or ["tv_table_h2_v1"]},
    {**_LZ_SHELF, "modules": _SH_CORR_R},
]
LIVING_ZONES_SOFA_TV_INNER_CORR_RIGHT = [
    _LZ_SOFA,
    {"id": "tv_table", "x_rule": ["last 2"], "y_rule": ["first 2"],
     "modules": _TV_CORR_R or ["tv_table_h2_v1"]},
]

# ── Bed zone configuration ────────────────────────────────────────────────────
# Shelf is always pre-placed by the solver; only the bed zone is solved here.
BED_ZONES_INNER = [
    {"id": "bed", "x_rule": ["first 6"],
     "y_rule": ["first 2"],
     "modules": ["bed_v5"]},
]

# Used by drawing.py to order zones in the module library view
ZONE_ORDER = [
    "chair_left", "chair_right", "sofa", "tv_table", "table",
    "lower_cabinet", "upper_cabinet", "bed", "shelf",
    "corridor_left", "corridor_right", "filler",
]
