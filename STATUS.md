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

---

## NOT YET TRIED

### N02 — nvflash on Windows ⬅ NEXT PRIORITY
- **Priority:** HIGH
- **How:** Reboot into Windows (on nvme0n1p4 "Blade 15", Boot0000 in EFI). Download nvflash64.exe + Razer.RTX3080.8192.210603.rom. Run as Administrator. Try: `nvflash64.exe Razer.RTX3080.8192.210603.rom` and with `-6 --overridesub`.
- **Why it might work:** UEFI firmware POSTs the GPU via GOP before any driver loads. If UEFI partially initializes the falcon (even minimally), Windows nvflash may find the EEPROM accessible. Different driver backend (Windows nvflash uses WDDM kernel driver shim, not raw /dev/mem BAR0).
- **Risk:** Low — worst case is same EEPROM not found error
- **Status:** NOT TRIED
- **Result:**
- **Note:** Windows partition confirmed present on nvme0n1p4. EFI has Windows Boot Manager as Boot0000.

### N03 — nvflashk — RULED OUT
- **Priority:** SKIP
- **Why skipped:** Confirmed (2026-03-31): nvflashk is Windows-only and only bypasses board ID/device ID/subsystem ID mismatch checks. It does NOT have different EEPROM detection logic — the underlying SPI probe code is identical to stock nvflash. Will hit the same halted falcon wall. No benefit over `-6 --overridesub` already tried in T05/T21.
- **Status:** RULED OUT — will not help with halted falcon

### N04 — NVIDIA 470 Proprietary Driver — LOW VALUE
- **Priority:** LOW (was HIGH — downgraded)
- **How:** Requires kernel ≤5.19 (470.xx does not support kernel 6.19). Would need to install an old kernel separately.
- **Why downgraded:** Even if 470 doesn't use GSP, it still needs to read VBIOS from hardware during init. The falcon is halted, so the VBIOS read will fail regardless of which driver does it. BIOS-less init for Ampere is not something 470 supports.
- **Status:** NOT TRIED — low value, skip unless N02 fails and CH341A unavailable

### N05 — nouveau NvBios/ForcePost — BLOCKED
- **Priority:** BLOCKED
- **Why blocked:** Fedora 43 kernel 6.19 ships nouveau with GSP RM firmware (570.144). Confirmed 2026-03-31: NvBios and NvForcePost parameters are NOT available as module parameters. The `config=` string path doesn't expose them either. The classic NvBios file-loading code path was removed when nouveau moved to GSP-based init. Would require an older kernel (≤5.19) with pre-GSP nouveau.
- **Status:** BLOCKED by GSP-based nouveau in kernel 6.19

### N06 — Boot Parameter Combinations
- **Priority:** LOW
- **How:** Add to kernel cmdline at GRUB prompt: `iommu=off iomem=relaxed pcie_aspm=off`
- **Why it might help:** iomem=relaxed enables broader /dev/mem MMIO access. pcie_aspm=off prevents PCIe power states interfering. iommu=off removes VT-d restrictions.
- **Why it probably won't:** The IOMMU is already permitting BAR0 access (direct reads work). The fundamental issue is the halted falcon, not access restrictions.
- **Status:** NOT TRIED — worth one attempt at next reboot before Windows test

### N07 — ACPI _ROM — RULED OUT
- **Priority:** SKIP
- **Why ruled out:** T18 (2026-03-31): Decompiled and searched all ACPI tables (DSDT + 13 SSDTs). No `_ROM` method exists. System BIOS does not hold a GPU VBIOS copy accessible via ACPI. Dead end.
- **Status:** RULED OUT

### N08 — Older nvflash Versions
- **Priority:** LOW
- **How:** Download nvflash v5.118, v5.314, v5.590 from TechPowerUp. Try each with standard and -6 flags.
- **Why it probably won't help:** The EEPROM detection failure comes from falcon registers returning BADF (uninitialized), not from the EEPROM database. Older versions use the same detection path.
- **Status:** NOT TRIED — low priority

### N09 — PCI Remove/Rescan — DONE, FAILED
- **Status:** FAILED (T19, 2026-03-31)

### N10 — envytools — DONE, FAILED
- **Status:** FAILED (T20, 2026-03-31)

### N11 — devmem2 / Direct SPI Register Writes
- **Priority:** LOW
- **How:** Boot with `iomem=relaxed`. Use devmem2 to write to GPU BAR0+0xE100 (SPI controller). Target SPI CSR registers to force-enable SPI without falcon.
- **Why probably won't work:** The SPI controller MMIO registers (0xE100+) return BADF because the falcon hardware block that gates them is halted. Writing to these registers has no effect without the falcon running.
- **Status:** NOT TRIED

### N12 — OMGVflash
- **Priority:** LOW
- **How:** Windows tool by Veii. Download and run as admin.
- **Why probably won't work:** Same falcon dependency. OMGVflash's "bypass" is for EEPROM write-protect bits, not halted falcon state.
- **Status:** NOT TRIED

### N13 — VFIO GPU Passthrough to Windows VM
- **Priority:** VERY LOW
- **Why:** The GPU enters the VM in the same halted state. OVMF cannot re-POST it without a valid VBIOS. Very complex setup for almost certain failure.
- **Status:** NOT TRIED

### N14 — DOS-Mode nvflash
- **Priority:** LOW
- **How:** FreeDOS bootable USB with nvflash DOS binary. Boot and flash.
- **Why it might work:** At DOS boot, UEFI has already run. If UEFI partially initialized the falcon, nvflash under DOS might find the EEPROM accessible (same theory as N02 but without Windows overhead).
- **Status:** NOT TRIED — simpler version of the UEFI-init theory

### N15 — CH341A Hardware SPI Programmer ⬅ DEFINITIVE SOLUTION
- **Priority:** FALLBACK — order now if N02 fails
- **How:** CH341A programmer + 1.8V adapter + SOP8 test clip → direct SPI flash of W25Q16JWN chip.
- **Why it works:** Bypasses the GPU and falcon entirely. Talks SPI directly to the flash chip. ~95% success rate.
- **CRITICAL:** Chip is 1.65V–1.95V only. CH341A native 3.3V output WILL destroy the chip. Must use 1.8V adapter board.
- **What to buy:**
  - CH341A USB programmer (any): ~$8–12
  - 1.8V adapter board (sometimes called "1.8V BIOS chip adapter"): ~$5–8
  - SOIC8/SOP8 test clip with ribbon cable: ~$5–8
  - Total: ~$20–28 on Amazon, or ~$15 on AliExpress (slower shipping)
- **Resources:** See ch341a_flash.sh for exact flashrom commands
- **Status:** NOT TRIED — hardware not yet purchased

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
