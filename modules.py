from typing import Dict

# ── Constants ─────────────────────────────────────────────────────────────────
EPS = 1e-9
LINE_COLOR  = "#cc2200"
PORT_COLOR  = "#009900"
GRID_COLOR  = "#aaaaaa"
ZONE_COLORS = {
    "chair_left":     "#fde9a2",
    "chair_right":    "#fde9a2",
    "table":          "#d0e8d0",
    "shelf":          "#ac2e2e",
    "corridor_left":  "#b0c4de",
    "corridor_right": "#b0c4de",
    "filler":         "#e0e0e0",
}

# ── Module Library ────────────────────────────────────────────────────────────
# Local coordinates: origin at bottom-left of module, x→right, y→up, 1 unit = 1 cell.
# segments : list of polylines [(x,y), ...] — for drawing only
# ports     : dict edge → [(x,y)] — boundary midpoints where lines exit the module


def _lean_segs(w: int, H: int, side: str, drop: float) -> list:
    """
    Circuit-valid segments for a lean-to corridor.
    Inner wall (dining side) top = H-0.5; outer wall top = H-0.5-drop.
    drop controls visible slope variation across v1/v2/v3 variants.
    """
    outer_y = H - 0.5 - drop
    if side == "right":
        return [
            [(0.0, 0.5),         (w - 0.5, 0.5)],
            [(w - 0.5, 0.5),     (w - 0.5, outer_y)],
            [(w - 0.5, outer_y), (0.0, H - 0.5)],
        ]
    else:
        return [
            [(w, 0.5),       (0.5, 0.5)],
            [(0.5, 0.5),     (0.5, outer_y)],
            [(0.5, outer_y), (w, H - 0.5)],
        ]


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
        "description": "Table, height 2. Two diagonals meet at a central V-tip below a mid-height horizontal bar.",
        "tags": ["v-tip", "symmetric", "h2"],
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
        "description": "Table, height 2. V-tip legs reach up to a horizontal bar near the top.",
        "tags": ["v-tip", "tall-bar", "h2"],
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
        "description": "Table, height 2. Rectangular frame with two straight vertical legs, each foot running to the side port.",
        "tags": ["rectilinear", "h2"],
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
        "description": "Table, height 2. Tall rectangular frame with the top bar at maximum height, legs run to side ports.",
        "tags": ["rectilinear", "tall-bar", "h2"],
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
        "description": "Table, height 2. Full-width top bar with inward-diagonal legs that splay back out to the side ports.",
        "tags": ["diagonal", "wide-top", "h2"],
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
        "description": "Table, height 2. Full-width top bar at maximum height with diagonal legs splaying to side ports.",
        "tags": ["diagonal", "wide-top", "tall-bar", "h2"],
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

    #-------Shelf_Modules------------------------------------------------------

    "shelf_h3_v1": {
        "id": "shelf_h3_v1", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. Simple U-bracket: two side posts and a top bar. Minimal open storage profile.",
        "tags": ["minimal", "u-bracket", "open"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.5)],
            [(W-0.5, 0.0), (W-0.5, 2.5)],
            [(0.5, 2.5), (W-0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v2": {
        "id": "shelf_h3_v2", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. U-bracket with a horizontal mid-shelf, creating two storage levels.",
        "tags": ["u-bracket", "two-level"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.5)],
            [(W-0.5, 0.0), (W-0.5, 2.5)],
            [(0.5, 2.5), (W-0.5, 2.5)],
            [(0.5, 1.5), (W-0.5, 1.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v3": {
        "id": "shelf_h3_v3", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
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
    "shelf_h3_v4": {
        "id": "shelf_h3_v4", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. Asymmetric: tall left post, shorter right post, connected by a diagonal top bar.",
        "tags": ["asymmetric", "diagonal"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.5)],
            [(W-0.5, 0.0), (W-0.5, 1.5)],
            [(0.5, 2.5), (W-0.5, 1.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v5": {
        "id": "shelf_h3_v5", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. Asymmetric: short left post, taller right post, connected by a diagonal top bar.",
        "tags": ["asymmetric", "diagonal"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 2.5)],
            [(0.5, 1.5), (W-0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v6": {
        "id": "shelf_h3_v6", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. U-bracket with two horizontal shelves — three storage levels.",
        "tags": ["u-bracket", "three-level", "detailed"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.5), (0.5, 2.5)],
            [(W-0.5, 0.0), (W-0.5, 1.5), (W-0.5, 2.5)],
            [(0.5, 1.5), (W-0.5, 1.5)],
            [(0.5, 2.5), (W-0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v7": {
        "id": "shelf_h3_v7", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Shelf, height 3. Small compartment on the left, multiple evenly-spaced bays filling the right section.",
        "tags": ["divided", "multi-bay", "complex"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.5)],
            [(W-0.5, 0.0), (W-0.5, 1.5)],
            [(0.5, 1.5), (1.5, 1.5), (1.5, 2.5), (0.5, 2.5), (0.5, 1.5)],
            [(1.5+i, 1.5) for i in range(W-1)] + [(W-0.5-i, 2.5) for i in range(W-1)] + [(1.5, 1.5)],
        ] + [[(1.5+i, 1.5), (1.5+i, 2.5)] for i in range(1, W-2)],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_h3_v8": {
        "id": "shelf_h3_v8", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
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
        "id": "shelf_pitched_sym_v1", "w": 6, "h": 4, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, centred ridge, steep slope. Eave at y=3, ridge at y=4.",
        "tags": ["pitched", "symmetric", "steep"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 3.0)],
            [(W-0.5, 0.0), (W-0.5, 3.0)],
            [(0.5, 3.0), (W/2, 4.0), (W-0.5, 3.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_sym_v2": {
        "id": "shelf_pitched_sym_v2", "w": 6, "h": 4, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, centred ridge, gentle slope. Eave at y=3, ridge at y=3.5.",
        "tags": ["pitched", "symmetric", "gentle"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 3.0)],
            [(W-0.5, 0.0), (W-0.5, 3.0)],
            [(0.5, 3.0), (W/2, 3.5), (W-0.5, 3.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_left_v1": {
        "id": "shelf_pitched_left_v1", "w": 6, "h": 4, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, left-biased ridge, steep slope.",
        "tags": ["pitched", "left-biased", "steep"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 3.0)],
            [(W-0.5, 0.0), (W-0.5, 3.0)],
            [(0.5, 3.0), (W/3, 4.0), (W-0.5, 3.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_left_v2": {
        "id": "shelf_pitched_left_v2", "w": 6, "h": 4, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, left-biased ridge, gentle slope.",
        "tags": ["pitched", "left-biased", "gentle"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 3.0)],
            [(W-0.5, 0.0), (W-0.5, 3.0)],
            [(0.5, 3.0), (W/3, 3.5), (W-0.5, 3.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_right_v1": {
        "id": "shelf_pitched_right_v1", "w": 6, "h": 4, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, right-biased ridge, steep slope.",
        "tags": ["pitched", "right-biased", "steep"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 3.0)],
            [(W-0.5, 0.0), (W-0.5, 3.0)],
            [(0.5, 3.0), (2*W/3, 4.0), (W-0.5, 3.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_pitched_right_v2": {
        "id": "shelf_pitched_right_v2", "w": 6, "h": 4, "zone": "shelf", "scalable": True,
        "description": "Pitched roof, right-biased ridge, gentle slope.",
        "tags": ["pitched", "right-biased", "gentle"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 3.0)],
            [(W-0.5, 0.0), (W-0.5, 3.0)],
            [(0.5, 3.0), (2*W/3, 3.5), (W-0.5, 3.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },

    # ── Lean-to shelf slope variants ─────────────────────────────────────────
    # Three slopes for each lean direction (right-rising and left-rising).
    # Eave heights are fixed; slope = (high_eave - low_eave) / (W - 1).
    # _build_corridor_variants() auto-generates _corr_r for right-rising variants
    # (right post endpoint at y=2.5) and _corr_l for left-rising variants.

    # ── lean right: low-left → high-right (right eave fixed at y=2.5) ────────
    "shelf_lean_r_gentle": {
        "id": "shelf_lean_r_gentle", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Lean-to shelf, gentle rise left→right. Left eave y=2.0, right eave y=2.5.",
        "tags": ["lean-to", "pitched", "gentle", "right-rise"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.0)],
            [(W - 0.5, 0.0), (W - 0.5, 2.5)],
            [(0.5, 2.0), (W - 0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W - 0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_lean_r_steep": {
        "id": "shelf_lean_r_steep", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Lean-to shelf, steep rise left→right. Left eave y=0.5, right eave y=2.5.",
        "tags": ["lean-to", "pitched", "steep", "right-rise"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 0.5)],
            [(W - 0.5, 0.0), (W - 0.5, 2.5)],
            [(0.5, 0.5), (W - 0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W - 0.5, 0.0)], "left": [], "right": []},
    },

    # ── lean left: high-left → low-right (left eave fixed at y=2.5) ──────────
    "shelf_lean_l_gentle": {
        "id": "shelf_lean_l_gentle", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Lean-to shelf, gentle rise right→left. Left eave y=2.5, right eave y=2.0.",
        "tags": ["lean-to", "pitched", "gentle", "left-rise"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.5)],
            [(W - 0.5, 0.0), (W - 0.5, 2.0)],
            [(0.5, 2.5), (W - 0.5, 2.0)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W - 0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_lean_l_steep": {
        "id": "shelf_lean_l_steep", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Lean-to shelf, steep rise right→left. Left eave y=2.5, right eave y=0.5.",
        "tags": ["lean-to", "pitched", "steep", "left-rise"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.5)],
            [(W - 0.5, 0.0), (W - 0.5, 0.5)],
            [(0.5, 2.5), (W - 0.5, 0.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W - 0.5, 0.0)], "left": [], "right": []},
    },

    # ── Narrow-mode shelf modules ─────────────────────────────────────────────
    # Used in 1-chair mode: one side is above the chair (open bay, post to floor),
    # the other side is above the table (no floor connection allowed — table has no
    # top port). The table side uses a CLOSED BRACKET instead of an open post:
    # a 1-unit-wide closed rectangle that visually reads as a supported end without
    # needing a floor port. All bracket vertices have degree ≥ 2 (closed loop).
    # The corr stub at y=2.5 is added by _build_corridor_variants() as usual.

    # shelf_narrow_r: chair on left, table on right (corridor_right narrow mode)
    "shelf_narrow_r_v1": {
        "id": "shelf_narrow_r_v1", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Narrow shelf: open bay (left post) over chair, closed bracket over table.",
        "tags": ["shelf", "narrow", "bracket", "right-corridor"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 2.5)],
            [(0.5, 2.5), (W - 0.5, 2.5)],
            [(W - 0.5, 2.5), (W - 0.5, 1.0), (W - 1.5, 1.0), (W - 1.5, 2.5), (W - 0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_narrow_r_v2": {
        "id": "shelf_narrow_r_v2", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Narrow shelf: open bay with mid-level shelf over chair, closed bracket over table.",
        "tags": ["shelf", "narrow", "two-level", "bracket", "right-corridor"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.5), (0.5, 2.5)],
            [(0.5, 2.5), (W - 0.5, 2.5)],
            [(0.5, 1.5), (W - 0.5, 1.5)],
            [(W - 0.5, 2.5), (W - 0.5, 1.5), (W - 0.5, 1.0), (W - 1.5, 1.0), (W - 1.5, 2.5), (W - 0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_narrow_r_v3": {
        "id": "shelf_narrow_r_v3", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Narrow shelf: open bay with diagonal brace over chair, closed bracket over table.",
        "tags": ["shelf", "narrow", "diagonal", "bracket", "right-corridor"],
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0), (0.5, 2.5)],
            [(0.5, 2.5), (W - 0.5, 2.5)],
            [(0.5, 1.0), (W - 1.5, 2.5)],
            [(W - 0.5, 2.5), (W - 0.5, 1.0), (W - 1.5, 1.0), (W - 1.5, 2.5), (W - 0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0)], "left": [], "right": []},
    },

    # shelf_narrow_l: table on left, chair on right (corridor_left narrow mode)
    "shelf_narrow_l_v1": {
        "id": "shelf_narrow_l_v1", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Narrow shelf: closed bracket over table, open bay (right post) over chair.",
        "tags": ["shelf", "narrow", "bracket", "left-corridor"],
        "segments_fn": lambda W: [
            [(W - 0.5, 0.0), (W - 0.5, 2.5)],
            [(0.5, 2.5), (W - 0.5, 2.5)],
            [(0.5, 2.5), (0.5, 1.0), (1.5, 1.0), (1.5, 2.5), (0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(W - 0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_narrow_l_v2": {
        "id": "shelf_narrow_l_v2", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Narrow shelf: closed bracket over table, open bay with mid-level shelf over chair.",
        "tags": ["shelf", "narrow", "two-level", "bracket", "left-corridor"],
        "segments_fn": lambda W: [
            [(W - 0.5, 0.0), (W - 0.5, 1.5), (W - 0.5, 2.5)],
            [(0.5, 2.5), (W - 0.5, 2.5)],
            [(0.5, 1.5), (W - 0.5, 1.5)],
            [(0.5, 2.5), (0.5, 1.5), (0.5, 1.0), (1.5, 1.0), (1.5, 2.5), (0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(W - 0.5, 0.0)], "left": [], "right": []},
    },
    "shelf_narrow_l_v3": {
        "id": "shelf_narrow_l_v3", "w": 6, "h": 3, "zone": "shelf", "scalable": True,
        "description": "Narrow shelf: closed bracket over table, open bay with diagonal brace over chair.",
        "tags": ["shelf", "narrow", "diagonal", "bracket", "left-corridor"],
        "segments_fn": lambda W: [
            [(W - 0.5, 0.0), (W - 0.5, 1.0), (W - 0.5, 2.5)],
            [(0.5, 2.5), (W - 0.5, 2.5)],
            [(W - 0.5, 1.0), (1.5, 2.5)],
            [(0.5, 2.5), (0.5, 1.0), (1.5, 1.0), (1.5, 2.5), (0.5, 2.5)],
        ],
        "ports_fn": lambda W: {"top": [], "bottom": [(W - 0.5, 0.0)], "left": [], "right": []},
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

    # ── Lean-to corridor modules ──────────────────────────────────────────────
    # Inner wall (dining side) top = H-0.5 (high port, connects to shelf eave).
    # Outer wall tops at max(H-0.5-drop, 6.0) — never lower than y=6.
    # Three drop variants give different slopes; solver picks randomly by seed.
    # All share identical ports with the standard corridor so zone rules are
    # reused without change.
    "corridor_right_lean_v1": {
        "id": "corridor_right_lean_v1", "w": 2, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Corridor right, lean-to — gentle slope (outer drops 1 unit below inner).",
        "tags": ["corridor", "circulation", "h-scalable", "right-side", "lean-to"],
        "wh_segments_fn": lambda w, H: _lean_segs(w, H, "right", 1.0),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [(0.0, 0.5), (0.0, H - 0.5)], "right": []},
    },
    "corridor_right_lean_v2": {
        "id": "corridor_right_lean_v2", "w": 2, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Corridor right, lean-to — medium slope (outer drops 2 units below inner).",
        "tags": ["corridor", "circulation", "h-scalable", "right-side", "lean-to"],
        "wh_segments_fn": lambda w, H: _lean_segs(w, H, "right", 2.0),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [(0.0, 0.5), (0.0, H - 0.5)], "right": []},
    },
    "corridor_right_lean_v3": {
        "id": "corridor_right_lean_v3", "w": 2, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Corridor right, lean-to — steep slope (outer drops 3 units below inner).",
        "tags": ["corridor", "circulation", "h-scalable", "right-side", "lean-to"],
        "wh_segments_fn": lambda w, H: _lean_segs(w, H, "right", 3.0),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [(0.0, 0.5), (0.0, H - 0.5)], "right": []},
    },
    "corridor_left_lean_v1": {
        "id": "corridor_left_lean_v1", "w": 2, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Corridor left, lean-to — gentle slope (outer drops 1 unit below inner).",
        "tags": ["corridor", "circulation", "h-scalable", "left-side", "lean-to"],
        "wh_segments_fn": lambda w, H: _lean_segs(w, H, "left", 1.0),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [], "right": [(w, 0.5), (w, H - 0.5)]},
    },
    "corridor_left_lean_v2": {
        "id": "corridor_left_lean_v2", "w": 2, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Corridor left, lean-to — medium slope (outer drops 2 units below inner).",
        "tags": ["corridor", "circulation", "h-scalable", "left-side", "lean-to"],
        "wh_segments_fn": lambda w, H: _lean_segs(w, H, "left", 2.0),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [], "right": [(w, 0.5), (w, H - 0.5)]},
    },
    "corridor_left_lean_v3": {
        "id": "corridor_left_lean_v3", "w": 2, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Corridor left, lean-to — steep slope (outer drops 3 units below inner).",
        "tags": ["corridor", "circulation", "h-scalable", "left-side", "lean-to"],
        "wh_segments_fn": lambda w, H: _lean_segs(w, H, "left", 3.0),
        "wh_ports_fn":    lambda w, H: {"top": [], "bottom": [], "left": [], "right": [(w, 0.5), (w, H - 0.5)]},
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
        "y_rule":      ["last 3", "last 4"],
        "modules": [
            "shelf_h3_v1", "shelf_h3_v2", "shelf_h3_v3", "shelf_h3_v4",
            "shelf_h3_v5", "shelf_h3_v6", "shelf_h3_v7", "shelf_h3_v8",
            "shelf_lean_r_gentle", "shelf_lean_r_steep",
            "shelf_lean_l_gentle", "shelf_lean_l_steep",
            "shelf_pitched_sym_v1",   "shelf_pitched_sym_v2",
            "shelf_pitched_left_v1",  "shelf_pitched_left_v2",
            "shelf_pitched_right_v1", "shelf_pitched_right_v2",
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
        if m["zone"] == "chair_right":
            xs_at_05 = [p[0] for seg in m["segments"] for p in seg if abs(p[1] - 0.5) < 1e-9]
            if xs_at_05:
                rx = max(xs_at_05)
                if rx < 2.0 - 1e-9:
                    nid = key.replace("chair_right_", "chair_right_corr_")
                    to_add[nid] = {
                        **m, "id": nid,
                        "segments": m["segments"] + [[(rx, 0.5), (2.0, 0.5)]],
                        "ports":    {**m["ports"], "right": [(2.0, 0.5)]},
                    }
        elif m["zone"] == "chair_left":
            xs_at_05 = [p[0] for seg in m["segments"] for p in seg if abs(p[1] - 0.5) < 1e-9]
            if xs_at_05:
                lx = min(xs_at_05)
                if lx > 0.0 + 1e-9:
                    nid = key.replace("chair_left_", "chair_left_corr_")
                    to_add[nid] = {
                        **m, "id": nid,
                        "segments": m["segments"] + [[(lx, 0.5), (0.0, 0.5)]],
                        "ports":    {**m["ports"], "left": [(0.0, 0.5)]},
                    }
        elif m["zone"] == "shelf":
            ref_W    = m["w"]
            ref_segs = m["segments_fn"](ref_W)
            if _has_endpoint(ref_segs, (ref_W - 0.5, 2.5)):
                nid_r = key + "_corr_r"
                sfn, pfn = m["segments_fn"], m["ports_fn"]
                to_add[nid_r] = {
                    **m, "id": nid_r,
                    "segments_fn": lambda W, _s=sfn: _s(W) + [[(W - 0.5, 2.5), (W, 2.5)]],
                    "ports_fn":    lambda W, _p=pfn: {**_p(W), "right": [(W, 2.5)]},
                }
            if _has_endpoint(ref_segs, (0.5, 2.5)):
                nid_l = key + "_corr_l"
                sfn, pfn = m["segments_fn"], m["ports_fn"]
                to_add[nid_l] = {
                    **m, "id": nid_l,
                    "segments_fn": lambda W, _s=sfn: _s(W) + [[(0.5, 2.5), (0.0, 2.5)]],
                    "ports_fn":    lambda W, _p=pfn: {**_p(W), "left": [(0.0, 2.5)]},
                }
    MODULES.update(to_add)


_build_corridor_variants()

# ── Corridor zone configurations ──────────────────────────────────────────────

_CL_CORR   = [m.replace("chair_left_",  "chair_left_corr_")  for m in ZONES[0]["modules"]
               if m.replace("chair_left_",  "chair_left_corr_")  in MODULES]
_CR_CORR   = [m.replace("chair_right_", "chair_right_corr_") for m in ZONES[2]["modules"]
               if m.replace("chair_right_", "chair_right_corr_") in MODULES]
_SH_CORR_R = [m + "_corr_r" for m in ZONES[3]["modules"] if m + "_corr_r" in MODULES]
_SH_CORR_L = [m + "_corr_l" for m in ZONES[3]["modules"] if m + "_corr_l" in MODULES]

_SH_NARROW_CORR_R = [m + "_corr_r" for m in
                     ["shelf_narrow_r_v1", "shelf_narrow_r_v2", "shelf_narrow_r_v3"]
                     if m + "_corr_r" in MODULES]
_SH_NARROW_CORR_L = [m + "_corr_l" for m in
                     ["shelf_narrow_l_v1", "shelf_narrow_l_v2", "shelf_narrow_l_v3"]
                     if m + "_corr_l" in MODULES]

ZONES_CORR_RIGHT = [
    ZONES[0],
    ZONES[1],
    {**ZONES[2], "modules": _CR_CORR},
    {**ZONES[3], "modules": _SH_CORR_R},
]

ZONES_CORR_LEFT = [
    {**ZONES[0], "modules": _CL_CORR},
    ZONES[1],
    ZONES[2],
    {**ZONES[3], "modules": _SH_CORR_L},
]

ZONES_CORR_RIGHT_NARROW = [
    ZONES[0],
    {**ZONES[1], "x_rule": ["last 2"]},
    {**ZONES[3], "modules": _SH_NARROW_CORR_R},
]

ZONES_CORR_LEFT_NARROW = [
    {**ZONES[1], "x_rule": ["first 2"]},
    ZONES[2],
    {**ZONES[3], "modules": _SH_NARROW_CORR_L},
]

# ── Table module groups ───────────────────────────────────────────────────────
# Compact (no wide-top): chairs flush against table, dining zone = 6 cols.
# Spacious (wide-top):   1-col filler gap each side, dining zone = 8 cols.
_TABLE_COMPACT  = [m for m in ZONES[1]["modules"] if "wide-top" not in MODULES[m]["tags"]]
_TABLE_SPACIOUS = [m for m in ZONES[1]["modules"] if "wide-top"     in MODULES[m]["tags"]]

# ── Shelf / roof style groups ─────────────────────────────────────────────────
# plane:   flat top bar, minimal geometry (h=3)
# divided: internal horizontal/vertical subdivisions or hatching (h=3)
# pitched: lean-to (h=3, v4/v5) + gable ridge (h=4, sym/left/right variants)
_SHELF_PLANE   = ["shelf_h3_v1"]
_SHELF_DIVIDED = ["shelf_h3_v2", "shelf_h3_v3", "shelf_h3_v6", "shelf_h3_v7", "shelf_h3_v8"]
_SHELF_PITCHED = [
    # h=3 lean-to variants — 3 slopes per lean direction
    "shelf_h3_v4",        # medium lean-left  (left=2.5, right=1.5)
    "shelf_h3_v5",        # medium lean-right (left=1.5, right=2.5)
    "shelf_lean_r_gentle", "shelf_lean_r_steep",   # gentle / steep lean-right
    "shelf_lean_l_gentle", "shelf_lean_l_steep",   # gentle / steep lean-left
    # h=4 gable variants (no corridor pairing — no corr stubs generated)
    "shelf_pitched_sym_v1",   "shelf_pitched_sym_v2",
    "shelf_pitched_left_v1",  "shelf_pitched_left_v2",
    "shelf_pitched_right_v1", "shelf_pitched_right_v2",
]

# Maps base module ID (without _corr_r/_corr_l) → category string
_SHELF_CATEGORY: dict = {
    **{m: "plain"   for m in _SHELF_PLANE},
    **{m: "divided" for m in _SHELF_DIVIDED},
    **{m: "pitched" for m in _SHELF_PITCHED},
    "shelf_narrow_r_v1": "plain",   "shelf_narrow_l_v1": "plain",
    "shelf_narrow_r_v2": "divided", "shelf_narrow_l_v2": "divided",
    "shelf_narrow_r_v3": "pitched", "shelf_narrow_l_v3": "pitched",
}

SECTION_RULES = ["chair_left", "table", "chair_right", "shelf"]

# Used by drawing.py to order zones in the module library view
ZONE_ORDER = ["chair_left", "chair_right", "table", "shelf",
              "corridor_left", "corridor_right", "filler"]
