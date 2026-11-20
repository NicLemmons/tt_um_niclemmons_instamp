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
rpm = layout.find_layer(pya.LayerInfo(86, 20))

if rpm < 0:
    raise RuntimeError("RPM layer 86/20 not found")

# Exact differences established against verified GDS.
changes = {
    "sky130_fd_pr__res_high_po_0p69_4NKL3V": {
        (-2.30, -3.61, -1.21, -0.93):
        (-2.30, -3.61, -1.01, -0.93),

        (1.21, -3.61, 2.30, -0.93):
        (1.01, -3.61, 2.30, -0.93),
    },

    "sky130_fd_pr__res_high_po_0p35_5B63ZM": {
        (-0.375, -4.03, 0.375, 4.03):
        (-0.650, -4.03, 0.650, 4.03),
    },
}

def make_box(coords):
    return pya.Box(*[
        round(v / dbu) for v in coords
    ])


# Verify the old bandgap RPM violation is already absent.
bandgap = layout.cell("bandgap")

if bandgap is None:
    raise RuntimeError("Bandgap cell missing")

old_marker = make_box((23.81, 1.24, 24.01, 1.99))

remaining = [
    shape for shape in bandgap.shapes(rpm).each()
    if shape.bbox().overlaps(old_marker)
]

if remaining:
    raise RuntimeError(
        "Unexpected RPM geometry remains at old bandgap marker"
    )

print("Bandgap RPM marker: ALREADY CORRECTED")

print("===== RPM CORRECTION =====")

operations = []

# Validate every expected shape before modifying anything.
for cell_name, replacements in changes.items():
    cell = layout.cell(cell_name)

    if cell is None:
        raise RuntimeError(f"Missing cell: {cell_name}")

    print(f"\nCELL: {cell_name}")

    for old, new in replacements.items():
        matches = [
            shape
            for shape in cell.shapes(rpm).each()
            if shape.is_box()
            and shape.bbox() == make_box(old)
        ]

        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one RPM shape in {cell_name}: "
                f"{old}; found {len(matches)}"
            )

        operations.append(
            (cell, matches[0], new)
        )

        print("Original:", old)
        print("Updated: ", new or "REMOVED")

assert len(operations) == 3

# Apply changes only after all geometry is validated.
for cell, shape, new in operations:
    shape.delete()

    if new is not None:
        cell.shapes(rpm).insert(make_box(new))

layout.write(dst)

print("\n===== COMPLETE =====")
print("RPM corrections:", len(operations))
print("Output:", dst)
print("Input preserved: YES")
