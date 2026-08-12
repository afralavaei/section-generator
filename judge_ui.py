"""
Visual dashboard for the LLM-as-judge research demo — standalone Streamlit app,
separate from the main configurator (app.py). Run on its own port:

    streamlit run judge_ui.py --server.port 8502

Reads pre-generated data from judge_demo_output/ (written by judge_demo.py and
judge_benchmark.py) — it does not call the LLM itself, so browsing this page
costs nothing and has no risk of a live API failure during the meeting.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from solver import solve
from drawing import plot_section
import scorecard
import scorecard_constants as SC

OUT_DIR = Path(__file__).parent / "judge_demo_output"

st.set_page_config(page_title="LLM-as-Judge — Evaluation Dashboard", layout="wide")
st.title("LLM-as-Judge — Evaluation Dashboard")
st.caption(
    "Research proof of concept for Nomadic Engine: an LLM scores kitchen-section candidates "
    "on enclosure/openness, grounded in geometric facts computed from the solver's own output."
)

tab_gallery, tab_benchmark, tab_scorecard = st.tabs(
    ["Kitchen candidates", "Self-check benchmark", "Scorecard (seat height fit)"]
)

# ── Tab 1: Kitchen candidate gallery ────────────────────────────────────────
with tab_gallery:
    manifest_path = OUT_DIR / "manifest.json"
    if not manifest_path.exists():
        st.warning("No manifest.json found — run `python judge_demo.py` first.")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        st.subheader("1. Choose a profile")
        preset = st.radio(
            "Quick presets", ["Wants privacy", "Balanced", "Wants openness", "Custom"],
            horizontal=True, index=1,
        )
        preset_w = {"Wants privacy": 0.8, "Balanced": 0.5, "Wants openness": 0.2}
        if preset == "Custom":
            w_enclosure = st.slider("Enclosure weight  (0 = wants openness, 1 = wants privacy)",
                                     0.0, 1.0, 0.5, 0.05)
        else:
            w_enclosure = preset_w[preset]
            st.slider("Enclosure weight  (0 = wants openness, 1 = wants privacy)",
                       0.0, 1.0, w_enclosure, 0.05, disabled=True)
        w_openness = 1.0 - w_enclosure

        if "correction_bump" not in st.session_state:
            st.session_state.correction_bump = 0.0
        if st.button('💬 Simulate correction: "too exposed, I want more privacy"'):
            st.session_state.correction_bump = min(0.95 - w_enclosure, st.session_state.correction_bump + 0.15)
        if st.session_state.correction_bump:
            w_enclosure = min(1.0, w_enclosure + st.session_state.correction_bump)
            w_openness = 1.0 - w_enclosure
            st.info(f"Correction applied — weights adjusted to enclosure={w_enclosure:.2f}, "
                    f"openness={w_openness:.2f} without any new candidates being generated.")

        for c in manifest:
            c["weighted_score"] = (
                w_enclosure * c["score"]["enclosure_score"] + w_openness * c["score"]["openness_score"]
            )
        ranked = sorted(manifest, key=lambda c: c["weighted_score"], reverse=True)

        st.subheader(f"2. Ranked candidates ({len(ranked)} valid, out of the seeds tried)")
        cols = st.columns(3)
        for i, c in enumerate(ranked):
            with cols[i % 3]:
                img_path = OUT_DIR / c["image"]
                label = "🏆 SELECTED" if i == 0 else f"#{i + 1}"
                st.markdown(f"**{label} — seed {c['seed']}**")
                if img_path.exists():
                    st.image(str(img_path), width="stretch")
                st.caption(
                    f"facts: reach_height={c['facts']['reach_height']}, "
                    f"overhead_height={c['facts']['overhead_height']} (H={c['facts']['H']})"
                )
                st.caption(
                    f"enclosure={c['score']['enclosure_score']}  ·  "
                    f"openness={c['score']['openness_score']}  ·  "
                    f"weighted={c['weighted_score']:.2f}"
                )
                with st.expander("LLM reasoning"):
                    st.write(c["score"]["reasoning"])

# ── Tab 2: Self-check benchmark ─────────────────────────────────────────────
with tab_benchmark:
    before_path = OUT_DIR / "benchmark_before.json"
    after_path = OUT_DIR / "benchmark_after.json"

    st.subheader("Does the judge's score actually track the geometry?")
    st.markdown(
        "No human ratings involved. `enclosure_proxy = overhead_height / H` is a mechanically "
        "obvious baseline computed straight from the same facts the judge sees — if the judge's "
        "score doesn't track it, something is wrong with the judge's reasoning (or its "
        "instructions). This benchmark synthesizes 12 fact combinations directly (no solver "
        "needed) spanning the plausible geometric range, and checks three things: correlation "
        "with the proxy, whether it ever inverts an unambiguous ranking (dominance violation), "
        "and whether repeated calls on identical facts agree with each other."
    )

    if not before_path.exists() or not after_path.exists():
        st.warning("Missing benchmark_before.json / benchmark_after.json in judge_demo_output/.")
    else:
        before = json.loads(before_path.read_text(encoding="utf-8"))
        after = json.loads(after_path.read_text(encoding="utf-8"))

        st.info(
            "**What happened:** the first run of this benchmark caught a real bug — the judge's "
            "prompt described enclosure using both `reach_height` and `overhead_height` in a way "
            "that was logically contradictory (they always sum to H, so they can't both be "
            "\"large\"). The LLM latched onto the wrong one. Fixing the wording and re-running "
            "is the before/after below."
        )

        col_before, col_after = st.columns(2)

        def scatter(data: dict, title: str, color: str):
            fig, ax = plt.subplots(figsize=(4.5, 4.5))
            ax.scatter(data["proxy_scores"], data["judge_scores"], color=color, s=60, zorder=3)
            ax.plot([0, 1], [0, 10], linestyle="--", color="gray", alpha=0.5,
                     label="score = proxy × 10 (expected)")
            ax.set_xlabel("enclosure_proxy  (overhead_height / H)")
            ax.set_ylabel("judge enclosure_score")
            ax.set_title(title)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 10)
            ax.legend(fontsize=8, loc="upper left")
            return fig

        with col_before:
            st.markdown("### Before fix")
            st.pyplot(scatter(before, "Buggy prompt", "#c0392b"))
            st.metric("Spearman correlation", f"{before['spearman']:.3f}")
            st.metric("Dominance violations", f"{before['violations']} / {before['total_pairs']}")

        with col_after:
            st.markdown("### After fix")
            st.pyplot(scatter(after, "Fixed prompt", "#27ae60"))
            st.metric("Spearman correlation", f"{after['spearman']:.3f}",
                       delta=f"{after['spearman'] - before['spearman']:+.3f}")
            st.metric("Dominance violations", f"{after['violations']} / {after['total_pairs']}",
                       delta=f"{after['violations'] - before['violations']:+d}", delta_color="inverse")

        st.subheader("Repeatability — same facts, 5 calls each")
        rcol1, rcol2 = st.columns(2)
        for col, data, label in [(rcol1, before, "Before"), (rcol2, after, "After")]:
            with col:
                st.markdown(f"**{label}**")
                for r in data["repeatability"]:
                    st.write(f"`{r['facts']}` → scores={r['scores']} · stdev={r['stdev']:.2f}")

        st.subheader("Honest limitation")
        st.warning(
            "After the fix, judge_enclosure ≈ proxy × 10 almost exactly — the LLM is now "
            "essentially just computing the formula stated in the prompt, not exercising "
            "independent judgment. Perfect correlation here proves the judge is internally "
            "consistent with the geometry, not that it adds value beyond the formula. The "
            "genuinely interesting test — whether it reasons well on the qualitative part "
            "(translucency, a rendered image, \"does this feel cozy\") — hasn't been run yet; "
            "this benchmark only covers the simple, single-variable synthetic cases."
        )

# ── Tab 3: Scorecard proof of concept ───────────────────────────────────────
with tab_scorecard:
    st.subheader("A deterministic scorecard, not a model's opinion")
    st.markdown(
        "**What this is:** generate several candidate layouts -> score every one against "
        "explicit, code-computed criteria -> rank them. A weighted-scoring decision matrix "
        "(candidates as rows, criteria as columns), the same structure as a requirement-"
        "prioritization matrix. No LLM involved anywhere in this tab — every score below is "
        "a plain calculation, fully traceable back to a formula and a stated assumption.\n\n"
        "**Criterion #1 (proof of concept): seat height fit** — does the chair in a given "
        "layout sit at a comfortable height for *this specific person's* stated height? "
        "Full write-up in `SCORECARD_PROPOSAL.md`."
    )

    with st.expander("Reference model this is based on (weighted-scoring decision matrix)"):
        st.caption(
            "Via Dr Eugene F.M. O'Loughlin, National College of Ireland — the teaching "
            "example that prompted this proposal. Options A-E become our generated "
            "candidates; the criteria rows become our scoring functions."
        )
        st.markdown(
            "| Criteria | Weight | A | B | C | D | E |\n"
            "|---|---|---|---|---|---|---|\n"
            "| Value | 20% | 80 | 45 | 40 | 15 | 35 |\n"
            "| Risk | 20% | 60 | 85 | 30 | 20 | 75 |\n"
            "| Difficulty | 15% | 55 | 80 | 50 | 15 | 25 |\n"
            "| Success | 10% | 30 | 60 | 55 | 65 | 30 |\n"
            "| Compliance | 5% | 35 | 60 | 50 | 60 | 50 |\n"
            "| Relationships | 5% | 80 | 70 | 70 | 85 | 80 |\n"
            "| Stakeholder | 15% | 25 | 50 | 45 | 60 | 60 |\n"
            "| Urgency | 10% | 60 | 25 | 40 | 65 | 60 |\n"
            "| **Weighted Scores** | **100%** | **54.8** | **60.0** | **43.3** | **38.0** | **52.3** |"
        )

    with st.expander("Related work — is this an established idea in architecture?"):
        st.markdown(
            "**Weighted scoring to rank generated architectural layouts is an established, "
            "active research area** — this is a specific instance of a recognized method, "
            "not an invented one.\n\n"
            "**The dominant existing approach in parametric/Grasshopper-style generative "
            "design is different**: genetic-algorithm multi-objective optimization "
            "(Pareto-front tools like Octopus) that explores trade-offs *during* generation, "
            "rather than scoring discrete candidates afterward. Nomadic Engine has "
            "deliberately removed Grasshopper — this scorecard is a plain-Python alternative "
            "to that norm, not a reimplementation of it.\n\n"
            "**Anthropometric furniture sizing is one of the oldest ideas in architecture** "
            "— but always applied once, by a human designer, for an average population. "
            "Using it as a *live, automated, per-individual* scoring function inside a "
            "generative ranking pipeline is the part that doesn't show up in prior work — "
            "that's the actual novel claim here, not \"we use ergonomics.\""
        )
        st.caption(
            "Sources: "
            "[Generative design for architectural spatial layouts: a review](https://www.tandfonline.com/doi/full/10.1080/13467581.2025.2512235) · "
            "[AHP + weighted scoring for design candidates](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0312282) · "
            "[Multi-objective genetic algorithm optimization](https://www.researchgate.net/publication/365834560_Multi-Objective_Optimisation_of_Urban_Design_Using_a_Genetic_Algorithm) · "
            "[Anthropometric measurements for furniture design](https://www.sciencedirect.com/science/article/pii/S2215098616304578) · "
            "[Anthropometrics/Ergonomics in architectural education](https://architecture.uonbi.ac.ke/research-projects/architectural-design-02-03-anthropometrics-and-ergonomics) · "
            "[Decision-matrix method for ranking design alternatives](https://mee.group.shef.ac.uk/ProjectWeeks/content/decisionMatrix/SelectFinalDesign_teachingNotes.html)"
        )

    col_h, col_s = st.columns([3, 1])
    with col_h:
        user_height_cm = st.slider("User height (cm)", 140, 200, 170, 1)
    with col_s:
        wants_storage = st.checkbox("Wants extra storage", value=False)

    SCENARIOS = [
        {"label": "Compact, seed 1", "W": 6, "H": 9, "seed": 1, "style": "compact"},
        {"label": "Compact, seed 5", "W": 6, "H": 9, "seed": 5, "style": "compact"},
        {"label": "Compact, seed 10", "W": 6, "H": 9, "seed": 10, "style": "compact"},
        {"label": "Spacious, seed 1", "W": 8, "H": 9, "seed": 1, "style": "spacious"},
        {"label": "Spacious, seed 5", "W": 8, "H": 9, "seed": 5, "style": "spacious"},
    ]

    @st.cache_data
    def solve_scenario(W, H, seed, style):
        return solve(W, H, seed, corridor="none", corridor_w=2,
                     dining_style=style, roof_style="any")

    candidates = []
    for sc in SCENARIOS:
        placed = solve_scenario(sc["W"], sc["H"], sc["seed"], sc["style"])
        if placed is not None:
            candidates.append({**sc, "placed": placed})

    criteria = scorecard.CRITERIA + ([scorecard.STORAGE_CRITERION] if wants_storage else [])
    context = {"user_height_cm": user_height_cm, "wants_storage": wants_storage}
    ranked = scorecard.rank(candidates, context, criteria)
    dropped = len(candidates) - len(ranked)

    st.subheader(f"Ranked for a {user_height_cm}cm-tall user")
    if dropped:
        st.caption(f"{dropped} candidate(s) dropped — missing furniture a criterion needs.")

    if not ranked:
        st.warning("No candidates could be scored — check solver parameters / criteria above.")
    else:
        cols = st.columns(len(ranked))
        for i, r in enumerate(ranked):
            with cols[i]:
                label = "🏆 BEST FIT" if i == 0 else f"#{i + 1}"
                st.markdown(f"**{label}**")
                st.caption(r["label"])
                fig = plot_section(r["placed"], r["W"], r["H"], show_figures=True)
                st.pyplot(fig, width="stretch")
                st.metric("Weighted total", f"{r['weighted_total']:.1f} / 10")

        st.subheader("Full scorecard")
        header = "| Candidate | " + " | ".join(c["label"] for c in criteria) + " | **Weighted Total** |"
        sep = "|---|" + "---|" * (len(criteria) + 1)
        table_rows = [header, sep]
        for r in ranked:
            cells = " | ".join(f"{r['scores'][c['id']]:.1f}" for c in criteria)
            table_rows.append(f"| {r['label']} | {cells} | **{r['weighted_total']:.1f}** |")
        st.markdown("\n".join(table_rows))

    st.subheader("Numbers used here (awaiting sign-off)")
    st.write(f"- Ideal seat height = {SC.SEAT_HEIGHT_RATIO:.0%} of height  ·  "
             f"low chair {SC.SEAT_HEIGHT_BY_CLASS_CM['h2']:.0f}cm, tall chair {SC.SEAT_HEIGHT_BY_CLASS_CM['h3']:.0f}cm")
    st.write(f"- Ideal table height = {SC.TABLE_HEIGHT_RATIO:.0%} of height  ·  "
             f"low table {SC.TABLE_HEIGHT_BY_CLASS_CM['h2']:.0f}cm, tall table {SC.TABLE_HEIGHT_BY_CLASS_CM['h3']:.0f}cm")
    st.write(f"- Max comfortable overhead reach = {SC.MAX_REACH_RATIO:.0%} of height")
    st.caption(
        "All placeholder rule-of-thumb estimates, not measured from the module drawings "
        "(the drawings are stylized 2D schematics on a 40cm grid, not precise physical "
        "blueprints — confirmed by inspection, not assumed)."
    )
