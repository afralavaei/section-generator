"""
export.py — Export solver results to Rhino Python scripts.

Coordinate mapping (module → Rhino, Z-up):
  Rhino X = module x (w direction)  × CELL
  Rhino Y = module z (d direction)  × CELL
  Rhino Z = module y (h direction)  × CELL
"""

from modules3d import MODULES_3D, get_segments_3d

CELL = 10  # Rhino units per grid unit


def _r(x: float, y: float, z: float) -> tuple:
    """Convert module (w, h, d) coords to Rhino (X, Y, Z) with Z-up."""
    return (x * CELL, z * CELL, y * CELL)


def export_section_3d_rhino(placed: list, W: int, H: int, D: int,
                             section_type: str = "section") -> str:
    """
    Generate a Rhino Python script (.py) that recreates a 3D solver result
    as polyline curves, one Rhino layer per zone type.

    Run inside Rhino via Tools → PythonScript → Run.
    """
    header = [
        "import rhinoscriptsyntax as rs",
        "",
        f"# Nomadic Engine — 3D {section_type.title()}  W={W} H={H} D={D}",
        "rs.EnableRedraw(False)",
        "",
    ]

    # Collect segments grouped by zone
    by_zone: dict[str, list] = {}
    for p in placed:
        mid = p["module_id"]
        if mid not in MODULES_3D:
            continue
        mod  = MODULES_3D[mid]
        zone = mod.get("zone", "misc")
        xo, yo, zo = p["x_off"], p["y_off"], p["z_off"]
        pw, ph, pd  = p["w"],     p["h"],     p["d"]

        for seg in get_segments_3d(mod, pw, ph, pd):
            pts = [_r(pt[0] + xo, pt[1] + yo, pt[2] + zo) for pt in seg]
            if len(pts) >= 2:
                by_zone.setdefault(zone, []).append(pts)

    body = []
    for zone, segs in by_zone.items():
        body.append(f"# ── {zone} {'─' * max(0, 50 - len(zone))}")
        body.append(f"if not rs.IsLayer('{zone}'):")
        body.append(f"    rs.AddLayer('{zone}')")
        body.append(f"rs.CurrentLayer('{zone}')")
        for pts in segs:
            pts_str = ", ".join(f"({x:.3f},{y:.3f},{z:.3f})" for x, y, z in pts)
            if len(pts) == 2:
                a, b = pts
                body.append(
                    f"rs.AddLine(({a[0]:.3f},{a[1]:.3f},{a[2]:.3f}),"
                    f"({b[0]:.3f},{b[1]:.3f},{b[2]:.3f}))"
                )
            else:
                body.append(f"rs.AddPolyline([{pts_str}])")
        body.append("")

    footer = [
        "rs.EnableRedraw(True)",
        "rs.ZoomExtents()",
        f'print("Nomadic Engine — {section_type.title()} imported.")',
    ]

    return "\n".join(header + body + footer)


def export_section_3d_json(placed: list, W: int, H: int, D: int,
                            section_type: str = "section") -> dict:
    """
    Return a JSON-serialisable dict of all 3D segments, ready for Three.js.

    Each segment entry:
        { "zone": str, "points": [[x,y,z], ...] }

    Coordinates are in grid units (not scaled to Rhino CELL).
    Three.js side: multiply by CELL (e.g. 10) to get world units.
    """
    segments: list[dict] = []

    for p in placed:
        mid = p["module_id"]
        if mid not in MODULES_3D:
            continue
        mod  = MODULES_3D[mid]
        zone = mod.get("zone", "misc")
        xo, yo, zo = p["x_off"], p["y_off"], p["z_off"]
        pw, ph, pd  = p["w"],     p["h"],     p["d"]

        for seg in get_segments_3d(mod, pw, ph, pd):
            pts = [[pt[0] + xo, pt[1] + yo, pt[2] + zo] for pt in seg]
            if len(pts) >= 2:
                segments.append({"zone": zone, "points": pts})

    return {
        "section_type": section_type,
        "W": W, "H": H, "D": D,
        "segments": segments,
    }
