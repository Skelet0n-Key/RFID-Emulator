from machine import Pin, SPI
import NFC_PN532 as nfc
import time

# Initialize SPI0 using your wiring
spi = SPI(0,
          baudrate=1152000,
          polarity=0,
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(18),
          mosi=Pin(19),
          miso=Pin(16))

# Chip select (active low)
cs = Pin(17, Pin.OUT)
cs.value(1)  # Deselect initially

# Optional reset and IRQ pins
irq = Pin(15, Pin.IN)
rst = Pin(20, Pin.OUT)
rst.value(1)

# Initialize PN532 driver
pn532 = nfc.PN532(spi, cs, rst, irq)

# Get firmware version
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {}.{}'.format(ver, rev))

# Configure for MiFare cards
pn532.SAM_configuration()


# Read function
def read_nfc(dev, timeout_ms=500):
    print('Waiting for a card...')
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
        uid = dev.read_passive_target(timeout=50)
        if uid:
            numbers = [i for i in uid]
            string_ID = '{}-{}-{}-{}'.format(*numbers)
            print('Found card with UID:', [hex(i) for i in uid])
            print('Number_id:', string_ID)
            return uid
        time.sleep(0.05)
    print('CARD NOT FOUND')
    return None


time.sleep(2)

# Run test
while (True):
    time.sleep(0.5)
    read_nfc(pn532, 115200)
