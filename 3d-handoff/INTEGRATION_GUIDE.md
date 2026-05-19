# Integration Guide — 3D Side-Branch → Main Project

> **Hand this file to a Claude Code agent before any work.** Everything the
> agent needs to (1) merge the 3D pipeline into the main project, and (2)
> continue the unfinished Phase 6 work, is in this file. Read it top to
> bottom before touching code.

---

## 📦 What you received

This handoff lives in a single self-contained folder (`3d-handoff/`). **Drop
the whole folder into the main project directory before doing anything.**
Don't unpack the files into the project root yet — keep them isolated in
`3d-handoff/` until you're ready to integrate, so the existing 2D files
stay clearly distinguishable from the incoming 3D ones.

Folder contents (do not modify until Step 1):
```
3d-handoff/
├── INTEGRATION_GUIDE.md            ← this file — read first
├── modules3d.py                    ← additive (copy to main project root in Step 1)
├── solver3d.py                     ← additive
├── viewer3d.py                     ← additive
├── app-3d.py                       ← reference for the app.py merge (Step 3)
├── MODULE_AUTHORING_WORKFLOW.md    ← additive (Rhino → Python format spec)
├── NOMADIC_ENGINE_3D_APPEND.md     ← the §19 + glossary entries to append (Step 4)
└── rhino exports/                  ← the user's Rhino designs (Phase 6 input)
    ├── chair_left.json
    ├── chair_right.json
    ├── table.json
    ├── roof.json
    └── section.json
```

**Where to put `3d-handoff/`**: at the root of the main project, alongside
`modules.py`, `app.py`, etc. The project tree should look like:

```
<main-project>/
├── app.py                  ← the architect's main app (gets merged in Step 3)
├── modules.py              ← the architect's 2D modules (untouched by 3D)
├── solver.py
├── drawing.py
├── NOMADIC_ENGINE.md
├── 3d-handoff/             ← drop this whole folder here, untouched
└── ... other architect files ...
```

The Step 1 commands below pull files OUT of `3d-handoff/` into the project
root as part of the integration. **Until Step 1, don't touch the main
project files.**

---

## ⚠️ READ THIS BOX FIRST

The user (an architect, vibe-coding) modeled 4 modules in Rhino and exported
them as JSON to `rhino exports/`. **Those JSONs are the source of truth.**

In the prior session, I (Claude) **drifted from the JSONs** and invented 3
modules from a verbal text description ("rectangle without the smaller sides"
→ I built a stadium-arch). The user's actual roof is a **tent/marquee** with
apex points and diagonal beams. The user was rightly upset. Those invented
modules were removed in cleanup.

**DO NOT REINVENT THEM.** If anything in this file's text description seems
to disagree with a JSON in `rhino exports/`, the JSON wins. If a JSON is
ambiguous, **ask the user before coding**. Don't reverse-engineer; don't
assume; don't extrapolate from chat history.

---

## What you're integrating (30-second overview)

A parallel 3D pipeline was built alongside the existing 2D one. Architecture:

| 2D file        | 3D counterpart  | Touched 2D? |
|----------------|-----------------|-------------|
| `modules.py`   | `modules3d.py`  | **No**      |
| `solver.py`    | `solver3d.py`   | **No**      |
| `drawing.py`   | `viewer3d.py`   | **No**      |
| `app.py`       | (merged in)     | **Yes — adds Mode radio + 3D branch** |

The 3D path is gated behind a `Mode: 2D | 3D` radio at the top of the
sidebar. Every existing 2D module auto-extrudes into a 3D variant for free
(see "Why" below — this is what makes the integration mostly mechanical).

**Phase 6 is unfinished**: native 3D modules from `rhino exports/` JSONs
have not been authored. The 3D mode currently shows auto-extruded versions
of 2D modules — NOT the user's Rhino designs.

---

## Files

### Copy these in (no merge)

```
modules3d.py
solver3d.py
viewer3d.py
INTEGRATION_GUIDE.md            (this file)
MODULE_AUTHORING_WORKFLOW.md
rhino exports/                  (whole folder, 5 JSON files)
```

### Merge these

```
app.py                          (see Step 3 — adds Mode radio + 3D branch)
NOMADIC_ENGINE.md               (see Step 4 — appends §19 + 4 glossary entries)
```

### Don't touch these (3D reads from them, but never modifies)

```
modules.py
solver.py
drawing.py
```

---

## Step-by-step integration

After each step: confirm 2D mode still works exactly as it did pre-merge.

### Step 1 — Drop in the additive files

Assuming the `3d-handoff/` folder is at the root of the main project:

```bash
cd <main-project>
cp 3d-handoff/{modules3d,solver3d,viewer3d}.py .
cp 3d-handoff/MODULE_AUTHORING_WORKFLOW.md .
cp -R "3d-handoff/rhino exports" .
```

Keep `3d-handoff/INTEGRATION_GUIDE.md`, `3d-handoff/app-3d.py`, and
`3d-handoff/NOMADIC_ENGINE_3D_APPEND.md` inside the folder — they're
references used in later steps, not files to copy out.

After integration is complete and verified, you can delete the
`3d-handoff/` folder.

### Step 2 — Verify imports against the architect's possibly-extended 2D files

`modules3d.py` reads these names from `modules.py`:

| Name                           | Type   | Failure mode if renamed                       |
|--------------------------------|--------|-----------------------------------------------|
| `MODULES`                      | dict   | `AttributeError` at import                    |
| `ZONES`                        | list   | `AttributeError`                              |
| `ZONES_CORR_RIGHT`             | list   | `AttributeError`                              |
| `ZONES_CORR_LEFT`              | list   | `AttributeError`                              |
| `ZONES_CORR_RIGHT_NARROW`      | list   | `AttributeError`                              |
| `ZONES_CORR_LEFT_NARROW`       | list   | `AttributeError`                              |
| `_TABLE_COMPACT`               | list   | `AttributeError`                              |
| `_TABLE_SPACIOUS`              | list   | `AttributeError`                              |
| `_SHELF_CATEGORY`              | dict   | `AttributeError`                              |
| `EPS`                          | float  | `ImportError`                                 |

`solver3d.py` reads from `solver.py`:

| Name             | Failure mode if renamed                       |
|------------------|-----------------------------------------------|
| `resolve_rule`   | `ImportError`                                 |
| `_seat_y`        | `ImportError`                                 |

`viewer3d.py` reads from `modules.py` (`LINE_COLOR`, `PORT_COLOR`,
`GRID_COLOR`, `ZONE_ORDER`, `ZONE_COLORS`) and `drawing.py`
(`plot_section`). Same pattern.

**Verify**:

```bash
python -c "import modules3d; print(len(modules3d.MODULES_3D), '3D variants')"
python -c "import solver3d; print('solver3d OK')"
python -c "import viewer3d; print('viewer3d OK')"
```

Expected: a number ≥ ~50 from the first; no errors on others.

**If any fail** with `ImportError` / `AttributeError`: the architect
renamed something in `modules.py` or `solver.py`. Find the new name and
update the import in the 3D file. Fix is mechanical and local.

**Common renames to look for**:
- `_SHELF_CATEGORY` → `SHELF_CATEGORY` (lost underscore)
- `_TABLE_COMPACT` → `TABLES_COMPACT` (pluralized)
- `resolve_rule` → `parse_rule` / `_resolve_rule`
- `ZONES` → `ZONES_2D` / `BASE_ZONES`

### Step 3 — Merge `app.py`

The side-branch's `app-3d.py` (171 lines) is `app.py` right after the 3D
integration was done. The main project's `app.py` may have new controls
the architect added since.

**Diff strategy**: take the main project's `app.py` as base. Add the
following changes in order.

#### 3.1 — Add imports near the top

```python
from solver3d import solve3d, check_adjacency_3d, check_circuit_3d
from viewer3d import plot_section_3d, plot_module_library_3d, plot_slice_2d
```

#### 3.2 — Insert the Mode radio at the very top of the sidebar

Before `st.header("Parameters")`:

```python
with st.sidebar:
    mode = st.radio(
        "Mode",
        options=["2D", "3D"],
        horizontal=True,
        help="2D = the original section drawing.  3D = volumetric assembly with a depth axis.",
    )
    st.divider()
    st.header("Parameters")
    # ... all the architect's existing parameter controls below ...
```

#### 3.3 — Add a conditional Depth D input next to Height H

```python
    H = int(st.number_input("Height H", min_value=7, max_value=20, value=7, step=1, ...))

    if mode == "3D":
        D = int(st.number_input(
            "Depth D", min_value=1, max_value=10, value=2, step=1,
            help="Number of depth cells. Every module is auto-extruded along z.",
        ))
    else:
        D = 1   # placeholder, unused in 2D
```

#### 3.4 — Branch the Module Library tab

```python
with tab_lib:
    if mode == "2D":
        st.pyplot(plot_module_library())
    else:
        st.pyplot(plot_module_library_3d(default_d=D))
```

#### 3.5 — Branch the Section tab's solve + render

Inside the existing `with tab_sec:` block, find where the architect's
code calls `solve(...)` and `plot_section(...)`. Replace with:

```python
    with st.spinner("Solving…"):
        if mode == "2D":
            result = solve(W, H, seed, corridor, corridor_w, dining_style, roof_style,
                           # ... whatever other params the architect added ...)
        else:
            result = solve3d(W, H, D, seed, corridor, corridor_w, dining_style, roof_style,
                             # ... pass the SAME extra params (see Step 3.7 note) ...)

    if result is None:
        st.error("No valid section found — try a different seed or combination.")
    else:
        if mode == "2D":
            st.pyplot(plot_section(result, W, H, ...))   # architect's existing call
        else:
            st.pyplot(plot_section_3d(result, W, H, D))

            with st.expander("2D slice at depth z", expanded=False):
                z_slice = st.slider(
                    "z position",
                    min_value=0.5, max_value=float(D) - 0.5,
                    value=0.5, step=1.0,
                )
                st.pyplot(plot_slice_2d(result, W, H, D, z=z_slice,
                                        # ... pass roof_style etc. if architect's plot_section accepts them ...))
```

#### 3.6 — Branch the validation expanders

```python
        with st.expander("Circuit validation"):
            if mode == "2D":
                ok_adj = check_adjacency(result)
                ok_cir = check_circuit(result)
            else:
                ok_adj = check_adjacency_3d(result)
                ok_cir = check_circuit_3d(result)
            st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
            st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")

        with st.expander("Placement details"):
            for p in result:
                off = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
                       else f"({p['x_off']:.0f}, {p['y_off']:.0f}, {p['z_off']:.0f})")
                size = (f"{p['w']}w × {p['h']}h" if mode == "2D"
                        else f"{p['w']}w × {p['h']}h × {p['d']}d")
                st.write(f"**{p['module_id']}** — offset {off}  size {size}")
```

#### 3.7 — If the architect added new `solve()` parameters

E.g., they added `chair_style`, `seasonal_mode`, etc. to `solve()`. Mirror
each one:

1. Add the same parameter to `solve3d()` in `solver3d.py` (same default).
2. Mirror the filter logic. Pattern (search `solver3d.py` for "Roof-style
   filter" — that's a template):

```python
if my_new_param != "default_value":
    def _my_filter(mid):
        base = mid.replace(EXT_SUFFIX, "")  # strip __ext suffix for 2D-id matching
        # ... existing 2D filter logic from solver.py ...
        return True
    active_zones = [
        {**z, "modules": [m for m in z["modules"] if _my_filter(m)]}
        if z.get("id") == "<target_zone_id>" else z
        for z in active_zones
    ]
```

3. Pass the param through in `app.py` (Step 3.5) — same way it's already
   passed to `solve()`.

### Step 4 — Append to `NOMADIC_ENGINE.md`

Open `3d-handoff/NOMADIC_ENGINE_3D_APPEND.md` — it contains:
- 4 glossary rows to add at the end of the §18 Glossary table
- The complete §19 "3D Mode — Volumetric Assembly" block (~80 lines)

Copy both blocks to the **end** of the main project's `NOMADIC_ENGINE.md`.
No conflicts expected — these are purely additive.

### Step 5 — End-to-end verification

```bash
streamlit run app.py
```

1. **2D mode (default)** — confirm it renders identically to pre-merge.
2. **3D mode** — switch the radio. Set `Depth D = 2`. See the 3D wireframe.
3. **Slice view** — open the `2D slice at depth z` expander. Scrub z. See slices.
4. **Placement details** — confirm 3-coord offsets and 3-dim sizes in 3D mode.
5. **Circuit validation** — both checks ✓ in both modes.
6. **Switch back to 2D** — confirm zero regression.

If 2D regresses, the merge in Step 3 accidentally rewrote 2D code paths.
Back out and isolate.

---

## Why the auto-extrusion handles new 2D modules for free

`modules3d.py` iterates `_m2d.MODULES.items()` at import time:

```python
MODULES_3D = {mid + EXT_SUFFIX: _make_extruded(m) for mid, m in _m2d.MODULES.items()}
```

So **any new 2D module the architect added to `MODULES` automatically gets
a 3D variant** with `__ext` suffix. The extrusion (`extrude_segments` in
`modules3d.py`) handles all four scaling modes:

- Static `segments` (fixed-size modules)
- `segments_fn(W)` (width-scalable shelves)
- `h_segments_fn(H)` (reserved, not currently used)
- `wh_segments_fn(w, H)` (both-scalable corridors)

Also auto-handled:

- **New shelf categories** in `_SHELF_CATEGORY` — the dict is re-exported
  as-is. The `roof_style` filter in `solver3d.py` uses whatever strings
  the 2D `_SHELF_CATEGORY` contains. Add "vaulted" to `_SHELF_CATEGORY` →
  it works as a `roof_style` value in both 2D and 3D.
- **New table tags** — `_TABLE_COMPACT` / `_TABLE_SPACIOUS` are
  re-exported.
- **New filler types** — `FILLER_IDS_3D` filters at runtime by `zone ==
  "filler"`.
- **New modules added to existing zones** — `ZONES_3D` is mirrored from
  `ZONES` at import time.

### The ONE place where extension is needed

If the architect adds a **new top-level zone-list global** to
`modules.py` (e.g., `ZONES_CORR_TOP` for a new corridor mode, or
`ZONES_TWO_TABLES` for a multi-table section), they need:

1. **One line in `modules3d.py`** to mirror it:
```python
ZONES_3D_CORR_TOP = _zones_2d_to_3d(_m2d.ZONES_CORR_TOP)
```

2. **One branch in `solver3d.py`** where corridor mode is selected
   (find the if/elif chain in `solve3d()` that picks between
   `ZONES_3D_CORR_RIGHT`, `ZONES_3D_CORR_LEFT`, etc., and add a branch
   for the new mode).

That's ~5 lines of mechanical mirror work per new zone-list. Pattern is
already there to copy from.

---

## Phase 6 — Native 3D modules from `rhino exports/`

### What's done vs. what isn't

**Done:**
- 3D pipeline (modules / solver / viewer / app branch).
- Auto-extrusion of every 2D module into a `__ext`-suffixed 3D variant.
- 6 face-pair adjacency, 3D closed-circuit, 2D-slice round-trip.

**Not done (Phase 6):**
- Translating the user's Rhino designs (`rhino exports/*.json`) into
  native 3D module dicts.

### What "native 3D" means in this codebase

The current `MODULES_3D` dict contains only auto-extruded modules (each
has a `source_2d_id` field). A **native** 3D module does NOT auto-extrude
— its segments and ports are 3D from the start, defined in module-local
`(x, y, z)` space.

The plumbing for native modules already exists. In `modules3d.py`:

```python
def get_segments_3d(mod, w, h, d):
    src = mod.get("source_2d_id")
    if src is not None:
        # auto-extruded path
        mod2d = _m2d.MODULES[src]
        seg2d   = _materialize_2d_segments(mod2d, w, h)
        ports2d = _materialize_2d_ports(mod2d, w, h)
        return extrude_segments(seg2d, ports2d, d)
    # native path
    if "whd_segments_fn" in mod:
        return mod["whd_segments_fn"](w, h, d)
    return mod["segments"]
```

So a native module dict looks like:

```python
"chair_left_3d_v1_native": {
    "id":          "chair_left_3d_v1_native",
    "w": 2, "h": 2, "d": 2,
    "zone":        "chair_left",
    "tags":        ["native-3d"],
    "segments":    [[(x,y,z), (x,y,z), ...], ...],   # 3D polylines, module-local
    "ports": {
        "left":   [],
        "right":  [(2.0, 0.5, 1.0)],
        "bottom": [],
        "top":    [],
        "front":  [],
        "back":   [],
    },
},
```

Or with a `whd_segments_fn(w, h, d)` lambda if the module should be
dimension-scalable.

### The 5 JSONs in `rhino exports/`

Each module JSON has:
- `segments`: list of polylines, each a list of `[x, y, z]` vertices.
  In the user's Rhino axes: **x = width, y = depth, z = height (Z up)**.
- `ports_unassigned`: flat list of port coordinates (NOT bucketed by face
  — you need to figure out which face each port belongs to).
- `module_id`, `w`, `h`, `d`: TODOs the user didn't fill in.

`section.json` is the assembled section with all 4 modules placed plus
their interface ports. **Use this as the ground truth for layout** —
compare your assembled section visually + programmatically to this.

### Visual identity of the 4 modules

| Module        | What it looks like in Rhino                                              |
|---------------|--------------------------------------------------------------------------|
| `chair_left`  | Closed rectangular box, leg sticking right toward the table              |
| `chair_right` | Mirror                                                                   |
| `table`       | Triangular-prism (V-shape extruded along depth), 2 leg ports at sides    |
| `roof`        | **Tent / marquee** — 4 corner posts, 2 apex points, top bar, diagonals. **NOT a stadium arch.** |

### Phase 6 step-by-step

1. **Read `MODULE_AUTHORING_WORKFLOW.md`** in this repo — handoff format spec.
2. **Open each JSON in `rhino exports/`**. The data is authoritative.
3. **Resolve open conventions WITH the user** (next subsection). Don't guess.
4. **For each module**, translate JSON → native 3D dict:
   - Convert user axes (x=width, y=depth, z=height) → our axes
     (x=width, y=height, z=depth) by swapping y and z.
   - Apply the per-module ORIGIN shift (cell-center → cell-edge, +0.5).
   - Bucket `ports_unassigned` into the 6 face categories by checking
     which axis equals 0 or w/h/d.
   - Verify in-module closed-circuit: every polyline endpoint either
     pairs with another endpoint or is declared as a port.
5. **Register in `MODULES_3D`** (add — don't replace the `__ext` variants).
6. **Add to `ZONES_3D[<zone>]["modules"]`** so the solver picks them.
7. **Author filler variants** if the section needs new fillers (e.g., for
   empty depth strips around half-depth modules — though the user
   confirmed modules span full depth).
8. **Test**: solve and render the assembled section. Compare to
   `section.json` programmatically AND visually.

### OPEN QUESTIONS — ask the user before coding

The prior session got these wrong by guessing. Ask the user:

1. **ORIGIN convention per module.** Did you set Rhino ORIGIN to the
   module's bottom-front-left corner, or to its first cell midpoint?
   The 5 JSONs appear inconsistent — chair_left and chair_right look
   like cell-center, table looks like module-corner. Either re-export
   with one convention or confirm per-module.

2. **Port positions at cell midpoints vs. cell boundaries.** Your
   chair-table junction port lives at section depth = 1 (the boundary
   between cells 0 and 1 in a 2-deep section). The existing 2D system
   has ports at midpoints (0.5 / 1.5). Is the new convention intentional?
   (Either works for the solver — it compares port sets, doesn't validate
   positions — but I want to document it.)

3. **The chair's two "top corner ports"** (at `(0, 0, 1.5)` and
   `(0, 1, 1.5)` in chair-local before shifting). They appear to be on
   the chair's left face, at the top corners — facing the room's outer
   wall. In our system, ports on the section's outer face have no
   neighbor to match (would be degree-1 dangling). Are they: (a)
   connectivity ports that need a new "wall" module type to match
   against, or (b) structural markers that aren't really ports?

4. **Confirm section dimensions: `W=6, H=6, D=2`.** This is what I read
   from `section.json` after applying the cell-center shift. You
   confirmed `H=6` in the prior chat — confirm the other two.

5. **Filler design.** The chair top (`y=2`) and roof bottom (`y=3`) on
   chair columns have a 1-row gap. If the chair has no top ports AND the
   roof has no bottom ports above those columns, `filler_empty` works
   (no port matching needed). If either has ports there, the filler
   needs matching ports — likely a new `filler_pass_v_3d` variant.

### Lessons from the prior session — DON'T REPEAT

1. **JSONs > text descriptions.** When chat shorthand seems to disagree
   with a JSON, the JSON wins.
2. **The prior session invented 3 modules** (`chair_left_h2_closed`,
   `chair_right_h2_closed`, `shelf_h3_arch_v1`) and a `chair_style`
   parameter from a verbal description. The user's actual roof was a
   tent, not a stadium-arch. The user was upset. Those were removed in
   cleanup. The state of the repo at handoff is **clean** — no Arch, no
   Closed Box, no `chair_style` anywhere. **Do not reintroduce.** Only
   build from the JSONs.
3. **When ambiguous, ASK.** Don't reverse-engineer from chat history.

---

## File layout after full integration

```
section-generator/
├── app.py                          (merged — has Mode radio + 3D branch)
├── modules.py                      (architect's, unchanged by 3D)
├── solver.py                       (architect's, unchanged by 3D)
├── drawing.py                      (architect's, unchanged by 3D)
├── modules3d.py                    (NEW — auto-extrusion + 3D zones)
├── solver3d.py                     (NEW — solve3d, adjacency, circuit)
├── viewer3d.py                     (NEW — matplotlib mplot3d + slice viewer)
├── NOMADIC_ENGINE.md               (merged — has new §19)
├── MODULE_AUTHORING_WORKFLOW.md    (NEW — Rhino → Python handoff spec)
├── rhino exports/                  (NEW — user's source-of-truth designs)
│   ├── chair_left.json
│   ├── chair_right.json
│   ├── table.json
│   ├── roof.json
│   └── section.json
└── 3d-handoff/                     (can delete after integration verified)
    ├── INTEGRATION_GUIDE.md
    ├── NOMADIC_ENGINE_3D_APPEND.md
    └── app-3d.py                   (reference for app.py merge)
```

---

## Verification checklist before declaring "done"

After integration:
- [ ] `streamlit run app.py` starts cleanly
- [ ] 2D mode renders identically to pre-merge
- [ ] 3D mode renders auto-extruded modules at `Depth D = 2`
- [ ] Slice expander scrubs correctly
- [ ] Placement / Circuit expanders work in both modes
- [ ] Any 2D features the architect added are intact

After Phase 6:
- [ ] Native 3D modules registered in `MODULES_3D`
- [ ] Solver picks them when seed and filters point to them
- [ ] Assembled section visually matches `rhino exports/section.json`
- [ ] All 5 open questions above were answered by the user before coding
- [ ] No invented modules (no `_closed`, no `_arch`, no `chair_style`)

---

## TL;DR for the agent

1. **Read the ⚠️ box at the top.** Don't invent. Use JSONs as truth. Ask user.
2. Copy the 3 `.py` files + `rhino exports/` folder + this doc + workflow doc.
3. Merge `app.py` (Mode radio + 3D branch — see Step 3 for exact patches).
4. Append §19 to `NOMADIC_ENGINE.md`.
5. Run `streamlit run app.py` → verify 2D unchanged, 3D shows extruded modules.
6. **Then start Phase 6**: ask the user the 5 open questions; translate the
   JSONs into native 3D module dicts; register them; verify against
   `section.json`.
