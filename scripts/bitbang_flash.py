#!/usr/bin/env python3
"""Bit-bang SPI via CH341A UIO GPIO — bypasses broken SPI stream MOSI buffer.

CH341A pin mapping (from flashrom CS# toggle analysis):
  D0 (bit 0, 0x01): CS# (0=selected, 1=deselected)
  D1 (bit 1, 0x02): always 1
  D2 (bit 2, 0x04): always 1
  D3 (bit 3, 0x08): SCK (SPI clock)
  D4 (bit 4, 0x10): always 1
  D5 (bit 5, 0x20): MOSI (SPI data out)
  D7 (input):       MISO (SPI data in)

SPI Mode 0 (CPOL=0, CPHA=0): chip samples MOSI on rising edge of SCK.
"""
import usb.core, usb.util, time, sys, os

EP_OUT, EP_IN = 0x02, 0x82
# Base value: D1=1, D2=1, D4=1 always on
BASE = 0x16  # 0b010110
CS_BIT = 0x01   # D0
SCK_BIT = 0x08  # D3
MOSI_BIT = 0x20 # D5

UIO_STREAM = 0xAB
UIO_STM_OUT = 0x80
UIO_STM_DIR = 0x40
UIO_STM_END = 0x20
UIO_STM_IN = 0x00

def find_ch341a():
    dev = usb.core.find(idVendor=0x1a86, idProduct=0x5512)
    if dev is None: print("ERROR: CH341A not found"); sys.exit(1)
    try:
        if dev.is_kernel_driver_active(0): dev.detach_kernel_driver(0)
    except: pass
    dev.set_configuration()
    return dev

# Standard SPI stream for short commands
def reverse_bit(b):
    r = 0
    for i in range(8): r = (r << 1) | (b & 1); b >>= 1
    return r
def rev(data): return bytes(reverse_bit(b) for b in data)

def spi_stream(dev, mosi):
    rd = rev(mosi)
    uio = bytearray([UIO_STREAM, UIO_STM_OUT|0x37, UIO_STM_OUT|0x37, UIO_STM_OUT|0x37, UIO_STM_OUT|0x36, UIO_STM_END])
    uio.extend([0x00] * (32 - len(uio)))
    dev.write(EP_OUT, bytes(uio) + bytes([0xA8]) + rd)
    try: resp = dev.read(EP_IN, max(len(mosi), 32), timeout=2000)
    except: return bytes(len(mosi))
    dev.write(EP_OUT, bytes([UIO_STREAM, UIO_STM_OUT|0x37, UIO_STM_END]))
    return rev(bytes(resp[:len(mosi)]))

def rdsr(dev):
    r = spi_stream(dev, bytes([0x05, 0x00]))
    return r[1] if len(r) > 1 else 0xFF
def wait_ready(dev):
    for _ in range(1000):
        if rdsr(dev) & 1 == 0: return True
        time.sleep(0.01)
    return False

def bitbang_spi_write(dev, mosi_bytes):
    """Bit-bang SPI write via UIO GPIO. No MISO capture (write-only).
    CS# is asserted before and deasserted after."""

    # Build UIO operations for all bits
    # Each bit needs 2 ops: (MOSI+SCK_low), (SCK_high)
    ops = []
    for byte in mosi_bytes:
        for bit in range(7, -1, -1):  # MSB first
            mosi_val = MOSI_BIT if ((byte >> bit) & 1) else 0
            # SCK low, set MOSI
            ops.append(UIO_STM_OUT | (BASE | mosi_val))
            # SCK high (chip latches on rising edge)
            ops.append(UIO_STM_OUT | (BASE | mosi_val | SCK_BIT))
    # Final: SCK low
    ops.append(UIO_STM_OUT | BASE)

    # Assert CS#
    dev.write(EP_OUT, bytes([UIO_STREAM, UIO_STM_OUT | (BASE & ~CS_BIT), UIO_STM_END]))

    # Send bit-bang operations in chunks (max ~30 ops per UIO packet)
    chunk_size = 29  # Leave room for UIO_STREAM prefix and UIO_STM_END
    for i in range(0, len(ops), chunk_size):
        chunk = ops[i:i+chunk_size]
        pkt = bytes([UIO_STREAM] + chunk + [UIO_STM_END])
        dev.write(EP_OUT, pkt)

    # Deassert CS# (triggers Page Program execution)
    dev.write(EP_OUT, bytes([UIO_STREAM, UIO_STM_OUT | (BASE | CS_BIT), UIO_STM_END]))

def bitbang_page_program(dev, addr, data):
    """Page Program via bit-bang. Writes up to 256 bytes."""
    assert len(data) <= 256
    # WREN first (using standard SPI stream — it's only 1 byte)
    spi_stream(dev, bytes([0x06]))
    # Build PP command
    cmd = bytes([0x02, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]) + data
    # Bit-bang it
    bitbang_spi_write(dev, cmd)
    # Wait for programming
    wait_ready(dev)

def main():
    dev = find_ch341a()
    dev.write(EP_OUT, bytes([0xAA, 0x61, 0x00]))
    dev.write(EP_OUT, bytes([UIO_STREAM, UIO_STM_OUT|0x37, UIO_STM_DIR|0x3F, UIO_STM_END]))

    # Verify chip
    r = spi_stream(dev, bytes([0x9F, 0, 0, 0]))
    jedec = f"{r[1]:02X} {r[2]:02X} {r[3]:02X}" if len(r) >= 4 else "??"
    print(f"JEDEC: {jedec}")
    if len(r) < 4 or r[1] != 0xEF:
        print("Chip not found!"); sys.exit(1)

    test_data = bytes([0x4E, 0x56, 0x47, 0x49, 0x42, 0x03, 0x24, 0x80,
                       0xC0, 0x19, 0x00, 0x00, 0x58, 0x1A, 0x18, 0x20])
    addr = 0x100000

    # Erase
    print("Erasing sector...")
    spi_stream(dev, bytes([0x06]))
    spi_stream(dev, bytes([0x20, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]))
    wait_ready(dev)

    # Bit-bang Page Program with 16 bytes
    print(f"Bit-bang writing {len(test_data)} bytes at 0x{addr:06X}...")
    bitbang_page_program(dev, addr, test_data)

    # Verify with standard SPI read
    print("Reading back...")
    rd = spi_stream(dev, bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*16))
    readback = rd[4:] if len(rd) >= 20 else bytes(16)

    match = sum(1 for a, b in zip(readback, test_data) if a == b)
    print(f"\nResult: {match}/{len(test_data)} bytes match!")
    print(f"Got:    {' '.join(f'{b:02X}' for b in readback)}")
    print(f"Expect: {' '.join(f'{b:02X}' for b in test_data)}")

    if match == len(test_data):
        print("\n*** BIT-BANG WRITE WORKS! ALL BYTES CORRECT! ***")
    else:
        print("\nBit analysis of mismatches:")
        for i, (got, exp) in enumerate(zip(readback, test_data)):
            if got != exp:
                print(f"  Byte {i}: exp 0x{exp:02X} ({exp:08b}), got 0x{got:02X} ({got:08b})")

if __name__ == "__main__":
    main()
