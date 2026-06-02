"""
3D module library — native modules only.
Axis convention: x = width, y = height, z = depth.
Ports: left (x=0), right (x=w), bottom (y=0), top (y=h), front (z=0), back (z=d).

New modules are defined by calling _lift2d() at import time on 2D segment data.
This produces explicit static 3D coordinates (not lazy-computed at render time).
"""
from typing import Dict

FACES_3D = ("left", "right", "bottom", "top", "front", "back")


# ── Helpers: lift 2D geometry to 3D at import time ───────────────────────────

def _lift2d(segs_2d: list, d: int = 3, ex: set = None) -> list:
    """Convert 2D segments to 3D: front profile at z=1, back at z=d-1.
    z-connectors are added at every unique vertex NOT in ex (port exclusion set)."""
    z0, z1 = 1.0, float(d) - 1.0
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
    """Lift 2D port dict to 3D — each (x,y) port becomes (x,y,1) and (x,y,d-1)."""
    z0, z1 = 1.0, float(d) - 1.0
    out: dict = {}
    for face in ("left", "right", "top", "bottom"):
        pts = ports_2d.get(face, [])
        out[face] = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
    out["front"] = []
    out["back"] = []
    return out


def _scale_segs_d(segs: list, old_d: int, new_d: int) -> list:
    """Remap z=back-plane coordinate from old_d to new_d; z=front stays at 1.0."""
    z_old = float(old_d) - 1.0
    z_new = float(new_d) - 1.0
    def rz(z): return z_new if abs(z - z_old) < 1e-9 else z
    return [[(x, y, rz(z)) for x, y, z in seg] for seg in segs]


def _scale_ports_d(ports: dict, old_d: int, new_d: int) -> dict:
    """Remap z=back-plane coordinate in a ports dict from old_d to new_d."""
    z_old = float(old_d) - 1.0
    z_new = float(new_d) - 1.0
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
        "tags":        ["native3d", "chair_left"],
        "segments": [
            [(0.5, 2.0, 1.0), (0.5, 1.5, 1.0), (1.5, 1.5, 1.0), (1.0, 0.5, 1.5)],
            [(0.5, 1.5, 1.0), (0.5, 1.5, 2.0)],
            [(0.5, 2.0, 2.0), (0.5, 1.5, 2.0), (1.5, 1.5, 2.0), (1.0, 0.5, 1.5)],
            [(1.5, 1.5, 1.0), (1.5, 1.5, 2.0)],
            [(1.0, 0.5, 1.5), (2.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [], "right":  [(2.0, 0.5, 1.5)],
            "bottom": [], "top":    [(0.5, 2.0, 1.0), (0.5, 2.0, 2.0)],
            "front":  [], "back":   [],
        },
    },

    "chair_right_3d_v1": {
        "id":          "chair_right_3d_v1",
        "w": 2, "h": 2, "d": 3,
        "zone":        "chair_right",
        "description": "Right-facing chair, native 3D from Rhino.",
        "tags":        ["native3d", "chair_right"],
        "segments": [
            [(1.0, 0.5, 1.5), (0.5, 1.5, 2.0), (1.5, 1.5, 2.0), (1.5, 2.0, 2.0)],
            [(0.5, 1.5, 1.0), (0.5, 1.5, 2.0)],
            [(1.0, 0.5, 1.5), (0.5, 1.5, 1.0), (1.5, 1.5, 1.0), (1.5, 2.0, 1.0)],
            [(1.5, 1.5, 1.0), (1.5, 1.5, 2.0)],
            [(1.0, 0.5, 1.5), (0.0, 0.5, 1.5)],
        ],
        "ports": {
            "left":   [(0.0, 0.5, 1.5)], "right":  [],
            "bottom": [],                "top":    [(1.5, 2.0, 1.0), (1.5, 2.0, 2.0)],
            "front":  [],                "back":   [],
        },
    },

    # ── Rhino native: table ───────────────────────────────────────────────────

    "table_3d_v1": {
        "id":          "table_3d_v1",
        "w": 2, "h": 3, "d": 3,
        "zone":        "table",
        "description": "Dining table, native 3D from Rhino.",
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
            [(0.5, 2.5, 2.0), (2.5, 2.5, 1.5), (0.5, 2.5, 1.0)],
            [(0.5, 2.5, 2.0), (0.5, 0.0, 2.0)],
            [(0.5, 2.5, 1.0), (0.5, 0.0, 1.0)],
            [(2.5, 2.5, 1.5), (3.5, 2.5, 1.5)],
            [(5.5, 2.5, 2.0), (3.5, 2.5, 1.5), (5.5, 2.5, 1.0)],
            [(5.5, 0.0, 2.0), (5.5, 2.5, 2.0)],
            [(5.5, 0.0, 1.0), (5.5, 2.5, 1.0)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(0.5, 0.0, 1.0), (0.5, 0.0, 2.0), (5.5, 0.0, 1.0), (5.5, 0.0, 2.0)],
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
            [(0.5, 0.0, 1.0), (0.5, 1.0, 1.0)],
            [(0.5, 0.0, 2.0), (0.5, 1.0, 2.0)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(0.5, 0.0, 1.0), (0.5, 0.0, 2.0)],
            "top":    [(0.5, 1.0, 1.0), (0.5, 1.0, 2.0)],
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
            [(1.5, 0.0, 1.0), (1.5, 1.0, 1.0)],
            [(1.5, 0.0, 2.0), (1.5, 1.0, 2.0)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(1.5, 0.0, 1.0), (1.5, 0.0, 2.0)],
            "top":    [(1.5, 1.0, 1.0), (1.5, 1.0, 2.0)],
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
            [(0.5, 0.0, 1.0), (0.5, 1.0, 1.0)],
            [(0.5, 0.0, 2.0), (0.5, 1.0, 2.0)],
        ],
        "ports": {
            "left":   [], "right":  [],
            "bottom": [(0.5, 0.0, 1.0), (0.5, 0.0, 2.0)],
            "top":    [(0.5, 1.0, 1.0), (0.5, 1.0, 2.0)],
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
            [(0.0, 0.5, 1.0), (1.0, 0.5, 1.0)],
            [(0.0, 0.5, 2.0), (1.0, 0.5, 2.0)],
        ],
        "ports": {
            "left":   [(0.0, 0.5, 1.0), (0.0, 0.5, 2.0)],
            "right":  [(1.0, 0.5, 1.0), (1.0, 0.5, 2.0)],
            "bottom": [], "top":    [],
            "front":  [], "back":   [],
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

})


# ── Shelf style categories (for roof_style filter in solver3d) ────────────────
# plain:   flat horizontal bar
# divided: internal subdivisions
# pitched: gable ridge

_SHELF_CAT_3D: dict = {
    "shelf_h1_v1":         "plain",
    "shelf_h2_v1":         "plain",
    "shelf_h2_v2":         "pitched",
    "shelf_h2_v3":         "pitched",
    "shelf_pitched_sym_v1":"pitched",
    "shelf_pitched_sym_v2":"pitched",
    "shelf_h3_v1":         "divided",
    "shelf_h3_v2":         "pitched",
    "roof_3d_v1":          "pitched",
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_segments_3d(mod: dict, w: int, h: int, d: int) -> list:
    if "whd_segments_fn" in mod:
        return mod["whd_segments_fn"](w, h, d)
    segs = mod.get("segments", [])
    if mod.get("scalable_d") and d != mod.get("d", 3):
        return _scale_segs_d(segs, mod.get("d", 3), d)
    return segs


def get_ports_3d(mod: dict, w: int, h: int, d: int) -> dict:
    if "whd_ports_fn" in mod:
        return mod["whd_ports_fn"](w, h, d)
    ports = mod.get("ports", {face: [] for face in FACES_3D})
    if mod.get("scalable_d") and d != mod.get("d", 3):
        return _scale_ports_d(ports, mod.get("d", 3), d)
    return ports


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

FILLER_IDS_3D = ["filler_empty_3d", "filler_pass_v_3d", "filler_pass_h_3d"]


# ── Kitchen 3D module helpers ─────────────────────────────────────────────────

def _kitchen_lower_segs(w, h, d):
    return _lift2d([
        [(0.5, 3.0), (0.5, 2.5)],
        [(0.5, 2.5), (2.0, 2.5), (2.0, 0.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
        [(1.5, 0.5), (3.0, 0.5)],
    ], d=d, ex={(0.5, 3.0), (3.0, 0.5)})

def _kitchen_lower_ports(w, h, d):
    return _ports_lift({"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}, d=d)

def _kitchen_upper_segs(w, h, d):
    return _lift2d([
        [(0.5, 0.0), (0.5, 0.5)],
        [(0.5, h - 0.5), (0.5, float(h))],
        [(0.5, 0.5), (w - 0.5, 0.5), (w - 0.5, h - 0.5), (0.5, h - 0.5), (0.5, 0.5)],
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
        "description": "Kitchen lower cabinet, native 3D lifted from 2D geometry.",
        "tags": ["lifted", "kitchen", "lower_cabinet"],
        "segments": _lift2d([
            [(0.5, 3.0), (0.5, 2.5)],
            [(0.5, 2.5), (2.0, 2.5), (2.0, 0.5), (1.5, 0.5), (0.5, 0.5), (0.5, 2.5)],
            [(1.5, 0.5), (3.0, 0.5)],
        ]),
        "ports": _ports_lift({"top": [(0.5, 3.0)], "right": [(3.0, 0.5)], "bottom": [], "left": []}),
        "whd_segments_fn": _kitchen_lower_segs,
        "whd_ports_fn":    _kitchen_lower_ports,
    },

    "kitchen_upper_w2_3d": {
        "id": "kitchen_upper_w2_3d", "w": 2, "h": 3, "d": 3,
        "zone": "upper_cabinet",
        "scalable_h": True,
        "source_2d_id": "kitchen_upper_w2",
        "description": "Kitchen upper cabinet, h-scalable, lifted from 2D geometry.",
        "tags": ["lifted", "kitchen", "upper_cabinet"],
        "segments": [],
        "ports": {face: [] for face in FACES_3D},
        "whd_segments_fn": _kitchen_upper_segs,
        "whd_ports_fn":    _kitchen_upper_ports,
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

_KZ3_LOWER       = {"id": "lower_cabinet", "x_rule": ["first 3"], "y_rule": ["first 3"],         "z_rule": ["full"], "modules": ["kitchen_lower_w3_h4_v2_3d"]}
_KZ3_UPPER_H3    = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 size 3"],   "z_rule": ["full"], "modules": ["kitchen_upper_w2_3d"]}
_KZ3_UPPER_TO_H2 = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 2"],"z_rule": ["full"], "modules": ["kitchen_upper_w2_3d"]}
_KZ3_UPPER_TO_H3 = {"id": "upper_cabinet", "x_rule": ["first 2"], "y_rule": ["from 3 to last 3"],"z_rule": ["full"], "modules": ["kitchen_upper_w2_3d"]}
_KZ3_WALL_H1     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 1"],     "z_rule": ["full"], "modules": ["kitchen_wall_3d"]}
_KZ3_WALL_H2     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 2"],     "z_rule": ["full"], "modules": ["kitchen_wall_3d"]}
_KZ3_WALL_H3     = {"id": "kitchen_wall",  "x_rule": ["last 2"],  "y_rule": ["skip last 3"],     "z_rule": ["full"], "modules": ["kitchen_wall_3d"]}

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
