# Razer Blade 15 Advanced 2021 — VBIOS Recovery Plan

## Target Hardware
- **Laptop:** Razer Blade 15 Advanced 2021 (RZ09-0409)
- **GPU:** NVIDIA GA104 RTX 3080 Laptop, 8GB GDDR6, 105W TDP
- **Hardware Device ID:** 10DE:249C (silicon fallback) → VBIOS sets it to 10DE:24DC
- **Subsystem ID:** 1A58:2018
- **Flash Chip:** Winbond W25Q16JWN (1.8V SOP8, 16Mbit/2MB)
- **Symptom:** Code 43, GPU-Z shows "Unknown" BIOS, 0 MHz clocks, 0 MB memory

## Device ID Explanation
With corrupted VBIOS, the GPU reports its silicon-default PCI ID (249C).
The correct VBIOS programs it to 24DC. This is normal NVIDIA behavior.
The subsystem ID 1A58:2018 and 105W TDP confirm VBIOS 235669 is correct.

## VBIOS File
- **File:** Razer.RTX3080.8192.210603.rom
- **Source:** TechPowerUp #235669
- **Version:** 94.04.55.00.92
- **MD5:** f458d34324bfd843bee5107006a0e70f ✓ VERIFIED
- **Size:** 999,424 bytes (976 KB)

## Attack Plan (in order of likelihood of success)

### Method 1: Software Flash via NVFlash (Linux)
Boot live Linux → unload GPU drivers → nvflash the ROM.
**Chance of success: ~30%** — corrupted VBIOS often prevents nvflash communication.

### Method 2: Sysfs ROM Write (Linux)
Write ROM through /sys/bus/pci/devices/.../rom interface.
**Chance of success: ~10%** — GPU must enumerate with ROM access enabled.

### Method 3: CH341A Hardware Programmer (Most Reliable)
Direct SPI flash to the Winbond chip, bypassing the GPU entirely.
**Chance of success: ~95%** — only fails if the chip or traces are physically damaged.

**Required hardware:**
- CH341A USB programmer ($5-15)
- **1.8V adapter board (CRITICAL — chip is 1.8V, CH341A native is 3.3V)**
- SOP8 test clip (Pomona 5250 or similar)

## File Inventory
- `diagnose.sh` — Run first, saves full GPU diagnostic to log file
- `flash.sh` — Automated software flash (tries nvflash → sysfs → prints CH341A instructions)
- `ch341a_flash.sh` — Interactive hardware flash script with safety checks
- `Razer.RTX3080.8192.210603.rom` — The VBIOS file (MD5 verified)
- `PLAN.md` — This file

## NVFlash Download (Manual Required)
TechPowerUp blocks automated downloads. Download manually:
1. Go to: https://www.techpowerup.com/download/nvidia-nvflash/
2. Download "nvflash_5.867_linux.zip" (26.4 MB)
3. Extract and place `nvflash` binary in this directory
4. MD5 of zip: DC4775FDEFA3D4CBF2B5AB9178A4720E
