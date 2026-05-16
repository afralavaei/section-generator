import streamlit as st

from solver import solve, check_adjacency, check_circuit
from drawing import plot_section, plot_module_library

st.set_page_config(page_title="Nomadic Engine", layout="wide")
st.title("Nomadic Engine")

# ── Sidebar: all controls ─────────────────────────────────────────────────────
with st.sidebar:
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

    W = dining_w + (corridor_w if corridor != "none" else 0)
    st.caption(
        f"Section: **{W} × {H}**  "
        f"({dining_w} dining"
        + (f" + {corridor_w} corridor" if corridor != "none" else "")
        + ")"
    )

    st.divider()

    show_figures = st.checkbox(
        "Show human figures",
        value=False,
        help="Overlays seated / standing silhouettes.  "
             "Requires silhouette PNG files in the app folder.",
    )

# ── Main area ─────────────────────────────────────────────────────────────────
tab_sec, tab_lib = st.tabs(["Section", "Module Library"])

with tab_lib:
    st.caption(
        "All module variants at unit scale (1 cell = 1 unit).  "
        "Red lines = geometry.  Green dots = ports.  Coloured fill = zone type."
    )
    st.pyplot(plot_module_library())

with tab_sec:
    if num_chairs == 1 and corridor == "none":
        st.warning("1-chair mode requires a corridor — select Corridor Left or Corridor Right in the sidebar.")
    else:
        if roof_style == "pitched" and corridor != "none" and corridor_w == 2:
            st.info(
                "Pitched mode + corridor: the solver randomly combines slanted shelf, "
                "lean-to corridor, or both — change Seed to explore variations."
            )

        with st.spinner("Solving…"):
            result = solve(W, H, seed, corridor, corridor_w, dining_style, roof_style)

        if result is None:
            st.error("No valid section found — try a different seed or combination.")
        else:
            st.pyplot(plot_section(result, W, H, show_figures=show_figures, roof_style=roof_style))

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
