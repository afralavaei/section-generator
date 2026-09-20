import io
import os
import streamlit as st

from solver import solve, check_adjacency, check_circuit
from drawing import plot_section, plot_module_library, plot_plan_view, _SECTION_ZONES, get_library_by_zone, plot_zone_group
from dwelling import solve_dwelling_2d, solve_dwelling_3d
from solver3d import solve3d, check_adjacency_3d, check_circuit_3d
from viewer3d import plot_section_3d, plot_module_library_3d, plot_slice_2d, plot_dwelling_3d, _draw_module_3d, get_library_3d_by_zone, plot_zone_group_3d
from modules3d import MODULES_3D, _SHELF_CAT_3D
import llm
from llm import chat_modify_dining, onboarding_to_spec
from sites import SITES, REGIONS, get_site, sites_by_region, site_to_roof_style
from export import export_section_3d_rhino
from modules import MODULES
from scorecard_constants import SEAT_HEIGHT_BY_CLASS_CM, TABLE_HEIGHT_BY_CLASS_CM

_MODULES_PATH   = os.path.join(os.path.dirname(__file__), "modules.py")
_DRAWING_PATH   = os.path.join(os.path.dirname(__file__), "drawing.py")
_MODULES3D_PATH = os.path.join(os.path.dirname(__file__), "modules3d.py")


@st.cache_data
def _module_library_png(section: str, mtime: float, drawing_mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    fig = plot_module_library(section)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


@st.cache_data
def _zone_group_png(section: str, zone_label: str, n_mods: int,
                    mtime: float, drawing_mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    groups = get_library_by_zone(section)
    mods = next((m for z, m in groups if z == zone_label), [])
    fig = plot_zone_group(zone_label, mods)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


@st.cache_data
def _module_library_3d_png(section: str, mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    fig = plot_module_library_3d(section)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=80, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


@st.cache_data
def _zone_group_3d_png(section: str, zone_label: str, n_mods: int, mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    groups = get_library_3d_by_zone(section)
    mods = next((m for z, m in groups if z == zone_label), [])
    fig = plot_zone_group_3d(zone_label, mods)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=80, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


@st.cache_data
def _furniture_thumbnail_png(module_id: str, mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    mod = MODULES_3D[module_id]
    w, h, d = mod["w"], mod["h"], 3
    fig = plt.figure(figsize=(1.2, 1.2))
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for _pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        _pane.fill = False
    _draw_module_3d(ax, mod, 0.0, 0.0, 0.0, w, h, d,
                    show_voxel=True, show_ports=False, zone_alpha=0.05)
    ax.set_xlim(0, w); ax.set_ylim(0, d); ax.set_zlim(0, h)
    ax.set_box_aspect((w, d, h))
    ax.view_init(elev=20, azim=-55)
    ax.set_axis_off()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=72, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def _chair_options(h_val: int, d_val: int) -> list[tuple[str, str]]:
    """Return (left_mid, right_mid) pairs for all chair variants at given h and d."""
    pairs = []
    for mid, m in MODULES_3D.items():
        if (m.get("zone") == "chair_left"
                and m.get("h") == h_val
                and "_corr_" not in mid
                and not mid.startswith("_frs")):
            d_ok = m.get("scalable_d") or "whd_segments_fn" in m or m.get("d", 3) == d_val
            if not d_ok:
                continue
            right_mid = mid.replace("chair_left_", "chair_right_")
            if right_mid in MODULES_3D:
                pairs.append((mid, right_mid))
    return sorted(pairs)


def _table_options(h_val: int, wide_top: bool, d_val: int) -> list[str]:
    """Return table module IDs matching the given h, wide-top class, and d."""
    results = []
    for mid, m in MODULES_3D.items():
        if (m.get("zone") == "table"
                and m.get("h") == h_val
                and ("wide-top" in m.get("tags", [])) == wide_top
                and not mid.startswith("_frs")):
            d_ok = m.get("scalable_d") or "whd_segments_fn" in m or m.get("d", 3) == d_val
            if d_ok:
                results.append(mid)
    return sorted(results)


def _shelf_suffix(mid: str) -> str:
    for suf in ("_corr_r", "_corr_l"):
        if mid.endswith(suf):
            return suf
    return ""


def _shelf_base_id(shelf_mid: str) -> str | None:
    """Resolve a placed shelf's module_id back to a catalog id — placed shelves
    are sometimes a runtime-generated full-roof variant (``_frs3d_<base>_...``)."""
    if not shelf_mid.startswith("_frs3d_"):
        return shelf_mid
    rest = shelf_mid[len("_frs3d_"):]
    candidates = [k for k in _SHELF_CAT_3D if rest.startswith(k + "_")]
    return max(candidates, key=len) if candidates else None


def _shelf_options(shelf_mid: str, h_val: int, d_val: int) -> list[str]:
    """Return shelf module IDs in the same roof-style category as shelf_mid
    (e.g. all 'divided' variants if the current shelf is divided), matching h/d
    and which side (if any) of a corridor the current shelf is built for."""
    base = _shelf_base_id(shelf_mid)
    if base is None:
        return []
    category = _SHELF_CAT_3D.get(base)
    if not category or category == "any":
        return []
    suffix = _shelf_suffix(base)
    results = []
    for mid, m in MODULES_3D.items():
        if (m.get("zone") == "shelf"
                and not mid.startswith("_frs3d_")
                and _shelf_suffix(mid) == suffix
                and _SHELF_CAT_3D.get(mid) == category
                and m.get("h") == h_val):
            d_ok = m.get("scalable_d") or "whd_segments_fn" in m or m.get("d", 3) == d_val
            if d_ok:
                results.append(mid)
    return sorted(results)


def _picker_grid(section_key: str, options: list[str], current: str,
                 strip_parts: list[str], mtime3d: float, n_cols: int = 2) -> str | None:
    """Render a compact multi-column grid of thumbnail+button picks.
    Returns the clicked module_id this run, or None."""
    clicked = None
    cols = st.columns(n_cols)
    for i, mid in enumerate(options):
        label = mid
        for part in strip_parts:
            label = label.replace(part, "")
        label = label.strip("_") or mid
        is_active = mid == current
        with cols[i % n_cols]:
            st.image(_furniture_thumbnail_png(mid, mtime3d), use_container_width=True)
            if st.button(label, key=f"pick_{section_key}_{mid}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                clicked = mid
    return clicked


GRID_SIZES_CM = [20, 30, 40, 50]


def _grid_comparison_classes(result: list[dict]) -> tuple[int | None, int | None]:
    """Pull the cell-height (2 or 3) of the placed chair and table modules out of a
    solved dining result — this is the 'h2'/'h3' class scorecard_constants keys on."""
    chair_h_cells = table_h_cells = None
    for p in result:
        zone = MODULES[p["module_id"]]["zone"]
        if zone in ("chair_left", "chair_right") and chair_h_cells is None:
            chair_h_cells = p["h"]
        elif zone == "table" and table_h_cells is None:
            table_h_cells = p["h"]
    return chair_h_cells, table_h_cells


def _render_grid_comparison(result: list[dict], W: int, H: int, roof_style: str,
                            corridor: str, corridor_w: int, show_figures: bool) -> None:
    """Render the same solved dining schematic at four candidate grid pitches (cm/cell)
    and compare the resulting real-world dimensions against ergonomic targets."""
    st.caption(
        "Same solved layout — same W × H cell grid, same module choices — rebuilt at four "
        "different real-world grid pitches. The 2D schematic never changes; only how many "
        "centimetres each cell is worth does."
    )

    chair_h_cells, table_h_cells = _grid_comparison_classes(result)
    chair_target = SEAT_HEIGHT_BY_CLASS_CM.get(f"h{chair_h_cells}") if chair_h_cells else None
    table_target = TABLE_HEIGHT_BY_CLASS_CM.get(f"h{table_h_cells}") if table_h_cells else None
    corridor_w_cells = corridor_w if corridor != "none" else None

    max_footprint_w = W * max(GRID_SIZES_CM)
    px_per_cm = min(2.4, 260 / max_footprint_w)

    rows = []
    cols = st.columns(len(GRID_SIZES_CM))
    for grid_cm, col in zip(GRID_SIZES_CM, cols):
        footprint_w = W * grid_cm
        footprint_h = H * grid_cm
        chair_real = chair_h_cells * grid_cm if chair_h_cells else None
        table_real = table_h_cells * grid_cm if table_h_cells else None
        corridor_real = corridor_w_cells * grid_cm if corridor_w_cells else None
        delta_chair = (chair_real - chair_target) if (chair_real is not None and chair_target is not None) else None
        delta_table = (table_real - table_target) if (table_real is not None and table_target is not None) else None

        with col:
            label = f"**{grid_cm} cm**" + ("  ·  current" if grid_cm == 40 else "")
            st.markdown(label)
            fig = plot_section(result, W, H, show_figures=show_figures, roof_style=roof_style)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
            import matplotlib.pyplot as plt
            plt.close(fig)
            st.image(buf.getvalue(), width=max(60, round(footprint_w * px_per_cm)))
            st.caption(f"{footprint_w:.0f} × {footprint_h:.0f} cm")

        rows.append({
            "Grid (cm/cell)":     grid_cm,
            "Footprint (cm)":     f"{footprint_w:.0f} × {footprint_h:.0f}",
            "Chair seat ht (cm)": round(chair_real) if chair_real is not None else None,
            "Chair Δ (cm)":       round(delta_chair) if delta_chair is not None else None,
            "Table ht (cm)":      round(table_real) if table_real is not None else None,
            "Table Δ (cm)":       round(delta_table) if delta_table is not None else None,
            "Corridor width (cm)": round(corridor_real) if corridor_real is not None else None,
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    target_bits = []
    if chair_target is not None:
        target_bits.append(f"chair seat **{chair_target:.0f} cm**")
    if table_target is not None:
        target_bits.append(f"table height **{table_target:.0f} cm**")
    if target_bits:
        st.caption("Ergonomic targets (scorecard_constants.py): " + " · ".join(target_bits))

    if chair_target is not None and table_target is not None and chair_h_cells and table_h_cells:
        best_grid = min(
            GRID_SIZES_CM,
            key=lambda g: abs(g * chair_h_cells - chair_target) + abs(g * table_h_cells - table_target),
        )
        st.info(
            f"Closest ergonomic fit across chair + table: **{best_grid} cm** grid. "
            f"The system's actual grid is **40 cm**."
        )


st.set_page_config(page_title="Nomadic Engine", layout="wide")

# ── Compact layout — shrink spacing/type so the app fits without scrolling ────
st.markdown("""
<style>
  /* Streamlit's fixed top header (~3.75rem) sits over the content; padding-top
     must clear it or the first heading renders hidden underneath it. */
  .block-container { padding-top: 3.5rem !important; padding-bottom: 1rem !important; }
  section[data-testid="stSidebar"] .block-container { padding-top: 2rem !important; }

  h1 { font-size: 1.5rem !important; margin: 0 0 0.3rem !important; }
  h2 { font-size: 1.1rem !important; margin: 0.3rem 0 !important; }
  h3, h4 { font-size: 0.95rem !important; margin: 0.25rem 0 !important; }

  div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
  div[data-testid="stHorizontalBlock"] { gap: 0.6rem !important; }
  div[data-testid="stVerticalBlockBorderWrapper"] { gap: 0.3rem !important; }

  html, body, [class*="css"] { font-size: 13.5px !important; }
  div[data-testid="stMarkdownContainer"] p { margin-bottom: 0.25rem !important; }

  .stButton > button, .stDownloadButton > button {
    padding: 0.25rem 0.7rem !important; font-size: 12.5px !important; min-height: 1.8rem !important;
  }
  .stRadio [role="radiogroup"] { gap: 0.3rem !important; }
  .stRadio label, .stCheckbox label { font-size: 13px !important; }
  .stSlider, .stNumberInput, .stSelectbox, .stTextInput { margin-bottom: 0.1rem !important; }

  hr { margin: 0.5rem 0 !important; }
  [data-testid="stExpander"] summary { padding: 0.3rem 0.6rem !important; font-size: 13px !important; }

  /* cap rendered figure/thumbnail height so plots don't push the page into a scroll */
  div[data-testid="stImage"] img { max-height: 46vh !important; width: auto !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "onboarding_complete" not in st.session_state:
    st.session_state.onboarding_complete = False
if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 0
if "onboarding_answers" not in st.session_state:
    st.session_state.onboarding_answers = {}
if "onboarding_site" not in st.session_state:
    st.session_state.onboarding_site = None
if "current_spec" not in st.session_state:
    st.session_state.current_spec = None
if "dining_spec" not in st.session_state:
    st.session_state.dining_spec = {
        "dining_style":  "compact",
        "num_chairs":    2,
        "h":             7,
        "d":             3,
        "roof_style":    "any",
        "preferred_tags": [],
        "corridor_side": "none",
        "corridor_w":    2,
    }
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "needs_llm_call" not in st.session_state:
    st.session_state.needs_llm_call = False
if "pending_user_msg" not in st.session_state:
    st.session_state.pending_user_msg = None
if "_mode" not in st.session_state:
    st.session_state._mode = "2D"
if "module_overrides" not in st.session_state:
    st.session_state.module_overrides = {}


_CHAIR_HEIGHT_TAGS = {"low_chairs", "tall_chairs", "low_furniture", "tall_furniture"}
_TABLE_HEIGHT_TAGS = {"low_table",  "tall_table",  "low_furniture", "tall_furniture"}


def _stabilize_furniture_tags(result: list, current_tags: list) -> list:
    """After solving, detect which chair/table height class was placed and lock it
    into preferred_tags so subsequent re-solves (e.g. adding a corridor) stay stable."""
    has_chair = any(t in current_tags for t in _CHAIR_HEIGHT_TAGS)
    has_table = any(t in current_tags for t in _TABLE_HEIGHT_TAGS)
    if has_chair and has_table:
        return current_tags  # already explicitly set — nothing to do

    new_tags = list(current_tags)
    for p in result:
        mid = p["module_id"]
        if not has_chair and ("chair_left" in mid or "chair_right" in mid):
            h = p.get("h", 0)
            if h == 2:
                new_tags.append("low_chairs")
                has_chair = True
            elif h == 3:
                new_tags.append("tall_chairs")
                has_chair = True
        if not has_table and ("table_h2" in mid or "_table_h2" in mid):
            new_tags.append("low_table")
            has_table = True
        elif not has_table and ("table_h3" in mid or "_table_h3" in mid):
            new_tags.append("tall_table")
            has_table = True
    return new_tags


def _spec_summary(spec: dict) -> str:
    tags = spec.get("preferred_tags", [])
    parts = [
        f"style **{spec['dining_style']}**",
        f"**{spec['num_chairs']} chair{'s' if spec['num_chairs'] > 1 else ''}**",
        f"height **{spec['h']}**",
        f"depth **{spec['d']}**",
        f"roof **{spec['roof_style']}**",
    ]
    if tags:
        parts.append(f"tags **{', '.join(tags)}**")
    return " · ".join(parts)


def _initial_greeting(site: dict, answers: dict, spec: dict) -> str:
    _occ = {"solo": "just you", "couple": "two people",
            "family": "your family", "large_group": "a large group"}
    _pur = {"remote_work": "remote work", "retreat": "relaxation",
            "socialising": "hosting guests", "field_research": "field research"}
    occ_str = _occ.get(answers.get("occupants", ""), answers.get("occupants", ""))
    pur_str  = _pur.get(answers.get("purpose",   ""), answers.get("purpose",   ""))
    return (
        f"Hi! I'm your Nomadic Engine assistant. Based on your answers, I've designed "
        f"a dining space for **{occ_str}** at **{site['name']}**, "
        f"suited for **{pur_str}**.\n\n"
        f"{_spec_summary(spec)}\n\n"
        "Is there anything you'd like to adjust?"
    )


def _dining_suggestions(spec: dict, answers: dict) -> list[str]:
    sugg = []
    if spec.get("dining_style") == "compact":
        sugg.append("Make it more spacious and open")
    else:
        sugg.append("Make it more compact and efficient")
    if spec.get("h", 7) <= 8:
        sugg.append("Raise the ceiling — make it feel more dramatic")
    else:
        sugg.append("Lower the ceiling for a cosier feel")
    if "more_shelves" not in spec.get("preferred_tags", []):
        sugg.append("Add storage shelves above the table")
    else:
        sugg.append("Remove the overhead shelves")
    occ = answers.get("occupants", "couple")
    if occ in ("family", "large_group"):
        sugg.append("Make it better for hosting large gatherings")
    elif occ == "solo":
        sugg.append("Give the single-person setup more presence")
    else:
        sugg.append("Make it feel more intimate for two")
    return sugg


def _change_summary(old: dict, new: dict) -> str:
    labels = {
        "dining_style": "style", "num_chairs": "seating",
        "h": "height", "d": "depth", "roof_style": "roof", "preferred_tags": "tags",
    }
    changes = []
    for key, label in labels.items():
        if old.get(key) != new.get(key):
            val = new[key]
            if key == "num_chairs":
                val = f"{val} chair{'s' if val > 1 else ''}"
            elif key == "preferred_tags":
                val = ", ".join(val) if val else "none"
            changes.append(f"{label} → **{val}**")
    return "Updated: " + " · ".join(changes) if changes else "No changes."

# ── LLM settings (hoisted before st.stop so visible during onboarding) ────────
with st.sidebar:
    st.markdown("**LLM**")
    _MODELS = {
        "gemini-2.0-flash":  "Gemini 2.0 Flash  (Google, 1500/day free)",
        "gemini-2.5-flash":  "Gemini 2.5 Flash  (Google, 500/day free)",
        "gemini-2.5-pro":    "Gemini 2.5 Pro    (Google, 25/day free)",
        "gemini-1.5-flash":  "Gemini 1.5 Flash  (Google, legacy)",
        "gemma-3-27b-it":    "Gemma 3 27B       (Google, 14400/day free)",
        "gemma-3-12b-it":    "Gemma 3 12B       (Google, 14400/day free)",
        "gemma-4-31b-it":    "Gemma 4 31B       (Google, 14400/day free)",
        "gpt-4o":            "GPT-4o            (OpenAI, paid)",
        "gpt-4o-mini":       "GPT-4o mini       (OpenAI, paid, cheap)",
        "gpt-4-turbo":       "GPT-4 Turbo       (OpenAI, paid)",
        "claude-opus-4-8":   "Claude Opus 4     (Anthropic, paid)",
        "claude-sonnet-4-6": "Claude Sonnet 4   (Anthropic, paid)",
        "claude-haiku-4-5-20251001": "Claude Haiku 4    (Anthropic, paid, fast)",
    }
    _model_choice = st.selectbox(
        "Model",
        options=list(_MODELS.keys()),
        format_func=lambda m: _MODELS[m],
        index=list(_MODELS.keys()).index(
            st.session_state.get("llm_model", llm.MODEL)
        ) if st.session_state.get("llm_model", llm.MODEL) in _MODELS else 0,
    )
    if _model_choice != st.session_state.get("llm_model"):
        st.session_state.llm_model = _model_choice
        llm.MODEL = _model_choice

    # Show key input only for the active provider if not yet set
    _provider = llm.provider_for(llm.MODEL)
    _key_labels = {
        "google":    ("Gemini API key",    "AIza…",       "aistudio.google.com"),
        "openai":    ("OpenAI API key",    "sk-…",        "platform.openai.com"),
        "anthropic": ("Anthropic API key", "sk-ant-…",    "console.anthropic.com"),
    }
    if not llm.is_configured(_provider):
        _label, _placeholder, _url = _key_labels[_provider]
        _key_input = st.text_input(
            _label, type="password", placeholder=_placeholder,
            help=f"Get your key at {_url}",
        )
        if _key_input:
            llm.configure(_provider, _key_input, save=True)
            st.success("API key saved.")
            st.rerun()
        else:
            st.warning(f"Enter your {_label} to enable chat.")
    st.divider()

# ── Onboarding ────────────────────────────────────────────────────────────────
if not st.session_state.onboarding_complete:

    _QUESTIONS = [
        {
            "key": "occupants", "question": "How many people will be staying?",
            "options": [
                ("Solo",        "Just me, full independence",  "solo"),
                ("Couple",      "Two people, shared space",    "couple"),
                ("Family",      "3–4 people, shared setup",    "family"),
                ("Large group", "5+ people, full capacity",    "large_group"),
            ],
        },
        {
            "key": "duration", "question": "How long are you planning to stay?",
            "options": [
                ("1–4 weeks",   "Medium-term immersion",          "1_4_weeks"),
                ("1–3 months",  "Extended stay, full comfort",    "1_3_months"),
                ("A season",    "3–6 months, deep immersion",     "season"),
                ("Open-ended",  "Nomadic lifestyle, flexible",    "open_ended"),
            ],
        },
        {
            "key": "purpose", "question": "What's the primary purpose of this stay?",
            "options": [
                ("Remote work",     "Focus & deep work",   "remote_work"),
                ("Retreat",         "Rest & reset",        "retreat"),
                ("Socialising",     "Gather with others",  "socialising"),
                ("Field research",  "Study & observe",     "field_research"),
            ],
        },
        {
            "key": "priority", "question": "What matters most to you?",
            "options": [
                ("Energy",       "Off-grid autonomy",  "energy"),
                ("Privacy",      "Quiet & secluded",   "privacy"),
                ("Comfort",      "Refined living",     "comfort"),
                ("Connectivity", "Always online",      "connectivity"),
            ],
        },
        {
            "key": "scale", "question": "How much space do you need?",
            "options": [
                ("Compact",   "Efficient footprint", "compact"),
                ("Standard",  "Balanced layout",     "standard"),
                ("Generous",  "Room to breathe",     "generous"),
            ],
        },
    ]

    step = st.session_state.onboarding_step

    st.markdown("## // Onboarding")

    # ── Step 0: site selection ────────────────────────────────────────────────
    if step == 0:
        st.markdown("### Where will you deploy?")
        region = st.selectbox("Region", REGIONS)
        region_sites = sites_by_region(region)
        site_names = [s["name"] for s in region_sites]
        chosen_name = st.selectbox("Site", site_names)
        chosen_site = get_site(chosen_name)
        if chosen_site:
            st.caption(
                f"{chosen_site['location']} — "
                f"{chosen_site['temperature'].title()} / {chosen_site['precipitation'].title()} — "
                f"Climate: **{chosen_site['climate_zone'].replace('_', ' ').title()}**"
            )
        if st.button("Continue →", key="ob_site_next"):
            st.session_state.onboarding_site = chosen_site
            st.session_state.onboarding_step = 1
            st.rerun()

    # ── Steps 1–5: questions ──────────────────────────────────────────────────
    elif 1 <= step <= 5:
        q = _QUESTIONS[step - 1]
        total = len(_QUESTIONS)
        st.caption(f"{step:02d} / {total:02d}")
        st.markdown(f"### {q['question']}")
        st.write("")

        cols = st.columns(len(q["options"]))
        for col, (label, desc, value) in zip(cols, q["options"]):
            with col:
                selected = st.session_state.onboarding_answers.get(q["key"]) == value
                btn_type = "primary" if selected else "secondary"
                if st.button(label, key=f"ob_{q['key']}_{value}",
                             use_container_width=True, type=btn_type):
                    st.session_state.onboarding_answers = {
                        **st.session_state.onboarding_answers, q["key"]: value
                    }
                    if step < total:
                        st.session_state.onboarding_step = step + 1
                    st.rerun()
                st.caption(desc)

        st.write("")

        # last question: show proposal button after answer given
        if step == total and q["key"] in st.session_state.onboarding_answers:
            st.write("")
            if st.button("See my proposal →", key="ob_finish", type="primary"):
                with st.spinner("Generating your dwelling proposal…"):
                    spec, _ob_err = onboarding_to_spec(
                        st.session_state.onboarding_site,
                        st.session_state.onboarding_answers,
                    )
                if spec:
                    _num_chairs = spec.get("num_chairs", 2)
                    _site       = st.session_state.onboarding_site
                    _site_roof  = site_to_roof_style(_site) if _site else "any"
                    st.session_state.dining_spec.update({
                        "dining_style":   spec.get("dining_style", "compact"),
                        "num_chairs":     _num_chairs,
                        "h":              spec.get("h", 7),
                        "d":              spec.get("d", 3),
                        "roof_style":     spec.get("roof_style") or _site_roof,
                        "preferred_tags": spec.get("preferred_tags", []),
                        "corridor_side":  "right" if _num_chairs == 1 else "none",
                        "corridor_w":     2,
                    })
                    answers = st.session_state.onboarding_answers
                    site    = st.session_state.onboarding_site
                    st.session_state.chat_history = [{
                        "role": "assistant",
                        "content": _initial_greeting(site, answers, st.session_state.dining_spec),
                    }]
                    st.session_state.onboarding_complete = True
                else:
                    st.error(f"Gemini error: {_ob_err}" if _ob_err else "Couldn't reach Gemini — check your API key in the sidebar.")

        if st.button("← Back", key=f"ob_back_{step}"):
            st.session_state.onboarding_step = step - 1
            st.rerun()

    st.stop()

st.title("Nomadic Engine")

section_type = st.radio(
    "",
    options=["Dwelling", "Dining", "Kitchen", "Living", "Bed", "Bath"],
    horizontal=True,
    key="section_type",
    label_visibility="collapsed",
)

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Dwelling tab is always 3D — hide the toggle there.
    _active_tab = st.session_state.get("section_type", "Dwelling")
    if _active_tab != "Dwelling":
        mode = st.radio(
            "Mode",
            options=["2D", "3D"],
            index=["2D", "3D"].index(st.session_state._mode),
            horizontal=True,
            help="2D = section drawing.  3D = volumetric assembly with a depth axis.",
        )
        st.session_state._mode = mode
    else:
        mode = "3D"
        st.session_state._mode = "3D"
    st.divider()
    st.header("Parameters")

    # Safe defaults — overridden per section type; Dwelling manages its own corridor.
    corridor   = "none"
    corridor_w = 2

    if section_type == "Dining":
        _spec_corr   = st.session_state.dining_spec.get("corridor_side", "none")
        _disp_to_val = {"None": "none", "Corridor Left": "left", "Corridor Right": "right"}
        _val_to_disp = {v: k for k, v in _disp_to_val.items()}
        _corr_idx    = list(_disp_to_val.values()).index(_spec_corr) if _spec_corr in _val_to_disp else 0
        corridor_choice = st.radio(
            "Corridor",
            options=list(_disp_to_val.keys()),
            index=_corr_idx,
            horizontal=True,
            help="Adds a circulation corridor on one side.",
        )
        _new_corr_side = _disp_to_val[corridor_choice]
        if _new_corr_side != _spec_corr:
            st.session_state.dining_spec = {**st.session_state.dining_spec, "corridor_side": _new_corr_side}
        # auto-force corridor for 1-chair mode
        if st.session_state.dining_spec["num_chairs"] == 1 and _new_corr_side == "none":
            _new_corr_side = "right"
            st.session_state.dining_spec = {**st.session_state.dining_spec, "corridor_side": "right"}
        corridor   = f"corridor_{_new_corr_side}" if _new_corr_side != "none" else "none"
        _raw_cw    = st.session_state.dining_spec.get("corridor_w", 2)
        corridor_w = 4 if int(_raw_cw) >= 3 else 2  # clamp to valid values
    elif section_type in ("Living", "Bath"):
        corridor_choice = st.radio(
            "Corridor",
            options=["None", "Corridor Left", "Corridor Right"],
            horizontal=True,
            help="Adds a circulation corridor on one side.",
        )
        corridor = {
            "None": "none",
            "Corridor Left": "corridor_left",
            "Corridor Right": "corridor_right",
        }[corridor_choice]
        if corridor != "none":
            _cw_choice = st.radio(
                "Corridor width",
                options=["Narrow (2)", "Wide (4)"],
                horizontal=True,
            )
            corridor_w = 4 if "Wide" in _cw_choice else 2
        else:
            corridor_w = 2
    elif section_type == "Bed":
        # Bed always has corridor on the right — only compact vs spacious
        _cw_choice_b = st.radio(
            "Corridor",
            options=["Compact (2)", "Spacious (4)"],
            horizontal=True,
            key="bed_corridor_w",
        )
        corridor   = "corridor_right"
        corridor_w = 4 if "Spacious" in _cw_choice_b else 2
    elif section_type == "Kitchen":
        # Kitchen always has corridor on the right — only compact vs spacious
        _cw_choice_k = st.radio(
            "Corridor",
            options=["Compact (2)", "Spacious (4)"],
            horizontal=True,
            key="kitchen_corridor_w",
        )
        corridor   = "corridor_right"
        corridor_w = 4 if "Spacious" in _cw_choice_k else 2
    # Dwelling: corridor is configured inside its own section-params block below.

    st.divider()

    if section_type == "Dining":
        _spec = st.session_state.dining_spec

        # read-only spec summary — parameters are set by onboarding + chat
        dining_style  = _spec["dining_style"]
        num_chairs    = _spec["num_chairs"]
        roof_style    = _spec["roof_style"]

        dining_w   = (6 if dining_style == "compact" else 8) if num_chairs == 2 \
                     else (4 if dining_style == "compact" else 5)

        st.caption("Parameters set by onboarding + chat")
        st.markdown(
            f"Style: **{dining_style}** · Seating: **{num_chairs} chair{'s' if num_chairs > 1 else ''}** · "
            f"Roof: **{roof_style}**"
        )
        if _spec["preferred_tags"]:
            st.caption(f"Tags: `{'`, `'.join(_spec['preferred_tags'])}`")

        show_figures = st.checkbox(
            "Show human figures",
            value=False,
            help="Overlays seated / standing silhouettes.",
        )

        W = dining_w + (corridor_w if corridor != "none" else 0)
        st.caption(
            f"Section: **{W} × H**  ({dining_w} dining"
            + (f" + {corridor_w} corridor" if corridor != "none" else "")
            + ")"
        )
    elif section_type == "Living":
        living_combo_choice = st.radio(
            "Layout",
            options=["Full", "Sofa + TV"],
            horizontal=True,
            help="Full = sofa + table + TV unit.  Sofa+TV = sofa and TV unit only.",
        )
        living_combo = {"Full": "full", "Sofa + TV": "sofa_tv"}[living_combo_choice]

        living_choice = st.radio(
            "Section Style",
            options=["Compact", "Spacious"],
            horizontal=True,
            help="Compact = tighter layout, no gap.  Spacious = 1 filler column between elements.",
        )
        living_style = "compact" if living_choice == "Compact" else "spacious"

        # corridor_w is set by the corridor width radio above — never override it here
        if living_combo == "full":
            _inner_w = 7 if living_style == "compact" else 9
            W = _inner_w + (corridor_w if corridor != "none" else 0)
            st.caption(
                f"Section: **{W} × H**  ({_inner_w} living"
                + (f" + {corridor_w} corridor" if corridor != "none" else "")
                + ")"
            )
        else:
            # compact = 5 inner cols (0 gap), spacious = 6 inner cols (1 gap between sofa and element)
            _inner_w = 5 if living_style == "compact" else 6
            if corridor == "none":
                W = _inner_w
                st.caption(f"Section: **{W} × H**  ({_inner_w} inner)")
            else:
                W = _inner_w + corridor_w
                st.caption(f"Section: **{W} × H**  ({_inner_w} inner + {corridor_w} corridor)")

        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched", "Slanted"],
            horizontal=True,
            help="Plain = flat/dry.  Divided = temperate.  Pitched = cold/snow (gable).  Slanted = rainy/oceanic (lean-to).",
        )
        roof_style = roof_choice.lower()
    elif section_type == "Kitchen":
        _inner_w_k = 4  # 3 cabinet cols + 1 filler col; corridor always on right
        W = _inner_w_k + corridor_w  # min 6 (compact) or 8 (spacious)
        st.caption(f"Section: **{W} × H**  ({_inner_w_k} kitchen + {corridor_w} corridor)")
        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched", "Slanted"],
            horizontal=True,
            help="Plain = flat/dry.  Divided = temperate.  Pitched = cold/snow (gable).  Slanted = rainy/oceanic (lean-to).",
        )
        roof_style = roof_choice.lower()
        show_figures = st.checkbox(
            "Show human figures",
            value=False,
            help="Overlays a standing silhouette at the kitchen counter.",
        )
    elif section_type == "Bath":
        _inner_w_bath = 6
        W = _inner_w_bath + (corridor_w if corridor != "none" else 0)
        st.caption(
            f"Section: **{W} × H**  ({_inner_w_bath} bath"
            + (f" + {corridor_w} corridor" if corridor != "none" else "")
            + ")"
        )
        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched", "Slanted"],
            horizontal=True,
            help="Plain = flat/dry.  Divided = temperate.  Pitched = cold/snow (gable).  Slanted = rainy/oceanic (lean-to).",
        )
        roof_style = roof_choice.lower()
    elif section_type == "Dwelling":
        # ── Dwelling assembler ────────────────────────────────────────────────
        _dw_corr_choice = st.radio(
            "Corridor Side",
            options=["Right", "Left", "None"],
            horizontal=True,
            key="dw_corr_side",
        )
        _dw_corridor_side = {"Right": "right", "Left": "left", "None": "none"}[_dw_corr_choice]
        _dw_cw_choice = st.radio(
            "Corridor Width",
            options=["Narrow (2)", "Wide (4)"],
            horizontal=True,
            key="dw_cw",
        )
        _dw_corridor_w = 4 if "Wide" in _dw_cw_choice else 2

        _dw_W = int(st.number_input(
            "Section Width W (shared)",
            min_value=4, max_value=14, value=9, step=1, key="dw_W",
            help="Total width including corridor — shared across all sections.",
        ))
        _dw_H = int(st.number_input(
            "Section Height H (shared)",
            min_value=7, max_value=11, value=7, step=1, key="dw_H",
        ))

        if "dwelling_functions" not in st.session_state:
            st.session_state.dwelling_functions = [
                {"type": "dining",  "d": 3, "seed": 46, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                {"type": "kitchen", "d": 3, "seed": 45, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                {"type": "living",  "d": 3, "seed": 44, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                {"type": "bed",     "d": 3, "seed": 42, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                {"type": "bath",    "d": 3, "seed": 100, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
            ]

        st.markdown("**Sections** (front → back)")
        _SECTION_TYPES = ["dining", "kitchen", "living", "bed", "bath"]
        _fns = st.session_state.dwelling_functions
        _to_remove = None
        for _i, _fn in enumerate(_fns):
            _c1, _c2, _c3, _c4 = st.columns([2, 1, 1, 0.5])
            with _c1:
                _fn["type"] = st.selectbox(
                    "type", _SECTION_TYPES,
                    index=_SECTION_TYPES.index(_fn["type"]) if _fn["type"] in _SECTION_TYPES else 0,
                    key=f"dw_type_{_i}", label_visibility="collapsed",
                )
            with _c2:
                _fn["d"] = int(st.number_input(
                    "d", min_value=1, max_value=12, value=_fn["d"],
                    key=f"dw_d_{_i}", label_visibility="collapsed",
                ))
            with _c3:
                _fn["seed"] = int(st.number_input(
                    "seed", min_value=0, max_value=999999, value=_fn["seed"],
                    key=f"dw_seed_{_i}", label_visibility="collapsed",
                ))
            with _c4:
                if st.button("✕", key=f"dw_rm_{_i}"):
                    _to_remove = _i
        if _to_remove is not None:
            st.session_state.dwelling_functions.pop(_to_remove)
            st.rerun()
        _btn_add, _btn_reset = st.columns(2)
        with _btn_add:
            if st.button("+ Add section", key="dw_add", use_container_width=True):
                st.session_state.dwelling_functions.append(
                    {"type": "dining", "d": 3, "seed": 42, "dining_style": "compact",
                     "roof_style": "any", "living_combo": "full"}
                )
                st.rerun()
        with _btn_reset:
            if st.button("↺ Reset", key="dw_reset", use_container_width=True):
                st.session_state.dwelling_functions = [
                    {"type": "dining",  "d": 3, "seed": 46, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                    {"type": "kitchen", "d": 3, "seed": 45, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                    {"type": "living",  "d": 3, "seed": 44, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                    {"type": "bed",     "d": 3, "seed": 42, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                    {"type": "bath",    "d": 3, "seed": 100, "dining_style": "compact", "roof_style": "any", "living_combo": "full"},
                ]
                st.rerun()
        W = _dw_W  # so H/D block below has a value for W
        roof_style = "any"
    else:  # Bed
        _inner_w_b = 6  # bed_v5 is 6 cols wide (BED_ZONES_INNER "first 6"); corridor always on right
        W = _inner_w_b + corridor_w
        st.caption(f"Section: **{W} × H**  ({_inner_w_b} bed + {corridor_w} corridor)")

        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched", "Slanted"],
            horizontal=True,
            help="Plain = flat/dry.  Divided = temperate.  Pitched = cold/snow (gable).  Slanted = rainy/oceanic (lean-to).",
        )
        roof_style = roof_choice.lower()

    st.divider()

    if section_type != "Dwelling":
        seed = int(st.slider("Seed", min_value=0, max_value=1_000_000, value=42, step=1))
    else:
        seed = 42  # per-section seeds set in the dwelling functions list

    if section_type == "Dining":
        # h and d are LLM-controlled for dining — read directly from session state
        H = max(7, min(11, st.session_state.dining_spec["h"]))
        D = max(2, min(9, st.session_state.dining_spec["d"])) if mode == "3D" else 1
    elif section_type == "Dwelling":
        H = _dw_H
        D = 1
    else:
        if mode == "3D":
            H = int(st.number_input(
                "Height H", min_value=7, max_value=11, value=7, step=1,
                help="Grid height in cells.",
            ))
            # Bed defaults to 6 — the front-view bed modules (bed_v1..v4) are a
            # side profile extruded along D, so D *is* the bed's own length;
            # z_rule="full" always stretches the bed to fill whatever D is set,
            # so a too-small D (the generic default of 3) renders a squashed bed.
            _default_D = 6 if section_type == "Bed" else 3
            D = int(st.number_input(
                "Depth D", min_value=2, max_value=9, value=_default_D, step=1,
                help=("Depth in cells (2–9). A front-view bed's own length equals "
                      "this — 6 matches a real bed; lower values will squash it."
                      if section_type == "Bed" else "Depth in cells (2–9)."),
            ))
        else:
            H = int(st.number_input(
                "Height H", min_value=7, max_value=11, value=7, step=1,
                help="Grid height in cells.",
            ))
            D = 1

# ── Main area: chat column (left) + section column (right) ────────────────────
_picker_result = None  # set by section_col, consumed by picker_col
chat_col, section_col, picker_col = st.columns([1.4, 2.1, 0.7], gap="medium")

# ── Chat column ───────────────────────────────────────────────────────────────
with chat_col:
    st.markdown("**Chat**")
    with st.container(height=380, border=True):
        if not st.session_state.chat_history:
            st.caption("No messages yet — describe your dining space below.")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Suggestion chips — only shown before the first user message
    _history = st.session_state.chat_history
    if (len(_history) == 1 and _history[0]["role"] == "assistant"
            and section_type == "Dining"):
        _suggs = _dining_suggestions(
            st.session_state.dining_spec,
            st.session_state.get("onboarding_answers", {}),
        )
        for _s in _suggs:
            if st.button(_s, key=f"sugg_{_s[:30]}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user",      "content": _s})
                st.session_state.chat_history.append({"role": "assistant", "content": "Generating…"})
                st.session_state.needs_llm_call  = True
                st.session_state.pending_user_msg = _s
                st.rerun()

    _disabled = section_type != "Dining"
    _placeholder = "Describe your dining space…" if not _disabled else "Chat available for Dining only"
    _user_input = st.chat_input(_placeholder, disabled=_disabled, key="chat_input")

    if _user_input and _user_input.strip():
        st.session_state.chat_history.append({"role": "user",      "content": _user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": "Generating…"})
        st.session_state.needs_llm_call  = True
        st.session_state.pending_user_msg = _user_input
        st.rerun()

    if st.session_state.needs_llm_call and st.session_state.pending_user_msg:
        with st.spinner("Generating…"):
            _pending = st.session_state.pending_user_msg
            # Pass history excluding the pending user msg and "Generating…" placeholder
            _hist = st.session_state.chat_history[:-2]
            _new, _reply = chat_modify_dining(st.session_state.dining_spec, _pending, history=_hist)
        if _new is not None:
            st.session_state.dining_spec.update(_new)
            st.session_state.module_overrides = {}
        _hist = st.session_state.chat_history
        if _hist and _hist[-1]["content"] == "Generating…":
            _hist[-1] = {"role": "assistant", "content": _reply}
        else:
            _hist.append({"role": "assistant", "content": _reply})
        st.session_state.needs_llm_call  = False
        st.session_state.pending_user_msg = None
        st.rerun()

# ── Section column ─────────────────────────────────────────────────────────────
with section_col:
    tab_sec, tab_lib, tab_grid = st.tabs(["Section", "Module Library", "Grid Comparison"])

    # ── Module Library tab ────────────────────────────────────────────────────
    with tab_lib:
        _mtime  = os.path.getmtime(_MODULES_PATH)
        _dmtime = os.path.getmtime(_DRAWING_PATH)
        _lib_sections = ["Dining", "Kitchen", "Living", "Bed"]
        for _sec in _lib_sections:
            with st.expander(_sec, expanded=(_sec == section_type)):
                if mode == "3D":
                    _m3d_mtime = os.path.getmtime(_MODULES3D_PATH)
                    _lib_groups_3d = get_library_3d_by_zone(_sec)
                    for _zone_label_3d, _zone_mods_3d in _lib_groups_3d:
                        st.markdown(f"**{_zone_label_3d}**")
                        st.image(
                            _zone_group_3d_png(_sec, _zone_label_3d, len(_zone_mods_3d), _m3d_mtime),
                            use_container_width=True,
                        )
                elif _sec in _SECTION_ZONES:
                    _lib_groups = get_library_by_zone(_sec)
                    for _zone_label, _zone_mods in _lib_groups:
                        st.markdown(f"**{_zone_label}**")
                        st.image(
                            _zone_group_png(_sec, _zone_label, len(_zone_mods), _mtime, _dmtime),
                            use_container_width=True,
                        )
                else:
                    st.info(f"**{_sec}** module library — coming soon.")

    # ── Section tab ───────────────────────────────────────────────────────────
    with tab_sec:
        if section_type == "Dining":
            if num_chairs == 1 and corridor == "none":
                st.warning(
                    "1-chair mode requires a corridor — "
                    "select Corridor Left or Corridor Right in the sidebar."
                )
            else:
                if roof_style == "pitched" and corridor != "none" and corridor_w == 2:
                    st.info(
                        "Pitched mode + corridor: the solver randomly combines slanted shelf, "
                        "lean-to corridor, or both — change Seed to explore variations."
                    )
                _preferred = st.session_state.dining_spec.get("preferred_tags", [])
                with st.spinner("Solving…"):
                    if mode == "2D":
                        result = solve(W, H, seed, corridor, corridor_w, dining_style, roof_style,
                                       preferred_tags=_preferred)
                    else:
                        result = solve3d(W, H, D, seed, corridor, corridor_w, dining_style, roof_style,
                                         preferred_tags=_preferred,
                                         zone_overrides=st.session_state.module_overrides or None)

                if result is None:
                    st.error("No valid section found — try a different seed or combination.")
                else:
                    # Lock furniture heights from this solve so they survive re-solves
                    _stable = _stabilize_furniture_tags(
                        result, st.session_state.dining_spec.get("preferred_tags", [])
                    )
                    if _stable != st.session_state.dining_spec.get("preferred_tags", []):
                        st.session_state.dining_spec = {
                            **st.session_state.dining_spec, "preferred_tags": _stable
                        }

                    if mode == "2D":
                        st.pyplot(plot_section(result, W, H,
                                               show_figures=show_figures, roof_style=roof_style))
                    else:
                        st.pyplot(plot_section_3d(result, W, H, D))
                        st.download_button(
                            "Export Rhino Script (.py)",
                            data=export_section_3d_rhino(result, W, H, D, "dining"),
                            file_name="dining_3d.py",
                            mime="text/plain",
                        )
                        _picker_result = result  # pass to picker_col
                        with st.expander("2D slice at depth z", expanded=False):
                            z_slice = st.slider(
                                "z position (slice through depth)",
                                min_value=0.5, max_value=float(D) - 0.5,
                                value=0.5, step=1.0,
                            )
                            st.pyplot(plot_slice_2d(result, W, H, D, z=z_slice,
                                                    show_figures=show_figures, roof_style=roof_style))

                    with st.expander("Placement details"):
                        for p in result:
                            off  = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
                                    else f"({p['x_off']:.0f}, {p['y_off']:.0f}, {p['z_off']:.0f})")
                            size = (f"{p['w']}w × {p['h']}h" if mode == "2D"
                                    else f"{p['w']}w × {p['h']}h × {p['d']}d")
                            st.write(f"**{p['module_id']}** — offset {off}  size {size}")
                    with st.expander("Circuit validation"):
                        if mode == "2D":
                            ok_adj = check_adjacency(result)
                            ok_cir = check_circuit(result)
                        else:
                            ok_adj = check_adjacency_3d(result)
                            ok_cir = check_circuit_3d(result)
                        st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
                        st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")

        elif section_type == "Kitchen":
            with st.spinner("Solving…"):
                if mode == "2D":
                    result = solve(W, H, seed, corridor, corridor_w, roof_style=roof_style, section="kitchen")
                else:
                    result = solve3d(W, H, D, seed, corridor, corridor_w, roof_style=roof_style, section="kitchen")
            if result is None:
                st.error("No valid section found — try a different seed or height.")
            else:
                if mode == "2D":
                    st.pyplot(plot_section(result, W, H, show_figures=show_figures, roof_style=roof_style))
                else:
                    st.pyplot(plot_section_3d(result, W, H, D))
                    with st.expander("2D slice at depth z", expanded=False):
                        z_slice = st.slider(
                            "z position (slice through depth)",
                            min_value=0.5, max_value=float(D) - 0.5,
                            value=0.5, step=1.0, key="kitchen_z_slice",
                        )
                        st.pyplot(plot_slice_2d(result, W, H, D, z=z_slice,
                                                show_figures=show_figures, roof_style=roof_style))
                with st.expander("Placement details"):
                    for p in result:
                        off  = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
                                else f"({p['x_off']:.0f}, {p['y_off']:.0f}, {p['z_off']:.0f})")
                        size = (f"{p['w']}w × {p['h']}h" if mode == "2D"
                                else f"{p['w']}w × {p['h']}h × {p['d']}d")
                        st.write(f"**{p['module_id']}** — offset {off}  size {size}")
                with st.expander("Circuit validation"):
                    if mode == "2D":
                        ok_adj = check_adjacency(result)
                        ok_cir = check_circuit(result)
                    else:
                        ok_adj = check_adjacency_3d(result)
                        ok_cir = check_circuit_3d(result)
                    st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
                    st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")

        elif section_type == "Living":
            with st.spinner("Solving…"):
                if mode == "2D":
                    result = solve(W, H, seed, corridor, corridor_w, living_style, roof_style,
                                   section="living", living_combo=living_combo)
                else:
                    result = solve3d(W, H, D, seed, corridor, corridor_w, living_style, roof_style,
                                     section="living", living_combo=living_combo)
            if result is None:
                st.error("No valid section found — try a different seed or height.")
            else:
                if mode == "2D":
                    st.pyplot(plot_section(result, W, H, roof_style=roof_style))
                    with st.expander("Placement details"):
                        for p in result:
                            st.write(
                                f"**{p['module_id']}** — "
                                f"offset ({p['x_off']:.0f}, {p['y_off']:.0f})  "
                                f"size {p['w']}w × {p['h']}h"
                            )
                    with st.expander("Circuit validation"):
                        ok_adj = check_adjacency(result)
                        ok_cir = check_circuit(result)
                        st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
                        st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")
                else:
                    st.pyplot(plot_section_3d(result, W, H, D))

        elif section_type == "Bath":
            with st.spinner("Solving…"):
                if mode == "2D":
                    result = solve(W, H, seed, corridor, corridor_w, roof_style=roof_style, section="bath")
                else:
                    result = solve3d(W, H, D, seed, corridor, corridor_w, roof_style=roof_style, section="bath")
            if result is None:
                st.error("No valid section found — try a different seed or height.")
            else:
                if mode == "2D":
                    st.pyplot(plot_section(result, W, H, roof_style=roof_style))
                else:
                    st.pyplot(plot_section_3d(result, W, H, D))
                with st.expander("Placement details"):
                    for p in result:
                        off  = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
                                else f"({p['x_off']:.0f}, {p['y_off']:.0f}, {p['z_off']:.0f})")
                        size = (f"{p['w']}w × {p['h']}h" if mode == "2D"
                                else f"{p['w']}w × {p['h']}h × {p['d']}d")
                        st.write(f"**{p['module_id']}** — offset {off}  size {size}")
                with st.expander("Circuit validation"):
                    if mode == "2D":
                        ok_adj = check_adjacency(result)
                        ok_cir = check_circuit(result)
                    else:
                        ok_adj = check_adjacency_3d(result)
                        ok_cir = check_circuit_3d(result)
                    st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
                    st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")

        elif section_type == "Dwelling":
            _dw_spec = {
                "corridor_side": _dw_corridor_side,
                "corridor_w":    _dw_corridor_w,
                "W":             _dw_W,
                "H":             _dw_H,
                "functions":     st.session_state.dwelling_functions,
            }
            with st.spinner("Solving dwelling…"):
                _dw_sections = solve_dwelling_3d(_dw_spec)

            _dw_failed = [s for s in _dw_sections if s["placed"] is None]
            if _dw_failed:
                st.warning(
                    f"{len(_dw_failed)} section(s) failed to solve: "
                    + ", ".join(s['type'] for s in _dw_failed)
                    + " — try adjusting W or seeds."
                )
            _col_3d, _col_plan = st.columns([3, 1])
            with _col_3d:
                st.pyplot(plot_dwelling_3d(
                    _dw_sections,
                    corridor_side=_dw_corridor_side,
                    corridor_w=_dw_corridor_w,
                ))
            with _col_plan:
                st.caption("Plan view")
                st.pyplot(plot_plan_view(_dw_sections, _dw_corridor_side, _dw_corridor_w))

            # ── Section picker — click to jump to that section's editor ──────
            st.markdown("**Edit a section:**")
            _jump_cols = st.columns(len(_dw_sections))
            for _ci, (_sc, _col) in enumerate(zip(_dw_sections, _jump_cols)):
                with _col:
                    _label = _sc["type"].capitalize()
                    _ok    = _sc["placed"] is not None
                    if st.button(
                        _label if _ok else f"{_label} ✗",
                        key=f"dw_jump_{_ci}",
                        use_container_width=True,
                        disabled=not _ok,
                        type="primary" if _ok else "secondary",
                    ):
                        st.session_state["_jump_section"] = _sc["type"].capitalize()
                        st.rerun()

            # Apply jump if requested
            if "_jump_section" in st.session_state:
                _jump = st.session_state.pop("_jump_section")
                _valid = ["Dining", "Kitchen", "Living", "Bed", "Bath"]
                if _jump in _valid:
                    st.info(f"→ Use the **Section** radio above to switch to **{_jump}**.")

        else:  # Bed
            with st.spinner("Solving…"):
                if mode == "2D":
                    result = solve(W, H, seed, corridor, corridor_w, roof_style=roof_style, section="bed")
                else:
                    result = solve3d(W, H, D, seed, corridor, corridor_w, roof_style=roof_style, section="bed")
            if result is None:
                st.error("No valid section found — try a different seed or height.")
            else:
                if mode == "2D":
                    st.pyplot(plot_section(result, W, H, roof_style=roof_style))
                else:
                    st.pyplot(plot_section_3d(result, W, H, D))
                    with st.expander("2D slice at depth z", expanded=False):
                        z_slice = st.slider(
                            "z position (slice through depth)",
                            min_value=0.5, max_value=float(D) - 0.5,
                            value=0.5, step=1.0, key="bed_z_slice",
                        )
                        st.pyplot(plot_slice_2d(result, W, H, D, z=z_slice, roof_style=roof_style))
                with st.expander("Placement details"):
                    for p in result:
                        off  = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
                                else f"({p['x_off']:.0f}, {p['y_off']:.0f}, {p['z_off']:.0f})")
                        size = (f"{p['w']}w × {p['h']}h" if mode == "2D"
                                else f"{p['w']}w × {p['h']}h × {p['d']}d")
                        st.write(f"**{p['module_id']}** — offset {off}  size {size}")
                with st.expander("Circuit validation"):
                    if mode == "2D":
                        ok_adj = check_adjacency(result)
                        ok_cir = check_circuit(result)
                    else:
                        ok_adj = check_adjacency_3d(result)
                        ok_cir = check_circuit_3d(result)
                    st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
                    st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")

    # ── Grid Comparison tab ────────────────────────────────────────────────────
    with tab_grid:
        if section_type != "Dining":
            st.info("Grid comparison is currently available for the Dining section only.")
        elif num_chairs == 1 and corridor == "none":
            st.info("Set a valid dining configuration in the Section tab first (1-chair mode needs a corridor).")
        else:
            _preferred_cmp = st.session_state.dining_spec.get("preferred_tags", [])
            with st.spinner("Solving…"):
                _cmp_result = solve(W, H, seed, corridor, corridor_w, dining_style, roof_style,
                                    preferred_tags=_preferred_cmp)
            if _cmp_result is None:
                st.warning("No valid section found for this configuration — try a different seed.")
            else:
                _render_grid_comparison(_cmp_result, W, H, roof_style, corridor, corridor_w, show_figures)

# ── Picker column (right) ─────────────────────────────────────────────────────
with picker_col:
    if _picker_result and mode == "3D":
        _mtime3d = os.path.getmtime(_MODULES3D_PATH)

        # ── Chair style ───────────────────────────────────────────────────────
        placed_cl = next(
            (p for p in _picker_result
             if MODULES_3D.get(p["module_id"], {}).get("zone") == "chair_left"),
            None)
        if placed_cl:
            h_val = placed_cl["h"]
            ch_opts = _chair_options(h_val, D)
            if len(ch_opts) > 1:
                st.markdown("**Chair style**")
                current_left = st.session_state.module_overrides.get(
                    "chair_left", placed_cl["module_id"])
                left_ids = [left_mid for left_mid, _right_mid in ch_opts]
                clicked = _picker_grid(
                    "chair", left_ids, current_left,
                    ["chair_left_", f"h{h_val}_"], _mtime3d,
                )
                if clicked:
                    right_mid = next(r for l, r in ch_opts if l == clicked)
                    st.session_state.module_overrides["chair_left"]  = clicked
                    st.session_state.module_overrides["chair_right"] = right_mid
                    st.rerun()

        st.divider()

        # ── Table style ───────────────────────────────────────────────────────
        placed_t = next(
            (p for p in _picker_result
             if MODULES_3D.get(p["module_id"], {}).get("zone") == "table"),
            None)
        if placed_t:
            t_mid  = placed_t["module_id"]
            t_h    = placed_t["h"]
            t_wide = "wide-top" in MODULES_3D.get(t_mid, {}).get("tags", [])
            t_opts = _table_options(t_h, t_wide, D)
            if len(t_opts) > 1:
                st.markdown("**Table style**")
                current_t = st.session_state.module_overrides.get("table", t_mid)
                clicked = _picker_grid(
                    "table", t_opts, current_t,
                    ["table_", f"h{t_h}_"], _mtime3d,
                )
                if clicked:
                    st.session_state.module_overrides["table"] = clicked
                    st.rerun()

        st.divider()

        # ── Shelf / roof style ────────────────────────────────────────────────
        # Locked to the current shelf's roof-style category — e.g. if the
        # placed shelf is "divided", only other "divided" variants are offered.
        placed_sh = next(
            (p for p in _picker_result
             if MODULES_3D.get(p["module_id"], {}).get("zone") == "shelf"),
            None)
        if placed_sh:
            sh_mid = placed_sh["module_id"]
            sh_h   = placed_sh["h"]
            sh_opts = _shelf_options(sh_mid, sh_h, D)
            if len(sh_opts) > 1:
                st.markdown("**Shelf / roof style**")
                current_sh = st.session_state.module_overrides.get(
                    "shelf", _shelf_base_id(sh_mid) or sh_mid)
                clicked = _picker_grid(
                    "shelf", sh_opts, current_sh,
                    ["shelf_"], _mtime3d,
                )
                if clicked:
                    st.session_state.module_overrides["shelf"] = clicked
                    st.rerun()
