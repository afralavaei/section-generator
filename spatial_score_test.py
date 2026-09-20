"""
EXPERIMENTAL / STANDALONE TEST — NOT wired into the production pipeline.

Prototype for the "Occupant-Centric Spatial Perception" proposal (ray-cast
V_open / R_vh / E_reach metrics + composite Spatial Score, used to rank
multi-seed candidates from solve3d()).

This file only *imports* from solver3d.py / modules3d.py — it never edits
them, and nothing in the real solver pipeline calls into this file. Run it
directly:

    python spatial_score_test.py
    python spatial_score_test.py --seeds 24 --section dining --profile all

--------------------------------------------------------------------------
ASSUMPTIONS THAT NEED TEAM SIGN-OFF (search "ASSUMPTION" below):

1. No cell-to-meters scale constant exists anywhere in this codebase today
   (checked claude.md, DWELLING_SPEC.md, drawing.py, viewer3d.py). The
   proposal's "0.8m" reach radius and "1.1m" eye height are hard-coded in
   real-world units, so CELL_TO_M below is a guess (0.3 m/cell, i.e. a
   2-cell-wide chair ~= 0.6m) — needs confirming against the real Rhino
   module dimensions before this number means anything.

2. There is no fabric-membrane mesh anywhere in modules.py/modules3d.py —
   every module is a wireframe polyline (rib/furniture edges only). The
   proposal's alpha=0.4 fabric layer has nothing to attenuate through in
   the current data model. This script APPROXIMATES the membrane as the
   section's own outer bounding-box envelope: the 4 walls and the
   ceiling/roof are alpha=0.4 fabric, the floor is alpha=1.0 solid (same
   as structure — you don't see through the deck). Real furniture/rib
   segments are treated as fully opaque (alpha=1.0), per the proposal's
   own "solid structural frames" rule — this part of the data model
   already exists and needed no approximation.

3. Geometry is wireframe (1D polylines in 3D), not solid meshes, so there
   is nothing to do classic ray-triangle intersection against. Instead
   each rib/furniture line is treated as a thin capsule (SEG_RADIUS_CELLS)
   and rays are stepped numerically (RAY_STEP_CELLS), checking distance to
   the nearest segment at each step. This matches the proposal's own
   framing ("discrete ray sum") rather than inventing a meshing step.

4. "Required functional modules" for E_reach are defined per-section in
   REQUIRED_ZONES below. Only "dining" is populated (table + both chairs) —
   extend this dict before testing other sections.
--------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field

import numpy as np

from solver3d import solve3d
from modules3d import MODULES_3D, get_segments_3d

# ── Tunable constants (all flagged assumptions live here, nowhere else) ──────

CELL_TO_M = 0.3          # ASSUMPTION #1 — see module docstring.
EYE_HEIGHT_M = 1.1        # from the proposal, seated eye height.
STRUCTURE_ALPHA = 1.0     # opaque rib/furniture segments.
FABRIC_ALPHA = 0.4        # approximated envelope crossing — ASSUMPTION #2.
SEG_RADIUS_CELLS = 0.12   # capsule radius around each structural line.
RAY_STEP_CELLS = 0.06     # numerical march step.
N_RAYS = 320              # Fibonacci-sphere sample count.
REACH_RADIUS_M = 0.8
HORIZONTAL_ELEV_DEG = 25.0   # |elevation| below this = "horizontal" ray
VERTICAL_ELEV_DEG = 60.0     # |elevation| above this = "vertical" ray

REACH_RADIUS_CELLS = REACH_RADIUS_M / CELL_TO_M
EYE_HEIGHT_CELLS = EYE_HEIGHT_M / CELL_TO_M

# ASSUMPTION #4 — only dining populated; extend per section before reuse.
REQUIRED_ZONES = {
    "dining": {"table", "chair_left", "chair_right"},
}
VANTAGE_ZONE_PRIORITY = {
    "dining": ["chair_left", "chair_right"],
}

# Weight presets straight from the proposal's "Composite Scoring" section.
WEIGHT_PROFILES = {
    "retreat_privacy":   (0.2, 0.6, 0.2),   # w1=V_open, w2=R_vh, w3=E_reach
    "openness_research": (0.6, 0.2, 0.2),
    "task_workstation":  (0.2, 0.2, 0.6),
}


# ── Geometry helpers ──────────────────────────────────────────────────────────

@dataclass
class Candidate:
    seed: int
    placed: list
    W: int
    H: int
    D: int
    seg_starts: np.ndarray = field(repr=False)
    seg_ends: np.ndarray = field(repr=False)
    vantage: np.ndarray = field(repr=False)


def module_world_segments(p: dict) -> list[np.ndarray]:
    """World-space polylines for one placed module (empty list if none)."""
    mod = MODULES_3D[p["module_id"]]
    segs = get_segments_3d(mod, p["w"], p["h"], p["d"])
    off = np.array([p["x_off"], p["y_off"], p["z_off"]], dtype=float)
    return [np.asarray(seg, dtype=float) + off for seg in segs]


def module_centroid(p: dict) -> np.ndarray:
    segs = module_world_segments(p)
    if segs:
        pts = np.concatenate(segs, axis=0)
        return pts.mean(axis=0)
    # empty-segment modules (fillers) — fall back to bounding-box center
    off = np.array([p["x_off"], p["y_off"], p["z_off"]], dtype=float)
    return off + np.array([p["w"], p["h"], p["d"]], dtype=float) / 2.0


def build_segment_arrays(placed: list) -> tuple[np.ndarray, np.ndarray]:
    """Flatten every placed module's polylines into (starts, ends) segment
    pairs for vectorized point-to-segment distance queries."""
    starts, ends = [], []
    for p in placed:
        for line in module_world_segments(p):
            for a, b in zip(line[:-1], line[1:]):
                starts.append(a)
                ends.append(b)
    if not starts:
        return np.zeros((0, 3)), np.zeros((0, 3))
    return np.array(starts), np.array(ends)


def pick_vantage(placed: list, section: str) -> np.ndarray | None:
    """Seated eye position at a primary seat/workstation module."""
    priority = VANTAGE_ZONE_PRIORITY.get(section, [])
    by_zone = {}
    for p in placed:
        zone = MODULES_3D[p["module_id"]].get("zone")
        by_zone.setdefault(zone, []).append(p)
    for zone in priority:
        if zone in by_zone:
            p = by_zone[zone][0]
            c = module_centroid(p)
            return np.array([c[0], p["y_off"] + EYE_HEIGHT_CELLS, c[2]])
    return None


# ── Ray casting ────────────────────────────────────────────────────────────────

def fibonacci_sphere(n: int) -> np.ndarray:
    """n roughly-uniform unit directions over the full sphere."""
    i = np.arange(n)
    ga = math.pi * (3.0 - math.sqrt(5.0))
    y = 1.0 - (i / max(n - 1, 1)) * 2.0
    r = np.sqrt(np.clip(1.0 - y * y, 0.0, None))
    theta = ga * i
    x = np.cos(theta) * r
    z = np.sin(theta) * r
    return np.stack([x, y, z], axis=1)


def envelope_exit_distance(vantage: np.ndarray, direction: np.ndarray,
                            W: float, H: float, D: float) -> tuple[float, str]:
    """Distance from `vantage` to where the ray exits the (0,W)x(0,H)x(0,D)
    envelope box, plus which face it crossed. The floor (y=0) is a distinct
    face from the other five — see `FACE_ALPHA` in cast_ray()."""
    bounds = (W, H, D)
    best = None
    best_face = "ceiling"
    for axis in range(3):
        d = direction[axis]
        if abs(d) < 1e-9:
            continue
        for target in (0.0, bounds[axis]):
            t = (target - vantage[axis]) / d
            if t <= 1e-6:
                continue
            p = vantage + direction * t
            ok = True
            for a2 in range(3):
                if a2 == axis:
                    continue
                if not (-1e-6 <= p[a2] <= bounds[a2] + 1e-6):
                    ok = False
                    break
            if ok and (best is None or t < best):
                best = t
                best_face = "floor" if (axis == 1 and target == 0.0) else "wall_or_ceiling"
    return (best, best_face) if best is not None else (max(bounds), "ceiling")


def min_dist_to_segments(point: np.ndarray, seg_starts: np.ndarray,
                          seg_ends: np.ndarray) -> float:
    if len(seg_starts) == 0:
        return math.inf
    seg_vec = seg_ends - seg_starts
    seg_len2 = np.einsum("ij,ij->i", seg_vec, seg_vec)
    seg_len2 = np.where(seg_len2 < 1e-12, 1e-12, seg_len2)
    t = np.einsum("ij,ij->i", point - seg_starts, seg_vec) / seg_len2
    t = np.clip(t, 0.0, 1.0)
    proj = seg_starts + t[:, None] * seg_vec
    return float(np.linalg.norm(point - proj, axis=1).min())


def cast_ray(vantage: np.ndarray, direction: np.ndarray,
             seg_starts: np.ndarray, seg_ends: np.ndarray,
             W: float, H: float, D: float) -> float:
    """Returns the ray's openness score in [0, 1]: the intensity-weighted
    fraction of the envelope-exit distance the ray reaches unattenuated.

    Envelope faces are not uniform: the floor is solid (alpha=1.0, same as
    structure — you don't see through the deck), the four walls and the
    ceiling/roof are the fabric membrane (alpha=0.4)."""
    t_env, exit_face = envelope_exit_distance(vantage, direction, W, H, D)
    t = 0.0
    intensity = 1.0
    inside_blocker = False
    integral = 0.0
    while t < t_env and intensity > 0.01:
        p = vantage + direction * t
        dist = min_dist_to_segments(p, seg_starts, seg_ends)
        blocked = dist < SEG_RADIUS_CELLS
        if blocked and not inside_blocker:
            intensity *= (1.0 - STRUCTURE_ALPHA)
            inside_blocker = True
        elif not blocked:
            inside_blocker = False
        integral += intensity * RAY_STEP_CELLS
        t += RAY_STEP_CELLS
    if intensity > 0.01:
        # ray survived to the envelope — floor is solid, walls/ceiling are fabric
        exit_alpha = STRUCTURE_ALPHA if exit_face == "floor" else FABRIC_ALPHA
        intensity *= (1.0 - exit_alpha)
        integral += intensity * RAY_STEP_CELLS
        t_env += RAY_STEP_CELLS
    return integral / t_env if t_env > 0 else 0.0


# ── Metrics ────────────────────────────────────────────────────────────────────

def evaluate_candidate(cand: Candidate, section: str) -> dict | None:
    if cand.vantage is None:
        return None
    directions = fibonacci_sphere(N_RAYS)
    scores = np.array([
        cast_ray(cand.vantage, d, cand.seg_starts, cand.seg_ends, cand.W, cand.H, cand.D)
        for d in directions
    ])
    elevation_deg = np.degrees(np.arcsin(np.clip(directions[:, 1], -1.0, 1.0)))
    horiz_mask = np.abs(elevation_deg) < HORIZONTAL_ELEV_DEG
    vert_mask = np.abs(elevation_deg) > VERTICAL_ELEV_DEG

    v_open = float(scores.mean())
    blockage = 1.0 - scores
    horiz_block = float(blockage[horiz_mask].mean()) if horiz_mask.any() else 0.0
    vert_block = float(blockage[vert_mask].mean()) if vert_mask.any() else 1e-6
    r_vh = horiz_block / max(vert_block, 1e-6)
    r_vh_norm = r_vh / (1.0 + r_vh)

    required = [p for p in cand.placed
                if MODULES_3D[p["module_id"]].get("zone") in REQUIRED_ZONES.get(section, set())]
    if required:
        dists = [np.linalg.norm(module_centroid(p) - cand.vantage) for p in required]
        within = sum(1 for d in dists if d <= REACH_RADIUS_CELLS)
        e_reach = within / len(required)
    else:
        e_reach = 0.0

    result = {
        "seed": cand.seed,
        "V_open": round(v_open, 4),
        "R_vh_raw": round(r_vh, 4),
        "R_vh_norm": round(r_vh_norm, 4),
        "E_reach": round(e_reach, 4),
        "horiz_blockage": round(horiz_block, 4),
        "vert_blockage": round(vert_block, 4),
    }
    for name, (w1, w2, w3) in WEIGHT_PROFILES.items():
        result[f"score_{name}"] = round(w1 * v_open + w2 * r_vh_norm + w3 * e_reach, 4)
    return result


# ── Candidate generation ──────────────────────────────────────────────────────

def generate_candidates(section: str, n_seeds: int, W: int, H: int, D: int,
                         dining_style: str, roof_style: str,
                         corridor: str, corridor_w: int) -> list[Candidate]:
    out = []
    for seed in range(n_seeds):
        placed = solve3d(W, H, D, seed, corridor, corridor_w,
                          dining_style, roof_style, section=section)
        if placed is None:
            continue
        seg_starts, seg_ends = build_segment_arrays(placed)
        vantage = pick_vantage(placed, section)
        out.append(Candidate(seed, placed, W, H, D, seg_starts, seg_ends, vantage))
    return out


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--section", default="dining", choices=["dining"],
                     help="Only 'dining' has REQUIRED_ZONES/vantage config so far.")
    ap.add_argument("--seeds", type=int, default=16, help="Seeds 0..N-1 to try.")
    ap.add_argument("--w", type=int, default=8, help="Section W (compact 2-chair default incl. corridor).")
    ap.add_argument("--h", type=int, default=8)
    ap.add_argument("--d", type=int, default=3)
    ap.add_argument("--dining-style", default="compact")
    ap.add_argument("--roof-style", default="any")
    ap.add_argument("--corridor", default="corridor_right",
                     choices=["corridor_right", "corridor_left", "none"])
    ap.add_argument("--corridor-w", type=int, default=2)
    ap.add_argument("--profile", default="all",
                     choices=["all", *WEIGHT_PROFILES.keys()])
    ap.add_argument("--json-out", default=None, help="Optional path to dump full results as JSON.")
    args = ap.parse_args()

    candidates = generate_candidates(
        args.section, args.seeds, args.w, args.h, args.d,
        args.dining_style, args.roof_style, args.corridor, args.corridor_w,
    )
    print(f"solve3d produced {len(candidates)}/{args.seeds} valid layouts "
          f"for section={args.section} W={args.w} H={args.h} D={args.d}\n")

    results = []
    for cand in candidates:
        r = evaluate_candidate(cand, args.section)
        if r is None:
            print(f"  seed {cand.seed}: no vantage module found (zone missing) — skipped")
            continue
        results.append(r)

    if not results:
        print("No candidates could be evaluated — nothing to rank.")
        return

    header = (f"{'seed':>4} {'V_open':>8} {'R_vh':>8} {'R_vh_n':>8} {'E_reach':>8}"
              + "".join(f" {'score_' + k:>22}" for k in WEIGHT_PROFILES))
    print(header)
    print("-" * len(header))
    for r in sorted(results, key=lambda x: x["seed"]):
        line = (f"{r['seed']:>4} {r['V_open']:>8.3f} {r['R_vh_raw']:>8.3f} "
                f"{r['R_vh_norm']:>8.3f} {r['E_reach']:>8.3f}")
        for k in WEIGHT_PROFILES:
            line += f" {r[f'score_{k}']:>22.3f}"
        print(line)

    print()
    profiles = WEIGHT_PROFILES.keys() if args.profile == "all" else [args.profile]
    for name in profiles:
        best = max(results, key=lambda r: r[f"score_{name}"])
        print(f"Best for '{name}': seed {best['seed']} "
              f"(score={best[f'score_{name}']:.3f}, "
              f"V_open={best['V_open']:.3f}, R_vh={best['R_vh_raw']:.3f}, "
              f"E_reach={best['E_reach']:.3f})")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nFull results written to {args.json_out}")


if __name__ == "__main__":
    main()
