# Razer Blade 15 Advanced 2021 — GPU VBIOS Recovery Troubleshooting Log

## System Info
- **Laptop:** Razer Blade 15 Advanced 2021 (RZ09-0409CEC3)
- **Serial:** REDACTED
- **BIOS:** Razer v1.06 (06/10/2021)
- **GPU:** NVIDIA GA104M RTX 3080 Laptop 8GB (10DE:249C — silicon fallback ID)
- **Subsystem:** 1A58:2018 (Razer)
- **Flash Chip:** Winbond W25Q16JWN (1.8V SOP8, 2MB)
- **Symptom:** Code 43, GPU-Z shows "Unknown" BIOS, 0 MHz clocks, 0 MB memory
- **VBIOS File:** Razer.RTX3080.8192.210603.rom (MD5: f458d34324bfd843bee5107006a0e70f)

---

## Session 1 — 2026-03-30 (Ubuntu Live USB)

### Diagnostic Results
- **GPU detected:** Yes, at PCI 01:00.0
- **Device ID:** 10DE:249C (silicon fallback — confirms corrupted VBIOS; should be 24DC)
- **PCIe Link:** 2.5 GT/s x8 (severely degraded; should be 16 GT/s x16)
- **PCI Command Register:** All disabled (I/O-, Mem-, BusMaster-)
- **Memory regions:** All disabled
- **Expansion ROM sysfs node:** Present and accessible (524KB)
- **BAR0 (MMIO):** Accessible — NV_PMC_BOOT_0 reads 0xB74000A1 (chip ID NV174 = GA104)
- **Kernel modules:** nouveau loaded (no nvidia driver)
- **No AER/hardware errors** related to GPU in dmesg
- **Full log:** `Logs and Attempts/gpu_diagnostic_20260330_205932.log`

### Attempt 1: nvflash Standard Flash
- **Command:** `./nvflash --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — "Adapter not accessible or supported EEPROM not found"
- **Error:** "Detecting GPU failed"
- nvflash sees the GPU in `--list` (10DE,249C,1A58,2018) but cannot communicate with the EEPROM
- `--protectoff` also fails: "A system restart might be required"

### Attempt 2: nvflash with Override Flags
- **Command:** `./nvflash -6 --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — same "EEPROM not found" error
- **Command:** `./nvflash --overridesub --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — same error
- **Command:** `./nvflash -6 --override --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — same error

### Attempt 3: Sysfs ROM Write
- **Path:** `/sys/bus/pci/devices/0000:01:00.0/rom`
- **Result:** FAILED — `cp: error writing '/sys/bus/pci/devices/0000:01:00.0/rom': File too large`
- ROM BAR is 512KB but VBIOS is 976KB
- Could not read current corrupted ROM either

### Attempt 4: PCI Command Register Enable + nvflash Retry
- Set PCI command register to 0x0007 (enable I/O, Memory, BusMaster) via `setpci`
- Confirmed readback: 0x0007
- **Result:** FAILED — nvflash still reports "EEPROM not found"
- The EEPROM accessibility is not a PCI enable issue

### Attempt 5: PCI Function Level Reset + nvflash Retry
- Issued FLR via `echo 1 > /sys/bus/pci/devices/0000:01:00.0/reset`
- Re-enabled PCI command register to 0x0007
- **Result:** FAILED — nvflash still reports "EEPROM not found"

### Attempt 6: Direct BAR0 MMIO Register Access
- Mapped BAR0 (16MB at 0x85000000) via `/sys/bus/pci/devices/0000:01:00.0/resource0`
- **NV_PMC_BOOT_0 (0x000):** 0xB74000A1 — GPU silicon responds, chip ID confirmed as GA104
- **PROM window (0x300000):** Contains corrupted data (first bytes: 6E 56 47 49 instead of 55 AA)
- **PROM window write test:** NOT writable — writes do not stick (read-only mapping)
- **PRAMIN window (0x700000):** Returns BAD0AC pattern — not accessible

### Attempt 7: SPI Controller Register Scan
- Scanned BAR0 register space looking for SPI flash controller hardware registers
- **Registers at 0xE100 (legacy SPI area):** Return 0xBADF5040 (bad falcon — uninitialized)
- **Registers at 0x10D000 (falcon SPI):** Return 0xBADF3000 (bad falcon)
- **Registers at 0x840000 (FSP area):** Falcon not running, DEAD5EC1/DEAD5EC2 signatures present
- **Registers at 0x110000:** Same falcon pattern, not initialized
- **PPCI shadow at 0x88000:** Active — mirrors PCI config space (expected)
- **Conclusion:** SPI controller is managed by falcon microcontrollers that require valid VBIOS firmware to boot. Without VBIOS, falcons can't load, so SPI controller is inaccessible.

### Attempt 8: PMC Engine Enable
- NV_PMC_ENABLE (0x200) reads 0x40000000 — only bit 30 (basic PCI) enabled
- Tried enabling additional engine bits (bit 12/PFLASH, bit 8, bit 4)
- Register rejects individual bit changes — reads back unchanged
- Setting 0xFFFFFFFF results in readback of 0x56000000 (only bits 30, 28, 26, 25 accepted)
- **SPI registers still return BADF after engine enable attempts**
- **Conclusion:** GPU only allows minimal engine set without valid VBIOS

### Summary — Session 1
All software flash methods exhausted. The core problem is a chicken-and-egg situation:
- The SPI flash controller is behind falcon microcontrollers
- Falcons need valid VBIOS firmware to boot
- VBIOS is on the SPI flash that the falcons control
- Therefore, the SPI flash cannot be written from software

**Next step: CH341A hardware SPI programmer (Method 3 from PLAN.md, ~95% success rate)**

Required hardware:
1. CH341A USB programmer ($5-15)
2. 1.8V adapter board (CRITICAL — chip is 1.8V only)
3. SOP8 test clip (Pomona 5250 or similar)

**Full flash log:** `Logs and Attempts/flash_20260330_205952.log`

---

## Session 1 (continued) — Additional Software Attempts

### Attempt 9: Bypass nvflash nomodeset Check
- nvflash spawns child process that reads `/proc/cmdline` and detects `nomodeset`
- Created fake cmdline without nomodeset: `mount --bind /tmp/fake_cmdline /proc/cmdline`
- **Result:** No change — the "system restart" error comes from GPU register state, not cmdline
- Strace confirmed nvflash successfully mmaps BAR0 at 0x85000000 via `/dev/mem`, reads registers, then fails

### Attempt 10: Force nouveau Driver Binding (modeset=2 headless)
- Unloaded nouveau (was loaded but NOT bound due to `nomodeset` boot parameter)
- Reloaded with `modprobe nouveau modeset=2` (headless mode)
- nouveau TRIED to probe the GPU, attempted BIOS from 5 sources in order:
  1. PRAMIN — "not enabled" (VRAM not initialized)
  2. PROM — ROM signature 0x56FE (corrupted, expects 0xAA55)
  3. ACPI — ROM signature 0x0000 (empty)
  4. PCIROM — same corrupted 0x56FE
  5. PLATFORM — nothing found
- **Result:** FAILED — `bios ctor failed: -22`, probe failed
- nouveau cannot initialize GPU without valid BIOS from any source

### Attempt 11: Install & Load NVIDIA Proprietary Driver (580.126.09)
- Installed `nvidia-driver-575-open` (resolved to 580.126.09)
- Driver loaded and **bound** to GPU at 0000:01:00.0
- **Result:** FAILED — driver also cannot find valid VBIOS:
  ```
  NVRM: kgspExtractVbiosFromRom_TU102: did not find valid ROM signature
  NVRM: kgspInitRm_IMPL: failed to extract VBIOS image from ROM: 0x25
  NVRM: RmInitAdapter: Cannot initialize GSP firmware RM
  NVRM: GPU 0000:01:00.0: RmInitAdapter failed! (0x62:0x25:2015)
  ```
- The open kernel module REQUIRES GSP firmware for Ampere, and GSP requires VBIOS
- Tried `NVreg_EnableGpuFirmware=0` — no effect, open module has hard GSP dependency
- When driver was loaded, nvflash gave different error: "unload NVIDIA kernel driver first" (it detected the driver)
- After unloading: back to original errors

### Attempt 12: PCIe Secondary Bus Reset
- Reset the PCIe bridge (00:01.0) using Secondary Bus Reset bit
- PCIe link still degraded at 2.5GT/s x8 after reset (should be 16GT/s x16)
- **Result:** nvflash gave new, DEFINITIVE error:
  ```
  Nvflash CPU side error Code:2
  Error Message: Falcon In HALT or STOP state, abort uCode command issuing process.
  ```
- **This confirms:** The GPU's falcon microcontroller (which manages SPI flash) is halted
- nvflash communicates with the falcon's microcode to access SPI EEPROM
- Falcon firmware is stored IN the VBIOS → chicken-and-egg problem confirmed

### Attempt 13: nvflash Internal Analysis (strace)
- nvflash tries to load `nvtool` kernel module (proprietary) — not available on live USB
- Falls back to direct `/dev/mem` BAR0 access
- Successfully maps BAR0 at physical 0x85000000 (16MB)
- Reads GPU registers, finds falcon in HALT state, gives up
- nvflash string analysis shows it does support SPI clock tuning (`--spiclkshmoo`) suggesting it accesses SPI through falcon microcode

### Summary — All Software Methods Exhausted
The fundamental problem is confirmed: **the GPU's falcon microcontroller is halted because its firmware (stored in the corrupted VBIOS on the SPI flash chip) cannot load**. Every software tool — nvflash, nouveau, NVIDIA proprietary driver — requires either a running falcon or a valid VBIOS to initialize, creating an unbreakable chicken-and-egg loop.

**Software flash is definitively impossible on this GPU in its current state.**

### Remaining Non-Hardware Option
- **Boot into Windows** — Windows UEFI boot process may initialize the GPU differently via ACPI/Option ROM. nvflash for Windows might have a different fallback path. Worth trying before purchasing hardware programmer.

### Hardware Fix Required
**CH341A USB SPI programmer** (Method 3 from PLAN.md, ~95% success rate):
1. CH341A USB programmer ($5-15)
2. 1.8V adapter board (CRITICAL — chip is 1.8V only, DO NOT USE 3.3V)
3. SOP8 test clip (Pomona 5250 or similar)
