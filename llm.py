"""
LLM wrapper integration — POST to Gemini API wrapper at http://127.0.0.1:8000.
Phase 1: dining chat modification.
Phase 2: onboarding → initial dwelling spec.
"""
import json
import time
import requests
from typing import Optional

WRAPPER_URL          = "http://127.0.0.1:8000"
RAG_COLLECTION       = "dining_vocabulary_RAG"
ONBOARDING_RAG       = "onboarding_RAG"
MODEL                = "gemma-4-31b-it" 

DINING_SCHEMA = {
    "type": "object",
    "properties": {
        "dining_style":   {"type": "string",  "enum": ["compact", "spacious"]},
        "num_chairs":     {"type": "integer", "minimum": 1, "maximum": 2},
        "h":              {"type": "integer", "minimum": 7, "maximum": 11},
        "d":              {"type": "integer", "minimum": 2, "maximum": 9},
        "roof_style":     {"type": "string",  "enum": ["any", "plain", "divided", "pitched"]},
        "preferred_tags": {"type": "array",   "items": {"type": "string"}},
    },
    "required": ["dining_style", "num_chairs", "h", "d", "roof_style", "preferred_tags"],
}

_CONTEXT = (
    "You are the configurator for Nomadic Engine, a deployable off-grid dwelling system. "
    "Translate the user's natural language into dining section parameters. "
    "Always output all eight required fields.\n\n"

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

    "WORKED EXAMPLES:\n"
    "  'higher table'    → preferred_tags: ['tall_table'],   h UNCHANGED, dining_style UNCHANGED\n"
    "  'higher chairs'   → preferred_tags: ['tall_chairs'],  h UNCHANGED, dining_style UNCHANGED\n"
    "  'more spacious'   → dining_style: 'spacious',         preferred_tags UNCHANGED\n"
    "  'higher ceiling'  → h increases by 2,                 preferred_tags UNCHANGED\n\n"

    "RULE: Only change num_chairs if the user explicitly mentions seating sides, dining alone, or face-to-face.\n\n"
    f"Output must be valid JSON matching this schema: {json.dumps(DINING_SCHEMA)}"
)


_CORRIDOR_KW: dict = {
    "right":   ["add a corridor", "add corridor", "i want a corridor", "add walkway", "add a walkway"],
    "left":    ["corridor on left", "left corridor", "add corridor on left"],
    "none":    ["remove corridor", "no corridor", "remove the corridor", "take away corridor",
                "without corridor"],
    "wide":    ["wider corridor", "bigger corridor", "more spacious corridor",
                "more circulation", "wider walkway"],
    "narrow":  ["narrow corridor", "compact corridor", "tight corridor", "smaller corridor"],
}
# Words that signal the user also explicitly wants a section-width change alongside the corridor
_SECTION_WIDTH_KW = ["spacious", "compact", "wider section", "open layout", "tighter section",
                     "narrower section", "make it spacious", "make it compact"]


def _apply_corridor_changes(msg: str, current: dict, params: dict) -> dict:
    """Detect corridor keywords and apply changes using current spec as base.
    Locks dining_style and preferred_tags to current when ONLY a corridor change was requested,
    preventing the LLM from spuriously widening the section or changing furniture."""
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
        # Start from current spec — only the corridor fields change.
        # Selectively allow dining_style to change if the user also asked for it.
        result = dict(current)
        result["corridor_side"] = side
        result["corridor_w"]    = cw
        if any(kw in msg_l for kw in _SECTION_WIDTH_KW):
            result["dining_style"] = params.get("dining_style", current.get("dining_style"))
        return result
    return params


_SHELF_TAGS = {"more_shelves", "wide_shelves"}
_ROOF_KW: dict = {
    "more_shelves": ["more shelves", "lots of shelves", "more storage overhead",
                     "more divisions", "many shelves", "extra shelves"],
    "wide_shelves": ["wide shelves", "big shelves", "deep shelves",
                     "generous shelving", "wider shelves"],
    "divided":      ["shelves above", "storage overhead", "divided ceiling",
                     "divided roof", "articulated top"],
    "pitched":      ["angled roof", "pitched roof", "tent-like", "lean-to",
                     "slanted ceiling", "slanted roof"],
    "plain":        ["plain ceiling", "clean top", "simple roof",
                     "flat ceiling", "unfussy overhead"],
    "any":          ["no preference", "any roof", "whatever roof"],
}


def _apply_roof_changes(msg: str, current: dict, params: dict) -> dict:
    """Detect roof/shelf keywords and force correct roof_style and shelf tags.
    Runs after _apply_furniture_height so preferred_tags already has correct furniture tags."""
    msg_l = msg.lower()
    roof  = params.get("roof_style", current.get("roof_style", "any"))
    tags  = [t for t in params.get("preferred_tags", []) if t not in _SHELF_TAGS]
    changed = False

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

    if changed:
        return {**params, "roof_style": roof, "preferred_tags": tags}
    return params


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

# Maps compound tag → (chair component, table component)
_COMPOUND_EXPAND = {
    "tall_furniture": ("tall_chairs", "tall_table"),
    "low_furniture":  ("low_chairs",  "low_table"),
}


def _apply_furniture_height(msg: str, current: dict, params: dict) -> dict:
    """Post-process: detect furniture-height keywords and force correct independent tags.
    Preserves unchanged furniture tags from current spec so unrelated elements stay stable.
    Restores h to current value so the LLM cannot accidentally change ceiling height."""
    msg_l = msg.lower()

    matched: dict[str, str] = {}  # tag_name → category (chairs/table/both)
    for tag, keywords in _KW.items():
        if any(kw in msg_l for kw in keywords):
            matched[tag] = tag

    if not matched:
        return params

    changing_chairs = any(t in _CHAIR_HEIGHT_TAGS | _COMPOUND_HEIGHT_TAGS for t in matched)
    changing_table  = any(t in _TABLE_HEIGHT_TAGS  | _COMPOUND_HEIGHT_TAGS for t in matched)

    # Build base from CURRENT spec tags (not LLM output) — stable foundation.
    # Expand compound tags (tall_furniture) into components when only one side changes.
    base: list[str] = []
    for t in current.get("preferred_tags", []):
        if t in _ALL_HEIGHT_TAGS:
            if t in _COMPOUND_HEIGHT_TAGS:
                chair_comp, table_comp = _COMPOUND_EXPAND[t]
                if not changing_chairs:
                    base.append(chair_comp)   # preserve chair component
                if not changing_table:
                    base.append(table_comp)   # preserve table component
            elif t in _CHAIR_HEIGHT_TAGS and not changing_chairs:
                base.append(t)               # preserve existing chair tag
            elif t in _TABLE_HEIGHT_TAGS and not changing_table:
                base.append(t)               # preserve existing table tag
            # else: this category is being replaced — drop it
        else:
            base.append(t)                   # non-height tags always preserved

    return {
        **params,
        "preferred_tags": base + list(matched),
        "h": current.get("h", params.get("h")),
    }


def chat_modify_dining(current_spec: dict, user_message: str) -> Optional[dict]:
    """Send user_message to the wrapper and return updated dining params, or None on failure."""
    context = _CONTEXT + f"\n\nCurrent parameters: {json.dumps(current_spec)}"

    payload = {
        "model":          MODEL,
        "prompt":         user_message,
        "context":        context,
        "use_rag":        True,
        "rag_collection": RAG_COLLECTION,
        "rag_top_k":      4,
        "temperature":    0.3,
        "metadata":       DINING_SCHEMA,
    }

    for attempt in range(3):
        try:
            resp = requests.post(f"{WRAPPER_URL}/completion", json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            result = data["json_data"] if data.get("json_data") else json.loads(data["text"])
            result = _apply_corridor_changes(user_message, current_spec, result)
            result = _apply_furniture_height(user_message, current_spec, result)
            return _apply_roof_changes(user_message, current_spec, result)
        except Exception:
            if attempt < 2:
                time.sleep(2)
    return None


# ── Onboarding ────────────────────────────────────────────────────────────────


_ONBOARDING_DINING_CONTEXT = (
    "You are the configurator for Nomadic Engine, a deployable off-grid dwelling system. "
    "Your job is to translate 5 onboarding answers + a site's climate data into dining section parameters. "
    "Use the RAG collection to understand how occupants, duration, purpose, priority, and scale "
    "map to dining parameters. "
    "Always output all six required fields: dining_style, num_chairs, h, d, roof_style, preferred_tags. "
    f"Output must be valid JSON matching this schema: {json.dumps(DINING_SCHEMA)}"
)


def onboarding_to_spec(site: dict, answers: dict) -> Optional[dict]:
    """Convert site climate + 5 onboarding answers into dining section params."""
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
        "Based on these answers, generate the dining section parameters for this nomad."
    )

    payload = {
        "model":          MODEL,
        "prompt":         prompt,
        "context":        _ONBOARDING_DINING_CONTEXT,
        "use_rag":        True,
        "rag_collection": ONBOARDING_RAG,
        "rag_top_k":      3,
        "temperature":    0.3,
        "metadata":       DINING_SCHEMA,
    }

    for attempt in range(3):
        try:
            resp = requests.post(f"{WRAPPER_URL}/completion", json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            if data.get("json_data"):
                return data["json_data"]
            return json.loads(data["text"])
        except Exception:
            if attempt < 2:
                time.sleep(2)
    return None
