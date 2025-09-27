// ** REFER TO THE README AT https://github.com/megabyte512/RFID-Emulator FOR WIRING INSTRUCTIONS **

#include <MFRC522.h>
#include <SPI.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 RFID_lock(SS_PIN, RST_PIN);
int GREEN_LED_PIN = 2;
int RED_LED_PIN = 4;

void handleSerialCommands();
void addCardMode();
void removeCardMode();
void checkForCard();
void listAuthorizedCards();
void clearAllCards();
String getCardUID();
bool isCardAuthorized(String cardUID);
bool removeCard(String cardUID);

String authorizedCards[10];
int cardCount = 0;


void setup() {
  Serial.begin(9600);
  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV128); // Our specific clone fix :(
  RFID_lock.PCD_Init();
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);

  Serial.println("***RFID Access Control System***");
  Serial.println("- ADD: Add a new card");
  Serial.println("- LIST: Show all authorized cards");
  Serial.println("- CLEAR: Remove all cards");
  Serial.println("- REMOVE: Remove specific card");
  Serial.println();
}



void loop() {
  handleSerialCommands();
  checkForCard();
  delay(100);
}


void handleSerialCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toUpperCase();
    
    if (command == "ADD") {
      addCardMode();
    }
    else if (command == "LIST") {
      listAuthorizedCards();
    }
    else if (command == "CLEAR") {
      clearAllCards();
    }
    else if (command == "REMOVE") {
      removeCardMode();
    }
    else {
      Serial.println("Unknown command: " + command);
    }
  }
}


void addCardMode() {
  if (cardCount >= 10) {
    Serial.println("Maximum cards reached (10)");
    return;
  }
  
  Serial.println("Listening for card...");
  
  unsigned long timeout = millis() + 10000;  // 10 second timeout
  
  while (millis() < timeout) {
    // Check for card
    if (RFID_lock.PICC_IsNewCardPresent() && RFID_lock.PICC_ReadCardSerial()) {
      String newCardUID = getCardUID();
      
      // Check if card already exists
      if (isCardAuthorized(newCardUID)) {
        Serial.println("Card already in authorized list: " + newCardUID);
      } else {
        // Add new card
        authorizedCards[cardCount] = newCardUID;
        cardCount++;
        Serial.println("Card added successfully: " + newCardUID);
        Serial.println("Total authorized cards: " + String(cardCount));
      }
      return;
    }
  }
  
  Serial.println("Add timeout - no card presented");
}


void removeCardMode() {
  if (cardCount == 0) {
    Serial.println("No cards to remove");
    return;
  }
  
  Serial.println("Listening for card to remove...");
  
  unsigned long timeout = millis() + 10000;
    while (millis() < timeout) {
      if (RFID_lock.PICC_IsNewCardPresent() && RFID_lock.PICC_ReadCardSerial()) {
        String cardUID = getCardUID();
      
        if (removeCard(cardUID)) {
          Serial.println("Card removed: " + cardUID);
          Serial.println("Total authorized cards: " + String(cardCount));
        } else {
          Serial.println("Card not found in authorized list: " + cardUID);
        }
        return;
      }
    }
  Serial.println("Remove timeout - no card presented");
}


void checkForCard() {
  if (RFID_lock.PICC_IsNewCardPresent() && RFID_lock.PICC_ReadCardSerial()) {
    String cardUID = getCardUID();
    
    if (isCardAuthorized(cardUID)) {
      Serial.println("ACCESS GRANTED: " + cardUID);
      digitalWrite(GREEN_LED_PIN, 1);
      delay(1000);
      digitalWrite(GREEN_LED_PIN, 0);
    } else {
      Serial.println("ACCESS DENIED: " + cardUID);
      digitalWrite(RED_LED_PIN, 1);
      delay(1000);
      digitalWrite(RED_LED_PIN, 0);
    }
    return;
  }
}


String getCardUID() {
  String content = "";
  for (byte i = 0; i < RFID_lock.uid.size; i++) {
    content.concat(String(RFID_lock.uid.uidByte[i] < 16 ? "0" : ""));
    content.concat(String(RFID_lock.uid.uidByte[i], HEX));
  }
  content.toUpperCase();
  return content;
}


bool isCardAuthorized(String cardUID) {
  for (int i = 0; i < cardCount; i++) {
    if (authorizedCards[i] == cardUID) {
      return true;
    }
  }
  return false;
}


bool removeCard(String cardUID) {
  for (int i = 0; i < cardCount; i++) {
    if (authorizedCards[i] == cardUID) {
      // Shift remaining cards down
      for (int j = i; j < cardCount - 1; j++) {
        authorizedCards[j] = authorizedCards[j + 1];
      }
      cardCount--;
      return true;
    }
  }
  return false;
}


void listAuthorizedCards() {
  Serial.println("=== Authorized Cards ===");
  if (cardCount == 0) {
    Serial.println("No authorized cards");
  } else {
    for (int i = 0; i < cardCount; i++) {
      Serial.println(String(i + 1) + ". " + authorizedCards[i]);
    }
  }
  Serial.println("Total: " + String(cardCount) + "/10");
}


void clearAllCards() {
  cardCount = 0;
  Serial.println("All authorized cards removed");
}
