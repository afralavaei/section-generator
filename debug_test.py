import sys
sys.path.insert(0, ".")
from solver import solve, check_adjacency, check_circuit

def first_pass(W, H, corridor, cw, style, roof, label):
    for seed in range(50):
        r = solve(W, H, seed, corridor, cw, style, roof)
        if r is not None:
            ok_adj = check_adjacency(r)
            ok_cir = check_circuit(r)
            status = "PASS" if ok_adj and ok_cir else "ADJ/CIR FAIL"
            print(f"{status}  {label}  seed={seed}")
            return
    print(f"FAIL  {label}  (no seed 0-49 succeeded)")

# compact (corridor_w=2, dining_w=6)
first_pass(8,  7, "corridor_right", 2, "compact", "any",    "compact  corr_right  any")
first_pass(8,  7, "corridor_right", 2, "compact", "pitched","compact  corr_right  pitched")
first_pass(8,  7, "corridor_left",  2, "compact", "any",    "compact  corr_left   any")
first_pass(8,  7, "corridor_left",  2, "compact", "pitched","compact  corr_left   pitched")
# spacious (corridor_w=4, dining_w=8)
first_pass(12, 7, "corridor_right", 4, "spacious","any",    "spacious corr_right  any")
first_pass(12, 7, "corridor_right", 4, "spacious","pitched","spacious corr_right  pitched")
first_pass(12, 7, "corridor_left",  4, "spacious","any",    "spacious corr_left   any")
first_pass(12, 7, "corridor_left",  4, "spacious","pitched","spacious corr_left   pitched")
# no corridor
first_pass(6,  7, "none",           2, "compact", "any",    "compact  no corr")
first_pass(8,  7, "none",           2, "spacious","any",    "spacious no corr")
