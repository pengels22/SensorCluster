# SensorCluster

SensorCluster is a modular Raspberry Pi + Arduino-based system for real-time signal acquisition, voltage control, and remote monitoring — fully integrated with an iOS app frontend. Designed for expandability, ease of use, and OTA updates, SensorCluster is ready for both development and production deployments.

---

## 📁 Project Structure

```
SensorCluster/
├── .DS_Store
├── CHANGELOG.md
├── Cluster_Watchdog.sh
├── Install.sh
├── README.md
├── VERSION
├── git_auto_push.sh
├── git_watchdog.log
├── quick_start.md
├── Arduino/
│   ├── Core_Backend/
│   │   ├── Core_Backend.ino
│   │   └── ...
│   ├── Sensor_Module/
│   │   ├── Sensor_Module.ino
│   │   └── ...
│   └── ...
├── Firmware/
│   ├── Core_Backend.hex
│   ├── Sensor_Module.hex
│   └── ...
├── Pi/
│   ├── main.py
│   ├── server/
│   │   ├── app.py
│   │   ├── routes.py
│   │   └── ...
│   ├── oled/
│   │   ├── display.py
│   │   └── ...
│   ├── gpio/
│   │   ├── control.py
│   │   └── ...
│   └── ...
├── Web/
│   ├── index.html
│   ├── css/
│   │   ├── style.css
│   │   └── ...
│   ├── js/
│   │   ├── app.js
│   │   └── ...
│   └── ...
└── docs/
    ├── architecture.md
    ├── api_reference.md
    └── ...


---

## 🔧 Features

- 📡 Real-time sensor streaming to iOS app via Flask + Socket.IO
- ⚡ Voltage mode selection (3.3V / 5V / 12V / 24V) with relay switching
- 💡 NeoPixel status indicator
- 📷 OLED display with menu (SH1106, via GPIO buttons)
- 🔁 OTA firmware updates from Pi to Arduino over `/dev/serial0`
- 🔊 Auto snapshot and full session logging (to local or USB)
- 🌐 Optional VPN access via Tailscale
- 🔄 Auto Git push service with changelog + version tagging

---

## 🚀 Setup

### 1. Flash Raspberry Pi OS (Lite or Full)
Use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) and enable SSH, serial, and I2C during setup.

### 2. Run the Installer

Clone and run:

```bash
cd ~
git clone https://github.com/pengels22/SensorCluster.git
cd ~/Cluster
sudo bash install.sh
```

This will:
- Install all required APT and Python dependencies
- Add the `pi` user to all required system groups
- Clone/update the GitHub repo
- Copy contents to `/home/pi/Pi` and `/home/pi/Arduino`
- Reboot the Raspberry Pi

---

## 📦 Dependencies

- 🐍 Python: `flask`, `flask-socketio`, `eventlet`, `pyserial`, `RPi.GPIO`, `luma.oled`, `pillow`
- 📦 APT: `inotify-tools`, `avrdude`, `git`, `libjpeg-dev`, `zlib1g-dev`, `build-essential`, etc.
- 🔌 Arduino: `Adafruit_NeoPixel`, `SoftwareSerial`
- 🌐 VPN: [Tailscale](https://tailscale.com)

See [`docs/dependencies.md`](docs/dependencies.md) for the full list.

---

## 📌 Pin Mapping

All hardware pin assignments are documented in [`docs/pin_mapping.md`](docs/pin_mapping.md).

---

## 🧾 Deployment Variants

- 🇺🇸 U.S. Setup Notes: [`setup_us.md`](setup_us.md)
- 🇪🇺 EU Setup Notes: [`setup_eu.md`](setup_eu.md)

These documents cover power specs, regulatory safety, and cabling requirements for different regions.

---

## 🧠 Quick Start for Users

If you're not technical, read [`quick_start.md`](quick_start.md) for simple setup instructions.

---

## 🛠 Developer Notes

- Flask server is in `Pi/server.py`
- Arduino source lives in `Arduino/`
- Compiled firmware lives in `Firmware/`
- Git hooks or watchers may auto-push and tag changes

---

## 📄 License

This project is open-source under the MIT License. See the `LICENSE` file if included.

---

## 👨‍💻 Maintainer

**Patrick Engels**  
[github.com/pengels22](https://github.com/pengels22)

test
