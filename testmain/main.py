from machine import Pin, SPI, I2C
import NFC_PN532 as nfc
from ssd1306 import SSD1306_I2C
import time
import ujson
import os

# ==== I2C setup ====
i2c = I2C(1, scl=Pin(3), sda=Pin(2))  # I2C1 uses GP2 (SDA) and GP3 (SCL)

# ==== OLED setup ====
WIDTH = 128
HEIGHT = 32  # most 0.91" displays are 128x32
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

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
irq = None # Set to None
# Initialize GPIO pins for the buttons.
# We are using internal pull-ups, so the buttons should be wired
# to connect the pin to ground when pressed.
up_button = Pin(14, Pin.IN, Pin.PULL_UP)
sel_button = Pin(13, Pin.IN, Pin.PULL_UP)
down_button = Pin(5, Pin.IN, Pin.PULL_UP)


# menus
mainMenu = [" ", "Mifare Classic", "NTAG", "Clear Saved", " "]
mifareMenu = [" ", "..", "Mifare Read", "Write current", "Save current", "Load from saved", " "]
ntagMenu = [" ", "..", "NTAG read", "Write current", "Save current", "Load from saved", " "]

# saved data
MIFARE_FILE = "saved_mifare.json"
NTAG_FILE = "saved_ntag.json"
savedUIDsMifare = []
savedUIDsNTAG = []
saved_block_0 = None

# --- PN532 Initialization ---
print("Initializing PN532...")
pn532 = nfc.PN532(spi, cs, rst, irq)
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {}.{}'.format(ver, rev))
pn532.SAM_configuration()

# initialize screen and menu
currentMenu = mainMenu
currentOptionIndex = 1
driverSelection = None

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
    oled_print("Waiting for SOURCE card...", clear=True)
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
        oled_print("CARD NOT FOUND", clear=True)
        return None
        
    uid_string = "".join(["{:02X}".format(i) for i in uid])
    print(f"Found source card with UID: {uid_string}")
    oled_print(f"Found:\n{uid_string}", clear=True)

    # Authenticate block 0 (or any block in sector 0) to read it.
    # We'll try a common default key, KEY_DEFAULT_B (all 0xFFs)
    print("Trying to authenticate with default key FF FF FF FF FF FF...")
    oled_print("Authenticating\nsource card...", clear=False)
    if not dev.mifare_classic_authenticate_block(uid, 0, nfc.MIFARE_CMD_AUTH_B, nfc.KEY_DEFAULT_B):
        print("Failed to authenticate block 0 with default key.")
        print("Note: Card must use the default key FF FF FF FF FF FF for this to work.")
        oled_print("Authentication\nfailed!", clear=True)
        return None
    
    print("Authentication successful.")
    oled_print("Authentication\nsuccessful!", clear=True)
    
    # Read block 0
    block0_data = dev.mifare_classic_read_block(0)
    
    if not block0_data:
        print("Failed to read block 0.")
        oled_print("Read Block 0\nfailed!", clear=True)
        time.sleep(1)
        return None

    print(f"Successfully read Block 0: {[hex(b) for b in block0_data]}")
    oled_print("Read Block 0\nsuccessful!", clear=True)
    time.sleep(1)

    # --- BCC SAFETY CHECK ---
    print("Validating source card BCC...")
    oled_print("Validating\nsource card BCC...", clear=True)
    card_uid_part = block0_data[0:4]
    card_bcc_part = block0_data[4]
    
    calculated_bcc = calculate_bcc(card_uid_part)
    
    if card_bcc_part == calculated_bcc:
        print(f"BCC is valid! (Read: 0x{card_bcc_part:02X}, Calculated: 0x{calculated_bcc:02X})")
        oled_print("BCC VALIDATION\nSUCCESS!", clear=True)
        time.sleep(0.5)
        oled_print("Block 0 Data:\n" + "".join(["{:02X}".format(b) for b in block0_data]), clear=True)
        time.sleep(3)
        return block0_data
    else:
        print("--- !!! BCC VALIDATION FAILED !!! ---")
        oled_print("!!! BCC VALIDATION\nFAILED !!!", clear=True)
        print(f"Read UID: {[hex(b) for b in card_uid_part]}")
        print(f"Read BCC: 0x{card_bcc_part:02X}")
        print(f"Calculated BCC: 0x{calculated_bcc:02X}")
        print("This card may be damaged or non-standard. Aborting clone to prevent bricking.")
        time.sleep(0.5)
        return None
    # --- END OF BCC CHECK ---


def write_data_to_clone(dev, block_data, timeout_ms=10000):
    """
    Waits for a programmable card and writes the saved block 0 data to it.
    This requires a special UID-modifiable card.
    """
    print("Waiting for TARGET card...")
    oled_print("Waiting for TARGET card...", clear=True)
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
        oled_print("No target card found.\nAborting.", clear=True)
        return

    target_uid_string = "".join(["{:02X}".format(i) for i in target_uid])
    print(f"Found target card with UID: {target_uid_string}")
    oled_print(f"Found target card:\n{target_uid_string}", clear=True)

    # For "Gen2" or "lab 401" cards, we can try a normal authentication
    # and then a standard write command to block 0.
    
    print("Attempting to authenticate target card...")
    # authenticate with the card's current key.
    # For a blank/new magic card, this is often the default key.
    if not dev.mifare_classic_authenticate_block(target_uid, 0, nfc.MIFARE_CMD_AUTH_B, nfc.KEY_DEFAULT_B):
        print("Failed to authenticate target card with default key.")
        oled_print("Authentication\nfailed!", clear=True)
        time.sleep(1.5)
        return
        
    print("Target card authenticated. Attempting to write to Block 0...")
    oled_print("Writing to\nBlock 0...", clear=True)
    
    # Now, try to write the saved block 0 data
    if dev.mifare_classic_write_block(0, block_data):
        print("SUCCESS! Block 0 written.")
        oled_print("Write SUCCESS!", clear=True)
        print(f"Wrote data: {[hex(b) for b in block_data]}")
        oled_print(f"Wrote data:\n{''.join(['{:02X}'.format(b) for b in block_data])}", clear=True)
        time.sleep(1.5)
        return
    else:
        print("Error: Failed to write to block 0.")
        oled_print("Write FAILED!", clear=True)
        time.sleep(1.5) 
        return


def driver_select(selection):
    global saved_block_0
    if selection == 0: #scan mifare classic
        scanned_data = read_source_card_data(pn532)
    
        if scanned_data:
            saved_block_0 = scanned_data # Save the 16-byte block
            print("Block 0 data saved.")
            oled_print("Scan successful!\nData saved.", clear=True)
            time.sleep(1.5)
        else:
            print("Scan failed. No data was saved.")
            oled_print("Scan failed.\nNo data saved.", clear=True)  
            time.sleep(1.5)

    elif selection == 1:#write mifare classic
        print("Writing saved Block 0 data to target card...")
        if saved_block_0 is None:
            print("Error: No data has been saved from a source card.")
            oled_print("No saved data!\nScan first.", clear=True)
            time.sleep(1.5)
        else:
            data_string = "".join(["{:02X}".format(i) for i in saved_block_0])
            print(f"Writing data: {data_string}")
            oled_print(f"Writing data:\n{data_string}", clear=True)
            write_data_to_clone(pn532, saved_block_0)

    elif selection == 2: #save current mifare classic TODO
        oled_print("Saving current\nMIFARE UID...", clear=True)
        time.sleep(0.5)
        savedUIDsMifare.append(saved_block_0)
        save_list_to_file(savedUIDsMifare, MIFARE_FILE) 

    elif selection== 3: #display saved mifare classic uids TODO
        oled_print("Loading saved\nMIFARE UIDs...", clear=True)
        time.sleep(0.5)
        savedUIDsMifare = load_list_from_file(MIFARE_FILE)
        for index, data in enumerate(savedUIDsMifare):
            data_string = "".join(["{:02X}".format(b) for b in data])
            print(f"{index + 1}: {data_string}")
            oled_print(f"{index + 1}: {data_string}")

    elif selection == 4: 
        oled_print("NTAG read not\nimplemented", clear=True)
        time.sleep(1.5)

        
    elif selection == 5: 
        oled_print("NTAG write not\nimplemented", clear=True)
        time.sleep(1.5)

    elif selection == 6: 
        oled_print("Save current to\nNTAG list not\nimplemented", clear=True)
        time.sleep(1.5)

    elif selection == 7: 
        oled_print("Display saved\nNTAG UIDs not\nimplemented", clear=True)
        time.sleep(1.5)

    else: pass  # no action

# --- Save function ---
def save_list_to_file(data_list, filename):
    try:
        with open(filename, "w") as f:
            ujson.dump(data_list, f)
        print(f"Saved {len(data_list)} items to {filename}")
        oled_print(f"Saved {len(data_list)} items", clear=True)
    except Exception as e:
        print("Error saving file:", e)
        oled_print("Error saving file", clear=True)
    
    return

# --- Load function ---
def load_list_from_file(filename):
    try:
        with open(filename, "r") as f:
            data = ujson.load(f)
        print(f"Loaded {len(data)} items from {filename}")
        return data
    except Exception as e:
        print("Error loading file:", e)
        oled_print("Error loading file", clear=True)
        return []
    
# --- Clear saved function ---    
def clear_saved_list(list_variable, filename):
    # Clear the in-memory list
    list_variable.clear()
    
    # Overwrite the JSON file with an empty list
    try:
        with open(filename, "w") as f:
            ujson.dump([], f)
        print(f"Cleared {filename} and emptied the list.")
        oled_print(f"Cleared saved\nitems!", clear=True)
    except Exception as e:
        print("Error clearing saved file:", e)
        oled_print("Error clearing\nsaved items!", clear=True)

def oled_print(*args, sep=" ", end="\n", clear=True):
    """
    Works like Python's print(), but writes to the OLED display.
    Example: oled_print("Hello", 123)
    """
    text = sep.join(str(a) for a in args) + end

    if clear:
        oled.fill(0)  # clear screen

    # split into lines and display
    lines = text.splitlines()
    y = 0
    for line in lines:
        if y > HEIGHT - 8:
            break  # stop if screen full
        oled.text(line[:21], 0, y)  # each char ≈6px wide → fits ~21 chars
        y += 8

    oled.show()

def printMenu(menu, index):
    # Clamp the index inside valid range
    if index <= 0:
        index = 1
    if index >= len(menu) - 1:
        index = len(menu) - 2

    ln1 = menu[index - 1]
    ln2 = menu[index]
    ln3 = menu[index + 1]

    text = f"{ln1}\n>{ln2}\n{ln3}"
    oled_print(text, clear=True)

    return index

# initialize
currentMenu = mainMenu
currentOptionIndex = 1
driverSelection = None

printMenu(currentMenu, currentOptionIndex)

while True:

    if up_button.value() == 0:  # up
        time.sleep(0.2)  # Debounce delay
        if currentOptionIndex > 1:
            currentOptionIndex -= 1
        currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

    elif down_button.value() == 0:  # down
        time.sleep(0.2)  # Debounce delay
        if currentOptionIndex < len(currentMenu) - 2:
            currentOptionIndex += 1
        currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

    elif sel_button.value() == 0:  # select
        time.sleep(0.2)  # Debounce delay
        if currentMenu == mainMenu:
            if currentOptionIndex == 1:  # Mifare Classic
                currentMenu = mifareMenu
                currentOptionIndex = 2
            elif currentOptionIndex == 2:  # NTAG
                currentMenu = ntagMenu
                currentOptionIndex = 2
            elif currentOptionIndex == 3:  # Clear Saved
                clear_saved_list(savedUIDsMifare, MIFARE_FILE)
                clear_saved_list(savedUIDsNTAG, NTAG_FILE)
            currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

        elif currentMenu == mifareMenu:
            if currentOptionIndex == 1:  # go back
                currentMenu = mainMenu
                currentOptionIndex = 1
                driverSelection = None
            elif currentOptionIndex == 2:
                driverSelection = 0
            elif currentOptionIndex == 3:
                driverSelection = 1
            elif currentOptionIndex == 4:
                driverSelection = 2
            elif currentOptionIndex == 5:
                driverSelection = 3
            if driverSelection is not None:
                driver_select(driverSelection)
                driverSelection = None
            currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

        elif currentMenu == ntagMenu:
            if currentOptionIndex == 1: #go back
                currentMenu = mainMenu
                currentOptionIndex = 1
                driverSelection = None
            elif currentOptionIndex == 2:
                driverSelection = 4
            elif currentOptionIndex == 3:
                driverSelection = 5
            elif currentOptionIndex == 4:
                driverSelection = 6
            elif currentOptionIndex == 5:
                driverSelection = 7
            if driverSelection is not None:
                driver_select(driverSelection)
                driverSelection = None
            currentOptionIndex = printMenu(currentMenu, currentOptionIndex)

    else:
        # invalid key
        pass
