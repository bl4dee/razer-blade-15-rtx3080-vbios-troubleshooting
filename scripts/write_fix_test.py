#!/usr/bin/env python3
"""Test different USB packet strategies for Page Program."""
import usb.core, usb.util, time, sys

CH341_VID, CH341_PID = 0x1a86, 0x5512
EP_OUT, EP_IN = 0x02, 0x82

def rb(b):
    r = 0
    for i in range(8):
        r = (r << 1) | (b & 1)
        b >>= 1
    return r
def rev(data): return bytes(rb(b) for b in data)

dev = usb.core.find(idVendor=CH341_VID, idProduct=CH341_PID)
try:
    if dev.is_kernel_driver_active(0): dev.detach_kernel_driver(0)
except: pass
dev.set_configuration()
dev.write(EP_OUT, bytes([0xAA, 0x61, 0x00]))
dev.write(EP_OUT, bytes([0xAB, 0xB7, 0x7F, 0x20]))

def cs_low(d):
    d.write(EP_OUT, bytes([0xAB, 0xB7, 0xB7, 0xB7, 0xB6, 0x20]))

def cs_high(d):
    d.write(EP_OUT, bytes([0xAB, 0xB7, 0x20]))

def spi_raw(d, mosi):
    """Send SPI with separate UIO and SPI USB writes"""
    rd = rev(mosi)
    cs_low(d)
    # Send SPI data in 32-byte chunks (31 data + A8 prefix each)
    for i in range(0, len(rd), 31):
        chunk = rd[i:i+31]
        d.write(EP_OUT, bytes([0xA8]) + chunk)
    try:
        resp = d.read(EP_IN, max(len(mosi), 32), timeout=2000)
    except:
        resp = bytes(len(mosi))
    cs_high(d)
    return rev(bytes(resp[:len(mosi)]))

def spi_flashrom(d, mosi):
    """Send SPI exactly like flashrom — one big USB write"""
    rd = rev(mosi)
    # UIO preamble: CS# low — exactly like flashrom verbose output
    uio = bytearray([0xAB, 0xB7, 0xB7, 0xB7, 0xB6, 0x20])
    uio.extend([0x00] * (32 - len(uio)))  # Pad to 32 bytes

    # SPI data in 31-byte chunks, each prefixed with A8
    spi_pkt = bytearray()
    for i in range(0, len(rd), 31):
        chunk = rd[i:i+31]
        spi_pkt.append(0xA8)
        spi_pkt.extend(chunk)

    d.write(EP_OUT, bytes(uio) + bytes(spi_pkt))
    try:
        resp = d.read(EP_IN, max(len(mosi), 32), timeout=2000)
    except:
        resp = bytes(len(mosi))
    cs_high(d)
    return rev(bytes(resp[:len(mosi)]))

def spi_2byte_pages(d, addr, data):
    """Write data 2 bytes at a time — exploiting the 2-byte-per-write limit"""
    for i in range(0, len(data), 2):
        chunk = data[i:i+2]
        a = addr + i
        wren_cmd = bytes([0x06])
        spi_flashrom(d, wren_cmd)
        pp_cmd = bytes([0x02, (a>>16)&0xFF, (a>>8)&0xFF, a&0xFF]) + chunk
        spi_flashrom(d, pp_cmd)
        # Wait for BUSY
        for _ in range(200):
            sr = spi_flashrom(d, bytes([0x05, 0x00]))[1]
            if sr & 1 == 0: break
            time.sleep(0.005)

def rdsr():
    return spi_flashrom(dev, bytes([0x05, 0x00]))[1]

def wait():
    for _ in range(500):
        if rdsr() & 1 == 0: return True
        time.sleep(0.01)
    return False

def wren():
    spi_flashrom(dev, bytes([0x06]))

def erase_sector(addr):
    wren()
    spi_flashrom(dev, bytes([0x20, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]))
    wait()

def read_flash(addr, n):
    r = spi_flashrom(dev, bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*n))
    return r[4:]

# Verify
r = spi_flashrom(dev, bytes([0x9F, 0, 0, 0]))
print(f"JEDEC: {r[1]:02X} {r[2]:02X} {r[3]:02X}")
if r[1] != 0xEF: print("No chip!"); sys.exit(1)

base = 0x100000
test_data = bytes([0x4E, 0x56, 0x47, 0x49, 0x42, 0x03, 0x24, 0x80,
                   0xC0, 0x19, 0x00, 0x00, 0x58, 0x1A, 0x18, 0x20])

# Test 1: Separate USB writes (UIO and SPI as separate packets)
print("\n=== Strategy 1: Separate USB writes for UIO and SPI ===")
for size in [4, 8, 16]:
    addr = base + size * 0x1000
    erase_sector(addr)
    data = test_data[:size]
    # WREN with separate writes
    cs_low(dev)
    dev.write(EP_OUT, bytes([0xA8]) + rev(bytes([0x06])))
    dev.read(EP_IN, 1, timeout=2000)
    cs_high(dev)
    # Page Program with separate writes
    cmd = bytes([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]) + data
    spi_raw(dev, cmd)
    wait()
    rb_data = read_flash(addr, size)
    match = sum(1 for a,b in zip(rb_data, data) if a == b)
    print(f"  {size:3d} bytes: {match}/{size} match | got={' '.join(f'{b:02X}' for b in rb_data)}")

# Test 2: Write 2 bytes at a time (exploiting the working window)
print("\n=== Strategy 2: Write 2 bytes per Page Program ===")
addr = base + 0x20000
erase_sector(addr)
spi_2byte_pages(dev, addr, test_data)
rb_data = read_flash(addr, len(test_data))
match = sum(1 for a,b in zip(rb_data, test_data) if a == b)
print(f"  {len(test_data)} bytes via 2-byte pages: {match}/{len(test_data)} match")
print(f"  got: {' '.join(f'{b:02X}' for b in rb_data)}")
print(f"  exp: {' '.join(f'{b:02X}' for b in test_data)}")
