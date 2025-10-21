# Overview

(links to sections)

**Timeline**

- Test lock finished (9/26/25)
- Basic read functions implemented on PN532 (10/7/25)
- Emulating function implemented, it is discovered that an 0x08 is prepended to every emulation (10/16/25)

# Features


# Hardware Requirements

 - Raspberry Pi Pico 2 W
 - Adafruit PN532
 - USB to microUSB data cable
 - *Arduino UNO
 - *RFID-RC522 module

*Necessary for RFID test lock


# Software Requirements

 - micropython .UF2 for pi pico 2 W
 - mpremote (recommended)
 - pyserial (optional debugging)
 - NFC PN532 SPI library
 - *ArduinoIDE
 - *MFRC library
 - thonny
 - PN532 driver

*Necessary for RFID test lock

# Installation


## Wiring Diagram (if necessary for emulator)
Pico 2 W (GPIO)        ->   Adafruit PN532 breakout
-------------------------------------------------
3V3 (3.3V pin)         ->   VCC / 3.3V
GND                    ->   GND
GP18 (SPI0 SCK)        ->   SCK
GP19 (SPI0 MOSI)       ->   MOSI (SDA)
GP16 (SPI0 MISO)       ->   MISO (SSO / SO)
GP17 (CS / CHIP_SELECT)->   SS   (active low)
(optional) GP15        ->   IRQ
(optional) GP20        ->   RSTO / RST

# RFID Test Lock

## *Wiring*

*Diagram Here*

- SDA : D10
- SCK : D13
- MOSI : D11
- MISO : D12
- IRQ : n/a
- GND : GND
- RST: D9
- 3.3V : 3.3V
- **Two LEDs** : We used D2 and D4


# CAD Files

(link)

# Acknowledgements
