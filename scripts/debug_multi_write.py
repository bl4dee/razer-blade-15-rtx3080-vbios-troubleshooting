#!/usr/bin/env python3
"""Debug why second Page Program to same sector fails after first succeeds."""
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

def spi(mosi):
    rd = rev(mosi)
    uio = bytearray([0xAB, 0xB7, 0xB7, 0xB7, 0xB6, 0x20])
    uio.extend([0x00] * (32 - len(uio)))
    spi_pkt = bytearray()
    for i in range(0, len(rd), 31):
        spi_pkt.append(0xA8)
        spi_pkt.extend(rd[i:i+31])
    dev.write(EP_OUT, bytes(uio) + bytes(spi_pkt))
    try: resp = dev.read(EP_IN, max(len(mosi), 32), timeout=2000)
    except: resp = bytes(len(mosi))
    dev.write(EP_OUT, bytes([0xAB, 0xB7, 0x20]))
    return rev(bytes(resp[:len(mosi)]))

def rdsr(n): return spi(bytes([n, 0x00]))[1]
def wait():
    for _ in range(500):
        if rdsr(0x05) & 1 == 0: return
        time.sleep(0.01)

r = spi(bytes([0x9F, 0, 0, 0]))
print(f"JEDEC: {r[1]:02X} {r[2]:02X} {r[3]:02X}\n")

addr = 0x100000

# Erase
print("[1] Erase sector...")
spi(bytes([0x06]))  # WREN
spi(bytes([0x20, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]))
wait()
sr1 = rdsr(0x05)
print(f"    SR1 after erase: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")

# Check it's erased
rd = spi(bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*4))
print(f"    Data at addr: {' '.join(f'{b:02X}' for b in rd[4:])}")

# First write: 2 bytes at offset 0
print("\n[2] First Page Program (2 bytes at +0)...")
spi(bytes([0x06]))  # WREN
sr1 = rdsr(0x05)
print(f"    SR1 after WREN: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")
spi(bytes([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF, 0xAA, 0x55]))
# Check SR1 immediately
sr1 = rdsr(0x05)
print(f"    SR1 immediately after PP: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")
wait()
sr1 = rdsr(0x05)
print(f"    SR1 after wait: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")
rd = spi(bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*4))
print(f"    Data: {' '.join(f'{b:02X}' for b in rd[4:])}")

# Check all 3 SRs
sr1, sr2, sr3 = rdsr(0x05), rdsr(0x35), rdsr(0x15)
print(f"    SR1=0x{sr1:02X} SR2=0x{sr2:02X} SR3=0x{sr3:02X}")
wps = (sr3>>2)&1
print(f"    WPS={wps}")

# Check block lock for this address
bl = spi(bytes([0x3D, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF, 0x00]))
print(f"    Block lock at 0x{addr:06X}: {bl[4]&1}")

# Second write: 2 bytes at offset 2
print("\n[3] Second Page Program (2 bytes at +2)...")
a2 = addr + 2
spi(bytes([0x06]))  # WREN
sr1 = rdsr(0x05)
print(f"    SR1 after WREN: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")

if sr1 & 0x02 == 0:
    print("    !!! WEL IS NOT SET! WREN FAILED!")
    print("    Trying WREN again...")
    time.sleep(0.1)
    spi(bytes([0x06]))
    sr1 = rdsr(0x05)
    print(f"    SR1 after retry WREN: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")

spi(bytes([0x02, (a2>>16)&0xFF, (a2>>8)&0xFF, a2&0xFF, 0xBB, 0xCC]))
sr1 = rdsr(0x05)
print(f"    SR1 immediately after PP: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")
wait()
sr1 = rdsr(0x05)
print(f"    SR1 after wait: 0x{sr1:02X} (BUSY={sr1&1}, WEL={sr1>>1&1})")
rd = spi(bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*4))
print(f"    Data: {' '.join(f'{b:02X}' for b in rd[4:])}")

# Try a third write after explicit delay
print("\n[4] Third Page Program after 500ms delay...")
time.sleep(0.5)
a3 = addr + 4
spi(bytes([0x06]))
sr1 = rdsr(0x05)
print(f"    SR1 after WREN: 0x{sr1:02X} (WEL={sr1>>1&1})")
spi(bytes([0x02, (a3>>16)&0xFF, (a3>>8)&0xFF, a3&0xFF, 0xDD, 0xEE]))
sr1 = rdsr(0x05)
print(f"    SR1 after PP: 0x{sr1:02X} (BUSY={sr1&1})")
wait()
rd = spi(bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF] + [0]*8))
print(f"    Data: {' '.join(f'{b:02X}' for b in rd[4:])}")

# Try writing to a DIFFERENT sector (same base, different 4KB block)
print("\n[5] Write to DIFFERENT sector (should work)...")
addr2 = addr + 0x1000
spi(bytes([0x06]))
spi(bytes([0x20, (addr2>>16)&0xFF, (addr2>>8)&0xFF, addr2&0xFF]))
wait()
spi(bytes([0x06]))
sr1 = rdsr(0x05)
print(f"    SR1 after WREN for new sector: 0x{sr1:02X} (WEL={sr1>>1&1})")
spi(bytes([0x02, (addr2>>16)&0xFF, (addr2>>8)&0xFF, addr2&0xFF, 0xFF, 0x00]))
sr1 = rdsr(0x05)
print(f"    SR1 after PP: 0x{sr1:02X} (BUSY={sr1&1})")
wait()
rd = spi(bytes([0x03, (addr2>>16)&0xFF, (addr2>>8)&0xFF, addr2&0xFF] + [0]*4))
print(f"    Data: {' '.join(f'{b:02X}' for b in rd[4:])}")
