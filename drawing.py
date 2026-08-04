import math
import pathlib
from typing import List

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

from modules import MODULES, ZONE_COLORS, ZONE_ALPHAS, LINE_COLOR, PORT_COLOR, GRID_COLOR, ZONE_ORDER, _SHELF_CATEGORY
from solver import get_segments, get_ports


def _draw_grid(ax, ox: float, oy: float, w: int, h: int,
               grid_color: str = GRID_COLOR) -> None:
    for i in range(w + 1):
        lw = 1.2 if i in (0, w) else 0.3
        ax.plot([ox + i, ox + i], [oy, oy + h], color=grid_color, lw=lw, zorder=1)
    for j in range(h + 1):
        lw = 1.2 if j in (0, h) else 0.3
        ax.plot([ox, ox + w], [oy + j, oy + j], color=grid_color, lw=lw, zorder=1)


def _draw_module(ax, mod: dict, x_off: float, y_off: float,
                 show_grid: bool = True, show_ports: bool = True,
                 placed_w: int = None, placed_h: int = None,
                 line_color_override: str | None = None,
                 grid_color_override: str | None = None,
                 no_fills: bool = False,
                 pipe: bool = False) -> None:
    w = placed_w if placed_w is not None else mod["w"]
    h = placed_h if placed_h is not None else mod["h"]
    lc = line_color_override or LINE_COLOR
    gc = grid_color_override or GRID_COLOR

    if show_grid:
        if not no_fills:
            zone = mod.get("zone", "")
            fc    = ZONE_COLORS.get(zone, "#ffffff")
            alpha = ZONE_ALPHAS.get(zone, 0.50)
            ax.add_patch(patches.Rectangle(
                (x_off, y_off), w, h,
                facecolor=fc, alpha=alpha, zorder=0, linewidth=0,
            ))
        _draw_grid(ax, x_off, y_off, w, h, grid_color=gc)

    for seg in get_segments(mod, w, h):
        xs = [p[0] + x_off for p in seg]
        ys = [p[1] + y_off for p in seg]
        ax.plot(xs, ys, color=lc, lw=2.2, zorder=3,
                solid_capstyle="round", solid_joinstyle="round")

    if show_ports:
        for pts in get_ports(mod, w, h).values():
            for px, py in pts:
                ax.plot(px + x_off, py + y_off, "o",
                        color=PORT_COLOR, ms=6, zorder=4)


_SILHOUETTE_DIR   = pathlib.Path(__file__).parent / "presentaion"
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
        if raw.ndim == 2:
            raw = np.stack([raw, raw, raw, np.ones_like(raw)], axis=-1)
        elif raw.shape[2] == 3:
            raw = np.concatenate([raw, np.ones((*raw.shape[:2], 1))], axis=-1)
        else:
            raw = raw.copy()
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


def plot_section(placed: List[dict], W: int, H: int,
                 show_figures: bool = False,
                 roof_style: str = "any",
                 dark: bool = False) -> plt.Figure:
    scale = max(1.2, 8.0 / W)
    fig, ax = plt.subplots(figsize=(W * scale, H * scale))

    line_color = "#c8d0c8" if dark else LINE_COLOR
    grid_color = "#3a4038" if dark else GRID_COLOR
    label_color = "#8a9a88" if dark else "#666666"

    for p in placed:
        mod = MODULES[p["module_id"]]
        _draw_module(ax, mod, p["x_off"], p["y_off"], placed_w=p["w"], placed_h=p["h"],
                     line_color_override=line_color, grid_color_override=grid_color,
                     no_fills=dark, show_ports=not dark)
        if not dark:
            cx = p["x_off"] + p["w"] / 2
            cy = p["y_off"] + mod["h"] / 2
            ax.text(cx, cy, mod["zone"].replace("_", "\n"),
                    ha="center", va="center", fontsize=7, color=label_color, alpha=0.7)

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
            elif zone == "lower_cabinet":
                _draw_silhouette(ax, standing_img, cx + 2, p["y_off"] + 0.5, height_units=4.5,
                                 clip_patch=clip)

    ax.set_xlim(-0.3, W + 0.3)
    ax.set_ylim(-0.3, H + 0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    if not dark:
        ax.set_title(f"Nomadic Engine — Section  {W} × {H}", fontsize=12, pad=10)

    if dark:
        fig.patch.set_facecolor("none")
        ax.set_facecolor("none")

    fig.tight_layout()
    return fig


_SECTION_ZONES: dict = {
    "Dining":  {"chair_left", "chair_right", "table", "shelf", "corridor_left", "corridor_right"},
    "Kitchen": {"lower_cabinet", "upper_cabinet", "kitchen_wall", "shelf", "corridor_left", "corridor_right"},
    "Living":  {"sofa", "tv_table", "table", "shelf", "corridor_left", "corridor_right"},
    "Bed":     {"bed", "shelf", "corridor_left", "corridor_right"},
}

def _library_mods(section: str):
    """Return module list filtered + sorted for a section's library view."""
    allowed = _SECTION_ZONES.get(section)
    return sorted(
        (m for m in MODULES.values()
         if (allowed is None or m["zone"] in allowed)
         and "narrow" not in m["id"]
         and not (m["zone"] in ("chair_left", "chair_right") and "_corr_" in m["id"])
         and not (m["zone"] == "tv_table" and "_corr_" in m["id"])
         and not (section == "Kitchen" and m["zone"] == "shelf" and "_corr_" in m["id"])
         and not (section == "Kitchen" and m["zone"] == "shelf"
                  and _SHELF_CATEGORY.get(m["id"]) == "divided")),
        key=lambda m: (
            ZONE_ORDER.index(m["zone"]) if m["zone"] in ZONE_ORDER else 99,
            m["id"],
        ),
    )


_ZONE_CATEGORY: dict[str, str] = {
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
    "filler":         "Fillers",
}

_CATEGORY_ORDER: list[str] = [
    "Beds", "Chairs", "Sofas", "TV Tables", "Tables",
    "Lower Cabinets", "Upper Cabinets", "Kitchen Walls",
    "Shelves", "Corridors", "Fillers",
]


def get_library_by_zone(section: str) -> list[tuple[str, list]]:
    """Return [(category_label, [mods])] merged by furniture type, in display order."""
    from collections import OrderedDict
    groups: OrderedDict = OrderedDict()
    for mod in _library_mods(section):
        cat = _ZONE_CATEGORY.get(mod["zone"], mod["zone"].replace("_", " ").title())
        groups.setdefault(cat, []).append(mod)
    # sort by _CATEGORY_ORDER
    ordered = sorted(groups.items(),
                     key=lambda kv: _CATEGORY_ORDER.index(kv[0])
                                    if kv[0] in _CATEGORY_ORDER else 99)
    return ordered


def plot_zone_group(zone_label: str, mods: list, n_cols: int = 4) -> plt.Figure:
    """Render one zone group as a tight grid of module thumbnails."""
    pad = 0.8
    n_rows = max(1, math.ceil(len(mods) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(n_cols * 3.5, n_rows * 3.2),
                             squeeze=False)
    flat = axes.flatten()
    for i, mod in enumerate(mods):
        ax = flat[i]
        w, h = mod["w"], mod["h"]
        _draw_module(ax, mod, 0.0, 0.0, show_grid=True, show_ports=True)
        ax.set_xlim(-pad, w + pad)
        ax.set_ylim(-pad, h + pad)
        ax.set_aspect("equal")
        ax.axis("off")
        short = mod["id"].replace("filler_", "")
        ax.set_title(f'{short}\n{w}w × {h}h', fontsize=7.5, pad=3)
    for j in range(len(mods), len(flat)):
        flat[j].axis("off")
    fc = ZONE_COLORS.get(mods[0]["zone"] if mods else "filler", "#e0e0e0") if mods else "#e0e0e0"
    fig.patch.set_facecolor(fc + "33")
    fig.tight_layout(pad=0.6)
    return fig

def plot_module_library(section: str = "Dining") -> plt.Figure:
    allowed = _SECTION_ZONES.get(section)
    mods = sorted(
        (m for m in MODULES.values()
         if (allowed is None or m["zone"] in allowed)
         and "narrow" not in m["id"]
         and not (m["zone"] in ("chair_left", "chair_right") and "_corr_" in m["id"])
         and not (m["zone"] == "tv_table" and "_corr_" in m["id"])
         and not (section == "Kitchen" and m["zone"] == "shelf" and "_corr_" in m["id"])
         and not (section == "Kitchen" and m["zone"] == "shelf"
                  and _SHELF_CATEGORY.get(m["id"]) == "divided")),
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

        short = mod["id"].replace("filler_", "")
        ax.set_title(f'{short}\n{w}w × {h}h', fontsize=8, pad=4)

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


_PLAN_CORRIDOR_COLOR = "#B0ADA6"
_PLAN_SECTION_COLORS = {
    "dining":  "#7D8B7A",
    "kitchen": "#9A8870",
    "living":  "#6E7A6C",
    "bed":     "#7A9A9A",
    "bath":    "#7A9190",
}


def plot_plan_view(sections: list, corridor_side: str = "none",
                   corridor_w: int = 2, dark: bool = False) -> plt.Figure:
    """Top-down (plan) view of the assembled dwelling derived from solver results."""
    if not sections:
        return plt.figure()

    W       = max(s["W"] for s in sections)
    total_D = sum(s["d"] for s in sections)

    # Portrait figure sized proportionally to W × total_D.
    # Avoid set_aspect("equal") — it fights tight_layout and produces a square.
    # Instead size the figure so data fills it proportionally.
    base_w = 3.6   # inches
    fig_w  = base_w
    fig_h  = max(base_w * total_D / max(W, 1), 2.4)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    if dark:
        bg = "#0d1117"   # solid dark navy — plan reads like a blueprint
    else:
        bg = "white"
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)

    # Palettes
    _dk_fills = {
        "dining":  "#1e3a28", "kitchen": "#3a2a14",
        "living":  "#1a2545", "bed":     "#38183a", "bath": "#143838",
    }
    _dk_corr  = "#161c26"
    _dk_edge  = "#c8d4c8"
    _dk_clbl  = "#dde8dd"
    _dk_cclbl = "#6a7a6a"

    d_cursor = 0.0
    for s in sections:
        sec_d = s["d"]
        sec_W = s["W"]
        stype = s["type"]

        if dark:
            fill   = _dk_fills.get(stype, "#1e1e2e")
            edge   = _dk_edge
            cedge  = _dk_edge
            clbl   = _dk_clbl
            cclbl  = _dk_cclbl
            cfill  = _dk_corr
            lw_main   = 1.5
            lw_corr   = 0.8
            alpha_main = 1.0
            alpha_corr = 1.0
        else:
            fill   = _PLAN_SECTION_COLORS.get(stype, "#C8C5BE")
            edge   = "#333"
            cedge  = "#333"
            clbl   = "#333"
            cclbl  = "#333"
            cfill  = _PLAN_CORRIDOR_COLOR
            lw_main   = 1.0
            lw_corr   = 0.6
            alpha_main = 0.70
            alpha_corr = 0.70

        # font size scaled to cell height in figure inches
        cell_h_in = (fig_h / total_D) * sec_d
        fs = max(6, min(11, int(cell_h_in * 72 * 0.30)))

        if corridor_side == "right":
            inner_W = sec_W - corridor_w
            ax.add_patch(patches.Rectangle(
                (0, d_cursor), inner_W, sec_d,
                facecolor=fill, edgecolor=edge, linewidth=lw_main,
                alpha=alpha_main, zorder=1))
            ax.add_patch(patches.Rectangle(
                (inner_W, d_cursor), corridor_w, sec_d,
                facecolor=cfill, edgecolor=cedge, linewidth=lw_corr, alpha=alpha_corr))
            ax.text(inner_W / 2, d_cursor + sec_d / 2, stype.upper(),
                    ha="center", va="center", fontsize=fs, color=clbl, alpha=0.95)
            ax.text(inner_W + corridor_w / 2, d_cursor + sec_d / 2, "—",
                    ha="center", va="center", fontsize=fs - 2, color=cclbl, alpha=0.7, rotation=90)
        elif corridor_side == "left":
            inner_W = sec_W - corridor_w
            ax.add_patch(patches.Rectangle(
                (0, d_cursor), corridor_w, sec_d,
                facecolor=cfill, edgecolor=cedge, linewidth=lw_corr, alpha=alpha_corr))
            ax.add_patch(patches.Rectangle(
                (corridor_w, d_cursor), inner_W, sec_d,
                facecolor=fill, edgecolor=edge, linewidth=lw_main,
                alpha=alpha_main, zorder=1))
            ax.text(corridor_w + inner_W / 2, d_cursor + sec_d / 2, stype.upper(),
                    ha="center", va="center", fontsize=fs, color=clbl, alpha=0.95)
            ax.text(corridor_w / 2, d_cursor + sec_d / 2, "—",
                    ha="center", va="center", fontsize=fs - 2, color=cclbl, alpha=0.7, rotation=90)
        else:
            ax.add_patch(patches.Rectangle(
                (0, d_cursor), sec_W, sec_d,
                facecolor=fill, edgecolor=edge, linewidth=lw_main,
                alpha=alpha_main, zorder=1))
            ax.text(sec_W / 2, d_cursor + sec_d / 2, stype.upper(),
                    ha="center", va="center", fontsize=fs, color=clbl, alpha=0.95)

        d_cursor += sec_d

    pad = 0.1
    ax.set_xlim(-pad, W + pad)
    ax.set_ylim(-pad, total_D + pad)
    ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    return fig


def plot_grid_only(W: int, H: int, section_type: str,
                   corridor: str = "none", corridor_w: int = 2) -> plt.Figure:
    SECTION_COLORS = {
        "Kitchen": "#f5deb3",
        "Living":  "#d0e8d0",
        "Bed":     "#e8d0e0",
    }
    fill = SECTION_COLORS.get(section_type, "#f0f0f0")
    corr_fill = "#b0c4de"

    scale = max(1.2, 8.0 / W)
    fig, ax = plt.subplots(figsize=(W * scale, H * scale))

    if corridor == "corridor_right":
        inner_W = W - corridor_w
        ax.add_patch(patches.Rectangle((0, 0), inner_W, H,
                     facecolor=fill, alpha=0.50, zorder=0, linewidth=0))
        ax.add_patch(patches.Rectangle((inner_W, 0), corridor_w, H,
                     facecolor=corr_fill, alpha=0.50, zorder=0, linewidth=0))
        _draw_grid(ax, 0, 0, inner_W, H)
        _draw_grid(ax, inner_W, 0, corridor_w, H)
        ax.text(inner_W + corridor_w / 2, H / 2, "corridor",
                ha="center", va="center", fontsize=7, color="#446688", alpha=0.7, rotation=90)
        cx = inner_W / 2
    elif corridor == "corridor_left":
        inner_W = W - corridor_w
        ax.add_patch(patches.Rectangle((0, 0), corridor_w, H,
                     facecolor=corr_fill, alpha=0.50, zorder=0, linewidth=0))
        ax.add_patch(patches.Rectangle((corridor_w, 0), inner_W, H,
                     facecolor=fill, alpha=0.50, zorder=0, linewidth=0))
        _draw_grid(ax, 0, 0, corridor_w, H)
        _draw_grid(ax, corridor_w, 0, inner_W, H)
        ax.text(corridor_w / 2, H / 2, "corridor",
                ha="center", va="center", fontsize=7, color="#446688", alpha=0.7, rotation=90)
        cx = corridor_w + inner_W / 2
    else:
        ax.add_patch(patches.Rectangle((0, 0), W, H,
                     facecolor=fill, alpha=0.50, zorder=0, linewidth=0))
        _draw_grid(ax, 0, 0, W, H)
        cx = W / 2

    ax.text(cx, H / 2, f"{section_type}\n(grid only)",
            ha="center", va="center", fontsize=10, color="#555555", alpha=0.5)

    ax.set_xlim(-0.3, W + 0.3)
    ax.set_ylim(-0.3, H + 0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Nomadic Engine — {section_type}  {W} × {H}", fontsize=12, pad=10)
    fig.tight_layout()
    return fig
