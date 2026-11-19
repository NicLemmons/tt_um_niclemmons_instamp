import pya
import os
from pathlib import Path

src = os.environ.get("GDS_INPUT")
if not src:
    raise RuntimeError("Set GDS_INPUT to a raw Magic GDS export")
dst = os.environ.get("GDS_OUTPUT")
if not dst:
    raise RuntimeError("Set GDS_OUTPUT to the cleaned output path")
if Path(src).resolve() == Path(dst).resolve():
    raise RuntimeError("Input and output must be different files")

layout = pya.Layout()
layout.read(src)

bandgap = layout.cell("bandgap")
top = layout.cell("tt_um_niclemmons_instamp")

if bandgap is None or top is None:
    raise RuntimeError("Required cells not found")

print("===== BANDGAP DUPLICATE CONTACT TEST =====")

total_removed = 0

for number, datatype, name in (
    (66, 44, "LICON"),
):
    li = layout.find_layer(
        pya.LayerInfo(number, datatype)
    )

    if li < 0:
        continue

    # Record complete original flattened geometry.
    before = pya.Region(
        top.begin_shapes_rec(li)
    )

    # Find rectangular contacts contributed by child cells.
    child_boxes = set()

    it = bandgap.begin_shapes_rec(li)

    while not it.at_end():
        shape = it.shape()

        if (it.cell().name != "bandgap"
                and shape.is_box()):
            transformed = it.trans() * shape.box
            child_boxes.add(
                (transformed.left, transformed.bottom, transformed.right, transformed.top)
            )

        it.next()

    # Identify identical contacts drawn in bandgap itself.
    to_delete = []

    for shape in bandgap.shapes(li).each():
        if not shape.is_box():
            continue

        key = (shape.box.left, shape.box.bottom, shape.box.right, shape.box.top)

        if key in child_boxes:
            to_delete.append(shape)

    print(f"\n{name}")
    print("Duplicate parent contacts:", len(to_delete))

    for shape in to_delete:
        shape.delete()

    # Check that removing duplicates did not change
    # any flattened physical geometry.
    after = pya.Region(
        top.begin_shapes_rec(li)
    )

    if not (before ^ after).is_empty():
        raise RuntimeError(
            f"{name}: Flattened geometry changed!"
        )

    print("Flattened geometry: IDENTICAL")
    total_removed += len(to_delete)

print("\nTotal duplicate parent contacts:", total_removed)

if total_removed == 0:
    raise RuntimeError("No duplicate contacts removed")

layout.write(dst)

print("Diagnostic GDS:", dst)
print("Original project: UNCHANGED")
