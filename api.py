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
from viewer3d import plot_section_3d, plot_dwelling_3d
from export import export_section_3d_json

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
    # Roof locked to pitched — ignore whatever the LLM returned.
    roof_style = "pitched"
    merged["roof_style"] = roof_style
    # Store dining W at dwelling level so living can match it.
    dining_style = dining_spec.get("dining_style", "compact")
    merged["W"] = _dining_W(dining_style, num_chairs, corridor_side, corridor_w)
    # Propagate roof_style to every function so section renders are consistent.
    for fn in merged.get("functions", []):
        fn["roof_style"] = roof_style
        if fn.get("type") == "dining":
            for key in ("dining_style", "num_chairs", "d", "preferred_tags", "seed"):
                if key in dining_spec:
                    fn[key] = dining_spec[key]
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


def _render_section(spec: dict, section: str = "dining", view: str = "2D",
                    highlight: str = "") -> str | None:
    """Solve + render any section (or the full dwelling) in 2D or 3D."""
    if section == "dwelling":
        dw_spec = spec.get("dwelling_spec") or _merge_dining_into_dwelling(spec)
        if view == "plan":
            return _render_plan(dw_spec)
        return _render_dwelling(dw_spec, highlight_section=highlight or None)
    H            = spec.get("h",             7)
    D            = spec.get("d",             3)
    seed         = spec.get("seed",          42)
    roof_style   = "pitched"  # locked for demo — all sections use pitched v1
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
        placed = solve3d(
            W, H, D, seed,
            corridor=solver_corr,
            corridor_w=corridor_w,
            dining_style=dining_style,
            roof_style=roof_style,
            section=section,
            preferred_tags=preferred_tags if section == "dining" else None,
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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/render")
def render(req: RenderRequest):
    image_b64 = _render_section(req.spec, section=req.section, view=req.view)
    return {"image_b64": image_b64}


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
