#include <Adafruit_NeoPixel.h>
#include <SoftwareSerial.h>
#include <LowPower.h>

// === CONFIGURATION ===
#define RELAY1_PIN 2
#define RELAY2_PIN 3
#define NEOPIXEL_PIN 11
#define ADDRESS_1 A6
#define ADDRESS_2 A7
#define SHUTDOWN_PIN 10  // Connected to Pi GPIO 5

const int ANALOG_PINS[] = {A0, A1, A2, A3};
const int DIGITAL_PINS[] = {6, 7, 8, 9};
bool digitalPinModes[4] = {true, true, true, true}; // true = INPUT, false = OUTPUT
bool digitalStates[4] = {false, false, false, false};

int analogValues[4];
int voltageMode = 0;
int rs485Address = 42;
int accessoryID = 0;

volatile bool shouldWake = false;

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

  pinMode(SHUTDOWN_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(SHUTDOWN_PIN), wakeISR, RISING);

  pixel.begin();
  pixel.setBrightness(1);
  applyVoltageMode(voltageMode);

  for (int i = 0; i < 4; i++) {
    pinMode(DIGITAL_PINS[i], INPUT);
  }
}

// === Main Loop ===
void loop() {
  if (digitalRead(SHUTDOWN_PIN) == LOW) {
    shouldWake = false;
    delay(50);

    if (digitalRead(SHUTDOWN_PIN) == LOW) {
      pixel.clear();
      pixel.show();
      LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
      delay(100);
      applyVoltageMode(voltageMode);
    }
  }

  handleSerial();
  readSensors();
  detectAccessoryID();
  streamSensorData();
}

// === Wake ISR ===
void wakeISR() {
  shouldWake = true;
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
      int firstColon = input.indexOf(':');
      int secondColon = input.indexOf(':', firstColon + 1);
      if (firstColon < 0 || secondColon < 0) return;

      int pinIndex = input.substring(firstColon + 1, secondColon).toInt();
      String mode = input.substring(secondColon + 1);

      if (pinIndex < 0 || pinIndex >= 4) return;

      mode.toLowerCase();

      if (mode == "in") {
        digitalPinModes[pinIndex] = true;
        pinMode(DIGITAL_PINS[pinIndex], INPUT);
      } else if (mode == "out") {
        digitalPinModes[pinIndex] = false;
        pinMode(DIGITAL_PINS[pinIndex], OUTPUT);
      } else if (mode == "pullup") {
        digitalPinModes[pinIndex] = true;
        pinMode(DIGITAL_PINS[pinIndex], INPUT_PULLUP);
      } else if (mode == "pulldown") {
        digitalPinModes[pinIndex] = true;
        pinMode(DIGITAL_PINS[pinIndex], INPUT);
        digitalWrite(DIGITAL_PINS[pinIndex], LOW); // emulate pulldown
      }

    } else if (input.startsWith("SET:")) {
      int firstColon = input.indexOf(':');
      int secondColon = input.indexOf(':', firstColon + 1);
      if (firstColon < 0 || secondColon < 0) return;

      int pinIndex = input.substring(firstColon + 1, secondColon).toInt();
      int value = input.substring(secondColon + 1).toInt();

      if (pinIndex >= 0 && pinIndex < 4 && !digitalPinModes[pinIndex]) {
        digitalWrite(DIGITAL_PINS[pinIndex], value ? HIGH : LOW);
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
      pixel.setPixelColor(0, 0, 0, 255); break;
    case 1:
      digitalWrite(RELAY1_PIN, HIGH);
      digitalWrite(RELAY2_PIN, LOW);
      pixel.setPixelColor(0, 255, 0, 0); break;
    case 2:
      digitalWrite(RELAY1_PIN, LOW);
      digitalWrite(RELAY2_PIN, HIGH);
      pixel.setPixelColor(0, 255, 255, 0); break;
    case 3:
      digitalWrite(RELAY1_PIN, HIGH);
      digitalWrite(RELAY2_PIN, HIGH);
      pixel.setPixelColor(0, 255, 255, 255); break;
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
    analogValues[i] = (int)(voltage * 100);
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

  if (!high1 && !high2) {
    accessoryID = 1;
  } else if (!high1 && high2) {
    accessoryID = 2;
  } else if (high1 && !high2) {
    accessoryID = 3;
  } else if (high1 && high2) {
    accessoryID = 4;
  } else {
    accessoryID = 0;
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
    Serial.println(accessoryID);
  }
}

