# Nouveau Kernel Module Patches for VBIOS Recovery

These patches modify the Linux nouveau driver (kernel 6.19) to load a GPU VBIOS
from a firmware file instead of requiring it from the GPU's corrupted SPI flash.

## The Patches

### 001-accept-nvgi-le-signature.patch
Adds `case 0x564e` (little-endian "NV") to the accepted ROM signatures in
`nvkm/subdev/bios/image.c`. Modern NVIDIA VBIOS files use the NVGI container
format which starts with bytes `4E 56 47 49` ("NVGI"). When read as a 16-bit
LE value, this produces `0x564E`, which the stock driver doesn't recognize.

### 002-firmware-no-pcir-validation.patch
Modifies `shadow_fw` in `nvkm/subdev/bios/shadow.c` to set `no_pcir = true`
and `ignore_checksum = true`. The NVGI format doesn't have a standard PCI ROM
data structure (PCIR) at the expected offset — the PCIR is inside a sub-image
at offset 0x9400. This patch skips PCIR validation for firmware-loaded VBIOS.

### 003-skip-preinit-failure.patch
Changes `nvkm/engine/device/base.c` to continue initialization even when
preinit (DEVINIT scripts) fails. On a GPU with corrupted SPI VBIOS, FWSEC
hasn't unlocked the hardware, so DEVINIT register writes timeout (-ETIMEDOUT).
Without this patch, the timeout aborts the entire init and prevents GSP boot.

## How to Use

```bash
# 1. Get kernel 6.19 nouveau source
curl -sL "https://github.com/torvalds/linux/archive/refs/tags/v6.19.tar.gz" | \
    tar xzf - --strip-components=4 "linux-6.19/drivers/gpu/drm/nouveau/"

# 2. Apply patches
cd nouveau
for p in /path/to/patches/0*.patch; do
    patch -p0 < "$p"
done

# 3. Build
make -C /usr/src/kernels/$(uname -r) M=$(pwd) CONFIG_DRM_NOUVEAU=m modules

# 4. Place VBIOS file
sudo cp YourVBIOS.rom /lib/firmware/nvvbios.rom

# 5. Load
sudo modprobe mxm_wmi
sudo insmod nouveau.ko config=NvBios=nvvbios.rom
```

## Results So Far

With patches 001+002, nouveau successfully:
- Loaded VBIOS from `/lib/firmware/nvvbios.rom` via `request_firmware()`
- Parsed the NVGI container format
- Found the BIT (BIOS Information Table) header
- Detected VBIOS version `32.4e.0a.1e.dd`
- Scored the firmware source as 4 (valid)

Preinit (DEVINIT scripts) timed out with -110 because FWSEC hasn't unlocked
GPU register access. Patch 003 skips this failure to allow GSP boot to proceed.

**Status: Testing patch 003 (requires clean reboot after previous kernel oops)**
