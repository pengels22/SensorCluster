# bluetooth_setup.py
from bluezero import peripheral
import subprocess
import socket
import time

class BLEWiFiPeripheral:
    def __init__(self):
        self.characteristic = peripheral.Characteristic(
            uuid='12345678-1234-5678-1234-56789abcdef0',
            value='',
            notifying=True,
            flags=['read', 'write', 'notify'],
            read_callback=self.read_callback,
            write_callback=self.write_callback
        )

        self.service = peripheral.Service(
            uuid='12345678-1234-5678-1234-56789abcdef1',
            primary=True
        )
        self.service.add_characteristic(self.characteristic)

        self.device = peripheral.Peripheral(adapter_addr='B8:27:EB:CF:BC:29',
                                            local_name='SignalCluster',
                                            services=[self.service])    

def read_callback(self):
        ip = self.get_ip()
        return ip.encode('utf-8') if ip else b''

    def write_callback(self, value):
        creds = value.decode('utf-8')
        ssid, password = creds.split(',')
        print(f"Received Wi-Fi creds: SSID={ssid}, PASS={password}")
        self.connect_to_wifi(ssid, password)
        time.sleep(5)
        ip = self.get_ip()
        if ip:
            self.characteristic.set_value(ip.encode('utf-8'))
            self.characteristic.notify()

    def get_ip(self):
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return None

    def connect_to_wifi(self, ssid, password):
        subprocess.run([
            "nmcli", "device", "wifi", "connect", ssid,
            "password", password
        ])

    def run(self):
        print("Starting BLE peripheral for Wi-Fi setup...")
        self.device.run()

from datetime import datetime
import traceback

LOG_FILE = "/home/patrick/SignalAnnalisys/Pi/boot_log.txt"

def log_error(error_message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{{now}}] ERROR: {{error_message}}\n")
if __name__ == "__main__":
    try:
        ble = BLEWiFiPeripheral()
        ble.run()
    except Exception as e:
        log_error(traceback.format_exc())
    ble = BLEWiFiPeripheral()
    ble.run()