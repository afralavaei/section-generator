from solver3d import solve3d
for seed in [100, 101, 102, 103, 104, 105, 200, 201]:
    r = solve3d(8, 7, 3, seed, "corridor_right", 2, section="bath")
    print("bath W=8 seed=%d: %s" % (seed, "OK(%d)" % len(r) if r else "FAIL"))
