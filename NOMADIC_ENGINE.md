# Nomadic Engine — Full Project Documentation

> This document is the authoritative reference for the Nomadic Engine project.
> It captures every design decision, axiom, rule, and implementation agreement
> reached during the design conversation. If context is lost, start here.

---

## 1. Project Overview

**Nomadic Engine** is a parametric section generator for an architectural dining space.
It works by assembling modular pieces — each a small 2D grid with lines drawn inside —
into a complete cross-sectional drawing. The assembly must satisfy two things:
a structural rule system (which zones must be present) and a geometric constraint
(all lines must form a closed circuit).

The output is a 2D section drawing. The engine picks module variants, places them
into zones, validates the result, and renders it.

---

## 2. Coordinate System & Dimensionality

- The prototype is **purely 2D**. No depth dimension.
- Each module occupies a rectangular region of **w** columns × **h** rows of unit cells.
- The coordinate origin `(0, 0)` is at the **bottom-left** of any module or section.
- `x` increases rightward, `y` increases upward.
- One unit cell = one grid square = `CS = 1.0` in drawing coordinates.

For the current prototype:
- Section dimensions: **W = 6, H = 6** (6 columns wide, 6 rows tall)

---

## 3. Core Axiom — The Port Rule

This is the single geometric rule that governs all modules.

> **A line inside a module may only cross the module's outer boundary at the
> midpoint of a boundary cell's edge. Nowhere else.**

These midpoints are called **ports**. They are the only legal entry/exit points
for lines at the outer edge of any module.

### Port positions for a w × h module

| Edge   | Count | Positions (local coordinates)                          |
|--------|-------|--------------------------------------------------------|
| Bottom | w     | `(0.5, 0), (1.5, 0), ..., (w−0.5, 0)`                |
| Top    | w     | `(0.5, h), (1.5, h), ..., (w−0.5, h)`                |
| Left   | h     | `(0, 0.5), (0, 1.5), ..., (0, h−0.5)`                |
| Right  | h     | `(w, 0.5), (w, 1.5), ..., (w, h−0.5)`                |

**Total ports** for a w × h module = `2w + 2h`.

### Example — chair_left (w=2, h=3): 10 possible ports
- Bottom: `(0.5,0)`, `(1.5,0)`
- Top: `(0.5,3)`, `(1.5,3)`
- Left: `(0,0.5)`, `(0,1.5)`, `(0,2.5)`
- Right: `(2,0.5)`, `(2,1.5)`, `(2,2.5)`

Not all ports need to be used — a module only uses the ports its lines actually touch.

---

## 4. Internal Line Freedom

Inside the module boundary, lines may go in **any direction** — horizontal, vertical,
or diagonal. There is no constraint on internal path.

- Lines are defined as sequences of `(x, y)` coordinate points (polylines).
- Lines may form **rectangles, loops, T-junctions, diagonals** — anything.
- Internal turning/junction points can be at interior cell-edge midpoints
  (e.g. `(0.5, 1.5)` inside a 2×3 module) or at any other coordinate.
- Lines can have **T-junctions** (3 lines meeting at one point) — valid as long
  as the full circuit is closed.

The grid is a **reference coordinate system only**. It does not constrain
internal line paths.

---

## 5. The Closed Circuit Rule

This is the **only validity condition** for a complete section assembly.

> **Every line endpoint must connect to exactly one other line endpoint.
> No dangling ends are allowed anywhere in the assembled section.**

### What this means in practice

**Between two adjacent modules sharing an edge:**
If module A has a line touching a shared boundary midpoint, module B must
also have a line touching that exact same midpoint. If A has no line there,
B must also have no line there. Any mismatch = a dangling end = invalid.

**At the outer boundary of the section:**
A line reaching the section's outer edge has no neighbouring module to connect
to. It would be a dangling end. Therefore the solver will never produce a
configuration where any module has a line touching the section's outer perimeter.
This is **self-enforcing** — no separate boundary rule is needed.

**Internal T-junctions:**
Three lines meeting at one interior point is valid, as long as the global
graph of all lines still forms one or more closed loops.

### Visual summary

```
Module A  |  Module B
          |
  ──────● | ●──────    ← valid: both have a line at the shared port
          |
  ──────● |            ← INVALID: A has a line, B does not → dangling end
          |
          | ●──────    ← INVALID: B has a line, A does not → dangling end
```

---

## 6. Drawing vs. Solver — Completely Separate Concerns

These two subsystems share no logic and must never be coupled.

### Solver (geometry-blind)
The solver only needs to know, for each module, **which boundary midpoints
have lines touching them on each edge**. This is a simple list per edge:

```python
module.ports = {
    "bottom": [(0.5, 0)],           # which bottom midpoints are used
    "top":    [(0.5, 3)],           # which top midpoints are used
    "left":   [],                   # none used
    "right":  [(2, 0.5)],           # which right midpoints are used
}
```

The solver uses this to check compatibility between adjacent modules and
to validate that the assembled section forms a closed circuit.
It never looks at internal line paths, diagonals, or any drawing data.

### Drawing (solver-blind)
The drawing system renders each module's lines using raw `(x, y)` coordinate
sequences. It knows nothing about validity or circuit closure. It just draws.

```python
module.segments = [
    [(0.5, 3), (0.5, 1.5)],                              # stem
    [(0.5, 1.5), (1.5, 1.5), (1.5, 0.5),
     (0.5, 0.5), (0.5, 1.5)],                            # rectangle loop
    [(1.5, 0.5), (2, 0.5)],                              # leg
]
```

### The only coupling
A line's endpoint at the module boundary must land on a valid port position.
That is all. Internal paths are invisible to the solver.

---

## 7. Module Data Structure

Each module variant is a dictionary (or object) with the following fields:

```python
{
    "id":       "chair_left_h3_v1",   # unique identifier
    "w":        2,                    # width in cells
    "h":        3,                    # height in cells
    "zone":     "chair_left",         # which zone type this belongs to
    "segments": [                     # list of polylines for drawing
        [(x1, y1), (x2, y2), ...],   # each polyline is a list of (x,y) points
        ...
    ],
    "ports": {                        # boundary midpoints used by lines
        "bottom": [...],             # list of (x, y) tuples
        "top":    [...],
        "left":   [...],
        "right":  [...],
    }
}
```

### Module naming convention
`{zone}_{h}_{variant}` — e.g. `chair_left_h3_v1`, `chair_left_h2_v1`, `table_h3_v1`

The `h` in the name encodes the module height, which must match the zone's
chosen y_rule. The variant number `v1`, `v2` etc. distinguishes different
line configurations for the same size.

---

## 8. Current Prototype Module Definitions

### `chair_left_h3_v1` (w=2, h=3)

**Active ports:**
- Top: `(0.5, 3)`
- Right: `(2, 0.5)`

**Line geometry:**
```
(0.5, 3)
   │  stem — vertical line down
(0.5, 1.5) ────── (1.5, 1.5)
   │    rectangle loop         │
(0.5, 0.5) ────── (1.5, 0.5) ──→ (2, 0.5)
                        leg
```

**Segments:**
```python
segments = [
    [(0.5, 3), (0.5, 1.5)],                              # stem
    [(0.5, 1.5), (1.5, 1.5), (1.5, 0.5),
     (0.5, 0.5), (0.5, 1.5)],                            # rectangle (closed)
    [(1.5, 0.5), (2, 0.5)],                              # leg to right port
]
```

**T-junctions** at `(0.5, 1.5)` (stem meets rectangle top-left) and
`(1.5, 0.5)` (leg meets rectangle bottom-right).

**Architectural reading:** The rectangle = chair seat body.
The stem going up = structural connection to ceiling/shelf above.
The leg going right = connection to the table beside it.

---

### `chair_right_h3_v1` (w=2, h=3)

Mirror image of `chair_left_h3_v1`.

**Active ports:**
- Top: `(1.5, 3)`
- Left: `(0, 0.5)`

**Segments (mirrored):**
```python
segments = [
    [(1.5, 3), (1.5, 1.5)],                              # stem
    [(1.5, 1.5), (0.5, 1.5), (0.5, 0.5),
     (1.5, 0.5), (1.5, 1.5)],                            # rectangle (closed)
    [(0.5, 0.5), (0, 0.5)],                              # leg to left port
]
```

---

### `table_h3_v1` (w=2, h=3)

**Active ports:**
- Left: `(0, 0.5)`
- Right: `(2, 0.5)`

**Line geometry:** ∇ (inverted triangle / V-shape)
```
       (0.5, 2) ─── (1.5, 2)    ← horizontal bar
          ╲               ╱
           ╲             ╱      ← two diagonals
            ╲           ╱
             (1, 0.5)           ← tip (T-junction)
            ╱           ╲
(0, 0.5) ←─               ─→ (2, 0.5)
  left port                   right port
```

**Segments:**
```python
segments = [
    [(0.5, 2), (1.5, 2)],                # top horizontal bar
    [(0.5, 2), (1, 0.5)],                # left diagonal to tip
    [(1.5, 2), (1, 0.5)],                # right diagonal to tip
    [(1, 0.5), (0, 0.5)],                # left leg to port
    [(1, 0.5), (2, 0.5)],                # right leg to port
]
```

**T-junction** at `(1, 0.5)` (tip — all four legs meet here).

**Architectural reading:** The bar = table surface/top.
The diagonals = structural legs/supports.
Left/right ports connect to the chairs on each side.

---

### `shelf_h3_v1` (w=W, h=3)

Spans the **full section width**. Geometry to be defined.
Ports will connect to the top ports of chairs and table below.

---

## 9. Zone System

A **zone** defines a region of the section and the module variants that may
be placed there. The solver picks exactly one module variant per zone.

### Zone data structure

```python
{
    "id":      "chair_left",
    "x_rule":  ["first 2"],                        # list of possible x rules
    "y_rule":  ["first 2", "first 3"],             # list of possible y rules
    "modules": ["chair_left_h2_v1",
                "chair_left_h3_v1"],               # available variants
}
```

### Position rule syntax

Each rule is a string describing a range relative to the section dimensions W and H:

| Rule       | Meaning                                         | Example (W=6)     |
|------------|-------------------------------------------------|-------------------|
| `first N`  | first N units from the start (left / bottom)    | `first 2` → 0–1  |
| `last N`   | last N units from the end (right / top)         | `last 2` → 4–5   |
| `middle N` | center N units                                  | `middle 2` → 2–3 |

`x_rule` governs column range. `y_rule` governs row range.

Rules are stored as **arrays** because a zone can accept different sizes.
The solver picks one x_rule value and one y_rule value, then filters the
module list to only those whose `w` and `h` match the chosen sizes.

### Size–module coupling

The solver picks `(x_rule, y_rule)` → derives `(w, h)` → filters modules by matching `w` and `h`.
A module is only eligible if its dimensions exactly match the resolved zone size.

---

## 10. Current Prototype Zones (W=6, H=6)

```python
ZONES = [
    {
        "id":      "chair_left",
        "x_rule":  ["first 2"],
        "y_rule":  ["first 2", "first 3"],
        "modules": ["chair_left_h2_v1", "chair_left_h3_v1"],
    },
    {
        "id":      "table",
        "x_rule":  ["middle 2"],
        "y_rule":  ["first 2", "first 3"],
        "modules": ["table_h2_v1", "table_h3_v1"],
    },
    {
        "id":      "chair_right",
        "x_rule":  ["last 2"],
        "y_rule":  ["first 2", "first 3"],
        "modules": ["chair_right_h2_v1", "chair_right_h3_v1"],
    },
    {
        "id":      "shelf",
        "x_rule":  ["first 6"],              # full width = first W
        "y_rule":  ["last 3"],
        "modules": ["shelf_h3_v1"],
    },
]
```

### Resolved positions (W=6, H=6)

| Zone        | Columns | Rows | w | h |
|-------------|---------|------|---|---|
| Chair Left  | 0–1     | 0–2  | 2 | 3 |
| Table       | 2–3     | 0–2  | 2 | 3 |
| Chair Right | 4–5     | 0–2  | 2 | 3 |
| Shelf       | 0–5     | 3–5  | 6 | 3 |

The bottom three zones sit side by side at the same row range.
The shelf sits on top spanning the full width.

---

## 11. Section Rules

Section rules are **logical constraints on zone presence**, evaluated at the
section level — above and independent of individual zone definitions.

They determine which zones must be fulfilled for the section to be valid.

### Rule syntax (agreed examples)

| Rule       | Meaning                                                  |
|------------|----------------------------------------------------------|
| `CL & CR`  | Both Chair Left AND Chair Right zones must be filled     |
| `T`        | Table zone must be filled                                |
| `RR \| RL` | Exactly one corridor zone must exist (right OR left)     |

Rules are logical expressions over zone IDs. The solver must satisfy all
section rules in addition to the closed circuit constraint.

### Corridors

Corridor zones (`RR` = Corridor Right, `RL` = Corridor Left) are conceptually
defined but **not included in the current prototype**. They are noted here
for completeness and future implementation.

### Current prototype section rules

```python
SECTION_RULES = ["CL & CR", "T"]
# Both chairs and table must exist. Shelf is always present (fixed zone).
```

---

## 12. Solver Logic

The solver has two responsibilities only:

1. **Satisfy section rules** — ensure the required zones are filled
2. **Produce a closed circuit** — all lines in the assembled section
   form closed loops with no dangling endpoints

### Solver algorithm (outline)

```
1. For each zone required by section rules:
   a. Choose an x_rule value from zone.x_rule array
   b. Choose a y_rule value from zone.y_rule array
   c. Resolve (w, h) from chosen rules and (W, H)
   d. Filter zone.modules to those with matching (w, h)
   e. Pick one module variant from the filtered list

2. Place all chosen modules at their resolved positions in the W×H grid

3. For each pair of adjacent modules (sharing an edge):
   a. Get the set of port positions on the shared edge from module A
   b. Get the set of port positions on the shared edge from module B
   c. Check they are identical → if not, reject and backtrack

4. Check that no module has a port touching the outer section boundary
   (automatically satisfied by the closed circuit check — any such port
   would be a dangling end)

5. Verify the full port graph forms one or more closed loops
   (every node has even degree, or equivalently, no node has degree 1)

6. If valid → output the placement. If not → backtrack and try another
   combination of module variants / size rules.
```

### Key insight about the outer boundary

The closed circuit rule makes the outer boundary self-enforcing:
any line reaching the section perimeter has no partner → dangling end →
automatically rejected. No separate "outer boundary" rule is needed.

---

## 13. Drawing System

The drawing system is **completely independent of the solver**. It receives
a solved placement (which module goes where) and renders it visually.

### Drawing pipeline

```
1. For each placed module:
   a. Get module's (x_offset, y_offset) in section coordinates
   b. For each segment in module.segments:
      - Translate all points by offset: (px + x_off, py + y_off)
      - Draw the polyline on the matplotlib axis
   c. Draw the module's w×h grid (faint lines) for reference
   d. Mark port positions with green dots

2. Draw the full section grid (faint outer lines)
3. Label zones
```

### Drawing rules (agreed)

- Module grid lines: thin, gray, for spatial reference only
- Lines (segments): drawn in a distinct colour (red in the sample)
- Port dots: green, drawn at boundary midpoints where lines touch edges
- Interior junction points (T-junctions): optionally marked
- No fills — everything is line-based

### Lines can be diagonal

Because segments are just `(x, y)` coordinate sequences, any line direction
is supported. The table's ∇ shape uses diagonal lines that are not
grid-aligned. This is fully valid for drawing.

---

## 14. Module Library

The module library is a separate display showing all available module
variants at unit scale, independent of any section assembly. It is for
human reference and design exploration.

Each module is rendered in its own subplot:
- Grid drawn faintly
- All segments drawn
- Ports marked with green dots
- Title shows module ID, w, h

---

## 15. Future Extensions (Not in Prototype)

These were discussed as conceptual extensions:

### More module variants
Any number of variants can be added for each zone. Each variant has the
same (w, h) but different internal line geometry. E.g.:
- `chair_left_h3_v2` — same size, different structural profile
- `chair_left_h2_v1` — shorter height variant

The solver will pick among valid variants to achieve circuit closure.

### Corridor zones
- `corridor_right` — vertical circulation on right side
- `corridor_left` — vertical circulation on left side
- Section rule: `RR | RL` — exactly one corridor
- Not implemented in prototype

### 3D extension
When depth (`d`) is added:
- Modules gain a third dimension
- Section becomes one slice through a volumetric assembly
- Port matching extends to the depth axis

### Variable section dimensions
The parametric zone system (first/last/middle N) already supports
different W and H values. The solver and zones scale automatically.

---

## 16. File Structure (Current)

```
sections/
├── app.py                  ← main Streamlit application
├── NOMADIC_ENGINE.md       ← this document
├── sample.jpg              ← reference image showing four prototype modules
                               assembled into a valid section
```

### app.py current state
The app currently has an incorrect module implementation (from before
the design conversation) and needs to be fully rebuilt according to this
document. The Streamlit UI structure (tabs, sliders) can be kept.

---

## 17. Implementation Checklist

When rebuilding `app.py`, implement in this order:

- [ ] Module data structure (id, w, h, zone, segments, ports)
- [ ] Define all current prototype module variants with correct geometry
- [ ] Zone data structure (id, x_rule, y_rule, modules)
- [ ] Zone resolver: x_rule/y_rule string → (col_start, col_end, row_start, row_end)
- [ ] Section rules evaluator
- [ ] Adjacency checker: given two placed modules sharing an edge, check port compatibility
- [ ] Circuit validator: check full port graph for closed loops
- [ ] Solver: backtracking search over zone assignments
- [ ] Drawing: render placed modules at section coordinates
- [ ] Module library: render all variants in a grid of subplots
- [ ] Streamlit UI: wire up controls (W, H, seed, section rules)

---

## 18. Glossary

| Term | Definition |
|------|-----------|
| **Module** | A w×h grid with internal lines. The building block of a section. |
| **Variant** | A specific line configuration for a given module size (e.g. v1, v2). |
| **Port** | A midpoint of a boundary cell's edge where a line is allowed to cross the module boundary. |
| **Active port** | (Avoided term) — a port that a line actually touches. Prefer: "port used by this module". |
| **Closed circuit** | The validity condition: all line endpoints connect, no dangling ends. |
| **Zone** | A parametrically positioned region of the section with a list of acceptable module variants. |
| **x_rule / y_rule** | A string like `"first 2"`, `"last 3"`, `"middle 2"` defining a zone's position/size. |
| **Section rule** | A logical expression over zone IDs (e.g. `CL & CR`) that the section must satisfy. |
| **Solver** | The algorithm that picks module variants per zone and validates the closed circuit. |
| **T-junction** | A point inside a module where three line segments meet. Valid as long as circuit closes. |
| **W, H** | Section width and height in unit cells. Prototype: W=6, H=6. |
| **CS** | Cell size in drawing coordinates. CS=1.0 in the prototype. |
