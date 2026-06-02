import sys; sys.path.insert(0, '.')
from solver import solve, check_adjacency, check_circuit

cases = [
    # 2-chair compact/spacious
    ("2ch compact no-corr",   dict(W=6,  H=9, seed=0, corridor="none",           corridor_w=2, dining_style="compact")),
    ("2ch compact corr-r",    dict(W=8,  H=9, seed=0, corridor="corridor_right",  corridor_w=2, dining_style="compact")),
    ("2ch spacious no-corr",  dict(W=8,  H=9, seed=0, corridor="none",           corridor_w=4, dining_style="spacious")),
    ("2ch spacious corr-r",   dict(W=12, H=9, seed=0, corridor="corridor_right",  corridor_w=4, dining_style="spacious")),
    # 1-chair compact/spacious
    ("1ch compact corr-r s0", dict(W=6,  H=9, seed=0, corridor="corridor_right",  corridor_w=2, dining_style="compact")),
    ("1ch compact corr-r s1", dict(W=6,  H=9, seed=1, corridor="corridor_right",  corridor_w=2, dining_style="compact")),
    ("1ch compact corr-r s2", dict(W=6,  H=9, seed=2, corridor="corridor_right",  corridor_w=2, dining_style="compact")),
    ("1ch compact corr-l s0", dict(W=6,  H=9, seed=0, corridor="corridor_left",   corridor_w=2, dining_style="compact")),
    ("1ch compact corr-l s1", dict(W=6,  H=9, seed=1, corridor="corridor_left",   corridor_w=2, dining_style="compact")),
    ("1ch spacious corr-r s0",dict(W=7,  H=9, seed=0, corridor="corridor_right",  corridor_w=2, dining_style="spacious")),
    ("1ch spacious corr-r s5",dict(W=7,  H=9, seed=5, corridor="corridor_right",  corridor_w=2, dining_style="spacious")),
    # roof styles
    ("plain corr-r",    dict(W=8, H=9, seed=0, corridor="corridor_right", corridor_w=2, dining_style="compact", roof_style="plain")),
    ("pitched no-corr", dict(W=6, H=9, seed=0, corridor="none",           corridor_w=2, dining_style="compact", roof_style="pitched")),
]

all_pass = True
for name, kwargs in cases:
    r = solve(**kwargs, section="dining")
    if r is None:
        print(f"FAIL {name}: None")
        all_pass = False
    else:
        adj = check_adjacency(r)
        cir = check_circuit(r)
        ok = adj and cir
        if not ok:
            print(f"FAIL {name}: adj={adj} cir={cir}")
            all_pass = False
        else:
            print(f"pass {name}")

print()
print("ALL PASS" if all_pass else "SOME FAILED")
