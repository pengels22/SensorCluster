import RPi.GPIO as GPIO
import subprocess
import time
import sys
import os
import re
import serial
from pathlib import Path

# === CONFIGURATION ===
RESET_PIN = 23
POWER_PIN = 24
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = "115200"
MCU = "atmega328p"
PROGRAMMER = "arduino"

BASE_DIR = "/home/pi/Cluster"
SKETCH_DIR = os.path.join(BASE_DIR, "Arduino/Core_Backend")
FIRMWARE_DEST = os.path.join(BASE_DIR, "Firmware/firmware.hex")
HEX_BUILD_NAME = "Core_Backend.ino.hex"
INO_FILE = os.path.join(SKETCH_DIR, "Core_Backend.ino")
SERVICE_NAME = "sensorcluster"

# === FIRMWARE UTILS ===

def extract_version_from_ino():
    try:
        with open(INO_FILE, "r") as f:
            first_line = f.readline()
            match = re.search(r'"([\d.]+)"', first_line)
            if match:
                return match.group(1)
    except Exception as e:
        print("❌ Failed to extract version from .ino:", e)
    return None

def fetch_current_arduino_version(timeout=3):
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=timeout)
        ser.reset_input_buffer()
        print("🔎 Checking Arduino firmware version...")
        ser.write(b"GET_VERSION\n")
        time.sleep(1)
        lines = ser.readlines()
        for line in lines:
            if b"VERSION:" in line:
                return line.decode().strip().split(":")[1]
    except Exception as e:
        print("⚠️ Failed to read version from Arduino:", e)
    return None

def version_tuple(v):
    return tuple(map(int, v.strip().split(".")))

def should_update(new_ver, current_ver):
    try:
        return version_tuple(new_ver) > version_tuple(current_ver)
    except Exception:
        return True  # default to update if parsing fails

def compile_sketch():
    print("🛠️ Compiling Arduino sketch to fixed output folder...")
    output_dir = os.path.join(BASE_DIR, "Firmware")
    result = subprocess.run([
        "arduino-cli", "compile",
        "--fqbn", "arduino:avr:nano",
        "--output-dir", output_dir,
        "--clean",
        SKETCH_DIR
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Compilation failed:")
        print(result.stderr)
        sys.exit(1)

    expected_hex = Path(output_dir) / HEX_BUILD_NAME
    if not expected_hex.exists():
        print("❌ HEX file not found after compile.")
        sys.exit(1)

    final_path = Path(FIRMWARE_DEST)
    if final_path.exists():
        os.remove(final_path)

    os.rename(expected_hex, final_path)
    print(f"📁 HEX moved to: {final_path}")

def stop_server():
    print("🛑 Stopping Flask server...")
    subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME])
    time.sleep(1)

def start_server():
    print("⚡ Restarting Flask server...")
    subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME])
    time.sleep(1)
    result = subprocess.run(["systemctl", "is-active", SERVICE_NAME], capture_output=True, text=True)
    status = result.stdout.strip()
    if status == "active":
        print("✅ Flask server restarted successfully.")
    else:
        print("❌ Flask server failed to restart.")
        subprocess.run(["systemctl", "status", SERVICE_NAME])

def reset_arduino_and_flash():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RESET_PIN, GPIO.OUT)
    GPIO.setup(POWER_PIN, GPIO.OUT)
    GPIO.output(POWER_PIN, GPIO.HIGH)

    print("⚡ Resetting Arduino into bootloader...")
    GPIO.output(RESET_PIN, GPIO.LOW)
    time.sleep(1.2)
    GPIO.output(RESET_PIN, GPIO.HIGH)
    time.sleep(0.2)
    GPIO.cleanup()

    print("🚀 Flashing firmware with avrdude...")
    cmd = [
        "avrdude",
        "-v",
        "-V",
        f"-p{MCU}",
        f"-c{PROGRAMMER}",
        f"-P{SERIAL_PORT}",
        f"-b{BAUD_RATE}",
        "-D",
        f"-Uflash:w:{FIRMWARE_DEST}:i"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"🧙 avrdude output:\n{result.stdout}")
        if result.returncode == 0:
            print("✅ Firmware flashed successfully!")
        else:
            print("❌ Flashing failed:")
            print(result.stderr)
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print("⏳ Flashing timed out. Arduino may not be in bootloader.")
        sys.exit(1)

# === MAIN ===

if __name__ == "__main__":
    new_version = extract_version_from_ino()
    if not new_version:
        print("❌ Unable to determine new firmware version from .ino file")
        # sys.exit(1)

    print(f"🏁 New firmware version: {new_version}")

    current_version = None
    print("⚡ Resetting Arduino for version check...")
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RESET_PIN, GPIO.OUT)
        GPIO.output(RESET_PIN, GPIO.LOW)
        time.sleep(0.15)
        GPIO.output(RESET_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.cleanup()
        time.sleep(1)
        current_version = fetch_current_arduino_version()
    except:
        pass

    if current_version:
        print(f"📦 Current firmware version: {current_version}")
        if not should_update(new_version, current_version):
            print("⏭️ Firmware is up to date. Skipping flash.")
            sys.exit(0)
    else:
        print("⚠️ No version reported by Arduino. Proceeding with update.")

    compile_sketch()
    stop_server()
    reset_arduino_and_flash()
    start_server()
