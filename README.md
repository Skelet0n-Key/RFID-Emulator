# Project Overview

**Introduction**

This project aims to solve a problem that we have: "I want to get through that door." This device is a lock-pick of sorts... but for 13.56MHz RFID locks. We move apartments a lot as college students and some apartments have better amenities than others. Why not enjoy them all?!

**Challenges and Solutions**

- We wanted a controlled environment to test our project's functionality and so that's what we did. We made an RFID lock with an arduino uno and MFRC-522 module ([code found here](RFID_lock/RFID_lock.ino)). The lock came with it's own problems. It took a while to find out what was going on, but we weren't getting any response from our MFRC-522 because it wasn't an official module. We needed to slow down communication to our module and connect it to 5V even though 3.3V was printed on the PCB. *Note: we labeled it 3.3V-3.3V in the wiring diagram*
- The original idea for this project was to have the PN532 emulate the copied UID itself. Unfortunately, due to security concerns (😒) the PN532 prepends a 0x08 byte when it sends its UID. So calling the command to send a specified UID like: 0x0000BEEF, would send: 0x080000BE. Luckily, you can just write a non-modified UID to a card. Weird, right? Almost too good to be true. So this is what we ended up pivoting to.

**Timeline**

- Test lock finished (9/26/25)
- Basic read functions implemented on PN532 (10/7/25)
- Emulating function implemented, it is discovered that an 0x08 is prepended to every emulation (10/16/25)
- Writing function finished (10/23/25)

**Testing and Results**

# Project Capabilities



# Hardware Components

 - Raspberry Pi Pico 2 W
 - Adafruit PN532
 - *Arduino UNO
 - *RFID-MFRC522 module

*Necessary for RFID test lock


# Software Dependencies

 - [micropython .UF2 for pi pico 2 W](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html)
 - [NFC PN532 SPI library](https://github.com/Carglglz/NFC_PN532_SPI?tab=readme-ov-file)
 - *[MFRC library](https://docs.arduino.cc/libraries/mfrc522)

*Necessary for RFID test lock

# Implementation


## Wiring Diagrams and Information

**Emulator**
*Diagram Here*

| RPI Pico 2 W | Adafruit PN532 Breakout |
|:------|:------|
| 3V3 (3.3V) | Vcc / 3.3V |
| GND | GND |
| GP16 (SPI0 MISO) | MISO (SSO / SO) |
| GP17 (CS / CHIP_SELECT | SS   (active low) |
| GP18 (SPI0 SCK) | SCK |
| GP19 (SPI0 MOSI) | MOSI (SDA) |
| (optional) GP15 | IRQ |
| (optional) GP20 | RSTO / RST |


**RFID Lock**
*Diagram Here*

| Arduino Uno | MFRC-522 |
|:----|:----|
| 3.3V | 3.3V |
| GND | GND |
| D9 | RST |
| D10 | SDA |
| D11 | MOSI |
| D12 | MISO |
| D13 | SCK |
| N/A | IRQ |

We also used two indicator LEDs on D2 and D4 so we didn't have to look at the terminal everytime to see if access was granted / denied. 

## CAD Files

We used a few prints to bring this project together and give it a more prolished look. You can find them [here]()
(link)

# Acknowledgements
We used Carglglz's [driver](https://github.com/Carglglz/NFC_PN532_SPI) to control the basic functions of the PN532, such as initialization and reading mifare classics

We added functionality to that driver using the principles from the [Adafruit PN532 driver](https://github.com/adafruit/Adafruit-PN532/blob/master/Adafruit_PN532.cpp) to write data to a programmable card, following mifare classic protocol. 
