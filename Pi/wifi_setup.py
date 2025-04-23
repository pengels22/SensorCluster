#!/usr/bin/env python3
import os
import subprocess
import time
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# HTML page template
HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Wi-Fi Setup</title>
  <style>
    body { font-family: sans-serif; text-align: center; padding-top: 50px; }
    input, select { padding: 10px; font-size: 1em; margin: 10px; }
    button { padding: 10px 20px; font-size: 1em; }
  </style>
</head>
<body>
  <h2>Configure Wi-Fi</h2>
  <form method="POST">
    <select name="ssid">
      {% for net in networks %}
      <option value="{{ net }}">{{ net }}</option>
      {% endfor %}
    </select><br>
    <input type="password" name="password" placeholder="Wi-Fi Password" required><br>
    <button type="submit">Connect</button>
  </form>
</body>
</html>
"""

def is_connected():
    try:
        result = subprocess.check_output("hostname -I", shell=True).decode().strip()
        return bool(result)
    except:
        return False

def start_hotspot():
    os.system("sudo systemctl stop NetworkManager.service || true")
    os.system("sudo systemctl stop wpa_supplicant.service || true")
    os.system("sudo ip link set wlan0 down")
    os.system("sudo ip addr flush dev wlan0")
    os.system("sudo ip link set wlan0 up")
    os.system("sudo create_ap --no-virt -n wlan0 SignalAnnalisys-Setup sig1234 &")

def stop_hotspot():
    os.system("sudo pkill create_ap")
    os.system("sudo systemctl start NetworkManager.service || true")
    os.system("sudo systemctl start wpa_supplicant.service || true")
    os.system("sudo dhclient wlan0")

def scan_networks():
    output = subprocess.check_output("sudo iwlist wlan0 scan | grep 'ESSID'", shell=True).decode()
    networks = [line.split(":")[1].strip().strip('"') for line in output.splitlines()]
    return sorted(set(networks))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ssid = request.form["ssid"]
        password = request.form["password"]

        conf = "\nnetwork={{\n    ssid=\"{}\"\n    psk=\"{}\"\n}}\n".format(ssid, password)

        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "a") as f:
            f.write(conf)

        stop_hotspot()
        time.sleep(2)
        os.system("sudo wpa_cli -i wlan0 reconfigure")
        time.sleep(10)

        if is_connected():
            return "<h2>✅ Connected! You can close this page.</h2>"
        else:
            return "<h2>❌ Connection failed. Try again.</h2>"

    nets = scan_networks()
    return render_template_string(HTML, networks=nets)

from datetime import datetime
import traceback

LOG_FILE = "/home/patrick/SignalAnnalisys/Pi/boot_log.txt"

def log_error(error_message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{{now}}] ERROR: {{error_message}}\n")
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=80)
    except Exception as e:
        log_error(traceback.format_exc())
    if not is_connected():
        print("No Wi-Fi connection. Starting hotspot...")
        start_hotspot()
        app.run(host="0.0.0.0", port=80)
    else:
        print("Already connected to Wi-Fi.")