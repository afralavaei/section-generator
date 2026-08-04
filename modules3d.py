"""
3D module library — native modules only.
Axis convention: x = width, y = height, z = depth.
Ports: left (x=0), right (x=w), bottom (y=0), top (y=h), front (z=0), back (z=d).

New modules are defined by calling _lift2d() at import time on 2D segment data.
This produces explicit static 3D coordinates (not lazy-computed at render time).
"""
from typing import Dict
from functools import lru_cache

FACES_3D = ("left", "right", "bottom", "top", "front", "back")


# ── Helpers: lift 2D geometry to 3D at import time ───────────────────────────

def _lift2d(segs_2d: list, d: int = 3, ex: set = None) -> list:
    """Convert 2D segments to 3D: front profile at z=0.5, back at z=d-0.5.
    z-connectors are added at every unique vertex NOT in ex (port exclusion set)."""
    z0, z1 = 0.5, float(d) - 0.5
    segs_3d = []
    unique_pts: set = set()
    for seg in segs_2d:
        segs_3d.append([(x, y, z0) for x, y in seg])
        segs_3d.append([(x, y, z1) for x, y in seg])
        for pt in seg:
            unique_pts.add(pt)
    skip = ex or set()
    for x, y in unique_pts:
        if (x, y) not in skip:
            segs_3d.append([(x, y, z0), (x, y, z1)])
    return segs_3d


def _ports_lift(ports_2d: dict, d: int = 3) -> dict:
    """Lift 2D port dict to 3D — each (x,y) port becomes (x,y,0.5) and (x,y,d-0.5)."""
    z0, z1 = 0.5, float(d) - 0.5
    out: dict = {}
    for face in ("left", "right", "top", "bottom"):
        pts = ports_2d.get(face, [])
        out[face] = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    out["front"] = []
    out["back"] = []
    return out


def _scale_segs_d(segs: list, old_d: int, new_d: int) -> list:
    """Remap z=back-plane coordinate from old_d to new_d; z=front stays at 0.5."""
    z_old = float(old_d) - 0.5
    z_new = float(new_d) - 0.5
    def rz(z): return z_new if abs(z - z_old) < 1e-9 else z
    return [[(x, y, rz(z)) for x, y, z in seg] for seg in segs]


def _scale_ports_d(ports: dict, old_d: int, new_d: int) -> dict:
    """Remap z=back-plane coordinate in a ports dict from old_d to new_d."""
    z_old = float(old_d) - 0.5
    z_new = float(new_d) - 0.5
    def rz(z): return z_new if abs(z - z_old) < 1e-9 else z
    return {face: [(x, y, rz(z)) for x, y, z in pts] for face, pts in ports.items()}


# ── Module library ────────────────────────────────────────────────────────────

MODULES_3D: Dict[str, dict] = {

    # ── Rhino native: chairs ──────────────────────────────────────────────────

    "chair_left_3d_v1": {
        "id":          "chair_left_3d_v1",
        "w": 2, "h": 2, "d": 3,
        "zone":        "chair_left",
        "description": "Left-facing chair, native 3D from Rhino.",
        "tags":        ["native3d", "chair_left", "h2"],
        "segments": [
            [(0.5, 2.0, 0.5), (0.5, 1.5, 0.5), (1.5, 1.5, 0.5), (1.0, 0.5, 1.5)],
            [(0.5, 1.5, 0.5), (0.5, 1.5, 2.5)],
            [(0.5, 2.0, 2.5), (0.5, 1.5, 2.5), (1.5, 1.5, 2.5), (1.0, 0.5, 1.5)],
            [(1.5, 1.5, 0.5), (1.5, 1.5, 2.5)],
            [(1.0, 0.5, 1.5), (2.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [], "right":  [(2.0, 0.5, 1.5)],
            "bottom": [], "top":    [(0.5, 2.0, 0.5), (0.5, 2.0, 2.5)],
            "front":  [], "back":   [],
        },
    },

    "chair_right_3d_v1": {
        "id":          "chair_right_3d_v1",
        "w": 2, "h": 2, "d": 3,
        "zone":        "chair_right",
        "description": "Right-facing chair, native 3D from Rhino.",
        "tags":        ["native3d", "chair_right", "h2"],
        "segments": [
            [(1.0, 0.5, 1.5), (0.5, 1.5, 2.5), (1.5, 1.5, 2.5), (1.5, 2.0, 2.5)],
            [(0.5, 1.5, 0.5), (0.5, 1.5, 2.5)],
            [(1.0, 0.5, 1.5), (0.5, 1.5, 0.5), (1.5, 1.5, 0.5), (1.5, 2.0, 0.5)],
            [(1.5, 1.5, 0.5), (1.5, 1.5, 2.5)],
            [(1.0, 0.5, 1.5), (0.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [(0.0, 0.5, 1.5)], "right":  [],
            "bottom": [],                "top":    [(1.5, 2.0, 0.5), (1.5, 2.0, 2.5)],
            "front":  [],                "back":   [],
        },
    },

    # ── Rhino native: table ───────────────────────────────────────────────────

    "table_3d_v1": {
        "id":          "table_3d_v1",
        "w": 2, "h": 3, "d": 3,
        "zone":        "table",
        "description": "Dining table, native 3D from Rhino.",
        "tags":        ["native3d", "table", "h3"],
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
            "left":   [(0.0, 0.5, 1.5)], "right":  [(2.0, 0.5, 1.5)],
            "bottom": [],                "top":    [],
            "front":  [],                "back":   [],
        },
    },

    # ── Rhino native: roof (placed in shelf zone) ─────────────────────────────

    "roof_3d_v1": {
        "id":          "roof_3d_v1",
        "w": 6, "h": 3, "d": 3,
        "zone":        "shelf",
        "description": "Full-width roof, native 3D from Rhino.",
        "tags":        ["native3d", "roof"],
        "segments": [
            [(0.5, 2.5, 2.5), (2.5, 2.5, 1.5), (0.5, 2.5, 0.5)],
            [(0.5, 2.5, 2.5), (0.5, 0.0, 2.5)],
            [(0.5, 2.5, 0.5), (0.5, 0.0, 0.5)],
            [(0.5, 0.0, 0.5), (0.5, 0.0, 2.5)],
            [(2.5, 2.5, 1.5), (3.5, 2.5, 1.5)],
            [(5.5, 2.5, 2.5), (3.5, 2.5, 1.5), (5.5, 2.5, 0.5)],
            [(5.5, 0.0, 2.5), (5.5, 2.5, 2.5)],
            [(5.5, 0.0, 0.5), (5.5, 2.5, 0.5)],
            [(5.5, 0.0, 0.5), (5.5, 0.0, 2.5)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(0.5, 0.0, 0.5), (0.5, 0.0, 2.5), (5.5, 0.0, 0.5), (5.5, 0.0, 2.5)],
            "top":    [],
            "front":  [], "back":   [],
        },
    },

    # ── Connectors (legacy, kept for backward compatibility) ──────────────────

    "conn_chair_roof_left": {
        "id":          "conn_chair_roof_left",
        "w": 2, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Bridges chair_left top to roof bottom (left side).",
        "tags":        ["native3d", "connector"],
        "segments": [
            [(0.5, 0.0, 0.5), (0.5, 1.0, 0.5)],
            [(0.5, 0.0, 2.5), (0.5, 1.0, 2.5)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(0.5, 0.0, 0.5), (0.5, 0.0, 2.5)],
            "top":    [(0.5, 1.0, 0.5), (0.5, 1.0, 2.5)],
            "front":  [], "back":   [],
        },
    },

    "conn_chair_roof_right": {
        "id":          "conn_chair_roof_right",
        "w": 2, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Bridges chair_right top to roof bottom (right side).",
        "tags":        ["native3d", "connector"],
        "segments": [
            [(1.5, 0.0, 0.5), (1.5, 1.0, 0.5)],
            [(1.5, 0.0, 2.5), (1.5, 1.0, 2.5)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(1.5, 0.0, 0.5), (1.5, 0.0, 2.5)],
            "top":    [(1.5, 1.0, 0.5), (1.5, 1.0, 2.5)],
            "front":  [], "back":   [],
        },
    },

    # ── Fillers ───────────────────────────────────────────────────────────────

    "filler_empty_3d": {
        "id":          "filler_empty_3d",
        "w": 1, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Empty filler cell.",
        "tags":        ["native3d", "filler", "empty"],
        "scalable_d": True,
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
    },

    "filler_pass_v_3d": {
        "id":          "filler_pass_v_3d",
        "w": 1, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Vertical pass-through — chains chair top ports up to shelf/roof bottom.",
        "tags":        ["native3d", "filler", "vertical"],
        "scalable_d": True,
        "segments": [
            [(0.5, 0.0, 0.5), (0.5, 1.0, 0.5)],
            [(0.5, 0.0, 2.5), (0.5, 1.0, 2.5)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(0.5, 0.0, 0.5), (0.5, 0.0, 2.5)],
            "top":    [(0.5, 1.0, 0.5), (0.5, 1.0, 2.5)],
            "front":  [], "back":   [],
        },
    },

    # Horizontal pass-through: needed in spacious (W=8) gap columns between
    # chair and table zones so lateral ports at y=0.5 are matched.
    "filler_pass_h_3d": {
        "id":          "filler_pass_h_3d",
        "w": 1, "h": 1, "d": 3,
        "zone":        "filler",
        "description": "Horizontal pass-through — bridges chair/table lateral ports across gap cell.",
        "tags":        ["native3d", "filler", "horizontal"],
        "scalable_d": True,
        "segments": [
            [(0.0, 0.5, 0.5), (1.0, 0.5, 0.5)],
            [(0.0, 0.5, 2.5), (1.0, 0.5, 2.5)],
        ],
        "ports": {
            "left":   [(0.0, 0.5, 0.5), (0.0, 0.5, 2.5)],
            "right":  [(1.0, 0.5, 0.5), (1.0, 0.5, 2.5)],
            "bottom": [], "top":    [],
            "front":  [], "back":   [],
        },
    },

    "filler_corner_tr_3d": {
        "id": "filler_corner_tr_3d", "w": 1, "h": 1, "d": 3, "zone": "filler",
        "description": "Top-right corner filler 3D — L-segment connecting vertical chain (top) to horizontal chain (right).",
        "tags": ["native3d", "filler", "corner", "top-right"],
        "scalable_d": True,
        "segments": [
            [(0.5, 1.0, 0.5), (0.5, 0.5, 0.5), (1.0, 0.5, 0.5)],
            [(0.5, 1.0, 2.5), (0.5, 0.5, 2.5), (1.0, 0.5, 2.5)],
        ],
        "ports": {
            "top":    [(0.5, 1.0, 0.5), (0.5, 1.0, 2.5)],
            "right":  [(1.0, 0.5, 0.5), (1.0, 0.5, 2.5)],
            "bottom": [], "left": [], "front": [], "back": [],
        },
    },
    "filler_corner_tl_3d": {
        "id": "filler_corner_tl_3d", "w": 1, "h": 1, "d": 3, "zone": "filler",
        "description": "Top-left corner filler 3D — L-segment connecting vertical chain (top) to horizontal chain (left).",
        "tags": ["native3d", "filler", "corner", "top-left"],
        "scalable_d": True,
        "segments": [
            [(0.5, 1.0, 0.5), (0.5, 0.5, 0.5), (0.0, 0.5, 0.5)],
            [(0.5, 1.0, 2.5), (0.5, 0.5, 2.5), (0.0, 0.5, 2.5)],
        ],
        "ports": {
            "top":    [(0.5, 1.0, 0.5), (0.5, 1.0, 2.5)],
            "left":   [(0.0, 0.5, 0.5), (0.0, 0.5, 2.5)],
            "bottom": [], "right": [], "front": [], "back": [],
        },
    },

    # ── Lifted chair_left h=2 ─────────────────────────────────────────────────

    "chair_left_h2_v1": {
        "id": "chair_left_h2_v1", "w": 2, "h": 2, "d": 3, "zone": "chair_left",
        "description": "Left chair h=2, closed rectangular seat.",
        "tags": ["lifted", "chair_left", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
            [(1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.5, 2.0), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 2.0)], "bottom": [], "left": [], "right": [(2.0, 0.5)]}),
    },

    "chair_left_h2_v2": {
        "id": "chair_left_h2_v2", "w": 2, "h": 2, "d": 3, "zone": "chair_left",
        "description": "Left chair h=2, single minimal polyline.",
        "tags": ["lifted", "chair_left", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.0), (0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.5, 2.0), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 2.0)], "bottom": [], "left": [], "right": [(2.0, 0.5)]}),
    },

    "chair_left_h2_v3": {
        "id": "chair_left_h2_v3", "w": 2, "h": 2, "d": 3, "zone": "chair_left",
        "description": "Left chair h=2, V-tip at seat base.",
        "tags": ["lifted", "chair_left", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.0), (0.5, 1.5), (1.5, 1.5), (1.0, 0.5), (2.0, 0.5)],
        ], ex={(0.5, 2.0), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 2.0)], "bottom": [], "left": [], "right": [(2.0, 0.5)]}),
    },

    # ── Lifted chair_left h=3 ─────────────────────────────────────────────────

    "chair_left_h3_v1": {
        "id": "chair_left_h3_v1", "w": 2, "h": 3, "d": 3, "zone": "chair_left",
        "description": "Left chair h=3, tall closed rectangular seat.",
        "tags": ["lifted", "chair_left", "h3"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 1.5)],
            [(0.5, 2.5), (1.5, 2.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.5, 3.0), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "bottom": [], "left": [], "right": [(2.0, 0.5)]}),
    },

    "chair_left_h3_v3": {
        "id": "chair_left_h3_v3", "w": 2, "h": 3, "d": 3, "zone": "chair_left",
        "description": "Left chair h=3, single polyline through seat.",
        "tags": ["lifted", "chair_left", "h3"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 2.5), (1.5, 2.5), (1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.5, 3.0), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "bottom": [], "left": [], "right": [(2.0, 0.5)]}),
    },

    # ── Lifted chair_right h=2 ────────────────────────────────────────────────

    "chair_right_h2_v1": {
        "id": "chair_right_h2_v1", "w": 2, "h": 2, "d": 3, "zone": "chair_right",
        "description": "Right chair h=2, closed rectangular seat.",
        "tags": ["lifted", "chair_right", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5)],
            [(1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (1.5, 0.5), (1.5, 1.5)],
            [(0.5, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 2.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    "chair_right_h2_v2": {
        "id": "chair_right_h2_v2", "w": 2, "h": 2, "d": 3, "zone": "chair_right",
        "description": "Right chair h=2, single minimal polyline.",
        "tags": ["lifted", "chair_right", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 2.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    "chair_right_h2_v3": {
        "id": "chair_right_h2_v3", "w": 2, "h": 2, "d": 3, "zone": "chair_right",
        "description": "Right chair h=2, V-tip at seat base.",
        "tags": ["lifted", "chair_right", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (1.0, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 2.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    # ── Lifted tv_table h=2 (Living) ─────────────────────────────────────────

    "tv_table_h2_v1": {
        "id": "tv_table_h2_v1", "w": 2, "h": 2, "d": 3, "zone": "tv_table",
        "description": "TV table h=2, closed rectangular shelf.",
        "tags": ["lifted", "tv_table", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5)],
            [(1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (1.5, 0.5), (1.5, 1.5)],
            [(0.5, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 2.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    "tv_table_h2_v2": {
        "id": "tv_table_h2_v2", "w": 2, "h": 2, "d": 3, "zone": "tv_table",
        "description": "TV table h=2, single minimal polyline.",
        "tags": ["lifted", "tv_table", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 2.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    "tv_table_h2_v3": {
        "id": "tv_table_h2_v3", "w": 2, "h": 2, "d": 3, "zone": "tv_table",
        "description": "TV table h=2, V-tip at base.",
        "tags": ["lifted", "tv_table", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (1.0, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 2.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    # ── Lifted chair_right h=3 ────────────────────────────────────────────────

    "chair_right_h3_v1": {
        "id": "chair_right_h3_v1", "w": 2, "h": 3, "d": 3, "zone": "chair_right",
        "description": "Right chair h=3, tall closed rectangular seat.",
        "tags": ["lifted", "chair_right", "h3"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 3.0), (1.5, 2.5)],
            [(1.5, 2.5), (0.5, 2.5), (0.5, 0.5), (1.5, 0.5), (1.5, 2.5)],
            [(0.5, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 3.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 3.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    "chair_right_h3_v3": {
        "id": "chair_right_h3_v3", "w": 2, "h": 3, "d": 3, "zone": "chair_right",
        "description": "Right chair h=3, single polyline through seat.",
        "tags": ["lifted", "chair_right", "h3"], "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 3.0), (1.5, 2.5), (0.5, 2.5), (0.5, 0.5), (0.0, 0.5)],
        ], ex={(1.5, 3.0), (0.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 3.0)], "bottom": [], "left": [(0.0, 0.5)], "right": []}),
    },

    # ── Lifted table h=2 ──────────────────────────────────────────────────────

    "table_h2_v1": {
        "id": "table_h2_v1", "w": 2, "h": 2, "d": 3, "zone": "table",
        "description": "Table h=2, V-tip legs below mid bar.",
        "tags": ["lifted", "table", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 1.5), (1.5, 1.5)],
            [(0.5, 1.5), (1.0, 0.5)],
            [(1.5, 1.5), (1.0, 0.5)],
            [(1.0, 0.5), (0.0, 0.5)],
            [(1.0, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "table_h2_v3": {
        "id": "table_h2_v3", "w": 2, "h": 2, "d": 3, "zone": "table",
        "description": "Table h=2, rectangular frame with vertical legs.",
        "tags": ["lifted", "table", "h2"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 1.5), (1.5, 1.5)],
            [(0.5, 1.5), (0.5, 0.5), (0.0, 0.5)],
            [(1.5, 1.5), (1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    # ── Lifted table h=3 ──────────────────────────────────────────────────────

    "table_h3_v1": {
        "id": "table_h3_v1", "w": 2, "h": 3, "d": 3, "zone": "table",
        "description": "Table h=3, V-tip legs below raised bar.",
        "tags": ["lifted", "table", "h3"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.5), (1.5, 2.5)],
            [(0.5, 2.5), (1.0, 0.5)],
            [(1.5, 2.5), (1.0, 0.5)],
            [(1.0, 0.5), (0.0, 0.5)],
            [(1.0, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "table_h3_v3": {
        "id": "table_h3_v3", "w": 2, "h": 3, "d": 3, "zone": "table",
        "description": "Table h=3, rectangular frame with tall vertical legs.",
        "tags": ["lifted", "table", "h3"], "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.5), (1.5, 2.5)],
            [(0.5, 2.5), (0.5, 0.5), (0.0, 0.5)],
            [(1.5, 2.5), (1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    # ── Wide-top table variants (spacious dining, W=8) ────────────────────────
    # Top bar spans x=0→2, connecting into gap filler cells on each side.

    "table_h2_v5": {
        "id": "table_h2_v5", "w": 2, "h": 2, "d": 3, "zone": "table",
        "description": "Table h=2, full-width top bar, inward-diagonal legs splaying to side ports. Spacious mode.",
        "tags": ["lifted", "table", "h2", "wide-top"], "scalable_d": True,
        # (0.0,1.5) and (2.0,1.5) kept outside ex → z-connectors at bar corners link front and back.
        "segments": _lift2d([
            [(0.0, 1.5), (2.0, 1.5)],
            [(0.0, 1.5), (0.5, 0.5), (0.0, 0.5)],
            [(2.0, 1.5), (1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "table_h2_v6": {
        "id": "table_h2_v6", "w": 2, "h": 2, "d": 3, "zone": "table",
        "description": "Table h=2, full-width top bar, A-frame legs meeting at a central base. Spacious mode.",
        "tags": ["lifted", "table", "h2", "wide-top"], "scalable_d": True,
        # Bar corners and central base all outside ex → z-connectors connect front and back at those points.
        "segments": _lift2d([
            [(0.0, 1.5), (2.0, 1.5)],
            [(0.0, 1.5), (1.0, 0.5)],
            [(2.0, 1.5), (1.0, 0.5)],
            [(1.0, 0.5), (0.0, 0.5)],
            [(1.0, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "table_h3_v2": {
        "id": "table_h3_v2", "w": 2, "h": 3, "d": 3, "zone": "table",
        "description": "Table h=3, full-width top bar, diagonal legs splaying to side ports. Spacious mode.",
        "tags": ["lifted", "table", "h3", "wide-top"], "scalable_d": True,
        # (0.0,2.5) and (2.0,2.5) outside ex → z-connectors at bar corners.
        "segments": _lift2d([
            [(0.0, 2.5), (2.0, 2.5)],
            [(0.0, 2.5), (0.5, 0.5), (0.0, 0.5)],
            [(2.0, 2.5), (1.5, 0.5), (2.0, 0.5)],
        ], ex={(0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [], "bottom": [], "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

}


# ── Scalable shelf geometry helpers ──────────────────────────────────────────
# These are called by whd_segments_fn / whd_ports_fn so shelves work at any W.

def _sh_ports(w, h, d):
    return _ports_lift({"bottom": [(0.5, 0.0), (w - 0.5, 0.0)],
                        "top": [], "left": [], "right": []}, d=d)

def _sh_u(w, h, d):
    t = h - 0.5
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, t)],
                    [(w - 0.5, 0.0), (w - 0.5, t)],
                    [(0.5, t), (w - 0.5, t)]], d=d, ex=_ex)

def _sh_u_mid(w, h, d):
    t = h - 0.5
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, t)],
                    [(w - 0.5, 0.0), (w - 0.5, t)],
                    [(0.5, t), (w - 0.5, t)],
                    [(0.5, 0.5), (w - 0.5, 0.5)]], d=d, ex=_ex)

def _sh_lean_r(w, h, d):
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, h - 1.0)],
                    [(w - 0.5, 0.0), (w - 0.5, h - 0.5)],
                    [(0.5, h - 1.0), (w - 0.5, h - 0.5)]], d=d, ex=_ex)

def _sh_lean_l(w, h, d):
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, h - 0.5)],
                    [(w - 0.5, 0.0), (w - 0.5, h - 1.0)],
                    [(0.5, h - 0.5), (w - 0.5, h - 1.0)]], d=d, ex=_ex)

def _sh_pitch_steep(w, h, d):
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, h - 1.0)],
                    [(w - 0.5, 0.0), (w - 0.5, h - 1.0)],
                    [(0.5, h - 1.0), (w / 2, float(h)), (w - 0.5, h - 1.0)]], d=d, ex=_ex)

def _sh_pitch_gentle(w, h, d):
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, h - 1.0)],
                    [(w - 0.5, 0.0), (w - 0.5, h - 1.0)],
                    [(0.5, h - 1.0), (w / 2, h - 0.5), (w - 0.5, h - 1.0)]], d=d, ex=_ex)

def _sh_divider(w, h, d):
    lo, hi = 1.0, h - 0.5
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, lo), (0.5, hi)],
                    [(w - 0.5, 0.0), (w - 0.5, lo), (w - 0.5, hi)],
                    [(0.5, lo), (w / 2, lo), (w - 0.5, lo)],
                    [(0.5, hi), (w / 2, hi), (w - 0.5, hi)],
                    [(w / 2, lo), (w / 2, hi)]], d=d, ex=_ex)

def _sh_steep_diag(w, h, d):
    _ex = {(0.5, 0.0), (w - 0.5, 0.0)}
    return _lift2d([[(0.5, 0.0), (0.5, h - 0.5)],
                    [(w - 0.5, 0.0), (w - 0.5, 0.5)],
                    [(0.5, h - 0.5), (w - 0.5, 0.5)]], d=d, ex=_ex)


# ── Corridor-variant shelf helpers ────────────────────────────────────────────
# Each adds a short stub from the existing eave endpoint to the module boundary
# (right or left face) so the shelf can port-match the corridor's inner wall.
# Only variants where the relevant post already reaches y=h-0.5 are supported.

def _sh_u_corr_r(w, h, d):
    return _sh_u(w, h, d)       + _lift2d([[(w - 0.5, h - 0.5), (float(w), h - 0.5)]], d=d, ex={(float(w), h - 0.5)})

def _sh_u_mid_corr_r(w, h, d):
    return _sh_u_mid(w, h, d)   + _lift2d([[(w - 0.5, h - 0.5), (float(w), h - 0.5)]], d=d, ex={(float(w), h - 0.5)})

def _sh_lean_r_corr_r(w, h, d):
    return _sh_lean_r(w, h, d)  + _lift2d([[(w - 0.5, h - 0.5), (float(w), h - 0.5)]], d=d, ex={(float(w), h - 0.5)})

def _sh_divider_corr_r(w, h, d):
    return _sh_divider(w, h, d) + _lift2d([[(w - 0.5, h - 0.5), (float(w), h - 0.5)]], d=d, ex={(float(w), h - 0.5)})

def _sh_u_corr_l(w, h, d):
    return _sh_u(w, h, d)       + _lift2d([[(0.5, h - 0.5), (0.0, h - 0.5)]], d=d, ex={(0.0, h - 0.5)})

def _sh_u_mid_corr_l(w, h, d):
    return _sh_u_mid(w, h, d)   + _lift2d([[(0.5, h - 0.5), (0.0, h - 0.5)]], d=d, ex={(0.0, h - 0.5)})

def _sh_lean_l_corr_l(w, h, d):
    return _sh_lean_l(w, h, d)  + _lift2d([[(0.5, h - 0.5), (0.0, h - 0.5)]], d=d, ex={(0.0, h - 0.5)})

def _sh_divider_corr_l(w, h, d):
    return _sh_divider(w, h, d) + _lift2d([[(0.5, h - 0.5), (0.0, h - 0.5)]], d=d, ex={(0.0, h - 0.5)})

def _sh_ports_corr_r(w, h, d):
    p = _sh_ports(w, h, d)
    return {**p, "right": [(float(w), h - 0.5, 1.0), (float(w), h - 0.5, 2.0)]}

def _sh_ports_corr_l(w, h, d):
    p = _sh_ports(w, h, d)
    return {**p, "left":  [(0.0, h - 0.5, 1.0), (0.0, h - 0.5, 2.0)]}


# ── Corridor geometry helpers ─────────────────────────────────────────────────
# Open U-brackets: inner-wall endpoints are declared as ports, matched by
# chair_right_corr (at y=0.5) and shelf_corr_r (at y=h-0.5) variants.

def _corr_r_segs(w, h, d):
    """Right-side corridor: outer wall at x=w-0.5, open face at x=0 (dining side)."""
    return _lift2d([
        [(0.0, 0.5), (w - 0.5, 0.5), (w - 0.5, h - 0.5), (0.0, h - 0.5)]
    ], d=d, ex={(0.0, 0.5), (0.0, h - 0.5)})

def _corr_l_segs(w, h, d):
    """Left-side corridor: outer wall at x=0.5, open face at x=w (dining side)."""
    return _lift2d([
        [(float(w), 0.5), (0.5, 0.5), (0.5, h - 0.5), (float(w), h - 0.5)]
    ], d=d, ex={(float(w), 0.5), (float(w), h - 0.5)})

def _corr_r_ports(w, h, d):
    return _ports_lift({"left":  [(0.0, 0.5), (0.0, h - 0.5)],
                        "right": [], "top": [], "bottom": []}, d=d)

def _corr_l_ports(w, h, d):
    return _ports_lift({"right": [(float(w), 0.5), (float(w), h - 0.5)],
                        "left":  [], "top": [], "bottom": []}, d=d)


def _corr_r_short_segs(w, h, d):
    """Short right corridor: floor arm + outer wall to y=h (L-shape)."""
    return _lift2d([[(0.0, 0.5), (w - 0.5, 0.5), (w - 0.5, h)]], d=d,
                   ex={(0.0, 0.5), (w - 0.5, float(h))})

def _corr_l_short_segs(w, h, d):
    """Short left corridor: floor arm + outer wall to y=h (L-shape)."""
    return _lift2d([[(float(w), 0.5), (0.5, 0.5), (0.5, h)]], d=d,
                   ex={(float(w), 0.5), (0.5, float(h))})

def _corr_r_short_ports(w, h, d):
    return _ports_lift({"left": [(0.0, 0.5)], "right": [], "top": [(w - 0.5, h)], "bottom": []}, d=d)

def _corr_l_short_ports(w, h, d):
    return _ports_lift({"left": [], "right": [(float(w), 0.5)], "top": [(0.5, h)], "bottom": []}, d=d)


# ── Lifted shelf modules (scalable_w=True → fit any section width) ───────────

MODULES_3D.update({

    # ── h=1 ──────────────────────────────────────────────────────────────────

    "shelf_h1_v1": {
        "id": "shelf_h1_v1", "w": 6, "h": 1, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Shelf h=1, simple U-bracket.",
        "tags": ["lifted", "shelf", "h1", "plain"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 0.5)],
            [(5.5, 0.0), (5.5, 0.5)],
            [(0.5, 0.5), (5.5, 0.5)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_u,
        "whd_ports_fn":    _sh_ports,
    },

    # ── h=2 ──────────────────────────────────────────────────────────────────

    "shelf_h2_v1": {
        "id": "shelf_h2_v1", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Shelf h=2, U-bracket with mid shelf.",
        "tags": ["lifted", "shelf", "h2", "plain"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 1.5)],
            [(5.5, 0.0), (5.5, 1.5)],
            [(0.5, 1.5), (5.5, 1.5)],
            [(0.5, 0.5), (5.5, 0.5)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_u_mid,
        "whd_ports_fn":    _sh_ports,
    },

    "shelf_h2_v2": {
        "id": "shelf_h2_v2", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Shelf h=2, tall left post, lean-to diagonal.",
        "tags": ["lifted", "shelf", "h2", "pitched"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 1.5)],
            [(5.5, 0.0), (5.5, 0.5)],
            [(0.5, 1.5), (5.5, 0.5)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_lean_l,
        "whd_ports_fn":    _sh_ports,
    },

    "shelf_h2_v3": {
        "id": "shelf_h2_v3", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Shelf h=2, tall right post, lean-to diagonal.",
        "tags": ["lifted", "shelf", "h2", "pitched"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 0.5)],
            [(5.5, 0.0), (5.5, 1.5)],
            [(0.5, 0.5), (5.5, 1.5)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_lean_r,
        "whd_ports_fn":    _sh_ports,
    },

    "shelf_pitched_sym_v1": {
        "id": "shelf_pitched_sym_v1", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Pitched shelf h=2, centred ridge, steep.",
        "tags": ["lifted", "shelf", "h2", "pitched"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 1.0)],
            [(5.5, 0.0), (5.5, 1.0)],
            [(0.5, 1.0), (3.0, 2.0), (5.5, 1.0)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_pitch_steep,
        "whd_ports_fn":    _sh_ports,
    },

    "shelf_pitched_sym_v2": {
        "id": "shelf_pitched_sym_v2", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Pitched shelf h=2, centred ridge, gentle.",
        "tags": ["lifted", "shelf", "h2", "pitched"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 1.0)],
            [(5.5, 0.0), (5.5, 1.0)],
            [(0.5, 1.0), (3.0, 1.5), (5.5, 1.0)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_pitch_gentle,
        "whd_ports_fn":    _sh_ports,
    },

    # ── h=3 ──────────────────────────────────────────────────────────────────

    "shelf_h3_v1": {
        "id": "shelf_h3_v1", "w": 6, "h": 3, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Shelf h=3, U-bracket with central divider.",
        "tags": ["lifted", "shelf", "h3", "divided"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 1.0), (0.5, 2.5)],
            [(5.5, 0.0), (5.5, 1.0), (5.5, 2.5)],
            [(0.5, 1.0), (3.0, 1.0), (5.5, 1.0)],
            [(0.5, 2.5), (3.0, 2.5), (5.5, 2.5)],
            [(3.0, 1.0), (3.0, 2.5)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_divider,
        "whd_ports_fn":    _sh_ports,
    },

    "shelf_h3_v2": {
        "id": "shelf_h3_v2", "w": 6, "h": 3, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "description": "Shelf h=3, tall left post, steep diagonal.",
        "tags": ["lifted", "shelf", "h3", "pitched"],
        "segments": _lift2d([
            [(0.5, 0.0), (0.5, 2.5)],
            [(5.5, 0.0), (5.5, 0.5)],
            [(0.5, 2.5), (5.5, 0.5)],
        ]),
        "ports": _ports_lift({"top": [], "bottom": [(0.5, 0.0), (5.5, 0.0)], "left": [], "right": []}),
        "whd_segments_fn": _sh_steep_diag,
        "whd_ports_fn":    _sh_ports,
    },

    # ── Corridor modules (extruded from 2D, scalable w+h) ─────────────────────

    "corridor_right_3d": {
        "id": "corridor_right_3d", "w": 2, "h": 7, "d": 3,
        "zone": "corridor_right",
        "scalable_w": True, "scalable_h": True,
        "description": "Right-side corridor — open U-bracket, left-face ports at y=0.5 and y=h-0.5.",
        "tags": ["lifted", "corridor", "right"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _corr_r_segs,
        "whd_ports_fn":    _corr_r_ports,
    },

    "corridor_left_3d": {
        "id": "corridor_left_3d", "w": 2, "h": 7, "d": 3,
        "zone": "corridor_left",
        "scalable_w": True, "scalable_h": True,
        "description": "Left-side corridor — open U-bracket, right-face ports at y=0.5 and y=h-0.5.",
        "tags": ["lifted", "corridor", "left"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _corr_l_segs,
        "whd_ports_fn":    _corr_l_ports,
    },

    "corridor_right_3d_short": {
        "id": "corridor_right_3d_short", "w": 2, "h": 6, "d": 3,
        "zone": "corridor_right",
        "scalable_w": True, "scalable_h": True,
        "description": "Short right corridor — L-shape floor+outer wall, left port + top port.",
        "tags": ["lifted", "corridor", "right", "short"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _corr_r_short_segs,
        "whd_ports_fn":    _corr_r_short_ports,
    },

    "corridor_left_3d_short": {
        "id": "corridor_left_3d_short", "w": 2, "h": 6, "d": 3,
        "zone": "corridor_left",
        "scalable_w": True, "scalable_h": True,
        "description": "Short left corridor — L-shape floor+outer wall, right port + top port.",
        "tags": ["lifted", "corridor", "left", "short"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _corr_l_short_segs,
        "whd_ports_fn":    _corr_l_short_ports,
    },

    # ── Sofa (Living) ─────────────────────────────────────────────────────────

    "sofa_h3_v4_3d": {
        "id": "sofa_h3_v4_3d", "w": 4, "h": 3, "d": 3,
        "zone": "sofa",
        "scalable_d": False,
        "description": "Sofa v4, w=4 h=3 d=3 -- native 3D organic curved shape with rounded armrests.",
        "tags": ["sofa", "h3", "living", "native-3d", "organic", "curved", "w4"],
        "segments": [
            # arm profile arc at x=1.124 (spans full depth)
            [(1.124,1.111,0.5),(1.124,1.348,0.524),(1.124,1.570,0.608),(1.124,1.721,0.785),(1.124,1.725,1.023),(1.124,1.725,1.261),(1.124,1.725,1.5),(1.124,1.725,1.738),(1.124,1.725,1.977),(1.124,1.721,2.215),(1.124,1.570,2.391),(1.124,1.348,2.475),(1.124,1.111,2.5)],
            # front face main arc (z=0.5)
            [(1.124,1.111,0.5),(1.251,0.740,0.5),(1.579,0.521,0.5),(1.979,0.5,0.5),(2.380,0.5,0.5),(2.781,0.507,0.5),(3.131,0.689,0.5),(3.298,1.046,0.5),(3.302,1.448,0.5),(3.302,1.849,0.5),(3.281,2.249,0.5),(3.062,2.577,0.5),(2.689,2.704,0.5)],
            # back face floor line (z=2.5)
            [(1.738,0.5,2.5),(2.689,0.5,2.5)],
            # back face lower-left arc (z=2.5)
            [(1.124,1.114,2.5),(1.129,1.033,2.5),(1.145,0.955,2.5),(1.171,0.879,2.5),(1.206,0.807,2.5),(1.251,0.740,2.5),(1.304,0.680,2.5),(1.364,0.627,2.5),(1.431,0.582,2.5),(1.503,0.547,2.5),(1.579,0.521,2.5),(1.657,0.505,2.5),(1.738,0.5,2.5)],
            # depth rail at x=3.302, y=1.725
            [(3.302,1.725,0.5),(3.302,1.725,2.5)],
            # back face right exit (z=2.5)
            [(2.689,0.5,2.5),(4.0,0.5,2.5)],
            # back face upper-right arc (z=2.5)
            [(3.302,2.090,2.5),(3.297,2.170,2.5),(3.281,2.249,2.5),(3.255,2.325,2.5),(3.220,2.397,2.5),(3.175,2.464,2.5),(3.122,2.524,2.5),(3.062,2.577,2.5),(2.995,2.622,2.5),(2.923,2.657,2.5),(2.847,2.683,2.5),(2.769,2.698,2.5),(2.689,2.704,2.5)],
            # back face right vertical (z=2.5)
            [(3.302,1.114,2.5),(3.302,2.090,2.5)],
            # back face lower-right arc (z=2.5)
            [(2.689,0.5,2.5),(2.769,0.505,2.5),(2.847,0.521,2.5),(2.923,0.547,2.5),(2.995,0.582,2.5),(3.062,0.627,2.5),(3.122,0.680,2.5),(3.175,0.740,2.5),(3.220,0.807,2.5),(3.255,0.879,2.5),(3.281,0.955,2.5),(3.297,1.033,2.5),(3.302,1.114,2.5)],
            # back face top stem
            [(0.5,2.090,2.5),(0.5,3.0,2.5)],
            # back face upper-left arc (z=2.5)
            [(0.5,2.090,2.5),(0.536,2.298,2.5),(0.640,2.481,2.5),(0.800,2.618,2.5),(0.997,2.692,2.5),(1.208,2.704,2.5),(1.419,2.704,2.5),(1.631,2.704,2.5),(1.842,2.704,2.5),(2.054,2.704,2.5),(2.265,2.704,2.5),(2.477,2.704,2.5),(2.689,2.704,2.5)],
            # side arc at y=2.704 connecting front and back
            [(1.461,2.704,2.5),(1.225,2.704,2.475),(1.002,2.704,2.391),(0.852,2.704,2.215),(0.848,2.704,1.977),(0.848,2.704,1.738),(0.848,2.704,1.5),(0.848,2.704,1.261),(0.848,2.704,1.023),(0.852,2.704,0.785),(1.002,2.704,0.608),(1.225,2.704,0.524),(1.461,2.704,0.5)],
            # front face upper-left arc (z=0.5)
            [(0.5,2.090,0.5),(0.536,2.298,0.5),(0.640,2.481,0.5),(0.800,2.618,0.5),(0.997,2.692,0.5),(1.208,2.704,0.5),(1.419,2.704,0.5),(1.631,2.704,0.5),(1.842,2.704,0.5),(2.054,2.704,0.5),(2.265,2.704,0.5),(2.477,2.704,0.5),(2.689,2.704,0.5)],
            # front face top stem
            [(0.5,2.090,0.5),(0.5,3.0,0.5)],
            # front face right exit
            [(2.689,0.5,0.5),(4.0,0.5,0.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0, 0.5), (0.5, 3.0, 2.5)],
            "right":  [(4.0, 0.5, 0.5), (4.0, 0.5, 2.5)],
            "bottom": [], "left": [], "front": [], "back": [],
        },
    },

    "sofa_h3_v3_3d": {
        "id": "sofa_h3_v3_3d", "w": 3, "h": 3, "d": 3,
        "zone": "sofa",
        "scalable_d": False,
        "description": "Sofa v3, w=3 h=3 d=3 -- native 3D with rounded hexagonal profile and curved backrest.",
        "tags": ["sofa", "h3", "living", "native-3d", "rounded", "curved"],
        "segments": [
            # front face (z=0.5): hexagonal sofa outline
            [(0.5,0.5,0.5),(0.5,1.5,0.5),(1.0,2.0,0.5),(2.0,2.0,0.5),(2.5,1.5,0.5),(2.5,0.5,0.5),(0.5,0.5,0.5)],
            # front face: backrest curve
            [(0.5,2.5,0.5),(1.0,1.5,0.5),(2.5,1.5,0.5)],
            # right exit front
            [(2.5,0.5,0.5),(3.0,0.5,0.5)],
            # top port stem front
            [(0.5,2.5,0.5),(0.5,3.0,0.5)],
            # back face (z=2.5): same hexagonal outline
            [(0.5,0.5,2.5),(0.5,1.5,2.5),(1.0,2.0,2.5),(2.0,2.0,2.5),(2.5,1.5,2.5),(2.5,0.5,2.5),(0.5,0.5,2.5)],
            # back face: backrest curve
            [(0.5,2.5,2.5),(1.0,1.5,2.5),(2.5,1.5,2.5)],
            # right exit back
            [(2.5,0.5,2.5),(3.0,0.5,2.5)],
            # top port stem back
            [(0.5,2.5,2.5),(0.5,3.0,2.5)],
            # depth rails
            [(2.5,1.5,0.5),(2.5,1.5,2.5)],
            [(1.0,1.5,0.5),(1.0,1.5,2.5)],
            [(0.5,2.5,0.5),(0.5,2.5,2.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0, 0.5), (0.5, 3.0, 2.5)],
            "right":  [(3.0, 0.5, 0.5), (3.0, 0.5, 2.5)],
            "bottom": [], "left": [], "front": [], "back": [],
        },
    },

    "sofa_h3_v2_3d": {
        "id": "sofa_h3_v2_3d", "w": 3, "h": 3, "d": 3,
        "zone": "sofa",
        "scalable_d": False,
        "description": "Sofa v2, w=3 h=3 d=3 -- native 3D with diagonal profile and cross-rails.",
        "tags": ["sofa", "h3", "living", "native-3d", "diagonal"],
        "segments": [
            # right exit front (y=0.5, z=0.5)
            [(2.5, 0.5, 0.5), (3.0, 0.5, 0.5)],
            # front bottom: horizontal then rising
            [(0.5, 0.5, 0.5), (2.5, 0.5, 0.5), (2.5, 1.5, 0.5)],
            # front cross-rail at h=1.5
            [(2.5, 1.5, 0.5), (0.5, 1.5, 0.5)],
            # diagonal from front to back + top port stem
            [(0.5, 0.5, 0.5), (1.5, 2.5, 0.5), (0.5, 2.5, 0.5), (0.5, 3.0, 0.5)],
            # right exit back (y=0.5, z=2.5)
            [(2.5, 0.5, 2.5), (3.0, 0.5, 2.5)],
            # back face path (z=2.5)
            [(0.5, 3.0, 2.5), (0.5, 2.5, 2.5), (1.5, 2.5, 2.5),
             (0.5, 0.5, 2.5), (2.5, 0.5, 2.5), (2.5, 1.5, 2.5), (0.5, 1.5, 2.5)],
            # depth rail at h=1.5, x=2.5
            [(2.5, 1.5, 0.5), (2.5, 1.5, 2.5)],
            # depth rail at h=1.5, x=0.5
            [(0.5, 1.5, 0.5), (0.5, 1.5, 2.5)],
            # depth rail at h=2.5, x=0.5
            [(0.5, 2.5, 0.5), (0.5, 2.5, 2.5)],
        ],
        "ports": {
            "top":    [(0.5, 3.0, 0.5), (0.5, 3.0, 2.5)],
            "right":  [(3.0, 0.5, 0.5), (3.0, 0.5, 2.5)],
            "bottom": [], "left": [], "front": [], "back": [],
        },
    },

    "sofa_h3_v1_3d": {
        "id": "sofa_h3_v1_3d", "w": 3, "h": 3, "d": 3,
        "zone": "sofa",
        "scalable_d": True,
        "description": "Sofa h=3 w=3, lifted from 2D geometry — spacious.",
        "tags": ["lifted", "sofa", "h3", "living", "spacious"],
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 2.5), (1.0, 2.5), (1.0, 1.5), (2.5, 1.5),
             (2.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(2.5, 0.5), (3.0, 0.5)],
        ], ex={(0.5, 3.0), (3.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "bottom": [], "left": [], "right": [(3.0, 0.5)]}),
    },

})


# ── Shelf style categories (for roof_style filter in solver3d) ────────────────
# plain:   flat horizontal bar
# divided: internal subdivisions
# pitched: gable ridge

_SHELF_CAT_3D: dict = {
    "shelf_h1_v1":         "plain",
    "shelf_h2_v1":         "plain",
    "shelf_h2_v2":         "plain",
    "shelf_h2_v3":         "plain",
    "shelf_pitched_sym_v1":"pitched",
    "shelf_h3_v1":         "divided",
    "shelf_h3_v2":         "plain",
    "roof_3d_v1":          "plain",
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_segments_3d(mod: dict, w: int, h: int, d: int) -> list:
    if "whd_segments_fn" in mod:
        return mod["whd_segments_fn"](w, h, d)
    segs = mod.get("segments", [])
    if mod.get("scalable_d") and d != mod.get("d", 3):
        return _scale_segs_d(segs, mod.get("d", 3), d)
    return segs


@lru_cache(maxsize=512)
def _get_ports_3d_cached(mod_id: str, w: int, h: int, d: int) -> dict:
    mod = MODULES_3D[mod_id]
    if "whd_ports_fn" in mod:
        return mod["whd_ports_fn"](w, h, d)
    ports = mod.get("ports", {face: [] for face in FACES_3D})
    if mod.get("scalable_d") and d != mod.get("d", 3):
        return _scale_ports_d(ports, mod.get("d", 3), d)
    return ports


def get_ports_3d(mod: dict, w: int, h: int, d: int) -> dict:
    return _get_ports_3d_cached(mod["id"], w, h, d)


# ── Zone definitions ──────────────────────────────────────────────────────────
# chairs+table: "first N" rows.  shelf/roof: "last N" rows.
# Gaps between them are filled by filler_pass_v_3d (at port columns x=0,5)
# and filler_empty_3d (all other gap cells).

ZONES_3D = [
    {
        "id":      "chair_left",
        "x_rule":  ["first 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "chair_left_3d_v1",
            "chair_left_h2_v1", "chair_left_h2_v2", "chair_left_h2_v3",
            "chair_left_h3_v1", "chair_left_h3_v3",
        ],
    },
    {
        "id":      "table",
        "x_rule":  ["middle 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "table_3d_v1",
            "table_h2_v1", "table_h2_v3",
            "table_h3_v1", "table_h3_v3",
            "table_h2_v5", "table_h2_v6",
            "table_h3_v2",
        ],
    },
    {
        "id":      "chair_right",
        "x_rule":  ["last 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "chair_right_3d_v1",
            "chair_right_h2_v1", "chair_right_h2_v2", "chair_right_h2_v3",
            "chair_right_h3_v1", "chair_right_h3_v3",
        ],
    },
    {
        "id":      "shelf",
        "x_rule":  ["full"],
        "y_rule":  ["last 1", "last 2", "last 3"],
        "z_rule":  ["full"],
        "modules": [
            "roof_3d_v1",
            "shelf_h1_v1",
            "shelf_h2_v1", "shelf_h2_v2", "shelf_h2_v3",
            "shelf_pitched_sym_v1", "shelf_pitched_sym_v2",
            "shelf_h3_v1", "shelf_h3_v2",
        ],
    },
]

# ── Table module groups (mirrors 2D _TABLE_COMPACT / _TABLE_SPACIOUS) ─────────
# Compact (no wide-top): chairs flush against table, dining zone W=6.
# Spacious (wide-top):   1-col filler gap each side, dining zone W=8.
_TABLE_COMPACT_3D  = [m for m in ZONES_3D[1]["modules"] if "wide-top" not in MODULES_3D[m].get("tags", [])]
_TABLE_SPACIOUS_3D = [m for m in ZONES_3D[1]["modules"] if "wide-top"     in MODULES_3D[m].get("tags", [])]

# ── Corridor-variant modules ──────────────────────────────────────────────────
# chair_right_corr_r: adds a right stub at seat height so the module ports-match
# corridor_right_3d's left face.  Only loop-based variants (v1/v3) are supported
# because the stub must attach to an existing junction point.
# chair_left_corr_l: symmetric, adds a left stub for corridor_left_3d.

MODULES_3D.update({

    # ── chair_right corr_r variants ───────────────────────────────────────────

    "chair_right_h2_v1_corr_r": {
        "id": "chair_right_h2_v1_corr_r", "w": 2, "h": 2, "d": 3, "zone": "chair_right",
        "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5)],
            [(1.5, 1.5), (0.5, 1.5), (0.5, 0.5), (1.5, 0.5), (1.5, 1.5)],
            [(0.5, 0.5), (0.0, 0.5)],
            [(1.5, 0.5), (2.0, 0.5)],   # stub to corridor
        ], ex={(1.5, 2.0), (0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [],
                               "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "chair_right_h2_v3_corr_r": {
        "id": "chair_right_h2_v3_corr_r", "w": 2, "h": 2, "d": 3, "zone": "chair_right",
        "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 2.0), (1.5, 1.5), (0.5, 1.5), (1.0, 0.5), (0.0, 0.5)],
            [(1.0, 0.5), (2.0, 0.5)],   # stub from V-tip to corridor
        ], ex={(1.5, 2.0), (0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 2.0)], "bottom": [],
                               "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "chair_right_h3_v1_corr_r": {
        "id": "chair_right_h3_v1_corr_r", "w": 2, "h": 3, "d": 3, "zone": "chair_right",
        "scalable_d": True,
        "segments": _lift2d([
            [(1.5, 3.0), (1.5, 2.5)],
            [(1.5, 2.5), (0.5, 2.5), (0.5, 0.5), (1.5, 0.5), (1.5, 2.5)],
            [(0.5, 0.5), (0.0, 0.5)],
            [(1.5, 0.5), (2.0, 0.5)],   # stub to corridor
        ], ex={(1.5, 3.0), (0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(1.5, 3.0)], "bottom": [],
                               "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    # ── chair_left corr_l variants ────────────────────────────────────────────

    "chair_left_h2_v1_corr_l": {
        "id": "chair_left_h2_v1_corr_l", "w": 2, "h": 2, "d": 3, "zone": "chair_left",
        "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.0), (0.5, 1.5)],
            [(0.5, 1.5), (1.5, 1.5), (1.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
            [(1.5, 0.5), (2.0, 0.5)],
            [(0.5, 0.5), (0.0, 0.5)],   # stub to corridor
        ], ex={(0.5, 2.0), (0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 2.0)], "bottom": [],
                               "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "chair_left_h2_v3_corr_l": {
        "id": "chair_left_h2_v3_corr_l", "w": 2, "h": 2, "d": 3, "zone": "chair_left",
        "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 2.0), (0.5, 1.5), (1.5, 1.5), (1.0, 0.5), (2.0, 0.5)],
            [(1.0, 0.5), (0.0, 0.5)],   # stub from V-tip to corridor
        ], ex={(0.5, 2.0), (0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 2.0)], "bottom": [],
                               "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    "chair_left_h3_v1_corr_l": {
        "id": "chair_left_h3_v1_corr_l", "w": 2, "h": 3, "d": 3, "zone": "chair_left",
        "scalable_d": True,
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 1.5)],
            [(0.5, 2.5), (1.5, 2.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(1.5, 0.5), (2.0, 0.5)],
            [(0.5, 0.5), (0.0, 0.5)],   # stub to corridor
        ], ex={(0.5, 3.0), (0.0, 0.5), (2.0, 0.5)}),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "bottom": [],
                               "left": [(0.0, 0.5)], "right": [(2.0, 0.5)]}),
    },

    # ── shelf corr_r variants (right post reaches y=h-0.5: u, u_mid, lean_r, divider) ──

    "shelf_h1_v1_corr_r": {
        "id": "shelf_h1_v1_corr_r", "w": 6, "h": 1, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_u_corr_r,
        "whd_ports_fn":    _sh_ports_corr_r,
    },

    "shelf_h2_v1_corr_r": {
        "id": "shelf_h2_v1_corr_r", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_u_mid_corr_r,
        "whd_ports_fn":    _sh_ports_corr_r,
    },

    "shelf_h2_v3_corr_r": {
        "id": "shelf_h2_v3_corr_r", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_lean_r_corr_r,
        "whd_ports_fn":    _sh_ports_corr_r,
    },

    "shelf_h3_v1_corr_r": {
        "id": "shelf_h3_v1_corr_r", "w": 6, "h": 3, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_divider_corr_r,
        "whd_ports_fn":    _sh_ports_corr_r,
    },

    # ── shelf corr_l variants (left post reaches y=h-0.5: u, u_mid, lean_l, divider) ──

    "shelf_h1_v1_corr_l": {
        "id": "shelf_h1_v1_corr_l", "w": 6, "h": 1, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_u_corr_l,
        "whd_ports_fn":    _sh_ports_corr_l,
    },

    "shelf_h2_v1_corr_l": {
        "id": "shelf_h2_v1_corr_l", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_u_mid_corr_l,
        "whd_ports_fn":    _sh_ports_corr_l,
    },

    "shelf_h2_v2_corr_l": {
        "id": "shelf_h2_v2_corr_l", "w": 6, "h": 2, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_lean_l_corr_l,
        "whd_ports_fn":    _sh_ports_corr_l,
    },

    "shelf_h3_v1_corr_l": {
        "id": "shelf_h3_v1_corr_l", "w": 6, "h": 3, "d": 3, "zone": "shelf",
        "scalable_w": True,
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _sh_divider_corr_l,
        "whd_ports_fn":    _sh_ports_corr_l,
    },

})


# ── Shelf style categories (for corr variants) ────────────────────────────────

_SHELF_CAT_3D.update({
    "shelf_h1_v1_corr_r":  "plain",
    "shelf_h2_v1_corr_r":  "plain",
    "shelf_h2_v3_corr_r":  "pitched",
    "shelf_h3_v1_corr_r":  "divided",
    "shelf_h1_v1_corr_l":  "plain",
    "shelf_h2_v1_corr_l":  "plain",
    "shelf_h2_v2_corr_l":  "pitched",
    "shelf_h3_v1_corr_l":  "divided",
})


ZONES_3D_CORR_RIGHT = [
    {
        "id":      "chair_left",
        "x_rule":  ["first 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "chair_left_h2_v1", "chair_left_h2_v2", "chair_left_h2_v3",
            "chair_left_h3_v1", "chair_left_h3_v3",
        ],
    },
    {
        "id":      "table",
        "x_rule":  ["middle 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "table_3d_v1",
            "table_h2_v1", "table_h2_v3",
            "table_h3_v1", "table_h3_v3",
        ],
    },
    {
        "id":      "chair_right",
        "x_rule":  ["last 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "chair_right_h2_v1_corr_r", "chair_right_h2_v3_corr_r",
            "chair_right_h3_v1_corr_r",
        ],
    },
    {
        "id":      "shelf",
        "x_rule":  ["full"],
        "y_rule":  ["last 1", "last 2", "last 3"],
        "z_rule":  ["full"],
        "modules": [
            "shelf_h1_v1_corr_r",
            "shelf_h2_v1_corr_r", "shelf_h2_v3_corr_r",
            "shelf_h3_v1_corr_r",
        ],
    },
]

ZONES_3D_CORR_LEFT = [
    {
        "id":      "chair_left",
        "x_rule":  ["first 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "chair_left_h2_v1_corr_l", "chair_left_h2_v3_corr_l",
            "chair_left_h3_v1_corr_l",
        ],
    },
    {
        "id":      "table",
        "x_rule":  ["middle 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "table_3d_v1",
            "table_h2_v1", "table_h2_v3",
            "table_h3_v1", "table_h3_v3",
        ],
    },
    {
        "id":      "chair_right",
        "x_rule":  ["last 2"],
        "y_rule":  ["first 2", "first 3"],
        "z_rule":  ["full"],
        "modules": [
            "chair_right_h2_v1", "chair_right_h2_v2", "chair_right_h2_v3",
            "chair_right_h3_v1", "chair_right_h3_v3",
        ],
    },
    {
        "id":      "shelf",
        "x_rule":  ["full"],
        "y_rule":  ["last 1", "last 2", "last 3"],
        "z_rule":  ["full"],
        "modules": [
            "shelf_h1_v1_corr_l",
            "shelf_h2_v1_corr_l", "shelf_h2_v2_corr_l",
            "shelf_h3_v1_corr_l",
        ],
    },
]

# ── Full-roof corridor zone configs ───────────────────────────────────────────
# Shelf is placed separately by solver3d (full W, above the short corridor).
# chair_right_corr_r variants supply the right-boundary port matched by the
# short corridor's left port; chair_left_corr_l variants supply the left-boundary
# port matched by the short corridor's right port.

ZONES_3D_FULL_ROOF_CORR_RIGHT = [
    ZONES_3D_CORR_RIGHT[0],  # chair_left (no stub needed on left side)
    ZONES_3D_CORR_RIGHT[1],  # table
    ZONES_3D_CORR_RIGHT[2],  # chair_right with corr_r stubs
]

ZONES_3D_FULL_ROOF_CORR_LEFT = [
    ZONES_3D_CORR_LEFT[0],   # chair_left with corr_l stubs
    ZONES_3D_CORR_LEFT[1],   # table
    ZONES_3D_CORR_LEFT[2],   # chair_right (no stub needed on right side)
]

# 1-chair variants: single chair + table only (no second chair, shelf placed separately).
ZONES_3D_FULL_ROOF_CORR_RIGHT_1CHAIR = [
    ZONES_3D_CORR_RIGHT[0],  # chair_left at "first 2"
    {**ZONES_3D_CORR_RIGHT[1], "x_rule": ["last 2"]},  # table at "last 2"
]

ZONES_3D_FULL_ROOF_CORR_LEFT_1CHAIR = [
    {**ZONES_3D_CORR_LEFT[1], "x_rule": ["first 2"]},  # table at "first 2"
    ZONES_3D_CORR_LEFT[2],   # chair_right at "last 2"
]

# No-corridor 1-chair variant: chair_left + table + shelf, table at "last 2"
# so volumes don't overlap when inner_W < 6 (e.g. W=4 solo compact).
ZONES_3D_1CHAIR = [
    ZONES_3D[0],                             # chair_left at "first 2"
    {**ZONES_3D[1], "x_rule": ["last 2"]},   # table at "last 2"
    ZONES_3D[3],                             # shelf at "full"
]

FILLER_IDS_3D = ["filler_empty_3d", "filler_pass_v_3d", "filler_pass_h_3d",
                  "filler_corner_tr_3d", "filler_corner_tl_3d"]


# ── Kitchen 3D module helpers ─────────────────────────────────────────────────

def _kitchen_lower_segs(w, h, d):
    return _lift2d([
        [(0.5, 3.0), (0.5, 2.5)],
        [(0.5, 2.5), (2.0, 2.5), (2.0, 0.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
        [(1.5, 0.5), (3.0, 0.5)],
    ], d=d, ex={(0.5, 3.0), (3.0, 0.5)})

def _kitchen_lower_wide_segs(w, h, d):
    return _lift2d([
        [(0.5, 3.0), (0.5, 2.5)],
        [(0.5, 2.5), (2.5, 2.5), (2.5, 0.5), (2.0, 0.5), (0.5, 0.5), (0.5, 2.5)],
        [(2.0, 0.5), (3.0, 0.5)],
    ], d=d, ex={(0.5, 3.0), (3.0, 0.5)})

def _kitchen_lower_ports(w, h, d):
    return _ports_lift({"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}, d=d)

def _kitchen_lower_through_segs(w, h, d):
    return _lift2d([
        [(2.5, 3.0), (2.5, 2.5)],
        [(2.5, 2.5), (0.5, 2.5), (0.5, 0.5), (1.0, 0.5), (2.5, 0.5), (2.5, 2.5)],
        [(0.0, 0.5), (0.5, 0.5)],
        [(1.0, 0.5), (3.0, 0.5)],
    ], d=d, ex={(2.5, 3.0), (0.0, 0.5), (3.0, 0.5)})

def _kitchen_lower_through_ports(w, h, d):
    return _ports_lift({"top": [(2.5, 3.0)], "left": [(0.0, 0.5)], "right": [(3.0, 0.5)], "bottom": []}, d=d)

def _kitchen_upper_segs(w, h, d):
    # narrow body: right edge at w-0.5 (matches 2D narrow variant)
    return _lift2d([
        [(0.5, 0.0), (0.5, 0.5)],
        [(0.5, h - 0.5), (0.5, float(h))],
        [(0.5, 0.5), (w - 0.5, 0.5), (w - 0.5, h - 0.5), (0.5, h - 0.5), (0.5, 0.5)],
    ], d=d, ex={(0.5, 0.0), (0.5, float(h))})

def _kitchen_upper_wide_segs(w, h, d):
    # wide body: right edge at w (matches 2D wide variant)
    return _lift2d([
        [(0.5, 0.0), (0.5, 0.5)],
        [(0.5, h - 0.5), (0.5, float(h))],
        [(0.5, 0.5), (float(w), 0.5), (float(w), h - 0.5), (0.5, h - 0.5), (0.5, 0.5)],
    ], d=d, ex={(0.5, 0.0), (0.5, float(h))})

def _kitchen_upper_ports(w, h, d):
    return _ports_lift({"bottom": [(0.5, 0.0)], "top": [(0.5, float(h))], "left": [], "right": []}, d=d)

def _kitchen_wall_segs(w, h, d):
    return _lift2d([[(1.5, float(h)), (1.5, 0.5), (0.0, 0.5)]], d=d,
                   ex={(1.5, float(h)), (0.0, 0.5)})

def _kitchen_wall_ports(w, h, d):
    return _ports_lift({"top": [(1.5, float(h))], "left": [(0.0, 0.5)], "bottom": [], "right": []}, d=d)


MODULES_3D.update({

    "kitchen_lower_w3_h4_v2_3d": {
        "id": "kitchen_lower_w3_h4_v2_3d", "w": 3, "h": 3, "d": 3,
        "zone": "lower_cabinet",
        "source_2d_id": "kitchen_lower_w3_h4_v2",
        "description": "Kitchen lower cabinet 3D — narrow body (right edge at x=2.0).",
        "tags": ["kitchen", "lower_cabinet"],
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 2.5), (2.0, 2.5), (2.0, 0.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(1.5, 0.5), (3.0, 0.5)],
        ]),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}),
        "whd_segments_fn": _kitchen_lower_segs,
        "whd_ports_fn":    _kitchen_lower_ports,
    },
    "kitchen_lower_w3_h4_v3_3d": {
        "id": "kitchen_lower_w3_h4_v3_3d", "w": 3, "h": 3, "d": 3,
        "zone": "lower_cabinet",
        "source_2d_id": "kitchen_lower_w3_h4_v3",
        "description": "Kitchen lower cabinet 3D — wide body (right edge at x=2.5).",
        "tags": ["kitchen", "lower_cabinet", "wide"],
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 2.5), (2.5, 2.5), (2.5, 0.5), (2.0, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(2.0, 0.5), (3.0, 0.5)],
        ]),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}),
        "whd_segments_fn": _kitchen_lower_wide_segs,
        "whd_ports_fn":    _kitchen_lower_ports,
    },
    # Through-counter 3D — right-bank module for W=8 double-counter (inner_W=6).
    # Left exit connects to left-bank right exit; right exit connects to corridor.
    # Top port at x=2.5 starts the filler chain to the FRS shelf post at x=5.5.
    "kitchen_lower_w3_h4_through_3d": {
        "id": "kitchen_lower_w3_h4_through_3d", "w": 3, "h": 3, "d": 3,
        "zone": "lower_cabinet",
        "source_2d_id": "kitchen_lower_w3_h4_through",
        "description": "Kitchen right-bank counter 3D — through variant (left + right exits) for W=8.",
        "tags": ["kitchen", "lower_cabinet", "through"],
        "segments": _lift2d([
            [(2.5, 3.0), (2.5, 2.5)],
            [(2.5, 2.5), (0.5, 2.5), (0.5, 0.5), (1.0, 0.5), (2.5, 0.5), (2.5, 2.5)],
            [(0.0, 0.5), (0.5, 0.5)],
            [(1.0, 0.5), (3.0, 0.5)],
        ]),
        "ports": _ports_lift({"top": [(2.5, 3.0)], "left": [(0.0, 0.5)], "right": [(3.0, 0.5)], "bottom": []}),
        "whd_segments_fn": _kitchen_lower_through_segs,
        "whd_ports_fn":    _kitchen_lower_through_ports,
    },

    "kitchen_upper_w2_h1_3d": {
        "id": "kitchen_upper_w2_h1_3d", "w": 2, "h": 1, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h1",
        "description": "Kitchen upper cabinet h=1 — shelf bracket, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h1"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h2_3d": {
        "id": "kitchen_upper_w2_h2_3d", "w": 2, "h": 2, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h2",
        "description": "Kitchen upper cabinet h=2, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h2"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h3_3d": {
        "id": "kitchen_upper_w2_h3_3d", "w": 2, "h": 3, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h3",
        "description": "Kitchen upper cabinet h=3, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h3"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h4_3d": {
        "id": "kitchen_upper_w2_h4_3d", "w": 2, "h": 4, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h4",
        "description": "Kitchen upper cabinet h=4, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h4"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h1_wide_3d": {
        "id": "kitchen_upper_w2_h1_wide_3d", "w": 2, "h": 1, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h1_wide",
        "description": "Kitchen upper cabinet h=1 wide body, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h1", "wide"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_wide_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h2_wide_3d": {
        "id": "kitchen_upper_w2_h2_wide_3d", "w": 2, "h": 2, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h2_wide",
        "description": "Kitchen upper cabinet h=2 wide body, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h2", "wide"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_wide_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h3_wide_3d": {
        "id": "kitchen_upper_w2_h3_wide_3d", "w": 2, "h": 3, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h3_wide",
        "description": "Kitchen upper cabinet h=3 wide body, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h3", "wide"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_wide_segs, "whd_ports_fn": _kitchen_upper_ports,
    },
    "kitchen_upper_w2_h4_wide_3d": {
        "id": "kitchen_upper_w2_h4_wide_3d", "w": 2, "h": 4, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h4_wide",
        "description": "Kitchen upper cabinet h=4 wide body, 3D.",
        "tags": ["kitchen", "upper_cabinet", "h4", "wide"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_wide_segs, "whd_ports_fn": _kitchen_upper_ports,
    },

    # legacy alias kept for any remaining references
    "kitchen_upper_w2_3d": {
        "id": "kitchen_upper_w2_3d", "w": 2, "h": 3, "d": 3,
        "zone": "upper_cabinet", "source_2d_id": "kitchen_upper_w2_h3",
        "description": "Kitchen upper cabinet h=3, 3D (legacy).",
        "tags": ["kitchen", "upper_cabinet", "h3"],
        "segments": [], "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_segs, "whd_ports_fn": _kitchen_upper_ports,
    },

    "kitchen_wall_3d": {
        "id": "kitchen_wall_3d", "w": 2, "h": 7, "d": 3,
        "zone": "kitchen_wall",
        "scalable_h": True,
        "source_2d_id": "kitchen_wall",
        "description": "Kitchen wall, h-scalable, lifted from 2D geometry.",
        "tags": ["lifted", "kitchen", "kitchen_wall"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_wall_segs,
        "whd_ports_fn":    _kitchen_wall_ports,
    },

})


# ── Kitchen 3D zone configurations ───────────────────────────────────────────
# Mirrors 2D KITCHEN_ZONES / KITCHEN_ZONES_SHELF_H2 / KITCHEN_ZONES_SHELF_H3.
# No corridor variants needed — kitchen never has a corridor.

_KZ3_LOWER_NARROW = {"id": "lower_cabinet", "x_rule": ["first 3"], "y_rule": ["first 3"], "z_rule": ["full"], "modules": ["kitchen_lower_w3_h4_v2_3d"]}
_KZ3_LOWER_WIDE   = {"id": "lower_cabinet", "x_rule": ["first 3"], "y_rule": ["first 3"], "z_rule": ["full"], "modules": ["kitchen_lower_w3_h4_v3_3d"]}
_KZ3_LOWER        = _KZ3_LOWER_NARROW  # default; solver3d patches per _wide_k3d

_UPPER_3D_ALL = ["kitchen_upper_w2_h1_3d", "kitchen_upper_w2_h2_3d",
                 "kitchen_upper_w2_h3_3d", "kitchen_upper_w2_h4_3d"]

_KZ3_UPPER_H3    = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 size 3"],   "z_rule": ["full"], "modules": _UPPER_3D_ALL}
_KZ3_UPPER_TO_H2 = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 2"],"z_rule": ["full"], "modules": _UPPER_3D_ALL}
_KZ3_UPPER_TO_H3 = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 3"],"z_rule": ["full"], "modules": _UPPER_3D_ALL}
_KZ3_WALL_H1     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 1"],     "z_rule": ["full"], "modules": ["corridor_right_3d_short"]}
_KZ3_WALL_H2     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 2"],     "z_rule": ["full"], "modules": ["corridor_right_3d_short"]}
_KZ3_WALL_H3     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 3"],     "z_rule": ["full"], "modules": ["corridor_right_3d_short"]}

_KITCHEN_SHELF_H2_3D = [
    "shelf_h2_v1", "shelf_h2_v2", "shelf_h2_v3",
    "shelf_pitched_sym_v1", "shelf_pitched_sym_v2",
]
_KITCHEN_SHELF_H3_3D = ["shelf_h3_v1", "shelf_h3_v2"]

KITCHEN_ZONES_3D = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 1"], "z_rule": ["full"], "modules": ["shelf_h1_v1"]},
    _KZ3_LOWER,
    _KZ3_UPPER_H3,
    _KZ3_WALL_H1,
]

KITCHEN_ZONES_SHELF_H2_3D = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 2"], "z_rule": ["full"], "modules": _KITCHEN_SHELF_H2_3D},
    _KZ3_LOWER,
    _KZ3_UPPER_TO_H2,
    _KZ3_WALL_H2,
]

KITCHEN_ZONES_SHELF_H3_3D = [
    {"id": "shelf", "x_rule": ["full"], "y_rule": ["last 3"], "z_rule": ["full"], "modules": _KITCHEN_SHELF_H3_3D},
    _KZ3_LOWER,
    _KZ3_UPPER_TO_H3,
    _KZ3_WALL_H3,
]

# Inner zones only (no shelf, no kitchen_wall) — both pre-placed by solver3d.
# Upper cabinet y_rule "from 3 to last 0" fills whatever height remains after the shelf.
KITCHEN_ZONES_INNER_3D = [
    _KZ3_LOWER,
    {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 0"],
     "z_rule": ["full"], "modules": _UPPER_3D_ALL},
]

# W=8 variant (inner_W=6): left bank (right-exit) + right bank (through: left+right exits).
# Mirrors the 2D KITCHEN_ZONES_INNER_W6 layout.
KITCHEN_ZONES_INNER_W6_3D = [
    {"id": "lower_cabinet",   "x_rule": ["first 3"],       "y_rule": ["first 3"],
     "z_rule": ["full"], "modules": ["kitchen_lower_w3_h4_v2_3d", "kitchen_lower_w3_h4_v3_3d"]},
    {"id": "lower_cabinet_r", "x_rule": ["from 3 size 3"], "y_rule": ["first 3"],
     "z_rule": ["full"], "modules": ["kitchen_lower_w3_h4_through_3d"]},
    {"id": "upper_cabinet",   "x_rule": ["first 2"],       "y_rule": ["from 3 to last 0"],
     "z_rule": ["full"], "modules": _UPPER_3D_ALL},
]


# ── Living 3D zone configurations ─────────────────────────────────────────────

_LIVING_SHELF_3D = [
    "shelf_h1_v1",
    "shelf_h2_v1", "shelf_h2_v2", "shelf_h2_v3",
    "shelf_pitched_sym_v1", "shelf_pitched_sym_v2",
    "shelf_h3_v1", "shelf_h3_v2",
]

_LZ3_SOFA = {
    "id":      "sofa",
    "x_rule":  ["first 3", "first 2"],
    "y_rule":  ["first 3", "first 2"],
    "z_rule":  ["full"],
    "modules": ["sofa_h3_v3_3d", "sofa_h3_v2_3d", "sofa_h3_v1_3d"],
}
_LZ3_TABLE = {
    "id":      "table",
    # "from 3 size 2" → x=[3,5): sits directly to the right of sofa, no overlap.
    "x_rule":  ["from 3 size 2"],
    "y_rule":  ["first 2"],
    "z_rule":  ["full"],
    "modules": ["table_h2_v1", "table_h2_v3", "table_h2_v5", "table_h2_v6"],
}
_LZ3_TV = {
    "id":      "tv_table",
    "x_rule":  ["last 2"],
    "y_rule":  ["first 2"],
    "z_rule":  ["full"],
    "modules": ["tv_table_h2_v1", "tv_table_h2_v2", "tv_table_h2_v3"],
}
_LZ3_SHELF = {
    "id":      "shelf",
    "x_rule":  ["full"],
    "y_rule":  ["last 1", "last 2", "last 3"],
    "z_rule":  ["full"],
    "modules": _LIVING_SHELF_3D,
}

# Full no-corridor layout: sofa + table + tv_table + shelf (W≥7, no corridor).
LIVING_ZONES_3D = [_LZ3_SOFA, _LZ3_TABLE, _LZ3_TV, _LZ3_SHELF]

# Inner corridor layout (pre-placed corridor + shelf): sofa + table only (tv_table
# won't fit in inner_W=6 alongside sofa w=3 + table w=2 + corridor w=2).
LIVING_ZONES_INNER_3D = [_LZ3_SOFA, _LZ3_TABLE]

# sofa + tv_table: tv_table has no right port — works at last 2
LIVING_ZONES_SOFA_TV_3D = [_LZ3_SOFA, _LZ3_TV, _LZ3_SHELF]

# ── Bed 3D modules ────────────────────────────────────────────────────────────
# All beds: d=5, front profile at z=0.5, back at z=4.5
# Port coords match the 2D modules exactly.

def _bed_v1_segs_3d(w, h, d):
    return _lift2d([
        [(0.5, 2.0), (0.5, 1.5)],
        [(0.5, 1.5), (2.5, 1.5), (2.5, 0.5), (2.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
        [(2.5, 0.5), (3.0, 0.5)],
    ], d=d, ex={(0.5, 2.0), (3.0, 0.5)})

def _bed_v1_ports_3d(w, h, d):
    return _ports_lift({"top": [(0.5, 2.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}, d=d)


def _bed_v2_segs_3d(w, h, d):
    return _lift2d([
        [(0.5, 2.0), (0.5, 1.5)],
        [(0.5, 1.5), (3.0, 1.5), (3.0, 0.5), (0.5, 0.5), (0.5, 1.5)],
    ], d=d, ex={(0.5, 2.0), (3.0, 0.5)})

def _bed_v2_ports_3d(w, h, d):
    return _ports_lift({"top": [(0.5, 2.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}, d=d)


def _bed_v3_segs_3d(w, h, d):
    return _lift2d([
        [(0.5, 2.0), (0.5, 1.5)],
        [(0.5, 1.5), (3.5, 1.5), (3.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
        [(3.5, 0.5), (4.0, 0.5)],
    ], d=d, ex={(0.5, 2.0), (4.0, 0.5)})

def _bed_v3_ports_3d(w, h, d):
    return _ports_lift({"top": [(0.5, 2.0)], "right": [(4.0, 0.5)], "bottom": [], "left": []}, d=d)


def _bed_v4_segs_3d(w, h, d):
    return _lift2d([
        [(0.5, 2.0), (0.5, 1.5)],
        [(0.5, 1.5), (4.5, 1.5), (4.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
        [(5.0, 0.5), (4.5, 0.5)],
    ], d=d, ex={(0.5, 2.0), (5.0, 0.5)})

def _bed_v4_ports_3d(w, h, d):
    return _ports_lift({"top": [(0.5, 2.0)], "right": [(5.0, 0.5)], "bottom": [], "left": []}, d=d)


MODULES_3D.update({
    "bed_v1_3d": {
        "id": "bed_v1_3d", "w": 3, "h": 2, "d": 6, "zone": "bed",
        "scalable_d": True,
        "description": "Compact single bed, 80cm wide — front view, depth 5 units.",
        "tags": ["bed", "single", "compact", "80cm", "front-view"],
        "whd_segments_fn": _bed_v1_segs_3d,
        "whd_ports_fn":    _bed_v1_ports_3d,
    },
    "bed_v2_3d": {
        "id": "bed_v2_3d", "w": 3, "h": 2, "d": 6, "zone": "bed",
        "scalable_d": True,
        "description": "Spacious single bed, 100cm wide — front view, depth 5 units.",
        "tags": ["bed", "single", "spacious", "100cm", "front-view"],
        "whd_segments_fn": _bed_v2_segs_3d,
        "whd_ports_fn":    _bed_v2_ports_3d,
    },
    "bed_v3_3d": {
        "id": "bed_v3_3d", "w": 4, "h": 2, "d": 6, "zone": "bed",
        "scalable_d": True,
        "description": "Queen bed, 120cm wide — front view, depth 5 units.",
        "tags": ["bed", "queen", "120cm", "front-view"],
        "whd_segments_fn": _bed_v3_segs_3d,
        "whd_ports_fn":    _bed_v3_ports_3d,
    },
    "bed_v4_3d": {
        "id": "bed_v4_3d", "w": 5, "h": 2, "d": 6, "zone": "bed",
        "scalable_d": True,
        "description": "King bed, 160cm wide — front view, depth 5 units.",
        "tags": ["bed", "king", "160cm", "front-view"],
        "whd_segments_fn": _bed_v4_segs_3d,
        "whd_ports_fn":    _bed_v4_ports_3d,
    },
})

# ── Bed v5 3D modules (side-view, 4 depth variants) ──────────────────────────
# bed_v5 is the side-view 2D cross-section; depth encodes bed width.

def _bed_v5_segs_3d(w, h, d):
    return _lift2d([
        [(0.5, 2.0), (0.5, 1.5)],
        [(0.5, 1.5), (5.5, 1.5), (5.5, 0.5), (0.5, 0.5), (0.5, 1.5)],
        [(6.0, 0.5), (5.5, 0.5)],
    ], d=d, ex={(0.5, 2.0), (6.0, 0.5)})

def _bed_v5_ports_3d(w, h, d):
    return _ports_lift({"top": [(0.5, 2.0)], "right": [(6.0, 0.5)], "bottom": [], "left": []}, d=d)

MODULES_3D.update({
    "bed_v5_3d_v1": {
        "id": "bed_v5_3d_v1", "w": 6, "h": 2, "d": 3, "zone": "bed",
        "scalable_d": False,
        "description": "Bed side view, depth 3 (z 0.5-2.5) -- compact single width.",
        "tags": ["bed", "side-view", "d3"],
        "whd_segments_fn": _bed_v5_segs_3d,
        "whd_ports_fn":    _bed_v5_ports_3d,
    },
    "bed_v5_3d_v2": {
        "id": "bed_v5_3d_v2", "w": 6, "h": 2, "d": 3.5, "zone": "bed",
        "scalable_d": False,
        "description": "Bed side view, depth 3.5 (z 0.5-3.0) -- spacious single width.",
        "tags": ["bed", "side-view", "d3.5"],
        "whd_segments_fn": _bed_v5_segs_3d,
        "whd_ports_fn":    _bed_v5_ports_3d,
    },
    "bed_v5_3d_v3": {
        "id": "bed_v5_3d_v3", "w": 6, "h": 2, "d": 4, "zone": "bed",
        "scalable_d": False,
        "description": "Bed side view, depth 4 (z 0.5-3.5) -- queen width.",
        "tags": ["bed", "side-view", "d4"],
        "whd_segments_fn": _bed_v5_segs_3d,
        "whd_ports_fn":    _bed_v5_ports_3d,
    },
    "bed_v5_3d_v4": {
        "id": "bed_v5_3d_v4", "w": 6, "h": 2, "d": 5, "zone": "bed",
        "scalable_d": False,
        "description": "Bed side view, depth 5 (z 0.5-4.5) -- king width.",
        "tags": ["bed", "side-view", "d5"],
        "whd_segments_fn": _bed_v5_segs_3d,
        "whd_ports_fn":    _bed_v5_ports_3d,
    },
})

# ── Bed 3D zone configuration ─────────────────────────────────────────────────
BED_ZONES_3D = [
    {"id": "bed", "x_rule": ["first 6", "first 5", "first 4", "first 3"],
     "y_rule": ["first 2"], "z_rule": ["full"],
     "modules": ["bed_v1_3d", "bed_v2_3d", "bed_v3_3d", "bed_v4_3d",
                 "bed_v5_3d_v1", "bed_v5_3d_v2", "bed_v5_3d_v3", "bed_v5_3d_v4"]},
]
