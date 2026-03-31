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

## Repository Structure

```
.
├── README.md                    This file
├── STATUS.md                    Master tracking: every method tried/untried
├── TROUBLESHOOTING_LOG.md       Detailed narrative log (4 sessions, 30+ methods)
├── docs/
│   ├── DIAGRAM.md               Visual diagrams of the problem and architecture
│   ├── PLAN.md                  Original attack plan
│   └── WINDOWS_NVFLASH_PROCEDURE.md
├── scripts/
│   ├── diagnose.sh              GPU diagnostic (lspci, dmesg, dmidecode, sysfs)
│   ├── flash.sh                 Automated software flash pipeline
│   └── ch341a_flash.sh          Interactive hardware SPI flash with safety checks
├── patches/                     Nouveau kernel module patches (8 total)
│   ├── README.md                Patch descriptions and test results
│   ├── image.patch              Accept NVGI LE signature
│   ├── shadow.patch             Skip PCIR validation for firmware VBIOS
│   ├── base.patch               Skip preinit + non-fatal ctor/init/intr
│   ├── gsp.patch                Survive FWSEC sb_ctor failure
│   └── fwsec.patch              Survive all FWSEC init failures
├── logs/                        Raw diagnostic output
│   ├── gpu_diagnostic_*.log     Hardware diagnostic captures
│   ├── flash_*.log              Flash attempt logs
│   └── diagnostic_attempt.log   MODS/MATS diagnostic attempt
├── nvflash                      NVIDIA flash tool binary (v5.867.0)
└── Razer.RTX3080.8192.210603.rom  Target VBIOS image (976KB)
```

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
9. **FWSEC hardware security** on the GPU die cryptographically verifies VBIOS from SPI before unlocking ANY falcon — this is the definitive reason all 30 software methods fail
10. **Falcon IMEM/DMEM direct write** (hexkyz technique) — PMU, GSP, SEC2 falcon registers are readable via BAR0 but ALL writes are hardware-locked by FWSEC

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

## Hardware Fix: Detailed Procedures

### Option 1: CH341A + 1.8V Adapter (recommended, ~$20)

The simplest and most reliable approach. The programmer talks directly to the SPI flash chip over its data pins, completely bypassing the GPU.

```
┌──────────┐     USB      ┌──────────┐    SPI bus    ┌─────────────┐
│  Your PC │ ◄══════════► │  CH341A  │ ◄═══════════► │ W25Q16JWN   │
│ (flashrom│              │  + 1.8V  │  MOSI/MISO    │ SPI chip on │
│  command)│              │  adapter │  CLK/CS#      │ GPU PCB     │
└──────────┘              └──────────┘               └─────────────┘
```

**What to buy:**
| Part | Price | Notes |
|---|---|---|
| CH341A USB programmer | ~$8-12 | The green PCB board, widely available |
| 1.8V adapter board | ~$5-8 | Search "CH341A 1.8V adapter" — small daughter board |
| SOIC8/SOP8 test clip | ~$5-8 | Spring-loaded clip that grabs the chip without soldering |

**The procedure:**
1. Power off laptop, open bottom panel
2. Locate the W25Q16JWN SOP8 chip near the GPU (8 tiny pins)
3. Attach the SOP8 clip — match pin 1 (dot on chip) to pin 1 on clip
4. Connect clip → 1.8V adapter → CH341A → USB to another computer
5. Run flashrom:
```bash
# Detect the chip
flashrom -p ch341a_spi
# Should show: Winbond W25Q16.W

# Read current contents (backup, do this TWICE)
flashrom -p ch341a_spi -r backup1.bin
flashrom -p ch341a_spi -r backup2.bin
md5sum backup1.bin backup2.bin   # MUST match — retry clip if different

# Pad VBIOS to chip size (2MB) and write
dd if=Razer.RTX3080.8192.210603.rom of=padded.bin bs=2M conv=sync
flashrom -p ch341a_spi -w padded.bin

# Verify
flashrom -p ch341a_spi -v padded.bin
```

**Voltage warning:** The W25Q16JWN operates at 1.65V-1.95V. A bare CH341A outputs 3.3V. **Connecting without the 1.8V adapter WILL permanently destroy the SPI chip.** Always use the adapter.

### Option 2: Raspberry Pi + Level Shifter (~$3 if you have a Pi)

A Raspberry Pi can act as a SPI programmer using its GPIO pins.

```
┌──────────┐    GPIO/SPI   ┌───────────┐   1.8V SPI   ┌─────────────┐
│  Raspi   │ ◄═══════════► │ TXS0108E  │ ◄══════════► │ W25Q16JWN   │
│  3.3V    │               │ level     │              │ SPI chip    │
│  GPIO    │               │ shifter   │              │ 1.8V        │
└──────────┘               └───────────┘              └─────────────┘
```

**Setup:**
1. Enable SPI on the Pi: `sudo raspi-config` → Interface Options → SPI
2. Wire GPIO to TXS0108E high side (3.3V), TXS0108E low side to SOP8 clip (1.8V)
3. Power the TXS0108E VA from Pi 3.3V, VB from the chip's own 1.8V rail (pin 8)
4. Run: `flashrom -p linux_spi:dev=/dev/spidev0.0,spispeed=512`

### Option 3: SPI Bus Proxy (research/advanced, ~$10)

Instead of writing to the chip, intercept the GPU's SPI reads and feed it correct data during boot. No permanent modification needed.

```
Normal:     GPU ◄──── SPI Flash (corrupted) ──► FWSEC FAILS

With proxy: GPU ◄──── Pi Pico ◄──── SPI Flash
                        │
                 Monitors SPI bus via PIO
                 When GPU reads VBIOS addresses:
                   returns correct data from local flash
                 FWSEC verifies proxy data ──► GPU UNLOCKS
                 Then use nvflash to write real VBIOS to chip
```

**Equipment:** Raspberry Pi Pico ($4) + TXS0108E ($2) + SOP8 clip ($5)

**Challenge:** GPU SPI clock runs at 25-50MHz. Pico's PIO hardware (programmable I/O, independent of CPU) runs at 125MHz — gives 2-5 clock cycles to respond. Tight but potentially feasible. Requires custom PIO firmware to intercept and respond to SPI transactions in real-time.

**Status:** Theoretical — nobody has publicly demonstrated this on NVIDIA FWSEC. Would be novel research if built.

### Pre-Flash Diagnostic: Check the 1.8V Power Rail

Before assuming data corruption, verify the SPI chip is actually powered:

```
Multimeter on DC voltage mode:
  Red probe → Pin 8 (VCC) of W25Q16JWN
  Black probe → Ground (any ground pad on PCB)

Expected: 1.8V (±0.15V) with laptop powered on

If 0V:     Power rail is dead — blown fuse, bad LDO, or broken trace
If 3.3V:   Wrong voltage rail connected — chip may already be damaged
If 1.8V:   Power is good — data corruption confirmed, proceed with flash
```

### Post-Flash: Memory Diagnostics

After flashing the VBIOS, if you see artifacts or crashes, test GDDR6 with MODS/MATS:

```bash
# Boot from MATS USB (version 455.120_3080 for RTX 3080)
# Initialize GPU (if testing as secondary card):
./mods gputest.js -skip_rm_state_init -mfg

# Run memory test:
./mats -n 1 -e 50     # test 50MB on card index 1

# Full manufacturing test:
./mods gputest.js -test 3 -test 19 -matsinfo
#   test 3  = MatsTest (memory coupling faults)
#   test 19 = FastMatsTest (HW-accelerated)
```

MATS identifies which specific GDDR6 chip is faulty by memory subpartition. If a chip is bad, it needs reballing or replacement — a separate board-level repair.

## For LLMs / AI Assistants

If you're an AI helping debug this issue, read `STATUS.md` first. It has the full state of what's been tried and what hasn't. Key context:

- 30+ software methods tried across 4 sessions — ALL failed due to FWSEC hardware verification
- The VBIOS chip is a standard Winbond 25-series 1.8V SPI NOR flash
- The GPU silicon is alive (responds to MMIO reads) but the falcon microcontroller is halted
- FWSEC (hardware security block on GPU die) blocks ALL software paths — this is definitively proven
- **Hardware SPI programmer (CH341A + 1.8V adapter) is the ONLY viable fix**
- See `docs/DIAGRAM.md` for comprehensive visual explanation of the architecture

