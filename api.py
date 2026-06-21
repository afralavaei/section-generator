"""
FastAPI backend for the Nomadic Engine configurator.

Endpoints:
  POST /onboarding  — translate 5 onboarding answers + site into an initial spec + render
  POST /chat        — modify dining spec via natural language + return reply + updated render
"""
import base64
import io
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before any pyplot import

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm import chat_modify_dining, onboarding_to_spec
from solver import solve
from drawing import plot_section

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dining_W(dining_style: str, num_chairs: int, corridor_side: str, corridor_w: int) -> int:
    inner = (6 if dining_style == "compact" else 8) if num_chairs == 2 \
            else (4 if dining_style == "compact" else 5)
    return inner + (corridor_w if corridor_side != "none" else 0)


def _render(spec: dict) -> str | None:
    """Solve + render the dining section described by spec. Returns base64 PNG or None."""
    dining_style  = spec.get("dining_style",  "compact")
    num_chairs    = spec.get("num_chairs",    2)
    corridor_side = spec.get("corridor_side", "none")
    corridor_w    = spec.get("corridor_w",    2)
    H             = spec.get("h",             7)
    seed          = spec.get("seed",          42)
    roof_style    = spec.get("roof_style",    "any")
    preferred_tags = spec.get("preferred_tags", [])

    W = _dining_W(dining_style, num_chairs, corridor_side, corridor_w)

    placed = solve(
        W, H, seed,
        corridor=corridor_side,
        corridor_w=corridor_w,
        dining_style=dining_style,
        roof_style=roof_style,
        section="dining",
        preferred_tags=preferred_tags,
    )
    if placed is None:
        return None

    import matplotlib.pyplot as plt
    fig = plot_section(placed, W, H)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ── Request models ────────────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    site: dict
    answers: dict  # keys: occupants, duration, purpose, priority, scale


class ChatRequest(BaseModel):
    current_spec: dict
    message: str


class RenderRequest(BaseModel):
    spec: dict
    history: list[dict] = []  # list of {role, content}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/render")
def render(req: RenderRequest):
    """Solve + render the current spec without calling the LLM. Used for initial page load."""
    image_b64 = _render(req.spec)
    return {"image_b64": image_b64}


@app.post("/onboarding")
def onboard(req: OnboardingRequest):
    params, err = onboarding_to_spec(req.site, req.answers)
    if params is None:
        return {"error": err, "spec": None, "image_b64": None, "reply": ""}

    params.setdefault("corridor_side", "none")
    params.setdefault("corridor_w",    2)
    params.setdefault("seed",          42)

    image_b64 = _render(params)
    return {"spec": params, "image_b64": image_b64, "reply": ""}


@app.post("/chat")
def chat(req: ChatRequest):
    updated, reply = chat_modify_dining(req.current_spec, req.message, req.history)

    if updated is None:
        # clarify or error — return current spec unchanged
        return {"spec": req.current_spec, "reply": reply, "image_b64": None}

    image_b64 = _render(updated)
    return {"spec": updated, "reply": reply, "image_b64": image_b64}
