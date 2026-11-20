# ECE 5120 — Instrumentation Amplifier Layout Verification

Date: November 19, 2026
Technology: SKY130A
Top cell: tt_um_niclemmons_instamp

## Final Design Files

- GDS: gds/tt_um_niclemmons_instamp.gds
- LEF: lef/tt_um_niclemmons_instamp.lef
- Magic layout: layout/mag/
- Build script: scripts/build_gds.sh
- LICON cleanup: scripts/cleanup_bandgap_licon.py
- RPM corrections: scripts/fix_rpm_markers.py

## DRC Verification

| Check | Result |
|---|---|
| Magic DRC on corrected source | 0 errors |
| Tiny Tapeout KLayout FEOL | 0 violations |
| Tiny Tapeout KLayout BEOL | 0 violations |
| Original full SKY130A KLayout deck | 23 markers |

The unmodified full SKY130A KLayout deck reports:

- m1.3ab: 15
- m3.3ab: 1
- m4.5ab: 7

A diagnostic version of the deck using
without_touching_edges on the wide-metal
separation checks reports zero violations.

This diagnostic does not establish sign-off
compliance with the unmodified full deck.

## LVS Verification

Tool: Netgen with SKY130A setup.

Comparison:
- SPICE extracted from production GDS
- Normalized Xschem schematic reference

Result: Circuits match uniquely.

The schematic normalization removed an
ideal 0 V current-measurement source and
reconnected its associated schematic nodes.

The extraction reports a duplicate-pin
warning for uio_oe[1]. This warning did
not prevent the unique LVS match.

## Interface Verification

- LEF pins: 54 unique
- GDS text labels: 54
- Digital pin directions: 40/40 correct
- uo_out labels: 8/8 present
- uio_out labels: 8/8 present
- uio_oe labels: 8/8 present

Magic's extracted SPICE interface has
30 ports because the 24 output signals
were consolidated with VGND.

All 24 output labels remain in the GDS.
Their intentional tie-off behavior should
be confirmed against the system interface
requirements.

## GDS Reproducibility

The production GDS was rebuilt from
the permanent Magic source.

Its flattened physical geometry matched
the verified trial across all 32 layers.

Production GDS SHA-256:
cbca486e51267f2e386a6f8171bbbb801e0f09c6905c09b26de0871ac00703f2

Production LEF SHA-256:
78e914ba9d90689fbfb21f8bde8b5e6fad3e4ae52f3a97ad148e18128f35025c

## Remaining Qualifications

1. Resolve or formally justify the 23
   markers from the original full SKY130A
   KLayout deck before claiming full
   PDK sign-off.
2. Review the Netgen duplicate-pin warning.
3. Confirm the intended output tie-offs.
4. Electrical performance simulations and
   post-layout characterization are separate
   from the DRC/LVS verification documented
   here.
