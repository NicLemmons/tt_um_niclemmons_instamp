#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

OUTPUT="${1:-/tmp/tt_instamp_build_candidate.gds}"

RC="$HOME/.ciel/sky130A/libs.tech/magic/sky130A.magicrc"

# Protect the checked-in GDS until verification is finished.
REPO_GDS="$ROOT/gds/tt_um_niclemmons_instamp.gds"

if [[ "$(realpath -m "$OUTPUT")" == \
      "$(realpath -m "$REPO_GDS")" ]]; then
    echo "ERROR: Refusing to overwrite repository GDS."
    exit 1
fi

WORKDIR="$(mktemp -d /tmp/tt_instamp_build.XXXXXX)"

RAW="$WORKDIR/raw.gds"
LICON="$WORKDIR/licon_clean.gds"
FINAL="$WORKDIR/final.gds"

echo "======================================"
echo "INSTRUMENTATION AMPLIFIER GDS BUILD"
echo "======================================"
echo "Project: $ROOT"
echo "Working directory: $WORKDIR"

echo
echo "===== STEP 1: MAGIC EXPORT ====="

(
    cd "$ROOT/layout/mag"

    export GDS_FILE="$RAW"

    magic -dnull -noconsole -rcfile "$RC" \
      > "$WORKDIR/magic.log" 2>&1 <<'TCL'
drc off
load tt_um_niclemmons_instamp
gds write $env(GDS_FILE)
quit -noprompt
TCL
)

test -s "$RAW"
echo "Magic export: SUCCESS"

echo
echo "===== STEP 2: LICON CLEANUP ====="

GDS_INPUT="$RAW" \
GDS_OUTPUT="$LICON" \
klayout -b -r "$ROOT/scripts/cleanup_bandgap_licon.py"

test -s "$LICON"

echo
echo "===== STEP 3: RPM CORRECTIONS ====="

GDS_INPUT="$LICON" \
GDS_OUTPUT="$FINAL" \
klayout -b -r "$ROOT/scripts/fix_rpm_markers.py"

test -s "$FINAL"

echo
echo "===== STEP 4: SAVE CANDIDATE ====="

mkdir -p "$(dirname "$OUTPUT")"
cp "$FINAL" "$OUTPUT"

echo
echo "======================================"
echo "BUILD COMPLETE"
echo "======================================"
echo "Output: $OUTPUT"
echo "Build logs: $WORKDIR"
echo "Repository GDS: UNCHANGED"

if grep -q "problems occurred" "$WORKDIR/magic.log"; then
    echo
    echo "WARNING: Magic reported feedback entries."
    grep "problems occurred" "$WORKDIR/magic.log"
    echo "Review: $WORKDIR/magic.log"
fi

echo
ls -lh "$OUTPUT"
