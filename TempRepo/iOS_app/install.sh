#!/bin/bash

echo "🔧 Starting SensorCluster installation..."

REPO_DIR="/home/pi/TempRepo/iOS_app"
TARGET_PI_DIR="/home/pi/Pi"
TARGET_ARDUINO_DIR="/home/pi/Arduino"
GIT_REPO_URL="https://github.com/pengels22/iOS_app.git"

# === Enable system interfaces ===
echo "🔌 Enabling SSH, I2C, and Serial..."
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 1

# === Install APT dependencies ===
echo "📦 Installing APT packages..."
sudo apt update
sudo apt install -y \
  python3-pip \
  git \
  inotify-tools \
  avrdude \
  libjpeg-dev \
  zlib1g-dev \
  libopenjp2-7 \
  i2c-tools \
  build-essential

# === Install Python libraries with pip ===
echo "🐍 Installing Python libraries..."
pip3 install --break-system-packages \
  flask \
  flask-socketio \
  eventlet \
  pyserial \
  RPi.GPIO \
  luma.oled \
  pillow

# === Add 'pi' user to required groups ===
echo "👤 Adding 'pi' to necessary groups..."
for group in pi adm dialout cdrom sudo audio video plugdev games users input render netdev lpadmin gpio i2c spi; do
  sudo usermod -aG $group pi
done

# === Clone GitHub repo ===
echo "🌐 Cloning GitHub repo..."
mkdir -p /home/pi/TempRepo
cd /home/pi/TempRepo
if [ ! -d "iOS_app" ]; then
  git clone "$GIT_REPO_URL"
else
  echo "ℹ️ Repo already cloned. Pulling latest changes..."
  cd iOS_app && git pull
fi

# === Copy project folders ===
echo "📁 Copying project folders..."
mkdir -p "$TARGET_PI_DIR"
mkdir -p "$TARGET_ARDUINO_DIR"

cp -r "$REPO_DIR/Pi/"* "$TARGET_PI_DIR/"
cp -r "$REPO_DIR/Arduino/"* "$TARGET_ARDUINO_DIR/"

# === Completion ===
echo "✅ SensorCluster installation complete!"
echo "🔄 Rebooting in 5 seconds..."
echo "Press CTRL+C to cancel"
sleep 5
sudo reboot

