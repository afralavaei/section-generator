import signal, sys
from solver3d import solve3d

def timeout(sig, frame):
    print("TIMEOUT")
    sys.exit(0)

signal.signal(signal.SIGALRM, timeout) if hasattr(signal, 'SIGALRM') else None

for W, sec in [(6, "kitchen"), (8, "bath"), (8, "kitchen")]:
    for seed in [42, 43, 44, 45]:
        try:
            r = solve3d(W, 7, 3, seed, "corridor_right", 2, section=sec)
            print(f"{sec} W={W} seed={seed}: {'OK(%d)' % len(r) if r else 'FAIL'}")
        except Exception as e:
            print(f"{sec} W={W} seed={seed}: ERROR {e}")
