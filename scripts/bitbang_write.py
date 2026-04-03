#!/usr/bin/env python3
"""
Bit-bang SPI via CH341A GPIO for slow, reliable writes to 1.8V flash chips.
Uses UIO stream commands to toggle CLK/MOSI/CS manually.
Much slower than hardware SPI (~few kHz) but much more reliable.
"""
import usb.core
import usb.util
import sys
import time
import struct

VID, PID = 0x1a86, 0x5512
EP_OUT = 0x02
EP_IN = 0x82
TIMEOUT = 5000

# CH341A commands
CMD_UIO_STREAM = 0xAB
CMD_I2C_STREAM = 0xAA
CMD_SPI_STREAM = 0xA8

# UIO sub-commands
UIO_STM_OUT = 0x80  # Set output pins
UIO_STM_IN  = 0xC0  # Read input pins
UIO_STM_DIR = 0x40  # Set pin direction
UIO_STM_END = 0x20  # End of stream

# CH341A SPI pin mapping (active low CS):
# D0 = CS#   (pin 15) - bit 0
# D3 = SCK   (pin 18) - bit 3
# D5 = MOSI  (pin 20) - bit 5
# D7 = MISO  (pin 22) - bit 7 (input)

CS_BIT   = 0x01  # D0
SCK_BIT  = 0x08  # D3
MOSI_BIT = 0x20  # D5
MISO_BIT = 0x80  # D7

# Bit reversal table (CH341A is LSB-first in hardware SPI, but for bitbang we control bit order)
SWAP = [int('{:08b}'.format(i)[::-1], 2) for i in range(256)]


class CH341A_BitBang:
    def __init__(self):
        self.dev = usb.core.find(idVendor=VID, idProduct=PID)
        if not self.dev:
            raise RuntimeError("CH341A not found!")
        try:
            self.dev.set_configuration()
        except:
            pass
        # Configure stream mode
        self.dev.write(EP_OUT, bytes([CMD_I2C_STREAM, 0x60, 0x00]), TIMEOUT)
        time.sleep(0.05)
        # Set pin directions: D0,D3,D5 as output, D7 as input
        self._set_pins(CS_BIT, 0, 0)  # CS high (deasserted), SCK low, MOSI low

    def _set_pins(self, cs_high, sck, mosi):
        """Set GPIO pins. cs_high=1 means CS deasserted (high)."""
        val = 0
        if cs_high:
            val |= CS_BIT
        if sck:
            val |= SCK_BIT
        if mosi:
            val |= MOSI_BIT
        # Direction: all SPI pins as output
        direction = CS_BIT | SCK_BIT | MOSI_BIT
        cmd = bytes([CMD_UIO_STREAM, UIO_STM_DIR | (direction & 0x3F),
                     UIO_STM_OUT | (val & 0x3F), UIO_STM_END])
        self.dev.write(EP_OUT, cmd, TIMEOUT)

    def _spi_transfer_byte(self, tx_byte, read=False):
        """Transfer one byte via bit-bang SPI mode 0 (CPOL=0, CPHA=0).
        Batches all 16 clock edges into one USB packet for speed."""
        # Build a UIO stream that clocks out 8 bits
        # For each bit: set MOSI + SCK low, then set MOSI + SCK high (sample on rising edge)
        cmd = bytearray([CMD_UIO_STREAM])
        rx_positions = []

        for bit in range(7, -1, -1):  # MSB first
            mosi_val = MOSI_BIT if (tx_byte >> bit) & 1 else 0

            # SCK low, set MOSI
            cmd.append(UIO_STM_OUT | ((mosi_val) & 0x3F))
            # SCK high (rising edge - slave samples MOSI, master samples MISO)
            cmd.append(UIO_STM_OUT | ((mosi_val | SCK_BIT) & 0x3F))
            if read:
                cmd.append(UIO_STM_IN)  # Read MISO
                rx_positions.append(len(cmd) - 1)

        # SCK low at end
        cmd.append(UIO_STM_OUT | 0x00)
        cmd.append(UIO_STM_END)

        self.dev.write(EP_OUT, bytes(cmd), TIMEOUT)

        if read:
            resp = self.dev.read(EP_IN, 32, TIMEOUT)
            rx_byte = 0
            for i, bit in enumerate(range(7, -1, -1)):
                if i < len(resp) and resp[i] & MISO_BIT:
                    rx_byte |= (1 << bit)
            return rx_byte
        return 0

    def cs_low(self):
        cmd = bytes([CMD_UIO_STREAM, UIO_STM_OUT | 0x00, UIO_STM_END])  # CS=0, SCK=0, MOSI=0
        self.dev.write(EP_OUT, cmd, TIMEOUT)

    def cs_high(self):
        cmd = bytes([CMD_UIO_STREAM, UIO_STM_OUT | CS_BIT, UIO_STM_END])  # CS=1
        self.dev.write(EP_OUT, cmd, TIMEOUT)

    def spi_cmd(self, tx_data, rx_len=0):
        """Send SPI command bytes, optionally read rx_len bytes back."""
        self.cs_low()
        for b in tx_data:
            self._spi_transfer_byte(b, read=False)
        result = bytearray()
        for _ in range(rx_len):
            result.append(self._spi_transfer_byte(0xFF, read=True))
        self.cs_high()
        return bytes(result)

    def read_id(self):
        return self.spi_cmd(bytes([0x9F]), 3)

    def read_status(self):
        return self.spi_cmd(bytes([0x05]), 1)[0]

    def write_enable(self):
        self.spi_cmd(bytes([0x06]))

    def wait_ready(self, timeout=5):
        start = time.time()
        while time.time() - start < timeout:
            sr = self.read_status()
            if not (sr & 0x01):
                return True
            time.sleep(0.001)
        return False

    def page_program(self, addr, data):
        """Page Program: write up to 256 bytes. Only changes 1→0."""
        assert len(data) <= 256
        self.write_enable()
        sr = self.read_status()
        if not (sr & 0x02):
            return False  # WEL not set
        cmd = bytes([0x02, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]) + data
        self.spi_cmd(cmd)
        return self.wait_ready()

    def read_data(self, addr, length):
        return self.spi_cmd(bytes([0x03, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]), length)


def main():
    vbios_file = "/home/blink/razer-vbios-recovery/padded_vbios.bin"
    vbios_end = 0x111000

    with open(vbios_file, "rb") as f:
        vbios = f.read()

    print("Connecting to CH341A (bit-bang mode)...")
    ch = CH341A_BitBang()

    print("Reading chip ID...")
    chip_id = ch.read_id()
    print(f"Chip ID: {chip_id.hex()}")
    if chip_id == bytes([0x00, 0x00, 0x00]) or chip_id == bytes([0xFF, 0xFF, 0xFF]):
        print("ERROR: No chip detected. Check clip connection.")
        return

    sr = ch.read_status()
    print(f"Status: 0x{sr:02x}")

    # Test: read first 16 bytes
    test = ch.read_data(0, 16)
    print(f"First 16 bytes on chip: {test.hex()}")
    print(f"Expected:               {vbios[:16].hex()}")

    # Write first page as test
    print("\n=== Test: writing first page (256 bytes) ===")
    ok = ch.page_program(0, vbios[:256])
    if not ok:
        print("FAILED - WEL not set or timeout. Check connection.")
        return

    verify = ch.read_data(0, 256)
    match = sum(1 for a, b in zip(verify, vbios[:256]) if a == b)
    print(f"First page: {match}/256 match ({match/256*100:.1f}%)")

    if match < 200:
        print("Write quality too low, aborting.")
        return

    if match == 256:
        print("PERFECT first page! Proceeding with full write...")
    else:
        print(f"Partial match ({match}/256). Proceeding anyway...")

    # Full write
    page_size = 256
    total_pages = (vbios_end + page_size - 1) // page_size
    written = 0
    skipped = 0
    errors = 0

    start_time = time.time()
    for addr in range(0, vbios_end, page_size):
        target = vbios[addr:addr + page_size]
        if target == bytes([0xFF] * len(target)):
            skipped += 1
            continue

        ok = ch.page_program(addr, target)
        if ok:
            written += 1
        else:
            errors += 1
            if errors > 50:
                print(f"\nToo many errors at 0x{addr:06x}")
                break

        if written % 50 == 0:
            elapsed = time.time() - start_time
            pct = addr / vbios_end * 100
            eta = elapsed / max(pct, 0.1) * (100 - pct) if pct > 0 else 0
            sys.stdout.write(f"\r  0x{addr:06x}/{vbios_end:06x} ({pct:.1f}%) "
                           f"written={written} skipped={skipped} errors={errors} "
                           f"ETA: {eta:.0f}s  ")
            sys.stdout.flush()

    elapsed = time.time() - start_time
    print(f"\n\nDone in {elapsed:.0f}s. Written={written}, Skipped={skipped}, Errors={errors}")

    # Final verify (sample)
    print("\nVerifying first 4KB...")
    verify = ch.read_data(0, 4096)
    match = sum(1 for a, b in zip(verify, vbios[:4096]) if a == b)
    print(f"First 4KB: {match}/4096 ({match/4096*100:.1f}%)")


if __name__ == "__main__":
    main()
