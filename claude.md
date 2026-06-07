# Nomadic Engine — Configurator Backend Context

This document is the single source of truth for the Nomadic Engine configurator architecture. Read it before making any architectural decisions.

---

## 1. Project Overview

**Nomadic Engine** is a deployable off-grid dwelling system. The end product is a 3D-printed rib + fabric-membrane hybrid structure that can be flat-packed, transported, and assembled on-site by modern nomads.

This codebase is the **configurator** — a web app that lets a prospective dweller go from natural-language description ("I need a place for two people, mostly remote work, in a temperate climate") to a buildable, fabricable dwelling design. The configurator must produce:

1. A **dwelling spec** (parameters describing the dwelling).
2. **2D sections** for each functional zone (dining, kitchen, living, bed).
3. A **plan view** of the assembled dwelling.
4. A **3D model** of the assembled dwelling.

The configurator is part of a larger product. End-users are prospective dwellers (not architects). The frontend will eventually be a React webapp built by a teammate, but for now we're working on a Streamlit prototype that proves the backend.

---

## 2. Hard Conventions (Never Violate)

### 2.1 Axis Convention
**w = width, h = height, d = depth. Always. Everywhere.**

- `w` is along the x-axis (left-right in section)
- `h` is along the y-axis (up-down in section, vertical in 3D)
- `d` is along the z-axis (into the page in section, dwelling length axis in 3D)

Every variable name, every function parameter, every dict key uses these. If you find yourself naming something `width_cells`, stop and use `w`. If something needs more disambiguation, prefix it (`grid_w`, `module_w`, `section_w`).

When rendering 3D with matplotlib, the on-screen vertical axis is `h` (mpl calls it `z`), so data `(w, h, d)` plots as `(x, z, y)` in mpl coordinates. This is a rendering detail only; the data axes never change names.

### 2.2 No Grasshopper
Grasshopper is being removed from the architecture. Python is the sole source of truth for everything: parameter resolution (via LLM), section solving, dwelling assembly, plan generation, 3D extrusion, and rendering. No code should assume Grasshopper exists downstream.

### 2.3 The Section Generator is the Layout System
There is no separate "layout generator". A dwelling is a linear back-to-back arrangement of functional sections along a shared corridor on one side. Each section is solved independently by `solver.py` / `solver3d.py`. The dwelling is the concatenation of those sections along their depth axis. The plan view is the union of section column-layouts viewed from above.

### 2.4 2D and 3D Are Independent Module Libraries
**Critical:** the 3D dwelling is NOT just the extruded 2D section. They are two distinct representations answering two different questions:

- **2D section = structural schematic.** Defines zone occupation, rib rhythm, dimensional slots. "Chair on left, table middle, chair on right, shelf above." It tells the rib/membrane system where major elements live. 2D modules are line-art glyphs conveying type and dimension, not specific furniture.

- **3D dwelling = realized furniture catalog.** Each zone slot from the 2D schematic gets filled by a specific 3D module pulled from a catalog. Multiple 3D modules can fill the same 2D zone — different styles, materials, ergonomics. Two dwellings with identical 2D sections can have completely different 3D realities because they pulled different 3D modules from the catalog.

The mapping is **2D zone slot → list of 3D module candidates that fit**, not 2D module → 3D module.

This decoupling is what enables the customization page in the configurator (pick furniture type, material, style) — the 2D structure stays fixed while the 3D contents swap.

### 2.5 Module Library Conventions
- 2D modules live in `modules.py`, 3D modules in `modules3d.py` — they are independent libraries
- Every module has: `id`, `w`, `h`, `zone`, `description`, `tags`, `segments`, `ports` (and `d` for 3D)
- 3D modules also have material, style, and other catalog metadata
- Ports are coordinates on module edges where lines exit; adjacent modules must have matching port sets for the assembly to be valid
- Closed-circuit rule: the assembled section's segment graph must have no degree-1 vertices (no dangling lines)
- Module descriptions and tags are for LLM/RAG retrieval and configurator filtering — keep them informative and consistent
- The legacy `_lift2d()` helper that extrudes 2D modules to 3D is a stopgap; new 3D modules should be defined natively in 3D

---

## 3. Current Codebase State

### 3.1 Files Already Built
- `modules.py` (~1444 lines) — 2D module library for chairs, tables, shelves, corridors, kitchen elements, living elements, fillers; zone configurations for dining/kitchen/living
- `modules3d.py` (~1284 lines) — 3D module library with native 3D modules and `_lift2d()` helper to extrude 2D modules to 3D
- `solver.py` (~665 lines) — 2D backtracking constraint solver with port matching and circuit validation. Handles dining (fully), kitchen (fully), living (fully)
- `solver3d.py` (~523 lines) — 3D version of solver. Handles dining (fully), kitchen (fully). Living 3D not implemented yet
- `drawing.py` — 2D matplotlib rendering
- `viewer3d.py` — 3D matplotlib rendering
- `app.py` — Streamlit UI with section type radio (Dining/Kitchen/Living/Bed), parameter sidebar, 2D/3D toggle, module library tab

### 3.2 What's Missing
- **Bed solver** — not started in 2D or 3D
- **Living 3D solver** — 2D works, 3D not implemented
- **LLM integration** — no code touches the LLM wrapper yet
- **Dwelling assembler** — no code stitches multiple sections into a dwelling
- **Plan view rendering** — only sections are rendered, not the top-down dwelling plan
- **Onboarding flow** — no UI for the 5 onboarding questions
- **Chat assistant** — no chat input or stateful spec modification

### 3.3 Solver API
```python
# 2D
solve(W, H, seed, corridor="none", corridor_w=2,
      dining_style="compact", roof_style="any",
      section="dining") -> Optional[List[dict]]

# 3D
solve3d(W, H, D, seed, corridor="none", corridor_w=2,
        dining_style="compact", roof_style="any",
        section="dining") -> Optional[List[dict]]
```

Returns a list of placed module dicts: `{"module_id": str, "x_off": float, "y_off": float, "w": int, "h": int}` (plus `z_off` and `d` in 3D).

Variables in the solver API still use uppercase `W, H, D` from earlier code; new code should use lowercase `w, h, d`. Don't rename the existing solver signatures without a refactor pass — just be consistent in new code.

---

## 4. LLM Architecture

### 4.1 The Wrapper
There is a **Gemini API wrapper server** built by Calin (ML tutor) at `http://127.0.0.1:8000`. Each user runs it locally. It exposes:

- A web UI for managing API keys, models, RAG collections, JSON schemas
- A `POST /...` endpoint that takes `{model, prompt, context, metadata, use_google_search, rag_collection, rag_top_k, images}` and returns Gemini's response
- A **Schema Builder** that produces a JSON Schema constraining Gemini's output
- A **RAG Collections** manager that indexes a directory of `.md/.txt/.pdf` files for retrieval-augmented generation

We use the wrapper as dumb infrastructure. Our code POSTs to it; the wrapper handles Gemini.

### 4.2 The LLM's Job
The LLM is a **parameter resolver**. It takes natural language and outputs a dwelling spec (structured JSON). It does NOT do geometry, layout math, or module selection logic — those are the solver's job.

The LLM has two modes:
- **Initial mode (onboarding):** structured enum inputs from the 5 questions → first dwelling spec
- **Modification mode (chat):** current dwelling spec + user message → new dwelling spec (stateless: each chat turn sees only the current spec and the new message, not prior turns)

Both modes use the same JSON schema, same RAG, same wrapper endpoint. They differ in system prompt.

The LLM's `preferred_tags` output drives both 2D and 3D module selection. For 2D, it biases zone-level variant choice. For 3D, it filters the furniture catalog. "Modern chairs" → `preferred_tags: ["modern"]` → 3D solver biases toward chairs tagged "modern". The 2D schematic is unchanged; the 3D realization swaps.

### 4.3 The Three-Stage Pipeline
The configurator backend operates in three distinct stages, each separable and replaceable:

1. **LLM → dwelling spec.** Parameters per function, including `preferred_tags`. Done by the LLM wrapper. Stateless (current_spec + message → new_spec).
2. **2D solver → schematic per function.** Zones placed with dimensions, port-matched, circuit-closed. This is what `solver.py` does today.
3. **3D solver → furniture-realized dwelling.** Given the 2D solution's zones (with their dimensions and adjacencies), pick specific 3D modules from the catalog that fit each zone's geometric envelope and respect 3D port adjacencies. Same backtracking pattern as 2D but operating on the 3D module library.

Today, `solver3d.py` partially conflates stages 2 and 3 by lifting 2D modules to 3D. The new architecture splits them: 2D solver runs first, produces a schematic, then 3D solver fills zones with catalog modules.

### 4.4 What the LLM Does NOT Do
- Compute column indices (the solver does this)
- Decide specific module IDs (the solver picks; LLM provides preferred tags as hints)
- Validate geometric constraints (the solver enforces port matching and closed-circuit rules)
- Maintain conversation history (each turn is `current_spec + message → new_spec`)

### 4.5 Vocabulary RAG Files
For each section type and for the dwelling-level vocabulary, we maintain a `<thing>_RAG.md` file. These teach the LLM what user words mean in our parameter system:

- "Higher chair" → `preferred_tags: ["h3"]`
- "Compact dining" → `dining_style: "compact"`
- "Bigger kitchen" → increase that function's `h`
- "Add a workspace" → insert new function in `functions` array
- "More privacy" → fewer open sections, more dividers

The RAG file does NOT encode column indices or solver internals. It only encodes intent → parameter mappings.

---

## 5. The Dwelling Spec (Parameter Contract)

This is the single JSON structure the LLM produces and the solver consumes.

```json
{
  "corridor_side": "left" | "right" | "none",
  "functions": [
    {
      "type": "bed" | "kitchen" | "dining" | "living" | "workspace",
      "params": {
        "w": int,
        "h": int,
        "d": int,
        "seed": int,
        "dining_style": "compact" | "spacious",
        "roof_style": "any" | "plain" | "divided" | "pitched",
        "num_chairs": 1 | 2,
        "occupants": int,
        "preferred_tags": [str]
      }
    }
  ]
}
```

Notes:
- `corridor_side` is shared across all functions — every section uses the same corridor side, or no corridor (last function may have `none`)
- `functions` is an ordered list; order determines the back-to-back arrangement along the dwelling's d-axis
- `params` fields that don't apply to a section type are omitted (e.g. `num_chairs` only applies to dining)
- The solver receives each function's params and calls `solve()` or `solve3d()` per function
- `preferred_tags` is a hint to the solver to bias module selection toward modules whose tags include these strings

---

## 6. The Roadmap

### Phase 0 — Lock the dwelling spec (1 day)
Write `DWELLING_SPEC.md` with the exact JSON structure, every field, every enum, every range. This file is referenced by the solver, the LLM RAG, and any UI code.

### Phase 1 — LLM parameter resolution for dining alone (3-5 days)
- Build dining sub-schema in wrapper's Schema Builder
- Write `dining_vocabulary_RAG.md` — strip column indices from existing RAG, focus on intent → parameters
- In `app.py`: add chat input at top, session state holding `current_spec`, function `chat_modify(current_spec, user_message)` that POSTs to wrapper, parses response, calls `solve()`, re-renders
- Sidebar stays as override panel — user can edit what the LLM chose
- Test with 30+ real prompts, iterate on RAG

### Phase 2 — Onboarding → initial spec (2 days)
Map the 5 onboarding enums (occupants, duration, purpose, priority, scale) + location climate to a structured prompt that produces the first `current_spec`. The function list (what zones exist) is also determined here.

### Phase 3 — Dwelling assembler with 2D/3D split (4-5 days)
Implement two functions:
- `solve_dwelling_2d(spec) -> List[dict]` — iterates over functions, calls `solve()` per function (2D schematic), stitches results into a dwelling-level placed-modules list with depth offsets.
- `solve_dwelling_3d(spec_2d_result, spec) -> List[dict]` — takes the 2D schematic and fills each zone with a 3D module from the catalog, biased by `preferred_tags`.

Add plan view (top-down, derived from 2D result) and dwelling 3D view (from 3D result) to the UI. Chat can now modify multiple functions: "bigger kitchen", "remove living", "add workspace", "make the chairs modern".

Unimplemented sections get placeholder rendering until their solver is ready.

### Phase 4 — Finish solvers and grow the 3D catalog (parallel track, 1-2 weeks)
- Finish kitchen 3D, living 3D, bed solvers (each slots into the dwelling assembler with zero changes)
- Build out the 3D module catalog: multiple chair variants, multiple table variants, multiple shelf variants per zone type — each with style/material tags so the LLM's `preferred_tags` and the customization page have meaningful catalog depth
- Native 3D modules from Rhino exports (see `rhino.py`); avoid `_lift2d()` for new modules

### Phase 5 — Replace Streamlit prototype with production app (teammate's track)
Teammate's React webapp calls the same Python endpoints. Stand up a small FastAPI service exposing `POST /onboarding`, `POST /chat`, `POST /solve_dwelling`. Streamlit becomes a developer tool.

### Phase 6 — Polish, tests, demo prep
Migrate `debug_*.py` to `pytest`. Add regression coverage for solver. Demo script for crit.

---

## 7. Final Crit Constraints

- **Deadline:** weeks away
- **Minimum viable demo:** end-to-end loop on dining alone, with chat modifications working
- **Defensible story:** "dining works fully with chat, other sections work with sidebar parameters" is acceptable. "Four sections work but no chat" is not — the AI configurator narrative collapses.
- **Stretch:** all four sections in chat-modifiable dwelling assembly

---

## 8. Working With This Codebase

### 8.1 Coding Style
- Match the existing style — type hints, docstrings on public functions, no inline lambdas in solver hot paths
- Use Python 3.10+ features (`Optional`, `dict | None`, walrus where it helps readability)
- Keep solver functions pure — input params, return result, no mutation of globals
- New tests go in `tests/` as `pytest` files, not as `debug_*.py` scripts

### 8.2 Naming
- `w, h, d` for sizes (see §2.1)
- `x_off, y_off, z_off` for placement offsets
- `mid` for module IDs (matches existing code)
- `placed` for the list of placement dicts
- `spec` for the dwelling spec JSON dict

### 8.3 When in Doubt
- Don't invent a new system — extend an existing pattern from the solver
- Don't add Grasshopper-specific code, ever
- Don't make the LLM do solver work or the solver do LLM work
- If a piece of geometry can be computed from params, compute it; don't store it in the spec

### 8.4 The Pattern for Adding a Section Type
1. Add 2D module definitions to `modules.py`
2. Add zone configurations (`X_ZONES`, `X_ZONES_CORR_RIGHT`, etc.)
3. Add a branch to `solve()` for `section == "x"`
4. Add 3D catalog modules to `modules3d.py` — multiple variants per zone type, with tags
5. Add a branch to `solve3d()` that fills the zones from the 2D solution with 3D catalog picks
6. Add the section's vocabulary mappings to its RAG file
7. Add the section to the dwelling spec's function `type` enum

### 8.5 The Pattern for Adding a 3D Furniture Variant
1. Define the 3D module natively (don't `_lift2d()` it) — segments and ports as 3D coordinates
2. Set `zone` to match the 2D zone it fills (e.g. `"chair_left"`)
3. Set `w, h, d` to match the zone's dimensional slot
4. Add `tags` for style, material, height class — these are what `preferred_tags` filters on
5. Add a `description` field for RAG retrieval
6. The 3D solver will automatically include it as a candidate for matching zones

---

## 9. Open Questions to Resolve in Implementation

- **Stateful vs stateless chat:** confirmed stateless for now (current_spec + message → new_spec). If we add multi-turn later, we wrap with a history layer.
- **Wrapper hosting:** local-only for now. For demo, both Streamlit and wrapper run on the demo machine.
- **Plan view rendering:** needs to be designed — it's the union of section column-layouts viewed from above, but the visual style isn't decided.
- **Default seed handling:** the section solver uses `seed` for randomization. For chat modifications, do we keep the seed stable (so "make chair higher" doesn't re-randomize everything else) or re-roll? Probably keep stable; let user explicitly re-roll.

---

## 10. Reference Files

When starting work, read in this order:
1. This file (`CLAUDE.md`)
2. `DWELLING_SPEC.md` (once written in Phase 0)
3. `solver.py` — understand the solver API before touching anything that calls it
4. `modules.py` — understand the module data structure before adding modules
5. `app.py` — understand the current UI before extending it

---

## 11. Restarting Streamlit

When the user says "restart streamlit" or "run streamlit in the background", do this silently in order — no prompts, no explanations:

1. Kill every process on port 8501:
   ```bash
   netstat -ano | grep ":8501" | awk '{print $5}' | sort -u | xargs -I{} sh -c 'kill -9 {} 2>/dev/null'
   pkill -f streamlit 2>/dev/null
   sleep 1
   ```
2. Start fresh in the background:
   ```bash
   cd "d:/Bartlett/RC 5/Studio/Term 3/1/sections" && streamlit run app.py --server.port 8501
   ```
3. Wait 4 seconds, confirm "Running at http://localhost:8501" from the log.
4. Tell the user one line: **"Running at http://localhost:8501 — hard-refresh the browser (Ctrl+Shift+R)."**

Never ask the user to run commands. Never surface port conflicts or process errors — just kill and restart.
