"""
Self-check benchmark for the LLM-as-judge mechanism (llm.judge_section).

Validates the judge against a transparent, mechanically-obvious proxy formula
derived from the same computed facts it's given — not a human rating. This
answers "is the generated result actually the best result?" without a human
in the loop, at the cost of only proving internal consistency with the
geometry, not that the geometry-quality link matches real human experience
(a separate, named assumption, not hidden).

Three checks:
  1. Correlation   — does the judge's enclosure_score track the proxy ranking
                      across many candidates? (Spearman rank correlation.)
  2. Dominance     — for two candidates where one is unambiguously more
                      enclosed than the other on every dimension (same H,
                      strictly more overhead_height), does the judge ever
                      invert that ranking? Each inversion is a hard,
                      falsifiable failure, not a matter of degree.
  3. Repeatability — how much does the judge's score vary across repeated
                      calls on IDENTICAL facts? (We already saw this vary by
                      accident in judge_demo.py; this formalizes it.)

Facts are synthesized directly — no solver call needed — so the sweep isn't
limited by whatever the current module catalog happens to produce (the
problem that blocked the seed-diversity approach in judge_demo.py).
"""
import itertools
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

import llm

OUT_DIR = Path(__file__).parent / "judge_demo_output"
OUT_DIR.mkdir(exist_ok=True)


def enclosure_proxy(facts: dict) -> float:
    """Mechanically obvious baseline: fraction of total height taken by overhead storage."""
    return facts["overhead_height"] / facts["H"]


def synthetic_facts(H_values=(7, 9, 11), overhead_step: int = 2) -> list[dict]:
    """Sweep the full plausible geometric range directly, without solving anything."""
    out = []
    for H in H_values:
        for overhead in range(1, H, overhead_step):
            reach = H - overhead
            out.append({"H": H, "reach_height": reach, "overhead_height": overhead})
    return out


def spearman(a: list[float], b: list[float]) -> float:
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    facts_list = synthetic_facts()
    print(f"--- Correlation sweep: {len(facts_list)} synthetic candidates ---\n")

    proxy_scores: list[float] = []
    judge_scores: list[float] = []
    scored_facts: list[dict] = []
    for f in facts_list:
        proxy = enclosure_proxy(f)
        result = llm.judge_section(f)
        if result is None:
            print(f"  {f} -> JUDGE FAILED")
            continue
        proxy_scores.append(proxy)
        judge_scores.append(result["enclosure_score"])
        scored_facts.append(f)
        print(f"  {f}  proxy={proxy:.2f}  judge_enclosure={result['enclosure_score']}")

    if len(judge_scores) >= 2:
        rho = spearman(proxy_scores, judge_scores)
        print(f"\nSpearman correlation (judge vs. proxy): {rho:.3f}")
    else:
        print("\nNot enough successful judgments to compute correlation.")

    # ── Dominance check, grouped by H ────────────────────────────────────────
    print("\n--- Dominance violations (within each H group) ---")
    violations = 0
    total_pairs = 0
    for H in sorted({f["H"] for f in scored_facts}):
        group = sorted(
            [(f, s) for f, s in zip(scored_facts, judge_scores) if f["H"] == H],
            key=lambda fs: fs[0]["overhead_height"],
        )
        for (fa, sa), (fb, sb) in itertools.combinations(group, 2):
            total_pairs += 1
            if sa > sb:  # fa has less-or-equal overhead_height than fb by sort order
                violations += 1
                print(f"  VIOLATION: H={H} overhead={fa['overhead_height']} (score {sa}) "
                      f"> overhead={fb['overhead_height']} (score {sb})")
    print(f"\n{violations}/{total_pairs} dominance pairs violated")

    # ── Repeatability check ──────────────────────────────────────────────────
    print("\n--- Repeatability (same facts, 5 runs each) ---")
    repeatability = []
    if scored_facts:
        probe_facts = [scored_facts[0], scored_facts[len(scored_facts) // 2], scored_facts[-1]]
        for f in probe_facts:
            scores = []
            for _ in range(5):
                r = llm.judge_section(f)
                if r:
                    scores.append(r["enclosure_score"])
            if len(scores) >= 2:
                stdev = statistics.stdev(scores)
                print(f"  {f}  scores={scores}  stdev={stdev:.2f}")
                repeatability.append({"facts": f, "scores": scores, "stdev": stdev})
            else:
                print(f"  {f}  not enough successful runs to compute stdev")

    results = {
        "facts": scored_facts,
        "proxy_scores": proxy_scores,
        "judge_scores": judge_scores,
        "spearman": spearman(proxy_scores, judge_scores) if len(judge_scores) >= 2 else None,
        "violations": violations,
        "total_pairs": total_pairs,
        "repeatability": repeatability,
    }
    (OUT_DIR / "benchmark_after.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote benchmark_after.json to {OUT_DIR}/")


if __name__ == "__main__":
    main()
