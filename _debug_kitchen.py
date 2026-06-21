from solver3d import resolve_zone_position_3d, _module_fits
from modules3d import MODULES_3D, KITCHEN_ZONES_INNER_3D
import random

W, H, D = 9, 7, 3
corridor_w = 2
inner_W = W - corridor_w  # 7
rng = random.Random(45)
rng.choice([True, False])  # skip wide roll
shelf_pool = [mid for mid, m in MODULES_3D.items()
              if m.get("zone") == "shelf"
              and not mid.endswith(("_corr_r", "_corr_l"))
              and "frs3d" not in mid]
rng.shuffle(shelf_pool)
by_h_k = {}
for mid in shelf_pool:
    sh = MODULES_3D[mid]["h"]
    if H - sh >= 4:
        by_h_k.setdefault(sh, []).append(mid)
shelf_h = rng.choice(list(by_h_k.keys()))
rng.choice(by_h_k[shelf_h])
H_solve_k = H - shelf_h
print("H_solve_k:", H_solve_k, "inner_W:", inner_W)

for zone in KITCHEN_ZONES_INNER_3D:
    print("Zone:", zone["id"])
    for xr in zone["x_rule"]:
        for yr in zone["y_rule"]:
            for zr in zone.get("z_rule", ["full"]):
                res = resolve_zone_position_3d(zone, inner_W, H_solve_k, D, xr, yr, zr)
                w, h, d = res["w"], res["h"], res["d"]
                print("  rule %s %s %s -> w=%d h=%d d=%d" % (xr, yr, zr, w, h, d))
                for mid in zone["modules"]:
                    m = MODULES_3D[mid]
                    fits = _module_fits(m, w, h, d)
                    print("    %s: mw=%d mh=%d md=%d -> fits=%s" % (mid, m["w"], m["h"], m.get("d",3), fits))

# Also check what inner W=4 gives (the expected kitchen width)
print("\n--- With inner_W=4 (single-section kitchen W=6) ---")
for zone in KITCHEN_ZONES_INNER_3D:
    print("Zone:", zone["id"])
    for xr in zone["x_rule"]:
        for yr in zone["y_rule"]:
            for zr in zone.get("z_rule", ["full"]):
                res = resolve_zone_position_3d(zone, 4, H_solve_k, D, xr, yr, zr)
                w, h, d = res["w"], res["h"], res["d"]
                print("  rule %s %s %s -> w=%d h=%d d=%d" % (xr, yr, zr, w, h, d))
                for mid in zone["modules"]:
                    m = MODULES_3D[mid]
                    fits = _module_fits(m, w, h, d)
                    print("    %s: mw=%d mh=%d md=%d -> fits=%s" % (mid, m["w"], m["h"], m.get("d",3), fits))
