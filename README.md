# Razer Blade 15 Advanced 2021 — RTX 3080 VBIOS Recovery

Complete documentation of recovering a corrupted NVIDIA GeForce RTX 3080 Laptop GPU VBIOS on a Razer Blade 15 Advanced (Early 2021, RZ09-0409). 31+ methods tried across 8 sessions. Every software approach fails due to NVIDIA FWSEC hardware security — physical SPI chip programming is the only path.

If you're here because your Razer Blade 15 has a **Code 43 GPU**, **GPU-Z shows "Unknown"**, or **Device Manager shows the GPU but it doesn't work** — this is likely your problem.

![Winbond W25Q16JWN GPU VBIOS flash chip on Razer Blade 15 2021 motherboard](photos/gpu-flash-chip-winbond-w25q16jwn-closeup.jpg)

## Symptoms

- **Windows:** GPU Code 43, GPU-Z shows "Unknown" BIOS, 0 MHz clocks, 0 MB memory
- **Linux:** Device ID 10DE:249C (silicon fallback — should be 10DE:24DC)
- **PCIe:** Degraded to 2.5 GT/s x8 (should be 16 GT/s x16)
- **dmesg/nouveau:** `Invalid PCI ROM header signature: expecting 0xaa55, got 0x56fe`
- **nvflash:** `Falcon In HALT or STOP state`

## The Problem

The GPU VBIOS lives on a tiny SPI flash chip (Winbond W25Q16JWNIQ, 1.8V, 2MB) soldered to the motherboard. When this chip's data is corrupted, the GPU can't boot — and because NVIDIA Ampere GPUs have **FWSEC** (a hardware security block that cryptographically verifies the VBIOS before allowing anything else to run), no software tool can fix it. The falcon microcontroller that manages SPI access is itself locked until FWSEC passes. Chicken and egg.

**Every software approach fails.** nvflash, sysfs writes, nouveau patches, NVIDIA open driver, BAR0 MMIO, falcon register injection, kernel modules — 31 methods tried, all dead ends. [Full list in STATUS.md](STATUS.md).

## The Fix: Desolder and Program Off-Board

**You CANNOT reliably program this chip in-circuit** (with a SOP8 clip while it's soldered to the board). The NVIDIA GPU's SPI controller pins create bus contention on the MOSI/CLK lines even when the laptop is powered off. Short SPI commands (erase, chip detection) get through, but Page Program (256-byte writes) fails because the GPU's I/O pads load down the data signal after the first few bytes.

This is confirmed by the CH341A manufacturer's own troubleshooting documentation:
> *"Communication line is occupied... the main control of the motherboard directly connected... The simplest solution: remove the chip to read and write!"*
> *"As long as you disconnect the chip's 8 wires and other circuits, the programmer in the board read and write 100% will not have a problem."*

### What You Need

| Part | Price | Notes |
|---|---|---|
| CH341A V1.7 with 1.8V level conversion | ~$14 | [Amazon B0D9XQ4YBV](https://www.amazon.com/dp/B0D9XQ4YBV) — has dedicated level conversion chip, voltage switch, and SOP8 adapter |
| Hot air rework station or fine-tip iron | varies | To desolder/resolder the SOP8 chip |
| Flux + solder paste/wire | ~$5-10 | For resoldering |

The CH341A V1.7 kit includes a SOP8-to-DIP8 adapter board for the ZIF socket. No additional level shifters or adapters needed — the board has an integrated level conversion chip that properly supports 1.8V.

> **Do NOT buy a separate "1.8V adapter board"** (the small green PCB with just an AMS1117 regulator). Those only drop VCC to 1.8V — the data lines still pass through at 3.3-5V. The CH341A V1.7 with integrated level conversion handles everything correctly.

### Flash Procedure

1. **Desolder the W25Q16JWNIQ** from the Razer motherboard using a hot air station (~300-350C with flux). The chip is a small 8-pin SOP8 located near the GPU die. [Photo of exact location.](photos/gpu-flash-chip-winbond-w25q16jwn-closeup.jpg)
2. **Place the chip on the SOP8-to-DIP8 adapter** (included in the CH341A V1.7 kit).
3. **Insert the adapter into the ZIF socket** on the CH341A. Match pin 1 (blue dot on chip) to pin 1 on the adapter/socket.
4. **Set the voltage switch to 1.8V** on the CH341A board.
5. **Connect CH341A to your PC via USB.**
6. **Flash using AsProgrammer (Windows) or flashrom (Linux):**

**Windows (AsProgrammer):**
- Install CH341A driver
- Open AsProgrammer, select chip: **W25Q16FW** (same JEDEC ID EF6015 as W25Q16JW)
- Set voltage to 1.8V
- Read chip → verify detection
- Open file → select `Razer.RTX3080.8192.210603.rom`
- Program → wait for completion and verification

**Linux (flashrom):**
```bash
# Detect chip
flashrom -p ch341a_spi
# Expect: Found Winbond flash chip "W25Q16.W"

# Backup current contents
flashrom -p ch341a_spi -c W25Q16.W -r backup.bin

# Pad VBIOS to 2MB chip size and write
dd if=Razer.RTX3080.8192.210603.rom of=padded.bin bs=2M conv=sync
flashrom -p ch341a_spi -c W25Q16.W -w padded.bin

# Verify
flashrom -p ch341a_spi -c W25Q16.W -v padded.bin
```

7. **Resolder the chip** back onto the motherboard. Align pin 1, apply flux, reflow with hot air or iron.
8. **Reassemble laptop.** Reconnect battery, replace heatsink, close backplate.
9. **Boot into Windows.** Check GPU-Z — should show VBIOS v94.04.55.00.92, RTX 3080, 8GB.

### Note on Bad Sector

There is a bad sector at address 0x111000 on our specific chip (hardware defect — can't be erased). This is in the padding area **past the VBIOS data** (VBIOS is ~976KB, bad sector starts at ~1.1MB), so it does not affect the VBIOS. If flashrom reports an erase failure at 0x111000, use the layout file to skip it:

```bash
flashrom -p ch341a_spi -c W25Q16.W --layout layout.txt --include vbios_region -w padded.bin
```

### Chip Part Number

The chip is **Winbond W25Q16JWNIQ**:
- W25Q16 = 16Mbit (2MB) Quad SPI NOR Flash
- JW = 1.8V series (J-generation, W=wide voltage)
- N = SOIC-8 narrow body package
- I = Industrial temperature range (-40 to +85C)
- Q = Lead-free/RoHS
- JEDEC ID: **EF 60 15**
- Datasheet: [Winbond W25Q16JW RevD](https://www.mouser.com/datasheet/2/949/W25Q16JW_RevD_01152020_Plus-1760324.pdf)
- Compatible chip selection in AsProgrammer: **W25Q16FW** (same JEDEC ID)

## Why In-Circuit Programming Fails

We spent 8 sessions and 31+ methods trying to make in-circuit programming work. Here's what happens:

1. **SOP8 clip makes electrical contact** — proven by chip detection (JEDEC ID EF6015 reads correctly) and erase operations completing successfully.
2. **Short SPI commands work** — Write Enable (1 byte), Sector Erase (4 bytes), Read JEDEC ID (4 bytes) all succeed 100%.
3. **Page Program fails** — the 260-byte MOSI data stream (1 cmd + 3 addr + 256 data) gets corrupted after the first ~6 bytes. Only 2 data bytes land per Page Program.
4. **The GPU's SPI controller pins load down the MOSI line** — even with the laptop powered off and battery disconnected, the GPU die's I/O pads (ESD protection diodes, pad structures) create a low-impedance path that interferes with sustained SPI data transmission.
5. **This is NOT a voltage problem, NOT a CH341A buffer limit, and NOT a write protection issue** — we proved all three wrong through systematic testing (see Session 8 in TROUBLESHOOTING_LOG.md).

The manufacturer of the CH341A V1.7 explicitly documents this as expected behavior for in-circuit programming when the chip shares a bus with a main controller.

## Current Status

**Waiting on desoldering.** The chip needs to be removed from the board for off-board programming. All equipment is on hand (CH341A V1.7 with SOP8 adapter, VBIOS ROM file verified).

See [STATUS.md](STATUS.md) for the full method-by-method breakdown and [TROUBLESHOOTING_LOG.md](TROUBLESHOOTING_LOG.md) for the narrative log of all 8 sessions.

## What We Learned

Things that are useful to know if you're debugging a similar issue:

**About the GPU VBIOS flash chip:**
- The chip is a **Winbond W25Q16JWNIQ** — 1.8V SOP8, near the GPU die. [Photo of exact location.](photos/gpu-flash-chip-winbond-w25q16jwn-closeup.jpg)
- There are **multiple SOP8 flash chips** on the board. The GigaDevice GD25B64C (8MB) is the system BIOS — [don't flash that one](photos/).
- The corruption was minimal — `backup_corrupted.bin` is a 99.8% match to the good VBIOS. Just enough damage to fail FWSEC signature verification.
- Chip protection state: SR1=0x00 (no block protect), SR2=0x02 (QE=1 only), SR3=0x00 (WPS=0). No write protection is active.
- There's a **bad sector at 0x111000** (hardware defect, can't erase) — but it's past the VBIOS data region.

**About NVIDIA Ampere security:**
- **FWSEC** is a hardware block on the GPU die. It reads and cryptographically verifies the VBIOS directly from SPI before unlocking any falcon microcontroller. No software can bypass it.
- The falcon registers (PMU, GSP, SEC2) are readable via BAR0 MMIO but all writes are hardware-locked. `SEC2 DMEMD` returns `0xDEAD5EC2` — NVIDIA's debug marker for "locked, don't bother."
- The GPU silicon IS alive — `NV_PMC_BOOT_0 = 0xB74000A1` (GA104 confirmed). It just can't do anything without a verified VBIOS.

**About in-circuit SPI programming on GPU VBIOS chips:**
- **In-circuit programming with SOP8 clips does NOT work reliably for GPU VBIOS chips.** The GPU's SPI controller creates bus contention that corrupts Page Program data. This is different from system BIOS chips (connected to Intel PCH, which has high-impedance pins when powered off).
- The CH341A V1.7 with integrated 1.8V level conversion (GODIYMODULES) works correctly for voltage/signal levels. The problem is bus contention from the GPU, not the programmer.
- 6 different software tools (flashrom, ch341prog, IMSProg, AsProgrammer, NeoProgrammer, custom Python) across 2 OSes all show the same behavior — confirming it's a hardware issue.
- **Desolder the chip to program it.** The CH341A kit includes a SOP8-to-DIP8 adapter for the ZIF socket.

## Hardware Info

| | |
|---|---|
| **Laptop** | Razer Blade 15 Advanced 2021 (RZ09-0409CEC3) |
| **GPU** | NVIDIA GA104M RTX 3080 Laptop 8GB |
| **Device ID** | 10DE:249C (fallback) → should be 10DE:24DC |
| **Subsystem** | 1A58:2018 (Razer) |
| **VBIOS chip** | Winbond W25Q16JWNIQ — 1.8V SOP8, 2MB, JEDEC 0xEF6015 |
| **Target VBIOS** | [TechPowerUp #235669](https://www.techpowerup.com/vgabios/235669/), v94.04.55.00.92 |
| **VBIOS MD5** | `f458d34324bfd843bee5107006a0e70f` |
| **Programmer** | CH341A V1.7 1.8V Level Conversion ([Amazon B0D9XQ4YBV](https://www.amazon.com/dp/B0D9XQ4YBV)) |

## Repository Contents

| Path | Description |
|---|---|
| [STATUS.md](STATUS.md) | Every method tried/untried with results |
| [TROUBLESHOOTING_LOG.md](TROUBLESHOOTING_LOG.md) | Full narrative log — 8 sessions, 31+ methods |
| [photos/](photos/) | Hardware photos — chip locations, CH341A setup, SOP8 identification |
| [scripts/](scripts/) | Flash scripts, diagnostics, write analysis tools |
| [patches/](patches/) | 8 nouveau kernel patches (all failed — FWSEC blocks everything) |
| [logs/](logs/) | Raw logs, binary chip dumps, verbose flashrom output |
| [win_tools/](win_tools/) | AsProgrammer, CH341/CH347 DLLs, Windows drivers |
| [docs/](docs/) | Architecture diagrams, attack plans |
| `backup_corrupted.bin` | Corrupted VBIOS read from chip (99.8% match to good) |
| `Razer.RTX3080.8192.210603.rom` | Target VBIOS image (976KB) |
| `layout.txt` | SPI chip memory layout — vbios region, bad sector, padding |

## Key Scripts

| Script | Purpose |
|---|---|
| `scripts/clear_wp.py` | Full write protection clearer — handles SR1/SR2/SR3, WPS, Global Block Unlock |
| `scripts/chip_diag.py` | Complete chip diagnostic — JEDEC ID, all status registers, block locks, write test |
| `scripts/probe_chip.py` | Retry-loop chip probe with flashrom-compatible CH341A init |
| `scripts/write_size_test.py` | Proved the 2-byte-per-Page-Program limit |
| `scripts/write_erase_test.py` | Proved writes work 100% on freshly erased sectors |
| `scripts/debug_multi_write.py` | Proved chip rejects 2nd Page Program to same page |
| `scripts/ch341a_write_noerase.py` | No-erase hammering (Session 7 approach) |
| `scripts/flash_vbios.py` | Automated flash script with retries |
| `scripts/ch341a_flash.sh` | Interactive hardware flash with safety checks |
