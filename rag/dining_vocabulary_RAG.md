# Dining Section — Vocabulary RAG

This file teaches the configurator how to translate natural language descriptions into dining section parameters. It contains only intent → parameter mappings. It does not contain column indices, grid widths, or solver internals.

---

## CRITICAL RULES — Always Apply These

**1. Occupancy always sets `d`.** Any mention of a number of people or group size MUST produce a `d` value. Never leave `d` unset when occupancy is known.

| Occupants | `d` |
|---|---|
| 1 | `2` |
| 2 | `2` (num_chairs=2) or `3` (num_chairs=1) |
| 3–4 | `4` or `5` |
| 5–6 | `6` or `7` |
| 7–8 | `8` or `9` |

**2. `more_shelves` and `wide_shelves` MUST always be paired with `roof_style: "divided"`.** Never set these tags without also setting `roof_style: "divided"`. They are meaningless without it.

- Shelves above → `roof_style: "divided"` (always set this first)
- Lots of shelves / more storage → `roof_style: "divided"` + `preferred_tags: ["more_shelves"]`
- Big / wide shelves → `roof_style: "divided"` + `preferred_tags: ["wide_shelves"]`

**3. Always output all relevant fields.** Do not omit `d`, `num_chairs`, or `roof_style` just because the user didn't mention them explicitly. Apply defaults when context is unclear.

---

## What the Dining Section Is

The dining section is the eating and gathering space of the dwelling. It contains a table, chairs on one or both sides, and a structural shelf above. It is typically the most social zone — the place where occupants spend time together or alone with food.

In the dwelling, dining usually sits near the kitchen (food preparation flows into eating). It is a public or semi-public zone.

---

## Parameters and What They Control

### `dining_style`: "compact" or "spacious"

Controls the physical width feel of the section.

- **Compact** — chairs sit flush against the table. Tight, efficient, minimal. Good for small dwellings, solo use, or when space is at a premium.
- **Spacious** — gap columns on either side of the table. More breathing room around the table. Feels generous and relaxed.

### `num_chairs`: 1 or 2

Controls which sides of the table are occupied.

- **2 chairs** — both sides of the table are used. Face-to-face seating. Works without a corridor.
- **1 chair** — only one side is occupied. More intimate or solo. **Always requires a corridor** (corridor_side must not be "none").

### `h`: 7–11 (height in grid cells)

Controls the **ceiling / section height** — how tall the overall space feels. This is NOT furniture height.

- **7** — standard, grounded, cosy ceiling.
- **8–9** — airy, comfortable overhead clearance.
- **10–11** — dramatic, high-ceilinged, expansive vertical space.

> **CRITICAL — `h` vs `preferred_tags` for height:**
> - "higher table", "taller table", "higher chairs", "taller chairs", "elevated seating" → use `preferred_tags: ["h3"]`. Do NOT change `h`.
> - "high ceiling", "tall space", "airy", "open overhead" → change `h`. Do NOT change `preferred_tags`.
> - These are two completely separate parameters. Never confuse them.

### `d`: 2–9 (depth in grid cells)

Controls how many people can sit at the table. Depth is an occupancy parameter for dining — it directly determines how many chairs fit along each side of the table.

| `d` | People per chair side | Total occupants (num_chairs=2) | Total occupants (num_chairs=1) |
|---|---|---|---|
| 2–3 | 1 | 2 | 1 |
| 4–5 | 2 | 4 | 2 |
| 6–7 | 3 | 6 | 3 |
| 8–9 | 4 | 8 | 4 |

The LLM should derive `d` from the number of occupants, not from spatial preference.

### `roof_style`: "any", "plain", "divided", "pitched"

Controls the structural and visual character of the ceiling/roof zone above the table.

- **any** — solver picks freely. Use when the user has no ceiling preference.
- **plain** — clean flat top bar. Simple, unfussy.
- **divided** — internal shelves or dividers above. Storage feel, more articulated overhead.
- **pitched** — slanted or gabled roof line. Expressive, lean-to or tent-like overhead.

> **TODO (climate layer):** Pitched and slanted roof styles will eventually be assigned based on climate and location — e.g. pitched for high-rain or high-snow climates, flat for arid zones. Until that layer is implemented, `roof_style` is set by user preference only. Do not assign roof style based on climate yet.

### `preferred_tags`: list of strings

Hints that bias the 3D furniture selection. The 2D section is unchanged — only the 3D realization shifts.

- `"tall_chairs"` — taller chairs only. Table height unchanged.
- `"low_chairs"` — lower chairs only. Table height unchanged.
- `"tall_table"` — taller table only. Chair height unchanged.
- `"low_table"` — lower table only. Chair height unchanged.
- `"tall_furniture"` — taller chairs **and** table together.
- `"low_furniture"` — lower chairs **and** table together.
- `"compact"` — bias toward compact furniture geometry.
- `"spacious"` — bias toward wider, more generous furniture geometry.
- `"more_shelves"` — **always set `roof_style: "divided"` alongside this tag.** Prefer more shelf subdivisions overhead.
- `"wide_shelves"` — **always set `roof_style: "divided"` alongside this tag.** Prefer wider, deeper shelf spans overhead.

> **Note:** `"h2"` and `"h3"` apply to the whole dining zone — they affect both chairs and table height together. Do not use them for chairs only.

---

## Vocabulary Mappings

### Size and scale

| User says | Parameter change |
|---|---|
| "compact dining", "tight space", "minimal", "small", "efficient" | `dining_style: "compact"` |
| "spacious dining", "open", "wide", "generous", "roomy", "breathing room" | `dining_style: "spacious"` |
| "cosy ceiling", "low", "cave-like", "intimate overhead" | `h: 7` |
| "airy", "high ceiling", "open overhead", "spacious above" | `h: 9` to `h: 11` |
| "normal height", "standard" | `h: 7` or `h: 8` |

### Occupancy → depth

Depth is determined by how many people need to eat at the same time.

| User says | `d` value |
|---|---|
| "just me", "1 person", "solo" | `d: 2` |
| "two people", "a couple", "me and one other" | `d: 3` (num_chairs=1) or `d: 2` (num_chairs=2) |
| "3–4 people", "small group", "family of four" | `d: 4` or `d: 5` |
| "5–6 people", "larger group", "friends over" | `d: 6` or `d: 7` |
| "7–8 people", "big gatherings", "communal table" | `d: 8` or `d: 9` |

When the user states a number of occupants directly, use the occupancy table above to derive `d`. Always check `num_chairs` too — with only 1 chair side, the same `d` seats half as many people.

### Seating and table height

| User says | Parameter change |
|---|---|
| "just me", "solo dining", "eating alone", "one person" | `num_chairs: 1` (requires corridor) |
| "two people", "couple", "face to face", "both sides" | `num_chairs: 2` |
| "higher chairs", "bar height", "taller seating", "bar stool" | `preferred_tags: ["tall_chairs"]` |
| "lower chairs", "low seating", "floor-level", "relaxed seating", "Japanese-style" | `preferred_tags: ["low_chairs"]` |
| "higher table", "elevated table", "bar table", "stand-up dining" | `preferred_tags: ["tall_table"]` |
| "lower table", "low table" | `preferred_tags: ["low_table"]` |
| "higher furniture", "tall furniture" (both chairs and table) | `preferred_tags: ["tall_furniture"]` |
| "lower furniture", "low furniture" (both chairs and table) | `preferred_tags: ["low_furniture"]` |

### Corridor

`corridor_side` and `corridor_w` are independent from `dining_style`. Changing the corridor does NOT change the section width, and changing the section style does NOT change the corridor.

| User says | Parameter change |
|---|---|
| "wider corridor", "bigger corridor", "more spacious corridor", "more circulation space", "wider walkway" | `corridor_w: 4` — dining_style UNCHANGED |
| "narrow corridor", "compact corridor", "tight corridor", "smaller walkway" | `corridor_w: 2` — dining_style UNCHANGED |
| "add a corridor", "I want a corridor", "add a walkway" | `corridor_side: "right"` (default) — everything else UNCHANGED |
| "remove the corridor", "no corridor", "take away the corridor" | `corridor_side: "none"` — everything else UNCHANGED |

> **Critical:** "more spacious" → changes `dining_style` only, NOT `corridor_w`. "wider corridor" → changes `corridor_w` only, NOT `dining_style`.

### Ceiling and roof

| User says | Parameter change |
|---|---|
| "plain ceiling", "clean top", "simple roof", "unfussy overhead" | `roof_style: "plain"` |
| "shelves above", "storage overhead", "divided ceiling", "articulated top" | `roof_style: "divided"` — set this field |
| "lots of shelves", "more storage", "many divisions overhead" | `roof_style: "divided"` AND `preferred_tags: ["more_shelves"]` — both required |
| "big shelves", "wide shelves", "deep storage overhead", "generous shelving" | `roof_style: "divided"` AND `preferred_tags: ["wide_shelves"]` — both required |
| "angled roof", "pitched", "tent-like", "lean-to", "slanted ceiling" | `roof_style: "pitched"` |
| "no preference", "any roof", "whatever works" | `roof_style: "any"` |

### Social character

| User says | Parameter change |
|---|---|
| "social", "hosting guests", "gathering space", "communal" | `dining_style: "spacious"`, `num_chairs: 2`, `h: 9+` |
| "private", "quiet eating", "solo meals" | `num_chairs: 1`, `dining_style: "compact"` |
| "cosy dinner", "intimate" | `dining_style: "compact"`, `h: 7`, `roof_style: "plain"` |
| "dramatic dining", "statement space" | `h: 10` or `h: 11`, `roof_style: "pitched"` |

---

## Multi-Parameter Examples

These are full phrases with combined intent. The LLM should resolve all parameters simultaneously, not sequentially.

| User phrase | Resulting params |
|---|---|
| "I want a small intimate dining space just for me" | `dining_style: "compact"`, `num_chairs: 1`, `h: 7`, `d: 2` |
| "open generous dining for two with high ceilings" | `dining_style: "spacious"`, `num_chairs: 2`, `h: 10`, `d: 2` |
| "dining for four, comfortable" | `dining_style: "compact"`, `num_chairs: 2`, `h: 8`, `d: 4` |
| "minimal Japanese-style low seating, two people" | `dining_style: "compact"`, `num_chairs: 2`, `preferred_tags: ["h2"]`, `h: 7`, `d: 2` |
| "cosy dinner nook, angled roof, two people" | `dining_style: "compact"`, `num_chairs: 2`, `roof_style: "pitched"`, `h: 8`, `d: 2` |
| "I eat alone but like a big open space" | `num_chairs: 1`, `dining_style: "spacious"`, `h: 9`, `d: 2` — requires corridor |
| "hosting six people, dramatic space" | `dining_style: "spacious"`, `num_chairs: 2`, `d: 6`, `h: 11`, `roof_style: "pitched"` |

---

## Modification Examples

These show how the LLM modifies an existing spec based on a chat message.

**CRITICAL:** Only change `num_chairs` if the user explicitly mentions chairs, seating, or number of people. Spatial words like "spacious", "bigger", "taller", "open" must NEVER change `num_chairs`.

**"make it taller"** → increase `h` by 2 (e.g. 7 → 9). Do not change other fields.

**"more spacious"** → change `dining_style` to `"spacious"`. Do NOT change `h`, `d`, or `num_chairs`.

**"bigger"** → increase `h` by 1 and/or `dining_style` to `"spacious"`. Do NOT change `num_chairs`.

**"I want higher chairs"** → add `"h3"` to `preferred_tags`. Do not change anything else.

**"make it feel more dramatic"** → increase `h` toward 10–11, set `roof_style: "pitched"`. Do NOT change `num_chairs`.

**"smaller and more compact"** → set `dining_style: "compact"`, reduce `d` by 1–2, reduce `h` toward 7. Do NOT change `num_chairs`.

**"I'll be eating alone"** → set `num_chairs: 1`. This is the only case where `num_chairs` changes.

**"add another chair"** / **"seat two people"** → set `num_chairs: 2`. This is the only other case where `num_chairs` changes.

---

## What the LLM Must NOT Do

- Set `w` or `corridor_w` — these are computed by the solver from `dining_style` and `num_chairs`.
- Set column indices or grid positions — the solver handles all geometry.
- Change `seed` — this is user-controlled.
- Set `num_chairs: 1` without ensuring `corridor_side` is `"left"` or `"right"` at the dwelling level.
- Invent parameter names not in the spec.
