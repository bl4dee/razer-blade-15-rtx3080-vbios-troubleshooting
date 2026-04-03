# Razer Blade 15 Advanced 2021 — VBIOS Recovery Status

## System
- **Laptop:** Razer Blade 15 Advanced 2021 (RZ09-0409CEC3)
- **GPU:** NVIDIA GA104M RTX 3080 Laptop 8GB
- **Device ID:** 10DE:249C (silicon fallback — should be 24DC with valid VBIOS)
- **Subsystem:** 1A58:2018 (Razer)
- **Flash Chip:** Winbond W25Q16JWN (1.8V SOP8, 16Mbit/2MB)
- **System BIOS:** Updated from v1.06 to v2.x via Razer updater tool (2026-03-30)
- **Symptom:** Code 43, GPU-Z shows "Unknown" BIOS, 0 MHz clocks, 0 MB memory
- **VBIOS File:** Razer.RTX3080.8192.210603.rom (TechPowerUp #235669, v94.04.55.00.92)
- **VBIOS MD5:** f458d34324bfd843bee5107006a0e70f

## Core Problem
Chicken-and-egg: GPU falcon microcontroller is halted because its firmware (stored in corrupted VBIOS on SPI flash) cannot load. Every software tool requires a running falcon or valid VBIOS to access SPI. Falcon firmware is IN the VBIOS.

---

## TRIED

### T01 — nvflash Standard Flash
- **When:** 2026-03-30, Session 1
- **How:** `./nvflash --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — "Adapter not accessible or supported EEPROM not found"
- **Times tried:** 1
- **Log:** `Logs and Attempts/flash_20260330_205952.log`

### T02 — nvflash --protectoff
- **When:** 2026-03-30, Session 1
- **How:** `./nvflash --protectoff --index=0`
- **Result:** FAILED — "A system restart might be required"
- **Times tried:** 1
- **Log:** `Logs and Attempts/flash_20260330_205952.log`

### T03 — nvflash -6 Override
- **When:** 2026-03-30, Session 1
- **How:** `./nvflash -6 --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — same "EEPROM not found"
- **Times tried:** 1
- **Log:** `Logs and Attempts/flash_20260330_205952.log`

### T04 — nvflash --overridesub
- **When:** 2026-03-30, Session 1
- **How:** `./nvflash --overridesub --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — same "EEPROM not found"
- **Times tried:** 1
- **Log:** `Logs and Attempts/flash_20260330_205952.log`

### T05 — nvflash -6 --override Combined
- **When:** 2026-03-30, Session 1
- **How:** `./nvflash -6 --override --index=0 Razer.RTX3080.8192.210603.rom`
- **Result:** FAILED — same "EEPROM not found"
- **Times tried:** 1

### T06 — Sysfs ROM Write
- **When:** 2026-03-30, Session 1
- **How:** `echo 1 > /sys/bus/pci/devices/0000:01:00.0/rom` then `cp ROM.rom .../rom`
- **Result:** FAILED — "File too large" (ROM BAR 512KB, VBIOS 976KB). Could not read current ROM either.
- **Times tried:** 1
- **Log:** `Logs and Attempts/flash_20260330_205952.log`

### T07 — PCI Command Register Enable + nvflash
- **When:** 2026-03-30, Session 1
- **How:** `setpci -s 01:00.0 COMMAND=0007` (enable I/O, Memory, BusMaster), confirmed readback 0x0007, then nvflash
- **Result:** FAILED — nvflash still "EEPROM not found". Not a PCI enable issue.
- **Times tried:** 1

### T08 — PCI Function Level Reset + nvflash
- **When:** 2026-03-30, Session 1
- **How:** `echo 1 > /sys/bus/pci/devices/0000:01:00.0/reset`, re-enabled command register, nvflash
- **Result:** FAILED — "EEPROM not found"
- **Times tried:** 1

### T09 — Direct BAR0 MMIO Register Access
- **When:** 2026-03-30, Session 1
- **How:** Mapped BAR0 (16MB at 0x85000000) via `/sys/bus/pci/devices/0000:01:00.0/resource0`
- **Result:** GPU silicon responds (NV_PMC_BOOT_0 = 0xB74000A1, GA104 confirmed). PROM window (0x300000) has corrupted data (starts 6E 56 47 49, not 55 AA). PROM NOT writable. PRAMIN (0x700000) returns BAD0AC.
- **Times tried:** 1

### T10 — SPI Controller Register Scan
- **When:** 2026-03-30, Session 1
- **How:** Scanned BAR0 offsets 0xE100, 0x10D000, 0x840000, 0x110000, 0x88000
- **Result:** All falcon-managed SPI areas return BADF (uninitialized) or DEAD5EC1/DEAD5EC2. SPI controller requires falcon, falcon requires VBIOS.
- **Times tried:** 1

### T11 — PMC Engine Enable
- **When:** 2026-03-30, Session 1
- **How:** Read/write NV_PMC_ENABLE (0x200). Tried enabling PFLASH (bit 12) and other engine bits.
- **Result:** FAILED — register rejects changes. 0xFFFFFFFF reads back as 0x56000000 (only bits 30/28/26/25 accepted). SPI registers still BADF.
- **Times tried:** 1

### T12 — Bypass nvflash nomodeset Check
- **When:** 2026-03-30, Session 1
- **How:** `mount --bind /tmp/fake_cmdline /proc/cmdline` (fake cmdline without nomodeset)
- **Result:** No change — error comes from GPU register state not cmdline. Strace confirms nvflash mmaps BAR0, reads registers, fails.
- **Times tried:** 1

### T13 — nouveau modeset=2 (Headless)
- **When:** 2026-03-30, Session 1
- **How:** `rmmod nouveau && modprobe nouveau modeset=2`
- **Result:** FAILED — nouveau tried 5 BIOS sources: PRAMIN (not enabled), PROM (sig 0x56FE, corrupt), ACPI (sig 0x0000, empty), PCIROM (0x56FE), PLATFORM (nothing). `bios ctor failed: -22`
- **Times tried:** 1

### T14 — NVIDIA Open Driver (580.126.09)
- **When:** 2026-03-30, Session 1
- **How:** `apt install nvidia-driver-575-open` (resolved to 580.126.09), modprobe nvidia
- **Result:** FAILED — `kgspExtractVbiosFromRom_TU102: did not find valid ROM signature`, `RmInitAdapter failed! (0x62:0x25:2015)`. Open module has hard GSP dependency for Ampere. `NVreg_EnableGpuFirmware=0` no effect on open module.
- **Times tried:** 1

### T15 — PCIe Secondary Bus Reset
- **When:** 2026-03-30, Session 1
- **How:** Reset PCIe bridge (00:01.0) Secondary Bus Reset bit
- **Result:** FAILED — PCIe still degraded 2.5GT/s x8. nvflash gave definitive error: `Falcon In HALT or STOP state, abort uCode command issuing process.` Confirms falcon is halted.
- **Times tried:** 1

### T16 — nvflash strace Analysis
- **When:** 2026-03-30, Session 1
- **How:** `strace -f ./nvflash --index=0 ROM.rom`
- **Result:** nvflash tries to load `nvtool` kernel module (unavailable), falls back to /dev/mem BAR0 mmap at 0x85000000, reads registers, finds falcon halted, gives up. Supports `--spiclkshmoo` suggesting SPI access goes through falcon microcode.
- **Times tried:** 1

### T17 — Razer System BIOS Update
- **When:** 2026-03-30
- **How:** Downloaded Razer BIOS updater for RZ09-0409 from mysupport.razer.com. Ran from Windows. System BIOS updated from v1.06 to v2.x.
- **Result:** FAILED — System BIOS updated from v1.06 to v2.x successfully. GPU still shows Code 43, same error. Running the Razer updater again reports "up to date." BIOS update did NOT re-provision the dGPU VBIOS.
- **Times tried:** 2 (update + re-run showing "up to date")

### T18 — ACPI Table Search for _ROM Method
- **When:** 2026-03-31
- **How:** Installed acpica-tools. Dumped and decompiled DSDT + all 13 SSDTs. Searched for `_ROM`, `VBIOS`, `NVROM`, `ROMF` strings.
- **Result:** DEAD END — No `_ROM` method exists in any ACPI table. System BIOS does not expose a GPU VBIOS via ACPI. N07 fully ruled out.
- **Times tried:** 1

### T19 — PCI Remove/Rescan (N09)
- **When:** 2026-03-31
- **How:** `echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove && echo 1 > /sys/bus/pci/devices/0000:00:01.0/rescan`
- **Result:** FAILED — GPU re-enumerates and nouveau auto-attaches. Same result: `Invalid PCI ROM header signature: expecting 0xaa55, got 0x56fe`, `bios ctor failed: -22`. No change in behavior. PCIe link still 2.5 GT/s x8.
- **Times tried:** 1

### T20 — envytools nvagetbios (N10)
- **When:** 2026-03-31
- **How:** Installed envytools from Fedora repos. `sudo nvagetbios` (auto-detect), `sudo nvagetbios -s PRAMIN`, `sudo nvagetbios -s PROM`
- **Result:** FAILED — Both methods report "Invalid signature(0x55aa)". PRAMIN output is garbage data (repeating pattern — uninitialized falcon memory). PROM reports corrupt sig 0x56FE. Same as T09/T13. No new information.
- **Times tried:** 1

### T21 — nvflash with nouveau Fully Unloaded (Post-BIOS-Update)
- **When:** 2026-03-31
- **How:** `sudo modprobe -r nouveau mxm_wmi`. Confirmed no GPU drivers loaded. Tried: standard flash, `--overridesub`, `-6`. ROM file confirmed valid via `nvflash --version Razer.RTX3080.8192.210603.rom` (shows correct v94.04.55.00.92, Device 24DC, Board 0x0262, Subsystem 1A58:2018).
- **Result:** FAILED — All variations give "Adapter not accessible or supported EEPROM not found". No change from T01–T05 despite BIOS update. nvflash detects the GPU (`10DE,249C,1A58,2018`) but cannot reach the EEPROM through the halted falcon.
- **Times tried:** 3

### T22 — System BIOS Flash Scan via MTD
- **When:** 2026-03-31, Session 4
- **How:** Read 12MB of system BIOS from `/dev/mtd0ro` (Intel SPI driver exposes BIOS flash as MTD). Scanned for NVGI, NVIDIA, GeForce, RTX, 10DE device IDs.
- **Result:** DEAD END — Zero NVIDIA content in system BIOS. Razer does NOT embed the dGPU VBIOS in system firmware.
- **Times tried:** 1

### T23 — SMBus/I2C Device Enumeration
- **When:** 2026-03-31, Session 4
- **How:** `i2cdetect -r -y` on buses 0 and 15. Dumped device at 0x44 (temperature sensor). Searched for GPU at 0x48-0x4F range.
- **Result:** DEAD END — No GPU SMBus slave found. Device at 0x44 is a system thermal sensor.
- **Times tried:** 1

### T24 — VBIOS File Format Analysis
- **When:** 2026-03-31, Session 4
- **How:** Hexdumped ROM file; compared first 512 bytes of PROM window (BAR0+0x300000) against ROM file byte-by-byte.
- **Result:** ROM starts with `NVGI` (4E 56 47 49), NOT `55 AA`. First `55 AA` PCI sub-image at offset 0x9400 (63KB, device ID 24DC confirmed). PROM data only 4.3% match — unreliable bus noise, not actual SPI contents.
- **Times tried:** 1

### T25 — BAR0 PROM Window Write Test
- **When:** 2026-03-31, Session 4
- **How:** Opened BAR0 resource0 for write. Wrote VBIOS bytes to PROM offset (0x300000). Verified readback.
- **Result:** FAILED — Writes silently discarded. PROM window is hardware read-only.
- **Times tried:** 1

### T26 — GSP RM Registry Keys (NVreg_RegistryDwords)
- **When:** 2026-03-31, Session 4
- **How:** `modprobe nouveau NVreg_RegistryDwords="RMDevinitBySecureBoot=0;RMDisableSpi=1"`
- **Result:** FAILED — PCIROM changed from 0x56EE→0xFFFF (keys affected SPI), but host-side bios ctor still fails -22.
- **Times tried:** 1

### T27 — nouveau PLATFORM Source + Firmware File
- **When:** 2026-03-31, Session 4
- **How:** Placed VBIOS at `/lib/firmware/nouveau/vbios.rom`. Loaded nouveau with `config=NvBios=PLATFORM debug=bios=trace`. Enabled firmware_class kernel debug.
- **Result:** FAILED — PLATFORM source does NOT call `request_firmware()` in GSP mode. Dead code path for Ampere. File never requested.
- **Times tried:** 3

### T28 — Custom kretprobe Kernel Module (vbios_inject.ko)
- **When:** 2026-03-31, Session 4
- **How:** Wrote and compiled custom kernel module using kretprobes on `pci_map_rom()` to intercept PCI ROM reads for GPU and return valid VBIOS data. Module loaded, kretprobes registered.
- **Result:** FAILED — With kretprobes active, nouveau stalled before reaching BIOS reading phase. PCI core interaction issue. Interceptor never triggered.
- **Times tried:** 2

### T29 — GSP Firmware FWSEC Security Analysis
- **When:** 2026-03-31, Session 4
- **How:** Extracted strings from `gsp-570.144.bin` (63MB). Searched for VBIOS verification error codes.
- **Result:** **DEFINITIVE FINDING** — FWSEC (Firmware Security) is a dedicated GPU hardware block that cryptographically verifies VBIOS directly from SPI before unlocking ANY falcon. Error strings confirm: signature verification, certificate chain, device ID, HAT (Hardware Access Token), HULK co-processor checks. FWSEC is NOT software-controllable. This is why all software approaches fail.
- **Times tried:** 1

### T30 — Falcon IMEM/DMEM Direct Write via BAR0 (hexkyz technique)
- **When:** 2026-03-31, Session 4
- **How:** Based on hexkyz/SciresM Falcon research. Scanned all falcon BAR0 bases. Found PMU (0x10A000), GSP (0x110000), SEC2 (0x840000) accessible for reads. Attempted writes to IMEMC/IMEMD, DMEMC/DMEMD, CPUCTL (START bit), BOOTVEC, DMATRFBASE on all three engines.
- **Result:** FAILED — **Every falcon register is completely write-locked.** All reads work but ALL writes are rejected (readback unchanged). FWSEC hardware gate blocks host writes to falcon IMEM/DMEM/control registers until VBIOS is verified from SPI. SEC2 DMEMD returns `0xDEAD5EC2` ("DEAD SEC2") confirming locked state.
- **Times tried:** 3 (PMU, GSP, SEC2 — each with IMEM, DMEM, CPUCTL, DMA tested)

### T31 — CH341A Hardware SPI Flash (Sessions 5, 6 & 7)
- **When:** 2026-04-02 to 2026-04-03, Sessions 5, 6 & 7
- **How:** CH341A USB programmer + 1.8V adapter + SOP8 clip on Winbond W25Q16JWN (confirmed by chip markings: "25Q16JWN", date code 2105, blue dot pin 1). Laptop battery disconnected, AC unplugged, vapor chamber removed. Flash computer: Ryzen 9 NixOS desktop. Tools: flashrom v1.7.0 (stock + patched), ch341prog, IMSProg, custom Python pyusb scripts.
- **Result:** PARTIAL SUCCESS
  - Sessions 5–6: No SPI response (USB crashes, all-zeros reads). Proved clip makes electrical contact via 3.3V overcurrent crash test.
  - **Session 7: BREAKTHROUGH** — chip detected (RDID 0xEF6015), reads/erases work perfectly. Writes partially land at **0.18% per-byte per pass**. After ~25 no-erase write passes: **45.5% overall byte match, zero overcorrect bits.**
- **Tools tried in Session 7:**
  - flashrom stock v1.7.0: erase works, writes don't land
  - flashrom patched (need_erase=0, skip-read, page_size=4): 0.18%/pass
  - ch341prog: same 0.18%/pass (confirms hardware issue)
  - IMSProg: fails verification
  - Custom Python no-erase script (`ch341a_write_noerase.py`): 0.18%/pass, bits accumulate correctly
  - Custom Python GPIO bit-bang (`bitbang_write.py`): protocol too complex, abandoned
- **Root cause:** The 1.8V adapter (AMS1117) only drops VCC to 1.8V. Data lines (MOSI/CLK/CS) pass through at CH341A native 3.3–5V. The W25Q16JWN (1.8V I/O) can't reliably latch 3.3V signals. Erase works (single-opcode, chip autonomous). Page Program fails (256-byte MOSI stream at wrong voltage). Three independent tools produce identical 0.18% → hardware-determined.
- **Current chip state:** 45.5% byte match, zero overcorrect bits, first 2 bytes correct (0x4E56 = "NV"), bad sector at 0x111000 still present. Safe to continue writing without erase.
- **backup_corrupted.bin:** Confirmed as valid prior read — 99.8% match to target VBIOS. The corruption is minimal (enough to fail FWSEC signature, not enough to destroy the image).
- **Times tried:** Sessions 5 (USB crashes), 6 (all-zeros), 7 (partial writes × 25+ passes with 3 different tools)
- **Blocker:** Data line voltage mismatch. Need TXS0108E level shifter ($3) or CH347T programmer ($15).
- **Logs:** `TROUBLESHOOTING_LOG.md` Sessions 5–7, `logs/flashrom_session7_verbose.log`, `logs/baseline_before_tools.bin`, `logs/after_ch341tool.bin`

---

## RULED OUT (researched, not attempted)

### N03 — nvflashk
- **Why ruled out:** Windows-only binary. Only bypasses board ID/device ID/subsystem ID mismatch checks — identical underlying SPI probe code to stock nvflash. Hits the same halted falcon wall. No benefit over `-6 --overridesub` already tried in T05/T21.
- **Ruled out:** 2026-03-31

### N05 — nouveau NvBios/ForcePost
- **Why ruled out:** Kernel 6.19 nouveau uses GSP RM firmware (570.144). NvBios and NvForcePost parameters do not exist in this version — the classic file-loading code path was removed when nouveau moved to GSP-based init. Would require kernel ≤5.19 with pre-GSP nouveau.
- **Ruled out:** 2026-03-31

### N07 — ACPI _ROM Extraction
- **Why ruled out:** Decompiled and searched DSDT + all 13 SSDTs (2026-03-31). No `_ROM` method exists in any table. System BIOS does not hold a GPU VBIOS copy via ACPI. See T18.
- **Ruled out:** 2026-03-31

### N16 — System BIOS Embedded VBIOS Extraction
- **Why ruled out:** Scanned 12MB of accessible system BIOS flash via `/dev/mtd0`. Zero hits for NVGI, NVIDIA, GeForce, RTX, or 10DE device IDs. Razer does not embed the dGPU VBIOS. See T22.
- **Ruled out:** 2026-03-31

### N17 — SMBus/I2C Access to GPU SPI
- **Why ruled out:** Enumerated all 16 I2C buses. No GPU SMBus slave found at any address. GPU does not expose I2C/SMBus interface for SPI access. See T23.
- **Ruled out:** 2026-03-31

### N18 — nouveau PLATFORM Firmware Loading (GSP mode)
- **Why ruled out:** Kernel firmware_class debug confirms PLATFORM source does NOT call `request_firmware()` in GSP-mode nouveau. The `vbios.rom` string in the binary is dead code for Ampere. See T27.
- **Ruled out:** 2026-03-31

### N19 — BAR0 PROM Window Data Injection
- **Why ruled out:** PROM window at BAR0+0x300000 is hardware read-only. Writes silently discard. Cannot inject VBIOS data through MMIO. See T25.
- **Ruled out:** 2026-03-31

### N20 — GSP RM Registry Key Override
- **Why ruled out:** While `RMDisableSpi` and `RMDevinitBySecureBoot` do affect GPU SPI behavior (confirmed: PCIROM value changed), the host-side nouveau `bios ctor` check happens BEFORE the GSP uses these keys. Can't bypass the host-side check. See T26.
- **Ruled out:** 2026-03-31

### N21 — pci_map_rom kretprobe Injection
- **Why ruled out:** Custom kernel module with kretprobes on `pci_map_rom()` causes nouveau to stall during PCI core initialization before BIOS reading phase. The kretprobes interfere with PCI enumeration. See T28.
- **Ruled out:** 2026-03-31

### N22 — Falcon IMEM/DMEM Direct Code Upload (hexkyz technique)
- **Why ruled out:** Scanned all falcon BAR0 bases — PMU, GSP, SEC2 are readable but ALL registers (IMEM, DMEM, CPUCTL, BOOTVEC, DMA) are completely write-locked by FWSEC. The hexkyz/SciresM Falcon exploits (maconstack, DMA race) require writable IMEM as a prerequisite. On Ampere, FWSEC blocks this at the hardware level. See T30.
- **Ruled out:** 2026-03-31

### N23 — Any Software-Only Approach (Definitive)
- **Why ruled out:** FWSEC hardware security module on the GPU die must read and cryptographically verify VBIOS directly from the SPI flash chip BEFORE any falcon microcontroller is unlocked. This is a hardware-enforced secure boot chain (signature → certificate → device ID → HAT → HULK). No OS, driver, firmware override, register manipulation, or falcon code injection can bypass FWSEC. 31 methods tried across 4 sessions — all failed. See T01–T30.
- **Ruled out:** 2026-03-31

---

## NOT YET TRIED

### N02 — nvflash on Windows
- **Priority:** LOW (downgraded from HIGH after FWSEC discovery)
- **How:** Reboot into Windows (nvme0n1p4 "Blade 15", Boot0000 in EFI). Download nvflash64.exe. Run as Administrator with the ROM file.
- **Why it probably won't work:** FWSEC hardware verification happens before any OS loads. UEFI cannot initialize the GPU without a valid VBIOS in SPI either. Windows nvflash would hit the same halted falcon.
- **Risk:** Low — worst case same EEPROM not found error
- **See:** WINDOWS_NVFLASH_PROCEDURE.md for step-by-step

### N15 — CH341A Hardware SPI Programmer ⬅ **IN PROGRESS (PARTIALLY WORKING)**
- **Priority:** CRITICAL — this is the ONLY remaining viable method
- **Status:** **Chip responds, reads/erases work, writes partially land (0.18%/pass).** Session 7 broke through the Session 5–6 detection failures. SPI bus contention hypothesis was WRONG — the real issue is data line voltage mismatch from the adapter. 45.5% of target bytes accumulated correctly via no-erase hammering.
- **How:** CH341A programmer + **proper 1.8V level shifting** + SOP8 test clip → direct SPI flash of W25Q16JWN.
- **Why it works:** Bypasses the GPU, falcons, and FWSEC entirely. Talks SPI directly to the flash chip. The approach is proven correct (bits land in the right direction, zero overcorrect bits).
- **⚠️ CRITICAL:** Chip is 1.65V–1.95V only. CH341A native 3.3V **WILL DESTROY IT**. 1.8V adapter is **MANDATORY** but current adapter only drops VCC, not data lines.
- **Blocker:** Data line voltage mismatch — need TXS0108E level shifter ($3) or CH347T programmer ($15) for proper 1.8V data line driving.
- **⚠️ DO NOT ERASE THE CHIP** — 45.5% accumulated correct bits would be lost.
- **See:** `scripts/ch341a_write_noerase.py`, `scripts/flash_vbios.py`, T31

---

## KEY DIAGNOSTIC DATA

| Field | Value |
|---|---|
| PCI Device ID | 10DE:249C (fallback — should be 24DC) |
| Subsystem ID | 1A58:2018 |
| PCIe Link Speed | 2.5 GT/s (should be 16 GT/s) |
| PCIe Link Width | x8 (should be x16) |
| PCI Command Register | All disabled (I/O-, Mem-, BusMaster-) |
| NV_PMC_BOOT_0 | 0xB74000A1 (GA104 silicon alive) |
| NV_PMC_ENABLE | 0x40000000 (only basic PCI enabled) |
| PROM Window (0x300000) | Corrupted — starts 6E 56 47 49 (should be 55 AA) |
| PRAMIN Window (0x700000) | BAD0AC (inaccessible) |
| Falcon Status | HALTED (confirmed by nvflash error Code:2) |
| SPI Registers (0xE100) | BADF5040 (uninitialized falcon) |
| nouveau BIOS read | PROM sig 0x56FE, ACPI sig 0x0000, all 5 sources failed |
| NVIDIA open driver | GSP init failed — no valid ROM signature (0x62:0x25:2015) |
| VBIOS file format | Starts with `NVGI` (4E 56 47 49), NOT `55 AA`. First PCI ROM at offset 0x9400 |
| System BIOS (MTD) | 12MB readable — NO embedded GPU VBIOS found |
| FWSEC (hardware) | Cryptographic VBIOS verification on GPU die — cannot be bypassed by software |
| GSP RM | Loads successfully (570.144) — but cannot proceed without FWSEC-verified VBIOS |
| Falcon register write-lock | PMU/GSP/SEC2 IMEM/DMEM/CPUCTL all reject writes — FWSEC hardware gate |
| SEC2 DMEMD marker | `0xDEAD5EC2` ("DEAD SEC2") — NVIDIA locked-state debug value |
| CH341A chip detection | RDID 0xEF6015 = Winbond W25Q16JW (Session 7) |
| CH341A read quality | Works but noisy — 133 bytes differ between consecutive reads |
| CH341A erase | Works perfectly — chip goes to all 0xFF reliably |
| CH341A write success rate | 0.18% per-byte per pass (identical across flashrom, ch341prog, Python) |
| CH341A overcorrect bits | 0 (zero) — every bit that lands is correct |
| Chip state after 25 passes | 45.5% overall byte match, 3.8% actual data bytes correct |
| backup_corrupted.bin | 99.8% match to target VBIOS — corruption is minimal |
| 1.8V adapter | AMS1117: drops VCC only, data lines pass through at 3.3–5V |
| Total methods tried | 31 (T01–T31 across 7 sessions) + 11 researched/ruled out (N03–N23) |
