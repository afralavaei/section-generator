# A Deterministic Scorecard for Selecting the Best-Fitting Dwelling Section

**The reference model this is based on**

A classic weighted-scoring / requirements-prioritization matrix: each row is a criterion
with a weight, each column is an option being evaluated, and the bottom row is the
weighted sum per option — the option with the highest weighted score wins.
(Example below via Dr Eugene F.M. O'Loughlin, National College of Ireland — the teaching
example that prompted this proposal.)

| Criteria | Weight | A | B | C | D | E |
|---|---|---|---|---|---|---|
| Value | 20% | 80 | 45 | 40 | 15 | 35 |
| Risk | 20% | 60 | 85 | 30 | 20 | 75 |
| Difficulty | 15% | 55 | 80 | 50 | 15 | 25 |
| Success | 10% | 30 | 60 | 55 | 65 | 30 |
| Compliance | 5% | 35 | 60 | 50 | 60 | 50 |
| Relationships | 5% | 80 | 70 | 70 | 85 | 80 |
| Stakeholder | 15% | 25 | 50 | 45 | 60 | 60 |
| Urgency | 10% | 60 | 25 | 40 | 65 | 60 |
| **Weighted Scores** | **100%** | **54.8** | **60.0** | **43.3** | **38.0** | **52.3** |

Mapped onto Nomadic Engine: **options A-E become the generated candidates** (seeds,
instead of five fixed requirements), and **the criteria rows become the scoring
functions** described below (seat height fit today, more to follow) — same structure,
same weighted-sum-and-rank logic, just applied to dwelling layouts instead of project
requirements.

**What We Are Doing**

Nomadic Engine's solver already produces many valid layouts for the same brief just by
changing its seed, with no way to tell them apart in quality — earlier proposals tried to
close that gap with a geometric analysis method borrowed from floor plans (didn't fit our
section-based, translucent-fabric system) and then with an LLM judging one layout at a
time (works, but raised a fair question: is the LLM doing anything a formula couldn't?).
This proposal sidesteps both problems. Instead of generating one layout and evaluating it,
we generate a whole batch of candidates, score every single one against a small set of
explicit, code-computed criteria, and rank them — a classic weighted-scoring decision
matrix (candidates as rows, criteria as columns, one weighted total), the same structure
used for requirement-prioritization matrices in engineering and product management. No
model judgment involved — every score is a plain, inspectable calculation.

**Why**

The motivating gap is the same one that's been true throughout: the solver can produce
many structurally valid options for a brief, and currently has no way to say which one
actually suits a specific person. What's different here is *how* we answer that. Instead
of asking a language model to form a qualitative opinion about a layout, we define a
concrete, numeric criterion — grounded directly in the solver's own output and a fact
about the person (their height) — and compute a score with arithmetic. That closes the
"is the AI actually doing anything" question directly: nothing here is a model's opinion;
every number can be traced back to a formula and a stated assumption.

**Method**

1. **Generate many candidates.** Run the existing solver across a batch of seeds
   (roughly 100, though the working demo currently uses 5 for a fast, legible walkthrough)
   for one fixed brief. Nothing about the solver itself changes.
2. **Score each on defined criteria.** A criterion is a small, explicit function:
   given a candidate's layout and some fact about the person, return a 0–10 score.
   Four are built so far, each the same shape — a real fact about the layout (read
   through the codebase's fixed 40cm grid, so every number is physical centimeters,
   not an abstract scale) compared against a rule-of-thumb ideal derived from the
   person's stated height:
   - **Seat height fit** — is the chair at a comfortable height for this person?
   - **Table height fit** — same idea, for the table/work surface.
   - **Shelf reach fit** — is the overhead shelf within comfortable reach, or does
     the person have to strain/stretch for it?
   - **Storage adequacy** (opt-in) — only checked when the person has said they
     want extra storage; scores whether the layout's shelf actually has that.
3. **Rank.** Every candidate gets a weighted total across whichever criteria apply to
   it (weights currently equal across all of them) and candidates are sorted
   best-to-worst for that person. A candidate missing furniture a criterion needs is
   dropped from that ranking rather than penalized with a 0.
4. **Every number is visible and flagged, not buried.** Every estimate this system
   depends on lives in one small, heavily commented file, explicitly marked as
   "awaiting sign-off" until independently confirmed. Nothing is silently assumed.
5. **Criteria are added one at a time**, with weighting deliberately deferred until at
   least two criteria exist and each has been individually validated — this may end up
   being a checklist of raw scores rather than one collapsed number, and that's a fine
   outcome, not a fallback.

**Related Work**

Multi-criteria weighted scoring for ranking generated architectural layouts is an
established, active research area, not an invented technique — there is direct prior
work reviewing exactly this pattern for generative spatial layouts, and other work
combining the Analytic Hierarchy Process with weighted scoring to rank generated design
candidates — the same shape as the reference matrix above (criteria, weights, scored
candidates, ranked). This proposal is a specific instance of a recognized method, not a
novel one.

Worth naming directly: the *dominant* existing approach in parametric/Grasshopper-style
generative design is different — genetic-algorithm multi-objective optimization
(Pareto-front tools like Octopus, built on algorithms such as SPEA-2/HypE), which
explores trade-offs *during* generation and picks from a Pareto-optimal set, rather than
generating discrete candidates and scoring them afterward. Nomadic Engine has explicitly
removed Grasshopper from its architecture, so this scorecard is a deliberate alternative
to that norm: plain Python, seed-driven candidate generation, post-hoc scoring, no
optimization loop.

Anthropometric sizing of furniture and space is one of the oldest, most foundational
ideas in architecture — a standard part of architectural education, not a stretch. What
existing material consistently describes, though, is a *human designer* applying
anthropometric data *once*, at design time, sized for an *average population*. Using it
as a live, automated scoring function inside a generative pipeline — personalized to one
specific stated individual, re-evaluated automatically across many machine-generated
candidates — is the combination that doesn't show up in what was found. That is the
sharper, more honest claim to make about what's actually new here: not "we use
ergonomics," but "we automate and personalize a criterion architecture has always used
manually."

Sources: [Generative design for architectural spatial layouts: a review of technical
approaches](https://www.tandfonline.com/doi/full/10.1080/13467581.2025.2512235) ·
[AHP + weighted scoring for evaluating generated design
candidates](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0312282) ·
[Multi-objective genetic algorithm optimization in
design](https://www.researchgate.net/publication/365834560_Multi-Objective_Optimisation_of_Urban_Design_Using_a_Genetic_Algorithm)
· [Anthropometric measurements for ergonomic furniture
design](https://www.sciencedirect.com/science/article/pii/S2215098616304578) ·
[Anthropometrics and Ergonomics in architectural
education](https://architecture.uonbi.ac.ke/research-projects/architectural-design-02-03-anthropometrics-and-ergonomics)
· [Decision-matrix method for ranking design
alternatives](https://mee.group.shef.ac.uk/ProjectWeeks/content/decisionMatrix/SelectFinalDesign_teachingNotes.html)

**Positive Sides**

Every score is a plain calculation, fully inspectable — there's no question of whether an
AI model is "really" reasoning or just pattern-matching, because there's no model in the
loop for scoring at all. It requires no new solver infrastructure — the seed-variation
and module data already exist; this adds an evaluation and ranking step on top. It's
grounded in a real physical unit (the confirmed 40cm grid), not an abstract scale, which
makes every number checkable by a human without special tooling. And extending the
criteria list needs no rearchitecting — each is an independent, testable function.

**Questionable Sides**

The rule-of-thumb constants (the 24% ratio, and the per-chair-style height estimates)
are genuinely unverified — they are estimates pending review, and the proposal is built
to surface that honestly rather than hide it behind a confident-sounding number. Building
this out honestly surfaced a real gap in the underlying module catalog: the "tall chair"
style category currently contains visually different chairs that are all treated as one
height in the data, when in reality they should represent at least two distinct real-world
heights (roughly 60cm and 80cm) — the catalog itself doesn't yet distinguish them, which
is flagged as a real content task, not something this scoring layer can resolve on its
own. And because seed variation alone doesn't always move every criterion (a specific
layout parameter, not the random seed, controls chair height in the current solver),
a batch of "different" candidates can sometimes tie on a given criterion — which is an
honest property of the underlying solver worth stating plainly, not a flaw in the scoring
method itself.

---

*Live demo: a Streamlit dashboard renders five candidate dining layouts and ranks them
live against a height slider — moving the slider re-ranks the candidates in real time,
with the underlying estimates shown on-page as pending review, not asserted as fact.*
