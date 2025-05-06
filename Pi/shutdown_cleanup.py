#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import subprocess
import os

SHUTDOWN_GPIO = 5  # GPIO pin connected to Arduino D10

def stop_sensorcluster():
    try:
        subprocess.run(["systemctl", "stop", "sensorcluster.service"], check=True)
        print("[Systemd] sensorcluster.service stopped.")
    except subprocess.CalledProcessError as e:
        print(f"[Systemd] Failed to stop sensorcluster.service: {e}")

def blank_oled():
    try:
        # Send SSD1306/SH1106 display OFF command
        subprocess.run(["i2cset", "-y", "1", "0x3C", "0x00", "0xAE"], check=True)
        print("[OLED] Display off command sent.")
    except subprocess.CalledProcessError as e:
        print(f"[OLED] Failed to send OFF command: {e}")

def signal_arduino_sleep():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SHUTDOWN_GPIO, GPIO.OUT)
    GPIO.output(SHUTDOWN_GPIO, GPIO.LOW)
    print("[GPIO] Pin 5 pulled LOW to signal Arduino sleep.")
    time.sleep(1)
    

def main():
    print("[Shutdown] Starting cleanup routine...")
    stop_sensorcluster()
    signal_arduino_sleep()
    blank_oled()
    print("[Shutdown] Done.")

if __name__ == "__main__":
    main()
