# Project Dependencies

This document lists all required software packages and Python libraries for the SensorCluster project. It covers the Raspberry Pi backend (Python/Flask server), Arduino firmware, and system-level services.

---

## 🐍 Raspberry Pi (Python-side)

The backend server uses Flask, SocketIO, serial communication, GPIO control, OLED display rendering, file system monitoring, and optionally Tailscale for secure remote access.

---

### APT Packages

Install system-level dependencies:

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  git \
  inotify-tools \
  avrdude \
  libjpeg-dev \
  zlib1g-dev \
  libopenjp2-7 \
  build-essential \
  i2c-tools
```

---

### Python Libraries

Install required Python packages using the `--break-system-packages` flag:

```bash
pip3 install --break-system-packages \
  flask \
  flask-socketio \
  eventlet \
  pyserial \
  RPi.GPIO \
  luma.oled \
  pillow
```

---

### Tailscale VPN

Used for secure remote access and control of SensorCluster units from your iOS app or another device.

Install and activate:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

> After running `tailscale up`, follow the on-screen instructions to authorize the Pi with your Tailscale account.

---

## 🔌 Arduino (Firmware-side)

The Arduino Nano runs lightweight firmware for analog and digital IO, relay control, voltage selection, RS485, and NeoPixel output.

### Required Libraries

Install via Arduino Library Manager:

```cpp
#include <Adafruit_NeoPixel.h>
#include <SoftwareSerial.h>
```

| Library              | Purpose                                 |
|----------------------|------------------------------------------|
| `Adafruit NeoPixel`  | Voltage mode color ring indicator        |
| `SoftwareSerial`     | Enables RS485 over GPIO (D4/D5)          |

These libraries are compatible with Arduino Nano (ATmega328p @ 115200 baud).

---

## 🧩 Optional Tools

While not required for initial setup, these tools can improve reliability and automation:

| Tool            | Purpose                                 |
|------------------|------------------------------------------|
| `systemd`         | Run the backend server on boot          |
| `cron`            | Automate log rotation or scheduled reboots |
| `watchdog`        | Auto-reboot the Pi if the process fails |

---

## 🛡️ System Access Notes

Ensure the `pi` user is in the following groups for full GPIO, I2C, SPI, serial, and USB access:

```bash
sudo usermod -aG pi,adm,dialout,cdrom,sudo,audio,video,plugdev,games,users,input,render,netdev,lpadmin,gpio,i2c,spi pi
```

---

## 📝 Setup Automation

Use the provided `install.sh` script to install all dependencies, configure interfaces, clone the GitHub repository, copy required folders, and reboot automatically.

---
