# Plan Generator RAG v2 — Dining Zone

---

## 1. System Purpose

This system generates a precise, furniture-informed dining plan on a rectangular grid for use in Grasshopper. Column widths and zone widths are fixed by the section module system. Zone depth is determined by occupancy. Cell size is fixed at 40 cm.

---

## 2. Spatial Model

- **Cell size: fixed at 40 cm.**
- Grid width = dining_cols + corridor_cols
- Grid height = dining depth in rows (determined by occupancy, see section 5)

---

## 3. Seating Mode

There are two seating modes:

- **2 chairs** — both sides of the table are occupied. No corridor required.
- **1 chair** — only one side of the table is occupied. **A corridor is always required.**

The model must not generate a 1-chair layout without a corridor.

---

## 4. Dining Column Layout

Column widths are **fixed by the section module system**. The model must not alter them.

Each chair zone is always exactly **2 columns wide**. Each table zone is always exactly **2 columns wide**. Gap columns (spacious only) are exactly **1 column wide**.

Each chair zone is always exactly **2 columns wide**. Each table zone is always exactly **2 columns wide**. Gap columns (spacious only) are exactly **1 column wide**.

### 4.1 2 Chairs, Compact — dining_cols = 6

`[chair_left: 2] [table: 2] [chair_right: 2]`

| Element | col_start | col_end |
|---|---|---|
| chair_left | 0 | 1 |
| table | 2 | 3 |
| chair_right | 4 | 5 |

No gap columns. Chairs are flush against the table.

### 4.2 2 Chairs, Spacious — dining_cols = 8

`[chair_left: 2] [gap: 1] [table: 2] [gap: 1] [chair_right: 2]`

| Element | col_start | col_end |
|---|---|---|
| chair_left | 0 | 1 |
| gap_left | 2 | 2 |
| table | 3 | 4 |
| gap_right | 5 | 5 |
| chair_right | 6 | 7 |

Gap columns are only present in Spacious mode.

### 4.3 1 Chair, Compact — dining_cols = 4

Corridor on right: `[chair_left: 2] [table: 2]`
Corridor on left:  `[table: 2] [chair_right: 2]`

| corridor_side | Element | col_start | col_end |
|---|---|---|---|
| right | chair_left | 0 | 1 |
| right | table | 2 | 3 |
| left | table | corridor_cols | corridor_cols + 1 |
| left | chair_right | corridor_cols + 2 | corridor_cols + 3 |

### 4.4 1 Chair, Spacious — dining_cols = 5

Corridor on right: `[chair_left: 2] [gap: 1] [table: 2]`
Corridor on left:  `[table: 2] [gap: 1] [chair_right: 2]`

| corridor_side | Element | col_start | col_end |
|---|---|---|---|
| right | chair_left | 0 | 1 |
| right | gap | 2 | 2 |
| right | table | 3 | 4 |
| left | table | corridor_cols | corridor_cols + 1 |
| left | gap | corridor_cols + 2 | corridor_cols + 2 |
| left | chair_right | corridor_cols + 3 | corridor_cols + 4 |

---

## 5. Dining Depth — Occupancy Rule

The section shows 1 chair per side = 2 people. Each additional pair of people adds 2 more rows.

Formula: `grid_height_cells = ceil(occupants / 2) * 2`

| Occupants | chairs per side | grid_height_cells | dining_end_row | depth |
|---|---|---|---|---|
| 1–2 | 1 | 2 | 1 | 80 cm |
| 3–4 | 2 | 4 | 3 | 160 cm |
| 5–6 | 3 | 6 | 5 | 240 cm |
| 7–8 | 4 | 8 | 7 | 320 cm |
| 9–10 | 5 | 10 | 9 | 400 cm |

Grid height is not a free variable.

---

## 6. Corridor

The corridor is a movement strip placed on one side of the dining columns.

- `"none"` → corridor_cols = 0 (only valid with 2 chairs)
- `"left"` → corridor occupies the leftmost columns
- `"right"` → corridor occupies the rightmost columns

Corridor width is always tied to dining_style — there is no separate corridor width setting:
- dining_style = Compact → corridor_cols = 2 (80 cm)
- dining_style = Spacious → corridor_cols = 4 (160 cm)

**1 chair always requires a corridor. corridor_side = "none" is forbidden when num_chairs = 1.**

### 6.1 Full Width Table — All Combinations

| num_chairs | dining_style | corridor_side | corridor_cols | dining_cols | grid_width |
|---|---|---|---|---|---|
| 2 | Compact | none | 0 | 6 | 6 |
| 2 | Compact | left or right | 2 | 6 | 8 |
| 2 | Spacious | none | 0 | 8 | 8 |
| 2 | Spacious | left or right | 4 | 8 | 12 |
| 1 | Compact | left or right | 2 | 4 | 6 |
| 1 | Spacious | left or right | 4 | 5 | 9 |

### 6.2 Corridor Column Positions

**Corridor right:** corridor starts at dining_cols.
- corridor_col_start = dining_cols
- corridor_col_end = dining_cols + corridor_cols - 1

**Corridor left:** corridor starts at 0. All dining column indices shift right by corridor_cols.
- corridor_col_start = 0
- corridor_col_end = corridor_cols - 1

---

## 7. Area Calculation

```
Total_area_m2 = (grid_width_cells x grid_height_cells x 1600) / 10000
```

---

## 8. Validity Conditions

- Cell_size = 40
- num_chairs is 1 or 2
- dining_style is "Compact" or "Spacious"
- corridor_side is "none", "left", or "right"
- corridor_cols = 0 when corridor_side is "none"; 2 when dining_style is Compact; 4 when dining_style is Spacious
- if num_chairs = 1 then corridor_side must not be "none"
- dining_cols matches section 4 for the given num_chairs and dining_style
- grid_width_cells = dining_cols + corridor_cols
- grid_height_cells = ceil(occupants / 2) * 2
- column indices match sections 4.1–4.4 exactly
- gap_left_col_start, gap_left_col_end, gap_right_col_start, gap_right_col_end = -1 when dining_style is Compact
- corridor_col_start, corridor_col_end = -1 when corridor_side is "none"
- Total_area_m2 is correctly calculated

---

## 9. Forbidden Behaviors

- Any cell size other than 40
- num_chairs = 1 with corridor_side = "none"
- dining_cols other than 4, 5, 6, or 8
- grid_height_cells other than 2, 4, 6, 8, or 10
- Column indices that don't match sections 4.1–4.4
- grid_width that does not equal dining_cols + corridor_cols
- Any gap field other than -1 when dining_style is Compact
- corridor_col_start or corridor_col_end other than -1 when corridor_side is "none"

---

## 10. JSON Schema (Metadata)

```json
{
  "type": "object",
  "properties": {
    "Cell_size": {
      "type": "integer",
      "description": "Fixed at 40 cm.",
      "minimum": 40,
      "maximum": 40
    },
    "grid_width_cells": {
      "type": "integer",
      "description": "dining_cols + corridor_cols",
      "minimum": 4
    },
    "grid_height_cells": {
      "type": "integer",
      "description": "ceil(occupants / 2) * 2",
      "minimum": 2,
      "maximum": 10
    },
    "Total_area_m2": {
      "type": "string",
      "description": "grid_width x grid_height x 1600 / 10000"
    },
    "occupants": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "dining_style": {
      "type": "string",
      "enum": [
        "Compact",
        "Spacious"
      ]
    },
    "corridor_side": {
      "type": "string",
      "enum": [
        "none",
        "left",
        "right"
      ]
    },
    "corridor_cols": {
      "type": "integer",
      "minimum": 0,
      "maximum": 4
    },
    "corridor_col_start": {
      "type": "integer",
      "minimum": -1
    },
    "corridor_col_end": {
      "type": "integer",
      "minimum": -1
    },
    "dining_col_start": {
      "type": "integer"
    },
    "dining_col_end": {
      "type": "integer"
    },
    "chair_left_col_start": {
      "type": "integer"
    },
    "chair_left_col_end": {
      "type": "integer"
    },
    "gap_left_col_start": {
      "type": "integer",
      "minimum": -1
    },
    "gap_left_col_end": {
      "type": "integer",
      "minimum": -1
    },
    "table_col_start": {
      "type": "integer"
    },
    "table_col_end": {
      "type": "integer"
    },
    "gap_right_col_start": {
      "type": "integer",
      "minimum": -1
    },
    "gap_right_col_end": {
      "type": "integer",
      "minimum": -1
    },
    "chair_right_col_start": {
      "type": "integer"
    },
    "chair_right_col_end": {
      "type": "integer"
    },
    "dining_start_row": {
      "type": "integer",
      "minimum": 0,
      "maximum": 0
    },
    "dining_end_row": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9
    },
    "num_chairs": {
      "type": "integer",
      "description": "1 = single-sided seating (requires corridor). 2 = both sides occupied."
    }
  },
  "required": [
    "Cell_size",
    "grid_width_cells",
    "grid_height_cells",
    "Total_area_m2",
    "occupants",
    "dining_style",
    "corridor_side",
    "corridor_cols",
    "corridor_col_start",
    "corridor_col_end",
    "dining_col_start",
    "dining_col_end",
    "chair_left_col_start",
    "chair_left_col_end",
    "gap_left_col_start",
    "gap_left_col_end",
    "table_col_start",
    "table_col_end",
    "gap_right_col_start",
    "gap_right_col_end",
    "chair_right_col_start",
    "chair_right_col_end",
    "dining_start_row",
    "dining_end_row",
    "num_chairs"
  ]
}
```

---