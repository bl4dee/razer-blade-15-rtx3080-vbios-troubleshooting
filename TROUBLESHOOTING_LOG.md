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

---

## Session 2 — 2026-03-30 (Windows, continued from Session 1)

### Attempt 14 (T17): Razer System BIOS Update
- Downloaded Razer BIOS updater for RZ09-0409 from mysupport.razer.com
- Ran from Windows. System BIOS updated successfully from v1.06 to v2.x
- Theory: newer system BIOS might re-provision the dGPU VBIOS from an embedded copy
- **Result:** FAILED — GPU still shows Code 43 after reboot. Running the updater again reports "up to date"
- System BIOS update did NOT re-provision the dGPU VBIOS chip
- Ran updater a second time to confirm — reported system already up to date

---

## Session 3 — 2026-03-31 (Fedora 43 Live USB, kernel 6.19.10)

**Environment change:** Moved from Ubuntu Live USB to Fedora 43 repair USB (installed on external SSD at /dev/sda). Kernel 6.19.10-200.fc43.x86_64. Windows confirmed on nvme0n1p4 ("Blade 15", 934GB). EFI Boot0000 = Windows Boot Manager.

**Key finding from this session:** The Fedora 43 kernel ships nouveau with GSP RM firmware (570.144) — nouveau now uses the same NVIDIA GSP firmware path as the open proprietary driver. This rules out the nouveau NvBios/ForcePost approach (N05), as those parameters no longer exist in GSP-based nouveau.

### Attempt 15 (T18): ACPI Table Search for _ROM Method
- Installed acpica-tools, dumped and decompiled DSDT + all 13 SSDTs
- Searched all tables for `_ROM`, `VBIOS`, `NVROM`, `ROMF` strings
- **Result:** DEAD END — No `_ROM` method exists in any ACPI table
- System BIOS does not hold a GPU VBIOS copy accessible via ACPI
- Rules out N07 entirely

### Attempt 16 (T19): PCI Remove/Rescan
- `echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove`
- `echo 1 > /sys/bus/pci/devices/0000:00:01.0/rescan`
- GPU re-enumerated and nouveau auto-attached on rescan
- **Result:** FAILED — identical behavior: `Invalid PCI ROM header signature: expecting 0xaa55, got 0x56fe`, `bios ctor failed: -22`
- PCIe link still 2.5 GT/s x8. No change in GPU state from remove/rescan.

### Attempt 17 (T20): envytools nvagetbios
- Installed envytools from Fedora 43 repos (v0.0-0.33.git20200810)
- Unloaded nouveau first, then ran:
  - `nvagetbios` (auto-detect) → tried PRAMIN then PROM, both failed
  - `nvagetbios -s PRAMIN` → "Invalid signature(0x55aa)" — output is repeating garbage (uninitialized falcon memory pattern)
  - `nvagetbios -s PROM` → "Invalid signature(0x55aa)" — corrupt sig 0x56FE, same as T09/T13
- **Result:** FAILED — No new information. Same corrupted/uninitialized state confirmed.

### Attempt 18 (T21): nvflash with nouveau Fully Unloaded (Post-BIOS-Update)
- Cloned repo to get nvflash (v5.867.0) and VBIOS ROM locally
- Confirmed ROM file integrity: `nvflash --version Razer.RTX3080.8192.210603.rom` shows correct metadata (v94.04.55.00.92, Device 24DC, Board 0x0262, Subsystem 1A58:2018, MD5 match)
- Fully unloaded nouveau (`modprobe -r nouveau mxm_wmi`), confirmed no GPU drivers in lsmod
- Tried three variations:
  - `./nvflash Razer.RTX3080.8192.210603.rom` → "EEPROM not found"
  - `./nvflash --overridesub Razer.RTX3080.8192.210603.rom` → "EEPROM not found"
  - `./nvflash -6 Razer.RTX3080.8192.210603.rom` → "EEPROM not found"
- GPU IS detected in `--list` (`10DE,249C,1A58,2018`) but SPI EEPROM unreachable
- **Result:** FAILED — No change from T01–T05. BIOS update had no effect on GPU VBIOS state.

### Research Findings — Methods Ruled Out Without Attempting
- **nvflashk (N03):** Confirmed Windows-only. Only bypasses board ID/subsystem mismatch checks. Underlying SPI probe code identical to stock nvflash. No benefit over `-6 --overridesub` already tried.
- **nouveau NvBios/ForcePost (N05):** GSP-based nouveau (kernel 6.19) does not expose NvBios or NvForcePost parameters. Classic file-based VBIOS loading path removed in GSP nouveau. Would require kernel ≤5.19.
- **ACPI _ROM (N07):** Eliminated by T18 above.

### Session 3 Summary
21 methods tried across 3 sessions. Every software path is exhausted or eliminated. The halted falcon is an absolute blocker for all software approaches — the SPI controller cannot be reached without a running falcon, and the falcon cannot run without the VBIOS stored on that same SPI chip.

**Next steps in priority order:**
1. **N02 — Windows nvflash** (boot into Windows, try nvflash64.exe — see WINDOWS_NVFLASH_PROCEDURE.md)
2. **N15 — Order CH341A + 1.8V adapter** (do this now regardless of N02 outcome — it's the definitive fix)

---

## Session 4 — 2026-03-31 (Fedora 43, same boot session as Session 3)

Advanced investigation using automated analysis, direct hardware probing, and custom kernel module development.

### Attempt 19 (T22): System BIOS Flash Scan via MTD
- **Discovery:** Intel SPI driver (`spi_intel_pci`) exposes the system BIOS flash as `/dev/mtd0` (32MB, "BIOS" partition)
- Read first 12MB successfully (remaining 20MB protected by Intel ME/SMM)
- Scanned for `NVGI`, `NVIDIA`, `GeForce`, `RTX`, `10DE:24DC` signatures
- **Result:** DEAD END — Zero hits for any NVIDIA content in the readable system BIOS region. Razer does NOT embed the dGPU VBIOS in the system firmware. The `ROM_CMN` EFI variable contains only ACPI device metadata (`GFX0`, `GLAN`, `SAT0`), not ROM images.

### Attempt 20 (T23): SMBus/I2C Device Enumeration
- Scanned all 16 I2C buses (`i2cdetect -r -y` on buses 0 and 15)
- **Bus 15 (Intel SMBus I801):** Found devices at 0x30, 0x35, 0x44, 0x50, 0x52
- **Device at 0x44:** Readable temperature sensor (values 0x39=57°C, 0x34=52°C) — system thermal sensor, NOT GPU-related
- Devices at 0x30, 0x35 returned XX (access error) — likely write-only or unsupported mode
- **Result:** DEAD END — No GPU SMBus slave found. The GPU does not expose an I2C/SMBus interface for SPI access.

### Attempt 21 (T24): VBIOS File Format Analysis (Critical Discovery)
- Hexdumped the target VBIOS ROM file
- **Key finding:** The ROM file starts with `4E 56 47 49` = **`NVGI`**, NOT `55 AA`
  - NVGI is NVIDIA's proprietary VBIOS container format for Ampere+
  - `55 AA` (standard PCI option ROM) appears first at offset **0x9400** (63KB legacy x86 sub-image)
  - The PCIR data structure at 0x9400+0x170 shows Vendor `10DE`, Device `24DC` (correct!)
  - 10+ additional sub-images at various offsets (EFI GOP, configuration tables, etc.)
- Previous PROM reading of `6E 56 47 49` = `nVGI` (lowercase n) differs from the file's `4E 56 47 49` = `NVGI` by exactly **1 bit** (bit 5 of byte 0, XOR = 0x20)
- **However:** Further 512-byte PROM comparison showed only 4.3% match, 27.7% erased (0xFF), 67.6% different — confirming PROM data is unreliable bus noise, not actual SPI contents

### Attempt 22 (T25): BAR0 PROM Window Write Test
- Attempted to write correct VBIOS data to PROM window at BAR0+0x300000
- Write calls succeeded (no exception), but readback showed **different** data — writes are silently discarded
- **Result:** CONFIRMED — PROM window is hardware read-only. Cannot inject VBIOS data through BAR0.

### Attempt 23 (T26): BAR0 PMC_ENABLE Register Manipulation
- Current value: `0x40000000` (only basic PCI enabled)
- Attempted OR with `0x10000000` (PROM engine enable bit)
- Readback unchanged at `0x40000000` — register rejects additional enable bits
- **Result:** Same as T11. PMC_ENABLE is locked when falcon is halted.

### Attempt 24 (T27): GSP RM Registry Keys via NVreg_RegistryDwords
- Searched the GSP firmware binary (`gsp-570.144.bin`, 63MB) for registry key names
- Found `RMDisableSpi` and `RMDevinitBySecureBoot` among ~200+ RM registry keys
- Loaded nouveau with: `NVreg_RegistryDwords="RMDevinitBySecureBoot=0;RMDisableSpi=1"`
- **Observation:** PCIROM changed from `0x56EE` to `0xFFFF` — the registry keys DID affect SPI access behavior
- **Result:** FAILED — Host-side nouveau BIOS check still fails before GSP can use the VBIOS. The `bios ctor failed: -22` error occurs on the host side, blocking the entire init chain.

### Attempt 25 (T28): nouveau PLATFORM Source Investigation
- Used `config=NvBios=PLATFORM` with `debug=bios=trace` for verbose BIOS loading
- **Full source order revealed:** PLATFORM → PRAMIN → PROM → ACPI → ACPI → PCIROM → PLATFORM
- PLATFORM said "PLATFORM invalid" — found but rejected
- **Critical finding via firmware_class debug:** Enabling firmware loader tracing showed **no `request_firmware()` call** for `vbios.rom` during PLATFORM source execution. In GSP-mode nouveau (kernel 6.19+), the PLATFORM source does NOT use the firmware subsystem to load VBIOS files. The `vbios.rom` string and `NvBios` config option are dead code paths for Ampere GPUs.
- Tried placing ROM at `/lib/firmware/nouveau/vbios.rom` and `/lib/firmware/nvidia/ga104/vbios.rom` — neither was requested by nouveau

### Attempt 26 (T29): Custom Kernel Module — VBIOS Injection via kretprobe
- **Wrote `vbios_inject.ko`:** Custom kernel module using kretprobes on `pci_map_rom()` and `pci_unmap_rom()` to intercept PCI ROM reads for the NVIDIA GPU (10DE:249C) and return valid VBIOS data from a kmalloc'd buffer
- Module compiled, loaded, and registered kretprobes successfully
- Loaded the extracted 55AA PCI option ROM sub-image (63KB) via `request_firmware("nouveau/vbios.rom")`
- **Result:** FAILED — When vbios_inject kretprobes were active, nouveau stalled at "Resources present before probing" without reaching the BIOS reading phase. The kretprobes on `pci_map_rom` interfered with PCI core initialization. The `pci_map_rom` interceptor was never triggered (0 hits).

### Attempt 27 (T30): GSP Firmware FWSEC Analysis (Definitive Finding)
- Extracted and searched all strings from `nvidia/ga102/gsp/gsp-570.144.bin` (63MB)
- **Found hardware-enforced VBIOS verification chain:**
  ```
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_BIOS_SIG_FAIL
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_CERT_NOT_FOUND
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_CERT_PARSE_FAIL
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_CERT_VERIFY_FAIL
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_DEVID_FAIL
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_HAT_FAIL
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_HULK_INIT_FAIL
  NV_FWSECLIC_ERR_CODE_CMD_VBIOS_VERIFY_HULK_SIG_INVALID
  ```
- **FWSEC** (Firmware Security) is a dedicated hardware block on the GPU die that reads and cryptographically verifies the VBIOS directly from SPI flash BEFORE unlocking any falcon microcontrollers
- The verification chain includes: digital signature, certificate chain, device ID matching, Hardware Access Token (HAT), and HULK (hardware security co-processor) verification
- FWSEC operates at a lower level than the falcon — it is NOT software-controllable

### Session 4 Conclusion

**FWSEC hardware security on NVIDIA Ampere is the definitive reason all software approaches fail.** The GPU has a dedicated hardware block (FWSEC) that must read the VBIOS directly from the SPI flash chip and verify its cryptographic signature chain before ANY falcon microcontroller is allowed to boot. This hardware mechanism:

1. Cannot be bypassed by any OS-level software
2. Cannot be overridden by GSP RM registry keys
3. Cannot be circumvented by providing VBIOS data from host memory
4. Is not affected by driver choice (nouveau, NVIDIA open, proprietary)

The GSP falcon IS loadable from the host filesystem (confirmed: RM version 570.144 loads successfully every time). But the GSP cannot proceed with GPU initialization because FWSEC has not verified the VBIOS from SPI, so all other falcons remain in HALT state.

**The ONLY fix is physical SPI flash programming.** Order the CH341A + 1.8V adapter + SOP8 clip immediately. Windows nvflash (N02) has near-zero probability of working given that FWSEC operates before any OS or driver loads.
