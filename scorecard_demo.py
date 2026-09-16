"""
Proof of concept run of the dwelling scorecard: generate ~100 dining-section
candidates, score each on the "seat height fit" criterion for one stated user
height, and rank them.

Standalone script — run with `python scorecard_demo.py`.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from solver import solve
from drawing import plot_section
import scorecard

W, H = 6, 9
SEEDS = range(1, 121)  # aim for ~100 valid candidates after some are rejected
USER_HEIGHT_CM = 170

OUT_DIR = Path(__file__).parent / "scorecard_output"
OUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    print(f"Solving {len(SEEDS)} seed candidates for a {W}x{H} dining section...\n")
    candidates = []
    for seed in SEEDS:
        placed = solve(W, H, seed, corridor="none", corridor_w=2,
                        dining_style="compact", roof_style="any")
        if placed is not None:
            candidates.append({"seed": seed, "placed": placed})

    print(f"{len(candidates)} valid candidates out of {len(SEEDS)} seeds.\n")

    ranked = scorecard.rank(candidates, context={"user_height_cm": USER_HEIGHT_CM})
    dropped = len(candidates) - len(ranked)
    print(f"{len(ranked)} candidates had a chair to score ({dropped} dropped — no chair present).\n")

    print(f"Ranking for a {USER_HEIGHT_CM}cm-tall user:\n")
    print(f"{'rank':>4}  {'seed':>4}  {'seat height fit':>15}")
    for i, c in enumerate(ranked, start=1):
        print(f"{i:>4}  {c['seed']:>4}  {c['scores']['seat_height_fit']:>15.2f}")
        if i >= 15 and i < len(ranked) - 3:
            continue
        if i == 15:
            print("   ...")

    best, worst = ranked[0], ranked[-1]
    print(f"\nBest fit:  seed {best['seed']}  (score {best['scores']['seat_height_fit']:.2f})")
    print(f"Worst fit: seed {worst['seed']}  (score {worst['scores']['seat_height_fit']:.2f})")

    fig_best = plot_section(best["placed"], W, H, show_figures=True)
    fig_best.savefig(OUT_DIR / f"best_seed{best['seed']}.png", dpi=150, bbox_inches="tight")
    fig_worst = plot_section(worst["placed"], W, H, show_figures=True)
    fig_worst.savefig(OUT_DIR / f"worst_seed{worst['seed']}.png", dpi=150, bbox_inches="tight")
    print(f"\nSaved best/worst renders to {OUT_DIR}/")


if __name__ == "__main__":
    main()
