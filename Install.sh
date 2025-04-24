#!/bin/bash

echo "? Starting SensorCluster installation..."

# === Configuration ===
REPO_NAME="iOS_app"
REPO_URL="https://github.com/pengels22/iOS_app.git"
TEMP_DIR="/home/pi/TempRepo"
REPO_DIR="$TEMP_DIR/$REPO_NAME"
CLUSTER_DIR="/home/pi/Cluster"
ARDUINO_DIR="$CLUSTER_DIR/Arduino"
PI_DIR="$CLUSTER_DIR/Pi"
FIRMWARE_DIR="$CLUSTER_DIR/Firmware"

# === Enable system interfaces ===
echo "? Enabling SSH, I2C, and Serial..."
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 1

# === Install APT dependencies ===
echo "? Installing APT packages..."
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

# === Install Python libraries ===
echo "? Installing Python libraries..."
pip3 install --break-system-packages \
  flask \
  flask-socketio \
  eventlet \
  pyserial \
  RPi.GPIO \
  luma.oled \
  pillow

# === Add 'pi' user to required groups ===
echo "? Adding 'pi' to necessary groups..."
for group in pi adm dialout cdrom sudo audio video plugdev games users input render netdev lpadmin gpio i2c spi; do
  sudo usermod -aG $group pi
done

# === Clone or Update Repo ===
echo "? Cloning or Updating GitHub repo..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"
if [ -d "$REPO_DIR/.git" ]; then
  echo "? Updating existing repo..."
  cd "$REPO_DIR" && git pull
else
  echo "? Cloning fresh repo..."
  git clone "$REPO_URL"
fi

# === Create Target Directory Structure ===
echo "? Creating folder structure under $CLUSTER_DIR"
mkdir -p "$ARDUINO_DIR"
mkdir -p "$PI_DIR/Icons"
mkdir -p "$FIRMWARE_DIR"

# === Copy Project Files ===
echo "? Copying files into place..."
cp -r "$REPO_DIR/Arduino/"* "$ARDUINO_DIR/"
cp -r "$REPO_DIR/Pi/"* "$PI_DIR/"
cp -r "$REPO_DIR/Pi/Icons/"* "$PI_DIR/Icons/" 2>/dev/null || echo "?? No Icons folder found."
cp -r "$REPO_DIR/Firmware/"* "$FIRMWARE_DIR/" 2>/dev/null || echo "?? No Firmware folder found."

# === Completion ===
echo "? SensorCluster installation complete!"
echo "? Rebooting in 5 seconds..."
echo "Press CTRL+C to cancel"
sleep 5
sudo reboot
