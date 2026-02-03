import yaml
import trimesh
import numpy as np
from pathlib import Path

# paths
ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "спецификация" / "celentrail.yaml"
OUT = ROOT / "models" / "latest.glb"

# load spec
with open(SPEC, "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

t = spec["trolley_alt_internal_rod"]

# ---------------- корпус (ПОЛЫЙ, с окнами) ----------------
tube = t["tube"]
L = tube["length"]
W = tube["width"]
H = tube["height"]
wall = tube["wall"]

# внешний короб
outer = trimesh.creation.box(extents=[L, W, H])

# внутренний объём (полость)
inner = trimesh.creation.box(
    extents=[L - 2*wall, W - 2*wall, H - 2*wall]
)
inner.apply_translation([0, 0, 0])

# вычесть полость
housing = outer.difference(inner)

# ---------------- ролики (ВНУТРИ, НЕ ЗАЛИТЫ) ----------------
r = t["roller"]
roller = trimesh.creation.cylinder(
    radius=r["outer_d"] / 2,
    height=r["width"],
    sections=64
)

rollers = []
clearance = 1.0  # зазор, чтобы не терлись о корпус

for h in t["holes"]:
    rr = roller.copy()
    # X: слева направо
    x = h["x"] - L / 2
    # Y: внутрь корпуса (центрируем по ширине)
    y = 0
    # Z: СВЕРХУ 18 мм (исправление)
    z = H/2 - h["y"]

    rr.apply_translation([x, y, z])
    rollers.append(rr)

# ---------------- вал ----------------
rod = t["rod"]
shaft = trimesh.creation.cylinder(
    radius=rod["d"] / 2,
    height=rod["L"],
    sections=64
)
shaft.apply_translation([0, 0, 0])

# ---------------- сборка ----------------
scene = trimesh.Scene()
scene.add_geometry(housing, node_name="housing")

for i, rr in enumerate(rollers):
    scene.add_geometry(rr, node_name=f"roller_{i}")

scene.add_geometry(shaft, node_name="shaft")

# ---------------- экспорт ----------------
OUT.parent.mkdir(parents=True, exist_ok=True)
scene.export(OUT)
print(f"Exported: {OUT}")
