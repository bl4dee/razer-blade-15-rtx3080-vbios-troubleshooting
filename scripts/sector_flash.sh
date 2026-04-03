#!/usr/bin/env bash
# Flash VBIOS sector by sector using flashrom, skipping bad sector at 0x111000
set -uo pipefail

VBIOS="/tmp/modified_target.bin"
CHIP="W25Q16.W"
PROGRAMMER="ch341a_spi"
SECTOR_SIZE=4096
BAD_SECTOR=0x111000
TOTAL_SECTORS=512  # 2MB / 4KB

echo "=== Sector-by-sector VBIOS flash ==="
echo "Skipping bad sector at 0x${BAD_SECTOR}"
echo ""

# First check if chip is detected
echo "Detecting chip..."
if ! flashrom -p $PROGRAMMER -c $CHIP 2>&1 | grep -q "Found"; then
    echo "ERROR: Chip not detected! Check clip."
    exit 1
fi
echo "Chip detected!"
echo ""

ERRORS=0
for ((i=0; i<TOTAL_SECTORS; i++)); do
    ADDR=$((i * SECTOR_SIZE))
    ADDR_HEX=$(printf "0x%06X" $ADDR)
    END=$((ADDR + SECTOR_SIZE - 1))
    END_HEX=$(printf "0x%06X" $END)

    # Skip bad sector
    if [ $ADDR -eq $((BAD_SECTOR)) ]; then
        echo "Sector $i/$TOTAL_SECTORS @ $ADDR_HEX: SKIP (bad)"
        continue
    fi

    # Check if sector is all FF in target (skip if so)
    SECTOR_DATA=$(dd if="$VBIOS" bs=1 skip=$ADDR count=$SECTOR_SIZE 2>/dev/null | od -A n -t x1 | tr -d ' \n')
    ALL_FF=$(printf 'ff%.0s' $(seq 1 $SECTOR_SIZE) | head -c $((SECTOR_SIZE * 2)))
    if [ "$SECTOR_DATA" = "$ALL_FF" ]; then
        if [ $((i % 64)) -eq 0 ]; then
            echo "Sector $i/$TOTAL_SECTORS @ $ADDR_HEX: skip (all FF)"
        fi
        continue
    fi

    # Create layout for this sector
    LAYOUT_FILE="/tmp/sector_layout.txt"
    echo "${ADDR_HEX}:${END_HEX} target_sector" > "$LAYOUT_FILE"

    # Write this sector
    if flashrom -p $PROGRAMMER -c $CHIP -l "$LAYOUT_FILE" --image target_sector -w "$VBIOS" --force 2>&1 | grep -q "done"; then
        if [ $((i % 16)) -eq 0 ]; then
            echo "Sector $i/$TOTAL_SECTORS @ $ADDR_HEX: OK"
        fi
    else
        echo "Sector $i/$TOTAL_SECTORS @ $ADDR_HEX: FAILED"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "=== Done! Errors: $ERRORS ==="
if [ $ERRORS -eq 0 ]; then
    echo "SUCCESS! Now verify with: flashrom -p $PROGRAMMER -c $CHIP -v $VBIOS"
fi
