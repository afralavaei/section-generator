---
name: dwelling-scorecard
description: >
  Build and extend a multi-criteria weighted scorecard for ranking Nomadic Engine
  section candidates (100 seeds -> score each on defined criteria -> weighted rank),
  developed iteratively with a non-technical stakeholder one criterion at a time.
  Use when the conversation is about defining/adding a scoring criterion, tuning
  anthropometric or other numeric constants, generating/ranking candidate batches,
  or when the user says things like "let's add a criterion", "score the candidates",
  "what criteria do we have so far", or references the scorecard/weighted-ranking work.
---

# Dwelling Scorecard

## What this is

A replacement/superset for the earlier single-seed-pick and LLM-judge approach:
instead of generating one layout and eyeballing it (or judging one candidate at a
time with an LLM), generate ~100 candidates from `solve()` by sweeping seeds for one
fixed brief, score every candidate against a small set of **deterministic, code-computed
criteria**, sum the (optionally weighted) scores, and rank. Modeled on a classic
weighted-scoring decision matrix: rows = candidates, columns = criteria, one weighted
total column.

This came from a second stakeholder (a friend of the primary user) who scoped the
architecture and proof-of-concept criterion, then handed off. The primary user
("she" below) will define further criteria with you going forward — she is not a
coder and does not think in code or formal logic by default. Her instinct, unprompted,
is to over-specify (many special cases, exceptions, edge conditions) rather than find
the general rule. Your job in this skill is to keep the system simple, generalized,
and implementable, while still capturing what she actually wants.

## Established architecture — do not re-derive or re-litigate this

- **Candidate generation:** call the existing `solve()` unmodified, across ~100-120
  seeds, for one fixed brief (some seeds will be rejected as invalid — expected).
- **A criterion is a plain dict:** `{id, label, weight, score_fn}`, where
  `score_fn(placed, context) -> float` returns a 0-10 score. No base classes, no
  plugin system, no config file format — a list of dicts and one sort call.
- **`rank(candidates, criteria)`** computes every candidate's per-criterion scores
  *and* a weighted total, then sorts. With one criterion the weight is moot (100%).
- **Weights are optional and deferred.** Default to an equal split across whatever
  criteria exist. Do not bring up weight *assignment* with her until at least two
  criteria exist and each has been individually validated on its own. She may decide
  never to use weights at all and just look at raw per-criterion scores — keep that
  door open, don't force a single collapsed number on her.
- **All tunable numeric constants live in one separate, heavily commented file**
  (e.g. `scorecard_constants.py`) — never hardcoded inline inside a scoring function.
  Every constant's comment must say: what it represents, why this value (rule-of-thumb
  vs. a real citation), and that it is **unverified — needs her sign-off**. When you
  introduce a new constant, tell her explicitly, in plain language, what it does and
  why you picked that number, and ask her to sanity check it.
- **Backward compatibility, without overengineering it:** this whole system lives in
  new, standalone files only (same pattern as `judge_demo.py` from earlier tonight).
  Never modify `solve()`, `modules.py`, `app.py`, `api.py`, or the React app to build
  this. No versioning scheme, no adapter layers — the fact that it's a separate file
  importing existing functions read-only *is* the backward-compatibility strategy.

## Working process with her — repeat per criterion

1. **Before discussing anything new, show her the current scorecard state** as a
   plain-text, sectioned summary (plain characters, no code, no jargon) — every
   criterion defined so far, one line each, plus any constants awaiting her review.
   This is so she can see the whole shape of the system at a glance before adding to
   it, and doesn't accidentally duplicate or contradict something that already exists.
   Example shape:

   ```
   CURRENT SCORECARD
   ==================
   Candidates per run: 100 seeds, one fixed brief

   Criteria defined:
     1. Seat height fit — chairs sit at a comfortable height for the stated
        user height. (status: built, needs your check on SEAT_HEIGHT_RATIO)

   Constants awaiting your review:
     - SEAT_HEIGHT_RATIO = 0.24  (rule-of-thumb: ideal seat height as a
       fraction of a person's height — not a cited source, please sanity-check)

   Not yet built (parked for later, don't build until asked):
     - Overhead/shelf clearance so a tall user doesn't bump their head
   ```

2. **Ask her what she wants to check next, in her own words.** Let her describe it
   loosely — she'll likely describe several special cases or exceptions at once.

3. **Find the one general rule underneath what she described.** Do not implement
   every exception she lists. If she says "the shelf near the bed should be lower for
   short people but the kitchen shelf can be higher because you don't lean on it" —
   the general rule is "overhead clearance scored against user height, per shelf
   zone" — not two hardcoded special cases. When you simplify what she said, say so
   explicitly and confirm she agrees with the simplification before building it.

4. **Scope exactly one criterion at a time.** Even if she describes three ideas in
   one sitting, implement and validate one, then move to the next — don't batch.

5. **Any new constant goes in the shared constants file**, commented, flagged for
   her review, as described above.

6. **After building, re-show the updated scorecard summary** (same format as step 1)
   so she can see what changed and confirm it matches what she meant.

## Do / Don't

- DO keep every criterion's `score_fn` a pure function of `(placed, context)` — no
  hidden state, no reaching into files that aren't passed in.
- DO keep criteria on the same 0-10 scale so they can be summed/weighted consistently.
- DO surface every new constant to her by name, value, and reasoning — never silently
  assume a number is fine.
- DO NOT implement a criterion she hasn't explicitly confirmed yet, even if it's an
  obvious next step (e.g. the shelf-clearance generalization below) — ask first.
- DO NOT let the criteria list grow branchy/special-cased. If a new ask looks like
  "criterion X, but different for case Y," look for the parameter that unifies X and Y
  before writing two functions.
- DO NOT touch `solve()`, `modules.py`, `app.py`, `api.py`, or the React app to build
  any of this.
- DO NOT introduce weight-assignment UI/discussion before 2+ criteria exist and are
  individually validated.

## Current state (as of hand-off)

**Criterion 1 — Seat height fit (scoped, not yet implemented in code):**
- Applies to any section with a chair-type module. Confirmed present in: **dining**
  (`chair_left` / `chair_right`, always) and **living** (`chair_left` when not using
  the sofa combo — verify whether `sofa` modules have `_seat_y()`-compatible
  segment/port data before assuming the same scorer works on them unmodified).
- Actual seat height: `solver._seat_y(chair_module) * 40` — the codebase's grid is
  fixed at 40cm/cell (documented in `plan_generator_RAG_v2.md`), and `_seat_y()`
  already exists in `solver.py` to compute the effective seat level from a chair
  module's geometry.
- Ideal seat height: `SEAT_HEIGHT_RATIO * user_height_cm`, `SEAT_HEIGHT_RATIO = 0.24`
  (rule-of-thumb, unverified — flag to her).
- Score: linear falloff from ideal within a tolerance constant (also unverified,
  also goes in the constants file), clipped to 0-10.
- `user_height_cm` is a new input, not yet wired into onboarding — for the POC it's
  just passed directly as a test value. Wiring it into the real questionnaire is
  explicitly out of scope until this criterion is validated.

**Noted for later — do not build yet, just remember to ask her:**
The height-matching *principle* generalizes beyond chairs — e.g. overhead/shelf
clearance so a tall user's head doesn't bump a shelf. When she's ready to add a
second criterion, this is a natural candidate to raise, but it was explicitly
deferred at hand-off — don't build it preemptively.
