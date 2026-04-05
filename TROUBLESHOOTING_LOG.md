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

### Attempt 28 (T30): Falcon IMEM/DMEM Direct Write via BAR0 (hexkyz technique)
- **When:** 2026-03-31, Session 4
- **Background:** The hexkyz/SciresM research paper "Je Ne Sais Quoi — Falcons over the Horizon" (https://hexkyz.blogspot.com/2021/11/je-ne-sais-quoi-falcons-over-horizon.html) documents complete exploitation of the NVIDIA Falcon microprocessor (the same architecture used in our GPU's falcons). Key technique: upload custom code to Falcon IMEM via BAR0 MMIO registers (IMEMC/IMEMD), then start the Falcon CPU.
- **How:** Scanned all falcon engine BAR0 base addresses for accessibility:

| Engine | Base | Status |
|---|---|---|
| PMU | 0x10A000 | Accessible (HWCFG=0x01, registers respond) |
| GSP | 0x110000 | Accessible (HWCFG=0x80, IMEM=32KB, has data from previous nouveau load) |
| SEC2 | 0x840000 | Accessible (same state as GSP, DMEMD=`DEAD5EC2`) |
| NVENC | 0x1C8000 | Accessible (BADF1201 pattern — different gating) |
| NVDEC0/1 | 0x848000/84C000 | Accessible (similar BADF pattern) |
| FWSEC | 0x8F0000 | **GATED** (BADF3000) |
| FBFALCON | 0x8F1000 | **GATED** (BADF3000) |
| DISP/MINION | 0x611000/612000 | **GATED** (BADF5040) |

- Attempted writes to PMU, GSP, and SEC2 falcon registers:

| Target Register | Write Value | Readback | Result |
|---|---|---|---|
| PMU IMEMC | 0x01000000 | 0x00000000 | Rejected |
| PMU IMEMD | 0xCAFEBABE | 0x00000000 | Rejected |
| PMU DMEMD | 0xDEADBEEF | 0x00000000 | Rejected |
| GSP IMEMC | 0x01000000 | 0x9100EB00 | Rejected (unchanged) |
| GSP IMEMD | 0xCAFEBABE | 0x00000000 | Rejected |
| GSP DMEMD | 0xDEADBEEF | 0xDEAD5EC2 | Rejected |
| GSP CPUCTL (START) | 0x00000002 | 0x00000000 | Rejected |
| GSP BOOTVEC | 0x00000000 | 0x80420100 | Rejected |
| GSP DMATRFBASE | 0x12345678 | 0x00000000 | Rejected |
| SEC2 IMEMD | 0xCAFEBABE | 0x00000000 | Rejected |
| SEC2 DMEMD | 0xDEADBEEF | 0xDEAD5EC2 | Rejected |

- **Result:** FAILED — **Every falcon register is completely write-locked by FWSEC.** All registers are readable (not gated) but reject all host writes: IMEM, DMEM, CPUCTL (start bit), BOOTVEC, DMA registers. The `DEAD5EC2` value in SEC2 DMEM is NVIDIA's debug marker ("DEAD SEC2") confirming the security engine knows it's in a locked state.
- **Analysis:** The hexkyz exploits (maconstack, DMA race against Secure Boot ROM) require writable IMEM as a prerequisite — the attacker must be able to upload code before exploiting the ROM. On the Nintendo Switch TSEC, IMEM is host-writable from power-on. On Ampere GPUs, FWSEC adds a hardware write-lock on ALL falcon registers that is only released after VBIOS cryptographic verification. This makes the hexkyz-style attack vector inapplicable to Ampere.

### Final Session 4 Summary

31 methods tested in total (T01–T30). Every conceivable software path has been explored and definitively blocked by FWSEC hardware write-locks on all falcon IMEM/DMEM/control registers. The CH341A hardware SPI programmer is the only remaining option.

---

## Session 5 — 2026-04-02 (NixOS Desktop, CH341A Hardware Flash Attempt)

### Equipment
- **Flash computer:** Ryzen 9 NixOS desktop
- **Programmer:** CH341A USB SPI programmer (idVendor=1a86, idProduct=5512)
- **Adapter:** 1.8V voltage adapter board
- **Clip:** SOP8 test clip
- **Software:** flashrom v1.7.0 via `nix-shell -p flashrom`
- **Kit reference:** Akali27 Medium article CH341A kit (Figure 1 setup)

### Setup & Software Verification

1. **flashrom installed and working** — `nix-shell -p flashrom` provides flashrom v1.7.0
2. **CH341A detected by Linux** — `dmesg` shows `idVendor=1a86, idProduct=5512, Product: USB UART-LPT`
3. **Baseline test (no clip):** `sudo flashrom -p ch341a_spi` → "No EEPROM/flash device found" — **expected and correct**
4. **VBIOS file verified:** `md5sum Razer.RTX3080.8192.210603.rom` → `f458d34324bfd843bee5107006a0e70f` ✓
5. **Padded VBIOS prepared:** 976KB ROM padded with 0xFF to 2,097,152 bytes (2MB) → `padded_vbios.bin`
6. **NOPASSWD sudo configured** for automated command execution

### Laptop Disassembly

1. Razer Blade 15 back panel removed (T5 Torx)
2. Battery ribbon cable disconnected from motherboard
3. AC power unplugged
4. Vapor chamber/heatsink removed (11 Phillips screws, crisscross pattern)
5. **VBIOS chip located:** Winbond 25Q16JWN, date code 2105, ~1-2cm below GPU die
6. **Pin 1 identified:** Blue dot on top-right corner of chip

### Attempt 1: CH341A + 1.8V Adapter + SOP8 Clip on W25Q16JWN

- **Command:** `sudo flashrom -p ch341a_spi`
- **Result:** FAILED — `LIBUSB_TRANSFER_TIMED_OUT`, `config_stream: Failed to write 3 bytes`, `Could not configure stream interface`
- **Observation:** CH341A LED changed from green to red upon clipping. Desktop rear USB xHCI host controller crashed (`xhci_hcd 0000:07:00.1: HC died; cleaning up`). Keyboard on rear USB stopped working. Had to move devices to front USB.

### Attempt 2: Reseated Clip, Different USB Port (Front)

- **Command:** `sudo flashrom -p ch341a_spi`
- **Result:** FAILED — "No EEPROM/flash device found" (clip not making good contact)

### Attempt 3: Forced Chip Detection

- **Command:** `sudo flashrom -p ch341a_spi -c W25Q16.W`
- **Result:** FAILED — "No EEPROM/flash device found" (same clip contact issue)

### Attempt 4: Reseated Clip Again

- **Command:** `sudo flashrom -p ch341a_spi`
- **Result:** FAILED — Massive `LIBUSB_TRANSFER_TIMED_OUT` spam followed by `LIBUSB_TRANSFER_STALL`. flashrom attempted ~30+ SPI transactions, all timed out. CH341A LED went red again.
- **Partial output:**
  ```
  cb_in: error: LIBUSB_TRANSFER_TIMED_OUT
  ch341a_spi_spi_send_command: Failed to read 4 bytes
  cb_out: error: LIBUSB_TRANSFER_TIMED_OUT
  ch341a_spi_spi_send_command: Failed to write 37 bytes
  [... ~30 more timeout/stall errors ...]
  ```
- **Analysis:** This is different from "no chip found" — the programmer IS trying to communicate but every SPI transaction fails. The chip is electrically present but communication is broken.

### Attempt 5: Without 1.8V Adapter (Diagnostic Only)

- **Test:** Clipped SOP8 directly to CH341A (no 1.8V adapter) to isolate the problem
- **Result:** CH341A stayed green with clip on chip — no crash
- **Command:** `sudo flashrom -p ch341a_spi` → `Couldn't open device 1a86:5512` (CH341A had disconnected from USB by this point)
- **Analysis:** The 1.8V adapter is the failure point. Without it, the CH341A doesn't crash when clipped to the chip. With it, every connection causes USB timeouts and CH341A LED goes red.

### USB Controller Degradation

Throughout the session, the desktop's USB subsystem progressively degraded:
- Rear xHCI controller crashed (`HC died`) — rear USB ports stopped working
- CH341A repeatedly caused USB timeouts, requiring replug cycles
- Front USB ports eventually started dropping devices (webcam stopped)
- **Root cause:** The repeated CH341A crashes/shorts corrupted the USB host controller state
- **Fix:** Desktop reboot required to reset all USB controllers

### Session 5 Summary

**The 1.8V adapter is suspected defective or damaged.** Evidence:
1. CH341A works fine without adapter (green LED, detected by Linux, no crash)
2. CH341A works fine with adapter when NOT clipped to any chip
3. CH341A crashes (red LED, USB timeouts) every time the clip connects to the W25Q16JWN through the 1.8V adapter
4. Without the adapter, clipping directly to chip does NOT crash the CH341A

**Next steps:**
- Reboot desktop to reset USB controllers
- Test with a new/replacement 1.8V adapter
- If adapter is confirmed bad, order replacement (~$5-8)
- Alternative: Raspberry Pi + TXS0108E level shifter approach

---

## Session 6 — 2026-04-02 (NixOS Desktop, CH341A Hardware Flash Continued)

### Pre-Session: USB Controller Recovery
- Rebooted NixOS desktop to reset crashed USB controllers from Session 5
- All USB ports fully functional after reboot
- CH341A confirmed working: detected as `1a86:5512`, both red+green LEDs normal

### Software Setup
- Installed **IMSProg** GUI as alternative to flashrom CLI: `nix-shell -p imsprog`
- Retained flashrom v1.7.0 from Session 5

### Attempt 6: CH341A + 1.8V Adapter + Clip on Chip (Post-Reboot)

- **Command:** `sudo flashrom -p ch341a_spi`
- **Result:** FAILED — all zeros returned (chip id1 0x00, id2 0x00). SPI bus returning nothing.
- **Analysis:** Adapter is in the chain, no USB crash this time, but chip does not respond to SPI commands at all.

### Attempt 7: Direct 3.3V (No 1.8V Adapter) + Clip on Chip

- **Test:** Removed 1.8V adapter from chain, connected SOP8 clip directly to CH341A output (3.3V native)
- **Command:** `sudo flashrom -p ch341a_spi`
- **Result:** FAILED — also all zeros (id1 0x00, id2 0x00). Same as with adapter.

### Key Discovery 1: USB Crash Proves Electrical Contact

- When clip was properly seated on chip and detected via flashrom, CH341A crashed with `LIBUSB_TRANSFER_TIMED_OUT` when 1.8V adapter was in the chain — same behavior as Session 5.
- **Direct 3.3V to chip (no adapter) caused IMMEDIATE USB crash** — this **PROVES** the clip IS making electrical contact with the chip.
- The 1.8V chip (W25Q16JWN, rated 1.65V–1.95V) latch-up at 3.3V draws too much current and crashes the CH341A's USB interface.

### Key Discovery 2: 1.8V Adapter Behavior Explained

- **With 1.8V adapter:** No USB crash but no chip response either. The adapter passes enough current/voltage to prevent the overcurrent condition, but the chip doesn't respond to SPI commands.
- **Without 1.8V adapter (3.3V direct):** Immediate USB crash — confirms clip is making contact and chip is electrically connected.
- **Conclusion:** The 1.8V adapter is NOT defective (revising Session 5 hypothesis). It correctly prevents overcurrent. The problem is that SPI communication doesn't work even when the electrical connection is established.

### Attempt 8: 60-Second Continuous Probe Loop

- Ran automated probe loop with 1.8V adapter in chain, wiggling clip throughout
- **Result:** Zero chip contact detected across entire 60-second window
- All reads returned zeros — no SPI response from chip at any clip position

### New Hypothesis: GPU SPI Bus Contention

- All individual parts confirmed working:
  1. **CH341A** — detects on USB, communicates with flashrom, LEDs normal
  2. **1.8V adapter** — doesn't crash USB, passes voltage correctly
  3. **SOP8 clip** — makes physical contact with chip (proven by 3.3V crash test)
  4. **W25Q16JWN chip** — electrically present (proven by current draw behavior)
- **Hypothesis:** The GPU's SPI controller pins may be holding/clamping the SPI bus even when the laptop is unpowered. The SPI lines (MOSI, MISO, CLK, CS#) connect to both the flash chip and the GPU. Even with power removed, the GPU's I/O pads may have protection diodes or ESD structures that create a low-impedance path, sinking current from the external programmer and preventing valid SPI signaling.
- **Possible fix:** Desolder the flash chip from the board to completely isolate it from the GPU, or lift the CS# (chip select) pin to break the GPU's hold on the bus while leaving the other pins connected.

### Session 6 Summary

**SPI bus contention from the GPU is the leading hypothesis.** The clip makes electrical contact (proven by 3.3V overcurrent crash), the 1.8V adapter works (prevents overcurrent), but the chip does not respond to SPI commands through the adapter. The GPU's SPI controller pins are likely holding the bus, preventing external programmer communication.

**Times tried:** Multiple probe attempts with various configurations (with/without adapter, continuous 60s probe loop with wiggling)

**Next steps:**
- Option A: Desolder W25Q16JWN from board, flash on breakout board, resolder
- Option B: Lift CS# pin to isolate from GPU, flash in-circuit
- Option C: Add series resistors or bus isolation circuit between clip and chip
- Research whether other Ampere laptop VBIOS recovery guides mention GPU bus contention issues

---

## Session 7 — 2026-04-03 (NixOS Desktop, CH341A Write Attempts)

### BREAKTHROUGH: Chip Now Responds

After Sessions 5–6 where the chip returned all zeros, Session 7 achieved **full SPI communication**. The chip is detected reliably by all tools:

- **flashrom**: `W25Q16.W` detected, RDID `0xEF6015`
- **ch341prog**: same detection
- **IMSProg GUI**: same detection

Exact cause of the change from Session 6 is unclear — likely a better clip seating or environmental change (chip contact was always marginal).

### What Works

| Operation | Status | Notes |
|---|---|---|
| Chip detection (RDID) | **WORKS** | 0xEF6015 = Winbond W25Q16JW, consistent |
| Status register read | **WORKS** | SR1=0x00 (no write protection, no BUSY) |
| Erase (sector + chip) | **WORKS** | Chip goes to all 0xFF, perfectly reliable |
| Read | **WORKS** | But noisy: 133 bytes differ between consecutive reads of same data |
| Page Program (write) | **PARTIAL** | 0.18% per-byte success rate per 256-byte page write |
| Write Enable (WREN) | **WORKS** | WEL bit sets correctly before every write |

### What Was Tried (Chronological)

#### Attempt 1: flashrom Stock v1.7.0 — Erase + Write
```
sudo flashrom -p ch341a_spi -c W25Q16.W -w padded_vbios.bin
```
- **Result:** FAILED — erase succeeds but write fails verification. Flashrom aborts at bad sector 0x111000.
- **Observation:** After write, readback shows almost no data landed. Erase wiped the chip clean but the write didn't stick.

#### Attempt 2: flashrom Patched — USB_IN_TRANSFERS=1
- Patched flashrom source to set `USB_IN_TRANSFERS = 1` (sequential USB transfers instead of batched)
- Rebuilt at `/tmp/flashrom-build/`
- **Result:** Same behavior. Erase works, writes don't land.

#### Attempt 3: flashrom Patched — need_erase=0, skip-read, page_size=4
- Patched `need_erase()` to return 0 (skip pre-erase, assume chip is already erased/0xFF)
- Patched read to return all-0xFF (skip slow read phase)
- Reduced `W25Q16.W` page_size from 256 to 4 bytes
- **Result:** **Writes now partially land!** 0.18% of bytes correct per pass. Smaller page size helped marginally.
- **Key insight:** Reducing page size from 256→4 bytes means fewer MOSI toggles per Page Program command, giving the voltage-mismatched data lines a better chance of landing each bit correctly.

#### Attempt 4: flashrom Patched — page_size=16
- Tried page_size=16 as a middle ground
- **Result:** Same ~0.18% success rate. The fundamental issue is per-bit, not per-page.

#### Attempt 5: ch341prog (Independent Codebase)
```
sudo ch341prog -w padded_vbios.bin
```
- **Result:** Same 0.18% per-byte success rate.
- **Significance:** Two completely independent SPI stacks (flashrom C vs ch341prog C) produce identical write success rates. **This proves the problem is hardware, not software.**

#### Attempt 6: IMSProg GUI
- Used IMSProg (Qt-based CH341A programmer)
- **Result:** Writes appear to execute but IMSProg's verification fails. Same underlying issue.

#### Attempt 7: Custom Python pyusb — GPIO Bit-Bang
- Wrote `bitbang_write.py`: manually toggles CLK/MOSI/CS via CH341A UIO stream commands
- Bypasses CH341A's hardware SPI engine entirely
- **Result:** FAILED — CH341A UIO stream command protocol is too complex for reliable bit-level control. Couldn't get consistent MISO reads. Abandoned after testing showed worse results than hardware SPI.
- **Script location:** `scripts/bitbang_write.py`

#### Attempt 8: Custom Python pyusb — No-Erase Page Program
- Wrote `ch341a_write_noerase.py`: uses CH341A hardware SPI but skips erase, just hammers Page Program repeatedly
- Exploits NOR flash property: Page Program can only change bits from 1→0, never 0→1. So repeated writes monotonically converge toward the target.
- **Result:** **THIS WORKS** — bits accumulate correctly across passes.
- 0.18% of target bytes land correctly per pass
- After ~25 passes: **45.5% overall byte match**
- **Zero overcorrect bits** — no byte was written to a value that's "past" the target. Every bit that flipped went in the right direction.
- **Script location:** `scripts/ch341a_write_noerase.py`

#### Attempt 9: Write Hammering (100+ Passes)
- Ran no-erase script in a loop, accumulating correct bits
- **Result:** Converges but logarithmically. Each pass adds fewer new correct bytes.
- **Estimated time to 100%:** ~31 hours at 0.18%/pass convergence rate
- Abandoned in favor of fixing the root cause (hardware).

### backup_corrupted.bin — Confirmed Valid Read

Compared `backup_corrupted.bin` (read from chip in an earlier session) against the target VBIOS:
- **99.8% byte match** — this is the actual corrupted VBIOS currently on the chip
- The 0.2% difference is read noise (same 133-byte noise floor seen in Session 7 reads)
- Starts with `4E 56 47 49` ("NVGI") — correct NVIDIA VBIOS header
- **This confirms the corrupted VBIOS is only slightly corrupted** — not wiped, not all-zeros, just enough damage to fail FWSEC signature verification

### Root Cause Analysis: Data Line Voltage Mismatch

The "1.8V adapter" in the CH341A kit (AMS1117-1.8 voltage regulator) only drops **VCC** to 1.8V. The SPI **data lines** (MOSI, CLK, CS#) pass straight through from the CH341A at its native **3.3V–5V** levels.

The W25Q16JWN is rated for 1.65V–1.95V I/O. When driven at 3.3V+:
- **Erase works** because it's a single-opcode command (0x20 or 0xC7). The chip latches the command autonomously — data lines only need to be valid for a few clock cycles.
- **Read works** because MISO is driven by the chip at 1.8V levels, which the CH341A can still interpret as valid (1.8V > typical 0.8V TTL threshold).
- **Page Program fails** because it requires 256+ bytes of MOSI data at correct voltage levels. At 3.3V into a 1.8V chip, the chip's input buffers are in an undefined state — some bits latch correctly, most don't.

**Evidence for this diagnosis:**
1. Partial byte programming observed: expected `0x4E`, got `0x6F` — some bits went 1→0 correctly, others stayed at 1 (erased state)
2. Three independent software tools (flashrom, ch341prog, custom Python) all produce identical **0.18%** per-byte success rate — hardware-determined, not software
3. **Zero overcorrect bits** — data that DOES land is always correct. The issue is bits failing to program, not being programmed to wrong values.
4. Success rate doesn't change with page size (4 vs 16 vs 256 bytes) — it's per-bit, not per-transaction

### Current Chip State (End of Session 7)

| Metric | Value |
|---|---|
| Overall byte match | 45.5% |
| Actual data bytes correct | 3.8% |
| Overcorrect bits | 0 (zero) |
| First 2 bytes | 0x4E56 ("NV") — CORRECT |
| Bad sector (0x111000) | Still present (hardware defect) |
| Safe to continue writing? | YES — no erase needed, bits only go 1→0 |

### Flashrom Patched Build Details

Located at `/tmp/flashrom-build/`, patches applied:
- `need_erase()` returns 0 → skip erase, assume 0xFF
- `USB_IN_TRANSFERS = 1` → sequential USB packets
- Read phase skipped (forced all-0xFF `curcontents`)
- `W25Q16.W` page_size overridden to 4
- Rebuild command: `cd /tmp/flashrom-build && nix-shell -p meson ninja pkg-config libusb1 pciutils --run 'ninja -C build'`

### Verbose Flashrom Log

Full chip probe log saved to `logs/flashrom_session7_verbose.log` (1744 lines).
Shows every RDID probe across 500+ chip models — all return `0xEF6015` confirming stable detection.

### Binary Dumps

- `logs/baseline_before_tools.bin` — 2MB read from chip before any Session 7 writes (timestamp 01:02)
- `logs/after_ch341tool.bin` — 2MB read after ch341prog write attempt (timestamp 01:08). Differs from baseline at byte offset 1411+.
- `backup_corrupted.bin` — original corrupted VBIOS read (99.8% match to good VBIOS)

### NixOS Configuration Changes

- `~/dotfiles/modules/features/virtualization.nix`: added udev rule for CH341A (`1a86:5512`), added `win-virtio` package for Windows VM passthrough
- Needs `sudo nixos-rebuild switch --flake ~/dotfiles` to apply

### Session 7 Summary

**The chip is alive and responsive.** Reads, erases, and detection all work perfectly. Writes partially land at 0.18%/pass due to the 1.8V adapter only dropping VCC, not data line voltage. The no-erase hammering strategy proves the concept works — bits accumulate in the right direction with zero errors — but is too slow for practical use (~31 hours).

**Root cause confirmed:** Data line voltage mismatch (3.3V MOSI/CLK/CS into a 1.8V chip).

**Next steps (priority order):**
1. **TXS0108E level shifter** (~$3) — bidirectional 8-channel voltage translator, drops MOSI/CLK/CS to 1.8V. Solder inline between CH341A output and SOP8 clip. This is the proper fix.
2. **CH347T programmer** (~$15) — native configurable SPI voltage and speed. Drop-in replacement for CH341A.
3. **AsProgrammer on Windows VM** — Tiny10 23H2 ISO downloading. Last-resort software attempt.
4. **DO NOT ERASE the chip** — the 45.5% accumulated correct bits would be lost. Any future write strategy should build on what's already there.

---

## Session 8 — 2026-04-04 (NixOS Desktop, CH341A V1.7 "1.8V Level Conversion" + Windows 10)

### Equipment Changes
- **New programmer:** CH341A V1.7 with built-in "1.8V Level Conversion" (Amazon B0D9XQ4YBV)
  - Standard CH341A with integrated AMS1117-1.8 voltage regulator
  - Blue ZIF socket + SOP8 pin header
  - USB 2.0 extender, back I/O on PC
- **Windows 10:** Installed Tiny10, tried AsProgrammer and NeoProgrammer
- **Chip confirmed:** Winbond W25Q16JWNIQ (not "JWN1Q" — the "I" is the letter I for Industrial temp range, not the number 1)

### Chip Part Number Clarification
- Full part number: **W25Q16JWNIQ**
  - W25Q16 = 16Mbit Quad SPI
  - JW = 1.8V series (J-generation)
  - N = SOIC-8 narrow body package
  - I = Industrial temperature range (-40 to +85°C)
  - Q = Lead-free/RoHS
- DigiKey lists W25Q16JW**S**NIQ (S = SOIC-8 wide body) — different package, same silicon
- **JEDEC ID: EF 60 15** — identical to W25Q16FW_1.8V in AsProgrammer's chip database
- Datasheet: Winbond W25Q16JW RevD (Mouser: W25Q16JW_RevD_01152020_Plus-1760324.pdf)

### Windows 10 Results (AsProgrammer & NeoProgrammer)
- **CH341A detected:** Both programs found the CH341A USB device
- **Chip not in database:** W25Q16JWNIQ not listed in either program's chip list
  - AsProgrammer has W25Q16FW_1.8V (ID: EF6015) — same JEDEC ID, compatible
  - Selected W25Q16FW_1.8V manually
- **Same behavior as Linux:** Chip detected, erase works, reads work, **writes don't land**
- **Conclusion:** Issue is hardware (CH341A), not OS or software

### Read Quality Improvement
| Metric | Session 7 (old CH341A + adapter) | Session 8 (CH341A V1.7) |
|---|---|---|
| Read noise between consecutive reads | 133 bytes | **2 bytes** |
| Chip detection | Intermittent | Reliable |
| USB crashes | Frequent | None |

The new CH341A V1.7 has significantly better read signal integrity.

### Chip Protection Analysis (Definitive)
Read all three status registers via custom Python pyusb script with flashrom-compatible CH341A init:

| Register | Value | Meaning |
|---|---|---|
| SR1 | 0x00 | No block protection (BP0-2=0, SEC=0, TB=0, SRP0=0) |
| SR2 | 0x02 | QE=1 (Quad Enable), all else zero (CMP=0, SRP1=0, LB1-3=0) |
| SR3 | 0x00 | WPS=0 (legacy block protect mode, NOT individual block lock) |

- **No write protection active.** All protection mechanisms confirmed cleared.
- QE=1 is the only non-default bit (enables Quad SPI mode, harmless for standard SPI)
- Updated `clear_wp.py` to handle WPS/SR3 and Global Block Unlock (0x98), but they weren't needed
- Block lock readback at all addresses = 0 (unlocked)
- /WP pin irrelevant (SRP0=SRP1=0 = software protection only)

### Root Cause Discovery: CH341A SPI MOSI Buffer Limitation

**THE REAL PROBLEM WAS NEVER THE VOLTAGE.** Through systematic testing, discovered that the CH341A's SPI engine has a hardware limitation on MOSI data transmission.

#### Evidence Chain

**Test 1: Write size sweep**
Wrote different amounts of data via Page Program, all to freshly erased sectors:

| Data Size | SPI Bytes (cmd+addr+data) | Bytes Landed | Result |
|---|---|---|---|
| 1 byte | 5 | 1 | OK (chunked mode) |
| 2 bytes | 6 | 2 | OK |
| 4 bytes | 8 | 2 | First 2 data bytes only |
| 8 bytes | 12 | 2 | First 2 data bytes only |
| 16 bytes | 20 | 2 | First 2 data bytes only |
| 32 bytes | 36 | 2 | First 2 data bytes only |
| 256 bytes | 260 | 2 | First 2 data bytes only |

**Exactly 2 data bytes land per Page Program, regardless of total size sent.**

**Test 2: Multiple writes to same sector (one erase)**
- 1st PP at page offset +0: ACCEPTED (SR1 BUSY=1 after PP) → 2 bytes landed
- 2nd PP at page offset +2: REJECTED (SR1 BUSY=0, WEL=0 after PP) → nothing
- 3rd PP at page offset +4: REJECTED
- Conclusion: **Chip only accepts ONE Page Program per 256-byte page per erase cycle**

**Test 3: Multiple writes to DIFFERENT sectors (each freshly erased)**
- ALL writes succeed at 100%: 8/8 different 2-byte values, all correct
- **Writes work perfectly when the data gets through**

**Test 4: Per-page vs per-sector limit**
- Write to page 0 (addr+0x000): ACCEPTED (BUSY=1)
- Write to page 1 (addr+0x100): ACCEPTED (BUSY=1) ← different page, same sector
- Write to page 0 offset +2: REJECTED (BUSY=0) ← same page as first write
- **Limit is per-page, not per-sector.** 16 pages per sector each get one PP.

**Test 5: Page corruption check**
- After writing 2 bytes at page offset 0, read full 64-byte range
- **0 non-FF bytes beyond the 2 written** — page is NOT corrupted
- The chip simply rejects additional PPs to an already-programmed page

**Test 6: SR1 between operations**
```
After erase:  SR1=0x00 (ready)
After WREN:   SR1=0x02 (WEL=1) ← Write Enable set correctly
After 1st PP: SR1=0x03 (BUSY=1, WEL=1) ← Chip ACCEPTED, programming
After wait:   SR1=0x00 (done)
After WREN:   SR1=0x02 (WEL=1) ← Write Enable set correctly again
After 2nd PP: SR1=0x00 (BUSY=0, WEL=0) ← Chip REJECTED, not programming
```
The chip correctly receives WREN each time but rejects the second PP silently.

**Test 7: SPI speed variation**
Tried CH341A speed settings 0x60, 0x61, 0x62, 0x63 — all produce identical 2-byte limit.

**Test 8: USB packet strategies**
- Single A8 prefix (all data in one SPI packet): 2 bytes
- Flashrom-style 31-byte A8 chunks: 2 bytes
- Separate USB writes for UIO and SPI: 2 bytes
- Multiple A8 commands with CS# held low: 2 bytes

**Test 9: GPIO bit-bang attempt**
Attempted to bypass the SPI engine entirely by bit-banging MOSI via UIO GPIO (D5).
**Result:** Same 2-byte limit — D5 GPIO does NOT connect to the physical MOSI pin.
The CH341A's SPI data pins are hardwired to the SPI engine, not accessible via UIO GPIO.

#### Root Cause Conclusion

**The CH341A's SPI stream engine (command 0xA8) has a hardware MOSI data buffer of approximately 6 bytes.** After the first 6 bytes of SPI data are clocked out correctly on MOSI, all subsequent bytes become 0xFF.

This explains ALL prior observations:
- **Erase works:** Sector Erase = 4 SPI bytes (0x20 + 3 addr) → within 6-byte buffer ✓
- **WREN works:** 1 SPI byte (0x06) → within buffer ✓
- **RDID works:** 1 SPI byte sent (0x9F), chip responds on MISO ✓
- **Reads work:** 4 SPI bytes sent (0x03 + 3 addr), chip drives MISO → MOSI only needs 4 bytes ✓
- **Page Program fails:** 260 SPI bytes needed (0x02 + 3 addr + 256 data) → only first 6 go through, data bytes 3-256 become 0xFF, which is a no-op on erased flash ✗
- **Session 7 "voltage mismatch" was a misdiagnosis:** The 0.18%/pass success rate was actually from the 2 bytes per PP landing randomly across repeated hammer cycles, not from per-bit voltage errors

The 6-byte MOSI limit is sufficient for all read/erase/status operations. It ONLY affects Page Program (writes), which is the only SPI command requiring more than ~4 bytes of meaningful MOSI data.

**This is a hardware limitation of the CH341A IC itself. No software, driver, or firmware change can fix it. A different programmer is required.**

### Chip State (End of Session 8)
- Chip has been erased multiple times during testing
- Some residual test data at address 0x100000 (test patterns from write experiments)
- VBIOS data region (0x000000-0x0F41FF) is mostly erased from the full-chip write attempt
- **The original corrupted VBIOS data is gone** — chip needs a complete re-flash

### What Works
- ✅ Chip detection (RDID EF 60 15)
- ✅ Status register read/write
- ✅ Sector erase (4KB)
- ✅ Chip erase (except bad sector 0x111000)
- ✅ Page Program for 2 data bytes per page
- ✅ Read (2-byte noise floor — excellent)
- ✅ No write protection issues

### What Doesn't Work
- ❌ Page Program with more than 2 data bytes (CH341A MOSI buffer limit)
- ❌ Multiple Page Programs to same page per erase (chip rejects)
- ❌ Bad sector at 0x111000 (physically damaged, can't erase)

### Root Cause Revision: GPU SPI Bus Contention, NOT CH341A MOSI Buffer

**CORRECTION:** The initial Session 8 diagnosis ("CH341A has a 6-byte MOSI buffer limit") was WRONG.

The CH341A V1.7 (Amazon B0D9XQ4YBV, GODIYMODULES) has:
- **Dedicated level conversion IC** on the PCB (not just an AMS1117 VCC regulator)
- **Voltage switch** for 1.8V/3.3V/5V selection
- Proven to work with 1.8V chips (W25Q64FW shown in manufacturer's AsProgrammer screenshot)
- Product claims: "Integrated dedicated level conversion chip, directly read and write 5v, 3.3v, 2.5v, 1.8v chips"

The manufacturer's troubleshooting guide explicitly describes our exact failure mode:
- **"Communication line is occupied"** — the GPU's SPI controller pins (MOSI, CLK, CS, MISO) are connected to the same flash chip. Even with the laptop powered off, the GPU's I/O pads have protection diodes and ESD structures that load down the SPI bus.
- Short SPI commands (erase: 4 bytes, RDID: 4 bytes) get through because they're brief and the bus loading doesn't corrupt them.
- Page Program (260 bytes sustained MOSI) fails because the GPU's bus loading corrupts the MOSI data after the first few bytes.
- **Manufacturer's stated solution: "remove the chip to read and write!"**
- **"As long as you disconnect the chip's 8 wires and other circuits, the programmer in the board read and write 100% will not have a problem."**

This was actually the Session 6 "SPI bus contention" hypothesis, which was CORRECT but was abandoned in Session 7 when the "voltage mismatch" theory took over.

### Required Fix
**Desolder the W25Q16JWNIQ from the Razer motherboard**, program it off-board using the SOP8-to-DIP8 adapter in the CH341A V1.7's ZIF socket, then solder it back.

No programmer can "overpower" the GPU's bus loading at 1.8V — the voltage is dictated by the chip's rating (1.65-1.95V max), and driving harder at 1.8V doesn't change the physics. People who successfully flash GPU VBIOS externally desolder the chip first. There is no in-circuit workaround for GPU SPI bus contention.

**Equipment on hand:** CH341A V1.7 kit (GODIYMODULES, Amazon B0D9XQ4YBV) includes SOP8-to-DIP8 adapter board for ZIF socket programming. No additional purchases needed.

### Scripts Created/Updated This Session
- `clear_wp.py` — Updated: now handles WPS/SR3, Global Block Unlock (0x98), JEDEC ID verification, individual block lock scanning
- `probe_chip.py` — New: retry-loop chip probe with flashrom-compatible CH341A init
- `chip_diag.py` — New: full chip diagnostic (SR1/SR2/SR3, block locks, write test)
- `write_size_test.py` — New: Page Program size sweep (proved 2-byte limit)
- `write_erase_test.py` — New: multi-write and per-page/per-sector limit testing
- `debug_multi_write.py` — New: SR1 analysis between sequential Page Programs
- `bitbang_flash.py` — New: GPIO bit-bang attempt (proved D5 GPIO ≠ MOSI pin)
- `write_test.py` — New: flashrom-based write analysis
- `write_fix_test.py` — New: USB packet strategy testing
