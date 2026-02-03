# tools/build_latest.py
import os, yaml
import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(__file__))
SPEC = os.path.join(ROOT, "spec", "celentrail.yaml")
OUT  = os.path.join(ROOT, "models", "latest.glb")

def mm(x): return float(x)/1000.0

def cyl_y(r_m, h_m, center):
    m = trimesh.creation.cylinder(radius=r_m, height=h_m, sections=64)   # axis Z
    R = trimesh.transformations.rotation_matrix(np.deg2rad(90), [1,0,0]) # Z->Y
    m.apply_transform(R)
    m.apply_translation(np.array(center))
    return m

def build(spec):
    cfg = spec["trolley_alt_internal_rod"]

    L = cfg["tube"]["length"]
    W = cfg["tube"]["width"]
    H = cfg["tube"]["height"]
    t = cfg["tube"]["wall"]

    # hollow tube (visual): outer + inner (flipped normals)
    outer = trimesh.creation.box(extents=[mm(L), mm(W), mm(H)])
    inner = trimesh.creation.box(extents=[mm(L-2*t), mm(W-2*t), mm(H-2*t)])
    inner.faces = inner.faces[:, ::-1]
    tube = trimesh.util.concatenate([outer, inner])

    def hole_center(x_left, y_top):
        x = -L/2 + x_left
        z =  H/2 - y_top
        return (mm(x), 0.0, mm(z))

    holes = cfg["holes"]  # 4 шт
    centers = [hole_center(h["x"], h["y"]) for h in holes]

    od = cfg["roller"]["outer_d"]
    rw = cfg["roller"]["width"]
    hd = cfg["hole_d"]
    rod_d = cfg["rod"]["d"]
    rod_L = cfg["rod"]["L"]

    scene = trimesh.Scene()
    scene.add_geometry(tube, node_name="tube")

    # markers + rollers
    for i,c in enumerate(centers):
        scene.add_geometry(cyl_y(mm(hd/2), mm(W+6), c), node_name=f"hole_{i}")
        scene.add_geometry(cyl_y(mm(od/2), mm(rw),   c), node_name=f"roller_{i}")

    # rod along X (center Z по твоей формуле)
    upper_y = holes[0]["y"]     # 30
    rod_center_z_mm = (H/2 - upper_y) - (od/2 + rod_d/2)

    rod = trimesh.creation.cylinder(radius=mm(rod_d/2), height=mm(rod_L), sections=96) # axis Z
    Rx = trimesh.transformations.rotation_matrix(np.deg2rad(90), [0,1,0])              # Z->X
    rod.apply_transform(Rx)
    rod.apply_translation([0.0, 0.0, mm(rod_center_z_mm)])
    scene.add_geometry(rod, node_name="rod")

    return scene

def main():
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    with open(SPEC, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}

    scene = build(spec)
    glb = trimesh.exchange.gltf.export_glb(scene)
    with open(OUT, "wb") as f:
        f.write(glb)
    print("WROTE", OUT, "BYTES", os.path.getsize(OUT))

if __name__ == "__main__":
    main()
