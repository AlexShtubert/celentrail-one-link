# tools/build_latest.py
import os
import yaml
import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(__file__))
SPEC = os.path.join(ROOT, "spec", "celentrail.yaml")
OUT_GLB = os.path.join(ROOT, "models", "latest.glb")

def mm(x: float) -> float:
    return float(x) / 1000.0

def box(extents_m, flip=False):
    m = trimesh.creation.box(extents=extents_m)
    if flip:
        m.faces = m.faces[:, ::-1]
    return m

def cylinder_y(radius_m, height_m, center=(0, 0, 0)):
    c = trimesh.creation.cylinder(radius=radius_m, height=height_m, sections=48)
    R = trimesh.transformations.rotation_matrix(np.deg2rad(90), [1, 0, 0])  # Z->Y
    c.apply_transform(R)
    c.apply_translation(np.array(center))
    return c

def build_trolley(spec: dict) -> trimesh.Scene:
    cfg = spec.get("trolley_alt_internal_rod", {})

    tube = cfg.get("housing", {}).get("tube", {})
    L = tube.get("length", 300)
    W = tube.get("width", 30)
    H = tube.get("height", 100)
    t = tube.get("wall_thickness", 2)

    outer = box([mm(L), mm(W), mm(H)])
    inner = box([mm(L - 2*t), mm(W - 2*t), mm(H - 2*t)], flip=True)
    tube_mesh = trimesh.util.concatenate([outer, inner])
    tube_mesh.metadata["name"] = "trolley_tube"

    holes = cfg.get("roller_holes", {})
    UL = holes.get("upper_left",  {"x": 30,  "y": 30})
    UR = holes.get("upper_right", {"x": 270, "y": 30})
    LL = holes.get("lower_left",  {"x": 60,  "y": 86})
    LR = holes.get("lower_right", {"x": 240, "y": 86})

    hole_d = cfg.get("rollers", {}).get("fastening", {}).get("hole_diameter", 10)

    def hole_center(x_from_left, y_from_top):
        x = -L/2 + x_from_left
        z =  H/2 - y_from_top
        return (mm(x), 0.0, mm(z))

    hole_centers = [
        ("UL", hole_center(UL["x"], UL["y"])),
        ("UR", hole_center(UR["x"], UR["y"])),
        ("LL", hole_center(LL["x"], LL["y"])),
        ("LR", hole_center(LR["x"], LR["y"])),
    ]

    # hole markers
    hole_markers = []
    for name, c in hole_centers:
        m = cylinder_y(mm(hole_d/2), mm(W + 6), center=c)
        m.metadata["name"] = f"hole_{name}"
        hole_markers.append(m)

    # rollers (simple cylinders)
    rcfg = cfg.get("rollers", {})
    od = rcfg.get("outer_diameter", 39.5)
    rw = rcfg.get("width", 20)

    rollers = []
    for name, c in hole_centers:
        m = cylinder_y(mm(od/2), mm(rw), center=c)
        m.metadata["name"] = f"roller_{name}"
        rollers.append(m)

    # rod along X
    rod = cfg.get("rod", {})
    rod_d = rod.get("diameter", 20)
    rod_L = rod.get("length", 1000)

    rod_center_z_mm = (H/2 - UL["y"]) - (od/2 + rod_d/2)
    rod_center = (0.0, 0.0, mm(rod_center_z_mm))

    rod_mesh = trimesh.creation.cylinder(radius=mm(rod_d/2), height=mm(rod_L), sections=64)
    Rx = trimesh.transformations.rotation_matrix(np.deg2rad(90), [0, 1, 0])  # Z->X
    rod_mesh.apply_transform(Rx)
    rod_mesh.apply_translation(np.array(rod_center))
    rod_mesh.metadata["name"] = "rod_20mm"

    scene = trimesh.Scene()
    scene.add_geometry(tube_mesh, node_name="trolley_tube")
    for i, h in enumerate(hole_markers):
        scene.add_geometry(h, node_name=f"hole_{i}")
    for i, r in enumerate(rollers):
        scene.add_geometry(r, node_name=f"roller_{i}")
    scene.add_geometry(rod_mesh, node_name="rod_20mm")
    return scene

def main():
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)

    with open(SPEC, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}

    scene = build_trolley(spec)
    glb = trimesh.exchange.gltf.export_glb(scene)
    with open(OUT_GLB, "wb") as f:
        f.write(glb)

    print("Wrote:", OUT_GLB)

if __name__ == "__main__":
    main()
