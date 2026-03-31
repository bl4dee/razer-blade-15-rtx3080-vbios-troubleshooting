# GSP RM Exploit Research Methodology

## Setup

```bash
# Ghidra project is at:
/home/tech/ghidra_projects/GSP_RM/gsp_rm.elf

# Open in Ghidra GUI:
/home/tech/ghidra/ghidraRun

# Binary info:
#   Architecture: RISC-V 64-bit (RV64GC with compressed instructions)
#   CODE: VA 0x1000000 - 0x1D73000 (13.45MB)
#   DATA: VA 0x4000000 - 0x40F0000 (0.94MB)
#   Entry: 0x19E67A4
#   Compiled with: -fstack-protector (stack canaries present)
```

## The Three Leads

### Lead A: Registry Key Node Creation (GSP-side, HIGHEST priority)

**The opportunity:** When `NVreg_RegistryDwords` sends an unknown key=value pair to the GSP, the GSP's registry subsystem creates a new linked list node to store it. The node allocation and key name copy is the most likely place for a buffer overflow.

**What we know:**
- Registry lookup function: **VA 0x19B9AEC** (linked list traversal, case-insensitive strcmp)
- Registry set/add function: **VA 0x19B9B70** (calls lookup, then creates node if not found)
- Node creation function: **~VA 0x19AC184** (called from 0x19B9BD0 when key not found)
- Each linked list node has: `[next_ptr @ +0x00] [value @ +0x10] [type @ +0x18] [key_name @ +0x19]`

**In Ghidra:**
1. Go to `0x19B9B70` (the set/add function)
2. Follow the call at `0x19B9BD0` to the node creation function
3. Look for how the key name string is copied into the new node
4. **KEY QUESTION:** Is the node allocated with a fixed size? If so, what happens when the key name is longer than that fixed size?
5. Check if there's a `portMemCopy` or `portStringCopy` with the key name length — does it check against the node's allocated size?

**Testing:**
```bash
# Send a key name of exactly N bytes and check GSP mailbox/error state
sudo modprobe nouveau NVreg_RegistryDwords="$(python3 -c "print('R'*100 + '=1')")"
# Then check: sudo dmesg | tail -20
# Look for: different error messages, GSP crash indicators, changed PRIV_ERR_ADDR
```

### Lead B: Host-side VBIOS Parsing Bug (confirmed, reported to NVIDIA PSIRT)

A confirmed code defect was found in the open-source NVIDIA driver's VBIOS
parsing code. Details have been reported to NVIDIA PSIRT and are not included
in this public repository. See `/home/tech/NVIDIA_PSIRT_REPORT_DRAFT.md` for
the full report.

**File:** `src/nvidia/src/kernel/gpu/gsp/kernel_gsp_fwsec.c` in open-gpu-kernel-modules
**Trigger:** Corrupted VBIOS data on SPI flash

### Lead C: VBIOS Descriptor Parsing Attack Surface (HOST-side)

**The opportunity:** When the NVIDIA driver parses the corrupted VBIOS from SPI, the FWSEC parsing code uses values from the VBIOS descriptors to size memory allocations and copies. While the current code has `portSafeAddU32` guards, the error handling paths (`continue` to skip entries) leave room for subtle bugs.

**In the source code** (`kernel_gsp_fwsec.c`):
- `pDescV3->StoredSize` → used to size the main ucode allocation
- `pDescV3->IMEMLoadSize` → used in portMemCopy
- `pDescV3->DMEMLoadSize` → used in portMemCopy  
- `pDescV3->SignatureCount` → controls loop iteration count

**What to look for:**
- What if `SignatureCount` is extremely large? (integer overflow in total size calculation)
- What if error paths leave partially initialized structures?
- What if `portSafeAddU32` returns false but the code continues on a different path?

## General Ghidra Workflow

1. **Start with strings:** Window → Defined Strings. Filter for "Rm", "vbios", "spi"
2. **Follow xrefs:** Right-click any string → References → Show References To
3. **Name functions:** When you identify a function's purpose, rename it (press 'L')
4. **Mark up structs:** Create struct definitions for the linked list nodes
5. **Decompiler:** Press F5 on any function to see C pseudocode
6. **Call graph:** Right-click function → References → Show Call Trees

## Key Addresses to Start From

| Address | What | Why |
|---|---|---|
| `0x010405F4` | osReadRegistryDword | Entry point for all registry reads |
| `0x19B9AEC` | registryLookup | Linked list traversal with string compare |
| `0x19B9B70` | registrySetDword | Calls lookup, creates node if missing |
| `~0x19AC184` | registryCreateNode | Allocates node and copies key name — **PRIMARY TARGET** |
| `0x19E67A4` | entryPoint | GSP RM entry point |

## What Success Looks Like

If you find a buffer overflow in the node creation:
1. Craft a `NVreg_RegistryDwords` string with an oversized key name
2. The GSP RM's node allocator overflows into adjacent heap memory
3. Overwrite a function pointer or return address on the GSP's heap
4. Redirect execution to a SPI write gadget (or a ROP chain that writes to SPI)
5. The correct VBIOS gets written to SPI flash
6. Cold reboot → GPU works

The SPI write primitives exist in the GSP RM binary (search for strings containing "spi", "flash", "eeprom" to find them). You just need code execution to call them.
