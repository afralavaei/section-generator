"""
Multi-criteria weighted scorecard for ranking dwelling section candidates.

See .claude/skills/dwelling-scorecard/SKILL.md for the process this follows.
Standalone module — imports existing solve()/MODULES/_seat_y() read-only.
Does not modify solve(), modules.py, app.py, api.py, or the React app.
"""
from typing import Callable, Optional

from modules import MODULES
import scorecard_constants as C

# A criterion is a plain dict: {id, label, weight, score_fn}.
# score_fn(placed, context) -> float in [0, 10], or None if this criterion
# doesn't apply to this candidate (e.g. no chair present) — None candidates
# are dropped from ranking for that run rather than penalized with a 0.
Criterion = dict


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def find_zone(placed: list[dict], zone_name: str) -> Optional[dict]:
    for p in placed:
        if MODULES[p["module_id"]]["zone"] == zone_name:
            return p
    return None


def seat_height_fit(placed: list[dict], context: dict) -> Optional[float]:
    """Score how well this candidate's chair seat height suits the stated user height.

    Seat height is estimated per chair style class (the "h2"/"h3" tags), not
    read from the module's drawing geometry — the drawings are stylized 2D
    schematics on a coarse grid, not precise physical blueprints, so raw
    coordinates aren't a reliable source for real-world centimeters.
    """
    chair = find_zone(placed, "chair_left") or find_zone(placed, "chair_right")
    if chair is None:
        return None
    mod = MODULES[chair["module_id"]]
    style_class = next((t for t in mod.get("tags", []) if t in C.SEAT_HEIGHT_BY_CLASS_CM), None)
    if style_class is None:
        return None
    actual_cm = C.SEAT_HEIGHT_BY_CLASS_CM[style_class]
    ideal_cm = C.SEAT_HEIGHT_RATIO * context["user_height_cm"]
    deviation = abs(actual_cm - ideal_cm)
    return _clip(10.0 - deviation / C.SEAT_HEIGHT_TOLERANCE_CM * 10.0, 0.0, 10.0)


def table_height_fit(placed: list[dict], context: dict) -> Optional[float]:
    """Score how well this candidate's table height suits the stated user height.

    Same approach as seat_height_fit: estimated per style class, not read
    from the drawing geometry (unreliable for the same reason).
    """
    table = find_zone(placed, "table")
    if table is None:
        return None
    mod = MODULES[table["module_id"]]
    style_class = next((t for t in mod.get("tags", []) if t in C.TABLE_HEIGHT_BY_CLASS_CM), None)
    if style_class is None:
        return None
    actual_cm = C.TABLE_HEIGHT_BY_CLASS_CM[style_class]
    ideal_cm = C.TABLE_HEIGHT_RATIO * context["user_height_cm"]
    deviation = abs(actual_cm - ideal_cm)
    return _clip(10.0 - deviation / C.TABLE_HEIGHT_TOLERANCE_CM * 10.0, 0.0, 10.0)


def reach_fit(placed: list[dict], context: dict) -> Optional[float]:
    """Score whether the overhead shelf sits within comfortable reach for this person.

    Unlike seat/table height, this one CAN be read from the placement grid
    directly — the shelf's y-offset is where its bottom edge sits, in real
    cm via the 40cm grid, no per-module style estimate needed.
    """
    shelf = find_zone(placed, "shelf")
    if shelf is None:
        return None
    actual_cm = shelf["y_off"] * 40.0
    max_reach_cm = C.MAX_REACH_RATIO * context["user_height_cm"]
    over = actual_cm - max_reach_cm
    if over <= 0:
        return 10.0
    return _clip(10.0 - over / C.REACH_TOLERANCE_CM * 10.0, 0.0, 10.0)


def storage_adequacy(placed: list[dict], context: dict) -> Optional[float]:
    """Score whether this candidate's shelf meets a stated need for extra storage.

    Only applies when the person has said they want extra storage
    (context["wants_storage"]) — otherwise this criterion doesn't apply and
    is dropped, same as a candidate missing a needed furniture piece.
    """
    if not context.get("wants_storage"):
        return None
    shelf = find_zone(placed, "shelf")
    if shelf is None:
        return None
    tags = MODULES[shelf["module_id"]].get("tags", [])
    is_extra = "more_shelves" in tags or "wide_shelves" in tags
    return C.STORAGE_ADEQUATE_SCORE if is_extra else C.STORAGE_INADEQUATE_SCORE


# Always-applicable criteria. "Storage adequacy" is deliberately NOT in this
# list — it only makes sense when the person has actually said they want
# extra storage, so it's opt-in per run (see STORAGE_CRITERION below) rather
# than always-on. If it were always-on, everyone who didn't ask for storage
# would fail it by returning None for every candidate, emptying the ranking.
CRITERIA: list[Criterion] = [
    {
        "id": "seat_height_fit",
        "label": "Seat height fit",
        "weight": 1.0,
        "score_fn": seat_height_fit,
    },
    {
        "id": "table_height_fit",
        "label": "Table height fit",
        "weight": 1.0,
        "score_fn": table_height_fit,
    },
    {
        "id": "reach_fit",
        "label": "Shelf reach fit",
        "weight": 1.0,
        "score_fn": reach_fit,
    },
]

STORAGE_CRITERION: Criterion = {
    "id": "storage_adequacy",
    "label": "Storage adequacy",
    "weight": 1.0,
    "score_fn": storage_adequacy,
}


def rank(candidates: list[dict], context: dict, criteria: list[Criterion] = CRITERIA) -> list[dict]:
    """
    candidates: list of {"seed": int, "placed": list[dict]}.
    Returns candidates augmented with per-criterion "scores" and a
    "weighted_total", sorted best first. Candidates missing furniture a
    criterion needs are dropped, not scored 0.
    """
    total_weight = sum(c["weight"] for c in criteria) or 1.0
    scored = []
    for cand in candidates:
        scores: dict[str, float] = {}
        applicable = True
        for c in criteria:
            s = c["score_fn"](cand["placed"], context)
            if s is None:
                applicable = False
                break
            scores[c["id"]] = s
        if not applicable:
            continue
        weighted_total = sum(scores[c["id"]] * c["weight"] for c in criteria) / total_weight
        scored.append({**cand, "scores": scores, "weighted_total": weighted_total})
    scored.sort(key=lambda c: c["weighted_total"], reverse=True)
    return scored
