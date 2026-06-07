# Onboarding — Vocabulary RAG

This file teaches the configurator how to translate the 5 onboarding answers + site climate into a full dwelling spec. It contains only intent → parameter mappings. It does not contain solver internals or column indices.

The output is a complete `dwelling spec` JSON: `corridor_side`, and an ordered `functions` array. Every function must have all required params.

---

## CRITICAL RULES — Always Apply First

**1. Required functions:** Every spec must include `kitchen`, `bathroom`, and `bed`. These are non-negotiable regardless of any answer.

**2. Kitchen and bathroom must always be adjacent** in the functions array (plumbing).

**3. `corridor_side` is shared across all functions.** Solo occupants dining alone always require a corridor (single-sided seating). Set `corridor_side: "right"` unless a specific reason to use left.

**4. Only the last function may have `skip_corridor: true`.** All other functions must carry the corridor if `corridor_side != "none"`.

**5. LLM decides function order** based on dwelling logic: kitchen+bathroom together (always adjacent), bed at private end, dining and living at social end, workspace near bed or near entrance depending on purpose.

**6. Always output all required fields** for every function. Never leave `h`, `d`, `roof_style`, or `preferred_tags` unset.

---

## Step 0 — Site / Climate

The site's temperature and precipitation determine the climate zone. Climate affects `roof_style` hints.

| Temperature | Precipitation | Climate zone |
|---|---|---|
| Hot | Wet | Tropical |
| Hot | Dry | Dry/Arid |
| Warm or Temperate | Moderate or Rainy | Temperate |
| Cool | Rainy or Moderate | Temperate (cool) |
| Cold | Snowy | Polar |
| Cold | Dry or Moderate | Continental |
| Cold or Cool | high altitude, Dry | Mountain/Alpine |

> **TODO (climate layer):** Roof style will eventually be climate-driven. Until implemented, use user preference only. Do not assign roof_style from climate yet — leave as `"any"` unless another answer specifies it.

---

## Step 1 — Occupants

Occupants determines which functions exist and dining occupancy depth.

| Answer | Occupants | Functions to include | Dining `d` | Dining `num_chairs` |
|---|---|---|---|---|
| Solo | 1 | kitchen + bathroom + bed | `2` | `1` (requires corridor) |
| Couple | 2 | dining + kitchen + bathroom + bed | `2` | `2` |
| Family | 3–4 | dining + kitchen + bathroom + bed + living | `4` or `5` | `2` |
| Large group | 5+ | dining + kitchen + bathroom + bed + living | `6` to `8` | `2` |

**Notes:**
- Solo always requires `corridor_side != "none"` because `num_chairs: 1` requires a corridor.
- Solo does not include dining or living by default — just the three required sections.
- Living is added for Family and Large group; may also be added for Couple if duration ≥ season or purpose == socialising.

---

## Step 2 — Duration

Duration sets the baseline comfort level — how generous `h` and `d` are across all sections.

| Answer | Base `h` | Base `d` | Notes |
|---|---|---|---|
| 1–4 weeks | `7` | `2` | Minimal, efficient. Short stay doesn't need full comfort. |
| 1–3 months | `8` | `3` | Standard comfort. Full sections. |
| A season | `9` | `4` | Generous. Living section more important. |
| Open-ended | `10` | `5` | Maximum comfort. All sections, fully sized. |

These are baseline values. Scale (Step 5) modifies them. Apply scale adjustments on top of duration base.

---

## Step 3 — Purpose

Purpose adjusts which functions exist and biases style choices.

| Answer | Function adjustments | Style / tag hints |
|---|---|---|
| Remote work | Add `workspace` (placeholder) near bed or entrance | `preferred_tags: ["compact"]`, privacy-leaning |
| Retreat | Living section important even for Couple. Bed prominent (generous h/d). | `roof_style: "plain"` or `"any"`, calm feel |
| Socialising | Dining prominent. Add living if not already present. Spacious dining. | `dining_style: "spacious"`, `preferred_tags: ["spacious"]` |
| Field research | Add `workspace` (placeholder). Compact and efficient. Minimal living. | `preferred_tags: ["compact"]`, smaller h/d |

---

## Step 4 — Priority

Priority shapes corridor, style choices, and section sizing.

| Answer | Effect |
|---|---|
| Energy (off-grid autonomy) | Compact everything. Prefer smaller h/d. No unnecessary sections. `dining_style: "compact"`, `living_style: "compact"`. |
| Privacy | `corridor_side: "right"`. Bed and bathroom at the very back. Fewer open sections. `dining_style: "compact"`. |
| Comfort | Spacious styles. Add living if not already present. Generous h. `dining_style: "spacious"`, `living_style: "spacious"`, `preferred_tags: ["spacious"]`. |
| Connectivity | Minimal structural effect. Moderate sizing. No specific style bias. |

---

## Step 5 — Scale

Scale is the final modifier on top of duration base values.

| Answer | `h` adjustment | `d` adjustment | Style |
|---|---|---|---|
| Compact | −1 from base (min 7) | −1 from base (min 2) | Prefer compact styles |
| Standard | No change | No change | No style bias |
| Generous | +1 or +2 from base (max 11) | +1 or +2 from base (max 9) | Prefer spacious styles |

---

## Combining the Answers

Apply in this order:

1. **Occupants** → decide which functions exist, set dining `d` and `num_chairs`
2. **Duration** → set base `h` and `d` for all sections
3. **Purpose** → add or remove functions, apply style/tag hints
4. **Priority** → adjust styles, corridor, section sizing
5. **Scale** → apply final h/d modifier

**`corridor_side` decision:**
- Solo → `"right"` (required for single-sided dining)
- Couple + Privacy priority → `"right"`
- Couple + Energy priority → `"none"` (efficient, no corridor)
- Family or Large group → `"right"` recommended for circulation
- Couple + duration ≥ season → `"right"` recommended

**`skip_corridor` on last function:**
- Set `skip_corridor: true` on the last function when it is the bed section and corridor is not needed for circulation beyond it.

---

## Function Ordering Rules

- Kitchen and bathroom must always be adjacent — never separated
- Dining at the social/front end
- Living between social and private zones
- Workspace near bed (for focus/privacy) or near entrance (for remote work lifestyle)
- Bed at the private/back end
- Bathroom adjacent to kitchen — place the kitchen+bathroom pair wherever it fits the above logic

**Suggested order by occupancy:**
- Solo: kitchen → bathroom → bed
- Couple: dining → kitchen → bathroom → bed
- Family/Group: dining → kitchen → bathroom → living → bed
- With workspace: insert after living, before bed

---

## `preferred_tags` Summary

Tags are cumulative — combine from multiple answers.

| Signal | Tags to add |
|---|---|
| Socialising purpose | `"spacious"` |
| Remote work / field research purpose | `"compact"` |
| Comfort priority | `"spacious"` |
| Energy priority | `"compact"` |
| Generous scale | `"spacious"` |
| Compact scale | `"compact"` |

---

## Example Specs

### Solo, 1–4 weeks, retreat, privacy, compact

```json
{
  "corridor_side": "right",
  "functions": [
    { "type": "kitchen", "params": { "h": 7, "d": 2, "roof_style": "any", "preferred_tags": [] } },
    { "type": "bathroom", "params": { "h": 7, "d": 2 } },
    { "type": "bed", "params": { "h": 7, "d": 2, "roof_style": "plain", "preferred_tags": [], "skip_corridor": true } }
  ]
}
```

### Couple, a season, socialising, comfort, standard

```json
{
  "corridor_side": "right",
  "functions": [
    { "type": "dining", "params": { "h": 10, "d": 2, "dining_style": "spacious", "num_chairs": 2, "roof_style": "any", "preferred_tags": ["spacious"] } },
    { "type": "kitchen", "params": { "h": 9, "d": 4, "roof_style": "any", "preferred_tags": [] } },
    { "type": "bathroom", "params": { "h": 9, "d": 3 } },
    { "type": "living", "params": { "h": 9, "d": 4, "living_style": "spacious", "roof_style": "any", "preferred_tags": ["spacious"] } },
    { "type": "bed", "params": { "h": 9, "d": 4, "roof_style": "any", "preferred_tags": [], "skip_corridor": true } }
  ]
}
```

### Family, 1–3 months, remote work, energy, compact

```json
{
  "corridor_side": "none",
  "functions": [
    { "type": "dining", "params": { "h": 7, "d": 4, "dining_style": "compact", "num_chairs": 2, "roof_style": "any", "preferred_tags": ["compact"] } },
    { "type": "kitchen", "params": { "h": 7, "d": 3, "roof_style": "plain", "preferred_tags": ["compact"] } },
    { "type": "bathroom", "params": { "h": 7, "d": 2 } },
    { "type": "workspace", "params": { "h": 7, "d": 3 } },
    { "type": "bed", "params": { "h": 7, "d": 3, "roof_style": "any", "preferred_tags": ["compact"] } }
  ]
}
```

---

## What the LLM Must NOT Do

- Set `w` or `corridor_w` — computed by solver.
- Change `seed` — user-controlled.
- Set `num_chairs: 1` without setting `corridor_side != "none"`.
- Place bathroom and kitchen non-adjacent.
- Set `skip_corridor: true` on any function except the last.
- Invent parameter names not in the spec.
- Output fewer than 3 functions (kitchen + bathroom + bed minimum).
