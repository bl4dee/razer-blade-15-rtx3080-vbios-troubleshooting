# Razer Blade 15 RTX 3080 VBIOS Recovery — Troubleshooting

Documenting the full process of recovering a corrupted NVIDIA VBIOS on a Razer Blade 15 Advanced 2021 (RZ09-0409) with an RTX 3080 Laptop GPU (GA104M).

## The Problem

The GPU's VBIOS SPI flash chip (Winbond W25Q16JWN) is corrupted, causing:
- **Windows:** GPU Code 43, GPU-Z shows "Unknown" BIOS, 0 MHz clocks, 0 MB memory
- **Linux:** Device ID reports 10DE:249C (silicon fallback) instead of correct 10DE:24DC
- **PCIe:** Link degraded to 2.5 GT/s x8 (should be 16 GT/s x16)

The core challenge is a **chicken-and-egg problem**: the GPU's falcon microcontroller manages the SPI flash, but the falcon needs valid VBIOS firmware (stored on that same SPI flash) to boot. Every software flash tool requires either a running falcon or valid VBIOS to initialize.

## Status

See **[STATUS.md](STATUS.md)** for a structured list of:
- Every method tried, with exact commands, results, and timestamps
- Every method NOT yet tried, with priority ranking and rationale

## Files

| File | Description |
|---|---|
| `STATUS.md` | Master tracking: tried/untried methods with results |
| `TROUBLESHOOTING_LOG.md` | Detailed narrative log of all sessions |
| `PLAN.md` | Original attack plan with methods ranked by success probability |
| `diagnose.sh` | GPU diagnostic script (lspci, dmesg, dmidecode, sysfs) |
| `flash.sh` | Automated software flash (nvflash → sysfs → CH341A instructions) |
| `ch341a_flash.sh` | Interactive hardware SPI flash script with safety checks |
| `logs/` | Raw diagnostic and flash attempt output |

## Hardware Info

| | |
|---|---|
| **Laptop** | Razer Blade 15 Advanced 2021 (RZ09-0409CEC3) |
| **GPU** | NVIDIA GA104M RTX 3080 Laptop 8GB |
| **GPU Device ID** | 10DE:249C (fallback) → should be 10DE:24DC |
| **Subsystem ID** | 1A58:2018 |
| **VBIOS Chip** | Winbond W25Q16JWN (1.8V SOP8, 16Mbit/2MB) |
| **Target VBIOS** | TechPowerUp #235669, v94.04.55.00.92 |
| **VBIOS MD5** | f458d34324bfd843bee5107006a0e70f |

## Key Findings

1. **nvflash** (all versions/flags) fails with "EEPROM not found" — the falcon is halted, so nvflash can't reach the SPI controller
2. **Sysfs ROM write** fails — ROM BAR is 512KB but VBIOS is 976KB
3. **NVIDIA open driver** (580) fails — hard GSP dependency for Ampere, GSP needs VBIOS to bootstrap
4. **nouveau** fails — all 5 BIOS sources (PRAMIN, PROM, ACPI, PCIROM, PLATFORM) return corrupt or empty data
5. **Direct BAR0 register access** confirms GPU silicon is alive (GA104) but SPI controller regions return BADF (uninitialized falcon)
6. **PCIe bus reset** produces definitive error: `Falcon In HALT or STOP state` — confirming the chicken-and-egg
7. **System BIOS** (12MB scanned via MTD) does NOT contain an embedded GPU VBIOS
8. **VBIOS file format** starts with `NVGI` (NVIDIA container), not `55 AA` — first PCI ROM sub-image at offset 0x9400
9. **FWSEC hardware security** on the GPU die cryptographically verifies VBIOS from SPI before unlocking ANY falcon — this is the definitive reason all 29 software methods fail

## Root Cause: FWSEC Hardware Security

NVIDIA Ampere GPUs have a dedicated hardware block called **FWSEC** (Firmware Security) that:
1. Reads the VBIOS directly from the SPI flash chip (not through software or the falcon)
2. Verifies a full cryptographic chain: digital signature → certificate → device ID → HAT → HULK
3. Only AFTER successful verification does it unlock the falcon microcontrollers

**No software — no driver, no registry key, no kernel module, no firmware override — can bypass FWSEC.** The SPI flash chip must be physically reprogrammed using an external hardware programmer.

## Solution: Hardware SPI Programming

**Order these parts (~$20-28 total):**
| Part | Price |
|---|---|
| CH341A USB programmer | ~$8-12 |
| 1.8V adapter board | ~$5-8 |
| SOIC8/SOP8 test clip | ~$5-8 |

**⚠️ CRITICAL: The W25Q16JWN is a 1.8V chip. A bare CH341A outputs 3.3V and WILL DESTROY IT. The 1.8V adapter is MANDATORY.**

**Alternative:** Raspberry Pi + TXS0108E level shifter (~$3 if you have a Pi already).

**Pre-flash check:** Use a multimeter on pin 8 (VCC) of the W25Q16JWN while the laptop is powered. Expected: 1.8V (±0.15V). If 0V or 3.3V, you have a power rail problem, not just data corruption.

See `ch341a_flash.sh` for the complete flash procedure with safety checks.

## Not in This Repo

The following files are **not included** for legal/security reasons:
- `Razer.RTX3080.8192.210603.rom` — NVIDIA copyrighted firmware (get from [TechPowerUp VBIOS Collection](https://www.techpowerup.com/vgabios/))
- `nvflash` — NVIDIA proprietary binary (get from [TechPowerUp](https://www.techpowerup.com/download/nvidia-nvflash/))

## For LLMs / AI Assistants

If you're an AI helping debug this issue, read `STATUS.md` first. It has the full state of what's been tried and what hasn't. Key context:

- 29 software methods tried across 4 sessions — ALL failed due to FWSEC hardware verification
- The VBIOS chip is a standard Winbond 25-series 1.8V SPI NOR flash
- The GPU silicon is alive (responds to MMIO reads) but the falcon microcontroller is halted
- FWSEC (hardware security block on GPU die) blocks ALL software paths — this is definitively proven
- **Hardware SPI programmer (CH341A + 1.8V adapter) is the ONLY viable fix**

