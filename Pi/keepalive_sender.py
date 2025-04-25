import serial
import time
import sys

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200
PING_INTERVAL = 1  # seconds

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("✅ Keepalive sender started.")
    except Exception as e:
        print(f"❌ Failed to open serial port {SERIAL_PORT}: {e}")
        sys.exit(1)

    while True:
        try:
            ser.write(b"PING\n")
            time.sleep(PING_INTERVAL)
        except Exception as e:
            print(f"❌ Serial write failed: {e}")
            break

if __name__ == "__main__":
    time.sleep(5)  # Small delay before starting
    main()
