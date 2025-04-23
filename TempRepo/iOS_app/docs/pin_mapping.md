# Pin Mapping

This document outlines the physical pin assignments used in the SensorCluster project for both the Arduino Nano and Raspberry Pi.

---

## 🔌 Arduino Nano

| Function               | Pin        | Notes                                         |
|------------------------|------------|-----------------------------------------------|
| NeoPixel Data          | D6         | Controls RGB ring for voltage status          |
| Voltage Relay 1        | D2         | Selects low-voltage (3.3V / 5V) path          |
| Voltage Relay 2        | D3         | Selects high-voltage (12V / 24V) path         |
| RS485 TX               | D5         | SoftwareSerial TX (to RS485 transceiver)      |
| RS485 RX               | D4         | SoftwareSerial RX (from RS485 transceiver)    |
| Analog Input 1         | A0         | Sensor 1 (voltage-divided)                    |
| Analog Input 2         | A1         | Sensor 2 (voltage-divided)                    |
| Analog Input 3         | A2         | Sensor 3 (voltage-divided)                    |
| Analog Input 4         | A3         | Sensor 4 (voltage-divided)                    |
| Battery Monitor 1      | A4         | Reads battery 1 voltage                       |
| Battery Monitor 2      | A5         | Reads battery 2 voltage                       |
| UART RX                | D0 (RX)    | Connected to Pi UART TX `/dev/serial0`       |
| UART TX                | D1 (TX)    | Connected to Pi UART RX `/dev/serial0`       |

---

## 🧠 Raspberry Pi GPIO

| Function               | GPIO       | Pin # | Notes                                      |
|------------------------|------------|-------|--------------------------------------------|
| Menu Button            | GPIO17     | 11    | Enters OLED menu or confirms selection     |
| Up Button              | GPIO27     | 13    | Moves up in OLED menu                      |
| Down Button            | GPIO22     | 15    | Moves down in OLED menu                    |
| I2C SDA (OLED)         | GPIO2      | 3     | SH1106 SDA line                            |
| I2C SCL (OLED)         | GPIO3      | 5     | SH1106 SCL line                            |
| UART TX                | GPIO14     | 8     | Pi TX → Arduino RX                         |
| UART RX                | GPIO15     | 10    | Pi RX ← Arduino TX                         |

---

## 🪛 Notes

- All analog inputs on the Arduino are read after a brief delay to allow voltage switching to stabilize.
- A NeoPixel on D6 displays the current voltage mode:
  - 🟣 3.3V
  - 🔴 5V
  - 🟡 12V
  - 🟢 24V
- Battery monitor pins A4 and A5 measure voltage via voltage dividers.

---

## 📡 Communication

- UART (`/dev/serial0`) is used for bidirectional Pi ↔ Arduino communication at 115200 baud.
- RS485 SoftwareSerial is reserved for future multi-device expansion.
