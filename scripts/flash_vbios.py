#!/usr/bin/env python3
"""Flash VBIOS to W25Q16JW via CH341A, skipping bad sector at 0x111000"""
import usb.core
import usb.util
import struct
import time
import sys

CH341_VID = 0x1a86
CH341_PID = 0x5512

CH341A_CMD_SPI_STREAM = 0xA8
CH341A_CMD_UIO_STREAM = 0xAB
CH341A_CMD_UIO_STM_OUT = 0x80
CH341A_CMD_UIO_STM_DIR = 0x40
CH341A_CMD_UIO_STM_END = 0x20

SPI_WRITE_ENABLE  = 0x06
SPI_READ_SR1      = 0x05
SPI_SECTOR_ERASE  = 0x20  # 4KB sector erase
SPI_PAGE_PROGRAM  = 0x02
SPI_READ_DATA     = 0x03

BULK_EP_OUT = 0x02
BULK_EP_IN  = 0x82

CHIP_SIZE = 2 * 1024 * 1024  # 2MB
SECTOR_SIZE = 4096           # 4KB
PAGE_SIZE = 256
BAD_SECTOR_ADDR = 0x111000

def find_ch341a():
    dev = usb.core.find(idVendor=CH341_VID, idProduct=CH341_PID)
    if dev is None:
        print("ERROR: CH341A not found")
        sys.exit(1)
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except:
        pass
    dev.set_configuration()
    return dev

def cs_low(dev):
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x36, CH341A_CMD_UIO_STM_DIR | 0x3F, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)

def cs_high(dev):
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x37, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)

def spi_transfer(dev, data):
    cs_low(dev)
    # CH341A SPI stream max payload is typically 32 bytes at a time
    result = bytearray()
    remaining = list(data)
    while remaining:
        chunk = remaining[:32]
        remaining = remaining[32:]
        pkt = bytearray([CH341A_CMD_SPI_STREAM]) + bytearray(chunk)
        dev.write(BULK_EP_OUT, pkt)
        resp = dev.read(BULK_EP_IN, len(chunk), timeout=5000)
        result.extend(resp)
    cs_high(dev)
    return bytes(result)

def write_enable(dev):
    spi_transfer(dev, [SPI_WRITE_ENABLE])

def wait_busy(dev, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        cs_low(dev)
        pkt = bytearray([CH341A_CMD_SPI_STREAM, SPI_READ_SR1, 0x00])
        dev.write(BULK_EP_OUT, pkt)
        resp = dev.read(BULK_EP_IN, 2, timeout=5000)
        cs_high(dev)
        if not (resp[1] & 0x01):  # BUSY bit clear
            return True
        time.sleep(0.001)
    return False

def erase_sector(dev, addr):
    write_enable(dev)
    a2 = (addr >> 16) & 0xFF
    a1 = (addr >> 8) & 0xFF
    a0 = addr & 0xFF
    spi_transfer(dev, [SPI_SECTOR_ERASE, a2, a1, a0])
    return wait_busy(dev, timeout=10)

def read_data(dev, addr, length):
    a2 = (addr >> 16) & 0xFF
    a1 = (addr >> 8) & 0xFF
    a0 = addr & 0xFF
    cmd = [SPI_READ_DATA, a2, a1, a0] + [0x00] * length
    resp = spi_transfer(dev, cmd)
    return bytes(resp[4:])

def program_page(dev, addr, data):
    assert len(data) <= PAGE_SIZE
    write_enable(dev)
    a2 = (addr >> 16) & 0xFF
    a1 = (addr >> 8) & 0xFF
    a0 = addr & 0xFF
    cmd = [SPI_PAGE_PROGRAM, a2, a1, a0] + list(data)
    spi_transfer(dev, cmd)
    return wait_busy(dev, timeout=5)

def main():
    if len(sys.argv) < 2:
        print("Usage: flash_vbios.py <firmware.bin>")
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        firmware = f.read()

    if len(firmware) != CHIP_SIZE:
        print(f"ERROR: File must be {CHIP_SIZE} bytes, got {len(firmware)}")
        sys.exit(1)

    dev = find_ch341a()
    print("CH341A found!")

    # Verify chip ID with retries
    print("Waiting for chip detection (reseat clip if needed)...")
    for attempt in range(60):
        resp = spi_transfer(dev, [0x9F, 0, 0, 0])
        jedec = f"{resp[1]:02X} {resp[2]:02X} {resp[3]:02X}"
        if jedec == "EF 60 15":
            print(f"JEDEC ID: {jedec} — chip detected!")
            break
        time.sleep(1)
    else:
        print(f"ERROR: Could not detect W25Q16JW after 60 attempts (last: {jedec})")
        sys.exit(1)

    total_sectors = CHIP_SIZE // SECTOR_SIZE
    bad_sector_num = BAD_SECTOR_ADDR // SECTOR_SIZE

    # Step 1: Erase all sectors except bad one
    print(f"\n=== ERASING {total_sectors - 1} sectors (skipping sector {bad_sector_num} at 0x{BAD_SECTOR_ADDR:06X}) ===")
    for i in range(total_sectors):
        addr = i * SECTOR_SIZE
        if addr == BAD_SECTOR_ADDR:
            print(f"  Sector {i:3d} @ 0x{addr:06X}: SKIPPING (bad sector)")
            continue
        if not erase_sector(dev, addr):
            print(f"  Sector {i:3d} @ 0x{addr:06X}: ERASE TIMEOUT!")
            sys.exit(1)
        if i % 32 == 0:
            print(f"  Sector {i:3d}/{total_sectors} @ 0x{addr:06X}: erased")

    print("Erase complete!")

    # Step 2: Verify erase (spot check)
    print("\n=== VERIFY ERASE (spot check) ===")
    for check_addr in [0x000000, 0x010000, 0x050000, 0x0F0000, 0x100000, 0x112000, 0x1F0000]:
        data = read_data(dev, check_addr, 16)
        if data == b'\xff' * 16:
            print(f"  0x{check_addr:06X}: OK (0xFF)")
        else:
            print(f"  0x{check_addr:06X}: NOT ERASED: {data.hex()}")

    # Step 3: Program
    print(f"\n=== PROGRAMMING {CHIP_SIZE} bytes ===")
    pages_written = 0
    total_pages = CHIP_SIZE // PAGE_SIZE
    for offset in range(0, CHIP_SIZE, PAGE_SIZE):
        page_data = firmware[offset:offset + PAGE_SIZE]
        # Skip pages that are all 0xFF (already erased)
        if page_data == b'\xff' * PAGE_SIZE:
            pages_written += 1
            continue
        # Skip the bad sector
        if BAD_SECTOR_ADDR <= offset < BAD_SECTOR_ADDR + SECTOR_SIZE:
            pages_written += 1
            continue
        if not program_page(dev, offset, page_data):
            print(f"  PROGRAM TIMEOUT at 0x{offset:06X}!")
            sys.exit(1)
        pages_written += 1
        if pages_written % 256 == 0:
            pct = pages_written * 100 // total_pages
            print(f"  {pct}% ({pages_written}/{total_pages} pages)")

    print("Programming complete!")

    # Step 4: Verify
    print(f"\n=== VERIFYING ===")
    errors = 0
    for offset in range(0, CHIP_SIZE, PAGE_SIZE):
        # Skip bad sector
        if BAD_SECTOR_ADDR <= offset < BAD_SECTOR_ADDR + SECTOR_SIZE:
            continue
        expected = firmware[offset:offset + PAGE_SIZE]
        actual = read_data(dev, offset, PAGE_SIZE)
        if actual != expected:
            for i in range(PAGE_SIZE):
                if actual[i] != expected[i]:
                    if errors < 20:
                        print(f"  MISMATCH at 0x{offset+i:06X}: expected 0x{expected[i]:02X}, got 0x{actual[i]:02X}")
                    errors += 1
        if (offset // PAGE_SIZE) % 512 == 0:
            pct = (offset * 100) // CHIP_SIZE
            print(f"  Verified {pct}%...")

    print(f"\n=== RESULT ===")
    if errors == 0:
        print("SUCCESS! VBIOS flashed and verified perfectly!")
        print("\nNext steps:")
        print("  1. Remove the SOP8 clip")
        print("  2. Reconnect battery (orange latch)")
        print("  3. Reassemble laptop")
        print("  4. Boot and check GPU-Z")
    else:
        print(f"FAILED: {errors} byte mismatches")
        print("Try running again — connection may be unstable")

if __name__ == "__main__":
    main()
