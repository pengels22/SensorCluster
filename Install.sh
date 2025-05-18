#!/bin/bash

echo "🔧 Starting SensorCluster installation..."

# === Configuration ===
REPO_NAME="SensorCluster"
REPO_URL="https://github.com/pengels22/SensorCluster.git"
TEMP_DIR="$HOME/TempRepo"
REPO_DIR="$TEMP_DIR/$REPO_NAME"
CLUSTER_DIR="$HOME/Cluster"
ARDUINO_DIR="$CLUSTER_DIR/Arduino"
PI_DIR="$CLUSTER_DIR/Pi"
ICONS_DIR="$PI_DIR/Icons"
FIRMWARE_DIR="$CLUSTER_DIR/Firmware"

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
  build-essential \
  tree

# === Install Python libraries ===
echo "🐍 Installing Python libraries..."
pip3 install --break-system-packages \
  flask \
  flask-socketio \
  eventlet \
  pyserial \
  RPi.GPIO \
  luma.oled \
  pillow

# === Add user to groups ===
echo "👤 Adding '$USER' to system groups..."
for group in pi adm dialout cdrom sudo audio video plugdev games users input render netdev lpadmin gpio i2c spi; do
  sudo usermod -aG $group $USER
done

# === Clone or update GitHub repo ===
echo "🌐 Cloning or updating GitHub repo..."
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"
if [ -d "$REPO_DIR/.git" ]; then
  echo "🔄 Repo already exists, pulling latest..."
  cd "$REPO_DIR" && git pull
else
  echo "📥 Cloning fresh repo..."
  git clone "$REPO_URL"
fi

# === Create and clean target folder structure ===
echo "📁 Creating and cleaning folders under $CLUSTER_DIR..."
mkdir -p "$ARDUINO_DIR" "$PI_DIR" "$ICONS_DIR" "$FIRMWARE_DIR"
rm -rf "$ARDUINO_DIR"/* "$PI_DIR"/* "$ICONS_DIR"/* "$FIRMWARE_DIR"/*

# === Copy files ===
echo "📂 Copying files into Cluster..."
cp -r "$REPO_DIR/Arduino/"* "$ARDUINO_DIR/"
cp -r "$REPO_DIR/Pi/"* "$PI_DIR/"
cp -r "$REPO_DIR/Pi/Icons/"* "$ICONS_DIR/" 2>/dev/null || echo "⚠️ No Icons folder found."
cp -r "$REPO_DIR/Firmware/"* "$FIRMWARE_DIR/" 2>/dev/null || echo "⚠️ No Firmware folder found."

# === Verify required files ===
echo "🔍 Verifying required files..."

required_files=(
  "$PI_DIR/Server-V3.py"
  "$PI_DIR/wifi_setup.py"
  "$PI_DIR/bluetooth_setup.py"
  "$PI_DIR/flash_arduino.py"
  "$ICONS_DIR/wifi.png"
  "$ICONS_DIR/bluetooth.png"
)

missing=false
for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing: $file"
    missing=true
  else
    echo "✅ Found: $file"
  fi
done

if [ "$missing" = true ]; then
  echo "🚫 One or more critical files are missing. Installation aborted."
  exit 1
fi

# === Setup systemd service for Server-V3.py ===
echo "🛠 Setting up systemd service for Server-V3.py..."

SERVICE_NAME="sensorcluster"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=SensorCluster Backend Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 $CLUSTER_DIR/Pi/Server-V3.py
WorkingDirectory=$CLUSTER_DIR/Pi
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reexec
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# === Optional Git Auto Push for Dev Server ===
if [ -f "$HOME/is_dev" ]; then
  echo "🟢 Detected dev environment — enabling git auto-push..."

  AUTOPUSH_SERVICE="/etc/systemd/system/git_auto_push.service"
  SCRIPT_PATH="$CLUSTER_DIR/git_auto_push.sh"

  sudo tee "$AUTOPUSH_SERVICE" > /dev/null <<EOF
[Unit]
Description=Git Auto Push Service for SensorCluster
After=network.target

[Service]
ExecStart=/bin/bash $SCRIPT_PATH
WorkingDirectory=$CLUSTER_DIR
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  sudo systemctl enable git_auto_push
  sudo systemctl start git_auto_push
else
  echo "🛑 Production environment — skipping git auto-push setup."
fi

# === Show final folder structure ===
echo "📂 Final folder structure:"
tree -L 2 "$CLUSTER_DIR" || ls -R "$CLUSTER_DIR"

# === Arduino CLI and Library Setup ===
echo "🧰 Setting up Arduino CLI and installing required libraries..."

CLI_VERSION="0.35.2"
CLI_BIN="$HOME/bin/arduino-cli"
INSTALL_DIR="$HOME/bin"

mkdir -p "$INSTALL_DIR"

if ! command -v arduino-cli &> /dev/null; then
  echo "🔧 arduino-cli not found. Installing..."

  ARCH=$(uname -m)
  OS=$(uname | tr '[:upper:]' '[:lower:]')

  case "$ARCH" in
    x86_64) PLATFORM="64bit" ;;
    aarch64 | armv7l) PLATFORM="arm64" ;;
    *) echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
  esac

  wget -q "https://downloads.arduino.cc/arduino-cli/arduino-cli_${CLI_VERSION}_${OS}_${PLATFORM}.tar.gz" -O /tmp/arduino-cli.tar.gz
  tar -xzf /tmp/arduino-cli.tar.gz -C "$INSTALL_DIR"
  chmod +x "$CLI_BIN"

  export PATH="$INSTALL_DIR:$PATH"

  if ! grep -q "$INSTALL_DIR" ~/.bashrc; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
    echo "📝 Added arduino-cli to ~/.bashrc"
  fi

  echo "✅ arduino-cli installed."
else
  echo "✅ arduino-cli already installed."
fi

arduino-cli config init > /dev/null 2>&1
arduino-cli core update-index
arduino-cli core install arduino:avr

LIBRARIES=(
  "Adafruit NeoPixel"
  "ArduinoBLE"
  "LowPower"
  "BLEPeripheral"
  "BLESerial"
)

for LIB in "${LIBRARIES[@]}"; do
  echo "📚 Installing Arduino library: $LIB"
  arduino-cli lib install "$LIB"
done

echo "✅ Arduino environment fully configured."

# === Completion ===
echo "✅ SensorCluster installation complete!"
echo "🔄 Rebooting in 5 seconds..."
echo "Press CTRL+C to cancel"
sleep 5
sudo reboot
