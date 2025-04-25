#define FIRMWARE_VERSION "1.2.4"
#include <Adafruit_NeoPixel.h>
#include <SoftwareSerial.h>
#include <avr/sleep.h>
#include <avr/power.h>

// === CONFIGURATION ===
#define RELAY1_PIN 2
#define RELAY2_PIN 3
#define NEOPIXEL_PIN 11

const int ANALOG_PINS[] = {A0, A1, A2, A3};
const int DIGITAL_PINS[] = {6, 7, 8, 9};
bool digitalPinModes[4] = {true, true, true, true}; // true = INPUT, false = OUTPUT
bool digitalStates[4] = {false, false, false, false};

int analogValues[4];
int voltageMode = 0;
int rs485Address = 42;

// === RS485 Setup ===
#define RS485_RX 5
#define RS485_TX 4
SoftwareSerial rs485(RS485_RX, RS485_TX);

// === NeoPixel ===
Adafruit_NeoPixel pixel(1, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

// === Timing ===
unsigned long lastStream = 0;
const unsigned long streamInterval = 100;
unsigned long lastSerialActivity = 0;
const unsigned long serialTimeout = 2000; // 2 seconds before sleep

// === Sleep Mode ===
void goToSleep() {
  pixel.setPixelColor(0, pixel.Color(0, 0, 0)); // Turn off NeoPixel
  pixel.show();

  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_enable();
  noInterrupts();
  sleep_bod_disable();
  interrupts();
  sleep_cpu();
  sleep_disable();
}

// === Setup ===
void setup() {
  delay(1000);
  Serial.begin(115200);
  rs485.begin(9600);

  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);

  pixel.begin();
  pixel.setBrightness(64);
  pixel.setPixelColor(0, pixel.Color(0, 255, 0)); 
  pixel.show();

  for (int i = 0; i < 4; i++) {
    pinMode(DIGITAL_PINS[i], INPUT);
  }

  applyVoltageMode(voltageMode);

  lastSerialActivity = millis(); // initialize tracking
}

// === Main Loop ===
void loop() {
  handleSerial();
  readSensors();
  streamSensorData();

  // Check if Serial has been disconnected for too long
  if (!Serial) {
    delay(2000); // confirm it's not a momentary blip
    if (!Serial) {
      goToSleep();
    }
  }
}

// === Serial Command Parser ===
void handleSerial() {
  if (Serial && Serial.available()) {
    lastSerialActivity = millis(); // reset timeout

    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("mode:")) {
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
      rs485.println(msg);  // Send to RS485 device
    }
  }
}

// === Voltage Handling ===
void applyVoltageMode(int mode) {
  switch (mode) {
    case 0:
      digitalWrite(RELAY1_PIN, LOW);
      digitalWrite(RELAY2_PIN, LOW);
      pixel.setPixelColor(0, pixel.Color(128, 0, 128)); break;
    case 1:
      digitalWrite(RELAY1_PIN, HIGH);
      digitalWrite(RELAY2_PIN, LOW);
      pixel.setPixelColor(0, pixel.Color(255, 0, 0)); break;
    case 2:
      digitalWrite(RELAY1_PIN, LOW);
      digitalWrite(RELAY2_PIN, HIGH);
      pixel.setPixelColor(0, pixel.Color(255, 255, 0)); break;
    case 3:
      digitalWrite(RELAY1_PIN, HIGH);
      digitalWrite(RELAY2_PIN, HIGH);
      pixel.setPixelColor(0, pixel.Color(0, 255, 0)); break;
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
    analogValues[i] = (int)(voltage * 100);  // scale to 2 decimals
  }

  for (int i = 0; i < 4; i++) {
    if (digitalPinModes[i]) {
      digitalStates[i] = digitalRead(DIGITAL_PINS[i]);
    }
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

    Serial.print("|mode:");
    Serial.print(voltageMode);

    Serial.print("|ADDR:");
    Serial.println(rs485Address);
  }
}
