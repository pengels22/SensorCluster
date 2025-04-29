#include <Adafruit_NeoPixel.h>
#include <SoftwareSerial.h>

// === CONFIGURATION ===
#define RELAY1_PIN 2
#define RELAY2_PIN 3
#define NEOPIXEL_PIN 11
#define ADDRESS_1 A6
#define ADDRESS_2 A7

const int ANALOG_PINS[] = {A0, A1, A2, A3};
const int DIGITAL_PINS[] = {6, 7, 8, 9};
bool digitalPinModes[4] = {true, true, true, true}; // true = INPUT, false = OUTPUT
bool digitalStates[4] = {false, false, false, false};

int analogValues[4];
int voltageMode = 0;
int rs485Address = 42;
int accessoryID = 0;

// === RS485 Setup ===
#define RS485_RX 5
#define RS485_TX 4
SoftwareSerial rs485(RS485_RX, RS485_TX);

// === NeoPixel ===
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// === Timing ===
unsigned long lastStream = 0;
const unsigned long streamInterval = 100;

// === Setup ===
void setup() {
  Serial.begin(115200);
  rs485.begin(9600);

  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);

  pixel.begin();
  pixel.setBrightness(20);
  pixel.setPixelColor(0, 255, 0); 
  pixel.show();

  for (int i = 0; i < 4; i++) {
    pinMode(DIGITAL_PINS[i], INPUT);
  }

  applyVoltageMode(voltageMode);
}

// === Main Loop ===
void loop() {
  handleSerial();
  readSensors();
  detectAccessoryID();
  streamSensorData();
}

// === Serial Command Parser ===
void handleSerial() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("MODE:")) {
      voltageMode = input.substring(5).toInt();
      applyVoltageMode(voltageMode);

    } else if (input.startsWith("DIO:")) {
      int pin = input.substring(4, 5).toInt();
      String dir = input.substring(6);
      if (pin >= 0 && pin < 4) {
        if (dir == "IN") {
          digitalPinModes[pin] = true;
          pinMode(DIGITAL_PINS[pin], INPUT);
        } else if (dir == "OUT") {
          digitalPinModes[pin] = false;
          pinMode(DIGITAL_PINS[pin], OUTPUT);
        }
      }

    } else if (input.startsWith("DWRITE:")) {
      int pin = input.substring(7, 8).toInt();
      int val = input.substring(9).toInt();
      if (pin >= 0 && pin < 4 && !digitalPinModes[pin]) {
        digitalWrite(DIGITAL_PINS[pin], val ? HIGH : LOW);
      }

    } else if (input.startsWith("RS485:")) {
      String msg = input.substring(6);
      rs485.println(msg);
    }
  }
}

// === Voltage Handling ===
void applyVoltageMode(int mode) {
  switch (mode) {
    case 0:
      digitalWrite(RELAY1_PIN, LOW);
      digitalWrite(RELAY2_PIN, LOW);
      pixel.setPixelColor(0, 0, 0, 255); break;  // Blue
    case 1:
      digitalWrite(RELAY1_PIN, HIGH);
      digitalWrite(RELAY2_PIN, LOW);
      pixel.setPixelColor(0, 255, 0, 0); break;  // Red
    case 2:
      digitalWrite(RELAY1_PIN, LOW);
      digitalWrite(RELAY2_PIN, HIGH);
      pixel.setPixelColor(0, 255, 255, 0); break;  // Yellow
    case 3:
      digitalWrite(RELAY1_PIN, HIGH);
      digitalWrite(RELAY2_PIN, HIGH);
      pixel.setPixelColor(0, 255, 255, 255); break;  // White
    default:
      return;
  }
  pixel.show();
}

// === IO Reading ===
void readSensors() {
  for (int i = 0; i < 4; i++) {
    int raw = analogRead(ANALOG_PINS[i]);
    float voltage = raw * (5.0 / 1023.0);
    analogValues[i] = (int)(voltage * 100);  // Scale to preserve 2 decimal places
  }

  for (int i = 0; i < 4; i++) {
    if (digitalPinModes[i]) {
      digitalStates[i] = digitalRead(DIGITAL_PINS[i]);
    }
  }
}

// === Accessory ID Detection ===
void detectAccessoryID() {
  float v1 = analogRead(ADDRESS_1) * (5.0 / 1023.0);
  float v2 = analogRead(ADDRESS_2) * (5.0 / 1023.0);

  bool high1 = (v1 > 2.5);
  bool high2 = (v2 > 2.5);

  if (high1 && !high2) {
    accessoryID = 1;
  } else if (!high1 && high2) {
    accessoryID = 2;
  } else if (!high1 && !high2) {
    accessoryID = 3;
  } else if (high1 && high2) {
    accessoryID = 4;
  } else {
    accessoryID = 0;  // Fallback if undefined
  }
}

// === Stream Data to Pi ===
void streamSensorData() {
  if (millis() - lastStream >= streamInterval) {
    lastStream = millis();

    Serial.print("A:");
    for (int i = 0; i < 4; i++) {
      Serial.print(analogValues[i] / 100.0, 2);
      if (i < 3) Serial.print(",");
    }

    Serial.print("|D:");
    for (int i = 0; i < 4; i++) {
      Serial.print(digitalStates[i]);
      if (i < 3) Serial.print(",");
    }

    Serial.print("|MODE:");
    Serial.print(voltageMode);

    Serial.print("|ADDR:");
    Serial.print(rs485Address);

    Serial.print("|ACC:");
    Serial.println(accessoryID);  // Now ends with Accessory ID
  }
}
