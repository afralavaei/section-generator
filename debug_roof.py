import sys; sys.path.insert(0, '.')
from solver import solve
from modules import _SHELF_CATEGORY, MODULES

print("=== Kitchen no-corridor pitched ===")
for seed in range(5):
    r = solve(7, 9, seed, corridor='none', roof_style='pitched', section='kitchen')
    if r:
        shelf = next((p for p in r if MODULES[p['module_id']]['zone'] == 'shelf'), None)
        if shelf:
            mid = shelf['module_id']
            cat = _SHELF_CATEGORY.get(mid, '?')
            print(f"  seed={seed}: {mid} cat={cat}")
        else:
            print(f"  seed={seed}: no shelf in result")
    else:
        print(f"  seed={seed}: None")

print("\n=== Kitchen no-corridor plain ===")
for seed in range(5):
    r = solve(7, 9, seed, corridor='none', roof_style='plain', section='kitchen')
    if r:
        shelf = next((p for p in r if MODULES[p['module_id']]['zone'] == 'shelf'), None)
        if shelf:
            mid = shelf['module_id']
            cat = _SHELF_CATEGORY.get(mid, '?')
            print(f"  seed={seed}: {mid} cat={cat}")
        else:
            print(f"  seed={seed}: no shelf")
    else:
        print(f"  seed={seed}: None")

print("\n=== Living no-corridor pitched ===")
for seed in range(5):
    r = solve(8, 9, seed, corridor='none', roof_style='pitched', section='living')
    if r:
        shelf = next((p for p in r if MODULES[p['module_id']]['zone'] == 'shelf'), None)
        if shelf:
            mid = shelf['module_id']
            base = mid.replace('_corr_r', '').replace('_corr_l', '')
            cat = _SHELF_CATEGORY.get(base, '?')
            print(f"  seed={seed}: {mid} cat={cat}")
        else:
            print(f"  seed={seed}: no shelf")
    else:
        print(f"  seed={seed}: None")
