"""
Tunable numeric constants for the dwelling scorecard system.

Every constant here is a simplification / rule-of-thumb, not a rigorously
sourced figure. Each one is flagged for the primary stakeholder's review
before being trusted for real decisions — see .claude/skills/dwelling-scorecard/
for the process this belongs to.
"""

# ── Seat height fit criterion ───────────────────────────────────────────────

# Ideal seat height as a fraction of a person's total height.
# Rule of thumb, not from a cited ergonomics study. Spot-checked as a
# reasonable starting point (170cm person -> ~41cm seat, real dining chairs
# run ~45-46cm) but not independently verified — revisit if it stops feeling
# right once more layouts are scored against it.
SEAT_HEIGHT_RATIO = 0.24

# How far off (in cm) the actual seat height can be from the ideal before the
# score drops all the way to 0. Rule of thumb — not yet reviewed.
SEAT_HEIGHT_TOLERANCE_CM = 10.0

# Assumed real-world seat height per chair style class ("h2" = the "low
# chairs" style tag, "h3" = the "tall/bar chairs" style tag elsewhere in the
# codebase). These are placeholder estimates, not measured from anything —
# the module drawings are stylized 2D schematics on a coarse 40cm grid, not
# precise physical blueprints, so seat height can't be read off the drawing
# reliably. Please sanity-check both numbers.
SEAT_HEIGHT_BY_CLASS_CM = {
    "h2": 40.0,  # standard/lower dining chair — confirmed by stakeholder
    # "h3" is a placeholder pending a real split — see note below. Every h3
    # chair module in the catalog currently has the same h=3 dimension, so
    # there's no existing way to tell a 60cm chair apart from an 80cm one.
    # Stakeholder says there should be two tiers here (60cm / 80cm) — needs
    # either specific module IDs assigned to each tier, or the module
    # library extended to actually distinguish them. Using the midpoint as
    # a stopgap until that's resolved.
    "h3": 70.0,
}

# ── Table height fit criterion (B) ──────────────────────────────────────────

# Ideal table/work-surface height as a fraction of stature. Rule of thumb
# (commonly cited ballpark for comfortable seated table height), not a
# cited study — please sanity-check.
TABLE_HEIGHT_RATIO = 0.40

TABLE_HEIGHT_TOLERANCE_CM = 10.0

# Same caveat as chairs: the drawings don't encode real height, so this is
# a placeholder estimate per style class, not measured from anything.
TABLE_HEIGHT_BY_CLASS_CM = {
    "h2": 70.0,  # standard/lower dining table
    "h3": 95.0,  # bar/pub-height table
}

# ── Reach distance criterion (C) ────────────────────────────────────────────

# Max comfortable overhead reach as a fraction of stature. Rule of thumb
# (commonly cited ballpark for functional overhead reach), not measured.
MAX_REACH_RATIO = 1.20

# How far above that max (in cm) before the score drops to 0.
REACH_TOLERANCE_CM = 20.0

# ── Storage adequacy criterion (H, demo-only toggle) ────────────────────────

# Score given when the shelf is tagged as extra/wide storage vs. a plain
# shelf, only checked when the person has said they want extra storage.
# Not a measurement — just a simple placeholder rule.
STORAGE_ADEQUATE_SCORE = 10.0
STORAGE_INADEQUATE_SCORE = 4.0
