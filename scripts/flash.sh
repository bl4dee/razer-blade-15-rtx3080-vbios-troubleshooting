#!/usr/bin/env bash
# flash.sh — VBIOS Flash Script for Razer Blade 15 Advanced 2021 RTX 3080
# Run as root from Ubuntu live USB: sudo bash flash.sh
#
# IMPORTANT: Run diagnose.sh FIRST and review the output before running this!
# This script will attempt multiple methods to flash the VBIOS.

set -euo pipefail

VBIOS="Razer.RTX3080.8192.210603.rom"
NVFLASH="./nvflash"
LOGFILE="flash_$(date +%Y%m%d_%H%M%S).log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1" | tee -a "$LOGFILE"; }
warn() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOGFILE"; }
err() { echo -e "${RED}[!]${NC} $1" | tee -a "$LOGFILE"; }

if [ "$(id -u)" -ne 0 ]; then
    err "This script must be run as root. Use: sudo bash flash.sh"
    exit 1
fi

if [ ! -f "$VBIOS" ]; then
    err "VBIOS file not found: $VBIOS"
    err "Make sure the ROM file is in the current directory."
    exit 1
fi

log "VBIOS file: $VBIOS"
log "MD5: $(md5sum "$VBIOS" | awk '{print $1}')"
log "Expected MD5: f458d34324bfd843bee5107006a0e70f"
echo "" | tee -a "$LOGFILE"

# Verify MD5
ACTUAL_MD5=$(md5sum "$VBIOS" | awk '{print $1}')
if [ "$ACTUAL_MD5" != "f458d34324bfd843bee5107006a0e70f" ]; then
    err "MD5 MISMATCH! VBIOS file may be corrupted. Aborting."
    exit 1
fi
log "MD5 verified OK"

# Detect GPU
GPU_ADDR=$(lspci -nn 2>/dev/null | grep -i nvidia | head -1 | awk '{print $1}')
if [ -z "$GPU_ADDR" ]; then
    err "No NVIDIA GPU found on PCI bus. Cannot flash."
    err "The GPU may be completely dead or disabled in BIOS."
    exit 1
fi
log "GPU found at PCI address: $GPU_ADDR"

# ──────────────────────────────────────────────────────────────
# STEP 1: Unload GPU kernel modules
# ──────────────────────────────────────────────────────────────
log "STEP 1: Unloading GPU kernel modules..."

# Blacklist modules to prevent reload
cat > /etc/modprobe.d/blacklist-nvidia-flash.conf << 'MODCONF'
blacklist nouveau
blacklist nvidia
blacklist nvidia_drm
blacklist nvidia_modeset
blacklist nvidia_uvm
MODCONF
log "Blacklisted nvidia/nouveau modules in modprobe.d"

for mod in nvidia_uvm nvidia_drm nvidia_modeset nvidia nouveau; do
    if lsmod | grep -q "^${mod}"; then
        log "Unloading module: $mod"
        rmmod "$mod" 2>/dev/null || warn "Could not unload $mod (may have dependencies)"
    fi
done

# Verify no nvidia modules loaded
if lsmod | grep -qi nvidia; then
    warn "Some nvidia modules still loaded:"
    lsmod | grep -i nvidia | tee -a "$LOGFILE"
    warn "Continuing anyway — nvflash may still work..."
else
    log "All nvidia modules unloaded successfully"
fi

if lsmod | grep -q nouveau; then
    warn "nouveau still loaded — trying harder..."
    rmmod nouveau 2>/dev/null || true
fi

echo "" | tee -a "$LOGFILE"

# ──────────────────────────────────────────────────────────────
# STEP 2: NVFlash standard attempt
# ──────────────────────────────────────────────────────────────
log "STEP 2: Attempting NVFlash (standard)..."

if [ ! -x "$NVFLASH" ]; then
    if [ -f "$NVFLASH" ]; then
        chmod +x "$NVFLASH"
    else
        err "nvflash binary not found at $NVFLASH"
        err "Make sure nvflash is in the current directory"
        warn "Skipping to alternative methods..."
        NVFLASH_AVAILABLE=false
    fi
fi

NVFLASH_AVAILABLE=${NVFLASH_AVAILABLE:-true}

if [ "$NVFLASH_AVAILABLE" = true ]; then
    log "Running: nvflash --list"
    $NVFLASH --list 2>&1 | tee -a "$LOGFILE" || true
    echo "" | tee -a "$LOGFILE"

    log "Disabling write protection..."
    $NVFLASH --protectoff --index=0 2>&1 | tee -a "$LOGFILE" || true
    echo "" | tee -a "$LOGFILE"

    log "Running: nvflash --index=0 $VBIOS"
    if $NVFLASH --index=0 "$VBIOS" 2>&1 | tee -a "$LOGFILE"; then
        log "========================================="
        log "NVFLASH SUCCEEDED!"
        log "========================================="
        log "REBOOT NOW AND CHECK GPU-Z IN WINDOWS"
        exit 0
    else
        warn "Standard nvflash failed. Trying with override flags..."
    fi

    # ──────────────────────────────────────────────────────────────
    # STEP 3: NVFlash with override flags
    # ──────────────────────────────────────────────────────────────
    echo "" | tee -a "$LOGFILE"
    log "STEP 3: Attempting NVFlash with override flag -6..."
    log "Running: nvflash -6 --index=0 $VBIOS"
    if $NVFLASH -6 --index=0 "$VBIOS" 2>&1 | tee -a "$LOGFILE"; then
        log "========================================="
        log "NVFLASH WITH -6 OVERRIDE SUCCEEDED!"
        log "========================================="
        log "REBOOT NOW AND CHECK GPU-Z IN WINDOWS"
        exit 0
    else
        warn "NVFlash -6 also failed."
    fi

    # Try additional override combinations
    echo "" | tee -a "$LOGFILE"
    log "STEP 3b: Trying nvflash --overridesub --index=0..."
    if $NVFLASH --overridesub --index=0 "$VBIOS" 2>&1 | tee -a "$LOGFILE"; then
        log "========================================="
        log "NVFLASH WITH --overridesub SUCCEEDED!"
        log "========================================="
        log "REBOOT NOW AND CHECK GPU-Z IN WINDOWS"
        exit 0
    else
        warn "NVFlash --overridesub also failed."
    fi
fi

# ──────────────────────────────────────────────────────────────
# STEP 4: Sysfs ROM write attempt
# ──────────────────────────────────────────────────────────────
echo "" | tee -a "$LOGFILE"
log "STEP 4: Attempting sysfs ROM write..."

SYSFS_ROM="/sys/bus/pci/devices/0000:${GPU_ADDR}/rom"
if [ -e "$SYSFS_ROM" ]; then
    log "ROM sysfs node exists at $SYSFS_ROM"

    # Enable ROM writing
    log "Enabling ROM write access..."
    echo 1 > "$SYSFS_ROM" 2>/dev/null || true

    # Read current (corrupted) ROM for backup
    log "Reading current corrupted ROM for backup..."
    cat "$SYSFS_ROM" > backup_corrupted_sysfs.rom 2>/dev/null || warn "Could not read current ROM"

    # Attempt write
    log "Writing new VBIOS via sysfs..."
    if cp "$VBIOS" "$SYSFS_ROM" 2>&1 | tee -a "$LOGFILE"; then
        log "========================================="
        log "SYSFS ROM WRITE COMPLETED!"
        log "========================================="
        warn "NOTE: sysfs ROM write has limitations — it may not persist after reboot."
        warn "Verify by reading back: cat $SYSFS_ROM > readback.rom && md5sum readback.rom"
        log "REBOOT NOW AND CHECK GPU-Z IN WINDOWS"
        exit 0
    else
        warn "Sysfs ROM write failed."
    fi
else
    warn "No ROM sysfs node at $SYSFS_ROM"
    warn "This is common with corrupted VBIOS — the GPU may not expose ROM via sysfs."
fi

# ──────────────────────────────────────────────────────────────
# STEP 5: All software methods failed
# ──────────────────────────────────────────────────────────────
echo "" | tee -a "$LOGFILE"
err "========================================="
err "ALL SOFTWARE FLASH METHODS FAILED"
err "========================================="
echo "" | tee -a "$LOGFILE"
warn "You need a CH341A USB SPI programmer for hardware flashing."
warn "The flash chip is: Winbond W25Q16JWN (1.8V SOP8)"
echo "" | tee -a "$LOGFILE"
echo "Required hardware:" | tee -a "$LOGFILE"
echo "  1. CH341A USB programmer (~\$5-15 on Amazon)" | tee -a "$LOGFILE"
echo "  2. 1.8V adapter board (CRITICAL - chip is 1.8V, CH341A outputs 3.3V/5V)" | tee -a "$LOGFILE"
echo "  3. SOP8 test clip or soldering equipment" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"
echo "See ch341a_flash.sh for exact hardware flash commands." | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"
echo "IMPORTANT WARNINGS:" | tee -a "$LOGFILE"
echo "  - DO NOT connect CH341A directly without 1.8V adapter — you WILL fry the chip" | tee -a "$LOGFILE"
echo "  - The W25Q16JWN is rated for 1.65V-1.95V only" | tee -a "$LOGFILE"
echo "  - Power off the laptop completely before connecting the programmer" | tee -a "$LOGFILE"
echo "  - Disconnect the battery if possible" | tee -a "$LOGFILE"

echo "" | tee -a "$LOGFILE"
log "Flash log saved to: $(pwd)/$LOGFILE"
