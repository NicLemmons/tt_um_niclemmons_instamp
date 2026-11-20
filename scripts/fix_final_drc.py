import os
from pathlib import Path
import pya

src = os.environ.get("GDS_INPUT")
dst = os.environ.get("GDS_OUTPUT")

if not src or not dst:
    raise RuntimeError("Set GDS_INPUT and GDS_OUTPUT")

if Path(src).resolve() == Path(dst).resolve():
    raise RuntimeError("Input and output must differ")

layout = pya.Layout()
layout.read(src)
dbu = layout.dbu

opamp = layout.cell("opamp")
bandgap = layout.cell("bandgap")
pfet = layout.cell("sky130_fd_pr__pfet_g5v0d10v5_4KCRW8")

if any(c is None for c in (opamp, bandgap, pfet)):
    raise RuntimeError("Required layout cells missing")

def box(coords):
    return pya.Box(*[round(v / dbu) for v in coords])

def layer(number, datatype):
    idx = layout.find_layer(pya.LayerInfo(number, datatype))
    if idx is None or idx < 0:
        raise RuntimeError(f"Missing layer {number}/{datatype}")
    return idx

nwell = layer(64, 20)
hvi = layer(75, 20)
poly = layer(66, 20)

print("===== FINAL DRC CORRECTIONS =====")

# 1. Remove verified redundant bandgap POLY geometry.
poly_targets = [
    (17.440, -1.880, 19.600, -1.530),
    (24.210, 1.440, 26.370, 1.790),
]

# 2. Adjust only the NWELL in the 4KCRW8 cell.
old_pfet = box((-3.790, -3.485, 3.790, 3.485))
new_pfet = box((-3.640, -3.485, 3.790, 3.485))

def unique_shape(cell, idx, expected):
    matches = [
        s for s in cell.shapes(idx).each()
        if s.is_box() and s.bbox() == expected
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"{cell.name}: expected one shape "
            f"{expected}, found {len(matches)}"
        )
    return matches[0]

# Validate all removals before making changes.
poly_shapes = [
    unique_shape(bandgap, poly, box(coords))
    for coords in poly_targets
]
pfet_shape = unique_shape(pfet, nwell, old_pfet)

# Prevent accidental duplicate application.
bridge = box((0.410, 17.600, 10.880, 19.260))
continuous = box((-13.480, 12.740, 28.460, 27.470))

for idx, name in ((nwell, "NWELL"), (hvi, "HVI")):
    existing = [
        s.bbox() for s in opamp.shapes(idx).each()
        if s.is_box()
    ]
    if bridge in existing or continuous in existing:
        raise RuntimeError(f"{name}: correction already present")

# Apply verified geometry changes.
for shape in poly_shapes:
    shape.delete()

print("Bandgap POLY: 2 rectangles removed")

for idx, name in ((nwell, "NWELL"), (hvi, "HVI")):
    opamp.shapes(idx).insert(bridge)
    opamp.shapes(idx).insert(continuous)
    print(f"{name}: bridge and continuous region added")

pfet_shape.delete()
pfet.shapes(nwell).insert(new_pfet)

print("4KCRW8 NWELL: 0.150 um adjustment applied")

layout.write(dst)

print("===== COMPLETE =====")
print("Output:", dst)
print("Original input preserved")
