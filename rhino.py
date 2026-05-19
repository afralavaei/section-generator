import rhinoscriptsyntax as rs
import json

# 1. Set the module-local origin and cell size before running.
ORIGIN = (0, 0, 0)   # bottom-front-left corner of the bounding box, in Rhino coords
CELL   = 10                    # Rhino units per unit-cell

def localise(p):
    return [round((p[i] - ORIGIN[i]) / CELL, 6) for i in range(3)]

# 2. Select all polylines for this module (curves), then run.
polyline_ids = rs.GetObjects("Select all polylines for this module", filter=rs.filter.curve)
segments = []
for cid in polyline_ids:
    pts = rs.PolylineVertices(cid) or [rs.CurveStartPoint(cid), rs.CurveEndPoint(cid)]
    segments.append([localise(p) for p in pts])

# 3. Select port points (the green dots), then run.
port_ids = rs.GetObjects("Select port points", filter=rs.filter.point)
ports_flat = [localise(rs.PointCoordinates(pid)) for pid in port_ids]

out = {
    "module_id": "TODO_fill_in",
    "w": "TODO", "h": "TODO", "d": "TODO",
    "segments": segments,
    "ports_unassigned": ports_flat,   # I'll bucket these by face from the coords
}
print(json.dumps(out, indent=2))