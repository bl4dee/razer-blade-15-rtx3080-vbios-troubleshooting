#!/usr/bin/env bash
# ch341a_flash.sh — Hardware SPI flash using CH341A programmer
# For Razer Blade 15 Advanced 2021 RTX 3080 VBIOS recovery
#
# CHIP: Winbond W25Q16JWN (1.8V SOP8, 16Mbit / 2MB)
# LOCATION: Near the GA104 GPU die on the motherboard
#
# ╔══════════════════════════════════════════════════════════════╗
# ║  CRITICAL: YOU MUST USE A 1.8V ADAPTER WITH THE CH341A!    ║
# ║  The W25Q16JWN operates at 1.65V-1.95V ONLY.               ║
# ║  Direct CH341A connection (3.3V/5V) WILL DESTROY THE CHIP. ║
# ╚══════════════════════════════════════════════════════════════╝
#
# Required hardware:
#   1. CH341A USB SPI programmer
#   2. 1.8V voltage adapter board (CH341A 1.8V adapter)
#   3. SOP8 test clip (e.g., Pomona 5250) OR fine soldering
#
# Physical setup:
#   1. Power off laptop COMPLETELY (hold power 10s after shutdown)
#   2. Disconnect the battery (if accessible — Razer uses internal battery)
#   3. Remove bottom panel screws
#   4. Locate Winbond W25Q16JWN near GPU (small 8-pin SOP8 chip)
#   5. Verify chip markings: "25Q16JWNI" or similar
#   6. Connect SOP8 clip to chip (pin 1 = dot/notch on chip)
#   7. Connect clip → 1.8V adapter → CH341A → USB to your computer
#
# SOP8 Pin 1 orientation:
#   Pin 1 is marked with a dot or notch on the chip package.
#   The SOP8 clip's red wire typically corresponds to pin 1.
#
#   W25Q16JWN pinout:
#     Pin 1: /CS    Pin 8: VCC (1.8V)
#     Pin 2: DO     Pin 7: /HOLD
#     Pin 3: /WP    Pin 6: CLK
#     Pin 4: GND    Pin 5: DI

set -euo pipefail

VBIOS="Razer.RTX3080.8192.210603.rom"
PROGRAMMER="ch341a_spi"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[!]${NC} $1"; }

if [ "$(id -u)" -ne 0 ]; then
    err "Run as root: sudo bash ch341a_flash.sh"
    exit 1
fi

if ! command -v flashrom &>/dev/null; then
    err "flashrom not installed."
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt install flashrom"
    echo "  NixOS:         nix-shell -p flashrom"
    exit 1
fi

if [ ! -f "$VBIOS" ]; then
    err "VBIOS file not found: $VBIOS"
    exit 1
fi

echo "============================================"
echo "  CH341A Hardware VBIOS Flash"
echo "  Chip: Winbond W25Q16JWN (1.8V)"
echo "============================================"
echo ""
warn "PREFLIGHT CHECKLIST:"
echo "  [ ] Laptop powered off and battery disconnected"
echo "  [ ] 1.8V adapter between CH341A and SOP8 clip"
echo "  [ ] SOP8 clip properly seated on chip (pin 1 aligned)"
echo "  [ ] CH341A connected to THIS computer via USB"
echo ""
read -p "All checks passed? Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# ──────────────────────────────────────────────────────────────
# STEP 1: Detect chip
# ──────────────────────────────────────────────────────────────
log "STEP 1: Detecting flash chip..."
echo "Running: flashrom -p $PROGRAMMER"
if ! flashrom -p "$PROGRAMMER" 2>&1; then
    err "Chip detection failed!"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check USB connection"
    echo "  - Check SOP8 clip alignment (reseat clip)"
    echo "  - Verify 1.8V adapter is connected"
    echo "  - Try: flashrom -p $PROGRAMMER -c W25Q16.W"
    echo "  - Check dmesg for CH341A USB errors"
    exit 1
fi
echo ""

# ──────────────────────────────────────────────────────────────
# STEP 2: Read/backup corrupted VBIOS
# ──────────────────────────────────────────────────────────────
log "STEP 2: Reading current (corrupted) chip contents for backup..."
echo "Running: flashrom -p $PROGRAMMER -c W25Q16.W -r backup_corrupted_hw.bin"
if flashrom -p "$PROGRAMMER" -c "W25Q16.W" -r backup_corrupted_hw.bin 2>&1; then
    log "Backup saved to: backup_corrupted_hw.bin ($(wc -c < backup_corrupted_hw.bin) bytes)"

    # Double-read for verification
    log "Reading again to verify consistent reads..."
    flashrom -p "$PROGRAMMER" -c "W25Q16.W" -r backup_corrupted_hw_verify.bin 2>&1
    if cmp -s backup_corrupted_hw.bin backup_corrupted_hw_verify.bin; then
        log "Both reads match — connection is stable"
    else
        err "Reads don't match! Connection may be unstable."
        err "Reseat the SOP8 clip and try again."
        exit 1
    fi
else
    warn "Could not read chip. Trying without chip specification..."
    flashrom -p "$PROGRAMMER" -r backup_corrupted_hw.bin 2>&1 || true
fi
echo ""

# ──────────────────────────────────────────────────────────────
# STEP 3: Pad VBIOS to chip size if needed
# ──────────────────────────────────────────────────────────────
CHIP_SIZE=2097152  # W25Q16 = 16Mbit = 2MB
VBIOS_SIZE=$(wc -c < "$VBIOS")

log "STEP 3: Preparing VBIOS for flash..."
log "  Chip size:  $CHIP_SIZE bytes (2MB)"
log "  VBIOS size: $VBIOS_SIZE bytes"

if [ "$VBIOS_SIZE" -lt "$CHIP_SIZE" ]; then
    log "VBIOS is smaller than chip — padding with 0xFF to fill 2MB"
    cp "$VBIOS" padded_vbios.bin
    dd if=/dev/zero bs=1 count=$((CHIP_SIZE - VBIOS_SIZE)) 2>/dev/null | tr '\000' '\377' >> padded_vbios.bin
    FLASH_FILE="padded_vbios.bin"
    log "Padded file size: $(wc -c < padded_vbios.bin) bytes"
elif [ "$VBIOS_SIZE" -eq "$CHIP_SIZE" ]; then
    log "VBIOS matches chip size exactly"
    FLASH_FILE="$VBIOS"
else
    err "VBIOS ($VBIOS_SIZE bytes) is LARGER than chip ($CHIP_SIZE bytes)!"
    err "This should not happen. Verify you have the correct VBIOS file."
    exit 1
fi
echo ""

# ──────────────────────────────────────────────────────────────
# STEP 4: Write VBIOS to chip
# ──────────────────────────────────────────────────────────────
log "STEP 4: Writing VBIOS to flash chip..."
warn "DO NOT DISCONNECT ANYTHING DURING THIS PROCESS!"
echo ""
echo "Running: flashrom -p $PROGRAMMER -c W25Q16.W -w $FLASH_FILE"
if flashrom -p "$PROGRAMMER" -c "W25Q16.W" -w "$FLASH_FILE" 2>&1; then
    log "Write completed successfully!"
else
    err "Write FAILED!"
    echo ""
    echo "If write failed, the chip may be in an inconsistent state."
    echo "Try again: flashrom -p $PROGRAMMER -c W25Q16.W -w $FLASH_FILE"
    echo ""
    echo "If repeated failures, try erasing first:"
    echo "  flashrom -p $PROGRAMMER -c W25Q16.W -E"
    echo "  flashrom -p $PROGRAMMER -c W25Q16.W -w $FLASH_FILE"
    exit 1
fi
echo ""

# ──────────────────────────────────────────────────────────────
# STEP 5: Verify write
# ──────────────────────────────────────────────────────────────
log "STEP 5: Verifying flash contents..."
echo "Running: flashrom -p $PROGRAMMER -c W25Q16.W -v $FLASH_FILE"
if flashrom -p "$PROGRAMMER" -c "W25Q16.W" -v "$FLASH_FILE" 2>&1; then
    echo ""
    log "========================================="
    log "  FLASH AND VERIFY SUCCESSFUL!"
    log "========================================="
    echo ""
    log "Next steps:"
    log "  1. Disconnect CH341A from chip"
    log "  2. Reconnect battery"
    log "  3. Reassemble laptop"
    log "  4. Boot into Windows"
    log "  5. Check GPU-Z — should show RTX 3080, VBIOS 94.04.55.00.92"
    log "  6. Check Device Manager — Code 43 should be gone"
    echo ""
    log "REBOOT NOW AND CHECK GPU-Z IN WINDOWS"
else
    err "VERIFICATION FAILED!"
    err "The written data does not match the source file."
    err "Try the write again. If it keeps failing, the chip may be damaged."
fi
