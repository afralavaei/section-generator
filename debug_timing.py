import sys; sys.path.insert(0, '.')
import time
from solver import solve, check_adjacency, check_circuit

# Time the failing cases
cases = [
    ("1ch compact corr-r s0", dict(W=6, H=9, seed=0, corridor="corridor_right",  corridor_w=2, dining_style="compact")),
    ("1ch compact corr-r s2", dict(W=6, H=9, seed=2, corridor="corridor_right",  corridor_w=2, dining_style="compact")),
    ("1ch compact corr-l s0", dict(W=6, H=9, seed=0, corridor="corridor_left",   corridor_w=2, dining_style="compact")),
    ("1ch spacious corr-r s0",dict(W=7, H=9, seed=0, corridor="corridor_right",  corridor_w=2, dining_style="spacious")),
]

for name, kwargs in cases:
    t = time.time()
    r = solve(**kwargs, section="dining")
    elapsed = time.time() - t
    print(f"{name}: {'PASS' if r else 'FAIL'} in {elapsed:.3f}s")
