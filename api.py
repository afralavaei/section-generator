"""
FastAPI backend for the Nomadic Engine configurator.

Endpoints:
  POST /render      — solve + render any section in 2D or 3D
  POST /onboarding  — translate 5 onboarding answers + site into an initial spec + render
  POST /chat        — modify dining spec via natural language + return reply + updated render
"""
import base64
import copy
import io
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before any pyplot import
import matplotlib.pyplot as plt

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm import chat_modify_dining, onboarding_to_spec
from sites import site_to_roof_style
from solver import solve
from solver3d import solve3d
from dwelling import solve_dwelling_3d, dwelling_sections_meta
from drawing import plot_section, plot_plan_view
from viewer3d import plot_section_3d, plot_dwelling_3d, _draw_module_3d, _clean_ax
from export import export_section_3d_json
from modules import MODULES
from modules3d import MODULES_3D, _SHELF_CAT_3D

app = FastAPI(title="Nomadic Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dwelling-spec")
def get_dwelling_spec():
    return _DEFAULT_DWELLING_SPEC


# ── Greeting / suggestion helpers ─────────────────────────────────────────────

def _spec_summary(spec: dict) -> str:
    tags  = spec.get("preferred_tags", [])
    parts = [
        f"style **{spec.get('dining_style', 'compact')}**",
        f"**{spec.get('num_chairs', 2)} chair{'s' if spec.get('num_chairs', 2) > 1 else ''}**",
        f"height **{spec.get('h', 7)}**",
        f"depth **{spec.get('d', 3)}**",
        f"roof **{spec.get('roof_style', 'any')}**",
    ]
    if tags:
        parts.append(f"tags **{', '.join(tags)}**")
    return " · ".join(parts)


def _initial_greeting(site: dict, answers: dict, spec: dict) -> str:
    # Accept both React short-form IDs and legacy long-form IDs.
    _occ = {
        "solo": "just you", "couple": "two people",
        "family": "your family", "group": "a large group", "large_group": "a large group",
    }
    _pur = {
        "work": "remote work", "remote_work": "remote work",
        "retreat": "relaxation",
        "social": "hosting guests", "socialising": "hosting guests",
        "research": "field research", "field_research": "field research",
    }
    occ_str = _occ.get(answers.get("occupants", ""), answers.get("occupants", "couple"))
    pur_str  = _pur.get(answers.get("purpose",   ""), answers.get("purpose",   "remote work"))
    return (
        f"Hi! I'm your Nomadic Engine assistant. Based on your answers, I've designed "
        f"a dining space for **{occ_str}** at **{site.get('name', 'your site')}**, "
        f"suited for **{pur_str}**.\n\n"
        f"{_spec_summary(spec)}\n\n"
        "Is there anything you'd like to adjust?"
    )


def _dining_suggestions(spec: dict, answers: dict) -> list[str]:
    sugg: list[str] = []
    if spec.get("dining_style") == "compact":
        sugg.append("Make it more spacious and open")
    else:
        sugg.append("Make it more compact and efficient")
    if spec.get("h", 7) <= 8:
        sugg.append("Raise the ceiling — make it feel more dramatic")
    else:
        sugg.append("Lower the ceiling for a cosier feel")
    if "more_shelves" not in spec.get("preferred_tags", []):
        sugg.append("Add storage shelves above the table")
    else:
        sugg.append("Remove the overhead shelves")
    occ = answers.get("occupants", "couple")
    if occ in ("family", "group", "large_group"):
        sugg.append("Make it better for hosting large gatherings")
    elif occ == "solo":
        sugg.append("Give the single-person setup more presence")
    else:
        sugg.append("Make it feel more intimate for two")
    return sugg


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dining_W(dining_style: str, num_chairs: int, corridor_side: str, corridor_w: int) -> int:
    inner = (6 if dining_style == "compact" else 8) if num_chairs == 2 \
            else (4 if dining_style == "compact" else 5)
    return inner + (corridor_w if corridor_side != "none" else 0)


# Default W for each non-dining section — all locked to 8 for demo
_SECTION_W = {
    "kitchen": lambda cw: 8,
    "living":  lambda cw: 8,
    "bed":     lambda cw: 8,
}

# Sections that always use corridor_right internally
_ALWAYS_CORR_RIGHT = {"kitchen", "bed"}

_DEFAULT_DWELLING_SPEC = {
    "corridor_side": "right",
    "corridor_w": 2,
    "W": 8,
    "H": 7,
    "roof_style": "pitched",
    "functions": [
        {"type": "dining",  "d": 3, "seed": 46, "dining_style": "spacious", "roof_style": "pitched", "living_combo": "full"},
        {"type": "kitchen", "d": 4, "seed": 45, "dining_style": "spacious", "roof_style": "pitched", "living_combo": "full"},
        {"type": "living",  "d": 3, "seed": 44, "dining_style": "spacious", "roof_style": "pitched", "living_combo": "full"},
        {"type": "bed",     "d": 4, "seed": 42, "dining_style": "spacious", "roof_style": "pitched", "living_combo": "full"},
    ],
}


def _merge_dining_into_dwelling(dining_spec: dict) -> dict:
    """Return a copy of _DEFAULT_DWELLING_SPEC with the dining function replaced
    by the user's onboarding dining params.  Also updates H, W, corridor_side, roof_style."""
    merged = copy.deepcopy(_DEFAULT_DWELLING_SPEC)
    num_chairs    = dining_spec.get("num_chairs", 2)
    corridor_side = dining_spec.get("corridor_side", merged["corridor_side"])
    # solo always needs corridor
    if num_chairs == 1 and corridor_side == "none":
        corridor_side = "right"
    corridor_w = dining_spec.get("corridor_w", merged["corridor_w"])
    merged["corridor_side"] = corridor_side
    merged["corridor_w"]    = corridor_w
    if "h" in dining_spec:
        # Cap dwelling H at 8 — kitchen/living/bed solvers get unstable above that.
        # The standalone dining tab still uses the full h from the spec.
        merged["H"] = min(int(dining_spec["h"]), 8)
    # Dwelling-wide roof defaults to pitched — kitchen/living/bed renders
    # assume it. Dining used to be forced onto this same default too
    # ("ignore whatever the LLM returned"), which silently erased any
    # roof_style change made via chat (e.g. "add storage shelves" ->
    # roof_style: "divided") the moment you looked at the assembled
    # dwelling instead of the standalone dining tab. Dining now keeps
    # whatever roof_style is actually in its own spec; only the other
    # functions fall back to the dwelling-wide pitched default.
    roof_style = "pitched"
    merged["roof_style"] = roof_style
    # Store dining W at dwelling level so living can match it.
    dining_style = dining_spec.get("dining_style", "compact")
    merged["W"] = _dining_W(dining_style, num_chairs, corridor_side, corridor_w)
    for fn in merged.get("functions", []):
        if fn.get("type") == "dining":
            for key in ("dining_style", "num_chairs", "d", "preferred_tags", "seed", "roof_style"):
                if key in dining_spec:
                    fn[key] = dining_spec[key]
        else:
            fn["roof_style"] = roof_style
    return merged


def _render_dwelling(spec: dict | None = None,
                     highlight_section: str | None = None) -> str | None:
    """Solve + render the full assembled dwelling in 3D. Returns base64 PNG or None."""
    dw_spec = spec if spec else _DEFAULT_DWELLING_SPEC
    sections = solve_dwelling_3d(dw_spec)
    if not any(s["placed"] is not None for s in sections):
        return None
    fig = plot_dwelling_3d(sections,
                           corridor_side=dw_spec.get("corridor_side", "right"),
                           corridor_w=dw_spec.get("corridor_w", 2),
                           dark=True,
                           highlight_section=highlight_section)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                transparent=True, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _render_plan(dw_spec: dict) -> str | None:
    """Render the dwelling plan view (top-down) from section metadata only."""
    sections = dwelling_sections_meta(dw_spec)
    if not sections:
        return None
    fig = plot_plan_view(
        sections,
        corridor_side=dw_spec.get("corridor_side", "right"),
        corridor_w=int(dw_spec.get("corridor_w", 2)),
        dark=True,
    )
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                transparent=False, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _zone_overrides_from_2d(placed_2d: list[dict] | None) -> dict:
    """2D and 3D are independent module libraries (own solves, own random
    picks) — same seed doesn't guarantee the same variant in both, e.g. the
    2D solve might place table_h2_v1 while the 3D solve independently picks
    table_h2_v3 for the same slot. Streamlit's app.py sidesteps this with a
    manual per-zone override map (module_overrides); this derives that same
    kind of override automatically from whatever the 2D solve just placed,
    for every zone whose 2D module id is ALSO a valid 3D module id for that
    same zone (chairs, table — most named/catalogued furniture). Modules
    whose 3D counterpart uses a different naming convention (corridor,
    "_corr" chair variants) or is procedurally generated per-gap rather
    than catalogued (the "_frs_"/"_frs3d_" shelf-fill modules) aren't
    covered by this — those still solve independently in 2D vs 3D.
    """
    overrides: dict[str, str] = {}
    for p in placed_2d or []:
        mid = p.get("module_id", "")
        zone = MODULES.get(mid, {}).get("zone")
        if zone and mid in MODULES_3D and MODULES_3D[mid].get("zone") == zone:
            overrides[zone] = mid
    return overrides


# ── Manual furniture style picker (dining, 3D only) ─────────────────────────
# Ported from app.py's picker column — same option-matching rules, same
# module library, so "chair style"/"table style"/"shelf style" mean the same
# thing here as they do in the Streamlit reference.

def _furniture_thumbnail_b64(module_id: str) -> str:
    """Small isolated 3D render of a single catalog module, styled to match
    the dark dwelling/section renders (_clean_ax(dark=True) — transparent
    background, light line color) rather than app.py's white-background
    Streamlit thumbnail, since these sit inside the same dark glass UI."""
    mod = MODULES_3D[module_id]
    w, h, d = mod["w"], mod["h"], 3
    fig = plt.figure(figsize=(1.4, 1.4))
    ax = fig.add_subplot(111, projection="3d")
    _clean_ax(fig, ax, dark=True)
    _draw_module_3d(ax, mod, 0.0, 0.0, 0.0, w, h, d,
                    show_voxel=True, show_ports=False, show_zone_fill=False,
                    line_color_override="#e8ece8", grid_color_override="#2a3028")
    ax.set_xlim(0, w); ax.set_ylim(0, d); ax.set_zlim(0, h)
    ax.set_box_aspect((w, d, h))
    ax.view_init(elev=20, azim=-55)
    ax.set_axis_off()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                transparent=True, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# Excluded from every picker outright — the four earliest native-3D
# placeholder modules (tagged "native3d"), from before the catalog switched
# to the "lifted" (2D-extruded) module set. Visually inconsistent with the
# rest of the catalog, and — confirmed live while building this — their
# port geometry doesn't reliably close the circuit against neighboring
# modules in every dining_style/roof combination (table_3d_v1 and
# roof_3d_v1 both silently break the render — "no valid section found" —
# under some but not all configs, which is worse than just being ugly).
# Kept in MODULES_3D itself so anything that already references one by id
# (zone_overrides, auto 2D-matching) still works; only excluded from being
# offered as a NEW pick.
_NATIVE3D_PICKER_EXCLUDE = {
    "chair_left_3d_v1", "chair_right_3d_v1", "table_3d_v1", "roof_3d_v1",
}


def _chair_options(d_val: int) -> list[dict]:
    """Return every chair variant — both height classes — that fits the
    given depth, each tagged with its own ``h`` (2 or 3).

    Unlike table/shelf, a plain zone_override isn't enough to pick a
    different-height chair: the chair zone's own vertical span is pinned to
    "first 2" or "first 3" cells, and by default that's driven by
    dining_style (compact/spacious). But it can ALSO be driven independently
    by preferred_tags — "tall_chairs"/"low_chairs" resize just the chair
    zone, leaving the table zone (and dining_style itself) untouched — see
    _apply_furniture_height in llm.py and _chair_rule_3d in solver3d.py.
    Verified live: dining_style "compact" + preferred_tags ["tall_chairs"]
    solves a full h3 chair alongside a normal h2 table. So the frontend
    picker can offer every height here, as long as picking one that isn't
    the chair's current height also patches preferred_tags to match — see
    applyChairOverride in ConfiguratorPortfolio.tsx.
    """
    pairs = []
    for mid, m in MODULES_3D.items():
        if (m.get("zone") == "chair_left"
                and "_corr_" not in mid and not mid.startswith("_frs")
                and mid not in _NATIVE3D_PICKER_EXCLUDE):
            d_ok = m.get("scalable_d") or "whd_segments_fn" in m or m.get("d", 3) == d_val
            if not d_ok:
                continue
            right_mid = mid.replace("chair_left_", "chair_right_")
            if right_mid in MODULES_3D:
                pairs.append({"left": mid, "right": right_mid, "h": m.get("h")})
    return sorted(pairs, key=lambda p: (p["h"], p["left"]))


def _table_options(h_val: int, d_val: int) -> list[str]:
    """Return every table module id at the given height class that fits the
    given depth — h_val is a hard filter for the same structural reason as
    _chair_options above. Wide-top vs narrow is NOT restricted anymore
    (verified safe: every wide-top variant shares the exact w/h/d envelope
    of its narrow counterpart at the same class), so both styles now show
    together instead of only one."""
    results = []
    for mid, m in MODULES_3D.items():
        if (m.get("zone") == "table" and m.get("h") == h_val
                and not mid.startswith("_frs")
                and mid not in _NATIVE3D_PICKER_EXCLUDE):
            d_ok = m.get("scalable_d") or "whd_segments_fn" in m or m.get("d", 3) == d_val
            if d_ok:
                results.append(mid)
    return sorted(results)


def _shelf_suffix(mid: str) -> str:
    for suf in ("_corr_r", "_corr_l"):
        if mid.endswith(suf):
            return suf
    return ""


def _shelf_base_id(shelf_mid: str) -> str | None:
    """Resolve a placed shelf's module_id back to a catalog id — placed shelves
    are sometimes a runtime-generated full-roof variant (``_frs3d_<base>_...``)."""
    if not shelf_mid.startswith("_frs3d_"):
        return shelf_mid
    rest = shelf_mid[len("_frs3d_"):]
    candidates = [k for k in _SHELF_CAT_3D if rest.startswith(k + "_")]
    return max(candidates, key=len) if candidates else None


def _shelf_options(d_val: int) -> list[str]:
    """Return every catalog shelf module id (any roof-style category —
    plain/slanted/pitched/divided — any height class) that fits the given
    depth. No longer locked to the currently-placed shelf's category: a
    manually-picked shelf goes through solve3d's zone_overrides, which
    bypasses the roof_style category filter and only still checks the
    geometric fit (see _build_options_3d / the corridor shelf branch in
    solver3d.py), so the full catalog is a safe — and much bigger — set of
    options to offer."""
    results = []
    for mid, m in MODULES_3D.items():
        if (m.get("zone") == "shelf" and not mid.startswith("_frs3d_")
                and not mid.endswith(("_corr_r", "_corr_l"))
                and mid not in _NATIVE3D_PICKER_EXCLUDE):
            d_ok = m.get("scalable_d") or "whd_segments_fn" in m or m.get("d", 3) == d_val
            if d_ok:
                results.append(mid)
    return sorted(results)


def _render_section(spec: dict, section: str = "dining", view: str = "2D",
                    highlight: str = "", manual_overrides: dict | None = None) -> str | None:
    """Solve + render any section (or the full dwelling) in 2D or 3D."""
    if section == "dwelling":
        dw_spec = spec.get("dwelling_spec") or _merge_dining_into_dwelling(spec)
        if view == "plan":
            return _render_plan(dw_spec)
        return _render_dwelling(dw_spec, highlight_section=highlight or None)
    H            = spec.get("h",             7)
    D            = spec.get("d",             3)
    seed         = spec.get("seed",          42)
    # Kitchen/living/bed stay locked to pitched (demo stability — chat never
    # touches their roof anyway). Dining is chat-controlled (e.g. "add
    # storage shelves" -> roof_style: "divided"), so it has to read its own
    # spec instead of being locked too — the standalone dining tab was
    # always rendering pitched regardless of what chat actually set,
    # completely independent of (and inconsistent with) the dwelling-
    # assembled view, which already read this correctly.
    roof_style   = spec.get("roof_style", "pitched") if section == "dining" else "pitched"
    corridor_side = spec.get("corridor_side", "none")
    corridor_w   = spec.get("corridor_w",    2)

    if section == "dining":
        dining_style   = spec.get("dining_style",   "compact")
        num_chairs     = spec.get("num_chairs",      2)
        preferred_tags = spec.get("preferred_tags",  [])
        # 1-chair dining with no corridor places table at "middle 2" which overlaps
        # chair_left at "first 2" when inner_W=4.  Force corridor_right so the solver
        # uses ZONES_FULL_ROOF_CORR_RIGHT_1CHAIR (chair[0,2) + table[2,4) — no overlap).
        if num_chairs == 1 and corridor_side == "none":
            corridor_side = "right"
        W = _dining_W(dining_style, num_chairs, corridor_side, corridor_w)
        solver_corr = f"corridor_{corridor_side}" if corridor_side in ("right", "left") else "none"
    else:
        dining_style   = spec.get("dining_style", "compact")
        preferred_tags = []
        dwelling_w     = int(spec["w"]) if spec.get("w") else None

        if section == "living":
            # Living tracks dwelling W when it's wide enough for a corridor (≥8).
            # Solo (W=6) falls back to W=7 without corridor — living solver minimum.
            if dwelling_w and dwelling_w >= 8:
                W = dwelling_w
                solver_corr = f"corridor_{corridor_side}" if corridor_side in ("right", "left") else "none"
            else:
                W = 7
                solver_corr = "none"
        elif section in _ALWAYS_CORR_RIGHT:
            if section == "kitchen":
                corridor_w = 3  # inner_W=5 + corridor=3 = W=8
            W = _SECTION_W[section](corridor_w)
            solver_corr = "corridor_right"
        else:
            W = _SECTION_W[section](corridor_w)
            solver_corr = f"corridor_{corridor_side}" if corridor_side in ("right", "left") else "none"

    if view == "3D":
        # Solve 2D first (same params) purely to read off which furniture it
        # picked, so the 3D solve can be steered onto the same choices
        # instead of independently random-picking — see
        # _zone_overrides_from_2d for what this can and can't cover.
        placed_2d_ref = solve(
            W, H, seed,
            corridor=solver_corr,
            corridor_w=corridor_w,
            dining_style=dining_style,
            roof_style=roof_style,
            section=section,
            preferred_tags=preferred_tags if section == "dining" else None,
        )
        placed = solve3d(
            W, H, D, seed,
            corridor=solver_corr,
            corridor_w=corridor_w,
            dining_style=dining_style,
            roof_style=roof_style,
            section=section,
            preferred_tags=preferred_tags if section == "dining" else None,
            zone_overrides={**_zone_overrides_from_2d(placed_2d_ref), **(manual_overrides or {})},
        )
        if placed is None:
            return None
        fig = plot_section_3d(placed, W, H, D, dark=True)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    transparent=True, edgecolor="none")
        plt.close(fig)
    else:
        placed = solve(
            W, H, seed,
            corridor=solver_corr,
            corridor_w=corridor_w,
            dining_style=dining_style,
            roof_style=roof_style,
            section=section,
            preferred_tags=preferred_tags if section == "dining" else None,
        )
        if placed is None:
            return None
        fig = plot_section(placed, W, H, dark=True)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="none", edgecolor="none")
        plt.close(fig)

    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# Keep legacy alias used by /onboarding and /chat (dining-only, 2D)
def _render(spec: dict) -> str | None:
    return _render_section(spec, section="dining", view="2D")


# ── Request models ────────────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    site: dict
    answers: dict


class ChatRequest(BaseModel):
    current_spec: dict
    message: str
    history: list[dict] = []


class RenderRequest(BaseModel):
    spec: dict
    section: str = "dining"
    view: str = "2D"
    manual_overrides: dict[str, str] | None = None


class FurnitureOptionsRequest(BaseModel):
    spec: dict
    manual_overrides: dict[str, str] | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/render")
def render(req: RenderRequest):
    image_b64 = _render_section(req.spec, section=req.section, view=req.view,
                                manual_overrides=req.manual_overrides)
    return {"image_b64": image_b64}


@app.post("/furniture-options")
def furniture_options(req: FurnitureOptionsRequest):
    """Dining-only, 3D-only. Solves dining with the current overrides applied
    (auto 2D-matched + any manual picks) and reports the currently-placed
    chair/table/shelf modules plus every catalog variant that fits the same
    h/d slot — mirrors app.py's picker column (_chair_options/_table_options/
    _shelf_options) so Under the Hood offers the same manual style swap."""
    spec = req.spec
    H              = spec.get("h",             7)
    D              = spec.get("d",              3)
    seed           = spec.get("seed",          42)
    roof_style     = spec.get("roof_style", "pitched")
    corridor_side  = spec.get("corridor_side", "none")
    corridor_w     = spec.get("corridor_w",     2)
    dining_style   = spec.get("dining_style", "compact")
    num_chairs     = spec.get("num_chairs",     2)
    preferred_tags = spec.get("preferred_tags", [])
    if num_chairs == 1 and corridor_side == "none":
        corridor_side = "right"
    W = _dining_W(dining_style, num_chairs, corridor_side, corridor_w)
    solver_corr = f"corridor_{corridor_side}" if corridor_side in ("right", "left") else "none"

    placed_2d_ref = solve(
        W, H, seed, corridor=solver_corr, corridor_w=corridor_w,
        dining_style=dining_style, roof_style=roof_style, section="dining",
        preferred_tags=preferred_tags,
    )
    overrides = {**_zone_overrides_from_2d(placed_2d_ref), **(req.manual_overrides or {})}
    placed = solve3d(
        W, H, D, seed, corridor=solver_corr, corridor_w=corridor_w,
        dining_style=dining_style, roof_style=roof_style, section="dining",
        preferred_tags=preferred_tags, zone_overrides=overrides,
    )
    if placed is None:
        return {"chair_options": [], "table_options": [], "shelf_options": [], "current": {}, "thumbnails": {}}

    current: dict[str, str] = {}
    chair_options: list[dict] = []
    table_options: list[str] = []
    shelf_options: list[str] = []
    # module_id -> base64 PNG thumbnail, one entry per module_id that appears
    # anywhere above (chair thumbnails are keyed by the left id only, same as
    # app.py's picker grid — the right chair is implied by the pair).
    thumbnails: dict[str, str] = {}

    placed_cl = next((p for p in placed if MODULES_3D.get(p["module_id"], {}).get("zone") == "chair_left"), None)
    if placed_cl:
        current["chair_left"] = placed_cl["module_id"]
        placed_cr = next((p for p in placed if MODULES_3D.get(p["module_id"], {}).get("zone") == "chair_right"), None)
        if placed_cr:
            current["chair_right"] = placed_cr["module_id"]
        ch_opts = _chair_options(D)
        if len(ch_opts) > 1:
            chair_options = ch_opts
            for opt in ch_opts:
                thumbnails[opt["left"]] = _furniture_thumbnail_b64(opt["left"])

    placed_t = next((p for p in placed if MODULES_3D.get(p["module_id"], {}).get("zone") == "table"), None)
    if placed_t:
        current["table"] = placed_t["module_id"]
        t_opts = _table_options(placed_t["h"], D)
        if len(t_opts) > 1:
            table_options = t_opts
            for mid in t_opts:
                thumbnails[mid] = _furniture_thumbnail_b64(mid)

    placed_sh = next((p for p in placed if MODULES_3D.get(p["module_id"], {}).get("zone") == "shelf"), None)
    if placed_sh:
        # Runtime-generated full-roof shelves use a "_frs3d_<base>_..." id
        # that won't appear in the (now catalog-wide) options list — resolve
        # back to the catalog base id so the matching option still shows as
        # active instead of nothing being highlighted.
        current["shelf"] = _shelf_base_id(placed_sh["module_id"]) or placed_sh["module_id"]
        sh_opts = _shelf_options(D)
        if len(sh_opts) > 1:
            shelf_options = sh_opts
            for mid in sh_opts:
                thumbnails[mid] = _furniture_thumbnail_b64(mid)

    return {
        "chair_options": chair_options,
        "table_options": table_options,
        "shelf_options": shelf_options,
        "current": current,
        "thumbnails": thumbnails,
    }


@app.post("/sections-3d-json")
def sections_3d_json(req: RenderRequest):
    """Return 3D segment data for a section as JSON (for Three.js tube rendering)."""
    spec    = req.spec
    section = req.section or "dining"

    corridor_side = spec.get("corridor_side", "none")
    corridor_w    = int(spec.get("corridor_w", 2))
    corridor      = f"corridor_{corridor_side}" if corridor_side != "none" else "none"
    H             = int(spec.get("h", 7))
    D             = int(spec.get("d", 3))
    seed          = int(spec.get("seed", 42))
    dining_style  = spec.get("dining_style", "compact")
    roof_style    = spec.get("roof_style", "any")
    num_chairs    = int(spec.get("num_chairs", 2))

    W = _dining_W(dining_style, num_chairs, corridor_side, corridor_w)

    result = solve3d(W, H, D, seed, corridor, corridor_w,
                     dining_style, roof_style, section=section)
    if result is None:
        return {"error": "no solution", "segments": []}

    return export_section_3d_json(result, W, H, D, section)


@app.post("/onboarding")
def onboard(req: OnboardingRequest):
    params, err = onboarding_to_spec(req.site, req.answers)
    if params is None:
        return {"error": err, "spec": None, "image_b64": None, "reply": "", "suggestions": []}

    params.setdefault("corridor_side", "none")
    params.setdefault("corridor_w",    2)
    params.setdefault("seed",          42)

    # Demo locks: initial dining always starts at d=3, pitched roof.
    params["d"]          = 3
    params["roof_style"] = "pitched"

    dwelling_spec = _merge_dining_into_dwelling(params)
    image_b64   = _render(params)
    reply       = _initial_greeting(req.site, req.answers, params)
    suggestions = _dining_suggestions(params, req.answers)
    return {"spec": params, "dwelling_spec": dwelling_spec, "image_b64": image_b64, "reply": reply, "suggestions": suggestions}


@app.post("/chat")
def chat(req: ChatRequest):
    updated, reply = chat_modify_dining(req.current_spec, req.message, req.history)

    if updated is None:
        return {"spec": req.current_spec, "reply": reply, "image_b64": None}

    # Merge: current_spec is the base so fields outside the LLM schema
    # (corridor_side, corridor_w, seed, …) are not silently dropped.
    merged = {**req.current_spec, **updated}
    image_b64 = _render(merged)
    return {"spec": merged, "reply": reply, "image_b64": image_b64}
