## Design Plan**
An RFID scanner works by emitting a radio frequency (RF) signal from a reader's antenna, which energizes an RFID tag's microchip and antenna. The powered-up tag then transmits 
its stored data, such as a unique identifier, back to the reader's antenna. The reader decodes this signal and sends the information to a connected system for processing

**Phase one: LED Lock on Arduino**
- Tap key on lock:
- Intepret data from decoder chip
- Check data against stored digital key
- Turn on LED to indicate system on / system off

**Phase two: Hacking chip with AdaFruit and Pi Pico**
- Tap key on Ada Fruit: Key returns signal
- Pico Stores signal
- Pico transmits equivalent signal based on data stolen

## Hardware Needed**
- Arduino for the lock
- Pi Pico for the unlocking system
- Ada Fruit PNC532 NFC/RFID controller breakoutboard
- RFID chips (correct key and incorrect key)
  

