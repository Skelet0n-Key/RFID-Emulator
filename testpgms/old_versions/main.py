from machine import Pin, SPI
import NFC_PN532 as nfc
import time

# --- NFC/SPI Setup ---
spi = SPI(0,
          baudrate=1152000,
          polarity=0,
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(18),
          mosi=Pin(19),
          miso=Pin(16))

cs = Pin(17, Pin.OUT)
cs.value(1)
rst = Pin(20, Pin.OUT)
rst.value(1)
irq = Pin(15, Pin.IN)
scan_LED = Pin(2, Pin.OUT)
scan_LED.value(0)
write_LED = Pin(3, Pin.OUT)
write_LED.value(0)
green_LED = Pin(4, Pin.OUT)
green_LED.value(0)
red_LED = Pin(5, Pin.OUT)
red_LED.value(0)


# Initialize GPIO pins for the buttons.
# We are using internal pull-ups, so the buttons should be wired
# to connect the pin to ground when pressed.
scan_button = Pin(14, Pin.IN, Pin.PULL_UP)
write_button = Pin(13, Pin.IN, Pin.PULL_UP)

# Variable to store the UID read from a card
saved_uid = None

# --- PN532 Initialization ---
pn532 = nfc.PN532(spi, cs, rst, irq)
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {}.{}'.format(ver, rev))
pn532.SAM_configuration()


def read_card_uid(dev, timeout_ms=5000):
    """
    Waits for a card to be presented and reads its UID.
    Returns the UID as a bytearray, or None if no card is found.
    """
    print('Waiting for a card...')
    start = time.ticks_ms()
    uid = None
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        # Check for a card
        uid = dev.read_passive_target(timeout=100)
        if uid is not None:
            # Card found, break out of the loop
            break
        time.sleep(0.1)

    if uid:
        uid_string = "".join(["{:02X}".format(i) for i in uid])
        print(f"Found card with UID: {uid_string}")
        return uid
    else:
        print('CARD NOT FOUND')
        return None


def write_uid_to_card(dev, uid_to_write, timeout_ms=10000):
    """
    Waits for a programmable card and writes the saved UID to it.
    This function writes the UID to data blocks (starting at block 4),
    it does not change the actual read-only UID of the card.
    """
    print("Waiting for card...")

    # Wait for a target card to appear
    target_uid = read_card_uid(dev, timeout_ms)

    if not target_uid:
        print("No target card found to write to. Aborting.")
        return

    print("Attempting to write...")

    # The UID will be written to block 4 onwards.
    # NTAG cards have 4-byte blocks.
    block_number = 0

    # We need to pad the UID to be a multiple of 4 bytes
    data_to_write = bytearray(uid_to_write)
    while len(data_to_write) % 4 != 0:
        data_to_write.append(0)

    # Write the data in 4-byte chunks
    for i in range(0, len(data_to_write), 4):
        chunk = data_to_write[i:i+4]
        print(f"Writing to block {block_number}: {[hex(b) for b in chunk]}...")

        # Authenticate the block first (for MIFARE Classic, may not be needed for all cards)
        # Using a default key B. This might fail if the card has different keys.
        if dev.mifare_classic_authenticate_block(target_uid, block_number, nfc.MIFARE_CMD_AUTH_B, nfc.KEY_DEFAULT_B):
            # Write the 4-byte chunk
            if dev.ntag2xx_write_block(block_number, chunk):
                green_LED.value(1)
                print(f"Block {block_number} written successfully.")
                time.sleep(0.5)
                green_LED.value(0)
            else:
                red_LED.value(1)
                print(f"Error: Failed to write to block {block_number}.")
                time.sleep(0.5)
                red_LED.value(0)
                return  # Stop if one write fails
        else:
            print(f"Error: Failed to authenticate block {block_number}.")
            # Try writing without authenticating for NTAG cards
            print("Trying to write without authentication...")
            if dev.ntag2xx_write_block(block_number, chunk):
                print(f"Block {block_number} written successfully")
            else:
                red_LED.value(1)
                print(f"Failed to write to block {block_number}")
                time.sleep(0.5)
                red_LED.value(0)
                return

        block_number += 1

    print("\n--- Write process completed. ---")


# --- Main Loop ---
while True:
    # Check if the scan button is pressed
    if scan_button.value() == 0:
        time.sleep(0.1)  # Debounce delay
        print("\nScanning for card...")
        scan_LED.value(1)

        scanned_uid = read_card_uid(pn532)
        scan_LED.value(0)
        if scanned_uid:
            green_LED.value(1)
            saved_uid = scanned_uid
            print("UID saved")
            time.sleep(0.5)
            green_LED.value(0)
        else:
            red_LED.value(1)
            print("Scan failed. No UID was saved.")
            time.sleep(0.5)
            red_LED.value(0)

        # Wait for the button to be released
        while scan_button.value() == 0:
            pass

    # Check if the write button is pressed
    if write_button.value() == 0:
        time.sleep(0.1)  # Debounce delay
        print("\nWriting to card...")
        write_LED.value(1)

        if saved_uid is None:
            print("Error: No UID has been saved.")
            time.sleep(0.25)
            write_LED.value(0)
            time.sleep(0.25)
            write_LED.value(1)
            time.sleep(0.25)
            write_LED.value(0)
            time.sleep(0.25)
            write_LED(1)
            time.sleep(0.25)
        else:
            uid_string = "".join(["{:02X}".format(i) for i in saved_uid])
            print(f"Writing: {uid_string}")
            write_uid_to_card(pn532, saved_uid)
        write_LED.value(0)

        # Wait for the button to be released
        while write_button.value() == 0:
            pass
    # A small delay to prevent the loop from running too fast
    time.sleep(0.1)
