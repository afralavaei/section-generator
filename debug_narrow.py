import sys; sys.path.insert(0, '.')
from modules import MODULES, ZONES_FULL_ROOF_CORR_RIGHT_NARROW, _TABLE_COMPACT
from solver import (resolve_zone_position, _make_full_roof_shelf, get_segments,
                    get_ports, check_adjacency, check_last_adjacency, check_circuit,
                    _gap_cells, _SHELF_CATEGORY)
import random

W, H, corridor_w = 6, 7, 2
inner_W = W - corridor_w  # 4
x_offset = 0
rng = random.Random(0)

# Build shelf
shelf_pool = [mid for mid, m in MODULES.items()
              if m['zone'] == 'shelf'
              and not mid.endswith(('_corr_r', '_corr_l'))
              and 'narrow' not in mid]
by_h = {}
for mid in shelf_pool:
    sh = MODULES[mid]['h']
    if H - sh >= 3:
        by_h.setdefault(sh, []).append(mid)

shelf_h = 1
shelf_mid_raw = by_h[1][0]
shelf_mid = _make_full_roof_shelf(shelf_mid_raw, W, float(inner_W) - 0.5)
H_solve = H - shelf_h  # 6

placed = [
    {'module_id': 'corridor_right_short', 'x_off': float(inner_W), 'y_off': 0.0, 'w': corridor_w, 'h': H_solve},
    {'module_id': shelf_mid, 'x_off': 0.0, 'y_off': float(H_solve), 'w': W, 'h': shelf_h},
]

# Build active_zones with table_mods substitution
active_zones = [
    {**z, 'modules': _TABLE_COMPACT} if z.get('id') == 'table' else z
    for z in ZONES_FULL_ROOF_CORR_RIGHT_NARROW
]

print(f"active zones after table_mods substitution:")
for z in active_zones:
    print(f"  {z['id']} x_rule={z['x_rule']} modules={z['modules'][:3]}...")

print(f"\nH_solve={H_solve}")

# Build reg_candidates
reg_candidates = []
for zone in active_zones:
    options = []
    for xr in zone['x_rule']:
        for yr in zone['y_rule']:
            res = resolve_zone_position(zone, inner_W, H_solve, xr, yr)
            w, h = res['w'], res['h']
            for mid in zone['modules']:
                m = MODULES[mid]
                if (m.get('scalable') or m['w'] == w) and (m.get('h_scalable') or m['h'] == h):
                    options.append({
                        'module_id': mid,
                        'x_off': res['x_off'] + x_offset,
                        'y_off': res['y_off'],
                        'w': w, 'h': h,
                    })
    print(f"\nZone {zone['id']}: {len(options)} options")
    for opt in options[:3]:
        print(f"  {opt['module_id']} x={opt['x_off']} y={opt['y_off']} w={opt['w']} h={opt['h']}")
    reg_candidates.append(options)

# Try placing first chair_left option
chair_opt = reg_candidates[0][0]
placed_test = placed + [chair_opt]
print(f"\nPlaced chair_left={chair_opt['module_id']}: adj={check_last_adjacency(placed_test)}")

# Try placing first table option too
table_opt = reg_candidates[1][0]
placed_test2 = placed_test + [table_opt]
print(f"Placed table={table_opt['module_id']}: adj={check_last_adjacency(placed_test2)}")

# Check gaps
gaps = _gap_cells(placed_test2, W, H)
print(f"\nGap cells (W={W}, H={H}): {len(gaps)} cells")
print(f"First 10: {gaps[:10]}")

# Try adding one filler
from modules import MODULES
filler_ids = [mid for mid, m in MODULES.items() if m['zone'] == 'filler']
print(f"\nFiller IDs: {filler_ids}")

# Trace circuit check directly
placed_all = placed_test2 + [{'module_id': 'filler_pass_v', 'x_off': float(c), 'y_off': float(r), 'w': 1, 'h': 1}
                              for c, r in gaps]
print(f"\nWith all gaps as filler_pass_v: adj={check_adjacency(placed_all)} cir={check_circuit(placed_all)}")
placed_all2 = placed_test2 + [{'module_id': 'filler_empty', 'x_off': float(c), 'y_off': float(r), 'w': 1, 'h': 1}
                               for c, r in gaps]
print(f"With all gaps as filler_empty: adj={check_adjacency(placed_all2)} cir={check_circuit(placed_all2)}")
