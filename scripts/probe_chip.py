#!/usr/bin/env python3
"""Quick chip probe — reads JEDEC ID and status registers, retries on failure."""
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
BULK_EP_OUT = 0x02
BULK_EP_IN  = 0x82

def find_ch341a():
    dev = usb.core.find(idVendor=CH341_VID, idProduct=CH341_PID)
    if dev is None:
        print("ERROR: CH341A not found on USB")
        sys.exit(1)
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except:
        pass
    dev.set_configuration()
    return dev

def spi_transfer(dev, data):
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x36, CH341A_CMD_UIO_STM_DIR | 0x3F, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)
    pkt = bytearray([CH341A_CMD_SPI_STREAM]) + bytearray(data)
    dev.write(BULK_EP_OUT, pkt)
    response = dev.read(BULK_EP_IN, len(data), timeout=1000)
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x37, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)
    return bytes(response)

dev = find_ch341a()
print("CH341A found!")
print()

max_tries = 20
for i in range(1, max_tries + 1):
    try:
        # Read JEDEC ID
        resp = spi_transfer(dev, [0x9F, 0x00, 0x00, 0x00])
        mfr, mtype, cap = resp[1], resp[2], resp[3]
        jedec = f"{mfr:02X} {mtype:02X} {cap:02X}"

        # Read status registers
        sr1 = spi_transfer(dev, [0x05, 0x00])[1]
        sr2 = spi_transfer(dev, [0x35, 0x00])[1]
        sr3 = spi_transfer(dev, [0x15, 0x00])[1]

        print(f"[{i:2d}] JEDEC={jedec}  SR1=0x{sr1:02X} SR2=0x{sr2:02X} SR3=0x{sr3:02X}", end="")

        if mfr == 0xEF and mtype == 0x60 and cap == 0x15:
            wps = (sr3 >> 2) & 1
            bp = (sr1 >> 2) & 0x07
            print(f"  << W25Q16JW FOUND!  WPS={wps} BP={bp:03b}")
            print()
            print(f"  SR1: SRP0={sr1>>7&1} SEC={sr1>>6&1} TB={sr1>>5&1} BP2={sr1>>4&1} BP1={sr1>>3&1} BP0={sr1>>2&1}")
            print(f"  SR2: CMP={sr2>>6&1} LB3={sr2>>5&1} LB2={sr2>>4&1} LB1={sr2>>3&1} QE={sr2>>1&1} SRP1={sr2&1}")
            print(f"  SR3: DRV1={sr3>>6&1} DRV0={sr3>>5&1} WPS={wps}")
            if wps:
                print()
                print("  !! WPS=1: Individual Block Lock mode — all blocks locked on power-up!")
                print("  !! Run clear_wp.py to send Global Block Unlock")
            if bp:
                print(f"  !! Block protection active (BP={bp:03b})")
            if bp == 0 and wps == 0:
                print()
                print("  No write protection detected. Chip should be writable.")
            sys.exit(0)
        elif mfr == 0xFF and mtype == 0xFF:
            print("  (no response — MISO high/floating)")
        elif mfr == 0x00 and mtype == 0x00:
            print("  (no response — MISO low/grounded)")
        else:
            print(f"  (unknown chip)")

    except Exception as e:
        print(f"[{i:2d}] ERROR: {e}")

    time.sleep(0.5)

print()
print(f"Chip not detected after {max_tries} attempts.")
print("Troubleshooting:")
print("  - Reseat the SOP8 clip (wiggle and re-clip)")
print("  - Check pin 1 alignment (blue dot on chip)")
print("  - Make sure laptop is fully powered off + battery disconnected")
print("  - Try a different USB port (USB 2.0 preferred)")
