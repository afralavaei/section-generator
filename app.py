import io
import os
import streamlit as st

from solver import solve, check_adjacency, check_circuit
from drawing import plot_section, plot_module_library, plot_grid_only, _SECTION_ZONES
from solver3d import solve3d, check_adjacency_3d, check_circuit_3d
from viewer3d import plot_section_3d, plot_module_library_3d, plot_slice_2d

_MODULES_PATH  = os.path.join(os.path.dirname(__file__), "modules.py")
_DRAWING_PATH  = os.path.join(os.path.dirname(__file__), "drawing.py")


@st.cache_data
def _module_library_png(section: str, mtime: float, drawing_mtime: float) -> bytes:
    import matplotlib.pyplot as plt
    fig = plot_module_library(section)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


st.set_page_config(page_title="Nomadic Engine", layout="wide")
st.title("Nomadic Engine")

section_type = st.radio(
    "",
    options=["Dining", "Kitchen", "Living", "Bed"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    mode = st.radio(
        "Mode",
        options=["2D", "3D"],
        horizontal=True,
        help="2D = section drawing.  3D = volumetric assembly with a depth axis.",
    )
    st.divider()
    st.header("Parameters")

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

    corridor_w = 2  # overridden below once dining_style is known

    st.divider()

    if section_type == "Dining":
        chairs_choice = st.radio(
            "Seating",
            options=["2 Chairs", "1 Chair"],
            horizontal=True,
            help="2 Chairs = both sides occupied.  1 Chair = single-sided, requires a corridor.",
        )
        num_chairs = 2 if chairs_choice == "2 Chairs" else 1

        dining_choice = st.radio(
            "Table Style",
            options=["Compact", "Spacious"],
            horizontal=True,
            help="Compact = narrow tables.  Spacious = wide-top tables with 1-col gap.",
        )
        dining_style = "compact" if dining_choice == "Compact" else "spacious"
        corridor_w = 2 if dining_style == "compact" else 4
        if num_chairs == 2:
            dining_w = 6 if dining_style == "compact" else 8
        else:
            dining_w = 4 if dining_style == "compact" else 5

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
            help="Overlays seated / standing silhouettes.",
        )

        W = dining_w + (corridor_w if corridor != "none" else 0)
        st.caption(
            f"Section: **{W} × H**  ({dining_w} dining"
            + (f" + {corridor_w} corridor" if corridor != "none" else "")
            + ")"
        )
    else:
        _inner_w = {"Kitchen": 6, "Living": 8, "Bed": 8}[section_type]
        W = _inner_w + (corridor_w if corridor != "none" else 0)
        st.caption(
            f"Section: **{W} × H**  ({_inner_w} {section_type.lower()}"
            + (f" + {corridor_w} corridor" if corridor != "none" else "")
            + ")"
        )

    st.divider()

    seed = int(st.slider("Seed", min_value=0, max_value=1_000_000, value=42, step=1))
    H = int(st.number_input(
        "Height H", min_value=7, max_value=20, value=7, step=1,
        help="Grid height in cells.",
    ))

    if mode == "3D":
        D = int(st.number_input(
            "Depth D", min_value=1, max_value=10, value=2, step=1,
            help="Number of depth cells. Every module is auto-extruded along z.",
        ))
    else:
        D = 1

# ── Main area ─────────────────────────────────────────────────────────────────
tab_sec, tab_lib, tab_test = st.tabs(["Section", "Module Library", "Native 3D Test"])

# ── Module Library tab ────────────────────────────────────────────────────────
with tab_lib:
    if mode == "3D":
        st.caption(
            "All module variants at unit scale (1 cell = 1 unit).  "
            "Red lines = geometry.  Green dots = ports.  3D modules are auto-extruded from the 2D library along z."
        )
        st.pyplot(plot_module_library_3d(default_d=D))
    elif section_type in _SECTION_ZONES:
        st.caption(
            "All module variants at unit scale (1 cell = 1 unit).  "
            "Red lines = geometry.  Green dots = ports.  Coloured fill = zone type."
        )
        _mtime = os.path.getmtime(_MODULES_PATH)
        _dmtime = os.path.getmtime(_DRAWING_PATH)
        st.image(_module_library_png(section_type, _mtime, _dmtime), use_container_width=True)
    else:
        st.info(f"**{section_type} module library** — modules will be drawn here once confirmed.")

# ── Section tab ───────────────────────────────────────────────────────────────
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
            with st.spinner("Solving…"):
                if mode == "2D":
                    result = solve(W, H, seed, corridor, corridor_w, dining_style, roof_style)
                else:
                    result = solve3d(W, H, D, seed, corridor, corridor_w, dining_style, roof_style)

            if result is None:
                st.error("No valid section found — try a different seed or combination.")
            else:
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
                        off = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
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
        if mode == "3D":
            st.info("3D mode for Kitchen is not yet available — switch to 2D.")
        else:
            with st.spinner("Solving…"):
                result = solve(W, H, seed, corridor, corridor_w, section="kitchen")
            if result is None:
                st.error("No valid section found — try a different seed or height.")
            else:
                st.pyplot(plot_section(result, W, H))
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
    elif section_type == "Living":
        if mode == "3D":
            st.info("3D mode for Living is not yet available — switch to 2D.")
        else:
            with st.spinner("Solving…"):
                result = solve(W, H, seed, corridor, corridor_w, "spacious", "any", section="living")
            if result is None:
                st.error("No valid section found — try a different seed or height.")
            else:
                st.pyplot(plot_section(result, W, H))
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

# ── Native 3D Test tab ────────────────────────────────────────────────────────
with tab_test:
    _TEST_W, _TEST_H, _TEST_D = 6, 6, 3
    st.caption(
        f"Native 3D modules ({_TEST_W}×{_TEST_H}×{_TEST_D} grid). "
        "Grey cells are auto-filled with filler_empty_3d."
    )
    # Zone rules: chairs y=0–2, table y=0–3, roof y=3–6.
    # Connector pieces bridge the 1-cell gap (y=2) on each side
    # where chairs end and the roof begins.
    _test_placed = [
        {"module_id": "chair_left_3d_v1",     "x_off": 0, "y_off": 0, "z_off": 0, "w": 2, "h": 2, "d": _TEST_D},
        {"module_id": "table_3d_v1",           "x_off": 2, "y_off": 0, "z_off": 0, "w": 2, "h": 3, "d": _TEST_D},
        {"module_id": "chair_right_3d_v1",     "x_off": 4, "y_off": 0, "z_off": 0, "w": 2, "h": 2, "d": _TEST_D},
        {"module_id": "conn_chair_roof_left",  "x_off": 0, "y_off": 2, "z_off": 0, "w": 2, "h": 1, "d": _TEST_D},
        {"module_id": "conn_chair_roof_right", "x_off": 4, "y_off": 2, "z_off": 0, "w": 2, "h": 1, "d": _TEST_D},
        {"module_id": "filler_empty_3d",     "x_off": 2, "y_off": 3, "z_off": 0, "w": 1, "h": 1, "d": _TEST_D},
        {"module_id": "filler_empty_3d",     "x_off": 3, "y_off": 3, "z_off": 0, "w": 1, "h": 1, "d": _TEST_D},
        {"module_id": "roof_3d_v1",            "x_off": 0, "y_off": 3, "z_off": 0, "w": 6, "h": 3, "d": _TEST_D},
    ]
    st.pyplot(plot_section_3d(_test_placed, W=_TEST_W, H=_TEST_H, D=_TEST_D))
