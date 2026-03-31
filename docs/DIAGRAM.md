# GPU VBIOS Corruption — The Chicken-and-Egg Problem

## Normal GPU Boot Sequence (working GPU)

```
┌─────────────────────────────────────────────────────────┐
│                    GPU POWERS ON                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ① FWSEC (Hardware Security Block on GPU die)           │
│                                                         │
│    Reads VBIOS from SPI flash chip ──────────┐          │
│    Verifies cryptographic signature chain:    │          │
│      - Digital signature ✓                    │          │
│      - Certificate chain ✓                    │          │
│      - Device ID match ✓           ┌─────────┴────────┐ │
│      - HAT verification ✓          │  Winbond SPI     │ │
│      - HULK co-processor ✓         │  W25Q16JWN       │ │
│                                    │  (1.8V, 2MB)     │ │
│    Result: SIGNATURE VALID ✓       │  Contains VBIOS  │ │
│                                    └──────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ② FWSEC UNLOCKS FALCON MICROCONTROLLERS                │
│                                                         │
│    Clears PRIV lockdown (SCTL[13:12] → 0)               │
│    Enables engine clocks via PMC_DEVICE_ENABLE           │
│    Host can now write to falcon IMEM/DMEM                │
│                                                         │
│    ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐              │
│    │ PMU  │  │ SEC2 │  │ GSP  │  │NVDEC │  ... more    │
│    │falcon│  │falcon│  │RISCV │  │falcon│              │
│    └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘              │
│       │UNLOCKED │UNLOCKED │UNLOCKED │UNLOCKED           │
└───────┼─────────┼─────────┼─────────┼───────────────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────┐
│  ③ DEVINIT (Hardware Initialization from VBIOS)         │
│                                                         │
│    Executes init scripts stored in VBIOS:               │
│    - Configure GDDR6 memory timing parameters           │
│    - Train memory controller (frequency, voltage)       │
│    - Set up PCIe link (16 GT/s x16)                     │
│    - Initialize display outputs                         │
│    - Configure power management                         │
│                                                         │
│    Result: GPU HARDWARE FULLY INITIALIZED ✓             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ④ GSP BOOT (GPU System Processor)                      │
│                                                         │
│    Host loads GSP firmware from /lib/firmware/ → GPU     │
│    GSP runs NVIDIA Resource Manager (RM 570.144)        │
│    Processes registry keys from host                    │
│    Manages all GPU subsystems                           │
│                                                         │
│    Result: GPU FULLY OPERATIONAL ✓                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  GPU WORKS          │
            │  - Display output   │
            │  - 3D acceleration  │
            │  - CUDA compute     │
            │  - Video decode     │
            └─────────────────────┘
```

## Our GPU (corrupted SPI flash)

```
┌─────────────────────────────────────────────────────────┐
│                    GPU POWERS ON                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ① FWSEC reads SPI flash...                             │
│                                                         │
│    Reads VBIOS from SPI ─────────────────┐              │
│                                          │              │
│                               ┌──────────┴────────────┐ │
│    ██████████████████████████  │  Winbond SPI          │ │
│    █ CORRUPTED DATA !!!!!! █  │  W25Q16JWN            │ │
│    █ Expected: 4E 56 47 49 █  │  DATA IS GARBAGE      │ │
│    █ Got:      6E 56 47 49 █  │  (partially erased/   │ │
│    █ Signature: INVALID    █  │   corrupted bytes)    │ │
│    ██████████████████████████  └───────────────────────┘ │
│                                                         │
│    ╔═══════════════════════════════════════════════╗     │
│    ║  FWSEC: SIGNATURE VERIFICATION FAILED        ║     │
│    ║  ALL FALCONS REMAIN LOCKED                   ║     │
│    ╚═══════════════════════════════════════════════╝     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  GPU IS DEAD        │
            │  - Windows: Code 43 │
            │  - Linux: -EINVAL   │
            │  - No display       │
            │  - No compute       │
            │  - 0 MB VRAM        │
            └─────────────────────┘
```

## The Circular Dependencies

```
  ┌───────────────────────────────────────────────────────┐
  │                                                       │
  │  DEPENDENCY LOOP 1: SPI ACCESS                        │
  │                                                       │
  │    Write to SPI flash                                 │
  │      └─► Need falcon with SPI access                  │
  │            └─► Need PRIV lockdown cleared              │
  │                  └─► Need FWSEC to verify VBIOS        │
  │                        └─► Need valid VBIOS on SPI ◄──┘
  │                                                       │
  │  DEPENDENCY LOOP 2: GSP BOOT                          │
  │                                                       │
  │    Boot the GSP processor                             │
  │      └─► Need VRAM for WPR region                     │
  │            └─► Need memory controller initialized      │
  │                  └─► Need DEVINIT scripts from VBIOS   │
  │                        └─► Need valid VBIOS on SPI ◄──┘
  │                                                       │
  │  DEPENDENCY LOOP 3: DRIVER LOADING                    │
  │                                                       │
  │    Load nouveau / NVIDIA driver                       │
  │      └─► Need to read VBIOS from hardware              │
  │            └─► 5 sources: PRAMIN, PROM, ACPI,          │
  │                           PCIROM, PLATFORM             │
  │                  └─► All return corrupt data ◄─────────┘
  │                                                       │
  └───────────────────────────────────────────────────────┘
```

## Three-Layer Falcon Lock System (Ampere)

```
  OUR GPU (power-on default)        WORKING GPU (after FWSEC)
  ══════════════════════════        ════════════════════════

  ┌─────────────────────┐          ┌─────────────────────┐
  │ Layer 1: CLOCK GATE │          │ Layer 1: CLOCK GATE │
  │ Status: GATED       │          │ Status: ENABLED     │
  │ Reads return: BADF  │          │ Reads: work         │
  │ Can't see registers │          │ Writes: work        │
  ├─────────────────────┤          ├─────────────────────┤
  │ Layer 2: PRIV LOCK  │          │ Layer 2: PRIV LOCK  │
  │ SCTL[13:12] = 3     │          │ SCTL[13:12] = 0     │
  │ Reads: work         │          │ Reads: work         │
  │ Writes: REJECTED    │          │ Writes: work        │
  ├─────────────────────┤          ├─────────────────────┤
  │ Layer 3: SCP LOCK   │          │ Layer 3: SCP LOCK   │
  │ Status: INACTIVE    │          │ Status: INACTIVE    │
  └─────────────────────┘          └─────────────────────┘
```

## VBIOS File Format Discovery

```
  NVGI Container (Razer.RTX3080.8192.210603.rom, 999,424 bytes)
  ══════════════════════════════════════════════════════════

  Offset 0x0000: ┌──────────────────────────────┐
                 │ 4E 56 47 49 42 03 24 80 ...  │  "NVGIB..."
                 │ NVGI Header (proprietary)     │  NOT standard 55 AA
                 ├──────────────────────────────┤
  Offset 0x2000: │ Second NVGI header            │
                 ├──────────────────────────────┤
  Offset 0x9400: │ 55 AA 7F EB 4B 37 ...       │  First PCI Option ROM
                 │ PCIR: Vendor 10DE            │  Legacy x86 init (63KB)
                 │       Device 24DC (correct!) │
                 ├──────────────────────────────┤
  Offset 0x19200:│ 55 AA C2 00 ...             │  EFI GOP driver (97KB)
                 ├──────────────────────────────┤
                 │ ... 10+ more sub-images ...  │  Config tables, etc.
                 └──────────────────────────────┘

  Key finding: nouveau expects 55 AA at offset 0. Our file has 4E 56 (NVGI).
  Patch 1 adds 0x564E (LE read of "NV") to the accepted signature list.
  Patch 2 skips PCIR validation (no PCIR at offset 0 in NVGI format).
```

## Patched Nouveau — How Deep We Got

```
  nouveau init flow                              Our patches
  ═══════════════                                ═══════════

  nvkm_device_pci_new
    └─► nvkm_device_ctor
          ├─► BIOS ctor: load firmware ─────────── Patch 1+2: accept NVGI
          │     "bios: version 32.4e.0a.1e.dd" ✓
          ├─► DEVINIT ctor ─────────────────────── Patch 5: non-fatal ctor
          ├─► other subdev ctors (some fail) ───── Patch 5: non-fatal ctor
          └─► nvkm_intr_install ────────────────── Patch 7: skip entirely
                (NULL deref on uninitialized
                 interrupt data)

    └─► nvkm_device_init
          ├─► nvkm_device_preinit ──────────────── Patch 3: skip entirely
          │     (DEVINIT x86 code on NX page +
          │      register writes timeout)
          ├─► BIOS init ✓
          ├─► other subdev init (some fail) ────── Patch 6: non-fatal init
          └─► GSP oneinit
                ├─► r535_gsp_rm_boot_ctor
                │     ├─► fwsec_sb_ctor ────────── Patch 4: survive failure
                │     ├─► fwsec_sb ─────────────── Patch 4: survive failure
                │     └─► fwsec_frts ───────────── Patch 4: survive failure
                └─► nvkm_mmu_vram ──────────────── WALL: VRAM not available
                      GPU memory controller
                      never initialized by
                      DEVINIT. No VRAM exists
                      for GSP's WPR region.

  Result: 8 patches, survived 6 crash points, hit hardware VRAM wall.
```

## Falcon Exploit Research (hexkyz technique)

```
  Based on "Je Ne Sais Quoi — Falcons over the Horizon" (hexkyz/SciresM)
  Same Falcon architecture as Nintendo Switch TSEC
  ══════════════════════════════════════════════════════════

  TECHNIQUE: Upload code to falcon IMEM via BAR0, start CPU

  ON SWITCH TSEC:                   ON OUR GPU (AMPERE):
  ─────────────                     ───────────────────

  IMEM writable from host ✓         IMEM write-locked by FWSEC
  Upload custom code ✓               Writes silently rejected
  Start falcon CPU ✓                 CPUCTL writes rejected
  Exploit BootROM (DMA race) ✓      Can't even load code

  PROBED VIA BAR0:
  ┌────────────┬──────────┬───────────────────────────┐
  │ Engine     │ Status   │ IMEM Write Test            │
  ├────────────┼──────────┼───────────────────────────┤
  │ PMU        │ Readable │ Write 0xCAFEBABE → read 0 │
  │ GSP        │ Readable │ Write 0xCAFEBABE → read 0 │
  │ SEC2       │ Readable │ Write 0xDEADBEEF → DEAD5EC2│
  │ FWSEC      │ GATED    │ Returns BADF3000          │
  └────────────┴──────────┴───────────────────────────┘
  SEC2 DMEM returns 0xDEAD5EC2 = "DEAD SEC2" (NVIDIA's locked marker)
```

## GSP RM Firmware Analysis

```
  gsp-570.144.bin (63MB, RISC-V 64-bit)
  ══════════════════════════════════════

  ┌──────────────────────────────────────────────────────┐
  │  Outer ELF wrapper                                   │
  │  ├── .fwimage (63MB) ────────────────────────────┐   │
  │  │   ├── Boot stubs (6 small ELFs, 48-180KB)    │   │
  │  │   ├── Main GSP RM (14.7MB) ◄── analyzed      │   │
  │  │   │   ├── CODE: VA 0x1000000 (13.45MB, RX)   │   │
  │  │   │   └── DATA: VA 0x4000000 (0.94MB, RW)    │   │
  │  │   └── LibOS kernel (45MB)                     │   │
  │  └── .fwsignature_ga10x (4KB, RSA signature)     │   │
  └──────────────────────────────────────────────────────┘

  DECOMPILED FUNCTIONS (Ghidra headless, RISC-V):
  ┌──────────────────────────────────────────────────────┐
  │ 0x010405F4  registry_read_full (18KB, 562 lines)     │
  │ 0x019B9AEC  registry_lookup (linked list + strcmp)    │
  │ 0x019B9B70  registry_set_dword (type dispatch)       │
  │ 0x019AC184  node_create (256-byte key limit, canary) │
  │ 0x019AD164  blob_processor (multi-part RPC + dispatch)│
  │ 0x019E67A4  entry_point (trampoline to main init)    │
  │ 0x019E6A1E  canary_handler (REGENERATES, doesn't halt)│
  │ 0x018543C4  mem_alloc (heap allocator)               │
  └──────────────────────────────────────────────────────┘

  357 registry keys found (126 security-related)
  All security keys fuse-gated on production silicon
```

## Alternative Hardware Approaches (theoretical)

```
  APPROACH 1: Voltage Glitching on FWSEC
  ═══════════════════════════════════════

  ┌──────────┐    glitch     ┌──────────────┐
  │ChipWhis- │───voltage────►│ FWSEC block  │
  │perer FPGA│   spike at    │ on GPU die   │
  │ ($250+)  │   comparison  │              │
  └──────────┘   instruction │ if(sig!=exp) │ ◄── glitch flips branch
                             │   LOCK ──────│──► UNLOCK (wrong path)
                             └──────────────┘
  Cost: $250+  Time: weeks  Risk: chip damage  Success: ~0.1%/try


  APPROACH 2: SPI Bus Man-in-the-Middle
  ═════════════════════════════════════

  Normal:  FWSEC ◄───► SPI Flash (corrupted) ──► FAIL

  Attack:  FWSEC ◄───► [Pi Pico proxy] ◄───► SPI Flash
                          │
                   Intercepts reads,
                   returns correct VBIOS
                   from local storage
                          │
                   FWSEC verifies ──► PASS ──► GPU unlocks

  Cost: $10 (Pico + level shifter)   Time: days   Risk: none
  Requires: custom PIO firmware for real-time SPI interception
```

## What We Tried (30+ methods)

```
  SESSION 1 (Ubuntu Live USB, 2026-03-30)
  ════════════════════════════════════════
  T01-T05: nvflash (standard, -6, --overridesub, combined) ──► EEPROM not found
  T06: sysfs ROM write ────────────────────────────────────► file too large
  T07-T08: PCI command register + FLR ─────────────────────► still EEPROM not found
  T09: BAR0 MMIO direct access ────────────────────────────► GPU alive, SPI gated
  T10: SPI register scan ──────────────────────────────────► all return BADF
  T11: PMC engine enable ──────────────────────────────────► register rejects writes
  T12: nvflash nomodeset bypass ───────────────────────────► not a cmdline issue
  T13: nouveau modeset=2 ─────────────────────────────────► 5 BIOS sources all fail
  T14: NVIDIA open driver 580 ─────────────────────────────► GSP needs VBIOS
  T15: PCIe secondary bus reset ───────────────────────────► "Falcon In HALT"
  T16: nvflash strace analysis ────────────────────────────► confirmed falcon path

  SESSION 2 (Windows, 2026-03-30)
  ════════════════════════════════
  T17: Razer BIOS update ──────────────────────────────────► GPU still Code 43

  SESSION 3 (Fedora 43, 2026-03-31)
  ══════════════════════════════════
  T18: ACPI table search ──────────────────────────────────► no _ROM method
  T19: PCI remove/rescan ──────────────────────────────────► same failure
  T20: envytools nvagetbios ───────────────────────────────► invalid signature
  T21: nvflash post-BIOS-update ───────────────────────────► same EEPROM error

  SESSION 4 (Fedora 43, deep research, 2026-03-31)
  ═════════════════════════════════════════════════
  T22: System BIOS MTD scan (12MB) ────────────────────────► no NVIDIA content
  T23: SMBus/I2C enumeration ──────────────────────────────► temp sensor only
  T24: VBIOS format analysis ──────────────────────────────► NVGI format discovered
  T25: BAR0 PROM write test ───────────────────────────────► hardware read-only
  T26: GSP RM registry keys ───────────────────────────────► fuse-gated
  T27: nouveau PLATFORM source ────────────────────────────► dead code in GSP mode
  T28: Custom kretprobe module ────────────────────────────► PCI core conflict
  T29: FWSEC security analysis ────────────────────────────► hardware crypto chain
  T30: Falcon IMEM/DMEM direct write ──────────────────────► PRIV write-locked
  T31: Patched nouveau (8 patches) ────────────────────────► reached VRAM wall
  T32: MODS/MATS diagnostic ───────────────────────────────► wrong version + needs VBIOS

  THE FIX
  ═══════
  CH341A + 1.8V adapter + SOP8 clip → direct SPI flash
  Bypasses GPU entirely. $20. 5 minutes. 95%+ success rate.
```
