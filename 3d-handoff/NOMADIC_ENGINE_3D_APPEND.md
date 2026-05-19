# NOMADIC_ENGINE.md — sections to append

> Open the main project's `NOMADIC_ENGINE.md`. Find §18 (Glossary) — it's
> the last numbered section. Append the four new glossary rows below to
> the existing glossary table, then append the entire §19 block after it.
> No conflicts expected: these are purely additive.

---

## Glossary rows to append at the end of §18

Add these rows to the bottom of the glossary table:

```markdown
| **D** | Section depth in unit cells (3D mode only). |
| **z_rule** | A `"first N"` / `"last N"` / `"middle N"` / `"full"` string defining a zone's depth-axis range (3D mode only). |
| **Face** | A 3D module's boundary plane. Six faces: `left` (x=0), `right` (x=w), `bottom` (y=0), `top` (y=h), `front` (z=0), `back` (z=d). |
| **3D port** | A face-cell midpoint where a line crosses the module's outer boundary in 3D. Generalizes the 2D edge-midpoint port. |
```

---

## §19 to append after the glossary

Append everything below (including the `---` separator):

---

## 19. 3D Mode — Volumetric Assembly

This section adds a depth axis to the prototype, producing a true 3D building from which the 2D section becomes one slice. The 3D mode runs **alongside** 2D (toggled in the UI) — the 2D system is untouched.

### 19.1 Coordinate frame

- `x` increases rightward (width), `y` increases upward (height), `z` increases into the depth axis (away from the section-view viewer).
- Origin `(0, 0, 0)` is at the **bottom-front-left** of any module or building.
- One unit cell = `CS = 1.0` on all three axes.
- The 2D section view is the `x-y` plane at some fixed `z`.

### 19.2 Module dimensions and the port rule in 3D

Modules become `w × h × d` voxels. The Port Rule extends naturally:

> **A line inside a 3D module may only cross the module's outer boundary at the
> midpoint of a face-cell. Nowhere else.**

For a `w × h × d` module, the six faces carry these port positions:

| Face   | Plane | Ports per face | Position formula                                              |
|--------|-------|----------------|---------------------------------------------------------------|
| left   | x = 0 | h · d          | `(0, y+0.5, z+0.5)`  for `y ∈ [0..h), z ∈ [0..d)`           |
| right  | x = w | h · d          | `(w, y+0.5, z+0.5)`  for `y ∈ [0..h), z ∈ [0..d)`           |
| bottom | y = 0 | w · d          | `(x+0.5, 0, z+0.5)`  for `x ∈ [0..w), z ∈ [0..d)`           |
| top    | y = h | w · d          | `(x+0.5, h, z+0.5)`  for `x ∈ [0..w), z ∈ [0..d)`           |
| front  | z = 0 | w · h          | `(x+0.5, y+0.5, 0)`  for `x ∈ [0..w), y ∈ [0..h)`           |
| back   | z = d | w · h          | `(x+0.5, y+0.5, d)`  for `x ∈ [0..w), y ∈ [0..h)`           |

**Total possible ports**: `2(wh + hd + wd)`. As in 2D, not all ports need be used — only those touched by lines.

### 19.3 Segments and closed circuit in 3D

- Segments are polylines of `(x, y, z)` tuples — exactly the 2D structure with one extra coordinate.
- Internal lines may take any direction in 3D space (axis-aligned, diagonal, or skew).
- The **Closed Circuit Rule is unchanged**: every line endpoint must connect to ≥ 1 other endpoint. T-junctions (degree 3) and higher-order junctions remain valid. Only degree-1 vertices are forbidden.
- The outer-boundary self-enforcement carries over: any line touching the section's outer perimeter has no partner → dangling end → automatically rejected.

### 19.4 Adjacency between 3D modules

Six face-pair cases instead of four:

| Module A face | Module B face | Trigger                          |
|---------------|---------------|----------------------------------|
| right         | left          | `A.x_off + A.w == B.x_off`       |
| left          | right         | `B.x_off + B.w == A.x_off`       |
| top           | bottom        | `A.y_off + A.h == B.y_off`       |
| bottom        | top           | `B.y_off + B.h == A.y_off`       |
| back          | front         | `A.z_off + A.d == B.z_off`       |
| front         | back          | `B.z_off + B.d == A.z_off`       |

For each, compute the 2D overlap rectangle on the shared face and verify the two modules' port sets on that rectangle are identical.

### 19.5 Zones in 3D

Zone definitions gain a `z_rule` alongside `x_rule` and `y_rule`. Same syntax (`"first N" / "last N" / "middle N" / "full"`). Zone size resolves to `(w, h, d)`; module filter checks all three dimensions.

**Locked decision:** every zone uses `z_rule: ["full"]`. The solver makes no depth-axis decisions, ever — it remains a 2D puzzle solver. Architectural variation along the depth axis lives inside each module's own 3D wireframe geometry, not in zone placement choices.

### 19.6 Module library strategy

The 2D library has ~54 modules. The 3D library is built in two waves:

1. **Auto-extrusion (Phase 1)**: every 2D module produces an `__ext`-suffixed 3D variant by stacking slice copies at z=0.5, 1.5, …, d-0.5 and connecting non-port vertices with depth-wires. Validates the pipeline end-to-end with no new content.
2. **Native 3D modules (Phase 6)**: hand-authored full-depth modules with arbitrary 3D wireframe geometry — pitched roofs with hip joints (one 3D apex point), corridors with archways, chairs facing each other across depth, tables with real legs at z=0 and z=d. Authored via `whd_segments_fn(w, h, d)` / `whd_ports_fn(w, h, d)` lambdas (mirroring the 2D `wh_*` pattern). Closed-circuit rule applies in 3D point-space.

### 19.7 Files

- `modules3d.py` — 3D module dict, `ZONES_3D`, extrusion utility.
- `solver3d.py` — `solve3d`, `check_adjacency_3d`, `check_circuit_3d`.
- `viewer3d.py` — 3D renderer (matplotlib mplot3d for v1; pluggable for plotly/pyvista/three.js later).
- `app.py` — top-level 2D/3D mode toggle. 2D branch unchanged.

The 2D files (`modules.py`, `solver.py`, `drawing.py`) remain untouched.
