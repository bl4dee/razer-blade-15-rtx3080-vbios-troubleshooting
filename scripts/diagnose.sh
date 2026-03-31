#!/usr/bin/env bash
# diagnose.sh — Razer Blade 15 Advanced 2021 (RZ09-0409) GPU Diagnostics
# Run as root from Ubuntu live USB: sudo bash diagnose.sh
# Expected GPU: NVIDIA GA104 RTX 3080 Laptop (10DE:249C/24DC, subsys 1A58:2018)

set -euo pipefail

OUTFILE="gpu_diagnostic_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "========================================"
    echo "=== $1"
    echo "========================================"
}

{
    log "SYSTEM INFO"
    date
    uname -a
    echo ""

    log "1. NVIDIA GPU PCI STATUS (lspci -vnn)"
    lspci -vnn 2>/dev/null | grep -A 30 -i nvidia || echo "!! No NVIDIA device found in lspci"
    echo ""

    # Detect GPU bus address
    GPU_ADDR=$(lspci -nn 2>/dev/null | grep -i nvidia | head -1 | awk '{print $1}')
    if [ -z "$GPU_ADDR" ]; then
        echo "!! CRITICAL: No NVIDIA GPU detected on PCI bus"
        echo "!! Possible causes:"
        echo "!!   - GPU is completely dead (no PCI enumeration)"
        echo "!!   - GPU is disabled in BIOS/UEFI"
        echo "!!   - MUX switch has routed GPU off"
        echo "!!   - Physical connection issue (battery swell damage)"
    else
        echo "GPU detected at bus address: $GPU_ADDR"
        echo ""

        log "2. GPU PCI CONFIG SPACE HEX DUMP (lspci -s $GPU_ADDR -xxx)"
        lspci -s "$GPU_ADDR" -xxx 2>/dev/null || echo "!! Failed to read PCI config space"
        echo ""

        log "2b. GPU PCI VERBOSE (lspci -s $GPU_ADDR -vvv)"
        lspci -s "$GPU_ADDR" -vvv 2>/dev/null || echo "!! Failed to read verbose PCI info"
        echo ""
    fi

    log "3. KERNEL NVIDIA MESSAGES (dmesg | grep nvidia)"
    dmesg 2>/dev/null | grep -i nvidia || echo "(no nvidia messages in dmesg)"
    echo ""

    log "4. ALL HARDWARE ERRORS (dmesg | grep error)"
    dmesg 2>/dev/null | grep -i error | tail -50 || echo "(no error messages)"
    echo ""

    log "5. PCI INITIALIZATION MESSAGES (dmesg | grep pci)"
    dmesg 2>/dev/null | grep -i pci | tail -50 || echo "(no pci messages)"
    echo ""

    log "6. SYSTEM IDENTIFICATION (dmidecode -t system)"
    dmidecode -t system 2>/dev/null || echo "!! dmidecode not available or not root"
    echo ""

    log "7. BIOS VERSION INFO (dmidecode -t bios)"
    dmidecode -t bios 2>/dev/null || echo "!! dmidecode not available"
    echo ""

    log "8. DETAILED GRAPHICS CARD INFO (hwinfo --gfxcard)"
    hwinfo --gfxcard 2>/dev/null || echo "!! hwinfo not installed — run: sudo apt install hwinfo"
    echo ""

    log "9. NVIDIA DRIVER VERSION"
    cat /proc/driver/nvidia/version 2>/dev/null || echo "(nvidia kernel module not loaded — expected for flash)"
    echo ""

    log "10. FULL PCIe TOPOLOGY TREE (lspci -t)"
    lspci -t 2>/dev/null || echo "!! lspci -t failed"
    echo ""

    log "11. TEMPERATURE READINGS (sensors)"
    sensors 2>/dev/null || echo "!! lm-sensors not installed — run: sudo apt install lm-sensors"
    echo ""

    log "12. GPU ROM SYSFS ACCESS"
    echo "Searching for GPU ROM sysfs entries..."
    ls -la /sys/bus/pci/devices/*/rom 2>/dev/null || echo "(no ROM files found)"
    echo ""
    if [ -n "${GPU_ADDR:-}" ]; then
        # Construct full sysfs path (need domain, typically 0000:)
        SYSFS_PATH="/sys/bus/pci/devices/0000:${GPU_ADDR}"
        echo "GPU sysfs path: $SYSFS_PATH"
        if [ -d "$SYSFS_PATH" ]; then
            echo "Directory exists: YES"
            ls -la "$SYSFS_PATH/rom" 2>/dev/null && echo "ROM file: ACCESSIBLE" || echo "ROM file: NOT PRESENT"
            ls -la "$SYSFS_PATH/config" 2>/dev/null && echo "Config file: ACCESSIBLE" || echo "Config file: NOT PRESENT"
            cat "$SYSFS_PATH/vendor" 2>/dev/null && echo " (vendor)"
            cat "$SYSFS_PATH/device" 2>/dev/null && echo " (device)"
            cat "$SYSFS_PATH/subsystem_vendor" 2>/dev/null && echo " (subsystem_vendor)"
            cat "$SYSFS_PATH/subsystem_device" 2>/dev/null && echo " (subsystem_device)"
            cat "$SYSFS_PATH/class" 2>/dev/null && echo " (class)"
            cat "$SYSFS_PATH/current_link_speed" 2>/dev/null && echo " (current_link_speed)" || true
            cat "$SYSFS_PATH/current_link_width" 2>/dev/null && echo " (current_link_width)" || true
            cat "$SYSFS_PATH/max_link_speed" 2>/dev/null && echo " (max_link_speed)" || true
            cat "$SYSFS_PATH/max_link_width" 2>/dev/null && echo " (max_link_width)" || true
        else
            echo "!! Sysfs path $SYSFS_PATH does not exist"
            echo "Listing all PCI devices:"
            ls /sys/bus/pci/devices/ 2>/dev/null
        fi
    fi
    echo ""

    log "13. GPU PCI CONFIG READABILITY"
    if [ -n "${GPU_ADDR:-}" ] && [ -f "/sys/bus/pci/devices/0000:${GPU_ADDR}/config" ]; then
        echo "Config file size: $(wc -c < "/sys/bus/pci/devices/0000:${GPU_ADDR}/config") bytes"
        echo "Config readable: YES"
        echo "First 64 bytes (hex):"
        xxd -l 64 "/sys/bus/pci/devices/0000:${GPU_ADDR}/config" 2>/dev/null || echo "!! xxd failed"
    else
        echo "!! GPU config file not found"
    fi
    echo ""

    log "14. LOADED KERNEL MODULES (GPU related)"
    lsmod 2>/dev/null | grep -iE "nvidia|nouveau|drm|i915" || echo "(no GPU modules loaded)"
    echo ""

    log "15. IOMMU GROUPS (useful for GPU passthrough context)"
    for d in /sys/kernel/iommu_groups/*/devices/*; do
        if [ -e "$d" ]; then
            dev=$(basename "$d")
            desc=$(lspci -nns "$dev" 2>/dev/null)
            if echo "$desc" | grep -qi nvidia; then
                echo "IOMMU Group $(echo "$d" | grep -o 'iommu_groups/[0-9]*' | cut -d/ -f2): $desc"
            fi
        fi
    done 2>/dev/null || echo "(IOMMU info not available)"
    echo ""

    log "DIAGNOSTIC COMPLETE"
    echo "Output saved to: $OUTFILE"
    echo ""
    echo "KEY THINGS TO CHECK:"
    echo "  - Does lspci show the NVIDIA GPU at all? (If not: GPU dead or disabled)"
    echo "  - What Device ID is reported? (249C = fallback/corrupted, 24DC = normal)"
    echo "  - PCIe link speed/width (x8 1.1 = degraded, x16 4.0 = normal)"
    echo "  - Any 'AER' or 'error' messages related to the GPU address"
    echo "  - Is the ROM file accessible via sysfs?"

} 2>&1 | tee "$OUTFILE"

echo ""
echo "Full diagnostic saved to: $(pwd)/$OUTFILE"
