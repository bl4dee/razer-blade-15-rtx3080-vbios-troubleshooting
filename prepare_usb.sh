#!/usr/bin/env bash
# prepare_usb.sh — Prepare USB drive with recovery tools
#
# Two strategies:
#   A) Use existing NixOS live USB (RECOMMENDED — no need to download Ubuntu)
#   B) Create fresh Ubuntu live USB (requires ~5GB download)
#
# This script copies tools to a FAT32 partition accessible from any live Linux.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "  VBIOS Recovery USB Preparation"
echo "============================================"
echo ""
echo "Available block devices:"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL
echo ""

echo "Choose strategy:"
echo "  A) Copy tools to existing NixOS live USB (RECOMMENDED)"
echo "     - No extra download needed"
echo "     - Use nix-shell for flashrom on the Razer"
echo "     - Just copy files to the mounted USB"
echo ""
echo "  B) Create Ubuntu live USB (alternative)"
echo "     - Requires downloading ~5GB ISO"
echo "     - Will ERASE the target USB drive"
echo "     - More straightforward apt-get workflow"
echo ""
read -p "Choose [A/B]: " STRATEGY

case "${STRATEGY^^}" in
    A)
        echo ""
        echo "Strategy A: Copy tools to existing USB"
        echo ""

        # Find NixOS USB mount
        NIXOS_MOUNT=$(findmnt -rn -o TARGET /dev/sdc1 2>/dev/null || echo "")
        if [ -z "$NIXOS_MOUNT" ]; then
            echo "NixOS USB not mounted. Attempting to mount..."
            sudo mkdir -p /mnt/usb
            sudo mount /dev/sdc1 /mnt/usb
            NIXOS_MOUNT="/mnt/usb"
        fi

        DEST="$NIXOS_MOUNT/vbios-recovery"
        echo "Copying tools to: $DEST"
        mkdir -p "$DEST"

        # Copy everything
        cp "$TOOLS_DIR/Razer.RTX3080.8192.210603.rom" "$DEST/"
        cp "$TOOLS_DIR/diagnose.sh" "$DEST/"
        cp "$TOOLS_DIR/flash.sh" "$DEST/"
        cp "$TOOLS_DIR/ch341a_flash.sh" "$DEST/"
        cp "$TOOLS_DIR/PLAN.md" "$DEST/"

        # Copy nvflash if available
        if [ -f "$TOOLS_DIR/nvflash" ]; then
            cp "$TOOLS_DIR/nvflash" "$DEST/"
            chmod +x "$DEST/nvflash"
        elif [ -f "$TOOLS_DIR/nvflash_5.867_linux.zip" ]; then
            cp "$TOOLS_DIR/nvflash_5.867_linux.zip" "$DEST/"
        else
            echo -e "${YELLOW}[!] nvflash not found — download manually from TechPowerUp${NC}"
        fi

        chmod +x "$DEST/diagnose.sh" "$DEST/flash.sh" "$DEST/ch341a_flash.sh"

        echo ""
        echo -e "${GREEN}Files copied to USB:${NC}"
        ls -la "$DEST/"
        echo ""
        echo "MD5 verification of VBIOS on USB:"
        md5sum "$DEST/Razer.RTX3080.8192.210603.rom"
        echo ""
        echo "============================================"
        echo "  NEXT STEPS (NixOS Live on Razer):"
        echo "============================================"
        echo "  1. Plug USB into Razer Blade 15"
        echo "  2. Boot from USB (F12 or DEL at POST)"
        echo "  3. Choose NixOS installer/live"
        echo "  4. Open terminal"
        echo "  5. Mount USB data partition:"
        echo "       sudo mount /dev/sdc1 /mnt  (or wherever the USB appears)"
        echo "  6. cd /mnt/vbios-recovery"
        echo "  7. Enter nix-shell with tools:"
        echo "       nix-shell -p flashrom pciutils lm_sensors dmidecode hwinfo"
        echo "  8. Run diagnostics first:"
        echo "       sudo bash diagnose.sh"
        echo "  9. Review output, then if GPU is detected:"
        echo "       sudo bash flash.sh"
        echo ""
        ;;

    B)
        echo ""
        echo "Strategy B: Create Ubuntu live USB"
        echo ""
        read -p "Target USB device (e.g., /dev/sdc) — THIS WILL BE ERASED: " TARGET_DEV

        if [ ! -b "$TARGET_DEV" ]; then
            echo "Error: $TARGET_DEV is not a block device"
            exit 1
        fi

        echo -e "${RED}WARNING: ALL DATA ON $TARGET_DEV WILL BE DESTROYED${NC}"
        read -p "Type 'ERASE' to confirm: " CONFIRM
        if [ "$CONFIRM" != "ERASE" ]; then
            echo "Aborted."
            exit 1
        fi

        ISO_URL="https://releases.ubuntu.com/24.04/ubuntu-24.04.2-desktop-amd64.iso"
        ISO_FILE="ubuntu-24.04.2-desktop-amd64.iso"

        if [ ! -f "$ISO_FILE" ]; then
            echo "Downloading Ubuntu 24.04 LTS ISO (~5.7GB)..."
            wget -c "$ISO_URL" -O "$ISO_FILE"
        fi

        echo "Writing ISO to $TARGET_DEV..."
        sudo dd if="$ISO_FILE" of="$TARGET_DEV" bs=4M status=progress oflag=sync

        echo "Creating tools partition..."
        # The ISO takes up some space; create a partition in remaining space
        # Use sgdisk or parted to add a partition after the ISO data
        DISK_SIZE=$(blockdev --getsize64 "$TARGET_DEV")
        ISO_SIZE=$(stat -c%s "$ISO_FILE")
        REMAINING=$((DISK_SIZE - ISO_SIZE))

        if [ "$REMAINING" -gt 1073741824 ]; then  # >1GB remaining
            echo "Creating FAT32 tools partition in remaining space..."
            # Calculate start sector (ISO size / 512, rounded up, + buffer)
            START_SECTOR=$(( (ISO_SIZE / 512) + 2048 ))
            echo "n
p
3
$START_SECTOR

t
3
b
w" | sudo fdisk "$TARGET_DEV" 2>/dev/null || true

            sudo partprobe "$TARGET_DEV" 2>/dev/null || true
            sleep 2

            TOOLS_PART="${TARGET_DEV}3"
            if [ -b "$TOOLS_PART" ]; then
                sudo mkfs.vfat -F 32 -n "VBIOS_TOOLS" "$TOOLS_PART"
                sudo mkdir -p /mnt/tools
                sudo mount "$TOOLS_PART" /mnt/tools

                sudo cp "$TOOLS_DIR/Razer.RTX3080.8192.210603.rom" /mnt/tools/
                sudo cp "$TOOLS_DIR/diagnose.sh" /mnt/tools/
                sudo cp "$TOOLS_DIR/flash.sh" /mnt/tools/
                sudo cp "$TOOLS_DIR/ch341a_flash.sh" /mnt/tools/
                [ -f "$TOOLS_DIR/nvflash" ] && sudo cp "$TOOLS_DIR/nvflash" /mnt/tools/

                sudo umount /mnt/tools
                echo "Tools partition created and populated!"
            else
                echo "Could not create tools partition. Copy files manually."
            fi
        else
            echo "Not enough space for tools partition."
            echo "Copy tools to USB manually after booting Ubuntu."
        fi

        echo ""
        echo "============================================"
        echo "  Ubuntu Live USB created!"
        echo "============================================"
        echo "  1. Boot Razer from USB"
        echo "  2. Choose 'Try Ubuntu'"
        echo "  3. Open terminal, install tools:"
        echo "       sudo apt update && sudo apt install -y flashrom hwinfo lm-sensors pciutils"
        echo "  4. Mount tools partition:"
        echo "       sudo mount /dev/sdc3 /mnt"
        echo "  5. cd /mnt && sudo bash diagnose.sh"
        echo ""
        ;;

    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
