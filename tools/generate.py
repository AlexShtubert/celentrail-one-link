import os
import yaml

import cadquery as cq
from cadquery import exporters

def read_spec(path="spec/celentrail.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_angle_L(leg, t, length):
    # L-профиль из двух прямоугольных "полок"
    a = cq.Workplane("XY").rect(leg, t).extrude(length)
    b = cq.Workplane("XY").rect(t, leg).extrude(length)
    return a.union(b)

def main():
    spec = read_spec()

    os.makedirs("cad", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # --- Beam (упрощённая параметрическая компоновка для визуального контроля) ---
    L = float(spec["beam"]["length"])
    leg = float(spec["beam"]["angle"]["leg"])
    t = float(spec["beam"]["angle"]["thickness"])
    gap = float(spec["beam"]["vertex_gap"])

    top = make_angle_L(leg, t, L).translate((0, gap/2.0, 0))
    bottom = (
        make_angle_L(leg, t, L)
        .rotate((0, 0, 0), (1, 0, 0), 180)
        .translate((0, -gap/2.0, 0))
    )

    beam = top.union(bottom)

    # --- Trolley plate (для контроля компоновки) ---
    tx = float(spec["trolley"]["plate"]["x"])
    ty = float(spec["trolley"]["plate"]["y"])
    tt = float(spec["trolley"]["plate"]["thickness"])

    plate = cq.Workplane("XY").box(tx, ty, tt).translate((L * 0.1, 0, tt / 2.0))

    model = beam.union(plate)

    # --- STEP for SimScale ---
    exporters.export(model, "cad/latest.step")

    # --- Mesh for viewer ---
    tmp_stl = "models/_tmp.stl"
    exporters.export(model, tmp_stl)

    # Конверсия STL -> GLB через trimesh (если не получится — сделаем PLY)
    import trimesh
    mesh = trimesh.load(tmp_stl, force="mesh")

    ok = False
    try:
        mesh.export("models/latest.glb")
        ok = True
    except Exception as e:
        with open("models/GLB_ERROR.txt", "w", encoding="utf-8") as f:
            f.write(str(e))

    if not ok:
        # PlayCanvas отлично ест PLY — это железная страховка
        mesh.export("models/latest.ply")

    try:
        os.remove(tmp_stl)
    except OSError:
        pass

if __name__ == "__main__":
    main()
