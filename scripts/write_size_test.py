#!/usr/bin/env python3
"""Test Page Program at different data sizes to find the breakpoint."""
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

# Init like flashrom
dev.write(EP_OUT, bytes([0xAA, 0x61, 0x00]))
dev.write(EP_OUT, bytes([0xAB, 0xB7, 0x7F, 0x20]))

def spi(data):
    rd = rev(data)
    uio = bytearray(32)
    uio[0] = 0xAB
    for i in range(1, 28): uio[i] = 0xB7
    uio[28] = 0xB6; uio[29] = 0x20
    pkt = bytes(uio) + bytes([0xA8]) + rd
    dev.write(EP_OUT, pkt)
    resp = dev.read(EP_IN, len(data), timeout=2000)
    dev.write(EP_OUT, bytes([0xAB, 0xB7, 0x20]))
    return rev(bytes(resp))

def spi_chunked(data):
    """Send SPI data using flashrom-style 31-byte chunks"""
    rd = rev(data)
    uio = bytearray(32)
    uio[0] = 0xAB
    for i in range(1, 28): uio[i] = 0xB7
    uio[28] = 0xB6; uio[29] = 0x20

    # Build chunked SPI payload
    spi_payload = bytearray()
    for i in range(0, len(rd), 31):
        chunk = rd[i:i+31]
        spi_payload.append(0xA8)
        spi_payload.extend(chunk)

    pkt = bytes(uio) + bytes(spi_payload)
    dev.write(EP_OUT, pkt)
    resp = dev.read(EP_IN, len(data), timeout=2000)
    dev.write(EP_OUT, bytes([0xAB, 0xB7, 0x20]))
    return rev(bytes(resp))

def rdsr():
    r = spi(bytes([0x05, 0x00]))
    return r[1]

def wait():
    for _ in range(500):
        if rdsr() & 1 == 0: return True
        time.sleep(0.01)
    return False

def wren(): spi(bytes([0x06]))

def erase_sector(addr):
    wren()
    spi(bytes([0x20, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]))
    wait()

def read_flash(addr, n):
    r = spi(bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*n))
    return r[4:]

# Verify chip
r = spi(bytes([0x9F, 0, 0, 0]))
print(f"JEDEC: {r[1]:02X} {r[2]:02X} {r[3]:02X}")
if r[1] != 0xEF:
    print("Chip not found!"); sys.exit(1)

print(f"SR1=0x{rdsr():02X} SR2=0x{spi(bytes([0x35,0]))[1]:02X} SR3=0x{spi(bytes([0x15,0]))[1]:02X}")
print()

# Test different write sizes using non-chunked (single A8 prefix)
base_addr = 0x100000
test_pattern = bytes([0x4E, 0x56, 0x47, 0x49, 0x42, 0x03, 0x24, 0x80,
                      0xC0, 0x19, 0x00, 0x00, 0x58, 0x1A, 0x18, 0x20,
                      0x02, 0x02, 0x00, 0x00, 0x24, 0x00, 0x00, 0x00,
                      0x00, 0x00, 0x04, 0xE0, 0x31, 0x50, 0x00, 0x01])

print("=== Non-chunked (single A8 prefix) ===")
for size in [1, 2, 4, 8, 16, 32]:
    addr = base_addr + size * 256  # Different sector for each
    erase_sector(addr)
    data = test_pattern[:size]
    wren()
    cmd = bytes([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]) + data
    spi(cmd)
    wait()
    rb_data = read_flash(addr, size)
    match = sum(1 for a,b in zip(rb_data, data) if a == b)
    landed = sum(1 for b in rb_data if b != 0xFF)
    print(f"  {size:3d} bytes: {match}/{size} match, {landed} non-FF  |  wrote={' '.join(f'{b:02X}' for b in data[:8])}...  got={' '.join(f'{b:02X}' for b in rb_data[:8])}...")

print()
print("=== Chunked (flashrom-style, 31-byte A8 chunks) ===")
for size in [1, 2, 4, 8, 16, 32]:
    addr = base_addr + (size + 32) * 256
    erase_sector(addr)
    data = test_pattern[:size]
    wren()
    cmd = bytes([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]) + data
    spi_chunked(cmd)
    wait()
    rb_data = read_flash(addr, size)
    match = sum(1 for a,b in zip(rb_data, data) if a == b)
    landed = sum(1 for b in rb_data if b != 0xFF)
    print(f"  {size:3d} bytes: {match}/{size} match, {landed} non-FF  |  wrote={' '.join(f'{b:02X}' for b in data[:8])}...  got={' '.join(f'{b:02X}' for b in rb_data[:8])}...")
