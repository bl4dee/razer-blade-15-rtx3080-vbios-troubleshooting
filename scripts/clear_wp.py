#!/usr/bin/env python3
"""Clear W25Q16JW write protection by writing 0x00 to Status Register 1 and 2 via CH341A"""
import usb.core
import usb.util
import struct
import time
import sys

# CH341A USB identifiers
CH341_VID = 0x1a86
CH341_PID = 0x5512

# CH341A SPI commands
CH341A_CMD_SPI_STREAM = 0xA8
CH341A_CMD_UIO_STREAM = 0xAB
CH341A_CMD_UIO_STM_IN  = 0x00
CH341A_CMD_UIO_STM_DIR = 0x40
CH341A_CMD_UIO_STM_OUT = 0x80
CH341A_CMD_UIO_STM_END = 0x20

# SPI Flash commands
SPI_WRITE_ENABLE  = 0x06
SPI_WRITE_SR1     = 0x01
SPI_WRITE_SR2     = 0x31
SPI_READ_SR1      = 0x05
SPI_READ_SR2      = 0x35
SPI_READ_SR3      = 0x15

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

def ch341_spi_transfer(dev, data):
    """Send SPI data and receive response via CH341A stream mode"""
    # CS low
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x36, CH341A_CMD_UIO_STM_DIR | 0x3F, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)

    # SPI transfer
    pkt = bytearray([CH341A_CMD_SPI_STREAM]) + bytearray(data)
    dev.write(BULK_EP_OUT, pkt)
    response = dev.read(BULK_EP_IN, len(data), timeout=1000)

    # CS high
    cmd = bytearray([CH341A_CMD_UIO_STREAM, CH341A_CMD_UIO_STM_OUT | 0x37, CH341A_CMD_UIO_STM_END])
    dev.write(BULK_EP_OUT, cmd)

    return bytes(response)

def read_status_register(dev, cmd):
    resp = ch341_spi_transfer(dev, [cmd, 0x00])
    return resp[1]

def write_enable(dev):
    ch341_spi_transfer(dev, [SPI_WRITE_ENABLE])

def write_status_register(dev, reg_cmd, value):
    write_enable(dev)
    ch341_spi_transfer(dev, [reg_cmd, value])
    time.sleep(0.05)  # Wait for write to complete

def main():
    print("=== W25Q16JW Write Protection Clearer ===")
    print()

    dev = find_ch341a()
    print("CH341A found!")
    print()

    # Read current status registers
    sr1 = read_status_register(dev, SPI_READ_SR1)
    sr2 = read_status_register(dev, SPI_READ_SR2)
    sr3 = read_status_register(dev, SPI_READ_SR3)

    print(f"Status Register 1: 0x{sr1:02X} (binary: {sr1:08b})")
    print(f"  SRP0={sr1>>7 & 1}  SEC={sr1>>6 & 1}  TB={sr1>>5 & 1}  BP2={sr1>>4 & 1}  BP1={sr1>>3 & 1}  BP0={sr1>>2 & 1}  WEL={sr1>>1 & 1}  BUSY={sr1 & 1}")
    print(f"Status Register 2: 0x{sr2:02X} (binary: {sr2:08b})")
    print(f"  SUS={sr2>>7 & 1}  CMP={sr2>>6 & 1}  LB3={sr2>>5 & 1}  LB2={sr2>>4 & 1}  LB1={sr2>>3 & 1}  res={sr2>>2 & 1}  QE={sr2>>1 & 1}  SRP1={sr2 & 1}")
    print(f"Status Register 3: 0x{sr3:02X} (binary: {sr3:08b})")
    print()

    if sr1 & 0x7C == 0 and sr2 & 0x41 == 0:
        print("No block protection bits are set. Write protection is already cleared!")
        return

    print("Block protection bits detected! Clearing...")
    print()

    # Clear SR1: set BP0=BP1=BP2=SEC=TB=SRP0 = 0
    new_sr1 = sr1 & 0x02  # Keep only WEL bit if set
    print(f"Writing SR1: 0x{new_sr1:02X}")
    write_status_register(dev, SPI_WRITE_SR1, new_sr1)

    # Clear SR2: set CMP=SRP1=0, keep QE as-is
    new_sr2 = sr2 & 0x02  # Keep QE bit
    print(f"Writing SR2: 0x{new_sr2:02X}")
    write_status_register(dev, SPI_WRITE_SR2, new_sr2)

    time.sleep(0.1)

    # Verify
    sr1_new = read_status_register(dev, SPI_READ_SR1)
    sr2_new = read_status_register(dev, SPI_READ_SR2)
    print()
    print(f"New Status Register 1: 0x{sr1_new:02X} (was 0x{sr1:02X})")
    print(f"New Status Register 2: 0x{sr2_new:02X} (was 0x{sr2:02X})")

    if sr1_new & 0x7C == 0:
        print()
        print("SUCCESS! Write protection cleared. You can now erase and flash.")
    else:
        print()
        print("WARNING: Protection bits may still be set. The chip might have hardware WP enabled.")
        print("Check if pin 3 (/WP) on the chip is being held low by the board.")

if __name__ == "__main__":
    main()
