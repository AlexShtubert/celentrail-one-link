  import yaml
import trimesh
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "спецификация" / "celentrail.yaml"
OUT = ROOT / "models" / "latest.glb"

with open(SPEC, "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

t = spec["trolley_alt_internal_rod"]

# ----- корпус -----
tube = t["tube"]
box = trimesh.creation.box(
    extents=[
        tube["length"],
        tube["width"],
        tube["height"]
    ]
)

# ----- ролик -----
r = t["roller"]
roller = trimesh.creation.cylinder(
    radius=r["outer_d"] / 2,
    height=r["width"],
    sections=64
)

rollers = []
for h in t["holes"]:
    rr = roller.copy()
    rr.apply_translation([
        h["x"] - tube["length"] / 2,
        0,
        tube["height"] / 2 - h["y"]
    ])
    rollers.append(rr)

# ----- вал -----
rod = t["rod"]
shaft = trimesh.creation.cylinder(
    radius=rod["d"] / 2,
    height=rod["L"],
    sections=64
)
shaft.apply_translation([0, 0, 0])

scene = trimesh.Scene()
scene.add_geometry(box)
scene.add_geometry(shaft)
for r in rollers:
    scene.add_geometry(r)

OUT.parent.mkdir(parents=True, exist_ok=True)
scene.export(OUT)

print("OK: models/latest.glb rebuilt")
  
