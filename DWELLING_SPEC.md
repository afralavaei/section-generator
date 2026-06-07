# Dwelling Spec — Parameter Contract v1

This is the single JSON structure that the LLM produces and the solver consumes. It is the contract between the language layer and the geometry layer. Nothing outside this document should invent new fields.

---

## Full Structure

```json
{
  "corridor_side": "left" | "right" | "none",
  "functions": [
    {
      "type": "kitchen" | "bed" | "bathroom" | "dining" | "living" | "filler",
      "params": { ... }
    }
  ]
}
```

- `corridor_side` is **shared across all functions** — every section in the dwelling uses the same corridor side.
- `functions` is **ordered** — index 0 is the front of the dwelling, last index is the back. The LLM decides both **which functions exist** and **in what order**, based on the user's description and dwelling logic heuristics in the RAG. The solver and UI render whatever the LLM produces — no fixed section list, no fixed order.
- **Required sections:** every dwelling must include `kitchen`, `bed`, and `bathroom`. These three are non-negotiable. `dining`, `living`, and other types are optional additions.
- **Corridor continuity rule:** all functions must have the corridor — except optionally the last function, which may set `skip_corridor: true` to terminate the corridor run. No middle function may skip the corridor.
- `bathroom` and `filler` are placeholder types — not solved yet, render as empty grid outlines.

---

## Top-Level Fields

| Field | Type | Required | Values | Notes |
|---|---|---|---|---|
| `corridor_side` | string | yes | `"left"`, `"right"`, `"none"` | Shared across all functions |
| `functions` | array | yes | 1–5 items | LLM decides which sections exist and their order (front-to-back) |

---

## Per-Function Fields

### `type`

| Value | Required | Solver status 2D | Solver status 3D |
|---|---|---|---|
| `"kitchen"` | yes | Full | Full |
| `"bed"` | yes | Not implemented | Not implemented |
| `"bathroom"` | yes | Placeholder | Placeholder |
| `"dining"` | no | Full | Full |
| `"living"` | no | Full | Not implemented |
| `"filler"` | no | Placeholder | Placeholder |

---

### `params` — field reference

#### Fields set by the LLM

| Field | Type | Default | Range / Values | Applies to | Notes |
|---|---|---|---|---|---|
| `h` | int | `7` | 7–11 | all | Section height in grid cells. Higher = more vertical space, more imposing structure. |
| `d` | int | `3` | 2–9 | all | Section depth in grid cells. For dining, `d` is an occupancy parameter — it determines how many people sit per chair side (see dining RAG). For other sections, deeper = more space along the dwelling axis. |
| `dining_style` | string | `"compact"` | `"compact"`, `"spacious"` | dining | Compact = flush chairs, narrower section. Spacious = wide-top tables with gap columns. |
| `living_style` | string | `"compact"` | `"compact"`, `"spacious"` | living | Compact W=7, spacious W=9. |
| `num_chairs` | int | `2` | `1`, `2` | dining | 1 = single-sided seating. **Requires `corridor_side != "none"`** — constraint enforced by solver. |
| `roof_style` | string | `"any"` | `"any"`, `"plain"`, `"divided"`, `"pitched"` | all | `"any"` = solver picks freely. **TODO:** pitched/slanted styles will be climate- and location-driven in a future update — for now set by user preference only. |
| `preferred_tags` | array of strings | `[]` | free strings | all | Hints to solver for 3D module selection. See tag vocabulary below. |
| `skip_corridor` | boolean | `false` | `true`, `false` | all | Only valid on the **last function**. If `true`, this section is solved without a corridor even though `corridor_side` is set. Middle functions must never set this. |

#### Fields NOT set by the LLM

| Field | Who sets it | Notes |
|---|---|---|
| `seed` | User (sidebar) or system | Controls solver randomisation. Kept stable across chat turns so a modification doesn't re-randomise the whole section. User can explicitly re-roll. |
| `w` | **Computed by solver** | Never in the spec. Derived from `dining_style` / `living_style` + `num_chairs` + `corridor_side`. See derivation table below. |
| `corridor_w` | **Computed by solver** | Never in the spec. Derived from section style. See derivation table below. |

---

## Computed Width Derivations

These are computed inside the solver and assembler. They must never appear in the spec JSON.

### Dining

| `dining_style` | `num_chairs` | inner `w` | `corridor_w` | total `w` (with corridor) |
|---|---|---|---|---|
| compact | 2 | 6 | 2 | 8 |
| compact | 1 | 4 | 2 | 6 |
| spacious | 2 | 8 | 4 | 12 |
| spacious | 1 | 5 | 4 | 9 |

### Living

| `living_style` | inner `w` | `corridor_w` | total `w` (with corridor) |
|---|---|---|---|
| compact | 7 | 2 | 9 |
| spacious | 9 | 4 | 13 |

### Kitchen

| `w` | `corridor_w` | Notes |
|---|---|---|
| 6 (fixed) | — | Kitchen never has a corridor. `corridor_side` is ignored for kitchen. |

### Bed

| `w` | `corridor_w` | Notes |
|---|---|---|
| 8 (fixed inner) | 2 | Corridor width always 2 for bed. Total w = 10 with corridor, 8 without. |

---

## Cross-Field Constraints

These are hard rules. The LLM must respect them; the solver enforces them.

| Constraint | Rule |
|---|---|
| Single-sided dining | `num_chairs: 1` requires `corridor_side != "none"` |
| Corridor continuity | Only the last function may set `skip_corridor: true`. All middle functions must carry the corridor. |
| Kitchen corridor | Kitchen ignores `corridor_side` — it never has a corridor regardless of `skip_corridor` |
| Roof + corridor | `roof_style: "pitched"` with a compact corridor (corridor_w=2) is valid but produces mixed variants — this is intentional |
| Required sections | Every spec must include at least one each of `kitchen`, `bed`, and `bathroom` |
| Bathroom + filler | `type: "bathroom"` and `type: "filler"` render as placeholders — no solver is called |
| Kitchen + bathroom adjacency | Kitchen and bathroom must be adjacent in the `functions` array — they share plumbing |

---

## `preferred_tags` Vocabulary

Tags are free strings. The following are currently meaningful in the 3D module catalog. The LLM should use these; it may combine them.

| Tag | Meaning |
|---|---|
| `"low_furniture"` | Lower height class — applies to chairs and tables together (maps to h2 modules) |
| `"tall_furniture"` | Taller height class — applies to chairs and tables together (maps to h3 modules) |
| `"compact"` | Prefer compact geometry variants |
| `"spacious"` | Prefer spacious geometry variants |
| `"pitched"` | Prefer pitched roof variants |
| `"divided"` | Prefer shelf-divided roof variants |
| `"more_shelves"` | With `roof_style: "divided"` — prefer more shelf subdivisions overhead |
| `"wide_shelves"` | With `roof_style: "divided"` — prefer wider, deeper shelf spans overhead |

This list grows as the 3D catalog grows. New tags must be documented here when added.

---

## Ordering and Composition Heuristics (for RAG)

The LLM uses these when deciding which sections to include and in what order. These live in the RAG file — not enforced by the solver, but the LLM should follow them.

**Which sections to include:**
- `kitchen`, `bed`, `bathroom` are always present — non-negotiable
- Solo dweller, short stay → kitchen + bathroom + bed only
- Two people, longer stay → add dining and/or living
- Social / hosting → larger dining, more spacious styles
- Minimalist → fewer optional sections, smaller h/d values
- A `filler` section can be inserted between any two sections to create a circulation pocket or transition zone

**Ordering logic (front → back):**
- There is no fixed public-first rule — the LLM decides based on context
- **Hard rule:** kitchen and bathroom must always be adjacent (plumbing)
- Bed typically sits at the private/back end, but is not required to
- `filler` sections go between two sections that need a transition gap — not at the very front or back
- Dining and living can appear anywhere that makes sense for the occupant's lifestyle

**Corridor decision:**
- Single-sided seating (`num_chairs: 1`) requires a corridor — LLM must set `corridor_side` accordingly
- Longer dwellings (3+ sections) benefit from a corridor for circulation
- Short solo dwellings can omit the corridor entirely (`corridor_side: "none"`)
- The last function may set `skip_corridor: true` when it is a terminating private zone that doesn't need to feed into further circulation

---

## Example Specs

### Solo dweller, short stay — minimal required sections only

```json
{
  "corridor_side": "none",
  "functions": [
    {
      "type": "kitchen",
      "params": {
        "h": 7, "d": 3,
        "roof_style": "plain", "preferred_tags": []
      }
    },
    {
      "type": "bathroom",
      "params": {
        "h": 7, "d": 2
      }
    },
    {
      "type": "bed",
      "params": {
        "h": 7, "d": 3,
        "roof_style": "any", "preferred_tags": [],
        "skip_corridor": true
      }
    }
  ]
}
```

### Single dining section — minimal

```json
{
  "corridor_side": "none",
  "functions": [
    {
      "type": "dining",
      "params": {
        "h": 7,
        "d": 3,
        "dining_style": "compact",
        "num_chairs": 2,
        "roof_style": "any",
        "preferred_tags": []
      }
    }
  ]
}
```

### Two-person dwelling — full with filler

```json
{
  "corridor_side": "right",
  "functions": [
    {
      "type": "dining",
      "params": {
        "h": 8, "d": 4,
        "dining_style": "compact", "num_chairs": 2,
        "roof_style": "any", "preferred_tags": []
      }
    },
    {
      "type": "kitchen",
      "params": {
        "h": 7, "d": 3,
        "roof_style": "plain", "preferred_tags": []
      }
    },
    {
      "type": "bathroom",
      "params": {
        "h": 7, "d": 2
      }
    },
    {
      "type": "filler",
      "params": {
        "h": 7, "d": 2
      }
    },
    {
      "type": "living",
      "params": {
        "h": 8, "d": 4,
        "living_style": "compact",
        "roof_style": "any", "preferred_tags": []
      }
    },
    {
      "type": "bed",
      "params": {
        "h": 7, "d": 4,
        "roof_style": "pitched", "preferred_tags": [],
        "skip_corridor": true
      }
    }
  ]
}
```

### Chat modification — "make the dining taller and more spacious"

Before:
```json
{ "type": "dining", "params": { "h": 7, "d": 3, "dining_style": "compact", "num_chairs": 2, "roof_style": "any", "preferred_tags": [] } }
```

After (LLM output — only changed fields):
```json
{ "type": "dining", "params": { "h": 10, "d": 3, "dining_style": "spacious", "num_chairs": 2, "roof_style": "any", "preferred_tags": ["spacious"] } }
```

Seed is unchanged. `w` is recomputed by the solver from the new `dining_style`.

---

## What the LLM Receives and Returns

**Input to LLM (every chat turn):**
```json
{
  "current_spec": { ... },
  "user_message": "make the dining taller and give me higher chairs"
}
```

**Output from LLM:**
```json
{
  "corridor_side": "...",
  "functions": [ ... ]
}
```

The LLM always returns the **full spec**, not a diff. The chat handler replaces `current_spec` with the LLM output and re-runs the solver.

---

## Version History

| Version | Date | Notes |
|---|---|---|
| v1 | 2026-05-25 | Initial spec. All sections, LLM sets h/d. |
| v1.1 | 2026-06-04 | Added corridor continuity rule + `skip_corridor` field. Renamed workspace → bathroom. LLM decides function order and composition. |
| v1.2 | 2026-06-04 | h range 7–11, d range 2–9. Required sections: kitchen + bed + bathroom. Added filler type. Kitchen+bathroom adjacency constraint. Removed public-first ordering rule. |
