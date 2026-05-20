"""
3D module library — native modules only.
All geometry authored directly in 3D (exported from Rhino, y↔z axis-swapped).

Axis convention: x = width, y = height, z = depth.
Ports sit on the six faces: left (x=0), right (x=w), bottom (y=0),
top (y=h), front (z=0), back (z=d).
"""
from typing import Dict

FACES_3D = ("left", "right", "bottom", "top", "front", "back")


# ── Native 3D modules ─────────────────────────────────────────────────────────

MODULES_3D: Dict[str, dict] = {

    # ── Chairs ────────────────────────────────────────────────────────────────

    "chair_left_3d_v1": {
        "id":          "chair_left_3d_v1",
        "w": 2, "h": 2, "d": 3,
        "zone":        "chair_left",
        "description": "Left-facing chair, native 3D from Rhino. Seat at mid-depth.",
        "tags":        ["native3d", "chair_left"],
        "segments": [
            [(0.5, 2.0, 1.0), (0.5, 1.5, 1.0), (1.5, 1.5, 1.0), (1.0, 0.5, 1.5)],
            [(0.5, 1.5, 1.0), (0.5, 1.5, 2.0)],
            [(0.5, 2.0, 2.0), (0.5, 1.5, 2.0), (1.5, 1.5, 2.0), (1.0, 0.5, 1.5)],
            [(1.5, 1.5, 1.0), (1.5, 1.5, 2.0)],
            [(1.0, 0.5, 1.5), (2.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [],
            "right":  [(2.0, 0.5, 1.5)],
            "bottom": [],
            "top":    [(0.5, 2.0, 1.0), (0.5, 2.0, 2.0)],
            "front":  [],
            "back":   [],
        },
    },

    "chair_right_3d_v1": {
        "id":          "chair_right_3d_v1",
        "w": 2, "h": 2, "d": 3,
        "zone":        "chair_right",
        "description": "Right-facing chair, native 3D from Rhino. Seat at mid-depth.",
        "tags":        ["native3d", "chair_right"],
        "segments": [
            [(1.0, 0.5, 1.5), (0.5, 1.5, 2.0), (1.5, 1.5, 2.0), (1.5, 2.0, 2.0)],
            [(0.5, 1.5, 1.0), (0.5, 1.5, 2.0)],
            [(1.0, 0.5, 1.5), (0.5, 1.5, 1.0), (1.5, 1.5, 1.0), (1.5, 2.0, 1.0)],
            [(1.5, 1.5, 1.0), (1.5, 1.5, 2.0)],
            [(1.0, 0.5, 1.5), (0.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [(0.0, 0.5, 1.5)],
            "right":  [],
            "bottom": [],
            "top":    [(1.5, 2.0, 1.0), (1.5, 2.0, 2.0)],
            "front":  [],
            "back":   [],
        },
    },

    # ── Table ─────────────────────────────────────────────────────────────────

    "table_3d_v1": {
        "id":          "table_3d_v1",
        "w": 2, "h": 3, "d": 3,
        "zone":        "table",
        "description": "Dining table, native 3D from Rhino. Tent top, central stem, two legs.",
        "tags":        ["native3d", "table"],
        "segments": [
            [(1.5, 2.5, 2.5), (1.0, 0.5, 2.0), (0.5, 2.5, 2.5), (1.5, 2.5, 2.5)],
            [(0.5, 2.5, 0.5), (0.5, 2.5, 2.5)],
            [(1.5, 2.5, 0.5), (1.5, 2.5, 2.5)],
            [(1.5, 2.5, 0.5), (1.0, 0.5, 1.0), (0.5, 2.5, 0.5), (1.5, 2.5, 0.5)],
            [(1.0, 0.5, 1.0), (1.0, 0.5, 2.0)],
            [(2.0, 0.5, 1.5), (1.0, 0.5, 1.5)],
            [(0.0, 0.5, 1.5), (1.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [(0.0, 0.5, 1.5)],
            "right":  [(2.0, 0.5, 1.5)],
            "bottom": [],
            "top":    [],
            "front":  [],
            "back":   [],
        },
    },

    # ── Roof ──────────────────────────────────────────────────────────────────

    "roof_3d_v1": {
        "id":          "roof_3d_v1",
        "w": 6, "h": 3, "d": 3,
        "zone":        "roof",
        "description": "Full-width roof, native 3D from Rhino. Plan-view tent shape.",
        "tags":        ["native3d", "roof"],
        "segments": [
            [(0.5, 2.5, 2.0), (2.5, 2.5, 1.5), (0.5, 2.5, 1.0)],
            [(0.5, 2.5, 2.0), (0.5, 0.0, 2.0)],
            [(0.5, 2.5, 1.0), (0.5, 0.0, 1.0)],
            [(2.5, 2.5, 1.5), (3.5, 2.5, 1.5)],
            [(5.5, 2.5, 2.0), (3.5, 2.5, 1.5), (5.5, 2.5, 1.0)],
            [(5.5, 0.0, 2.0), (5.5, 2.5, 2.0)],
            [(5.5, 0.0, 1.0), (5.5, 2.5, 1.0)],
        ],
        "ports": {
            "left":   [],
            "right":  [],
            "bottom": [(0.5, 0.0, 1.0), (0.5, 0.0, 2.0), (5.5, 0.0, 1.0), (5.5, 0.0, 2.0)],
            "top":    [],
            "front":  [],
            "back":   [],
        },
    },

    # ── Connectors / Fillers ──────────────────────────────────────────────────

    "conn_chair_roof_left": {
        "id":          "conn_chair_roof_left",
        "w": 2, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Bridges chair_left top ports to roof bottom ports (left side).",
        "tags":        ["native3d", "connector"],
        "segments": [
            [(0.5, 0.0, 1.0), (0.5, 1.0, 1.0)],
            [(0.5, 0.0, 2.0), (0.5, 1.0, 2.0)],
        ],
        "ports": {
            "left":   [],
            "right":  [],
            "bottom": [(0.5, 0.0, 1.0), (0.5, 0.0, 2.0)],
            "top":    [(0.5, 1.0, 1.0), (0.5, 1.0, 2.0)],
            "front":  [],
            "back":   [],
        },
    },

    "conn_chair_roof_right": {
        "id":          "conn_chair_roof_right",
        "w": 2, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Bridges chair_right top ports to roof bottom ports (right side).",
        "tags":        ["native3d", "connector"],
        "segments": [
            [(1.5, 0.0, 1.0), (1.5, 1.0, 1.0)],
            [(1.5, 0.0, 2.0), (1.5, 1.0, 2.0)],
        ],
        "ports": {
            "left":   [],
            "right":  [],
            "bottom": [(1.5, 0.0, 1.0), (1.5, 0.0, 2.0)],
            "top":    [(1.5, 1.0, 1.0), (1.5, 1.0, 2.0)],
            "front":  [],
            "back":   [],
        },
    },

    "filler_empty_3d": {
        "id":          "filler_empty_3d",
        "w": 1, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Empty filler cell. No geometry, no ports.",
        "tags":        ["native3d", "filler", "empty"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_segments_3d(mod: dict, w: int, h: int, d: int) -> list:
    if "whd_segments_fn" in mod:
        return mod["whd_segments_fn"](w, h, d)
    return mod.get("segments", [])


def get_ports_3d(mod: dict, w: int, h: int, d: int) -> dict:
    if "whd_ports_fn" in mod:
        return mod["whd_ports_fn"](w, h, d)
    return mod.get("ports", {face: [] for face in FACES_3D})


# ── Zone definitions (populated as native modules are added) ──────────────────

ZONES_3D                   = []
ZONES_3D_CORR_RIGHT        = []
ZONES_3D_CORR_LEFT         = []
ZONES_3D_CORR_RIGHT_NARROW = []
ZONES_3D_CORR_LEFT_NARROW  = []

FILLER_IDS_3D = [mid for mid, m in MODULES_3D.items() if m["zone"] == "filler"]
