#!/usr/bin/env python3
"""Clear ALL W25Q16JW write protection: SR1/SR2 block protect, SR3 WPS/Individual Block Locks, and Global Block Unlock.
Targets: Winbond W25Q16JWNIQ (1.8V SOP8, JEDEC ID EF6015) on Razer Blade 15 RTX 3080.
Also compatible with W25Q16FW (same JEDEC ID, same register layout)."""
import usb.core
import usb.util
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
SPI_WRITE_ENABLE       = 0x06
SPI_WRITE_SR1          = 0x01
SPI_WRITE_SR2          = 0x31
SPI_WRITE_SR3          = 0x11
SPI_READ_SR1           = 0x05
SPI_READ_SR2           = 0x35
SPI_READ_SR3           = 0x15
SPI_READ_JEDEC_ID      = 0x9F
SPI_GLOBAL_BLOCK_UNLOCK = 0x98
SPI_READ_BLOCK_LOCK    = 0x3D
SPI_INDIVIDUAL_UNLOCK  = 0x39

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

def read_jedec_id(dev):
    resp = ch341_spi_transfer(dev, [SPI_READ_JEDEC_ID, 0x00, 0x00, 0x00])
    return resp[1], resp[2], resp[3]

def read_status_register(dev, cmd):
    resp = ch341_spi_transfer(dev, [cmd, 0x00])
    return resp[1]

def write_enable(dev):
    ch341_spi_transfer(dev, [SPI_WRITE_ENABLE])

def wait_busy(dev, timeout_s=2):
    """Poll SR1 BUSY bit until chip is ready"""
    start = time.time()
    while time.time() - start < timeout_s:
        sr1 = read_status_register(dev, SPI_READ_SR1)
        if sr1 & 0x01 == 0:
            return True
        time.sleep(0.01)
    return False

def write_status_register(dev, reg_cmd, value):
    write_enable(dev)
    ch341_spi_transfer(dev, [reg_cmd, value])
    if not wait_busy(dev):
        print("  WARNING: Chip still BUSY after SR write")

def global_block_unlock(dev):
    """Send Write Enable then Global Block Unlock (0x98) to unlock all individual block locks"""
    write_enable(dev)
    ch341_spi_transfer(dev, [SPI_GLOBAL_BLOCK_UNLOCK])
    if not wait_busy(dev):
        print("  WARNING: Chip still BUSY after Global Block Unlock")

def read_block_lock(dev, addr):
    """Read the individual lock bit for a block at the given address"""
    a2 = (addr >> 16) & 0xFF
    a1 = (addr >> 8) & 0xFF
    a0 = addr & 0xFF
    resp = ch341_spi_transfer(dev, [SPI_READ_BLOCK_LOCK, a2, a1, a0, 0x00])
    return resp[4] & 0x01

def print_sr_details(sr1, sr2, sr3):
    print(f"  Status Register 1: 0x{sr1:02X} ({sr1:08b})")
    print(f"    SRP0={sr1>>7 & 1}  SEC={sr1>>6 & 1}  TB={sr1>>5 & 1}  BP2={sr1>>4 & 1}  BP1={sr1>>3 & 1}  BP0={sr1>>2 & 1}  WEL={sr1>>1 & 1}  BUSY={sr1 & 1}")
    print(f"  Status Register 2: 0x{sr2:02X} ({sr2:08b})")
    print(f"    SUS={sr2>>7 & 1}  CMP={sr2>>6 & 1}  LB3={sr2>>5 & 1}  LB2={sr2>>4 & 1}  LB1={sr2>>3 & 1}  res={sr2>>2 & 1}  QE={sr2>>1 & 1}  SRP1={sr2 & 1}")
    print(f"  Status Register 3: 0x{sr3:02X} ({sr3:08b})")
    print(f"    HOLD/RST={sr3>>7 & 1}  DRV1={sr3>>6 & 1}  DRV0={sr3>>5 & 1}  res={sr3>>4 & 1}  res={sr3>>3 & 1}  WPS={sr3>>2 & 1}  res={sr3>>1 & 1}  res={sr3 & 1}")

    # Decode protection state
    bp = (sr1 >> 2) & 0x07
    sec = (sr1 >> 6) & 0x01
    tb = (sr1 >> 5) & 0x01
    cmp = (sr2 >> 6) & 0x01
    wps = (sr3 >> 2) & 0x01
    srp0 = (sr1 >> 7) & 0x01
    srp1 = sr2 & 0x01

    print()
    if wps:
        print("  >> WPS=1: Individual Block Lock mode ACTIVE")
        print("     All blocks default LOCKED on every power cycle!")
        print("     BP bits in SR1 are IGNORED in this mode.")
    else:
        print("  >> WPS=0: Legacy Block Protect mode (SR1 BP bits)")
        if bp == 0 and cmp == 0:
            print("     No blocks protected (BP=000, CMP=0)")
        else:
            print(f"     BP={bp:03b} SEC={sec} TB={tb} CMP={cmp} — some blocks ARE protected!")

    if srp0 == 0 and srp1 == 0:
        print("  >> SRP=00: Software protection only (/WP pin ignored)")
    elif srp0 == 1 and srp1 == 0:
        print("  >> SRP=10: Hardware protection (/WP pin controls SR writes)")
    elif srp0 == 0 and srp1 == 1:
        print("  >> SRP=01: Power Supply Lock-Down (SR locked until power cycle)")
    else:
        print("  >> SRP=11: OTP Lock (SR PERMANENTLY read-only!)")

def main():
    print("=" * 60)
    print("  W25Q16JW Full Write Protection Clearer")
    print("  Handles: SR1/SR2 block protect, SR3 WPS,")
    print("           Individual Block Locks, Global Block Unlock")
    print("=" * 60)
    print()

    dev = find_ch341a()
    print("[+] CH341A found!")

    # Verify chip identity
    mfr, mem_type, capacity = read_jedec_id(dev)
    jedec = f"{mfr:02X} {mem_type:02X} {capacity:02X}"
    print(f"[+] JEDEC ID: {jedec}")

    if mfr == 0xEF and mem_type == 0x60 and capacity == 0x15:
        print("    Confirmed: Winbond W25Q16JW (1.8V, 16Mbit)")
    elif mfr == 0x00 and mem_type == 0x00:
        print("    ERROR: Chip returned all zeros — no SPI communication!")
        print("    Check clip connection and 1.8V adapter.")
        sys.exit(1)
    else:
        print(f"    WARNING: Unexpected chip ID! Expected EF 60 15")
        resp = input("    Continue anyway? (yes/no): ")
        if resp.strip().lower() != "yes":
            sys.exit(1)
    print()

    # Read current status registers
    sr1 = read_status_register(dev, SPI_READ_SR1)
    sr2 = read_status_register(dev, SPI_READ_SR2)
    sr3 = read_status_register(dev, SPI_READ_SR3)

    print("[*] Current protection state:")
    print_sr_details(sr1, sr2, sr3)
    print()

    wps = (sr3 >> 2) & 0x01
    bp = (sr1 >> 2) & 0x07
    cmp = (sr2 >> 6) & 0x01
    srp0 = (sr1 >> 7) & 0x01
    srp1 = sr2 & 0x01
    qe = (sr2 >> 1) & 0x01

    # Check if anything needs clearing
    needs_work = False
    if bp != 0 or cmp != 0:
        needs_work = True
        print("[!] Block protection bits set in SR1/SR2")
    if srp0 or srp1:
        needs_work = True
        print("[!] Status Register Protection (SRP) is active")
    if wps:
        needs_work = True
        print("[!] WPS=1: Individual Block Lock mode active — blocks locked on power-up!")

    # Always check individual block locks if WPS is set
    if wps:
        print()
        print("[*] Checking individual block locks (WPS=1 mode)...")
        locked_count = 0
        for addr in range(0, 0x200000, 0x10000):  # Check each 64KB block
            lock = read_block_lock(dev, addr)
            if lock:
                locked_count += 1
        print(f"    {locked_count}/32 blocks are individually locked")
        if locked_count > 0:
            needs_work = True

    if not needs_work:
        # Even if registers look clean, still do Global Block Unlock as safety measure
        print()
        print("[*] No protection bits detected in status registers.")
        print("[*] Sending Global Block Unlock as safety measure...")
        global_block_unlock(dev)
        print("[+] Done. Chip should be fully writable.")
        return

    print()
    print("[*] Clearing ALL write protection...")
    print()

    # Step 1: Clear SRP0/SRP1 first (must be done before other SR writes if hardware WP is active)
    if srp0 or srp1:
        print("[1] Clearing SRP0 and SRP1...")
        # Write SR1 with SRP0=0, keep other bits for now
        new_sr1 = sr1 & 0x7E  # Clear SRP0 (bit 7), keep bits 6-1
        write_status_register(dev, SPI_WRITE_SR1, new_sr1)
        # Write SR2 with SRP1=0, keep QE
        new_sr2 = sr2 & 0xFE  # Clear SRP1 (bit 0)
        write_status_register(dev, SPI_WRITE_SR2, new_sr2)
        print("    SRP cleared")

    # Step 2: Clear block protection bits in SR1 (BP0-BP2, SEC, TB)
    if bp != 0 or (sr1 & 0x60):  # Check BP bits and SEC/TB
        print("[2] Clearing SR1 block protection (BP0-BP2, SEC, TB)...")
        new_sr1 = 0x00  # All protection off
        write_status_register(dev, SPI_WRITE_SR1, new_sr1)
        print("    SR1 cleared")
    else:
        print("[2] SR1 block protection already clear")

    # Step 3: Clear CMP in SR2, preserve QE
    if cmp:
        print("[3] Clearing SR2 CMP bit...")
        new_sr2 = (qe << 1)  # Keep only QE bit
        write_status_register(dev, SPI_WRITE_SR2, new_sr2)
        print("    SR2 CMP cleared")
    else:
        print("[3] SR2 CMP already clear")

    # Step 4: Clear WPS in SR3 (switch back to legacy BP mode)
    if wps:
        print("[4] Clearing WPS bit in SR3 (disabling Individual Block Lock mode)...")
        new_sr3 = sr3 & ~0x04  # Clear WPS (bit 2), keep DRV bits
        write_status_register(dev, SPI_WRITE_SR3, new_sr3)
        print("    WPS cleared — switched to legacy block protect mode")
    else:
        print("[4] WPS already clear (legacy BP mode)")

    # Step 5: Global Block Unlock — clears all individual block lock bits
    # Do this regardless, as a safety measure even after clearing WPS
    print("[5] Sending Global Block Unlock (0x98)...")
    global_block_unlock(dev)
    print("    All individual block locks cleared")

    time.sleep(0.1)

    # Verify
    print()
    print("[*] Verifying final state...")
    sr1_new = read_status_register(dev, SPI_READ_SR1)
    sr2_new = read_status_register(dev, SPI_READ_SR2)
    sr3_new = read_status_register(dev, SPI_READ_SR3)
    print_sr_details(sr1_new, sr2_new, sr3_new)

    # Check if protection is fully cleared
    bp_new = (sr1_new >> 2) & 0x07
    cmp_new = (sr2_new >> 6) & 0x01
    wps_new = (sr3_new >> 2) & 0x01
    srp0_new = (sr1_new >> 7) & 0x01
    srp1_new = sr2_new & 0x01

    all_clear = True
    if bp_new != 0 or cmp_new:
        print()
        print("  WARNING: Block protection bits still set!")
        all_clear = False
    if srp0_new or srp1_new:
        print()
        print("  WARNING: SRP still active!")
        all_clear = False
    if wps_new:
        print()
        print("  WARNING: WPS still set!")
        # Check individual locks again
        locked = 0
        for addr in range(0, 0x200000, 0x10000):
            if read_block_lock(dev, addr):
                locked += 1
        if locked > 0:
            print(f"  WARNING: {locked}/32 blocks still individually locked!")
            all_clear = False
        else:
            print("  (But all individual block locks are cleared via Global Unlock)")

    print()
    if all_clear:
        print("=" * 60)
        print("  SUCCESS — ALL write protection cleared!")
        print("  Chip is fully writable. You can now erase and flash.")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  PARTIAL — Some protection may remain.")
        print("  Check /WP pin (pin 3) — GPU board may hold it low.")
        print("  If SRP=10, /WP must be HIGH to allow SR writes.")
        print("=" * 60)

if __name__ == "__main__":
    main()
