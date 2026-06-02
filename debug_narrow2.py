import sys; sys.path.insert(0, '.')
from solver import solve, check_adjacency, check_circuit

print("=== 1-chair compact corridor_right ===")
for seed in range(10):
    r = solve(6, 9, seed, "corridor_right", 2, "compact", section="dining")
    if r:
        adj = check_adjacency(r)
        cir = check_circuit(r)
        print(f"  seed={seed}: OK adj={adj} cir={cir}")
    else:
        print(f"  seed={seed}: None")

print()
print("=== 1-chair compact corridor_left ===")
for seed in range(10):
    r = solve(6, 9, seed, "corridor_left", 2, "compact", section="dining")
    if r:
        adj = check_adjacency(r)
        cir = check_circuit(r)
        print(f"  seed={seed}: OK adj={adj} cir={cir}")
    else:
        print(f"  seed={seed}: None")

print()
print("=== 1-chair spacious corridor_right ===")
for seed in range(10):
    r = solve(7, 9, seed, "corridor_right", 2, "spacious", section="dining")
    if r:
        adj = check_adjacency(r)
        cir = check_circuit(r)
        print(f"  seed={seed}: OK adj={adj} cir={cir}")
    else:
        print(f"  seed={seed}: None")
