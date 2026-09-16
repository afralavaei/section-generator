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

from modules import LINE_COLOR, PORT_COLOR, GRID_COLOR, ZONE_ORDER, ZONE_COLORS, ZONE_ALPHAS
from modules3d import MODULES_3D, get_segments_3d, get_ports_3d


def _clean_ax(fig: plt.Figure, ax, dark: bool = False) -> None:
    """Set figure/axes backgrounds. dark=True → transparent with subtle pane edges."""
    bg = "none" if dark else "white"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    edge = "#1c2420" if dark else "#d0d4d0"
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.fill = False
        pane.set_edgecolor(edge)


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
                    zone_alpha: float = 0.50,
                    line_width: float = 2.0,
                    line_color_override: str | None = None,
                    grid_color_override: str | None = None,
                    pipe: bool = False) -> None:
    """Draw a single placed module. Emits ``(x, z, y)`` so the on-screen
    vertical axis is ``y`` (height)."""
    lc = line_color_override or LINE_COLOR
    gc = grid_color_override or GRID_COLOR

    if show_zone_fill:
        zone       = mod.get("zone", "")
        zone_color = ZONE_COLORS.get(zone, None)
        eff_alpha  = ZONE_ALPHAS.get(zone, zone_alpha)
        if zone_color is not None and eff_alpha > 0:
            faces_xzy = [
                [(p[0] + xo, p[2] + zo, p[1] + yo) for p in face]
                for face in _voxel_faces(w, h, d)
            ]
            coll = Poly3DCollection(
                faces_xzy, facecolor=zone_color, edgecolor="none",
                alpha=eff_alpha, zorder=0,
            )
            ax.add_collection3d(coll)

    if show_voxel:
        for (p0, p1) in _voxel_edges(w, h, d):
            ax.plot(
                [p0[0] + xo, p1[0] + xo],
                [p0[2] + zo, p1[2] + zo],
                [p0[1] + yo, p1[1] + yo],
                color=gc, lw=0.4, zorder=1,
            )

    for seg in get_segments_3d(mod, w, h, d):
        xs = [p[0] + xo for p in seg]
        ys = [p[1] + yo for p in seg]
        zs = [p[2] + zo for p in seg]
        ax.plot(xs, zs, ys, color=lc, lw=line_width, zorder=3,
                solid_capstyle="round", solid_joinstyle="round")

    if show_ports:
        for pts in get_ports_3d(mod, w, h, d).values():
            for px, py, pz in pts:
                ax.scatter([px + xo], [pz + zo], [py + yo],
                           color=PORT_COLOR, s=18, zorder=4, depthshade=False)


# ── plot_section_3d ───────────────────────────────────────────────────────────

def plot_section_3d(placed: List[dict], W: int, H: int, D: int,
                    show_ports: bool = True,
                    elev: float = 28, azim: float = -60,
                    dark: bool = False) -> plt.Figure:
    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")
    _clean_ax(fig, ax, dark=dark)

    line_c = "#c8d0c8" if dark else LINE_COLOR
    grid_c = "#2a3028" if dark else GRID_COLOR

    for p in placed:
        mod = MODULES_3D[p["module_id"]]
        _draw_module_3d(ax, mod,
                        p["x_off"], p["y_off"], p["z_off"],
                        p["w"], p["h"], p["d"],
                        show_voxel=True, show_ports=show_ports,
                        show_zone_fill=not dark,
                        line_color_override=line_c,
                        grid_color_override=grid_c)

    ax.set_xlim(0, W); ax.set_ylim(0, D); ax.set_zlim(0, H)
    label_color = "#8a9a88" if dark else "black"
    ax.set_xlabel(f"width  {W}×40 = {W*40} cm",  labelpad=6, color=label_color)
    ax.set_ylabel(f"depth  {D}×40 = {D*40} cm",  labelpad=6, color=label_color)
    ax.set_zlabel(f"height  {H}×40 = {H*40} cm", labelpad=6, color=label_color)
    ax.xaxis.set_ticklabels([])
    ax.yaxis.set_ticklabels([])
    ax.zaxis.set_ticklabels([])
    ax.tick_params(colors=label_color, length=0)
    ax.set_box_aspect((W, D, H))
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(f"Nomadic Engine — 3D Section  {W} × {H} × {D}", fontsize=11, pad=10)
    ax.grid(False)
    fig.tight_layout()
    return fig


# ── plot_dwelling_3d ──────────────────────────────────────────────────────────

def plot_dwelling_3d(sections: list,
                     corridor_side: str = "none",
                     corridor_w: int = 2,
                     elev: float = 25, azim: float = -60,
                     dark: bool = False,
                     highlight_section: str | None = None) -> plt.Figure:
    """
    Render all sections of the assembled dwelling in one combined 3D figure.

    Each section's placed modules already have z_off shifted by their depth
    offset (done by solve_dwelling_3d), so they sit end-to-end along z.
    """
    if not sections:
        return plt.figure()

    W       = max(s["W"] for s in sections)
    H       = sections[0]["H"]
    total_D = sum(s["d"] for s in sections)

    fig = plt.figure(figsize=(10, 10))   # square → SVG overlay aligns without letterboxing
    ax  = fig.add_subplot(111, projection="3d")
    _clean_ax(fig, ax, dark=dark)

    lc      = "#e8ece8" if dark else LINE_COLOR
    gc      = "#2a3028" if dark else GRID_COLOR
    lbl_clr = "#8a9a88" if dark else "black"

    for s in sections:
        if s["placed"] is None:
            continue
        # When a section is highlighted, others dim; the active one uses full brightness.
        if highlight_section and dark:
            is_active = s["type"] == highlight_section
            sec_lc = "#ffffff" if is_active else "#2a3028"
            sec_gc = "#1a2018" if is_active else "#141810"
            sec_lw = 2.2 if is_active else 0.6
        else:
            sec_lc, sec_gc, sec_lw = lc, gc, 2.0
        for p in s["placed"]:
            mod = MODULES_3D[p["module_id"]]
            _draw_module_3d(ax, mod,
                            p["x_off"], p["y_off"], p["z_off"],
                            p["w"], p["h"], p["d"],
                            show_voxel=True, show_ports=False,
                            show_zone_fill=not dark,
                            line_color_override=sec_lc,
                            grid_color_override=sec_gc,
                            line_width=sec_lw)

    for (xd, yd) in [(0, 0), (W, 0), (0, H), (W, H)]:
        ax.plot([xd, xd], [0, total_D], [yd, yd], color=lc, lw=1.5, zorder=6)

    _frame_zs = sorted({s["d_offset"] for s in sections} | {total_D})
    for _z in _frame_zs:
        ax.plot([0, W], [_z, _z], [0, 0], color=lc, lw=1.2, zorder=5)
        ax.plot([0, W], [_z, _z], [H, H], color=lc, lw=1.2, zorder=5)
        ax.plot([0, 0], [_z, _z], [0, H], color=lc, lw=1.2, zorder=5)
        ax.plot([W, W], [_z, _z], [0, H], color=lc, lw=1.2, zorder=5)

    _corner_pts: set = set()
    for s in sections:
        if s["placed"] is None:
            continue
        for p in s["placed"]:
            x0, y0 = float(p["x_off"]), float(p["y_off"])
            for xi in [x0, x0 + p["w"]]:
                for yi in [y0, y0 + p["h"]]:
                    _corner_pts.add((xi, yi))
    for (xi, yi) in _corner_pts:
        ax.plot([xi, xi], [0, total_D], [yi, yi],
                color=lc, lw=0.7, alpha=0.45, zorder=3)

    for s in sections:
        if s["placed"] is None:
            _mid_z = s["d_offset"] + s["d"] / 2
            ax.text(W / 2, _mid_z, H / 2, s["type"].upper(),
                    ha="center", va="center", fontsize=9, color=lbl_clr)

    ax.set_xlim(0, W)
    ax.set_ylim(0, total_D)
    ax.set_zlim(0, H)
    ax.set_xlabel(f"width  {W}×40 = {W*40} cm",          labelpad=6, color=lbl_clr)
    ax.set_ylabel(f"depth  {total_D}×40 = {total_D*40} cm", labelpad=6, color=lbl_clr)
    ax.set_zlabel(f"height  {H}×40 = {H*40} cm",          labelpad=6, color=lbl_clr)
    ax.xaxis.set_ticklabels([])
    ax.yaxis.set_ticklabels([])
    ax.zaxis.set_ticklabels([])
    ax.tick_params(colors=lbl_clr, length=0)
    ax.set_box_aspect((W, total_D, H))
    ax.view_init(elev=elev, azim=azim)
    ax.grid(False)
    fig.tight_layout()
    return fig


# ── plot_module_library_3d ────────────────────────────────────────────────────

_SECTION_ZONES_3D = {
    "Dining":  {"chair_left", "chair_right", "table", "shelf", "corridor_left", "corridor_right"},
    "Kitchen": {"lower_cabinet", "upper_cabinet", "kitchen_wall", "shelf"},
    "Living":  {"sofa", "table", "tv_table", "shelf"},
    "Bed":     {"bed", "shelf", "corridor_left", "corridor_right"},
}

_ZONE_CATEGORY_3D: dict = {
    "chair_left":     "Chairs",
    "chair_right":    "Chairs",
    "table":          "Tables",
    "sofa":           "Sofas",
    "tv_table":       "TV Tables",
    "shelf":          "Shelves",
    "lower_cabinet":  "Lower Cabinets",
    "upper_cabinet":  "Upper Cabinets",
    "kitchen_wall":   "Kitchen Walls",
    "bed":            "Beds",
    "corridor_left":  "Corridors",
    "corridor_right": "Corridors",
}

_CATEGORY_ORDER_3D: list = [
    "Beds", "Chairs", "Sofas", "TV Tables", "Tables",
    "Lower Cabinets", "Upper Cabinets", "Kitchen Walls",
    "Shelves", "Corridors",
]


def _library_mods_3d(section: str) -> list:
    allowed = _SECTION_ZONES_3D.get(section)
    return sorted(
        (m for m in MODULES_3D.values()
         if m["zone"] != "filler"
         and "conn_" not in m["id"]
         and (allowed is None or m["zone"] in allowed)
         and "legacy" not in m.get("description", "")),
        key=lambda m: (
            ZONE_ORDER.index(m["zone"]) if m["zone"] in ZONE_ORDER else 99,
            m["h"], m["id"],
        ),
    )


def get_library_3d_by_zone(section: str) -> list[tuple[str, list]]:
    """Return [(category_label, [mods])] merged by furniture type, in display order."""
    from collections import OrderedDict
    groups: OrderedDict = OrderedDict()
    for mod in _library_mods_3d(section):
        cat = _ZONE_CATEGORY_3D.get(mod["zone"], mod["zone"].replace("_", " ").title())
        groups.setdefault(cat, []).append(mod)
    return sorted(groups.items(),
                  key=lambda kv: _CATEGORY_ORDER_3D.index(kv[0])
                                 if kv[0] in _CATEGORY_ORDER_3D else 99)


def plot_zone_group_3d(zone_label: str, mods: list, n_cols: int = 4) -> plt.Figure:
    """Render one zone group as a tight grid of 3D module thumbnails."""
    n_rows = max(1, math.ceil(len(mods) / n_cols))
    fig = plt.figure(figsize=(n_cols * 3.2, n_rows * 3.0))
    fig.patch.set_facecolor("white")
    for i, mod in enumerate(mods):
        ax = fig.add_subplot(n_rows, n_cols, i + 1, projection="3d")
        _clean_ax(fig, ax)
        w, h, d = mod["w"], mod["h"], mod["d"]
        _draw_module_3d(ax, mod, 0.0, 0.0, 0.0, w, h, d)
        ax.set_xlim(0, w); ax.set_ylim(0, d); ax.set_zlim(0, h)
        ax.set_box_aspect((w, d, h))
        ax.view_init(elev=20, azim=-55)
        label = mod["id"].replace("chair_left_", "cl_").replace("chair_right_", "cr_") \
                         .replace("_3d_v", "_v").replace("roof_3d_v1", "roof")
        ax.set_title(f"{label}\n{w}×{h}×{d}", fontsize=6, pad=3)
        ax.tick_params(labelsize=4)
        ax.grid(False)
    fig.tight_layout()
    return fig


def plot_module_library_3d(section: str = "") -> plt.Figure:
    allowed_zones = _SECTION_ZONES_3D.get(section, None)
    mods = sorted(
        (m for m in MODULES_3D.values()
         if m["zone"] != "filler"
         and "conn_" not in m["id"]
         and (allowed_zones is None or m["zone"] in allowed_zones)
         and "legacy" not in m.get("description", "")),
        key=lambda m: (
            ZONE_ORDER.index(m["zone"]) if m["zone"] in ZONE_ORDER else 99,
            m["h"],
            m["id"],
        ),
    )

    n_cols = 5
    n_rows = math.ceil(len(mods) / n_cols)
    fig = plt.figure(figsize=(n_cols * 3.2, n_rows * 3.0))
    fig.patch.set_facecolor("white")

    for i, mod in enumerate(mods):
        ax = fig.add_subplot(n_rows, n_cols, i + 1, projection="3d")
        _clean_ax(fig, ax)
        w, h, d = mod["w"], mod["h"], mod["d"]
        _draw_module_3d(ax, mod, 0.0, 0.0, 0.0, w, h, d)
        ax.set_xlim(0, w); ax.set_ylim(0, d); ax.set_zlim(0, h)
        ax.set_box_aspect((w, d, h))
        ax.view_init(elev=20, azim=-55)
        label = mod["id"].replace("chair_left_", "cl_").replace("chair_right_", "cr_") \
                         .replace("table_", "t_").replace("shelf_", "s_") \
                         .replace("_3d_v", "_v").replace("roof_3d_v1", "roof")
        ax.set_title(f"{label}\n{w}×{h}×{d}", fontsize=6, pad=3)
        ax.tick_params(labelsize=4)
        ax.grid(False)

    fig.suptitle("Nomadic Engine — 3D Module Library", fontsize=12, y=1.0)
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
