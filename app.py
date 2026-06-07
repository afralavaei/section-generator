import io
import os
import streamlit as st

from solver import solve, check_adjacency, check_circuit
from drawing import plot_section, plot_module_library, plot_grid_only, _SECTION_ZONES
from solver3d import solve3d, check_adjacency_3d, check_circuit_3d
from viewer3d import plot_section_3d, plot_module_library_3d, plot_slice_2d
from llm import chat_modify_dining, onboarding_to_spec
from sites import SITES, REGIONS, get_site, sites_by_region

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
def _module_library_3d_png(mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    fig = plot_module_library_3d()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=80, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


st.set_page_config(page_title="Nomadic Engine", layout="wide")

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
            if "_h2_" in mid or mid.endswith("_h2"):
                new_tags.append("low_chairs")
                has_chair = True
            elif "_h3_" in mid or mid.endswith("_h3"):
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
                    spec = onboarding_to_spec(
                        st.session_state.onboarding_site,
                        st.session_state.onboarding_answers,
                    )
                if spec:
                    _num_chairs = spec.get("num_chairs", 2)
                    st.session_state.dining_spec.update({
                        "dining_style":   spec.get("dining_style", "compact"),
                        "num_chairs":     _num_chairs,
                        "h":              spec.get("h", 7),
                        "d":              spec.get("d", 3),
                        "roof_style":     spec.get("roof_style", "any"),
                        "preferred_tags": spec.get("preferred_tags", []),
                        "corridor_side":  "right" if _num_chairs == 1 else "none",
                        "corridor_w":     2,
                    })
                    answers = st.session_state.onboarding_answers
                    site    = st.session_state.onboarding_site
                    st.session_state.chat_history = [{
                        "role": "assistant",
                        "content": (
                            f"Proposal generated for **{site['name']}** "
                            f"({answers['occupants'].replace('_', ' ')} · "
                            f"{answers['duration'].replace('_', ' ')} · "
                            f"{answers['purpose'].replace('_', ' ')} · "
                            f"{answers['scale']}).\n\n"
                            f"Dining: {_spec_summary(st.session_state.dining_spec)}"
                        ),
                    }]
                    st.session_state.onboarding_complete = True
                else:
                    st.error("Couldn't reach the LLM — is the wrapper running at http://127.0.0.1:8000?")

        if st.button("← Back", key=f"ob_back_{step}"):
            st.session_state.onboarding_step = step - 1
            st.rerun()

    st.stop()

st.title("Nomadic Engine")

section_type = st.radio(
    "",
    options=["Dining", "Kitchen", "Living", "Bed"],
    horizontal=True,
    key="section_type",
    label_visibility="collapsed",
)

# ── Pending LLM call handler (runs before rendering so result shows on same rerun) ──
if st.session_state.needs_llm_call and st.session_state.pending_user_msg:
    _pending = st.session_state.pending_user_msg
    _old     = dict(st.session_state.dining_spec)
    _new     = chat_modify_dining(st.session_state.dining_spec, _pending)
    if _new:
        st.session_state.dining_spec.update(_new)
        _reply = _change_summary(_old, st.session_state.dining_spec)
    else:
        _reply = "⚠️ Couldn't reach the LLM — is the wrapper running at http://127.0.0.1:8000?"
    _hist = st.session_state.chat_history
    if _hist and _hist[-1]["content"] == "Generating…":
        _hist[-1] = {"role": "assistant", "content": _reply}
    else:
        _hist.append({"role": "assistant", "content": _reply})
    st.session_state.needs_llm_call = False
    st.session_state.pending_user_msg = None
    st.rerun()

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    mode = st.radio(
        "Mode",
        options=["2D", "3D"],
        horizontal=True,
        key="mode",
        help="2D = section drawing.  3D = volumetric assembly with a depth axis.",
    )
    st.divider()
    st.header("Parameters")

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
    elif section_type != "Kitchen":
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
        corridor_w = 2
    else:
        corridor   = "none"
        corridor_w = 2

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
        living_choice = st.radio(
            "Section Style",
            options=["Compact", "Spacious"],
            horizontal=True,
            help="Compact = flush sofa (W=7).  Spacious = wide coffee table with gap columns (W=9).",
        )
        living_style = "compact" if living_choice == "Compact" else "spacious"
        corridor_w = 2 if living_style == "compact" else 4
        _inner_w = 7 if living_style == "compact" else 9
        W = _inner_w + (corridor_w if corridor != "none" else 0)
        st.caption(
            f"Section: **{W} × H**  ({_inner_w} living"
            + (f" + {corridor_w} corridor" if corridor != "none" else "")
            + ")"
        )

        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched"],
            horizontal=True,
            help="Plain = flat top bar.  Divided = internal shelves/dividers.  Pitched = lean-to or gable ridge.",
        )
        roof_style = roof_choice.lower()
    elif section_type == "Kitchen":
        W = 6
        st.caption("Section: **6 × H**")
        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched"],
            horizontal=True,
            help="Plain = flat top bar.  Divided = internal shelves/dividers.  Pitched = lean-to or gable ridge.",
        )
        roof_style = roof_choice.lower()
        show_figures = st.checkbox(
            "Show human figures",
            value=False,
            help="Overlays a standing silhouette at the kitchen counter.",
        )
    else:
        _inner_w = 8  # Bed
        W = _inner_w + (corridor_w if corridor != "none" else 0)
        st.caption(
            f"Section: **{W} × H**  ({_inner_w} bed"
            + (f" + {corridor_w} corridor" if corridor != "none" else "")
            + ")"
        )

        roof_choice = st.radio(
            "Roof Style",
            options=["Any", "Plain", "Divided", "Pitched"],
            horizontal=True,
            help="Plain = flat top bar.  Divided = internal shelves/dividers.  Pitched = lean-to or gable ridge.",
        )
        roof_style = roof_choice.lower()
        living_style = "spacious"

    st.divider()

    seed = int(st.slider("Seed", min_value=0, max_value=1_000_000, value=42, step=1))

    if section_type == "Dining":
        # h and d are LLM-controlled for dining — read directly from session state
        H = max(7, min(11, st.session_state.dining_spec["h"]))
        D = max(2, min(9, st.session_state.dining_spec["d"])) if mode == "3D" else 1
    else:
        if mode == "3D":
            H = int(st.number_input(
                "Height H", min_value=7, max_value=11, value=7, step=1,
                help="Grid height in cells.",
            ))
            D = int(st.number_input(
                "Depth D", min_value=2, max_value=9, value=3, step=1,
                help="Depth in cells (2–9).",
            ))
        else:
            H = int(st.number_input(
                "Height H", min_value=7, max_value=11, value=7, step=1,
                help="Grid height in cells.",
            ))
            D = 1

# ── Main area: chat column (left) + section column (right) ────────────────────
chat_col, section_col = st.columns([1, 2], gap="medium")

# ── Chat column ───────────────────────────────────────────────────────────────
with chat_col:
    st.markdown("**Chat**")
    with st.container(height=480, border=True):
        if not st.session_state.chat_history:
            st.caption("No messages yet — describe your dining space below.")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    with st.form("chat_form", clear_on_submit=True):
        _user_input = st.text_input(
            "msg", placeholder="Describe your dining space…",
            label_visibility="collapsed",
        )
        _send = st.form_submit_button("Send →", use_container_width=True)

    if _send and _user_input.strip():
        if section_type == "Dining":
            st.session_state.chat_history.append({"role": "user",      "content": _user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": "Generating…"})
            st.session_state.needs_llm_call  = True
            st.session_state.pending_user_msg = _user_input
            st.rerun()
        else:
            st.info("Chat is available for the Dining section only.")

# ── Section column ─────────────────────────────────────────────────────────────
with section_col:
    tab_sec, tab_lib = st.tabs(["Section", "Module Library"])

    # ── Module Library tab ────────────────────────────────────────────────────
    with tab_lib:
        if mode == "3D":
            st.caption(
                "All module variants at unit scale (1 cell = 1 unit).  "
                "Red lines = geometry.  Green dots = ports."
            )
            _m3d_mtime = os.path.getmtime(_MODULES3D_PATH)
            st.image(_module_library_3d_png(_m3d_mtime), use_container_width=True)
        elif section_type in _SECTION_ZONES:
            st.caption(
                "All module variants at unit scale (1 cell = 1 unit).  "
                "Red lines = geometry.  Green dots = ports.  Coloured fill = zone type."
            )
            _mtime  = os.path.getmtime(_MODULES_PATH)
            _dmtime = os.path.getmtime(_DRAWING_PATH)
            st.image(_module_library_png(section_type, _mtime, _dmtime), use_container_width=True)
        else:
            st.info(f"**{section_type} module library** — modules will be drawn here once confirmed.")

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
                                         preferred_tags=_preferred)

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
                    result = solve(W, H, seed, "none", 2, roof_style=roof_style, section="kitchen")
                else:
                    result = solve3d(W, H, D, seed, "none", 2, roof_style=roof_style, section="kitchen")
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
            if mode == "3D":
                st.info("3D mode for Living is not yet available — switch to 2D.")
            else:
                with st.spinner("Solving…"):
                    result = solve(W, H, seed, corridor, corridor_w, living_style, roof_style, section="living")
                if result is None:
                    st.error("No valid section found — try a different seed or height.")
                else:
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
            st.pyplot(plot_grid_only(W, H, section_type, corridor, corridor_w))

