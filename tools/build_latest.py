import yaml
import trimesh
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "celentrail.yaml"
OUT = ROOT / "models" / "latest.glb"

with open(SPEC, "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

t = spec["trolley_alt_internal_rod"]

# === КОРПУС ===
tube = t["housing"]["tube"]
L = tube["length"]
W = tube["width"]
H = tube["height"]
wall = tube["wall"]

outer = trimesh.creation.box(extents=[L, W, H])
inner = trimesh.creation.box(extents=[L-2*wall, W-2*wall, H-2*wall])
inner.apply_translation([0, 0, 0])

body = outer.difference(inner)

# === РОЛИК ===
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
        h["x"] - L/2,
        0,
        H/2 - h["y"]
    ])
    rollers.append(rr)

scene = trimesh.Scene([body] + rollers)
scene.export(OUT)

print("OK → models/latest.glb")
