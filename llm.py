"""
Multi-provider LLM integration — Google (Gemini/Gemma), OpenAI (GPT), Anthropic (Claude).
No wrapper server required.
"""
import json
import os
import time
from pathlib import Path
MODEL    = "gemma-4-31b-it"
_RAG_DIR = Path(__file__).parent / "rag"

# ── Provider detection ─────────────────────────────────────────────────────────

def provider_for(model: str) -> str:
    """Return 'google', 'openai', or 'anthropic' based on model name."""
    if model.startswith(("gpt-", "o1-", "o3-", "o4-")):
        return "openai"
    if model.startswith("claude-"):
        return "anthropic"
    return "google"

# ── API keys ───────────────────────────────────────────────────────────────────

_BASE = Path(__file__).parent
_KEY_FILES = {
    "google":    _BASE / ".gemini_key",
    "openai":    _BASE / ".openai_key",
    "anthropic": _BASE / ".anthropic_key",
}
_ENV_VARS = {
    "google":    "GEMINI_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
_keys: dict[str, str] = {}


def configure(provider: str, api_key: str, save: bool = False) -> None:
    _keys[provider] = api_key.strip()
    if save:
        _KEY_FILES[provider].write_text(api_key.strip(), encoding="utf-8")


def is_configured(provider: str | None = None) -> bool:
    p = provider or provider_for(MODEL)
    return bool(_key_for(p, raise_if_missing=False))


def _key_for(provider: str, raise_if_missing: bool = True) -> str:
    if provider in _keys and _keys[provider]:
        return _keys[provider]
    key = os.environ.get(_ENV_VARS[provider], "")
    if not key and _KEY_FILES[provider].exists():
        key = _KEY_FILES[provider].read_text(encoding="utf-8").strip()
    if key:
        _keys[provider] = key
        return key
    if raise_if_missing:
        raise RuntimeError(f"No API key for {provider} — add it in the sidebar.")
    return ""


# ── RAG ────────────────────────────────────────────────────────────────────────

def _load_rag(filename: str) -> str:
    p = _RAG_DIR / filename
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ── Schema ─────────────────────────────────────────────────────────────────────

DINING_SCHEMA = {
    "type": "object",
    "properties": {
        "action":         {"type": "string",  "enum": ["update", "clarify"]},
        "dining_style":   {"type": "string",  "enum": ["compact", "spacious"]},
        "num_chairs":     {"type": "integer", "minimum": 1, "maximum": 2},
        "h":              {"type": "integer", "minimum": 7, "maximum": 8},
        "d":              {"type": "integer", "minimum": 2, "maximum": 9},
        "roof_style":     {"type": "string",  "enum": ["any", "plain", "divided", "pitched", "slanted", "divided_slanted"]},
        "preferred_tags": {"type": "array",   "items": {"type": "string"}},
        "reply":          {"type": "string"},
    },
    "required": ["action", "dining_style", "num_chairs", "h", "d", "roof_style", "preferred_tags", "reply"],
}

# ── System prompts ─────────────────────────────────────────────────────────────

_DINING_SYSTEM = (
    "You are the configurator for Nomadic Engine, a deployable off-grid dwelling system. "
    "You are having an ongoing design conversation with a prospective dweller. "
    "You have access to the full conversation history — use it to understand their intent, "
    "refer back to earlier preferences, and build on what has already been decided.\n\n"

    "THREE INDEPENDENT PARAMETERS — only change what the user asks about:\n"
    "  dining_style   = WIDTH OF THE TABLE/SECTION ('compact'=narrow, 'spacious'=wide).\n"
    "  h              = HEIGHT OF THE ROOM/CEILING (7–11). NOT furniture.\n"
    "  preferred_tags = HEIGHT/STYLE OF FURNITURE only.\n\n"

    "SECTION WIDTH rules (only change dining_style):\n"
    "  'more spacious', 'wider section', 'open layout', 'compact section', 'tighter' "
    "→ change dining_style. preferred_tags UNCHANGED.\n\n"

    "FURNITURE HEIGHT rules (chairs and table are INDEPENDENT — only change preferred_tags):\n"
    "  'higher chairs', 'bar height', 'taller seating' → add 'tall_chairs' to preferred_tags. h UNCHANGED.\n"
    "  'lower chairs', 'floor seating', 'Japanese-style' → add 'low_chairs' to preferred_tags. h UNCHANGED.\n"
    "  'higher table', 'elevated table', 'bar table' → add 'tall_table' to preferred_tags. h UNCHANGED.\n"
    "  'lower table', 'low table' → add 'low_table' to preferred_tags. h UNCHANGED.\n"
    "  'higher furniture', 'tall furniture' (both) → add 'tall_furniture' to preferred_tags. h UNCHANGED.\n\n"

    "CEILING HEIGHT rules (only change h):\n"
    "  'higher ceiling', 'taller room', 'more headroom', 'airy', 'dramatic space' "
    "→ increase h. preferred_tags UNCHANGED.\n\n"

    "SECTION DEPTH rules (only change d):\n"
    "  'guests', 'entertaining', 'hosting', 'visitors', 'have people over' "
    "→ double current d (e.g. d=3 → d=6). dining_style and preferred_tags UNCHANGED.\n\n"

    "WORKED EXAMPLES:\n"
    "  'higher table'              → preferred_tags: ['tall_table'],   h UNCHANGED, dining_style UNCHANGED\n"
    "  'higher chairs'             → preferred_tags: ['tall_chairs'],  h UNCHANGED, dining_style UNCHANGED\n"
    "  'more spacious'             → dining_style: 'spacious',         preferred_tags UNCHANGED\n"
    "  'higher ceiling'            → h increases by 2,                 preferred_tags UNCHANGED\n"
    "  'might have guests'         → d doubles (e.g. 3→6),             everything else UNCHANGED\n"
    "  'we sometimes entertain'    → d doubles,                        everything else UNCHANGED\n\n"

    "RULE: Only change num_chairs if the user explicitly mentions seating sides, dining alone, or face-to-face.\n\n"

    "ACTION field rules:\n"
    "  Set action='update' when the intent is clear enough to act — make the change.\n"
    "  Set action='clarify' when the request is genuinely ambiguous between two different parameters "
    "(e.g. 'make it bigger' could mean ceiling height or table width). "
    "Ask ONE short question in the reply field. Do not change any parameters when clarifying. "
    "Default to 'update' — only clarify when truly necessary.\n\n"

    "REPLY field: Write 1–2 sentences in the voice of a calm, direct architect. "
    "You may reference earlier turns ('as you mentioned before…', 'building on your preference for…'). "
    "Do not mention parameter field names. "
    "If action='clarify', the reply IS the question.\n\n"

    f"Output must be valid JSON matching this schema: {json.dumps(DINING_SCHEMA)}\n\n"
    "--- VOCABULARY REFERENCE ---\n"
)

_ONBOARDING_SYSTEM = (
    "You are the configurator for Nomadic Engine, a deployable off-grid dwelling system. "
    "Translate 5 onboarding answers + site climate data into dining section parameters. "
    "Always output all required fields: dining_style, num_chairs, h, d, roof_style, preferred_tags.\n"
    "The reply field should be left as an empty string for onboarding.\n\n"
    f"Output must be valid JSON matching this schema: {json.dumps(DINING_SCHEMA)}\n\n"
    "--- ONBOARDING VOCABULARY REFERENCE ---\n"
)

# ── Corridor / roof / furniture post-processing (unchanged logic) ──────────────

_CORRIDOR_KW: dict = {
    "right":   ["add a corridor", "add corridor", "i want a corridor", "add walkway", "add a walkway"],
    "left":    ["corridor on left", "left corridor", "add corridor on left"],
    "none":    ["remove corridor", "no corridor", "remove the corridor", "take away corridor",
                "without corridor"],
    "wide":    ["wider corridor", "bigger corridor", "more spacious corridor",
                "more circulation", "wider walkway"],
    "narrow":  ["narrow corridor", "compact corridor", "tight corridor", "smaller corridor"],
}
_SECTION_WIDTH_KW = ["spacious", "compact", "wider section", "open layout", "tighter section",
                     "narrower section", "make it spacious", "make it compact"]


def _apply_corridor_changes(msg: str, current: dict, params: dict) -> dict:
    """Detect corridor keywords and apply changes using current spec as base."""
    msg_l = msg.lower()
    side = current.get("corridor_side", "none")
    cw   = current.get("corridor_w",   2)
    changed = False

    if any(kw in msg_l for kw in _CORRIDOR_KW["left"]):
        side, changed = "left",  True
    elif any(kw in msg_l for kw in _CORRIDOR_KW["right"]):
        side, changed = "right", True
    elif any(kw in msg_l for kw in _CORRIDOR_KW["none"]):
        side, changed = "none",  True

    if any(kw in msg_l for kw in _CORRIDOR_KW["wide"]):
        cw, changed = 4, True
    elif any(kw in msg_l for kw in _CORRIDOR_KW["narrow"]):
        cw, changed = 2, True

    if changed:
        result = dict(current)
        result["corridor_side"] = side
        result["corridor_w"]    = cw
        # Corridor added to a slanted section → divided_slanted
        if side in ("left", "right") and current.get("corridor_side", "none") == "none":
            if current.get("roof_style", "any") == "slanted":
                result["roof_style"] = "divided_slanted"
        # Corridor removed → revert divided_slanted back to plain slanted
        elif side == "none" and current.get("roof_style") == "divided_slanted":
            result["roof_style"] = "slanted"
        if any(kw in msg_l for kw in _SECTION_WIDTH_KW):
            result["dining_style"] = params.get("dining_style", current.get("dining_style"))
        return result
    return params


_SHELF_TAGS = {"more_shelves", "wide_shelves"}
_ROOF_KW: dict = {
    "more_shelves": ["shelves", "add shelves", "want shelves", "i want shelf",
                     "more shelves", "lots of shelves", "more storage overhead",
                     "more divisions", "many shelves", "extra shelves", "some shelves"],
    "wide_shelves": ["wide shelves", "big shelves", "deep shelves",
                     "generous shelving", "wider shelves"],
    "divided":      ["shelves above", "storage overhead", "divided ceiling",
                     "divided roof", "articulated top"],
    "pitched":      ["angled roof", "pitched roof", "tent-like", "lean-to",
                     "slanted ceiling", "slanted roof"],
    "plain":        ["plain ceiling", "clean top", "simple roof", "plain roof",
                     "flat ceiling", "unfussy overhead", "roof to plain", "roof plain"],
    "any":          ["no preference", "any roof", "whatever roof"],
}


def _apply_roof_changes(msg: str, current: dict, params: dict) -> dict:
    msg_l = msg.lower()
    tags  = [t for t in params.get("preferred_tags", []) if t not in _SHELF_TAGS]
    changed = False
    roof = current.get("roof_style", "any")  # start from current, not LLM output

    if any(kw in msg_l for kw in _ROOF_KW["more_shelves"]):
        roof, changed = "divided", True
        tags.append("more_shelves")
    elif any(kw in msg_l for kw in _ROOF_KW["wide_shelves"]):
        roof, changed = "divided", True
        tags.append("wide_shelves")
    elif any(kw in msg_l for kw in _ROOF_KW["divided"]):
        roof, changed = "divided", True
    elif any(kw in msg_l for kw in _ROOF_KW["pitched"]):
        roof, changed = "pitched", True
    elif any(kw in msg_l for kw in _ROOF_KW["plain"]):
        roof, changed = "plain", True
    elif any(kw in msg_l for kw in _ROOF_KW["any"]):
        roof, changed = "any", True

    if not changed:
        # No keyword matched — pass through the LLM's value; main locking handles drift.
        return params
    return {**params, "roof_style": roof, "preferred_tags": tags}


_CHAIR_HEIGHT_TAGS    = {"tall_chairs", "low_chairs"}
_TABLE_HEIGHT_TAGS    = {"tall_table",  "low_table"}
_COMPOUND_HEIGHT_TAGS = {"tall_furniture", "low_furniture"}
_ALL_HEIGHT_TAGS      = _CHAIR_HEIGHT_TAGS | _TABLE_HEIGHT_TAGS | _COMPOUND_HEIGHT_TAGS | {"h2", "h3"}

_KW: dict = {
    "tall_chairs":    ["higher chair", "taller chair", "tall chair", "bar height chair",
                       "higher seating", "taller seating", "bar stool", "high stool"],
    "low_chairs":     ["lower chair", "low chair", "floor seating", "floor-level",
                       "japanese", "low seating", "lower seating"],
    "tall_table":     ["higher table", "taller table", "tall table", "elevated table",
                       "bar table", "stand-up dining", "bar height table", "high table"],
    "low_table":      ["lower table", "low table", "sunken table"],
    "tall_furniture": ["tall furniture", "higher furniture", "taller furniture"],
    "low_furniture":  ["low furniture", "lower furniture"],
}
_COMPOUND_EXPAND = {
    "tall_furniture": ("tall_chairs", "tall_table"),
    "low_furniture":  ("low_chairs",  "low_table"),
}


def _apply_furniture_height(msg: str, current: dict, params: dict) -> dict:
    msg_l   = msg.lower()
    matched: dict[str, str] = {}
    for tag, keywords in _KW.items():
        if any(kw in msg_l for kw in keywords):
            matched[tag] = tag

    if not matched:
        return params

    changing_chairs = any(t in _CHAIR_HEIGHT_TAGS | _COMPOUND_HEIGHT_TAGS for t in matched)
    changing_table  = any(t in _TABLE_HEIGHT_TAGS  | _COMPOUND_HEIGHT_TAGS for t in matched)

    base: list[str] = []
    for t in current.get("preferred_tags", []):
        if t in _ALL_HEIGHT_TAGS:
            if t in _COMPOUND_HEIGHT_TAGS:
                chair_comp, table_comp = _COMPOUND_EXPAND[t]
                if not changing_chairs:
                    base.append(chair_comp)
                if not changing_table:
                    base.append(table_comp)
            elif t in _CHAIR_HEIGHT_TAGS and not changing_chairs:
                base.append(t)
            elif t in _TABLE_HEIGHT_TAGS and not changing_table:
                base.append(t)
        else:
            base.append(t)

    return {
        **params,
        "preferred_tags": base + list(matched),
        "h": current.get("h", params.get("h")),
    }


# ── Multi-provider call ────────────────────────────────────────────────────────

def _generate(system: str, prompt: str,
              history: list[dict] | None = None,
              temperature: float = 0.3,
              model: str | None = None) -> dict:
    """Call the active model with optional conversation history. Returns parsed JSON.

    `model` overrides the module-level MODEL for this call only (used by judge_section
    to run the same rubric against a second model for a cross-model agreement check).
    """
    _model   = model or MODEL
    provider = provider_for(_model)
    key      = _key_for(provider)
    history  = history or []

    if provider == "google":
        from google import genai
        from google.genai import types as gtypes
        client   = genai.Client(api_key=key)
        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(gtypes.Content(role=role, parts=[gtypes.Part(text=msg["content"])]))
        contents.append(gtypes.Content(role="user", parts=[gtypes.Part(text=prompt)]))
        # Gemma models don't support response_mime_type — omit it and parse manually.
        _is_gemma = _model.startswith("gemma")
        cfg = gtypes.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            **({} if _is_gemma else {"response_mime_type": "application/json"}),
        )
        response = client.models.generate_content(model=_model, contents=contents, config=cfg)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    if provider == "openai":
        from openai import OpenAI
        client   = OpenAI(api_key=key)
        messages = [{"role": "system", "content": system}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=_model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(response.choices[0].message.content)

    if provider == "anthropic":
        import anthropic
        client   = anthropic.Anthropic(api_key=key)
        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        response = client.messages.create(
            model=_model,
            max_tokens=1024,
            system=system + "\n\nYou must respond with valid JSON only, no other text.",
            messages=messages,
            temperature=temperature,
        )
        return json.loads(response.content[0].text)

    raise RuntimeError(f"Unknown provider for model: {_model}")


# ── Public API ─────────────────────────────────────────────────────────────────

_HISTORY_LIMIT = 20  # max messages passed as context (10 exchanges)


def chat_modify_dining(
    current_spec: dict,
    user_message: str,
    history: list[dict] | None = None,
) -> tuple[dict, str] | tuple[None, str]:
    """Returns (updated_params, reply_text) on update,
    (None, reply_text) on clarify question or error."""
    system     = _DINING_SYSTEM + _load_rag("dining_vocabulary_RAG.md")
    prompt     = f"Current parameters: {json.dumps(current_spec)}\n\nUser: {user_message}"
    clean_hist = [m for m in (history or []) if m.get("content") not in ("", "Generating…")]
    hist       = clean_hist[-_HISTORY_LIMIT:]
    last_error = ""

    _msg_l = user_message.lower()

    _seating_kw  = ["chair", "seat", "seating", "one person", "solo", "alone", "face-to-face",
                    "both sides", "two people", "single side"]
    _depth_kw    = ["deeper", "shallower", "depth", "longer table", "shorter table",
                    "longer section", "shorter section", "more depth", "less depth",
                    "extend", "longer dining", "make it longer", "make it shorter",
                    "guest", "guests", "entertaining", "visitors", "hosting", "company",
                    "people over", "have people", "social"]
    _ceiling_kw  = ["higher ceiling", "taller room", "more headroom", "lower ceiling",
                    "ceiling height", "room height", "raise the ceiling", "airy",
                    "dramatic space", "tall room", "short room", "change the height"]
    _style_kw    = ["spacious", "compact", "wider section", "narrower section",
                    "open layout", "tighter", "wider table", "bigger section",
                    "smaller section", "make it wider", "make it narrower"]
    _furniture_kw = [kw for kws in _KW.values() for kw in kws]
    _all_roof_kw  = [kw for kws in _ROOF_KW.values() for kw in kws]

    for attempt in range(3):
        try:
            result = _generate(system, prompt, history=hist)
            action = result.pop("action", "update")
            reply  = result.pop("reply", "Done.")
            if action == "clarify":
                return None, reply
            result = _apply_corridor_changes(user_message, current_spec, result)
            result = _apply_furniture_height(user_message, current_spec, result)
            result = _apply_roof_changes(user_message, current_spec, result)
            # Lock every field the user's message doesn't explicitly address.
            _roof_kw = _all_roof_kw + ["roof", "ceiling type", "shelf type"]
            if not any(kw in _msg_l for kw in _seating_kw):
                result["num_chairs"] = current_spec.get("num_chairs", 2)
            if not any(kw in _msg_l for kw in _depth_kw):
                result["d"] = current_spec.get("d", 3)
            if not any(kw in _msg_l for kw in _ceiling_kw):
                result["h"] = current_spec.get("h", 9)
            if not any(kw in _msg_l for kw in _style_kw):
                result["dining_style"] = current_spec.get("dining_style", "compact")
            if not any(kw in _msg_l for kw in _roof_kw):
                result["roof_style"] = current_spec.get("roof_style", "any")
            if not any(kw in _msg_l for kw in _furniture_kw + _all_roof_kw):
                result["preferred_tags"] = current_spec.get("preferred_tags", [])
            return result, reply
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                time.sleep(2)
    return None, f"⚠️ {last_error}"


def onboarding_to_spec(site: dict, answers: dict) -> tuple[dict | None, str]:
    """Returns (params, error_message). params is None on failure."""
    system = _ONBOARDING_SYSTEM + _load_rag("onboarding_RAG.md")
    prompt = (
        f"Site: {site['name']} ({site['location']}). "
        f"Temperature: {site['temperature']}. Precipitation: {site['precipitation']}. "
        f"Climate zone: {site['climate_zone']}.\n\n"
        f"Onboarding answers:\n"
        f"- Occupants: {answers['occupants']}\n"
        f"- Duration: {answers['duration']}\n"
        f"- Purpose: {answers['purpose']}\n"
        f"- Priority: {answers['priority']}\n"
        f"- Scale: {answers['scale']}\n\n"
        "Generate the dining section parameters for this nomad."
    )
    last_error = ""

    for attempt in range(3):
        try:
            result = _generate(system, prompt, temperature=0.2)
            result.pop("reply", None)
            return result, ""
        except Exception as e:
            last_error = str(e)
            if attempt < 2:
                time.sleep(2)
    return None, last_error


# ── Section judge (spatial-quality selection — research proof of concept) ──────
#
# The solver already produces several valid section candidates by varying its seed,
# with no way to tell them apart on spatial quality. judge_section scores one
# candidate's enclosure/openness character, grounded in geometric facts computed
# from the solver's own placement data (reach distance, headroom) — the LLM is not
# asked to invent measurements, only to interpret them for a translucent-fabric
# section rather than an opaque-wall floor plan. Candidate ranking and per-user
# weighting happen in plain Python (see judge_demo.py); this function only scores
# one candidate at a time so the same rubric can be re-run against a second model
# for a cross-model agreement check.

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "enclosure_score": {"type": "number", "minimum": 0, "maximum": 10},
        "openness_score":  {"type": "number", "minimum": 0, "maximum": 10},
        "reasoning":       {"type": "string"},
    },
    "required": ["enclosure_score", "openness_score", "reasoning"],
}

_JUDGE_SYSTEM = (
    "You are judging one candidate layout of a section for Nomadic Engine, a deployable off-grid "
    "dwelling built from structural ribs and a translucent fabric membrane — not solid opaque "
    "walls. You are given computed geometric facts about the vertical stack the occupant deals "
    "with at this spot: how high they must reach for the highest comfortably-usable storage "
    "(reach_height), and how much additional storage or roofline sits above that comfortable "
    "reach (overhead_height).\n\n"
    "Score two things on a 0-10 scale, describing the space as built (not for any specific user):\n"
    "  enclosure_score = how enclosed/heavy the overhead presence feels at this spot — driven by "
    "overhead_height RELATIVE TO H: the larger that fraction, the more storage is stacked close "
    "overhead, the HIGHER this score should be. A small overhead_height relative to H means most "
    "of the height is open above the occupant, so this score should be LOW.\n"
    "  openness_score = how much clear vertical space there is above the occupant before hitting "
    "any storage — driven by reach_height RELATIVE TO H: the larger that fraction, the more open "
    "height there is, the HIGHER this score should be.\n\n"
    "Ground every score in the computed facts given — do not invent details not in the data. "
    "Because the envelope is translucent fabric rather than solid walls, reason about proximity and "
    "enclosure, not opaque occlusion.\n\n"
    f"Output valid JSON matching this schema: {json.dumps(JUDGE_SCHEMA)}\n"
)


def judge_section(facts: dict, model: str | None = None) -> dict | None:
    """Score one candidate section's spatial character. Returns None on failure.

    `facts` describes computed placement geometry, e.g.
    {"H": 9, "headroom_at_seat": 2.0, "shelf_reach": 1.5}.
    `model` overrides the default model for this call (for cross-model comparison).
    """
    prompt = f"Computed facts for this candidate: {json.dumps(facts)}"
    for attempt in range(3):
        try:
            return _generate(_JUDGE_SYSTEM, prompt, temperature=0.2, model=model)
        except Exception:
            if attempt < 2:
                time.sleep(2)
    return None
