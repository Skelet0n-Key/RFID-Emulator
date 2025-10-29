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
# IRQ pin is not used in this library's polling mode
# irq = Pin(15, Pin.IN)
irq = None  # Set to None

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

# Variable to store the Block 0 data read from a card
saved_block_0 = None

# --- PN532 Initialization ---
print("Initializing PN532...")
pn532 = nfc.PN532(spi, cs, rst, irq)
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {}.{}'.format(ver, rev))
pn532.SAM_configuration()


def calculate_bcc(uid_bytes):
    """
    Calculates the BCC (XOR checksum) for a 4-byte MIFARE UID.
    """
    if len(uid_bytes) != 4:
        raise ValueError("UID must be 4 bytes long")
    bcc = 0
    for byte in uid_bytes:
        bcc ^= byte
    return bcc


def read_source_card_data(dev, timeout_ms=5000):
    """
    Waits for a source card, authenticates block 0, validates its BCC, 
    and reads the 16-byte block.
    Returns the 16 bytes of block 0, or None if it fails.
    """
    print('Waiting for SOURCE card...')
    print('Present the card you want to CLONE.')
    start = time.ticks_ms()
    uid = None
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        # Check for a card
        uid = dev.read_passive_target(timeout=100)
        if uid is not None:
            # Card found, break out of the loop
            break
        time.sleep(0.1)

    if not uid:
        print('CARD NOT FOUND')
        return None

    uid_string = "".join(["{:02X}".format(i) for i in uid])
    print(f"Found source card with UID: {uid_string}")

    # Authenticate block 0 (or any block in sector 0) to read it.
    # We'll try a common default key, KEY_DEFAULT_B (all 0xFFs)
    print("Trying to authenticate with default key FF FF FF FF FF FF...")
    if not dev.mifare_classic_authenticate_block(uid, 0, nfc.MIFARE_CMD_AUTH_B, nfc.KEY_DEFAULT_B):
        print("Failed to authenticate block 0 with default key.")
        print("Note: Card must use the default key FF FF FF FF FF FF for this to work.")
        return None

    print("Authentication successful.")

    # Read block 0
    block0_data = dev.mifare_classic_read_block(0)

    if not block0_data:
        print("Failed to read block 0.")
        return None

    print(f"Successfully read Block 0: {[hex(b) for b in block0_data]}")

    # --- BCC SAFETY CHECK ---
    print("Validating source card BCC...")
    card_uid_part = block0_data[0:4]
    card_bcc_part = block0_data[4]

    calculated_bcc = calculate_bcc(card_uid_part)

    if card_bcc_part == calculated_bcc:
        print(f"BCC is valid! (Read: 0x{card_bcc_part:02X}, Calculated: 0x{calculated_bcc:02X})")
        return block0_data
    else:
        print("--- !!! BCC VALIDATION FAILED !!! ---")
        print(f"Read UID: {[hex(b) for b in card_uid_part]}")
        print(f"Read BCC: 0x{card_bcc_part:02X}")
        print(f"Calculated BCC: 0x{calculated_bcc:02X}")
        print("This card may be damaged or non-standard. Aborting clone to prevent bricking.")
        return None
    # --- END OF BCC CHECK ---


def write_data_to_clone(dev, block_data, timeout_ms=10000):
    """
    Waits for a programmable card and writes the saved block 0 data to it.
    This requires a special UID-modifiable card.
    """
    print("Waiting for TARGET card...")
    print("Present your UID-MODIFIABLE (magic) card.")

    # Wait for a target card to appear
    start_wait = time.ticks_ms()
    target_uid = None
    while time.ticks_diff(time.ticks_ms(), start_wait) < timeout_ms:
        target_uid = dev.read_passive_target(timeout=100)
        if target_uid is not None:
            break
        time.sleep(0.1)

    if not target_uid:
        print("No target card found to write to. Aborting.")
        red_LED.value(1)
        time.sleep(0.5)
        red_LED.value(0)
        return

    target_uid_string = "".join(["{:02X}".format(i) for i in target_uid])
    print(f"Found target card with UID: {target_uid_string}")

    # For "Gen2" or "lab 401" cards, we can try a normal authentication
    # and then a standard write command to block 0.

    print("Attempting to authenticate target card...")
    # We must authenticate with the card's *current* key.
    # For a blank/new magic card, this is often the default key.
    if not dev.mifare_classic_authenticate_block(target_uid, 0, nfc.MIFARE_CMD_AUTH_B, nfc.KEY_DEFAULT_B):
        print("Failed to authenticate target card with default key.")
        red_LED.value(1)
        time.sleep(0.5)
        red_LED.value(0)
        return

    print("Target card authenticated. Attempting to write to Block 0...")

    # Now, try to write the saved block 0 data
    if dev.mifare_classic_write_block(0, block_data):
        print("SUCCESS! Block 0 written.")
        print(f"Wrote data: {[hex(b) for b in block_data]}")
        green_LED.value(1)
        time.sleep(1)
        green_LED.value(0)

        print("\n--- CLONE COMPLETE ---")
        print("Verify the new UID by scanning it again (press Scan button).")
    else:
        print("Error: Failed to write to block 0.")
        print("This may not be a 'Direct Write' card, or it may be faulty.")
        red_LED.value(1)
        time.sleep(1)
        red_LED.value(0)


# --- Main Loop ---
print("\n--- MIFARE 1K Cloner Ready (with BCC Check) ---")
print("Press SCAN button to read from source card.")
print("Press WRITE button to write to target card.")
while True:
    # Check if the scan button is pressed
    if scan_button.value() == 0:
        time.sleep(0.1)  # Debounce delay
        print("\n--- READ SOURCE CARD ---")
        scan_LED.value(1)

        scanned_data = read_source_card_data(pn532)
        scan_LED.value(0)

        if scanned_data:
            green_LED.value(1)
            saved_block_0 = scanned_data  # Save the 16-byte block
            print("Block 0 data saved.")
            time.sleep(0.5)
            green_LED.value(0)
        else:
            red_LED.value(1)
            print("Scan failed. No data was saved.")
            time.sleep(0.5)
            red_LED.value(0)

        # Wait for the button to be released
        while scan_button.value() == 0:
            pass
        print("\n--- Ready for next command ---")

    # Check if the write button is pressed
    if write_button.value() == 0:
        time.sleep(0.1)  # Debounce delay
        print("\n--- WRITE TO TARGET CARD ---")
        write_LED.value(1)

        if saved_block_0 is None:
            print("Error: No data has been saved from a source card.")
            # Blink red LED
            red_LED.value(1)
            time.sleep(0.25)
            red_LED.value(0)
            time.sleep(0.25)
            red_LED.value(1)
            time.sleep(0.25)
            red_LED.value(0)
        else:
            data_string = "".join(["{:02X}".format(i) for i in saved_block_0])
            print(f"Writing data: {data_string}")
            write_data_to_clone(pn532, saved_block_0)

        write_LED.value(0)

        # Wait for the button to be released
        while write_button.value() == 0:
            pass
        print("\n--- Ready for next command ---")

    # A small delay to prevent the loop from running too fast
    time.sleep(0.05)
