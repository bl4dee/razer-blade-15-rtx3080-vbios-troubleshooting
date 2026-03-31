# Nouveau Patches for VBIOS Recovery (v5 — 8 patches across 5 files)

## Patches (apply to Linux kernel 6.19 nouveau source)

| File | Patch | Purpose |
|---|---|---|
| `image.patch` | Accept 0x564E (LE "NV") signature | NVGI format VBIOS files start with "NV" in LE |
| `shadow.patch` | Skip PCIR/checksum for firmware source | NVGI container has no standard PCIR at offset 0 |
| `base.patch` | Skip preinit, non-fatal ctor/init/intr | DEVINIT hits NX page + FWSEC timeout; all errors non-fatal |
| `gsp.patch` | Survive fwsec_sb_ctor failure | FWSEC can't verify VBIOS from corrupted SPI |
| `fwsec.patch` | Survive fwsec_init failures | Multiple FWSEC calls patched to continue on error |
| `tu102.patch` | Survive fwsec_sb/frts/sb_init failures | All FWSEC calls in Turing+ GSP init path non-fatal |

**Note:** `tu102.patch` not generated yet — the tu102.c changes need fresh diff.

## Test Results

| Version | Patches | Result |
|---|---|---|
| v1 | sig only | `ROM signature (564e) unknown` — signature not recognized |
| v2 | sig + no_pcir | `scored 4, using image from nvvbios.rom` — **VBIOS accepted!** BIT found, version detected. Preinit NX crash. |
| v3 | +skip_preinit +fwsec_survive | `skipping preinit` — reached nvkm_gsp_fwsec_init! OOB warnings + fwsec failure survived. NULL deref in fwsec_frts. |
| v4 | +ctor_nonfatal | nvkm_intr_install returning -22 blocked ctor. |
| v5 | +intr_nonfatal +init_nonfatal +tu102_fwsec | Got through ctor→init→preinit→fwsec_init→fwsec_frts. Kernel tainted from earlier oops prevents clean test. |

## Next Step

Reboot for clean kernel, then:
```bash
sudo modprobe mxm_wmi
sudo insmod /home/tech/nouveau-patched-v5.ko config=NvBios=nvvbios.rom
sudo dmesg | tail -60
```

If more NULL derefs, add more survival patches. The goal: reach `r535_gsp_rpc_set_registry` (GSP boot + registry RPC).

## Pre-built Module

`/home/tech/nouveau-patched-v5.ko` (239MB, not in git — too large)
