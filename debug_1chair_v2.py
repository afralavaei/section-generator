import sys; sys.path.insert(0, '.')
import random
from modules import MODULES, ZONES_FULL_ROOF_CORR_RIGHT_1CHAIR, _TABLE_COMPACT
from solver import solve, check_adjacency, check_circuit, get_segments, get_ports, _gap_cells

def trace_1chair(seed, W=6, H=9, corridor_w=2, dining_style="compact"):
    rng = random.Random(seed)
    inner_W = W - corridor_w  # 4
    corridor = "corridor_right"

    # Replicate shelf selection from solver
    shelf_pool = [mid for mid, m in MODULES.items()
                  if m["zone"] == "shelf"
                  and not mid.endswith(("_corr_r", "_corr_l"))]
    rng.shuffle(shelf_pool)
    by_h = {}
    for mid in shelf_pool:
        sh = MODULES[mid]["h"]
        if H - sh >= 3:
            by_h.setdefault(sh, []).append(mid)
    shelf_h = rng.choice(list(by_h.keys()))
    shelf_mid = rng.choice(by_h[shelf_h])
    H_solve = H - shelf_h
    print(f"seed={seed}: shelf={shelf_mid} h={shelf_h} H_solve={H_solve}")

    # Corridor placement
    corr = {"module_id": "corridor_right_short", "x_off": float(W - corridor_w), "y_off": 0.0, "w": corridor_w, "h": H_solve}
    shelf_placed = {"module_id": shelf_mid, "x_off": 0.0, "y_off": float(H_solve), "w": W, "h": shelf_h}
    placed = [corr, shelf_placed]

    # Check shelf circuit on its own
    shelf_mod = MODULES[shelf_mid]
    from collections import defaultdict
    degree = defaultdict(int)
    for seg in get_segments(shelf_mod, W, shelf_h):
        pts = [(round(x, 9), round(y + H_solve, 9)) for x, y in seg]
        for k in range(len(pts)-1):
            degree[pts[k]] += 1
            degree[pts[k+1]] += 1
    bad = [(v, d) for v, d in degree.items() if d == 1]
    if bad:
        print(f"  Shelf alone has degree-1 vertices: {bad}")

    # Zone candidates
    active_zones = ZONES_FULL_ROOF_CORR_RIGHT_1CHAIR
    table_mods = _TABLE_COMPACT

    active_zones = [
        {**z, "modules": table_mods} if z.get("id") == "table" else z
        for z in active_zones
    ]

    from solver import resolve_zone_position
    reg_candidates = []
    x_offset = 0
    for zone in active_zones:
        options = []
        for xr in zone["x_rule"]:
            for yr in zone["y_rule"]:
                res = resolve_zone_position(zone, inner_W, H_solve, xr, yr)
                w, h = res["w"], res["h"]
                for mid in zone["modules"]:
                    m = MODULES[mid]
                    if (m.get("scalable") or m["w"] == w) and (m.get("h_scalable") or m["h"] == h):
                        options.append({"module_id": mid, "x_off": res["x_off"] + x_offset,
                                        "y_off": res["y_off"], "w": w, "h": h})
        rng.shuffle(options)
        reg_candidates.append(options)

    print(f"  chair_left options ({len(reg_candidates[0])}): first={reg_candidates[0][0]['module_id']} h={reg_candidates[0][0]['h']}")
    print(f"  table options ({len(reg_candidates[1])}): first={reg_candidates[1][0]['module_id']} h={reg_candidates[1][0]['h']}")

    # Try first few chair_left options and diagnose
    from solver import check_last_adjacency
    filler_ids = [mid for mid, m in MODULES.items() if m["zone"] == "filler"]

    tested = 0
    for cl_opt in reg_candidates[0][:6]:
        placed2 = placed + [cl_opt]
        if not check_last_adjacency(placed2):
            print(f"  chair_left {cl_opt['module_id']} y={cl_opt['y_off']}: ADJACENCY FAIL vs corridor/shelf")
            continue
        for tbl_opt in reg_candidates[1][:4]:
            placed3 = placed2 + [tbl_opt]
            if not check_last_adjacency(placed3):
                print(f"  chair_left {cl_opt['module_id']} + table {tbl_opt['module_id']}: ADJACENCY FAIL")
                continue
            # Check gaps
            gaps = _gap_cells(placed3, W, H)
            # Try forced filler assignment
            from collections import defaultdict as dd
            trial = list(placed3)
            ok = True
            for col, row in gaps:
                placed_filler = None
                for fid in filler_ids:
                    candidate = {"module_id": fid, "x_off": float(col), "y_off": float(row), "w": 1, "h": 1}
                    trial.append(candidate)
                    if check_last_adjacency(trial):
                        placed_filler = fid
                        break
                    trial.pop()
                if placed_filler is None:
                    print(f"  chair_left {cl_opt['module_id']} + table {tbl_opt['module_id']}: no valid filler at ({col},{row})")
                    ok = False
                    break
            if ok:
                circ = check_circuit(trial)
                if not circ:
                    # Find bad vertices
                    degree2 = defaultdict(int)
                    for p in trial:
                        m = MODULES[p["module_id"]]
                        xo, yo = p["x_off"], p["y_off"]
                        for seg in get_segments(m, p["w"], p["h"]):
                            pts2 = [(round(x+xo,9), round(y+yo,9)) for x, y in seg]
                            for k in range(len(pts2)-1):
                                degree2[pts2[k]] += 1
                                degree2[pts2[k+1]] += 1
                    bad2 = [(v, d) for v, d in degree2.items() if d == 1]
                    print(f"  FAIL circuit: chair_left={cl_opt['module_id']} table={tbl_opt['module_id']} bad={bad2[:3]}")
                else:
                    print(f"  PASS: chair_left={cl_opt['module_id']} table={tbl_opt['module_id']}")
                    return
            del trial[len(placed3):]
            tested += 1
            if tested >= 8:
                break
        if tested >= 8:
            break
    print()

for seed in [0, 2]:
    trace_1chair(seed, W=6, H=9, corridor_w=2)
    print()
