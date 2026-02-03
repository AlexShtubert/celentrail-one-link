import yaml
import trimesh
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "celentrail.yaml"
OUT = ROOT / "models" / "latest.glb"
OUT.parent.mkdir(parents=True, exist_ok=True)

def _get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _tube_block(t):
    # support both:
    # trolley_alt_internal_rod: { tube: {...} }
    # trolley_alt_internal_rod: { housing: { tube: {...} } }
    tube = t.get("tube") or _get(t, "housing", "tube", default={}) or {}
    L = float(tube.get("length", 300))
    W = float(tube.get("width", 30))
    H = float(tube.get("height", 100))
    wall = tube.get("wall", tube.get("wall_thickness"))
if wall is None:
    raise ValueError("В spec/celentrail.yaml отсутствует wall или wall_thickness")

    if wall is None:
        wall = tube.get("wall_thickness", tube.get("wallThickness", 2))
    wall = float(wall)

    # build tube as 4 wall-boxes (not a solid brick) so rollers are NOT "залиты"
    walls = []

    # bottom
    b = trimesh.creation.box(extents=[L, W, wall])
    b.apply_translation([0, 0, -H/2 + wall/2])
    walls.append(b)

    # top
    tbox = trimesh.creation.box(extents=[L, W, wall])
    tbox.apply_translation([0, 0, H/2 - wall/2])
    walls.append(tbox)

    # left
    l = trimesh.creation.box(extents=[L, wall, max(0.001, H - 2*wall)])
    l.apply_translation([0, -W/2 + wall/2, 0])
    walls.append(l)

    # right
    r = trimesh.creation.box(extents=[L, wall, max(0.001, H - 2*wall)])
    r.apply_translation([0, W/2 - wall/2, 0])
    walls.append(r)

    tube_mesh = trimesh.util.concatenate(walls)
    return tube_mesh, (L, W, H, wall)

def _roller_mesh(outer_d, width):
    roller = trimesh.creation.cylinder(radius=float(outer_d)/2.0, height=float(width), sections=64)
    # default axis is Z; rotate to Y
    roller.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(90), [1, 0, 0]))
    return roller

def _rod_mesh(d, L):
    rod = trimesh.creation.cylinder(radius=float(d)/2.0, height=float(L), sections=64)
    # axis Z -> X
    rod.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(90), [0, 1, 0]))
    return rod

def main():
    with open(SPEC, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}

    t = spec.get("trolley_alt_internal_rod")
    if not isinstance(t, dict):
        raise KeyError("Missing 'trolley_alt_internal_rod' in spec/celentrail.yaml")

    tube_mesh, (L, W, H, wall) = _tube_block(t)

    # rollers block: support roller or rollers
    rblock = t.get("roller") or t.get("rollers") or {}
    outer_d = float(rblock.get("outer_diameter", rblock.get("outer_d", 39.5)))
    rW = float(rblock.get("width", 20))

    holes = t.get("holes")
    if holes is None:
        # support old structure roller_holes.{upper_left...}
        rh = t.get("roller_holes", {})
        holes = []
        for k in ["upper_left", "upper_right", "lower_left", "lower_right"]:
            if k in rh and isinstance(rh[k], dict):
                holes.append({"x": rh[k].get("x"), "y": rh[k].get("y")})
    if not holes:
        raise KeyError("Missing roller holes: put 'holes:' list into trolley_alt_internal_rod")

    roller_template = _roller_mesh(outer_d, rW)
    rollers = []
    for hpos in holes:
        x = float(hpos["x"])
        y_from_top = float(hpos["y"])
        # coords: X left->right, Z bottom->top (so y_from_top converts)
        xw = x - L/2
        zw = H/2 - y_from_top
        rw = roller_template.copy()
        rw.apply_translation([xw, 0, zw])
        rollers.append(rw)

    # rod (optional)
    rod_block = t.get("rod", {})
    rod_d = float(rod_block.get("diameter", rod_block.get("d", 20)))
    rod_L = float(rod_block.get("length", rod_block.get("L", L + 200)))
    rod = _rod_mesh(rod_d, rod_L)

    scene = trimesh.Scene()
    scene.add_geometry(tube_mesh, node_name="tube")
    for i, rr in enumerate(rollers):
        scene.add_geometry(rr, node_name=f"roller_{i+1}")
    scene.add_geometry(rod, node_name="rod")

    scene.export(str(OUT))
    print(f"OK: wrote {OUT}")

if __name__ == "__main__":
    main()
