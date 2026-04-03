#!/usr/bin/env python3
"""Direct CH341A SPI page program WITHOUT erase. Repeated runs converge bits 1→0."""
import usb.core
import usb.util
import sys
import time

# CH341A constants
VID, PID = 0x1a86, 0x5512
WRITE_EP = 0x02
READ_EP = 0x82
PKT_LEN = 32
CMD_SPI_STREAM = 0xA8
CMD_UIO_STREAM = 0xAB
TIMEOUT = 1000

# Bit reversal table (CH341A requires LSB-first)
SWAP = [int('{:08b}'.format(i)[::-1], 2) for i in range(256)]

def swap_bytes(data):
    return bytes(SWAP[b] for b in data)

class CH341A:
    def __init__(self):
        self.dev = usb.core.find(idVendor=VID, idProduct=PID)
        if not self.dev:
            raise RuntimeError("CH341A not found")
        self.dev.set_configuration()
        # Set stream mode
        self.dev.write(WRITE_EP, bytes([0xAA, 0x60, 0x00]), TIMEOUT)
        time.sleep(0.01)

    def cs_low(self):
        self.dev.write(WRITE_EP, bytes([CMD_UIO_STREAM, 0x80, 0x36, 0x00]), TIMEOUT)

    def cs_high(self):
        self.dev.write(WRITE_EP, bytes([CMD_UIO_STREAM, 0x80, 0x37, 0x20, 0x00]), TIMEOUT)

    def spi_transfer(self, data):
        """Send SPI data in 31-byte chunks via stream packets."""
        swapped = swap_bytes(data)
        result = bytearray()
        offset = 0
        while offset < len(swapped):
            chunk = swapped[offset:offset + PKT_LEN - 1]
            pkt = bytes([CMD_SPI_STREAM]) + chunk
            self.dev.write(WRITE_EP, pkt, TIMEOUT)
            resp = self.dev.read(READ_EP, PKT_LEN, TIMEOUT)
            result.extend(swap_bytes(bytes(resp[:len(chunk)])))
            offset += PKT_LEN - 1
        return bytes(result)

    def spi_cmd(self, cmd_bytes, read_len=0):
        """Send SPI command with CS control."""
        self.cs_low()
        if read_len > 0:
            send = cmd_bytes + bytes(read_len)
            resp = self.spi_transfer(send)
            self.cs_high()
            return resp[len(cmd_bytes):]
        else:
            self.spi_transfer(cmd_bytes)
            self.cs_high()
            return b''

    def read_id(self):
        resp = self.spi_cmd(bytes([0x9F]), 3)
        return resp

    def read_status(self):
        resp = self.spi_cmd(bytes([0x05]), 1)
        return resp[0]

    def write_enable(self):
        self.spi_cmd(bytes([0x06]))

    def wait_ready(self, timeout_s=3):
        start = time.time()
        while time.time() - start < timeout_s:
            sr = self.read_status()
            if not (sr & 0x01):  # WIP bit
                return True
            time.sleep(0.001)
        return False

    def page_program(self, addr, data):
        """Write up to 256 bytes at addr. Only changes 1→0 bits."""
        assert len(data) <= 256
        self.write_enable()
        sr = self.read_status()
        if not (sr & 0x02):  # WEL bit
            return False
        cmd = bytes([0x02, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]) + data
        self.spi_cmd(cmd)
        return self.wait_ready()

    def read_data(self, addr, length):
        cmd = bytes([0x03, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF])
        return self.spi_cmd(cmd, length)


def main():
    vbios_file = "/home/blink/razer-vbios-recovery/padded_vbios.bin"
    vbios_end = 0x111000  # Skip bad sector at 0x111000

    with open(vbios_file, "rb") as f:
        vbios = f.read()

    print("Connecting to CH341A...")
    ch = CH341A()

    chip_id = ch.read_id()
    print(f"Chip ID: {chip_id.hex()} (expect ef6015 for W25Q16JW)")
    if chip_id[:2] != bytes([0xEF, 0x60]):
        print("WARNING: unexpected chip ID, check connection")

    sr = ch.read_status()
    print(f"Status register: 0x{sr:02x}")

    num_passes = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    page_size = 256

    for pass_num in range(1, num_passes + 1):
        print(f"\n=== Pass {pass_num}/{num_passes} ===")
        pages_written = 0
        pages_skipped = 0
        errors = 0

        for addr in range(0, vbios_end, page_size):
            target = vbios[addr:addr + page_size]

            # Skip pages that are all 0xFF (nothing to program)
            if target == bytes([0xFF] * len(target)):
                pages_skipped += 1
                continue

            ok = ch.page_program(addr, target)
            if ok:
                pages_written += 1
            else:
                errors += 1
                if errors > 10:
                    print(f"  Too many errors at 0x{addr:06x}, stopping pass")
                    break

            if pages_written % 100 == 0 and pages_written > 0:
                sys.stdout.write(f"\r  Written {pages_written} pages, skipped {pages_skipped} (0xFF)...")
                sys.stdout.flush()

        print(f"\r  Pass {pass_num}: {pages_written} pages written, {pages_skipped} skipped, {errors} errors")

        # Quick verification of first few KB
        sample = ch.read_data(0, 256)
        match = sum(1 for a, b in zip(sample, vbios[:256]) if a == b)
        print(f"  First 256 bytes: {match}/256 match ({match/256*100:.1f}%)")

        if match == 256:
            print("  First page PERFECT! Checking full chip...")
            # Read full VBIOS region in chunks
            all_match = True
            total_diff = 0
            for check_addr in range(0, vbios_end, 4096):
                chunk = ch.read_data(check_addr, min(4096, vbios_end - check_addr))
                expected = vbios[check_addr:check_addr + len(chunk)]
                diff = sum(1 for a, b in zip(chunk, expected) if a != b)
                total_diff += diff
            if total_diff == 0:
                print("  FULL VBIOS REGION: PERFECT MATCH!")
                print("  Done! Reassemble the laptop and test.")
                return
            else:
                print(f"  Full check: {total_diff} bytes still differ, continuing...")

    # Final full readback
    print("\n=== Final verification ===")
    total_match = 0
    total_bytes = 0
    for addr in range(0, vbios_end, 4096):
        chunk_len = min(4096, vbios_end - addr)
        chunk = ch.read_data(addr, chunk_len)
        expected = vbios[addr:addr + chunk_len]
        m = sum(1 for a, b in zip(chunk, expected) if a == b)
        total_match += m
        total_bytes += chunk_len
    print(f"Final: {total_match}/{total_bytes} bytes match ({total_match/total_bytes*100:.2f}%)")


if __name__ == "__main__":
    main()
