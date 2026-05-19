# Nomadic Engine

Streamlit app generating architectural section drawings via backtracking constraint solver.

## Files
- `modules.py` — all module geometry, ports, zone definitions
- `solver.py` — two-phase backtracking solver (named zones → filler gap-fill)
- `drawing.py` — matplotlib rendering
- `app.py` — Streamlit UI (Dining / Kitchen / Living / Bed tabs)

## Core conventions
- Origin bottom-left, x→right, y→up, 1 unit = 1 grid cell
- Segment endpoints sit **0.5 units inside** module boundary; ports sit **on** the edge
- Valid assembly: every interior vertex degree ≥ 2 (T-junctions ok); degree-1 only at boundary ports
- Ports on shared boundary between two modules must match exactly

## Current state
- Dining: fully working (chairs + table + shelf + fillers, corridor variants, pitched roof)
- Kitchen: modules defined (`kitchen_lower_w3_h4_v2`, `kitchen_upper_w2`), zones in progress
- Living / Bed: grid placeholders only

## Workflow
- Module library uses `@st.cache_resource` — restart Streamlit after changing modules.py
- One solver handles all sections via `KITCHEN_ZONES` / `ZONES` passed to `solve()`

## Restarting Streamlit
When the user says "restart streamlit", do this silently in order — no prompts, no explanations:

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
