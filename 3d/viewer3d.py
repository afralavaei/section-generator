"""
3D renderer — matplotlib mplot3d for v1 (viewer choice pluggable in Phase 5).

Public API mirrors drawing.py:
  - plot_section_3d(placed, W, H, D)
  - plot_module_library_3d(default_d=2)
  - plot_slice_2d(placed_3d, W, H, D, z, ...)  — extracts a z-slice and renders
    via drawing.plot_section, proving the 3D→2D round-trip.

Axis convention on screen: matplotlib mplot3d puts its own ``z`` axis vertical,
but our coordinate frame uses ``y`` for height. We therefore plot data as
``(x, z, y) → (mpl_x, mpl_y, mpl_z)`` so height (y) appears vertical, and depth
(z) recedes into the screen.

When swapping to plotly/pyvista/three.js in Phase 5, only this file changes.
"""
import math
from typing import List

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers '3d' projection)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from modules import LINE_COLOR, PORT_COLOR, GRID_COLOR, ZONE_ORDER, ZONE_COLORS
from modules3d import MODULES_3D, get_segments_3d, get_ports_3d, EXT_SUFFIX


# ── Voxel outline (12 edges of the module's bounding box) ─────────────────────

def _voxel_edges(w: float, h: float, d: float):
    return [
        # 4 x-running edges
        ((0,0,0),(w,0,0)), ((0,h,0),(w,h,0)), ((0,0,d),(w,0,d)), ((0,h,d),(w,h,d)),
        # 4 y-running edges
        ((0,0,0),(0,h,0)), ((w,0,0),(w,h,0)), ((0,0,d),(0,h,d)), ((w,0,d),(w,h,d)),
        # 4 z-running edges
        ((0,0,0),(0,0,d)), ((w,0,0),(w,0,d)), ((0,h,0),(0,h,d)), ((w,h,0),(w,h,d)),
    ]


def _voxel_faces(w: float, h: float, d: float):
    """6 faces of the bounding box, each a list of 4 corner points (x, y, z)."""
    return [
        [(0,0,0), (w,0,0), (w,0,d), (0,0,d)],   # bottom  (y=0)
        [(0,h,0), (w,h,0), (w,h,d), (0,h,d)],   # top     (y=h)
        [(0,0,0), (0,h,0), (0,h,d), (0,0,d)],   # left    (x=0)
        [(w,0,0), (w,h,0), (w,h,d), (w,0,d)],   # right   (x=w)
        [(0,0,0), (w,0,0), (w,h,0), (0,h,0)],   # front   (z=0)
        [(0,0,d), (w,0,d), (w,h,d), (0,h,d)],   # back    (z=d)
    ]


def _draw_module_3d(ax, mod: dict,
                    xo: float, yo: float, zo: float,
                    w: int, h: int, d: int,
                    show_voxel: bool = True, show_ports: bool = True,
                    show_zone_fill: bool = True,
                    zone_alpha: float = 0.08,
                    line_width: float = 2.0) -> None:
    """Draw a single placed module. Emits ``(x, z, y)`` so the on-screen
    vertical axis is ``y`` (height)."""
    if show_zone_fill:
        zone_color = ZONE_COLORS.get(mod.get("zone", ""), None)
        if zone_color is not None and zone_alpha > 0:
            faces_xzy = [
                [(p[0] + xo, p[2] + zo, p[1] + yo) for p in face]
                for face in _voxel_faces(w, h, d)
            ]
            coll = Poly3DCollection(
                faces_xzy, facecolor=zone_color, edgecolor="none",
                alpha=zone_alpha, zorder=0,
            )
            ax.add_collection3d(coll)

    if show_voxel:
        for (p0, p1) in _voxel_edges(w, h, d):
            ax.plot(
                [p0[0] + xo, p1[0] + xo],
                [p0[2] + zo, p1[2] + zo],
                [p0[1] + yo, p1[1] + yo],
                color=GRID_COLOR, lw=0.4, zorder=1,
            )

    for seg in get_segments_3d(mod, w, h, d):
        xs = [p[0] + xo for p in seg]
        ys = [p[1] + yo for p in seg]
        zs = [p[2] + zo for p in seg]
        ax.plot(xs, zs, ys, color=LINE_COLOR, lw=line_width, zorder=3,
                solid_capstyle="round", solid_joinstyle="round")

    if show_ports:
        for pts in get_ports_3d(mod, w, h, d).values():
            for px, py, pz in pts:
                ax.scatter([px + xo], [pz + zo], [py + yo],
                           color=PORT_COLOR, s=18, zorder=4, depthshade=False)


# ── plot_section_3d ───────────────────────────────────────────────────────────

def plot_section_3d(placed: List[dict], W: int, H: int, D: int,
                    show_ports: bool = True,
                    elev: float = 22, azim: float = -55) -> plt.Figure:
    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")

    for p in placed:
        mod = MODULES_3D[p["module_id"]]
        _draw_module_3d(ax, mod,
                        p["x_off"], p["y_off"], p["z_off"],
                        p["w"], p["h"], p["d"],
                        show_voxel=True, show_ports=show_ports)

    ax.set_xlim(0, W); ax.set_ylim(0, D); ax.set_zlim(0, H)
    ax.set_xlabel("x  (width)",  labelpad=6)
    ax.set_ylabel("z  (depth)",  labelpad=6)
    ax.set_zlabel("y  (height)", labelpad=6)
    ax.set_box_aspect((W, D, H))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(f"Nomadic Engine — 3D Section  {W} × {H} × {D}", fontsize=11, pad=10)
    ax.grid(False)
    fig.tight_layout()
    return fig


# ── plot_module_library_3d ────────────────────────────────────────────────────

def plot_module_library_3d(default_d: int = 2) -> plt.Figure:
    mods = sorted(
        (m for m in MODULES_3D.values()
         if "narrow" not in m["id"]
         and not (m["zone"] in ("chair_left", "chair_right") and "_corr_" in m["id"])),
        key=lambda m: (
            ZONE_ORDER.index(m["zone"]) if m["zone"] in ZONE_ORDER else 99,
            m["id"],
        ),
    )

    n_cols = 4
    n_rows = math.ceil(len(mods) / n_cols)
    fig = plt.figure(figsize=(n_cols * 3.4, n_rows * 3.2))

    for i, mod in enumerate(mods):
        ax = fig.add_subplot(n_rows, n_cols, i + 1, projection="3d")
        w, h = mod["w"], mod["h"]
        d = default_d
        _draw_module_3d(ax, mod, 0.0, 0.0, 0.0, w, h, d)
        ax.set_xlim(0, w); ax.set_ylim(0, d); ax.set_zlim(0, h)
        ax.set_box_aspect((w, d, h))
        ax.view_init(elev=20, azim=-55)
        short = mod["id"].replace(EXT_SUFFIX, "").replace("filler_", "")
        ax.set_title(f"{short}\n{w}×{h}×{d}", fontsize=7, pad=4)
        ax.tick_params(labelsize=5)
        ax.grid(False)

    fig.suptitle("Nomadic Engine — 3D Module Library  (auto-extruded)",
                 fontsize=12, y=1.0)
    fig.tight_layout()
    return fig


# ── 2D slice viewer (extracts a z-slice and renders via the existing 2D path) ─

def plot_slice_2d(placed_3d: List[dict], W: int, H: int, D: int,
                  z: float, show_figures: bool = False,
                  roof_style: str = "any") -> plt.Figure:
    """Render the 2D section at depth slice ``z`` by mapping each placed 3D
    module back to its 2D source. Reuses drawing.plot_section."""
    from drawing import plot_section

    placed_2d = []
    for p in placed_3d:
        if not (p["z_off"] - 1e-9 <= z <= p["z_off"] + p["d"] + 1e-9):
            continue
        mod3d = MODULES_3D[p["module_id"]]
        src_id = mod3d.get("source_2d_id")
        if src_id is None:
            continue  # native 3D modules need their own slice impl (Phase 6+)
        placed_2d.append({
            "module_id": src_id,
            "x_off": p["x_off"], "y_off": p["y_off"],
            "w": p["w"], "h": p["h"],
        })
    return plot_section(placed_2d, W, H, show_figures=show_figures, roof_style=roof_style)
