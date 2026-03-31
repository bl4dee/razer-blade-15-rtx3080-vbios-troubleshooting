# N02: Windows nvflash Test Procedure

## Why This Might Work

When the laptop boots Windows via UEFI, the firmware executes the GPU's GOP (Graphics Output
Protocol) driver to get display output. This UEFI initialization runs **before** any OS driver
loads and uses a completely different code path than Linux. If UEFI partially initializes the
GPU falcon during this process, Windows nvflash (which uses a Windows WDDM kernel driver shim
rather than raw /dev/mem BAR0 access) may be able to reach the SPI controller.

Low probability, but the easiest remaining software test.

---

## Setup (do from Windows)

1. **Get nvflash for Windows** — TechPowerUp → Downloads → NVIDIA nvFlash → latest version
   - You want `nvflash_X.XXX_windows.zip` — extract `nvflash64.exe`

2. **Copy files to Windows** — place on Desktop or C:\nvflash\:
   - `nvflash64.exe`
   - `Razer.RTX3080.8192.210603.rom` (already in this repo)

---

## Boot Windows

Windows is on the NVMe drive (nvme0n1). EFI has it as Boot0000 (Windows Boot Manager).

**From Linux:**
```bash
# Set next boot to Windows (one-time, no permanent change)
sudo efibootmgr -n 0000
sudo reboot
```

Or just restart and select "Windows Boot Manager" from the UEFI/GRUB menu.

---

## Windows Procedure

Open **Command Prompt as Administrator** (right-click Start → "Command Prompt (Admin)"):

```cmd
cd C:\nvflash

REM Step 1: List adapters — confirm GPU is detected
nvflash64.exe --list

REM Expected: should show the GPU (10DE:249C or 10DE:24DC if UEFI initialized it)

REM Step 2: Standard flash attempt
nvflash64.exe Razer.RTX3080.8192.210603.rom

REM Step 3: If "EEPROM not found", try with overrides
nvflash64.exe -6 --overridesub Razer.RTX3080.8192.210603.rom

REM Step 4: If "system restart required", disable GPU in Device Manager first:
REM   Device Manager → Display Adapters → right-click GPU → Disable device
REM   Then retry steps 2-3

REM Step 5: Try protectoff first (removes write protection)
nvflash64.exe --protectoff
nvflash64.exe Razer.RTX3080.8192.210603.rom
```

---

## What to Record

Note the exact error message for each attempt:
- "EEPROM not found" → falcon still halted, same as Linux (expected failure)
- "System restart required" → driver conflict, disable GPU in Device Manager and retry
- "Board ID mismatch" → add `-6 --overridesub` flags
- **Success** → flash proceeds, GPU reboots with correct VBIOS

If all Windows attempts fail with "EEPROM not found" → hardware path is required. Order CH341A.

---

## After Windows Test

**If failed:** Return to Linux USB, update STATUS.md T22, order CH341A hardware.

**Boot back to Fedora USB:**
```bash
# From Windows, to set next boot to Fedora USB:
# Hold Shift while clicking Restart → UEFI Firmware Settings → select USB boot

# Or from Linux (after booting into Fedora USB):
sudo efibootmgr -n 0001   # Boot0001 = Fedora USB
sudo reboot
```

---

## If Flash Succeeds

1. Restart laptop normally (no USB)
2. Windows should detect RTX 3080 with correct Device ID 10DE:24DC
3. GPU-Z should show v94.04.55.00.92
4. Install NVIDIA drivers if not already present
5. PCIe link should show 16 GT/s x16
