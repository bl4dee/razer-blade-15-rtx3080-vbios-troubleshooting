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
│      • Digital signature ✓                    │          │
│      • Certificate chain ✓                    │          │
│      • Device ID match ✓           ┌─────────┴────────┐ │
│      • HAT verification ✓          │  Winbond SPI     │ │
│      • HULK co-processor ✓         │  W25Q16JWN       │ │
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
│    • Configure GDDR6 memory timing parameters           │
│    • Train memory controller (frequency, voltage)       │
│    • Set up PCIe link (16 GT/s x16)                     │
│    • Initialize display outputs                         │
│    • Configure power management                         │
│                                                         │
│    Result: GPU HARDWARE FULLY INITIALIZED ✓             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ④ GSP BOOT (GPU System Processor)                      │
│                                                         │
│    Host loads GSP firmware from /lib/firmware/ ──► GPU   │
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
            │  • Display output   │
            │  • 3D acceleration  │
            │  • CUDA compute     │
            │  • Video decode     │
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
│    ║  FWSEC: SIGNATURE VERIFICATION FAILED ✗      ║     │
│    ║  → ALL FALCONS REMAIN LOCKED                 ║     │
│    ╚═══════════════════════════════════════════════╝     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ② EVERYTHING STAYS LOCKED                              │
│                                                         │
│    PRIV lockdown: LEVEL 3 (maximum)                     │
│    Engine clocks: DISABLED                              │
│    All host writes to falcon registers: REJECTED        │
│                                                         │
│    ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐              │
│    │ PMU  │  │ SEC2 │  │ GSP  │  │NVDEC │              │
│    │falcon│  │falcon│  │RISCV │  │falcon│              │
│    └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘              │
│       │ HALTED  │ HALTED  │ HALTED  │ HALTED            │
│       │ LOCKED  │ LOCKED  │ LOCKED  │ LOCKED            │
│       │ 🔒      │ 🔒      │ 🔒      │ 🔒               │
└───────┼─────────┼─────────┼─────────┼───────────────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────┐
│  ③ DEVINIT: CANNOT RUN                                  │
│                                                         │
│    No falcon available to execute init scripts           │
│    GDDR6 memory: UNTRAINED (no timing config)           │
│    PCIe link: DEGRADED (2.5 GT/s x8 instead of 16x16)  │
│    Memory controller: IN RESET                          │
│    VRAM: INACCESSIBLE                                   │
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  ④ GSP BOOT: IMPOSSIBLE                                 │
│                                                         │
│    GSP firmware loads from filesystem ✓                  │
│    But GSP needs VRAM for WPR (Write Protected Region)  │
│    VRAM not available (memory controller in reset)      │
│    GSP cannot allocate working memory → FAILS           │
│                                                         │
│    Also: nouveau driver can't read VBIOS from hardware  │
│    All 5 sources return corrupt/empty data:             │
│    PRAMIN ✗  PROM ✗  ACPI ✗  PCIROM ✗  PLATFORM ✗     │
│                                                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  GPU IS DEAD        │
            │  • Windows: Code 43 │
            │  • Linux: -EINVAL   │
            │  • No display       │
            │  • No compute       │
            │  • 0 MB VRAM        │
            └─────────────────────┘
```

## The Circular Dependencies (why software can't fix it)

```
    ┌──────────────────────────────────────────────────┐
    │                                                  │
    │   To write to SPI flash:                         │
    │     → Need falcon with SPI access                │
    │       → Need PRIV lockdown cleared               │
    │         → Need FWSEC to verify VBIOS             │
    │           → Need valid VBIOS on SPI flash ◄──────┤
    │                                                  │
    │   To boot GSP:                                   │
    │     → Need VRAM for WPR region                   │
    │       → Need memory controller initialized       │
    │         → Need DEVINIT scripts from VBIOS        │
    │           → Need valid VBIOS on SPI flash ◄──────┤
    │                                                  │
    │   To load VBIOS from file (our patches):         │
    │     → Nouveau accepts file ✓ (patches 1+2)      │
    │     → Skips preinit ✓ (patch 3)                 │
    │     → Survives FWSEC failure ✓ (patches 4-7)    │
    │     → Hits VRAM allocation ✗ (patch 8 needed)   │
    │       → VRAM needs hardware init ◄───────────────┤
    │                                                  │
    └──────────────────────────────────────────────────┘

                    ╔═════════════╗
                    ║  SOLUTION:  ║
                    ╚══════╤══════╝
                           │
                           ▼
    ┌──────────────────────────────────────────────────┐
    │                                                  │
    │   CH341A USB SPI Programmer + 1.8V Adapter       │
    │                                                  │
    │   Connects DIRECTLY to the SPI flash chip        │
    │   Bypasses the GPU entirely                      │
    │   Writes correct VBIOS to the Winbond chip       │
    │                                                  │
    │   ┌─────────┐     SPI bus      ┌─────────────┐  │
    │   │ CH341A  │ ═══════════════► │ W25Q16JWN   │  │
    │   │ USB     │  MOSI/MISO/CLK   │ SPI Flash   │  │
    │   │ to PC   │  (1.8V via       │ on GPU PCB  │  │
    │   │         │   adapter)       │             │  │
    │   └─────────┘                  └─────────────┘  │
    │                                                  │
    │   GPU doesn't even know it's happening.          │
    │   No falcons, no FWSEC, no drivers needed.       │
    │                                                  │
    └──────────────────────────────────────────────────┘
```

## Three-Layer Lock System on Ampere Falcons

```
  POWER-ON STATE                    NORMAL (after FWSEC)
  ══════════════                    ════════════════════

  ┌─────────────────────┐          ┌─────────────────────┐
  │ Layer 1: CLOCK GATE │          │ Layer 1: CLOCK GATE │
  │ Status: GATED (BADF)│          │ Status: ENABLED ✓   │
  │ Registers: BADF5040 │          │ Registers: readable │
  │ Can't even read regs│          │ and writable        │
  ├─────────────────────┤          ├─────────────────────┤
  │ Layer 2: PRIV LOCK  │          │ Layer 2: PRIV LOCK  │
  │ SCTL[13:12] = 3     │          │ SCTL[13:12] = 0     │
  │ Host reads: work    │          │ Host reads: work    │
  │ Host writes: BLOCKED│          │ Host writes: work ✓ │
  │ Can't load IMEM code│          │ Can load IMEM code  │
  ├─────────────────────┤          ├─────────────────────┤
  │ Layer 3: SCP HS LOCK│          │ Layer 3: SCP HS LOCK│
  │ Status: INACTIVE    │          │ Status: INACTIVE    │
  │ (only during secure │          │ (only during secure │
  │  code execution)    │          │  code execution)    │
  └─────────────────────┘          └─────────────────────┘
        ▲                                ▲
        │                                │
    OUR GPU                         WORKING GPU
```

## What We Tried (30 methods across 4 sessions)

```
  SOFTWARE APPROACHES (all failed — blocked by FWSEC)
  ═══════════════════════════════════════════════════

  nvflash (5 variations) ──────────────────────► falcon HALTED
  sysfs ROM write ─────────────────────────────► ROM BAR too small
  NVIDIA open driver ──────────────────────────► GSP needs VBIOS
  nouveau (5 BIOS sources) ────────────────────► all corrupt/empty
  BAR0 register manipulation ──────────────────► PMC_ENABLE locked
  PCIe bus reset ──────────────────────────────► falcon stays HALTED
  ACPI _ROM method ────────────────────────────► doesn't exist
  System BIOS scan (MTD) ──────────────────────► no embedded VBIOS
  SMBus/I2C scan ──────────────────────────────► no GPU interface
  GSP RM registry keys ────────────────────────► fuse-gated on production
  Custom kretprobe module ─────────────────────► PCI core interference
  Falcon IMEM direct write ────────────────────► PRIV write-locked
  PROM window write ───────────────────────────► hardware read-only
  Patched nouveau (8 patches) ─────────────────► reached VRAM wall

  HARDWARE APPROACH (the fix)
  ═══════════════════════════

  CH341A + 1.8V adapter + SOP8 clip
    │
    ├── Talks directly to SPI chip (bypasses GPU)
    ├── flashrom -p ch341a_spi -w padded.bin
    ├── 5 minutes, $20
    └── 95%+ success rate
```
