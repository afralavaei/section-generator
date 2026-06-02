import sys; sys.path.insert(0, '.')
import time
from solver3d import solve3d

cases = [
    ("3D 1ch corr-r s0", dict(W=6, H=9, D=3, seed=0, corridor="corridor_right", corridor_w=2)),
    ("3D 1ch corr-r s1", dict(W=6, H=9, D=3, seed=1, corridor="corridor_right", corridor_w=2)),
    ("3D 1ch corr-r s2", dict(W=6, H=9, D=3, seed=2, corridor="corridor_right", corridor_w=2)),
    ("3D 1ch corr-l s0", dict(W=6, H=9, D=3, seed=0, corridor="corridor_left",  corridor_w=2)),
    ("3D 1ch corr-l s1", dict(W=6, H=9, D=3, seed=1, corridor="corridor_left",  corridor_w=2)),
    ("3D 1ch corr-l s2", dict(W=6, H=9, D=3, seed=2, corridor="corridor_left",  corridor_w=2)),
    ("3D 1ch W7 corr-r s0", dict(W=7, H=9, D=3, seed=0, corridor="corridor_right", corridor_w=2)),
    ("3D 1ch W7 corr-l s0", dict(W=7, H=9, D=3, seed=0, corridor="corridor_left",  corridor_w=2)),
    # 2-chair sanity
    ("3D 2ch corr-r s0", dict(W=8, H=9, D=3, seed=0, corridor="corridor_right", corridor_w=2)),
    ("3D 2ch corr-l s0", dict(W=8, H=9, D=3, seed=0, corridor="corridor_left",  corridor_w=2)),
    ("3D no-corr s0",    dict(W=6, H=9, D=3, seed=0, corridor="none")),
]

all_pass = True
for name, kwargs in cases:
    t = time.time()
    r = solve3d(**kwargs)
    elapsed = time.time() - t
    status = 'PASS' if r else 'FAIL'
    if not r:
        all_pass = False
    print(f"{name}: {status} in {elapsed:.3f}s ({len(r) if r else 0} modules)")

print()
print("ALL PASS" if all_pass else "SOME FAILED")
