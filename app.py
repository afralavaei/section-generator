import math
import pathlib
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

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
        "description": "Table, height 2. Rectangular frame with two straight vertical legs and a mid-height bar.",
        "tags": ["rectilinear", "h2"],
        "segments": [
            [(0.5, 1.5), (1.5, 1.5)],   # top horizontal bar
            [(0.5, 1.5), (0.5, 0.5)],
            [(1.5, 1.5), (1.5, 0.5)],
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
     "table_h2_v4": {
        "id": "table_h2_v4",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Table, height 2. Tall rectangular frame with the top bar at maximum height.",
        "tags": ["rectilinear", "tall-bar", "h2"],
        "segments": [
            [(0.5, 2.0), (1.5, 2.0)],   # top horizontal bar
            [(0.5, 2.0), (0.5, 0.5)],
            [(1.5, 2.0), (1.5, 0.5)],
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
    "table_h2_v5": {
        "id": "table_h2_v5",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Table, height 2. Full-width top bar with outward-leaning diagonal legs.",
        "tags": ["diagonal", "wide-top", "h2"],
        "segments": [
            [(0.0, 1.5), (2.0, 1.5)],   # top horizontal bar
            [(0.0, 1.5), (0.5, 0.5)],   # left diagonal to tip
            [(2.0, 1.5), (1.5, 0.5)],   # right diagonal to tip
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
    "table_h2_v6": {
        "id": "table_h2_v6",
        "w": 2, "h": 2,
        "zone": "table",
        "description": "Table, height 2. Full-width top bar at maximum height with outward diagonal legs.",
        "tags": ["diagonal", "wide-top", "tall-bar", "h2"],
        "segments": [
            [(0.0, 2.0), (2.0, 2.0)],   # top horizontal bar
            [(0.0, 2.0), (0.5, 0.5)],   # left diagonal to tip
            [(2.0, 2.0), (1.5, 0.5)],   # right diagonal to tip
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
        "description": "Table, height 3. Full-width top bar with outward diagonal legs — wide, triangular profile.",
        "tags": ["diagonal", "wide-top", "h3"],
        "segments": [
            [(0.0, 2.5), (2.0, 2.5)],   # top horizontal bar
            [(0.0, 2.5), (0.5, 0.5)],   # left diagonal to tip
            [(2.0, 2.5), (1.5, 0.5)],   # right diagonal to tip
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
    "table_h3_v3": {
        "id": "table_h3_v3",
        "w": 2, "h": 3,
        "zone": "table",
        "description": "Table, height 3. Tall rectangular frame with vertical legs and a high horizontal bar.",
        "tags": ["rectilinear", "h3"],
        "segments": [
            [(0.5, 2.5), (1.5, 2.5)],   # top horizontal bar
            [(0.5, 2.5), (0.5, 0.5)],
            [(1.5, 2.5), (1.5, 0.5)],
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
        # left small compartment + right section with evenly-spaced dividers
        # right rect traverses all divider x-positions as waypoints so degree check passes
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
        # frame (short stems + closed rectangle) with diagonal hatching lines
        # frame traverses all hatch x-positions as waypoints so degree check passes
        "segments_fn": lambda W: [
            [(0.5, 0.0), (0.5, 1.0)],
            [(W-0.5, 0.0), (W-0.5, 1.0)],
            [(0.5+i, 1.0) for i in range(W)] + [(W-0.5-i, 2.5) for i in range(W)] + [(0.5, 1.0)],
        ] + [[(0.5+i, 1.0), (1.5+i, 2.5)] for i in range(1, W-2)],
        "ports_fn": lambda W: {"top": [], "bottom": [(0.5, 0.0), (W-0.5, 0.0)], "left": [], "right": []},
    },

    # ── Corridor modules ──────────────────────────────────────────────────────
    # h_scalable: spans full section height H (resolved at solve time via h_segments_fn / h_ports_fn).
    # Inner-face ports connect to the corridor-adjacent chair and shelf.
    # Circuit: U-bracket polyline — both endpoints connect to neighbours → degree 2 each.

    "corridor_right": {
        "id": "corridor_right", "w": 2, "h": 6, "zone": "corridor_right", "h_scalable": True,
        "description": "Corridor on the right side. U-bracket spanning the full section height, opening inward. Connects to adjacent chair at the bottom and shelf at the top.",
        "tags": ["corridor", "circulation", "h-scalable", "right-side"],
        # U-bracket opening leftward: bottom-left port → right wall → top-left port
        "h_segments_fn": lambda H: [[(0.0, 0.5), (1.5, 0.5), (1.5, H - 0.5), (0.0, H - 0.5)]],
        "h_ports_fn":    lambda H: {"top": [], "bottom": [], "left": [(0.0, 0.5), (0.0, H - 0.5)], "right": []},
    },
    "corridor_left": {
        "id": "corridor_left", "w": 2, "h": 6, "zone": "corridor_left", "h_scalable": True,
        "description": "Corridor on the left side. U-bracket spanning the full section height, opening inward. Connects to adjacent chair at the bottom and shelf at the top.",
        "tags": ["corridor", "circulation", "h-scalable", "left-side"],
        # U-bracket opening rightward: bottom-right port → left wall → top-right port
        "h_segments_fn": lambda H: [[(2.0, 0.5), (0.5, 0.5), (0.5, H - 0.5), (2.0, H - 0.5)]],
        "h_ports_fn":    lambda H: {"top": [], "bottom": [], "left": [], "right": [(2.0, 0.5), (2.0, H - 0.5)]},
    },

    # ── 1×1 filler tiles ──────────────────────────────────────────────────────
    "filler_empty": {
        "id": "filler_empty", "w": 1, "h": 1, "zone": "filler",
        "description": "Empty filler tile. No geometry — fills dead space without contributing to the circuit.",
        "tags": ["filler", "empty", "invisible"],
        "segments": [],
        "ports": {"top": [], "bottom": [], "left": [], "right": []},
    },
    "filler_pass_v": {
        "id": "filler_pass_v", "w": 1, "h": 1, "zone": "filler",
        "description": "Vertical pass-through filler. Routes the drawn circuit upward through a gap cell.",
        "tags": ["filler", "vertical", "pass-through"],
        "segments": [[(0.5, 0.0), (0.5, 1.0)]],
        "ports": {"top": [(0.5, 1.0)], "bottom": [(0.5, 0.0)], "left": [], "right": []},
    },
    "filler_pass_h": {
        "id": "filler_pass_h", "w": 1, "h": 1, "zone": "filler",
        "description": "Horizontal pass-through filler. Routes the drawn circuit sideways through a gap cell.",
        "tags": ["filler", "horizontal", "pass-through"],
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
        "id":          "chair_left",
        "description": "Left seating zone. First 2 columns. Chairs face right toward the table; the circuit enters from the shelf above and exits to the table.",
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
        "description": "Central table zone. Middle 2 columns. Bridges the left and right chairs at floor level.",
        "tags":        ["table", "central", "connector"],
        "x_rule":      ["middle 2"],
        "y_rule":      ["first 3", "first 2"],
        "modules": ["table_h3_v1", "table_h3_v2", "table_h3_v3",
                    "table_h2_v1", "table_h2_v2", "table_h2_v3", "table_h2_v4", "table_h2_v5", "table_h2_v6"],
    },
    {
        "id":          "chair_right",
        "description": "Right seating zone. Last 2 columns. Chairs face left toward the table; mirrors the left seating zone.",
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
        "description": "Full-width storage zone along the top 3 rows. Spans the entire section width and anchors the circuit from above.",
        "tags":        ["shelf", "storage", "full-width", "top"],
        "x_rule":      ["full"],
        "y_rule":      ["last 3"],
        "modules": ["shelf_h3_v1", "shelf_h3_v2", "shelf_h3_v3", "shelf_h3_v4",
                     "shelf_h3_v5", "shelf_h3_v6", "shelf_h3_v7", "shelf_h3_v8"],
    },
]

# ── Corridor variant factory ──────────────────────────────────────────────────
# Generates corridor-ready chair/shelf variants.
# Each variant adds BOTH a port (for adjacency) AND a segment stub (for circuit).
# Variants are only created when the base module's geometry reaches the connection point.

def _has_waypoint(segments, pt, eps=1e-9):
    return any(
        abs(p[0] - pt[0]) < eps and abs(p[1] - pt[1]) < eps
        for seg in segments for p in seg
    )


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
            # Seat-rectangle variants have (1.5, 0.5) as a waypoint → add right stub
            if _has_waypoint(m["segments"], (1.5, 0.5)):
                nid = key.replace("chair_right_", "chair_right_corr_")
                to_add[nid] = {
                    **m, "id": nid,
                    "segments": m["segments"] + [[(1.5, 0.5), (2.0, 0.5)]],
                    "ports":    {**m["ports"], "right": [(2.0, 0.5)]},
                }
        elif m["zone"] == "chair_left":
            # Seat-rectangle variants have (0.5, 0.5) as a waypoint → add left stub
            if _has_waypoint(m["segments"], (0.5, 0.5)):
                nid = key.replace("chair_left_", "chair_left_corr_")
                to_add[nid] = {
                    **m, "id": nid,
                    "segments": m["segments"] + [[(0.5, 0.5), (0.0, 0.5)]],
                    "ports":    {**m["ports"], "left": [(0.0, 0.5)]},
                }
        elif m["zone"] == "shelf":
            ref_W    = m["w"]
            ref_segs = m["segments_fn"](ref_W)
            # corr_r: right vertical must reach y=2.5 (i.e. (W-0.5, 2.5) is a segment endpoint)
            if _has_endpoint(ref_segs, (ref_W - 0.5, 2.5)):
                nid_r = key + "_corr_r"
                sfn, pfn = m["segments_fn"], m["ports_fn"]
                to_add[nid_r] = {
                    **m, "id": nid_r,
                    "segments_fn": lambda W, _s=sfn: _s(W) + [[(W - 0.5, 2.5), (W, 2.5)]],
                    "ports_fn":    lambda W, _p=pfn: {**_p(W), "right": [(W, 2.5)]},
                }
            # corr_l: left vertical must reach y=2.5 (i.e. (0.5, 2.5) is a segment endpoint)
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
# Filter to only include variants that were actually created by the factory.

_CL_CORR   = [m.replace("chair_left_",  "chair_left_corr_")  for m in ZONES[0]["modules"]
               if m.replace("chair_left_",  "chair_left_corr_")  in MODULES]
_CR_CORR   = [m.replace("chair_right_", "chair_right_corr_") for m in ZONES[2]["modules"]
               if m.replace("chair_right_", "chair_right_corr_") in MODULES]
_SH_CORR_R = [m + "_corr_r" for m in ZONES[3]["modules"] if m + "_corr_r" in MODULES]
_SH_CORR_L = [m + "_corr_l" for m in ZONES[3]["modules"] if m + "_corr_l" in MODULES]

# corridor_right layout: corridor pre-placed at x=W-2..W; inner zones solved over W-2
ZONES_CORR_RIGHT = [
    ZONES[0],                                          # chair_left  — unchanged
    ZONES[1],                                          # table       — unchanged
    {**ZONES[2], "modules": _CR_CORR},                 # chair_right — adds right port
    {**ZONES[3], "modules": _SH_CORR_R},              # shelf       — adds right port
]

# corridor_left layout: corridor pre-placed at x=0..2; inner zones offset +2
ZONES_CORR_LEFT = [
    {**ZONES[0], "modules": _CL_CORR},                # chair_left  — adds left port
    ZONES[1],                                          # table       — unchanged
    ZONES[2],                                          # chair_right — unchanged
    {**ZONES[3], "modules": _SH_CORR_L},              # shelf       — adds left port
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

            # A's right edge coincides with B's left edge
            if abs((ax0 + aw) - bx0) < EPS:
                y_lo = max(ay0, by0)
                y_hi = min(ay0 + ah, by0 + bh)
                if y_hi > y_lo:
                    if (_ports_in_range(ma, "right", ax0, ay0, y_lo, y_hi, aw, ah) !=
                            _ports_in_range(mb, "left",  bx0, by0, y_lo, y_hi, bw, bh)):
                        return False

            # B's right edge coincides with A's left edge
            if abs((bx0 + bw) - ax0) < EPS:
                y_lo = max(ay0, by0)
                y_hi = min(ay0 + ah, by0 + bh)
                if y_hi > y_lo:
                    if (_ports_in_range(mb, "right", bx0, by0, y_lo, y_hi, bw, bh) !=
                            _ports_in_range(ma, "left",  ax0, ay0, y_lo, y_hi, aw, ah)):
                        return False

            # A's top edge coincides with B's bottom edge
            if abs((ay0 + ah) - by0) < EPS:
                x_lo = max(ax0, bx0)
                x_hi = min(ax0 + aw, bx0 + bw)
                if x_hi > x_lo:
                    if (_ports_in_range(ma, "top",    ax0, ay0, x_lo, x_hi, aw, ah) !=
                            _ports_in_range(mb, "bottom", bx0, by0, x_lo, x_hi, bw, bh)):
                        return False

            # B's top edge coincides with A's bottom edge
            if abs((by0 + bh) - ay0) < EPS:
                x_lo = max(ax0, bx0)
                x_hi = min(ax0 + aw, bx0 + bw)
                if x_hi > x_lo:
                    if (_ports_in_range(mb, "top",    bx0, by0, x_lo, x_hi, bw, bh) !=
                            _ports_in_range(ma, "bottom", ax0, ay0, x_lo, x_hi, aw, ah)):
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
        for seg in get_segments(mod, p["w"], p["h"]):
            pts = [(round(x + xo, 9), round(y + yo, 9)) for x, y in seg]
            for k in range(len(pts) - 1):
                degree[pts[k]]     += 1
                degree[pts[k + 1]] += 1

    return all(d != 1 for d in degree.values())

# ── Parametric segment / port resolvers ──────────────────────────────────────

def get_segments(mod: dict, w: int, h: int = None) -> List:
    if "segments_fn" in mod:
        return mod["segments_fn"](w)
    if "h_segments_fn" in mod:
        return mod["h_segments_fn"](h if h is not None else mod["h"])
    return mod["segments"]


def get_ports(mod: dict, w: int, h: int = None) -> dict:
    if "ports_fn" in mod:
        return mod["ports_fn"](w)
    if "h_ports_fn" in mod:
        return mod["h_ports_fn"](h if h is not None else mod["h"])
    return mod["ports"]


# ── Solver ────────────────────────────────────────────────────────────────────

def _gap_cells(placed_so_far: List[dict], W: int, H: int) -> List[Tuple[int, int]]:
    """Return all (col, row) cells in the W×H grid not covered by any placed module."""
    covered: set = set()
    for p in placed_so_far:
        for col in range(int(p["x_off"]), int(p["x_off"]) + p["w"]):
            for row in range(int(p["y_off"]), int(p["y_off"]) + p["h"]):
                covered.add((col, row))
    return [(col, row) for row in range(H) for col in range(W)
            if (col, row) not in covered]


def solve(W: int, H: int, seed: int, corridor: str = "none") -> Optional[List[dict]]:
    """
    Two-phase backtracking solver.
    Phase 1: place named zone modules (chair, table, shelf, …).
    Phase 2: fill every remaining cell with a 1×1 filler tile so the
             full W×H grid is covered and the closed-circuit rule is met.
    """
    rng = random.Random(seed)
    filler_ids = [mid for mid, m in MODULES.items() if m["zone"] == "filler"]

    # Corridor pre-placement — occupies 2 columns on one side; inner zones fill the rest
    if corridor == "corridor_right":
        inner_W, x_offset = W - 2, 0
        placed = [{"module_id": "corridor_right",
                   "x_off": float(W - 2), "y_off": 0.0, "w": 2, "h": H}]
        active_zones = ZONES_CORR_RIGHT
    elif corridor == "corridor_left":
        inner_W, x_offset = W - 2, 2
        placed = [{"module_id": "corridor_left",
                   "x_off": 0.0, "y_off": 0.0, "w": 2, "h": H}]
        active_zones = ZONES_CORR_LEFT
    else:
        inner_W, x_offset = W, 0
        placed = []
        active_zones = ZONES

    # Phase 1 candidates — one option list per named zone
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

    def _chairs_same_height() -> bool:
        cl_h = next((p["h"] for p in placed if MODULES[p["module_id"]]["zone"] == "chair_left"),  None)
        cr_h = next((p["h"] for p in placed if MODULES[p["module_id"]]["zone"] == "chair_right"), None)
        return cl_h is None or cr_h is None or cl_h == cr_h

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

# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_grid(ax, ox: float, oy: float, w: int, h: int) -> None:
    for i in range(w + 1):
        lw = 1.2 if i in (0, w) else 0.3
        ax.plot([ox + i, ox + i], [oy, oy + h], color=GRID_COLOR, lw=lw, zorder=1)
    for j in range(h + 1):
        lw = 1.2 if j in (0, h) else 0.3
        ax.plot([ox, ox + w], [oy + j, oy + j], color=GRID_COLOR, lw=lw, zorder=1)


def _draw_module(ax, mod: dict, x_off: float, y_off: float,
                 show_grid: bool = True, show_ports: bool = True,
                 placed_w: int = None, placed_h: int = None) -> None:
    w = placed_w if placed_w is not None else mod["w"]
    h = placed_h if placed_h is not None else mod["h"]

    if show_grid:
        fc = ZONE_COLORS.get(mod.get("zone", ""), "#ffffff")
        ax.add_patch(patches.Rectangle(
            (x_off, y_off), w, h,
            facecolor=fc, alpha=0.25, zorder=0, linewidth=0,
        ))
        _draw_grid(ax, x_off, y_off, w, h)

    for seg in get_segments(mod, w, h):
        xs = [p[0] + x_off for p in seg]
        ys = [p[1] + y_off for p in seg]
        ax.plot(xs, ys, color=LINE_COLOR, lw=2.2, zorder=3,
                solid_capstyle="round", solid_joinstyle="round")

    if show_ports:
        for pts in get_ports(mod, w, h).values():
            for px, py in pts:
                ax.plot(px + x_off, py + y_off, "o",
                        color=PORT_COLOR, ms=6, zorder=4)

# ── Silhouette helpers ────────────────────────────────────────────────────────

_SILHOUETTE_DIR   = pathlib.Path(__file__).parent
_silhouette_cache: dict = {}


def _load_silhouette(filename: str):
    """Load an image file and make the white background transparent. Cached in-process."""
    if filename in _silhouette_cache:
        return _silhouette_cache[filename]
    path = _SILHOUETTE_DIR / filename
    if not path.exists():
        _silhouette_cache[filename] = None
        return None
    try:
        raw = plt.imread(str(path)).astype(float)
        if raw.max() > 1.0:
            raw = raw / 255.0
        # Ensure RGBA
        if raw.ndim == 2:
            raw = np.stack([raw, raw, raw, np.ones_like(raw)], axis=-1)
        elif raw.shape[2] == 3:
            raw = np.concatenate([raw, np.ones((*raw.shape[:2], 1))], axis=-1)
        else:
            raw = raw.copy()
        # Remove near-white background
        white = (raw[:, :, 0] > 0.85) & (raw[:, :, 1] > 0.85) & (raw[:, :, 2] > 0.85)
        raw[white, 3] = 0.0
        _silhouette_cache[filename] = raw
        return raw
    except Exception:
        _silhouette_cache[filename] = None
        return None


def _draw_silhouette(ax, img, cx: float, y_bot: float,
                     height_units: float, alpha: float = 0.5,
                     clip_patch=None) -> None:
    """Overlay a silhouette image centred at cx, bottom edge at y_bot, scaled to height_units tall."""
    if img is None:
        return
    ih, iw = img.shape[:2]
    w_units = height_units * iw / ih
    extent  = [cx - w_units / 2, cx + w_units / 2, y_bot, y_bot + height_units]
    artist  = ax.imshow(img, extent=extent, aspect="auto", zorder=2, alpha=alpha)
    if clip_patch is not None:
        artist.set_clip_path(clip_patch)
        artist.set_clip_on(True)


# ── Section plot ──────────────────────────────────────────────────────────────

def plot_section(placed: List[dict], W: int, H: int,
                 show_figures: bool = False) -> plt.Figure:
    scale = max(1.2, 8.0 / W)
    fig, ax = plt.subplots(figsize=(W * scale, H * scale))

    for p in placed:
        mod = MODULES[p["module_id"]]
        _draw_module(ax, mod, p["x_off"], p["y_off"], placed_w=p["w"], placed_h=p["h"])
        cx = p["x_off"] + p["w"] / 2
        cy = p["y_off"] + mod["h"] / 2
        ax.text(cx, cy, mod["zone"].replace("_", "\n"),
                ha="center", va="center", fontsize=7, color="#666666", alpha=0.7)

    # ── Human scale figures ───────────────────────────────────────────────────
    # 1 grid unit = 40 cm  →  180 cm person = 4.5 units tall
    if show_figures:
        seated_img   = _load_silhouette("Screenshot 2026-05-11 112615.png")
        standing_img = _load_silhouette("side standing.png")
        clip = patches.Rectangle((0, 0), W, H, transform=ax.transData)
        for p in placed:
            zone = MODULES[p["module_id"]]["zone"]
            cx   = p["x_off"] + p["w"] / 2
            if zone == "chair_left":
                _draw_silhouette(ax, seated_img, cx + 0.5, p["y_off"], height_units=4.5,
                                 clip_patch=clip)
            elif zone in ("corridor_left", "corridor_right"):
                _draw_silhouette(ax, standing_img, cx, p["y_off"] + 0.5, height_units=4.5,
                                 clip_patch=clip)

    ax.set_xlim(-0.3, W + 0.3)
    ax.set_ylim(-0.3, H + 0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Nomadic Engine — Section  {W} × {H}", fontsize=12, pad=10)
    fig.tight_layout()
    return fig

# ── Module library plot ───────────────────────────────────────────────────────

ZONE_ORDER = ["chair_left", "chair_right", "table", "shelf",
              "corridor_left", "corridor_right", "filler"]


def plot_module_library() -> plt.Figure:
    # Exclude auto-generated corridor-connection variants — they are internal solver variants,
    # not standalone design primitives.
    mods = sorted(
        (m for m in MODULES.values() if "_corr_" not in m["id"] and not m["id"].endswith("_corr_r") and not m["id"].endswith("_corr_l")),
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
    # ── Step 1: corridor mode ──────────────────────────────────────────────────
    corridor_choice = st.radio(
        "Corridor",
        options=["None", "Corridor Left", "Corridor Right"],
        horizontal=True,
        help="Corridors connect adjacent sections. When active, 2 columns are reserved on the chosen side.",
    )
    corridor = {"None": "none", "Corridor Left": "corridor_left", "Corridor Right": "corridor_right"}[corridor_choice]

    # ── Step 2: dimensions & seed ─────────────────────────────────────────────
    min_W = 8 if corridor != "none" else 6
    c1, c2, c3 = st.columns(3)
    with c1:
        seed = int(st.slider("Seed", min_value=0, max_value=1_000_000, value=42, step=1))
    with c2:
        W = int(st.number_input("Width W", min_value=min_W, max_value=20, value=max(6, min_W), step=1,
                                help="Shelf auto-scales to full width; gaps between zones filled automatically"))
    with c3:
        H = int(st.number_input("Height H", min_value=6, max_value=20, value=6, step=1,
                                help="Extra rows above zones are auto-filled with filler tiles"))

    show_figures = st.checkbox(
        "Show human scale figures  (180 cm = 4.5 grid units)",
        value=False,
        help="Overlays seated figures in chair zones and a standing figure in the corridor. "
             "Requires silhouette_seated.png and silhouette_standing.png in the app folder.",
    )

    if corridor != "none" and W < 8:
        st.warning("Corridor mode requires W ≥ 8 (2 columns reserved for corridor + 6 for inner zones).")

    with st.spinner("Solving…"):
        result = solve(W, H, seed, corridor)

    if result is None:
        st.error("No valid section found — circuit cannot be closed with current modules.")
    else:
        st.pyplot(plot_section(result, W, H, show_figures=show_figures))

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
