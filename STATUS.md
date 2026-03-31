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

---

## NOT YET TRIED

### N02 — nvflash on Windows
- **Priority:** HIGH
- **How:** Boot Windows (NTFS on sda2 or install fresh). Disable dGPU in Device Manager. Run nvflash64.exe as admin.
- **Why it might work:** UEFI firmware POSTs the GPU during Windows boot via GOP driver. This initialization path is different from Linux — the GPU falcon may be partially alive after UEFI init. Windows nvflash may use a different driver backend for SPI access.
- **Risk:** Low
- **Resources:** techpowerup.com/download/nvidia-nvflash/
- **Status:** NOT TRIED
- **Result:**

### N03 — nvflashk (Patched nvflash with Board ID Bypass)
- **Priority:** HIGH
- **How:** Download nvflashk from github.com/notfromstatefarm/nvflashk. Run on Linux or Windows. Has enhanced EEPROM override that force-enables internal bypass code and different SPI probe sequence.
- **Why it might work:** Uses NVIDIA's internal bypass code paths that stock nvflash doesn't expose. Different EEPROM detection logic.
- **Risk:** Low
- **Resources:** github.com/notfromstatefarm/nvflashk
- **Status:** NOT TRIED
- **Result:**

### N04 — NVIDIA 470 Proprietary (Closed-Source) Driver
- **Priority:** HIGH
- **How:** `apt install nvidia-driver-470` on live USB. Boot with `nvidia.NVreg_EnableGpuFirmware=0`. Then retry nvflash.
- **Why it might work:** The 470 legacy driver is the last series WITHOUT mandatory GSP. It does its own direct register init — pokes GPU registers directly to read/write VBIOS without delegating to falcon/GSP. Completely different init path from the open driver that was tried.
- **Risk:** Low
- **Resources:** download.nvidia.com/XFree86/Linux-x86_64/470.223.02/README/gsp.html
- **Status:** NOT TRIED
- **Result:**

### N05 — nouveau with File-Based VBIOS + ForcePost
- **Priority:** HIGH
- **How:** Boot with kernel params: `nouveau.config=NvBios=/root/recovery/Razer.RTX3080.8192.210603.rom nouveau.config=NvForcePost=1`
- **Why it might work:** Tells nouveau to load the good VBIOS from a file instead of corrupt SPI flash, then force-POST the GPU. If it executes devinit scripts and boots the falcon, the SPI controller may become accessible for nvflash.
- **Risk:** Low
- **Resources:** nouveau.freedesktop.org/KernelModuleParameters.html
- **Status:** NOT TRIED
- **Result:**

### N06 — Boot Parameter Combinations
- **Priority:** MEDIUM
- **How:** Add to kernel cmdline: `intel_iommu=off iomem=relaxed pcie_aspm=off pci=realloc nouveau.config=NvBios=PROM`
- **Why it might work:** iommu=off removes IOMMU blocking of BAR access. pcie_aspm=off prevents power management from putting GPU to sleep. iomem=relaxed allows /dev/mem access to MMIO. pci=realloc fixes BAR sizing. Any of these might change GPU init behavior.
- **Risk:** Low
- **Status:** NOT TRIED
- **Result:**

### N07 — ACPI _ROM Extraction
- **Priority:** MEDIUM
- **How:** Boot with `nouveau.config=NvBios=ACPI`. If nouveau reads VBIOS from ACPI, extract via `cat /sys/kernel/debug/dri/1/vbios.rom > acpi_vbios.rom`. Use for hardware flash or further attempts.
- **Why it might work:** On muxless Optimus laptops, system BIOS holds a copy of dGPU VBIOS and serves it via ACPI _ROM method. Previous attempt showed ACPI returned sig 0x0000 (empty) but that was without explicitly forcing ACPI mode.
- **Risk:** Low
- **Status:** NOT TRIED
- **Result:**

### N08 — Older nvflash Versions (5.118, 5.314, 5.590)
- **Priority:** MEDIUM
- **How:** Download older nvflash versions from TechPowerUp. Different versions have different EEPROM detection databases and SPI probe sequences.
- **Why it might work:** Users report cases where older versions detect EEPROMs that newer ones don't. v5.590 "with board ID mismatch disabled" available separately.
- **Risk:** Low
- **Resources:** techpowerup.com/download/nvidia-nvflash-with-board-id-mismatch-disabled/
- **Status:** NOT TRIED
- **Result:**

### N09 — PCI Remove/Rescan
- **Priority:** MEDIUM
- **How:** `echo 1 > /sys/bus/pci/devices/0000:01:00.0/remove && sleep 2 && echo 1 > /sys/bus/pci/rescan`
- **Why it might work:** Forces full PCI re-enumeration. Kernel may re-execute GPU option ROM or trigger different init sequence on rescan.
- **Risk:** Low
- **Status:** NOT TRIED
- **Result:**

### N10 — envytools (nvapeek/nvapoke/nvagetbios)
- **Priority:** MEDIUM
- **How:** `apt install envytools` or build from github.com/envytools/envytools. Try `nvagetbios -s prom > dump.rom`, `nvapeek 0x300000 0x10000`.
- **Why it might work:** Different access path than nvflash. Can directly poke any BAR0 register. May reveal SPI controller access that nvflash's higher-level abstraction misses.
- **Risk:** Low
- **Status:** NOT TRIED
- **Result:**

### N11 — devmem2 / Direct /dev/mem SPI Register Writes
- **Priority:** LOW
- **How:** Boot with `iomem=relaxed`. Use devmem2 to directly read/write GPU registers at BAR0+offsets. Target SPI controller registers.
- **Why it might work:** Bypasses all software abstraction. Direct memory-mapped I/O to GPU. Can try register sequences that nvflash doesn't attempt.
- **Risk:** Medium — wrong register writes could lock up system
- **Status:** NOT TRIED
- **Result:**

### N12 — OMGVflash (by Veii)
- **Priority:** LOW
- **How:** Download OMGVflash. Interacts with falcon security processor directly, can bypass signature verification and remove EEPROM locks.
- **Why it might work:** Can address XUSB FW lockdown that implements one-way software EEPROM access lock on newer VBIOS. Different falcon communication method.
- **Risk:** Low
- **Resources:** kitguru.net article on OMGVflash
- **Status:** NOT TRIED
- **Result:**

### N13 — VFIO GPU Passthrough to Windows VM
- **Priority:** LOW
- **How:** Bind dGPU to vfio-pci, pass through to Windows QEMU VM with custom ACPI SSDT providing _ROM method, flash from inside VM.
- **Why it might work:** If OVMF firmware can POST GPU using ACPI-supplied VBIOS, GPU might be functional inside VM.
- **Risk:** Complex setup, likely same halted falcon issue inside VM
- **Status:** NOT TRIED
- **Result:**

### N14 — DOS-Mode nvflash from Bootable USB
- **Priority:** LOW
- **How:** Create FreeDOS bootable USB, copy nvflash DOS version + ROM. Boot and flash.
- **Why it might work:** GPU state is simpler at DOS boot time. Minimal OS interference. Some users report success with DOS when OS-based flash fails.
- **Risk:** Low
- **Status:** NOT TRIED
- **Result:**

### N15 — CH341A Hardware SPI Programmer
- **Priority:** FALLBACK (if all software methods fail)
- **How:** CH341A programmer ($5-15) + 1.8V adapter (CRITICAL) + SOP8 test clip. Direct SPI flash bypassing GPU entirely.
- **Why it works:** Talks directly to W25Q16JWN chip via SPI protocol. GPU is not involved. 95%+ success rate.
- **Risk:** Must use 1.8V adapter — chip rated 1.65V-1.95V only. CH341A native 3.3V WILL fry it.
- **Resources:** See ch341a_flash.sh
- **Status:** NOT TRIED — hardware not yet purchased
- **Result:**

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
