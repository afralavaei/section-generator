import streamlit as st

from solver import solve, check_adjacency, check_circuit
from drawing import plot_section, plot_module_library
from solver3d import solve3d, check_adjacency_3d, check_circuit_3d
from viewer3d import plot_section_3d, plot_module_library_3d, plot_slice_2d

st.set_page_config(page_title="Nomadic Engine", layout="wide")
st.title("Nomadic Engine")

# ── Sidebar: all controls ─────────────────────────────────────────────────────
with st.sidebar:
    mode = st.radio(
        "Mode",
        options=["2D", "3D"],
        horizontal=True,
        help="2D = the original section drawing.  3D = volumetric assembly with a depth axis.",
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

    if corridor != "none":
        corr_w_choice = st.radio(
            "Corridor Width",
            options=["Compact  (2 cols)", "Spacious  (4 cols)"],
            horizontal=True,
        )
        corridor_w = 2 if "Compact" in corr_w_choice else 4
    else:
        corridor_w = 2

    chairs_choice = st.radio(
        "Seating",
        options=["2 Chairs", "1 Chair"],
        horizontal=True,
        help="2 Chairs = both sides occupied.  "
             "1 Chair = single-sided, requires a corridor.",
    )
    num_chairs = 2 if chairs_choice == "2 Chairs" else 1

    dining_choice = st.radio(
        "Table Style",
        options=["Compact", "Spacious"],
        horizontal=True,
        help="Compact = narrow tables.  Spacious = wide-top tables with 1-col gap.",
    )
    dining_style = "compact" if dining_choice == "Compact" else "spacious"
    if num_chairs == 2:
        dining_w = 6 if dining_style == "compact" else 8
    else:
        dining_w = 4 if dining_style == "compact" else 5

    roof_choice = st.radio(
        "Roof Style",
        options=["Any", "Plain", "Divided", "Pitched"],
        horizontal=True,
        help="Plain = flat top bar.  Divided = internal shelves/dividers.  "
             "Pitched = lean-to or gable ridge.",
    )
    roof_style = roof_choice.lower()

    st.divider()

    seed = int(st.slider("Seed", min_value=0, max_value=1_000_000, value=42, step=1))
    H = int(st.number_input(
        "Height H", min_value=7, max_value=20, value=7, step=1,
        help="Extra rows above zones are auto-filled with filler tiles.",
    ))

    if mode == "3D":
        D = int(st.number_input(
            "Depth D", min_value=1, max_value=10, value=2, step=1,
            help="Number of depth cells. Every module is auto-extruded along z.",
        ))
    else:
        D = 1  # placeholder, unused in 2D mode

    W = dining_w + (corridor_w if corridor != "none" else 0)
    st.caption(
        f"Section: **{W} × {H}**" + (f" × {D}" if mode == "3D" else "") + "  "
        f"({dining_w} dining"
        + (f" + {corridor_w} corridor" if corridor != "none" else "")
        + ")"
    )

    st.divider()

    show_figures = st.checkbox(
        "Show human figures",
        value=False,
        help="Overlays seated / standing silhouettes.  "
             "Requires silhouette PNG files in the app folder.  (2D mode only.)",
    )

# ── Main area ─────────────────────────────────────────────────────────────────
tab_sec, tab_lib = st.tabs(["Section", "Module Library"])

with tab_lib:
    st.caption(
        "All module variants at unit scale (1 cell = 1 unit).  "
        "Red lines = geometry.  Green dots = ports."
        + ("  Coloured fill = zone type." if mode == "2D" else
           "  3D modules are auto-extruded from the 2D library along z.")
    )
    if mode == "2D":
        st.pyplot(plot_module_library())
    else:
        st.pyplot(plot_module_library_3d(default_d=D))

with tab_sec:
    if num_chairs == 1 and corridor == "none":
        st.warning("1-chair mode requires a corridor — select Corridor Left or Corridor Right in the sidebar.")
    else:
        if roof_style == "pitched" and corridor != "none":
            st.info(
                "Gable (h=4) pitched variants are not available with a corridor — "
                "lean-to variants will be used instead."
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
                st.pyplot(plot_section(result, W, H, show_figures=show_figures, roof_style=roof_style))
            else:
                st.pyplot(plot_section_3d(result, W, H, D))

                with st.expander("2D slice at depth z", expanded=False):
                    z_slice = st.slider(
                        "z position (slice through depth)",
                        min_value=0.5, max_value=float(D) - 0.5, value=0.5, step=1.0,
                        help="Pick a depth cell midpoint. The slice is rendered with the 2D pipeline.",
                    )
                    st.pyplot(plot_slice_2d(result, W, H, D, z=z_slice,
                                            show_figures=show_figures, roof_style=roof_style))

            with st.expander("Placement details"):
                for p in result:
                    off_str = (f"({p['x_off']:.0f}, {p['y_off']:.0f})" if mode == "2D"
                               else f"({p['x_off']:.0f}, {p['y_off']:.0f}, {p['z_off']:.0f})")
                    size_str = (f"{p['w']}w × {p['h']}h" if mode == "2D"
                                else f"{p['w']}w × {p['h']}h × {p['d']}d")
                    st.write(f"**{p['module_id']}** — offset {off_str}  size {size_str}")

            with st.expander("Circuit validation"):
                if mode == "2D":
                    ok_adj = check_adjacency(result)
                    ok_cir = check_circuit(result)
                else:
                    ok_adj = check_adjacency_3d(result)
                    ok_cir = check_circuit_3d(result)
                st.write(f"Adjacency check: {'✓ pass' if ok_adj else '✗ fail'}")
                st.write(f"Closed circuit:  {'✓ pass' if ok_cir else '✗ fail'}")
