"""
Dwelling assembler — stitches multiple section solves into a single dwelling.

Each function in the spec is solved independently by solver.solve(), then
assigned a depth offset so sections stack linearly along the d-axis.
"""
from solver import solve
from solver3d import solve3d

# These section types ignore the global corridor_side and always use right.
_ALWAYS_CORR_RIGHT = {"kitchen", "bed"}

# Natural inner widths per section type.
# Using the shared dwelling W for kitchen/bath causes 20-35 gap cells that
# exhaust the backtracker.  Each section solves at its natural width instead.
_SECTION_INNER_W = {
    "dining":  6,   # compact 2-chair layout
    "kitchen": 4,   # cabinet block (3 cols) + 1 filler col
    "living":  7,   # compact full layout
    "bed":     4,   # bed module width
    "bath":    6,   # bath interior
}


def solve_dwelling_2d(spec: dict) -> list[dict]:
    """
    Solve each function in the spec and return placed-module results with depth offsets.

    spec keys:
      corridor_side  "left" | "right" | "none"
      corridor_w     int (2 or 4)
      W              int  — shared section width (total, including corridor)
      H              int  — shared section height
      functions      list of function dicts (see below)

    Function dict keys:
      type           "dining" | "kitchen" | "living" | "bed" | "bath"
      d              int  — depth of this section along the dwelling axis
      seed           int
      dining_style   "compact" | "spacious"
      roof_style     "any" | "plain" | "divided" | "pitched"
      living_combo   "full" | "sofa_tv"

    Returns a list of section result dicts — one per function, in order:
      type, d_offset, d, W, H, placed (list[dict] or None if solve failed)
    """
    corridor_side = spec.get("corridor_side", "right")
    corridor_w    = spec.get("corridor_w", 2)
    W             = spec["W"]
    H             = spec["H"]
    corridor      = f"corridor_{corridor_side}" if corridor_side != "none" else "none"

    results   : list[dict] = []
    d_offset  : float      = 0.0

    for fn in spec["functions"]:
        fn_type      = fn["type"]
        d            = fn.get("d", 3)
        seed         = fn.get("seed", 42)
        dining_style = fn.get("dining_style", "compact")
        roof_style   = fn.get("roof_style",   "any")
        living_combo = fn.get("living_combo", "full")

        fn_corridor = "corridor_right" if fn_type in _ALWAYS_CORR_RIGHT else corridor

        placed = solve(
            W, H, seed, fn_corridor, corridor_w,
            dining_style, roof_style,
            section=fn_type,
            living_combo=living_combo,
        )

        results.append({
            "type":     fn_type,
            "d_offset": d_offset,
            "d":        d,
            "W":        W,
            "H":        H,
            "placed":   placed,
        })
        d_offset += d

    return results


def solve_dwelling_3d(spec: dict) -> list[dict]:
    """
    3D version of solve_dwelling_2d.  Each section is solved at its natural width
    (from _SECTION_INNER_W) to avoid exponential gap-filling blowup in narrow
    section types like kitchen and bath.  The "W" in the spec is kept as a
    reference max-width but each section result carries its own W.
    """
    corridor_side = spec.get("corridor_side", "right")
    corridor_w    = spec.get("corridor_w", 2)
    H             = spec["H"]
    ref_W         = spec.get("W", 9)   # reference / max width (sidebar value)
    corridor      = f"corridor_{corridor_side}" if corridor_side != "none" else "none"

    results  : list[dict] = []
    d_offset : float      = 0.0

    for fn in spec["functions"]:
        fn_type      = fn["type"]
        d            = fn.get("d", 3)
        seed         = fn.get("seed", 42)
        dining_style = fn.get("dining_style", "compact")
        roof_style   = fn.get("roof_style",   "any")
        living_combo = fn.get("living_combo", "full")

        fn_corridor = "corridor_right" if fn_type in _ALWAYS_CORR_RIGHT else corridor
        fn_corr_w   = corridor_w if fn_corridor != "none" else 0

        # Use each section's natural inner width so gap-filling stays tractable.
        inner_w = _SECTION_INNER_W.get(fn_type, ref_W - fn_corr_w)
        fn_W    = inner_w + fn_corr_w

        raw = solve3d(
            fn_W, H, d, seed, fn_corridor, fn_corr_w,
            dining_style, roof_style,
            section=fn_type,
            living_combo=living_combo,
        )

        placed = (
            [{**p, "z_off": p["z_off"] + d_offset} for p in raw]
            if raw is not None else None
        )

        results.append({
            "type":     fn_type,
            "d_offset": d_offset,
            "d":        d,
            "W":        fn_W,
            "H":        H,
            "placed":   placed,
        })
        d_offset += d

    return results
