# Plan Generator RAG v2 — Nomadic Dwelling

---

## 1. System Purpose

This system generates a precise, furniture-informed dwelling plan on a rectangular grid for use in Grasshopper. It is controlled through a large language model that interprets user prompts and returns structured JSON. The JSON is then used to generate a visual plan in Grasshopper.

The plan is derived from the section module system. Column widths in the dining zone are fixed by section module rules and must not be invented by the model. Zone depths are computed from standard furniture plan dimensions using the selected cell size. The system maintains five functional zones as full-width horizontal bands.

The system must remain constrained, modular, and directly usable by Grasshopper without interpretation or correction.

---

## 2. Spatial Model

The dwelling is a rectangular grid of square cells.

Each layout consists of:
- A chosen base cell size
- A grid width determined by the dining style and corridor choice
- A grid height equal to the sum of all zone depths
- Five functional zones stacked vertically as full-width horizontal bands
- An optional corridor strip running the full height of the plan

The five required zones are: **dining, bedroom, kitchen, bathroom, work**

Each zone occupies one continuous full-width horizontal band. Zones cannot overlap, cannot leave gaps, and cannot be split.

The **grid width is not freely chosen by the model**. It is determined by:

```
grid_width = dining_cols + corridor_cols
```

Where:
- dining_cols = 6 (compact) or 8 (spacious)
- corridor_cols = 0 (no corridor), 2 (standard corridor), or 4 (spacious corridor)

---

## 3. Cell Size

The base cell is the modular planning unit. Choose from this fixed set only:

**20 cm / 30 cm / 40 cm / 60 cm / 80 cm**

No other value is allowed.

Choose the cell size that best supports:
1. The standard furniture dimensions used in the section (chair width = 2 cells, table width = 2 cells)
2. The requested dwelling area
3. Occupancy requirements

The preferred default cell size for dining-based layouts is **40 cm** unless area or occupancy constraints require otherwise.

---

## 4. Corridor

The corridor is a vertical strip running the full height of the plan. It passes through every zone simultaneously. It is not a separate horizontal zone.

Corridor placement:
- `"none"` — no corridor, corridor_cols = 0
- `"left"` — corridor occupies the leftmost columns
- `"right"` — corridor occupies the rightmost columns

Corridor width:
- Standard: 2 cells
- Spacious: 4 cells

The corridor does not affect zone row counts. It only affects column positions and grid width.

---

## 5. Dining Zone — Column Layout

The column layout for the dining zone is **fixed by the section module system**. The model must not alter these column counts or widths.

### 5.1 Compact Dining — dining_cols = 6

Layout: `[chair_left: 2] [table: 2] [chair_right: 2]`

| Element | col_start | col_end | width |
|---|---|---|---|
| chair_left | 0 | 1 | 2 cells |
| table | 2 | 3 | 2 cells |
| chair_right | 4 | 5 | 2 cells |

No gap columns. Chairs sit flush against the table in the section.

### 5.2 Spacious Dining — dining_cols = 8

Layout: `[chair_left: 2] [gap: 1] [table: 2] [gap: 1] [chair_right: 2]`

| Element | col_start | col_end | width |
|---|---|---|---|
| chair_left | 0 | 1 | 2 cells |
| gap_left | 2 | 2 | 1 cell |
| table | 3 | 4 | 2 cells |
| gap_right | 5 | 5 | 1 cell |
| chair_right | 6 | 7 | 2 cells |

Gap columns represent circulation space beside the seated person.

### 5.3 Column Positions With Corridor

**Corridor right** — dining columns stay at 0-based index, corridor follows:

| Style | dining cols | corridor_col_start | corridor_col_end | grid_width |
|---|---|---|---|---|
| compact + corr standard | 0–5 | 6 | 7 | 8 |
| compact + corr spacious | 0–5 | 6 | 9 | 10 |
| spacious + corr standard | 0–7 | 8 | 9 | 10 |
| spacious + corr spacious | 0–7 | 8 | 11 | 12 |

**Corridor left** — all dining column indices shift right by corridor_cols:

| Style | corridor_col_start | corridor_col_end | dining col offset | grid_width |
|---|---|---|---|---|
| compact + corr standard | 0 | 1 | +2 | 8 |
| compact + corr spacious | 0 | 3 | +4 | 10 |
| spacious + corr standard | 0 | 1 | +2 | 10 |
| spacious + corr spacious | 0 | 3 | +4 | 12 |

When corridor is on the left, add corridor_cols to every dining column index listed in sections 5.1 and 5.2.

---

## 6. Dining Zone — Plan Depth

The dining zone depth is computed from standard furniture plan dimensions. It is not freely allocated.

Standard dimensions:
- Dining chair seat depth (in plan): **40 cm** (circulation embedded per section 15)
- Dining table depth (in plan, short side): **80 cm**

Formula:
```
chair_rows = ceil(40 / cell_size)
table_rows = ceil(80 / cell_size)
dining_depth_rows = chair_rows + table_rows + chair_rows
```

Always round up. Never round down.

Reference values per cell size:

| cell_size | chair_rows | table_rows | dining_depth_rows | depth (cm) |
|---|---|---|---|---|
| 20 cm | 2 | 4 | 8 | 160 cm |
| 30 cm | 2 | 3 | 7 | 210 cm |
| 40 cm | 1 | 2 | 4 | 160 cm |
| 60 cm | 1 | 2 | 6 | 360 cm |
| 80 cm | 1 | 1 | 3 | 240 cm |

The model must use these exact values. The dining zone row count is not a free variable.

---

## 7. Other Zones — Row Allocation

Bedroom, kitchen, bathroom, and work zones use row-based allocation. They span the full grid width (including behind the corridor strip). More precise column layouts for these zones will be added in future versions.

### General sizing tendencies

- **bathroom**: usually the smallest zone
- **kitchen**: small to moderate
- **work**: moderate; increases if user requests it
- **bedroom**: scales with occupancy

### Bedroom sizing by occupancy

Size the bedroom so it could plausibly accommodate the required beds:
- 1 occupant: 1 single bed (90 cm × 200 cm)
- 2 occupants: 2 single beds or 1 double (140 cm × 200 cm)
- 4 occupants: 4 single beds or equivalent

Convert bed dimensions to rows using:
```
rows = ceil(dimension / cell_size)
```
Add at least 1 extra row for circulation.

### Dining row ordering

Dining occupies 4 rows (at cell_size=40) computed in section 6. It must be placed first (start_row = 0) unless the user specifies a different zone order.

### Zone row sum constraint

The sum of all zone row counts must equal grid_height_cells exactly. No gaps. No overlaps. First zone starts at row 0. Last zone ends at row grid_height_cells - 1.

---

## 8. Area Calculation

```
total_area_m2 = (grid_width_cells × grid_height_cells × cell_size²) / 10000
```

Cell size is in centimetres. Divide by 10000 to convert cm² to m².

If the user specifies an area target, choose zone depths and cell size to hit it. Dining zone depth is fixed — adjust other zone depths to meet the area target.

---

## 9. Zone Ordering

The order of zones is not fixed. The model may reorder them based on:
- User priorities
- Logical functional grouping (bathroom adjacent to bedroom or kitchen)
- Area efficiency

However, the dining zone always determines the column structure regardless of its row position.

---

## 10. Occupancy Rules

Occupancy is always provided by the user. Never infer a different number.

Occupancy affects bedroom, dining, kitchen, and work zone sizing. Bathroom scales slightly with occupancy.

---

## 11. Validity Conditions

A valid output must satisfy all of the following:

- JSON is valid
- cell_size is one of: 20, 30, 40, 60, 80
- all five zones appear exactly once
- dining_style is "compact" or "spacious"
- corridor_side is "none", "left", or "right"
- corridor_cols matches the stated corridor style (0, 2, or 4)
- grid_width_cells = dining_cols + corridor_cols
- dining_depth_rows matches the formula in section 6 for the chosen cell_size
- column indices for chair_left, table, chair_right (and gaps if spacious) are correct
- corridor column indices are correct for the stated side
- all zone start/end rows are integers
- sum of all zone row counts = grid_height_cells
- no overlap and no gap between zones
- first zone starts at row 0, last zone ends at grid_height_cells - 1
- total_area_m2 is correctly calculated

---

## 12. Forbidden Behaviors

The model must not:
- Invent a dining_cols value other than 6 (compact) or 8 (spacious)
- Freely allocate dining zone depth — it must use the formula in section 6
- Use a cell size outside the allowed set
- Output overlapping zones
- Output gaps between zones
- Output a grid_width that does not match dining_cols + corridor_cols
- Ignore occupancy
- Omit any of the five zones
- Output column indices that do not match sections 5.1, 5.2, and 5.3

---

## 13. JSON Schema

```json
{
  "cell_size": integer (20|30|40|60|80),
  "grid_width_cells": integer,
  "grid_height_cells": integer,
  "total_area_m2": string,

  "dining_style": "compact" | "spacious",
  "corridor_side": "none" | "left" | "right",
  "corridor_cols": integer (0|2|4),

  "corridor_col_start": integer | null,
  "corridor_col_end": integer | null,

  "dining_col_start": integer,
  "dining_col_end": integer,

  "chair_left_col_start": integer,
  "chair_left_col_end": integer,

  "gap_left_col_start": integer | null,
  "gap_left_col_end": integer | null,

  "table_col_start": integer,
  "table_col_end": integer,

  "gap_right_col_start": integer | null,
  "gap_right_col_end": integer | null,

  "chair_right_col_start": integer,
  "chair_right_col_end": integer,

  "dining_chair_rows": integer,
  "dining_table_rows": integer,

  "dining_start_row": integer,
  "dining_end_row": integer,

  "kitchen_start_row": integer,
  "kitchen_end_row": integer,

  "bathroom_start_row": integer,
  "bathroom_end_row": integer,

  "bedroom_start_row": integer,
  "bedroom_end_row": integer,

  "work_start_row": integer,
  "work_end_row": integer
}
```

Null values are used for fields that do not apply (e.g. gap columns when dining_style is "compact", corridor fields when corridor_side is "none").

---

## 14. Example Outputs

### Example A — Compact dining, no corridor, 2 occupants, ~20 m²

```json
{
  "cell_size": 40,
  "grid_width_cells": 6,
  "grid_height_cells": 21,
  "total_area_m2": "20.16",

  "dining_style": "compact",
  "corridor_side": "none",
  "corridor_cols": 0,

  "corridor_col_start": null,
  "corridor_col_end": null,

  "dining_col_start": 0,
  "dining_col_end": 5,

  "chair_left_col_start": 0,
  "chair_left_col_end": 1,
  "gap_left_col_start": null,
  "gap_left_col_end": null,
  "table_col_start": 2,
  "table_col_end": 3,
  "gap_right_col_start": null,
  "gap_right_col_end": null,
  "chair_right_col_start": 4,
  "chair_right_col_end": 5,

  "dining_chair_rows": 1,
  "dining_table_rows": 2,

  "dining_start_row": 0,
  "dining_end_row": 3,
  "kitchen_start_row": 4,
  "kitchen_end_row": 7,
  "bathroom_start_row": 8,
  "bathroom_end_row": 10,
  "bedroom_start_row": 11,
  "bedroom_end_row": 17,
  "work_start_row": 18,
  "work_end_row": 20
}
```

### Example B — Spacious dining, corridor right (standard), 4 occupants, ~28 m²

```json
{
  "cell_size": 40,
  "grid_width_cells": 10,
  "grid_height_cells": 28,
  "total_area_m2": "44.8",

  "dining_style": "spacious",
  "corridor_side": "right",
  "corridor_cols": 2,

  "corridor_col_start": 8,
  "corridor_col_end": 9,

  "dining_col_start": 0,
  "dining_col_end": 7,

  "chair_left_col_start": 0,
  "chair_left_col_end": 1,
  "gap_left_col_start": 2,
  "gap_left_col_end": 2,
  "table_col_start": 3,
  "table_col_end": 4,
  "gap_right_col_start": 5,
  "gap_right_col_end": 5,
  "chair_right_col_start": 6,
  "chair_right_col_end": 7,

  "dining_chair_rows": 1,
  "dining_table_rows": 2,

  "dining_start_row": 0,
  "dining_end_row": 3,
  "kitchen_start_row": 4,
  "kitchen_end_row": 8,
  "bathroom_start_row": 9,
  "bathroom_end_row": 11,
  "bedroom_start_row": 12,
  "bedroom_end_row": 22,
  "work_start_row": 23,
  "work_end_row": 27
}
```

### Example C — Compact dining, corridor left (spacious), 1 occupant

```json
{
  "cell_size": 40,
  "grid_width_cells": 10,
  "grid_height_cells": 18,
  "total_area_m2": "28.8",

  "dining_style": "compact",
  "corridor_side": "left",
  "corridor_cols": 4,

  "corridor_col_start": 0,
  "corridor_col_end": 3,

  "dining_col_start": 4,
  "dining_col_end": 9,

  "chair_left_col_start": 4,
  "chair_left_col_end": 5,
  "gap_left_col_start": null,
  "gap_left_col_end": null,
  "table_col_start": 6,
  "table_col_end": 7,
  "gap_right_col_start": null,
  "gap_right_col_end": null,
  "chair_right_col_start": 8,
  "chair_right_col_end": 9,

  "dining_chair_rows": 1,
  "dining_table_rows": 2,

  "dining_start_row": 0,
  "dining_end_row": 3,
  "kitchen_start_row": 4,
  "kitchen_end_row": 6,
  "bathroom_start_row": 7,
  "bathroom_end_row": 9,
  "bedroom_start_row": 10,
  "bedroom_end_row": 14,
  "work_start_row": 15,
  "work_end_row": 17
}
```
