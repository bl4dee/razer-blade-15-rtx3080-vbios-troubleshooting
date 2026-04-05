#!/usr/bin/env python3
"""Full chip diagnostic — uses flashrom-compatible CH341A init sequence.
Reads all status registers, checks WPS/block locks, attempts Global Block Unlock,
then tests a single-byte write to verify if writes actually land."""
import usb.core
import usb.util
import time
import sys

CH341_VID = 0x1a86
CH341_PID = 0x5512

# CH341A protocol constants
CH341A_CMD_SET_OUTPUT = 0xAA
CH341A_CMD_SPI_STREAM = 0xA8
CH341A_CMD_UIO_STREAM = 0xAB
CH341A_CMD_UIO_STM_OUT = 0x80
CH341A_CMD_UIO_STM_DIR = 0x40
CH341A_CMD_UIO_STM_END = 0x20

EP_OUT = 0x02
EP_IN  = 0x82

def reverse_bits(b):
    """Reverse bits in a byte — CH341A SPI is LSB-first, flash chips are MSB-first"""
    r = 0
    for i in range(8):
        r = (r << 1) | (b & 1)
        b >>= 1
    return r

def reverse_bytes(data):
    return bytes(reverse_bits(b) for b in data)

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

def ch341_init(dev):
    """Initialize CH341A exactly as flashrom does"""
    # Set Output (AA 61 00) — configure I/O
    dev.write(EP_OUT, bytes([CH341A_CMD_SET_OUTPUT, 0x61, 0x00]))
    # UIO Stream (AB B7 7F 20) — set GPIO directions, CS# high
    dev.write(EP_OUT, bytes([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x37,
                              CH341A_CMD_UIO_STM_DIR | 0x3F, CH341A_CMD_UIO_STM_END]))

def spi_xfer(dev, mosi_data):
    """SPI transfer matching flashrom's CH341A driver.
    mosi_data is in normal MSB-first SPI byte order.
    Returns MISO data in normal MSB-first order."""
    reversed_mosi = reverse_bytes(mosi_data)

    # Build packet like flashrom: UIO to assert CS#, then SPI stream, then UIO to deassert
    # CS# low
    uio_cs_low = bytearray(32)
    uio_cs_low[0] = CH341A_CMD_UIO_STREAM
    for i in range(1, 28):
        uio_cs_low[i] = CH341A_CMD_UIO_STM_OUT | 0x37  # padding
    uio_cs_low[28] = CH341A_CMD_UIO_STM_OUT | 0x36  # CS# low (bit 0 = 0)
    uio_cs_low[29] = CH341A_CMD_UIO_STM_END
    # Pad remaining with zeros
    # Add SPI stream
    pkt = bytes(uio_cs_low) + bytes([CH341A_CMD_SPI_STREAM]) + reversed_mosi
    dev.write(EP_OUT, pkt)

    # Read response
    resp = dev.read(EP_IN, len(mosi_data), timeout=2000)

    # CS# high
    dev.write(EP_OUT, bytes([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x37,
                              CH341A_CMD_UIO_STM_END]))

    return reverse_bytes(bytes(resp))

def read_jedec(dev):
    resp = spi_xfer(dev, bytes([0x9F, 0x00, 0x00, 0x00]))
    return resp[1], resp[2], resp[3]

def read_sr(dev, cmd):
    resp = spi_xfer(dev, bytes([cmd, 0x00]))
    return resp[1]

def write_enable(dev):
    spi_xfer(dev, bytes([0x06]))

def wait_ready(dev, timeout=5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        sr = read_sr(dev, 0x05)
        if sr & 0x01 == 0:
            return True
        time.sleep(0.01)
    return False

def write_sr(dev, reg_cmd, value):
    write_enable(dev)
    spi_xfer(dev, bytes([reg_cmd, value]))
    wait_ready(dev)

def global_block_unlock(dev):
    write_enable(dev)
    spi_xfer(dev, bytes([0x98]))
    wait_ready(dev)

def read_block_lock(dev, addr):
    resp = spi_xfer(dev, bytes([0x3D, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF, 0x00]))
    return resp[4] & 0x01

def page_program(dev, addr, data):
    """Page Program — write up to 256 bytes"""
    cmd = bytes([0x02, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]) + bytes(data)
    write_enable(dev)
    spi_xfer(dev, cmd)
    wait_ready(dev)

def read_data(dev, addr, length):
    """Read data from flash"""
    cmd = bytes([0x03, (addr>>16)&0xFF, (addr>>8)&0xFF, addr&0xFF]) + bytes([0x00]*length)
    resp = spi_xfer(dev, cmd)
    return resp[4:]

def main():
    print("=" * 60)
    print("  W25Q16JW Full Chip Diagnostic")
    print("=" * 60)
    print()

    dev = find_ch341a()
    ch341_init(dev)
    print("[+] CH341A initialized (flashrom-compatible)")

    # JEDEC ID
    mfr, mtype, cap = read_jedec(dev)
    print(f"[+] JEDEC ID: {mfr:02X} {mtype:02X} {cap:02X}", end="")
    if mfr == 0xEF and mtype == 0x60 and cap == 0x15:
        print("  — W25Q16JW confirmed")
    elif mfr == 0xFF:
        print("  — NO RESPONSE (check clip)")
        sys.exit(1)
    else:
        print(f"  — unexpected!")
    print()

    # Read all status registers
    sr1 = read_sr(dev, 0x05)
    sr2 = read_sr(dev, 0x35)
    sr3 = read_sr(dev, 0x15)

    print("[*] Status Registers:")
    print(f"  SR1: 0x{sr1:02X} ({sr1:08b})")
    print(f"    SRP0={sr1>>7&1} SEC={sr1>>6&1} TB={sr1>>5&1} BP2={sr1>>4&1} BP1={sr1>>3&1} BP0={sr1>>2&1}")
    print(f"  SR2: 0x{sr2:02X} ({sr2:08b})")
    print(f"    CMP={sr2>>6&1} LB3={sr2>>5&1} LB2={sr2>>4&1} LB1={sr2>>3&1} QE={sr2>>1&1} SRP1={sr2&1}")
    print(f"  SR3: 0x{sr3:02X} ({sr3:08b})")
    wps = (sr3>>2)&1
    print(f"    DRV1={sr3>>6&1} DRV0={sr3>>5&1} WPS={wps}")
    print()

    # Decode protection
    bp = (sr1>>2)&0x07
    if wps:
        print("[!] WPS=1 — INDIVIDUAL BLOCK LOCK MODE ACTIVE!")
        print("    Checking block locks...")
        locked = 0
        for addr in range(0, 0x200000, 0x10000):
            l = read_block_lock(dev, addr)
            if l:
                locked += 1
                print(f"      Block at 0x{addr:06X}: LOCKED")
        print(f"    {locked}/32 blocks locked")
    else:
        print(f"[*] WPS=0 — Legacy BP mode, BP={bp:03b}")

    print()

    # Clear everything
    print("[*] Clearing ALL protection...")
    # Clear SR1
    if sr1 & 0xFC:
        print("  Clearing SR1 (BP/SEC/TB/SRP0)...")
        write_sr(dev, 0x01, 0x00)
    # Clear SR2 (keep QE)
    qe = (sr2>>1)&1
    if sr2 & 0xFD:
        print(f"  Clearing SR2 (CMP/SRP1), keeping QE={qe}...")
        write_sr(dev, 0x31, qe << 1)
    # Clear WPS in SR3
    if wps:
        print("  Clearing WPS in SR3...")
        new_sr3 = sr3 & ~0x04
        write_sr(dev, 0x11, new_sr3)
    # Global Block Unlock
    print("  Sending Global Block Unlock (0x98)...")
    global_block_unlock(dev)

    # Verify
    sr1_new = read_sr(dev, 0x05)
    sr2_new = read_sr(dev, 0x35)
    sr3_new = read_sr(dev, 0x15)
    print(f"  After: SR1=0x{sr1_new:02X} SR2=0x{sr2_new:02X} SR3=0x{sr3_new:02X}")
    print()

    # Write test — single page at address 0x100000 (in padding area, safe)
    test_addr = 0x100000
    test_data = bytes([0x4E, 0x56, 0x47, 0x49, 0x42, 0x03, 0x24, 0x80])  # "NVGIB" + header

    print("[*] Write test at 0x{:06X}...".format(test_addr))

    # Read current contents
    before = read_data(dev, test_addr, 8)
    print(f"  Before: {' '.join(f'{b:02X}' for b in before)}")

    # Erase the sector first (sector erase = 0x20)
    print("  Erasing sector...")
    write_enable(dev)
    spi_xfer(dev, bytes([0x20, (test_addr>>16)&0xFF, (test_addr>>8)&0xFF, test_addr&0xFF]))
    wait_ready(dev, timeout=10)

    after_erase = read_data(dev, test_addr, 8)
    print(f"  After erase: {' '.join(f'{b:02X}' for b in after_erase)}")

    if all(b == 0xFF for b in after_erase):
        print("  Erase OK!")
    else:
        print("  ERASE FAILED — sector not all 0xFF")

    # Write test data
    print(f"  Writing: {' '.join(f'{b:02X}' for b in test_data)}")
    page_program(dev, test_addr, test_data)

    # Read back
    after_write = read_data(dev, test_addr, 8)
    print(f"  After write: {' '.join(f'{b:02X}' for b in after_write)}")

    match = sum(1 for a,b in zip(after_write, test_data) if a == b)
    print(f"  Match: {match}/{len(test_data)} bytes")

    if match == len(test_data):
        print()
        print("=" * 60)
        print("  WRITE TEST PASSED! Writes are landing!")
        print("=" * 60)
    else:
        print()
        print("  Bit analysis:")
        for i, (got, expected) in enumerate(zip(after_write, test_data)):
            if got != expected:
                bits_ok = sum(1 for bit in range(8) if ((got>>bit)&1) == ((expected>>bit)&1))
                print(f"    Byte {i}: expected 0x{expected:02X} ({expected:08b}), got 0x{got:02X} ({got:08b}) — {bits_ok}/8 bits correct")

    # Also try writing just 1 byte
    print()
    print("[*] Single-byte write test at 0x{:06X}...".format(test_addr + 256))
    write_enable(dev)
    spi_xfer(dev, bytes([0x20, (test_addr>>16)&0xFF, ((test_addr+256)>>8)&0xFF, 0x00]))
    wait_ready(dev, timeout=10)

    single_byte = bytes([0xAA])
    page_program(dev, test_addr + 256, single_byte)
    readback = read_data(dev, test_addr + 256, 1)
    print(f"  Wrote 0xAA, read back 0x{readback[0]:02X}")
    if readback[0] == 0xAA:
        print("  SINGLE BYTE WRITE OK!")
    else:
        print(f"  FAILED — bits: wrote {0xAA:08b}, got {readback[0]:08b}")

if __name__ == "__main__":
    main()
