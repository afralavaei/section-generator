import sys; sys.path.insert(0, '.')
from modules import MODULES
from solver import solve, check_adjacency, check_circuit, _make_full_roof_shelf
import random

# Trace what happens for compact 1-chair corridor_right seeds 0 and 1
for seed in [0, 1, 2]:
    rng = random.Random(seed)
    W, H, corridor_w = 6, 9, 2
    inner_W = W - corridor_w  # 4

    # Replicate shelf selection
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

    # Check corridor ports
    corr = MODULES["corridor_right_short"]
    from solver import get_ports
    corr_ports = get_ports(corr, corridor_w, H_solve)
    print(f"  corridor_right_short (w={corridor_w}, H={H_solve}) left ports: {corr_ports['left']}")

    # Check a compact table's right ports
    from modules import _TABLE_COMPACT
    table_mid = _TABLE_COMPACT[0]
    tmod = MODULES[table_mid]
    print(f"  table {table_mid} (w=2,h={tmod['h']}) right ports: {tmod.get('ports', {}).get('right', [])}")
    print()
