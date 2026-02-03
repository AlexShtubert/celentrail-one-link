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


def cylinder_y(radius_m, height_m, center=(0, 0, 0), sections=64):
    # create cylinder along Z then rotate Z->Y
    c = trimesh.creation.cylinder(radius=radius_m, height=height_m, sections=sections)
    R = trimesh.transformations.rotation_matrix(np.deg2rad(90), [1, 0, 0])  # Z->Y
    c.apply_transform(R)
    c.apply_translation(np.array(center))
    return c


def cylinder_x(radius_m, height_m, center=(0, 0, 0), sections=96):
    # create cylinder along Z then rotate Z->X
    c = trimesh.creation.cylinder(radius=radius_m, height=height_m, sections=sections)
    R = trimesh.transformations.rotation_matrix(np.deg2rad(90), [0, 1, 0])  # Z->X
    c.apply_transform(R)
    c.apply_translation(np.array(center))
    return c


def build_scene(spec: dict) -> trimesh.Scene:
    cfg = spec.get("trolley_alt_internal_rod", {})
    housing = cfg.get("housing", {})
    tube = housing.get("tube", {})

    L = tube.get("length", 300)          # mm
    W = tube.get("width", 30)            # mm
    H = tube.get("height", 100)          # mm
    t = tube.get("wall_thickness", 2)    # mm

    # visual hollow tube (outer + inner flipped)
    outer = box([mm(L), mm(W), mm(H)])
    inner = box([mm(L - 2*t), mm(W - 2*t), mm(H - 2*t)], flip=True)
    tube_mesh = trimesh.util.concatenate([outer, inner])
    tube_mesh.metadata["name"] = "trolley_tube"

    rollers = cfg.get("rollers", {})
    od = rollers.get("outer_diameter", 39.5)  # mm
    rw = rollers.get("width", 20)             # mm
    hole_d = rollers.get("fastening", {}).get("hole_diameter", 10)  # mm

    holes_cfg = cfg.get("roller_holes", {})
    UL = holes_cfg.get("upper_left",  {"x": 30,  "y": 30})
    UR = holes_cfg.get("upper_right", {"x": 270, "y": 30})
    LL = holes_cfg.get("lower_left",  {"x": 60,  "y": 86})
    LR = holes_cfg.get("lower_right", {"x": 240, "y": 86})

    def hole_center(x_from_left_mm, y_from_top_mm):
        # origin at tube center:
        x = -L/2 + x_from_left_mm
        z =  H/2 - y_from_top_mm
        return (mm(x), 0.0, mm(z))

    centers = [
        ("UL", hole_center(UL["x"], UL["y"])),
        ("UR", hole_center(UR["x"], UR["y"])),
        ("LL", hole_center(LL["x"], LL["y"])),
        ("LR", hole_center(LR["x"], LR["y"])),
    ]

    rod = cfg.get("rod", {})
    rod_d = rod.get("diameter", 20)   # mm
    rod_L = rod.get("length", 1000)   # mm

    # rod Z-center by your rule:
    # rod_center_z_mm = (H/2 - upper_y) - (od/2 + rod_d/2)
    upper_y = UL["y"]
    rod_center_z_mm = (H/2 - upper_y) - (od/2 + rod_d/2)
    rod_center = (0.0, 0.0, mm(rod_center_z_mm))

    scene = trimesh.Scene()
    scene.add_geometry(tube_mesh, node_name="tube")

    # add holes (markers) + rollers (visual)
    for name, c in centers:
        scene.add_geometry(
            cylinder_y(mm(hole_d/2), mm(W + 6), center=c, sections=48),
            node_name=f"hole_{name}",
        )
        scene.add_geometry(
            cylinder_y(mm(od/2), mm(rw), center=c, sections=64),
            node_name=f"roller_{name}",
        )

    # add rod (visual)
    scene.add_geometry(
        cylinder_x(mm(rod_d/2), mm(rod_L), center=rod_center, sections=96),
        node_name="rod_20",
    )

    return scene


def main():
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)

    with open(SPEC, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}

    scene = build_scene(spec)
    glb = trimesh.exchange.gltf.export_glb(scene)

    with open(OUT_GLB, "wb") as f:
        f.write(glb)

    print("WROTE", OUT_GLB, "BYTES", os.path.getsize(OUT_GLB))


if __name__ == "__main__":
    main()
