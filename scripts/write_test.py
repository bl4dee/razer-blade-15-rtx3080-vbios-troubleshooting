#!/usr/bin/env python3
"""Test Page Program at various sizes to find where writes break down.
Uses flashrom's CH341A init (which works for detection) via subprocess,
then does raw SPI for the actual write test."""
import subprocess
import tempfile
import os
import sys

PADDED = "/home/blink/razer-vbios-recovery/padded_vbios.bin"

def flashrom_cmd(args):
    result = subprocess.run(
        ["flashrom", "-p", "ch341a_spi", "-c", "W25Q16.W"] + args,
        capture_output=True, text=True
    )
    return result.returncode, result.stdout + result.stderr

def main():
    target = open(PADDED, "rb").read()

    # Step 1: Erase using layout (skip bad sector)
    print("[1] Erasing VBIOS region (skipping bad sector)...")
    rc, out = flashrom_cmd([
        "--layout", "/home/blink/razer-vbios-recovery/layout.txt",
        "--include", "vbios_region", "-E"
    ])
    if rc != 0 and "ERASE FAILED" in out:
        print("    Erase reported failure — checking if it's just the bad sector...")
    print("    Erase command sent.")

    # Step 2: Verify the first sector is erased
    print("[2] Reading back first 4KB to verify erase...")
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        tmpfile = f.name
    rc, out = flashrom_cmd(["-r", tmpfile])
    if rc != 0:
        print(f"    Read failed: {out}")
        return

    readback = open(tmpfile, "rb").read()
    first_4k = readback[:4096]
    ff_count = sum(1 for b in first_4k if b == 0xFF)
    print(f"    First 4KB: {ff_count}/4096 bytes are 0xFF ({100*ff_count/4096:.1f}%)")
    if ff_count < 4090:
        print("    WARNING: First sector not fully erased!")
        print(f"    First 16 bytes: {' '.join(f'{b:02X}' for b in first_4k[:16])}")

    # Step 3: Write the target VBIOS using layout
    print("[3] Writing VBIOS via flashrom (layout, skip bad sector)...")
    rc, out = flashrom_cmd([
        "--layout", "/home/blink/razer-vbios-recovery/layout.txt",
        "--include", "vbios_region",
        "-w", PADDED
    ])
    print(f"    Exit code: {rc}")
    if "Verifying" in out:
        # Extract verify result
        for line in out.split('\n'):
            if "FAILED" in line or "VERIFIED" in line or "Verifying" in line:
                print(f"    {line.strip()}")

    # Step 4: Read back and compare
    print("[4] Reading back for analysis...")
    rc, out = flashrom_cmd(["-r", tmpfile])
    readback = open(tmpfile, "rb").read()

    vbios_len = 999424
    match = sum(1 for i in range(vbios_len) if readback[i] == target[i])
    ff = sum(1 for i in range(vbios_len) if readback[i] == 0xFF)
    non_ff = vbios_len - ff

    # Byte-by-byte analysis for first 256 bytes (first page)
    page0_match = sum(1 for i in range(256) if readback[i] == target[i])
    page0_ff = sum(1 for i in range(256) if readback[i] == 0xFF)

    # Check pages at different offsets
    print()
    print("=== Write Analysis ===")
    print(f"  Overall VBIOS match: {match}/{vbios_len} ({100*match/vbios_len:.1f}%)")
    print(f"  0xFF in VBIOS region: {ff} ({100*ff/vbios_len:.1f}%)")
    print(f"  Non-0xFF bytes landed: {non_ff}")
    print()
    print("  Per-page analysis (first 16 pages, 256 bytes each):")
    for page in range(16):
        start = page * 256
        end = start + 256
        p_match = sum(1 for i in range(start, end) if readback[i] == target[i])
        p_ff = sum(1 for i in range(start, end) if readback[i] == 0xFF)
        p_landed = 256 - p_ff
        status = "FULL" if p_match == 256 else f"{p_landed} bytes landed"
        print(f"    Page {page:3d} (0x{start:06X}): {p_match}/256 match, {status}")

    print()
    print("  First 32 bytes on chip:", " ".join(f"{b:02X}" for b in readback[:32]))
    print("  First 32 bytes target: ", " ".join(f"{b:02X}" for b in target[:32]))

    # Check if WEL (Write Enable Latch) is being set
    print()
    print("  Checking status register after write attempt...")
    # Use flashrom to read SR
    rc, out = flashrom_cmd(["-VVV", "-r", "/dev/null"])
    for line in out.split('\n'):
        if 'status register' in line.lower() or 'spi_read_register' in line.lower():
            print(f"    {line.strip()}")

    os.unlink(tmpfile)

if __name__ == "__main__":
    main()
