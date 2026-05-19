# Module Authoring Workflow — Rhino → Python dict

> When a new 3D module is designed in Rhino and needs to be translated into a
> `MODULES_3D` entry, follow this workflow. The goal: zero ambiguity, no
> guessing, no back-and-forth.

This file is the contract between **you (Rhino author)** and **the
implementer (the person writing the Python module dict)**. If a Rhino model
arrives without satisfying the requirements below, the implementer should
push back rather than guess.

---

## Tier 1 — Best: structured coordinate export

The fastest, most accurate handoff is a **structured export**, not screenshots.

In Rhino, export one of:

- **Plain text file** (`.txt`), one polyline per line, vertices comma-separated:
  ```
  POLY  (0.5, 0.5, 0.5)  (1.5, 0.5, 0.5)  (1.5, 1.5, 0.5)  (0.5, 1.5, 0.5)  (0.5, 0.5, 0.5)
  POLY  (1.5, 0.5, 0.5)  (2.0, 0.5, 0.5)
  PORT  right  (2.0, 0.5, 0.5)
  ```
- **DXF / IGES file** — implementer parses via `ezdxf` / `rhino3dm`.
- **JSON** with explicit `segments` and `ports`:
  ```json
  {
    "id": "chair_left_3d_v1",
    "w": 2, "h": 2, "d": 2,
    "segments": [[[0.5,0.5,0.5],[1.5,0.5,0.5],...], ...],
    "ports": {"right": [[2.0,0.5,0.5],[2.0,0.5,1.5]], ...}
  }
  ```

**If you can do this, the views become reference material rather than the
primary source of truth, and the implementation lands first-try.**

---

## Tier 2 — Acceptable: views + coordinate table

If a structured export isn't available, send **all four views below per
module** AND a **vertex coordinate table**. Views alone are NOT sufficient
because:

- Diagonal endpoints land between grid lines → 0.5? 0.4? 1/3?
- Curves are NURBS in Rhino, polylines here → discretization unspecified.
- Ports can be ambiguous when a green dot sits near a face corner.

### Required views per module

| View | Camera | Shows |
|---|---|---|
| Front | Looking along +z | x-y plane geometry |
| Side  | Looking along +x | y-z plane geometry |
| Top   | Looking along -y (down) | x-z plane geometry |
| Iso   | Azimuth ≈ -55°, Elevation ≈ 20° | 3D check |

All four views must include:
- The module's **bounding box** (w × h × d) as wire grid lines at unit-cell intervals.
- The module's **local origin (0, 0, 0)** clearly marked (corner annotation or red dot).
- **Axis labels** (x→, y↑, z⤢ or similar).
- **Port markers** in a single agreed convention (green dot, as currently used).
- Crop tight to the bounding box — no extraneous geometry.

### Required views per section

Same four views (front / side / top / iso) of the **assembled section** with
all modules placed. Used by the implementer to verify module placement and
adjacency after coding.

### Required coordinate table

A simple Markdown or CSV table per module:

```
Module: roof_arch_3d_v1   (w=6, h=3, d=variable)

Vertices (module-local):
  V1: (1.5, 3.0, 0.5)        # top-bar left, front slice
  V2: (4.5, 3.0, 0.5)        # top-bar right, front slice
  V3: (0.0, 1.5, 0.5)        # left semicircle midpoint
  ...

Polylines (vertex sequences; closed if first==last):
  P1: V1 → V2 → V3a → V3b → ... (closed)   # front-slice profile
  P2: same vertices at z=d-0.5             # back-slice profile
  P3: V1 ↔ V1'                              # depth-wire at V1
  ...

Ports:
  right:  V_p1, V_p2
  left:   V_p3, V_p4
  bottom, top, front, back: (none)
```

---

## Tier 3 — Bare minimum (NOT recommended)

A single front view of the assembled section. Implementer will guess
module-internal structure and **must** ask follow-up questions before coding.
Curves and diagonals will need a coordinate table regardless.

---

## What I (the implementer) CANNOT recover from views alone

- **Curve discretization**: how many segments approximate a Rhino arc.
- **Sub-cell coordinates**: anything that lands between half-grid lines.
- **Coincident-vertex distinction**: when multiple polylines share a vertex,
  views can't tell which polylines start/end vs pass through.
- **Polyline ordering / closure**: whether `A→B→C→A` is one closed polyline or
  three open ones.
- **Per-face port assignment**: a dot near a corner could belong to either of
  two faces.
- **Module-local origin convention**: views can show geometry, but the
  origin/orientation could be flipped or shifted.

For any of the above, a coordinate table OR explicit annotation is required.

---

## Curve handling

Any non-axis-aligned curve must be specified as:

```
Curve: roof_arch left semicircle
  Type: semicircle
  Center: (1.5, 1.5)
  Radius: 1.5
  From angle: π/2 (top)
  To angle: 3π/2 (bottom)
  Discretization: N = 6 segments
```

Or as an explicit list of vertices (preferred — leaves no room for
interpretation).

---

## Closed-circuit sanity check (run before sending)

Before handing over a module, verify in Rhino:

1. **Every polyline endpoint either**:
   - Connects to another polyline endpoint at the exact same point (degree ≥ 2), OR
   - Sits at a declared port location.
2. **No "dangling" interior vertex** — every interior vertex has degree ≥ 2.
3. **Every port lies at a face-cell midpoint** — for a w×h×d module:
   - Left/right ports: `(0 or w, y+0.5, z+0.5)`
   - Bottom/top ports: `(x+0.5, 0 or h, z+0.5)`
   - Front/back ports: `(x+0.5, y+0.5, 0 or d)`
   - Any port off these positions is invalid.

If any of these checks fails, fix in Rhino first.

---

## The handoff template

When sending a new module, include this header:

```markdown
## Module: <name>

**Architectural identity:** <one sentence prose>
**Dimensions:** w=<>, h=<>, d=<> (or d=variable)
**Tier:** 1 (export) | 2 (views + table) | 3 (views only — last resort)
**Files attached:**
  - front view: <filename>
  - side view: <filename>
  - top view: <filename>
  - iso view: <filename>
  - coordinate table: <inline below, or attached file>
**Curves:** <list any non-polyline geometry and its discretization>
**Open questions:** <anything you're uncertain about>
```

For a new **section** assembly, also list:
- Which modules go where (column, row, zone)
- Any new fillers or filler-pass variants needed

---

## Why this contract matters

Each ambiguity in a view-based handoff is a coin-flip during translation.
Across 4 modules with ~10 polylines each, even 5% ambiguity per polyline
compounds to a high chance the implementation diverges from the design. The
Tier 1 export workflow eliminates this entirely; Tier 2 reduces it; Tier 3
guarantees a guessing round.

If you find yourself sending a Tier 3 handoff, ask whether 10 minutes of
Rhino scripting could produce a Tier 1 export and save an hour of
back-and-forth.
