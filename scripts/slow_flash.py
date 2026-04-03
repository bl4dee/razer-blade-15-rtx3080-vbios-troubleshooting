#!/usr/bin/env python3
"""Slow byte-by-byte VBIOS flash for flaky 1.8V adapter connections"""
import usb.core
import usb.util
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
SPI_SECTOR_ERASE  = 0x20
SPI_PAGE_PROGRAM  = 0x02
SPI_READ_DATA     = 0x03

BULK_EP_OUT = 0x02
BULK_EP_IN  = 0x82

CHIP_SIZE = 2 * 1024 * 1024
SECTOR_SIZE = 4096
BAD_SECTOR_ADDR = 0x111000
WRITE_CHUNK = 16  # Write only 16 bytes at a time

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
    cfg = dev.get_active_configuration()
    intf = cfg[(0,0)]
    usb.util.claim_interface(dev, intf)

    # Initialize CH341A for SPI mode (based on IMSProg's ch341a.c)
    try:
        dev.ctrl_transfer(0x40, 0x5A, 0, 0, None, 1000)  # init
        time.sleep(0.05)
        dev.ctrl_transfer(0x40, 0xA1, 0, 0, None, 1000)  # configure
        time.sleep(0.05)
        dev.ctrl_transfer(0x40, 0xA4, 0, 1, None, 1000)  # setStream speed=1 (slow)
        time.sleep(0.05)
        # Set CS high, pin directions
        cmd = bytearray([CH341A_CMD_UIO_STREAM,
                         CH341A_CMD_UIO_STM_OUT | 0x37,
                         CH341A_CMD_UIO_STM_DIR | 0x3F,
                         CH341A_CMD_UIO_STM_END])
        dev.write(BULK_EP_OUT, cmd)
        time.sleep(0.02)
        print("  CH341A initialized for SPI mode")
    except Exception as e:
        print(f"  Warning during init: {e} (continuing anyway)")

    return dev

def cs_low(dev):
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x36, CH341A_CMD_UIO_STM_DIR | 0x3F, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)

def cs_high(dev):
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x37, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)

def spi_transfer(dev, data):
    cs_low(dev)
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
        if not (resp[1] & 0x01):
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

def program_small(dev, addr, data):
    """Program a small chunk (<=16 bytes) at a time"""
    assert len(data) <= WRITE_CHUNK
    write_enable(dev)
    a2 = (addr >> 16) & 0xFF
    a1 = (addr >> 8) & 0xFF
    a0 = addr & 0xFF
    spi_transfer(dev, [SPI_PAGE_PROGRAM, a2, a1, a0] + list(data))
    return wait_busy(dev, timeout=5)

def main():
    if len(sys.argv) < 2:
        print("Usage: slow_flash.py <firmware.bin>")
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        firmware = f.read()

    if len(firmware) != CHIP_SIZE:
        print(f"ERROR: File must be {CHIP_SIZE} bytes, got {len(firmware)}")
        sys.exit(1)

    dev = find_ch341a()
    print("CH341A found!")

    # Detect chip with retries
    print("Waiting for chip...")
    for attempt in range(30):
        resp = spi_transfer(dev, [0x9F, 0, 0, 0])
        jedec = f"{resp[1]:02X} {resp[2]:02X} {resp[3]:02X}"
        if jedec == "EF 60 15":
            print(f"JEDEC ID: {jedec} — W25Q16JW detected!")
            break
        time.sleep(1)
        if attempt % 5 == 4:
            print(f"  Attempt {attempt+1}/30 - got {jedec}, retrying...")
    else:
        print(f"ERROR: Chip not detected after 30 attempts (last: {jedec})")
        sys.exit(1)

    total_sectors = CHIP_SIZE // SECTOR_SIZE
    bad_sector_idx = BAD_SECTOR_ADDR // SECTOR_SIZE

    # Step 1: Erase sectors (skip bad one)
    print(f"\n=== ERASING (skipping sector {bad_sector_idx} @ 0x{BAD_SECTOR_ADDR:06X}) ===")
    for i in range(total_sectors):
        addr = i * SECTOR_SIZE
        if addr == BAD_SECTOR_ADDR:
            sys.stdout.write(f"\r  Sector {i}/{total_sectors}: SKIP (bad)          ")
            continue
        if not erase_sector(dev, addr):
            print(f"\n  Sector {i} @ 0x{addr:06X}: ERASE TIMEOUT!")
            sys.exit(1)
        if i % 16 == 0:
            sys.stdout.write(f"\r  Sector {i}/{total_sectors} erased...          ")
            sys.stdout.flush()
    print(f"\r  All {total_sectors - 1} sectors erased!              ")

    # Step 2: Program in small chunks
    print(f"\n=== PROGRAMMING ({WRITE_CHUNK} bytes at a time — this will be slow) ===")
    chunks_written = 0
    chunks_skipped = 0
    total_chunks = CHIP_SIZE // WRITE_CHUNK
    errors = 0
    start_time = time.time()

    for offset in range(0, CHIP_SIZE, WRITE_CHUNK):
        chunk_data = firmware[offset:offset + WRITE_CHUNK]

        # Skip all-FF chunks
        if chunk_data == b'\xff' * len(chunk_data):
            chunks_skipped += 1
            chunks_written += 1
            continue

        # Skip bad sector
        if BAD_SECTOR_ADDR <= offset < BAD_SECTOR_ADDR + SECTOR_SIZE:
            chunks_skipped += 1
            chunks_written += 1
            continue

        # Write chunk
        if not program_small(dev, offset, chunk_data):
            print(f"\n  TIMEOUT at 0x{offset:06X}!")
            errors += 1
            continue

        # Verify this chunk immediately
        readback = read_data(dev, offset, len(chunk_data))
        if readback != chunk_data:
            # Retry once
            time.sleep(0.01)
            program_small(dev, offset, chunk_data)
            time.sleep(0.01)
            readback = read_data(dev, offset, len(chunk_data))
            if readback != chunk_data:
                errors += 1
                if errors <= 10:
                    print(f"\n  MISMATCH at 0x{offset:06X}: wrote {chunk_data[:4].hex()}, read {readback[:4].hex()}")

        chunks_written += 1
        if chunks_written % 1024 == 0:
            elapsed = time.time() - start_time
            pct = chunks_written * 100 // total_chunks
            rate = chunks_written / elapsed if elapsed > 0 else 0
            eta = (total_chunks - chunks_written) / rate if rate > 0 else 0
            sys.stdout.write(f"\r  {pct}% — {chunks_written}/{total_chunks} chunks, {errors} errors, ETA {eta:.0f}s   ")
            sys.stdout.flush()

    elapsed = time.time() - start_time
    print(f"\r  Programming complete! {chunks_written} chunks in {elapsed:.1f}s, {chunks_skipped} skipped (0xFF), {errors} errors")

    # Step 3: Final verify
    print(f"\n=== FINAL VERIFICATION ===")
    verify_errors = 0
    for offset in range(0, CHIP_SIZE, 256):
        if BAD_SECTOR_ADDR <= offset < BAD_SECTOR_ADDR + SECTOR_SIZE:
            continue
        expected = firmware[offset:offset + 256]
        actual = read_data(dev, offset, 256)
        for i in range(256):
            if actual[i] != expected[i]:
                verify_errors += 1
                if verify_errors <= 20:
                    print(f"  0x{offset+i:06X}: expected 0x{expected[i]:02X}, got 0x{actual[i]:02X}")
        if (offset // 256) % 512 == 0:
            sys.stdout.write(f"\r  Verified {offset * 100 // CHIP_SIZE}%...          ")
            sys.stdout.flush()

    print(f"\r                                          ")
    print(f"\n=== RESULT ===")
    if verify_errors == 0:
        print("SUCCESS! VBIOS written and verified perfectly!")
    elif verify_errors <= 5:
        print(f"MOSTLY OK: {verify_errors} byte(s) differ — likely read glitches. GPU should boot.")
    else:
        print(f"FAILED: {verify_errors} bytes differ")

    if verify_errors <= 5:
        print("\nNext steps:")
        print("  1. Remove SOP8 clip")
        print("  2. Reconnect battery (orange latch)")
        print("  3. Reassemble laptop")
        print("  4. Boot and check GPU-Z")

if __name__ == "__main__":
    main()
