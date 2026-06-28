import rhinoscriptsyntax as rs
import json

# -- CONFIG -- set these before running ------------------------------------
ORIGIN     = (0, 0, 0)  # bottom-front-left corner of the module bounding box
CELL       = 10         # Rhino units per grid unit  (e.g. 10 if 1 unit = 10 Rhino units)
MODULE_ID  = "sofa_v4"
W          = "4"     # grid units wide
H          = "3"     # grid units tall
D          = "3"       # grid units deep -- set to None for 2D modules
CURVE_SEGS = 12         # segments used to approximate smooth curves (arcs, splines etc.)
# --------------------------------------------------------------------------

def loc(p):
    return [round((p[i] - ORIGIN[i]) / CELL, 6) for i in range(3)]

def loc2(p):
    return loc(p)[:2]

is_3d = D is not None

# Select curves (polylines OR smooth curves)
curve_ids = rs.GetObjects("Select all curves for this module", filter=rs.filter.curve)
segments = []
if curve_ids:
    for cid in curve_ids:
        try:
            verts = rs.PolylineVertices(cid)      # works for polylines
        except:
            verts = None
        if not verts:
            verts = rs.DivideCurve(cid, CURVE_SEGS)  # discretise smooth curve into points
        if not verts:
            verts = [rs.CurveStartPoint(cid), rs.CurveEndPoint(cid)]  # last resort: endpoints only
        if verts:
            segments.append([loc(p) if is_3d else loc2(p) for p in verts])

# Select port points
port_ids = rs.GetObjects("Select port points", filter=rs.filter.point)
raw_ports = []
if port_ids:
    for pid in port_ids:
        pt = rs.PointCoordinates(pid)
        if pt:
            raw_ports.append(loc(pt) if is_3d else loc2(pt))

# Auto-bucket ports by face (tolerance = 0.1 grid units)
TOL = 0.1

def bucket_2d(pts, w, h):
    b = {"top": [], "bottom": [], "left": [], "right": []}
    for p in pts:
        x, y = p[0], p[1]
        if   abs(y - h) < TOL: b["top"].append(p)
        elif abs(y)     < TOL: b["bottom"].append(p)
        elif abs(x)     < TOL: b["left"].append(p)
        elif abs(x - w) < TOL: b["right"].append(p)
        else: b.setdefault("unassigned", []).append(p)
    return b

def bucket_3d(pts, w, h, d):
    b = {"top": [], "bottom": [], "left": [], "right": [], "front": [], "back": []}
    for p in pts:
        x, y, z = p[0], p[1], p[2]
        if   abs(y - h) < TOL: b["top"].append(p)
        elif abs(y)     < TOL: b["bottom"].append(p)
        elif abs(x)     < TOL: b["left"].append(p)
        elif abs(x - w) < TOL: b["right"].append(p)
        elif abs(z)     < TOL: b["front"].append(p)
        elif abs(z - d) < TOL: b["back"].append(p)
        else: b.setdefault("unassigned", []).append(p)
    return b

try:
    w_num = float(W); h_num = float(H)
    if is_3d:
        ports = bucket_3d(raw_ports, w_num, h_num, float(D))
    else:
        ports = bucket_2d(raw_ports, w_num, h_num)
except (ValueError, TypeError):
    ports = {"unassigned": raw_ports}

out = {"module_id": MODULE_ID, "w": W, "h": H}
if is_3d:
    out["d"] = D
out["segments"] = segments
out["ports"]    = ports

print(json.dumps(out, indent=2))
