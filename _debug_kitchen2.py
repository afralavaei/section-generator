from solver3d import solve3d, check_circuit_3d, check_adjacency_3d
from modules3d import MODULES_3D

# Test kitchen at the individual-section W (4+2=6) vs dwelling W (9)
for W in [6, 9]:
    for seed in range(40, 55):
        r = solve3d(W, 7, 3, seed, "corridor_right", 2, section="kitchen")
        print("kitchen W=%d seed=%d: %s" % (W, seed, "OK(%d)" % len(r) if r else "FAIL"))

print()
# Test bath
for W in [8, 9]:
    for seed in range(40, 55):
        r = solve3d(W, 7, 3, seed, "corridor_right", 2, section="bath")
        print("bath W=%d seed=%d: %s" % (W, seed, "OK(%d)" % len(r) if r else "FAIL"))
