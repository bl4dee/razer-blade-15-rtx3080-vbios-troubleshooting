#!/usr/bin/env python3
"""Test: does each Page Program need a fresh erase? Or is it position-dependent?"""
import usb.core, usb.util, time, sys

CH341_VID, CH341_PID = 0x1a86, 0x5512
EP_OUT, EP_IN = 0x02, 0x82

def reverse_bit(b):
    r = 0
    for i in range(8): r = (r << 1) | (b & 1); b >>= 1
    return r
def rev(data): return bytes(reverse_bit(b) for b in data)

dev = usb.core.find(idVendor=CH341_VID, idProduct=CH341_PID)
try:
    if dev.is_kernel_driver_active(0): dev.detach_kernel_driver(0)
except: pass
dev.set_configuration()
dev.write(EP_OUT, bytes([0xAA, 0x61, 0x00]))
dev.write(EP_OUT, bytes([0xAB, 0xB7, 0x7F, 0x20]))

def spi(d, mosi):
    rd = rev(mosi)
    uio = bytearray([0xAB, 0xB7, 0xB7, 0xB7, 0xB6, 0x20])
    uio.extend([0x00] * (32 - len(uio)))
    spi_pkt = bytearray()
    for i in range(0, len(rd), 31):
        spi_pkt.append(0xA8)
        spi_pkt.extend(rd[i:i+31])
    d.write(EP_OUT, bytes(uio) + bytes(spi_pkt))
    try: resp = d.read(EP_IN, max(len(mosi), 32), timeout=2000)
    except: resp = bytes(len(mosi))
    d.write(EP_OUT, bytes([0xAB, 0xB7, 0x20]))
    return rev(bytes(resp[:len(mosi)]))

def rdsr(): return spi(dev, bytes([0x05, 0x00]))[1]
def wait():
    for _ in range(500):
        if rdsr() & 1 == 0: return True
        time.sleep(0.01)
    return False
def wren(): spi(dev, bytes([0x06]))
def erase_sector(addr):
    wren()
    spi(dev, bytes([0x20, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]))
    wait()
def read_flash(addr, n):
    r = spi(dev, bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*n))
    return r[4:]
# Fix: 'rb' name collision — rename read_back variable in tests
def readback(addr, n):
    return read_flash(addr, n)
def page_program(addr, data):
    wren()
    spi(dev, bytes([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]) + data)
    wait()

r = spi(dev, bytes([0x9F, 0, 0, 0]))
print(f"JEDEC: {r[1]:02X} {r[2]:02X} {r[3]:02X}")

base = 0x100000
test = bytes([0x4E, 0x56, 0x47, 0x49, 0x42, 0x03, 0x24, 0x80,
              0xC0, 0x19, 0x00, 0x00, 0x58, 0x1A, 0x18, 0x20])

# Test 1: Multiple writes to same sector WITHOUT re-erasing
print("\n=== Test 1: Multiple 2-byte writes, ONE erase ===")
addr = base
erase_sector(addr)
for i in range(0, 16, 2):
    page_program(addr + i, test[i:i+2])
    rd = read_flash(addr, 16)
    landed = sum(1 for j in range(16) if rd[j] != 0xFF)
    print(f"  After write at +{i}: {' '.join(f'{b:02X}' for b in rd)}  ({landed} bytes landed)")

# Test 2: Each write gets its own erase (different sectors)
print("\n=== Test 2: Each 2-byte write in its OWN freshly erased sector ===")
for i in range(0, 16, 2):
    addr = base + 0x10000 + i * 0x1000
    erase_sector(addr)
    page_program(addr, test[i:i+2])
    rd = read_flash(addr, 2)
    ok = "OK" if rd[0] == test[i] and rd[1] == test[i+1] else "FAIL"
    print(f"  Bytes {i}-{i+1}: wrote {test[i]:02X} {test[i+1]:02X}, got {rd[0]:02X} {rd[1]:02X}  {ok}")

# Test 3: Write 2 bytes, same address, repeated — does the FIRST always work?
print("\n=== Test 3: Repeat 2-byte write at same addr after erase ===")
addr = base + 0x30000
for attempt in range(8):
    erase_sector(addr)
    page_program(addr, bytes([0xAA, 0x55]))
    rd = read_flash(addr, 2)
    ok = "OK" if rd[0] == 0xAA and rd[1] == 0x55 else "FAIL"
    print(f"  Attempt {attempt+1}: wrote AA 55, got {rd[0]:02X} {rd[1]:02X}  {ok}")

# Test 4: Write 1 byte at multiple offsets (each with own erase)
print("\n=== Test 4: Single-byte writes at different offsets ===")
for i in range(8):
    addr = base + 0x40000 + i * 0x1000
    erase_sector(addr)
    page_program(addr, bytes([test[i]]))
    rd = read_flash(addr, 1)
    ok = "OK" if rd[0] == test[i] else "FAIL"
    print(f"  Byte {i}: wrote 0x{test[i]:02X}, got 0x{rd[0]:02X}  {ok}")
