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


def dwelling_sections_meta(spec: dict) -> list[dict]:
    """
    Return section metadata (type, d, W) without running any solver.
    Used for plan-view rendering where only dimensions matter.
    """
    shared_W : int   = spec.get("W", 9)
    results          : list[dict] = []
    d_offset : float = 0.0
    for fn in spec.get("functions", []):
        d = fn.get("d", 3)
        results.append({
            "type":     fn["type"],
            "d_offset": d_offset,
            "d":        d,
            "W":        shared_W,
        })
        d_offset += d
    return results


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
    3D dwelling assembler.

    Rules enforced:
    - Every section reports the same outer frame width (spec["W"]) so the
      structural envelope is uniform.  Interior modules solve at each section's
      natural inner width; extra space within the frame is left as an open bay.
    - Every non-last section uses the same corridor side.
    - Kitchen is always solved with corridor_right (only orientation its solver
      supports).
    - The last section may omit the corridor when spec["last_no_corridor"] is
      True (default False).
    """
    corridor_side      = spec.get("corridor_side", "right")
    corridor_w         = spec.get("corridor_w", 2)
    H                  = spec["H"]
    shared_W           = spec.get("W", 9)   # uniform outer frame width
    last_no_corridor   = spec.get("last_no_corridor", False)
    shared_corr        = f"corridor_{corridor_side}" if corridor_side != "none" else "none"

    functions = spec["functions"]
    results   : list[dict] = []
    d_offset  : float      = 0.0

    for i, fn in enumerate(functions):
        fn_type      = fn["type"]
        d            = fn.get("d", 3)
        seed         = fn.get("seed", 42)
        dining_style = fn.get("dining_style", "compact")
        num_chairs   = fn.get("num_chairs",   2)
        roof_style   = fn.get("roof_style",   "any")
        living_combo = fn.get("living_combo", "full")

        is_last = (i == len(functions) - 1)

        if is_last and last_no_corridor:
            fn_corridor = "none"
            fn_corr_w   = 0
        elif fn_type in _ALWAYS_CORR_RIGHT:
            fn_corridor = "corridor_right"
            fn_corr_w   = corridor_w
        else:
            fn_corridor = shared_corr
            fn_corr_w   = corridor_w if fn_corridor != "none" else 0

        # For dining, inner width depends on num_chairs and dining_style.
        # 1-chair always needs corridor_right so the table has a clean right boundary.
        if fn_type == "dining":
            if num_chairs == 1 and fn_corridor == "none":
                fn_corridor = "corridor_right"
                fn_corr_w   = corridor_w
            inner_w = (6 if dining_style == "compact" else 8) if num_chairs == 2 \
                      else (4 if dining_style == "compact" else 5)
        else:
            inner_w = _SECTION_INNER_W.get(fn_type, shared_W - fn_corr_w)
        fn_W = inner_w + fn_corr_w

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
            "W":        shared_W,   # uniform frame — all sections same width
            "H":        H,
            "placed":   placed,
        })
        d_offset += d

    return results
