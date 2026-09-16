"""
Research proof-of-concept: LLM-as-judge selection layer for kitchen sections.

Standalone demo script — run with `python judge_demo.py`. Not wired into app.py;
this exists to demonstrate the concept for the Marios meeting, not as production code.

Kitchen was chosen over dining for this demo because its cabinet stack (lower
cabinet -> upper cabinet -> overhead shelf) genuinely varies in height by seed
(upper cabinets range h1-h4, shelves h2-h3), unlike the dining brief we tried
first, where the pitched-shelf catalog only had one module matching at the
tested width — seed varied which module got picked, but not its geometry.

What it does, end to end:
  1. Calls the real solver (solve()) across several seeds to get several valid
     kitchen-section candidates for the same brief — exactly what the solver
     already does today.
  2. Computes hard geometric facts for each candidate directly from the placed
     module data (no LLM involved in this step) — how high the occupant must
     reach for the top of the usable cabinet stack, and how much storage sits
     above that comfortable reach.
  3. Sends those facts to the LLM judge (llm.judge_section) and gets back an
     enclosure/openness score for that candidate, grounded in the facts.
  4. Combines the scores with per-profile weights in plain Python — a "wants
     privacy" profile weights enclosure higher, a "wants openness" profile
     weights openness higher — and picks the best candidate per profile.
  5. Simulates one conversational correction ("too exposed, I want more
     privacy") and shows the weights shift and the pick change.
  6. Optionally re-runs the judge with a second model and reports whether the
     two models agree on the top pick (cross-model reliability check).
  7. Renders the winning candidates to PNGs for the meeting.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import llm
from solver import solve
from modules import MODULES
from drawing import plot_section

OUT_DIR = Path(__file__).parent / "judge_demo_output"
OUT_DIR.mkdir(exist_ok=True)

W, H = 6, 9
SEEDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# Set to a second model string to run the cross-model agreement check
# (must use a provider you have an API key configured for). Set to None to skip.
SECOND_MODEL = None


def find_zone(placed: list[dict], zone_name: str) -> dict | None:
    for p in placed:
        if MODULES[p["module_id"]]["zone"] == zone_name:
            return p
    return None


def compute_facts(placed: list[dict], H: int) -> dict | None:
    """Hard geometric facts, computed once, handed to the LLM as ground truth.

    Kitchen's cabinet stack fills the height with no air gap (lower cabinet,
    then upper cabinet, then overhead shelf, stacked directly), so the
    meaningful section-specific fact isn't a reach *distance* like in dining —
    it's how tall the reachable stack is, and how much storage sits above it.
    """
    lower = find_zone(placed, "lower_cabinet")
    upper = find_zone(placed, "upper_cabinet")
    shelf = find_zone(placed, "shelf")
    if lower is None or upper is None or shelf is None:
        return None
    reach_height   = MODULES[lower["module_id"]]["h"] + MODULES[upper["module_id"]]["h"]
    overhead_height = MODULES[shelf["module_id"]]["h"]
    return {
        "H": H,
        "reach_height":    round(reach_height, 2),
        "overhead_height": round(overhead_height, 2),
    }


def weighted_score(score: dict, w_enclosure: float, w_openness: float) -> float:
    return w_enclosure * score["enclosure_score"] + w_openness * score["openness_score"]


def rank(scored: list[dict], w_enclosure: float, w_openness: float) -> list[dict]:
    return sorted(scored, key=lambda c: weighted_score(c["score"], w_enclosure, w_openness),
                  reverse=True)


def main() -> None:
    print(f"Solving {len(SEEDS)} seed candidates for a {W}x{H} kitchen section...\n")
    candidates = []
    for seed in SEEDS:
        placed = solve(W, H, seed, corridor="none", corridor_w=2,
                        roof_style="divided", section="kitchen")
        if placed is None:
            print(f"  seed {seed:>2}  -> solver rejected (no valid layout)")
            continue
        facts = compute_facts(placed, H)
        if facts is None:
            continue
        candidates.append({"seed": seed, "placed": placed, "facts": facts})

    print(f"{len(candidates)} valid candidates out of {len(SEEDS)} seeds.\n")

    print("Judging each candidate (LLM scores enclosure/openness, grounded in computed facts)...\n")
    for c in candidates:
        c["score"] = llm.judge_section(c["facts"])
        status = c["score"] if c["score"] else "FAILED"
        print(f"  seed {c['seed']:>2}  facts={c['facts']}  ->  {status}")

    scored = [c for c in candidates if c["score"]]
    if not scored:
        print("\nNo candidates were successfully judged — check API key / model config.")
        return

    # ── Render every valid candidate + save a manifest for the Streamlit UI ──
    manifest = []
    for c in scored:
        img_name = f"seed{c['seed']}.png"
        fig = plot_section(c["placed"], W, H, show_figures=True)
        fig.savefig(OUT_DIR / img_name, dpi=150, bbox_inches="tight")
        manifest.append({
            "seed": c["seed"], "facts": c["facts"], "score": c["score"], "image": img_name,
        })
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Rendered {len(manifest)} candidates + wrote manifest.json to {OUT_DIR}/\n")

    print("\n" + "=" * 70)
    print("Profile: WANTS PRIVACY  (enclosure weighted 0.8, openness 0.2)")
    print("=" * 70)
    privacy_rank = rank(scored, w_enclosure=0.8, w_openness=0.2)
    for c in privacy_rank:
        print(f"  seed {c['seed']:>2}  weighted_score={weighted_score(c['score'], 0.8, 0.2):.2f}  "
              f"({c['score']['reasoning']})")
    best_privacy = privacy_rank[0]
    print(f"\n  -> Selected seed {best_privacy['seed']}")

    print("\n" + "=" * 70)
    print("Profile: WANTS OPENNESS  (enclosure weighted 0.2, openness 0.8)")
    print("=" * 70)
    open_rank = rank(scored, w_enclosure=0.2, w_openness=0.8)
    best_open = open_rank[0]
    for c in open_rank:
        print(f"  seed {c['seed']:>2}  weighted_score={weighted_score(c['score'], 0.2, 0.8):.2f}")
    print(f"\n  -> Selected seed {best_open['seed']}")

    # ── Simulated conversational correction ─────────────────────────────────
    print("\n" + "=" * 70)
    print("Correction turn: user says \"too exposed, I want more privacy\"")
    print("=" * 70)
    w_enclosure, w_openness = 0.8, 0.2
    w_enclosure, w_openness = min(1.0, w_enclosure + 0.15), max(0.0, w_openness - 0.15)
    corrected_rank = rank(scored, w_enclosure, w_openness)
    print(f"  Weights adjusted: enclosure={w_enclosure:.2f}, openness={w_openness:.2f}")
    print(f"  Re-selected seed {corrected_rank[0]['seed']} (was {best_privacy['seed']})")

    # ── Cross-model agreement check ─────────────────────────────────────────
    if SECOND_MODEL:
        print("\n" + "=" * 70)
        print(f"Cross-model check against {SECOND_MODEL}")
        print("=" * 70)
        scored_b = []
        for c in scored:
            score_b = llm.judge_section(c["facts"], model=SECOND_MODEL)
            if score_b:
                scored_b.append({**c, "score": score_b})
                print(f"  seed {c['seed']:>2}  model_a={c['score']}  model_b={score_b}")
        if scored_b:
            best_privacy_b = rank(scored_b, 0.8, 0.2)[0]
            agree = best_privacy_b["seed"] == best_privacy["seed"]
            print(f"\n  Model A top pick: seed {best_privacy['seed']}")
            print(f"  Model B top pick: seed {best_privacy_b['seed']}")
            print(f"  {'AGREE' if agree else 'DISAGREE'}")
        else:
            print("  Second model produced no usable scores — check model name / API key.")


if __name__ == "__main__":
    main()
