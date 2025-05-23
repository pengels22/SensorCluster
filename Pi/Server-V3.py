# === Direct Imports ===
import eventlet
eventlet.monkey_patch()
import csv
import datetime
import io
import json
import logging
import os
import pty
import queue
import re
import RPi.GPIO as GPIO
import serial
import socket
import subprocess
import sys
import threading
import time
import busio
import board

# === From Imports (Alphabetized with Submodules Sorted) ===
from collections import deque
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request, send_from_directory
from flask_socketio import SocketIO, emit
from io import StringIO
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from PIL import Image, ImageDraw, ImageFont, ImageOps
from adafruit_ina219 import INA219
i2c_bus = busio.I2C(board.SCL, board.SDA)
ina219 = INA219(i2c_bus, addr=0x45)  # Try 0x45 if needed
font = ImageFont.load_default()
debugg = False
debug_sid = None

# Create pseudo-terminal
master_fd, slave_fd = pty.openpty()
shell = subprocess.Popen(
    ["/bin/bash"],
    stdin=slave_fd,
    stdout=slave_fd,
    stderr=slave_fd,
    universal_newlines=True,
    bufsize=0,
)
GPIO.setwarnings(False)
SESSION_LOG = {}
SESSION_LOG_PATH = ""
SESSION_LOG_DIR = os.path.expanduser("~/Desktop/Logs")
suppress_menu_draw = False
GPIO.setmode(GPIO.BCM)
SHUTDOWN_GPIO = 5
GPIO.setup(SHUTDOWN_GPIO, GPIO.OUT)
GPIO.output(SHUTDOWN_GPIO, GPIO.HIGH)
def append_session_log(message, level="INFO"):
    global SESSION_LOG, SESSION_LOG_PATH

    if not SESSION_LOG_PATH:
        return

    log_line = f"[{level.upper()}] {message}"
    SESSION_LOG["system_logs"].append(log_line)
    print(log_line)

    try:
        with open(SESSION_LOG_PATH, "w") as f:
            json.dump(SESSION_LOG, f, indent=2)
    except Exception as e:
        print("? Failed to write session log:", e)


#wifi and bluetooth icon
WIFI_ICON = None
BLUETOOTH_ICON = None

try:
    # Load and process Wi-Fi icon
    wifi_path = os.path.expanduser("~/Cluster/Pi/icons/wifi.png")
    if os.path.exists(wifi_path):
        WIFI_ICON = Image.open(wifi_path).convert("1").resize((12, 12), Image.LANCZOS)
    else:
        print(f"?? Wi-Fi icon not found at {wifi_path}")

    # Load and process Bluetooth icon
    bt_path = os.path.expanduser("~/Cluster/Pi/icons/bluetooth.png")
    if os.path.exists(bt_path):
        BLUETOOTH_ICON = Image.open(bt_path).convert("1").resize((16, 16), Image.LANCZOS)
    else:
        print(f"?? Bluetooth icon not found at {bt_path}")

except Exception as e:
    print("? Icon load failed:", e)
# === CONFIGURATION ===
SERIAL_PORT = '/dev/ttyS0'
BAUD_RATE = 115200
LOCAL_LOG_DIR = '~/Desktop/sensor_logs'
sensor_log_filename = None

dio_config = {
    "digital": ["In", "In", "In", "In"]
}



def get_battery_status():
    try:
        voltage = ina219.bus_voltage
        # Map voltage range to percent (3.2V?4.2V)
        percent = min(100, max(0, int((voltage - 3.2) / (4.2 - 3.2) * 100)))
        return voltage, percent
    except Exception as e:
        print(f"[INA219] Battery read error: {e}")
        return None, 0

def find_usb_drive():
    global ACTIVE_LOG_DIR
    media_dir = '/media/'
    usb_base_dir = None

    if os.path.exists(media_dir):
        for user_dir in os.listdir(media_dir):
            user_path = os.path.join(media_dir, user_dir)
            if os.path.isdir(user_path):
                for mount in os.listdir(user_path):
                    potential_path = os.path.join(user_path, mount)
                    log_path = os.path.join(potential_path, 'sensor_logs')
                    try:
                        os.makedirs(log_path, exist_ok=True)
                        usb_base_dir = log_path
                        
                        return usb_base_dir
                    except Exception as e:
                        return None

def usb_monitor():
    global ACTIVE_LOG_DIR, log_active

    while True:
        new_usb = find_usb_drive()
        if new_usb and ACTIVE_LOG_DIR != new_usb:
            append_session_log(f"? USB inserted ? switching log path to: {new_usb}")
            ACTIVE_LOG_DIR = new_usb
            show_temp_message("USB Detected")
            socketio.emit("usb_event", {
                "status": "inserted",
                "path": ACTIVE_LOG_DIR
            })

        elif not new_usb and "media" in ACTIVE_LOG_DIR:
            append_session_log("? USB removed ? reverting to local log path")
            ACTIVE_LOG_DIR = LOCAL_LOG_DIR
            show_temp_message("USB Removed")
            socketio.emit("usb_event", {
                "status": "removed"
            })

            if log_active:
                append_session_log("? Logging stopped due to USB removal")
                log_active = False
                socketio.emit("logging_stopped", {"reason": "usb_removed"})

        time.sleep(5)


USB_DIR = find_usb_drive()
ACTIVE_LOG_DIR = USB_DIR if USB_DIR else LOCAL_LOG_DIR
BUTTON_MENU_PIN = 22
BUTTON_UP_PIN = 17
BUTTON_DOWN_PIN = 27

VOLTAGE_MODES = ["3.3V", "5V", "12V", "24V"]
current_voltage_index = 0
server_pin = [1, 2, 3, 4]  # Default 1234
entered_pin = []
connected = False

# === OLED DISPLAY ===
oled_available = True
try:
    i2c_interface = i2c(port=1, address=0x3C)
    oled = sh1106(i2c_interface)
    WIDTH, HEIGHT = oled.width, oled.height
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
except Exception as e:
    oled_available = False
    append_session_log(f"?? OLED setup failed: {e}")
# === STATE ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_MENU_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
data_log = deque()
log_lock = threading.Lock()
latest_data = {}

# === LOGGING CONFIGURATION ===
log_active = False
log_end_time = None
log_format = ""
log_io_filter = {"analog": True, "digital": True, "rs485": True}
log_save_to = "local"

menu_items = ["PIN Setup", "Voltage Select", "Battery Voltage", "Power Controls"]
menu_index = 0
menu_active = False
menu_last_activity = time.time()
MENU_TIMEOUT = 30
pin_entry_digit = 0
pin_editing = False
scroll_offsets = {
    "ip": 20,
    "ts": 20
}
scroll_speed = 2
scroll_reset_padding = 20
power_submenu_index = 0  # 0 = Shutdown, 1 = Reboot
confirming_power_action = False
confirmation_selection = 1  # 0 = Yes, 1 = No
oled_available = True
menu_editing = False


def set_voltage_mode(index):
    global current_voltage_index
    current_voltage_index = index % len(VOLTAGE_MODES)
    ser.write(f"MODE:{current_voltage_index}\n".encode())
    append_session_log(f"Sent to Arduino: MODE:{current_voltage_index}")


def is_wifi_connected():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        return ip != "127.0.0.1"
    except:
        return False

def is_bluetooth_active():
    result = subprocess.getoutput("hciconfig")
    return "UP RUNNING" in result

# === DRAW ICONS ===
def draw_battery(draw, x, y, voltage):
    try:
        percent = min(100, max(0, int((voltage - 3.2) / (4.2 - 3.2) * 100)))
        draw.rectangle((x, y, x + 20, y + 10), outline="white", fill="black")
        fill_width = int(18 * percent / 100)
        draw.rectangle((x + 1, y + 1, x + 1 + fill_width, y + 9), fill="white")
    except Exception as e:
        print(f"Error drawing battery: {e}")

def draw_wifi(draw, image, x, y):
    if WIFI_ICON:
        image.paste(WIFI_ICON, (x, y))

def draw_bluetooth(draw, image, x, y):
    if BLUETOOTH_ICON:
        image.paste(BLUETOOTH_ICON, (x, y))



# === IP ADDRESS ===
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

# === LOGGING HANDLER ===
def handle_logging(entry):
    global log_end_time, log_format, log_io_filter, log_save_to, log_active
    global sensor_log_filename
    if not log_active:
        append_session_log()
        return
    if not ACTIVE_LOG_DIR:
        return
    if not sensor_log_filename:
        return
    
    if datetime.now() >= log_end_time:
        log_active = False
        socketio.emit("logging_stopped", {"reason": "duration_expired"})
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if not sensor_log_filename:
        append_session_log("?? No sensor_log_filename set. Skipping log write.")
        return

    path = os.path.join(ACTIVE_LOG_DIR, sensor_log_filename)

    if log_format == "json":
        payload = {"timestamp": timestamp}
        if log_io_filter.get("analog"): payload["analog"] = entry.get("analog")
        if log_io_filter.get("digital"): payload["digital"] = entry.get("digital")
        if log_io_filter.get("rs485"): payload["rs485_address"] = entry.get("rs485_address")
        text = json.dumps(payload) + "\n"
    elif log_format == "csv":
        row = [timestamp]
        if log_io_filter.get("analog"): row += entry.get("analog", [])
        if log_io_filter.get("digital"): row += entry.get("digital", [])
        if log_io_filter.get("rs485"): row.append(entry.get("rs485_address"))
        text = ",".join(map(str, row)) + "\n"
    else:
        return

    with open(path, "a") as f:
        f.write(text)


# === SERIAL READER ===
def serial_reader():
    global latest_data, log_active
    global debugg
    while True:
        try:
            line = ser.readline().decode().strip()
            if debugg:
                print("RAW LINE:", line)
                

            if line:
                parts = line.split("|")
                result = {}
                for part in parts:
                    if part.startswith("A:"):
                        result["analog"] = [float(x) for x in part[2:].split(",")]
                    elif part.startswith("D:"):
                        result["digital"] = [int(x) for x in part[2:].split(",")]
                    elif part.startswith("MODE:"):
                        result["voltage_mode"] = int(part[5:])
                    elif part.startswith("ADDR:"):
                        result["rs485_address"] = int(part[5:])
                    elif part.startswith("BAT1:"):
                        result["battery1"] = float(part[5:])
                    elif part.startswith("BAT2:"):
                        result["battery2"] = float(part[5:])

                if result:
                    latest_data = result
                    
                    socketio.emit("sensor_update", result)
                    if log_active:
                        handle_logging(result)
        except Exception as e:
            append_session_log(f"Serial read error: {e}")

# === SOCKET HANDLERS ===
@socketio.on("set_voltage")
def handle_set_voltage(index):
    global current_voltage_index
    current_voltage_index = index  # ? This was missing

    cmd = f"MODE:{current_voltage_index}\n"
    append_session_log(f"?? set_voltage received: {index}")
    if ser:
        ser.write(cmd.encode())
        append_session_log(f"?? Sent to Arduino: {cmd.strip()}")

    draw_menu()  # Update OLED display with new voltage

def get_current_digital_modes():
    return dio_config["digital"]

@socketio.on('connect')
def on_connect():
    append_session_log("? Client connected")
    print("? Client connected")
    
@socketio.on("set_dio_mode")
def handle_dio_mode(data):
    pin = data.get("pin")
    mode = data.get("mode")

    if pin is not None and mode in ["In", "Out", "Pullup", "Pulldown"]:
        ser.write(f"DIO:{pin}:{mode}\n".encode())
        if pin < 4:  # Only track digital IO (D0?D3)
            dio_config["digital"][pin] = mode


@socketio.on("set_digital_output")
def handle_set_digital_output(data):
    try:
        pin = int(data.get("pin"))
        state = data.get("state")

        if state not in [True, False]:
            print(f"[WARN] Invalid output state: {state}")
            return

        value = 1 if state else 0
        send_serial_command(f"SET:{pin}:{value}")
        append_session_log(f"DIO pin {pin} toggled {state_str}", level="INFO")
    except Exception as e:
        print(f"[ERROR] set_digital_output failed: {e}")

@socketio.on("send_rs485")
def handle_send_rs485(data):
    message = data.get("message")
    if message:
        ser.write(f"RS485:{message}\n".encode())

@socketio.on("get_latest")
def handle_get_latest():
    emit("sensor_update", latest_data)
    latest_data["log_path"] = ACTIVE_LOG_DIR

@socketio.on("start_logging")
def handle_start_logging(config):
    global log_active, log_end_time, log_format, log_io_filter, log_save_to, sensor_log_filename

    duration = config.get("duration", 5)
    log_format = config.get("format", "json")
    append_session_log(log_format)
    log_io_filter = config.get("filters", {"analog": True, "digital": True, "rs485": True})
    log_save_to = config.get("save_to", "local")
    log_end_time = datetime.now() + timedelta(minutes=duration)
    log_active = True

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sensor_log_filename = f"SensorLog_{timestamp}.{log_format}"

    append_session_log("? Received start_logging:", config)
    append_session_log("? Logging started. Session file:", sensor_log_filename)



# === ROUTES ===

    
@app.route("/tailscale-ip")
def tailscale_ip_route():
    return jsonify({"tailscale_ip": get_tailscale_ip()})


def get_tailscale_ip():
    try:
        result = subprocess.check_output(
            "ip -4 addr show tailscale0 | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'",
            shell=True,
            text=True
        ).strip()
        return result
    except:
        return "Tailscale IP not found"

@app.route('/auth', methods=['POST'])
def authenticate():
    data = request.get_json()
    if not data or 'pin' not in data:
        return jsonify({"error": "Missing PIN"}), 400
    if data['pin'] == ''.join(str(d) for d in server_pin):
        # Determine connection type
        client_ip = request.remote_addr
        connection_type = "tailscale" if client_ip.startswith("100.") else "local"
        voltage_mode = VOLTAGE_MODES[current_voltage_index]

        digital_modes = get_current_digital_modes()
        

        start_session_log(connection_type, voltage_mode, digital_modes)
        append_session_log("✅ Authenticated", "INFO")

        return jsonify({"message": "Authenticated"})
    else:
        return jsonify({"error": "Invalid PIN"}), 401
    
web_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Web'))

# Load index.html
with open(os.path.join(web_folder, 'index.html'), 'r') as f:
    dashboard_html = f.read()

@app.route('/dashboard')
def dashboard():
    return send_from_directory(web_folder, "index.html")

# Load debug.html
with open(os.path.join(web_folder, 'debug.html'), 'r') as f:
    debug_html = f.read()

@app.route('/debug')
def debug():
    return send_from_directory(web_folder, "debug.html")
@socketio.on('set_debug')
def handle_set_debug(state):
    global debugg
    debugg = bool(state)
    msg = "? Debug mode enabled.\n" if debugg else "? Debug mode disabled.\n"
    socketio.emit("shell_output", msg)

@socketio.on('ios_log_batch')
def handle_ios_log_batch(data):
    lines = data.get('lines', [])
    for line in lines:
        socketio.emit('ios_log', {'line': line})
@socketio.on('send_command')
def handle_command(command):
    try:
        os.write(master_fd, (command + "\n").encode())
    except Exception as e:
        socketio.emit('command_response', f"?? Error sending command: {e}\n")


@app.route('/latest-log')
def latest_log():
    if not debugg:
        return "Unauthorized", 403
    log_dir = os.path.expanduser("~/Desktop/Logs")
    json_files = sorted(glob.glob(os.path.join(log_dir, "*.json")), key=os.path.getmtime, reverse=True)
    if not json_files:
        return "No logs found", 404
    return send_file(json_files[0], mimetype='application/json')

@socketio.on('debug_pin')
def handle_debug_pin(pin):
    global debugg, debug_sid

    actual = ''.join(str(d) for d in server_pin)
    submitted = str(pin).strip()

    if submitted == actual:
        debugg = True
        debug_sid = request.sid  # Store who accessed debug mode

        # Log debug access
        connection_type = "socket"
        voltage_mode = VOLTAGE_MODES[current_voltage_index]
        digital_modes = get_current_digital_modes()
        start_session_log(connection_type, voltage_mode, digital_modes)
        append_session_log("? Debug Access Granted", "INFO")

        emit('pin_result', {'success': True})
    else:
        emit('pin_result', {'success': False})

@socketio.on('index_pin')
def handle_index_pin(pin):
    global server_pin
    actual = ''.join(str(d) for d in server_pin)  # The same logic used for menu-auth PIN
    if str(pin).strip() == actual:
        emit('pin_result', {'success': True})
    else:
        emit('pin_result', {'success': False})


@socketio.on('disconnect')
def handle_disconnect(sid):
    global debugg, debug_sid
    if request.sid == debug_sid:
        debugg = False
        append_session_log("? Debug session ended", "INFO")

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def read_shell_output():
    buffer = ""
    while True:
        try:
            
            output = os.read(master_fd, 1024).decode(errors='ignore')
            cleaned = ansi_escape.sub('', output)
            
            buffer += output

            # Echo to both windows
            socketio.emit('command_response', cleaned)

            # Optional: also extract specific server-side messages to show in shell_output
            if "debugging" in output or "Client connected" in output:
                socketio.emit('shell_output', output)

        except Exception as e:
            print("Shell read error:", e)
            break

socketio.start_background_task(read_shell_output)




def redirect_stdout_and_stderr(socketio):
    logger = SocketIOLogger(socketio)
    sys.stdout = logger
    sys.stderr = logger


class SocketIOLogger(io.TextIOBase):
    def __init__(self, socketio_instance, channel='shell_output'):
        super().__init__()
        self.socketio = socketio_instance
        self.channel = channel

    def write(self, message):
        if message.strip():
            self.socketio.start_background_task(self.socketio.emit, self.channel, message)

    def flush(self):
        pass  # Not needed for real-time emit

def redirect_stdout_and_stderr(socketio_instance):
    sys.stdout = SocketIOLogger(socketio_instance)
    sys.stderr = SocketIOLogger(socketio_instance)


def draw_scrolling_text(draw, y, label, scroll_key, text, font, max_width):
    global scroll_offsets, image

    LINE_HEIGHT = 14  # Should match draw_menu

    label_padding = 4
    label_width = int(draw.textlength(label, font=font))
    text_start_x = label_width + label_padding

    draw.text((0, y), label, font=font, fill=255)

    text_width = int(draw.textlength(text, font=font))

    if text_width <= max_width:
        draw.text((text_start_x, y), text, font=font, fill=255)
        scroll_offsets[scroll_key] = 0
    else:
        scroll_offsets[scroll_key] += scroll_speed
        if scroll_offsets[scroll_key] > text_width + scroll_reset_padding:
            scroll_offsets[scroll_key] = 0

        temp_img = Image.new("1", (text_width, LINE_HEIGHT))  # Only 1 line tall now
        temp_draw = ImageDraw.Draw(temp_img)
        temp_draw.text((0, 0), text, font=font, fill=255)

        crop_x = int(scroll_offsets[scroll_key])
        cropped = temp_img.crop((crop_x, 0, crop_x + max_width, LINE_HEIGHT))

        image.paste(cropped, (text_start_x, y))

def draw_menu():
    global scroll_offsets, image, oled_available

    # === Layout constants ===
    LINE_HEIGHT = 14  # adjust to 16 if your font is tall or needs more space
    Y_STATUS = 0
    Y_TITLE = LINE_HEIGHT * 1
    Y_LINE_1 = LINE_HEIGHT * 2
    Y_LINE_2 = LINE_HEIGHT * 3
    Y_LINE_3 = LINE_HEIGHT * 4
    WIDTH = 128
    HEIGHT = 64

    ip = get_ip()
    ts_ip = get_tailscale_ip()
    pin_display = ''.join(str(d) for d in server_pin)

    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, HEIGHT), outline=0, fill=0)

    # === Top Status Bar ===
    voltage_avg = ina219.bus_voltage


    draw_battery(draw, 0, Y_STATUS, voltage_avg)
    x_wifi = 30
    x_bt = 45
    x_countdown = 62  # space between BT icon and voltage label

    if is_wifi_connected():
        draw_wifi(draw, image, x_wifi, Y_STATUS)
    if is_bluetooth_active():
        draw_bluetooth(draw, image, x_bt, Y_STATUS)

# === Show countdown if logging ===
    if log_active and log_end_time:
        remaining = int((log_end_time - datetime.now()).total_seconds())
        minutes = remaining // 60
        seconds = remaining % 60
        countdown_text = f"{minutes:01}:{seconds:02}"
        draw.text((x_countdown, Y_STATUS), countdown_text, font=font, fill=255)

# === Voltage Mode
    label = VOLTAGE_MODES[current_voltage_index]
    label_width = draw.textlength(label, font=font)
    draw.text((WIDTH - label_width - 2, Y_STATUS), label, font=font, fill=255)


        # === Main Area ===
    if not menu_active:
        draw_scrolling_text(draw, Y_TITLE, " IP:", "ip", ip, font, WIDTH - 35)
        draw.text((0, Y_LINE_1), f" PN: {pin_display}", font=font, fill=255)
        draw_scrolling_text(draw, Y_LINE_2, " TS:", "ts", ts_ip, font, WIDTH - 35)

    else:
        item = menu_items[menu_index]
        draw.text((0, Y_TITLE), f"> {item}", font=font, fill=255)

        if item == "PIN Setup":
            pin_str = ""
            for i in range(4):
                if pin_editing and i == pin_entry_digit:
                    pin_str += f"[{entered_pin[i]}]" if i < len(entered_pin) else "[_]"
                else:
                    pin_str += str(server_pin[i]) + " "
            draw.text((0, Y_LINE_1), f"PIN: {pin_str.strip()}", font=font, fill=255)

        elif item == "Voltage Select":
            preview_label = VOLTAGE_MODES[voltage_preview_index]
            draw.text((0, Y_LINE_1), f"Select: {preview_label}", font=font, fill=255)

        elif item == "Battery Voltage" and latest_data:
            b1 = latest_data.get("battery1", 0)
            
            draw.text((0, Y_LINE_1), f"BAT1: {b1:.2f}V", font=font, fill=255)
            

        elif item == "Power Controls":
            if confirming_power_action:
                draw.text((0, Y_LINE_1), "Are you sure?", font=font, fill=255)
                yes = "[Yes]" if confirmation_selection == 0 else " Yes "
                no = "[No]" if confirmation_selection == 1 else " No "
                draw.text((0, Y_LINE_2), f"{yes}   {no}", font=font, fill=255)
            else:
                shutdown = "> Shutdown" if power_submenu_index == 0 else "  Shutdown"
                reboot = "> Reboot" if power_submenu_index == 1 else "  Reboot"
                draw.text((0, Y_LINE_1), shutdown, font=font, fill=255)
                draw.text((0, Y_LINE_2), reboot, font=font, fill=255)

    # === OLED output ===
    if oled_available:
        try:
            oled.display(image)
        except Exception as e:
            append_session_log(f"?? OLED display error: {e}")
            oled_available = False

def clear_oled():
    if not oled_available:
        return
    try:
        image = Image.new("1", (WIDTH, HEIGHT), 0)  # All black
        oled.display(image)
        print("[OLED] Screen cleared.")
    except Exception as e:
        append_session_log("? Failed to clear OLED:", e)
def menu_monitor():
    global menu_index, menu_active, current_voltage_index, menu_last_activity
    global pin_entry_digit, entered_pin, pin_editing, server_pin
    global voltage_preview_index, power_submenu_index, confirming_power_action, confirmation_selection
    global menu_editing

    last_menu = GPIO.input(BUTTON_MENU_PIN)
    last_up = GPIO.input(BUTTON_UP_PIN)
    last_down = GPIO.input(BUTTON_DOWN_PIN)
    menu_press_time = None
    voltage_preview_index = current_voltage_index

    while True:
        now = time.time()

        if menu_active and now - menu_last_activity > MENU_TIMEOUT:
            menu_active = False
            menu_editing = False
            pin_editing = False
            confirming_power_action = False
            pin_entry_digit = 0
            entered_pin = []
            voltage_preview_index = current_voltage_index

        menu = GPIO.input(BUTTON_MENU_PIN)
        up = GPIO.input(BUTTON_UP_PIN)
        down = GPIO.input(BUTTON_DOWN_PIN)

        # === MENU PRESS HANDLING ===
        if menu == GPIO.LOW and last_menu == GPIO.HIGH:
            menu_press_time = now

        elif menu == GPIO.HIGH and last_menu == GPIO.LOW:
            press_duration = now - menu_press_time if menu_press_time else 0

            if press_duration >= 1.5:
                menu_active = not menu_active
                menu_index = 0
                menu_editing = False
                pin_editing = False
                confirming_power_action = False
                pin_entry_digit = 0
                entered_pin = server_pin[:]
                voltage_preview_index = current_voltage_index
                menu_last_activity = now

            elif menu_active:
                item = menu_items[menu_index]
                menu_last_activity = now

                if not menu_editing:
                    menu_editing = True
                    if item == "PIN Setup":
                        pin_editing = True
                        pin_entry_digit = 0
                        entered_pin = server_pin[:]
                    elif item == "Power Controls":
                        confirming_power_action = False
                        power_submenu_index = 0
                        confirmation_selection = 1  # Default to No
                else:
                    # Edit mode actions
                    if item == "PIN Setup":
                        pin_editing = False
                        pin_entry_digit = 0
                        server_pin = entered_pin[:]
                        menu_editing = False
                    elif item == "Voltage Select":
                        current_voltage_index = voltage_preview_index
                        set_voltage_mode(current_voltage_index)
                        show_temp_message(f"Voltage: {VOLTAGE_MODES[current_voltage_index]}")
                        menu_editing = False
                    elif item == "Power Controls":
                        if not confirming_power_action:
                            confirming_power_action = True
                            confirmation_selection = 1  # Default to No
                        elif confirmation_selection == 0:
                            if power_submenu_index == 0:
                                show_temp_message("Shutting down...")
                                clear_oled()
                                GPIO.setmode(GPIO.BCM)
                                GPIO.setup(SHUTDOWN_GPIO, GPIO.OUT)
                                GPIO.output(SHUTDOWN_GPIO, GPIO.LOW)
                                print("[GPIO] Pin 5 pulled LOW to signal Arduino sleep.")
                                time.sleep(1)
                                os.system("sudo shutdown -h now")

                            else:
                                show_temp_message("Rebooting...")
                                clear_oled()
                                GPIO.setmode(GPIO.BCM)
                                GPIO.setup(SHUTDOWN_GPIO, GPIO.OUT)
                                GPIO.output(SHUTDOWN_GPIO, GPIO.LOW)
                                print("[GPIO] Pin 5 pulled LOW to signal Arduino sleep.")
                                time.sleep(1)
                                os.system("sudo reboot")
                            menu_active = False
                            menu_editing = False
                            confirming_power_action = False
                            return
                        else:
                            confirming_power_action = False
                            menu_editing = False


        # === UP / DOWN HANDLING ===
        if menu_active:
            item = menu_items[menu_index]

            if up == GPIO.LOW and last_up == GPIO.HIGH:
                menu_last_activity = now
                if menu_editing:
                    if item == "PIN Setup" and pin_editing:
                        entered_pin[pin_entry_digit] = (entered_pin[pin_entry_digit] + 1) % 10
                    elif item == "Voltage Select":
                        voltage_preview_index = (voltage_preview_index - 1) % len(VOLTAGE_MODES)
                    elif item == "Power Controls":
                        if confirming_power_action:
                            confirmation_selection = (confirmation_selection - 1) % 2
                        else:
                            power_submenu_index = (power_submenu_index - 1) % 2
                else:
                    menu_index = (menu_index - 1) % len(menu_items)

            if down == GPIO.LOW and last_down == GPIO.HIGH:
                menu_last_activity = now
                if menu_editing:
                    if item == "PIN Setup" and pin_editing:
                        entered_pin[pin_entry_digit] = (entered_pin[pin_entry_digit] - 1) % 10
                    elif item == "Voltage Select":
                        voltage_preview_index = (voltage_preview_index + 1) % len(VOLTAGE_MODES)
                    elif item == "Power Controls":
                        if confirming_power_action:
                            confirmation_selection = (confirmation_selection + 1) % 2
                        else:
                            power_submenu_index = (power_submenu_index + 1) % 2
                else:
                    menu_index = (menu_index + 1) % len(menu_items)

        # === Render and update ===
        last_menu = menu
        last_up = up
        last_down = down
        if not suppress_menu_draw:
            draw_menu()
        time.sleep(0.05)


def show_temp_message(text, duration=2):
    global suppress_menu_draw
    if not oled_available:
        return
    try:
        suppress_menu_draw = True  # Pause menu drawing
        image = Image.new("1", (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(image)
        w = draw.textlength(text, font=font)
        draw.text(((WIDTH - w) // 2, HEIGHT // 2 - 6), text, font=font, fill=255)
        oled.display(image)
        time.sleep(duration)
    except Exception as e:
        append_session_log("? OLED temp msg error:", e)
    finally:
        suppress_menu_draw = False
        draw_menu()

def start_session_log(connection_type, voltage_mode, digital_modes):
    global SESSION_LOG, SESSION_LOG_PATH

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"SessionLog_{timestamp}.json"
    SESSION_LOG_PATH = os.path.join(SESSION_LOG_DIR, filename)

    SESSION_LOG = {
        "timestamp_start": datetime.now().isoformat(),
        "connection_type": connection_type,
        "voltage_mode": voltage_mode,
        "dio": {
            "digital": digital_modes
        },
        "system_logs": []
    }

    with open(SESSION_LOG_PATH, "w") as f:
        json.dump(SESSION_LOG, f, indent=2)

def append_session_log(message, level="INFO"):
    global SESSION_LOG, SESSION_LOG_PATH

    if not SESSION_LOG_PATH:
        return

    log_line = f"[{level.upper()}] {message}"
    SESSION_LOG["system_logs"].append(log_line)

    try:
        with open(SESSION_LOG_PATH, "w") as f:
            json.dump(SESSION_LOG, f, indent=2)
    except Exception as e:
        print("Failed to write session log:", e)

class ShellRedirector(StringIO):
    def write(self, msg):
        msg = msg.strip()
        if not msg:
            return 0
        if "reloading Detected change" in msg:
            return len(msg) 
        socketio.emit('shell_output', msg + '\n')
        return len(msg)

    def flush(self):
        pass
if __name__ == "__main__":
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

    threading.Thread(target=menu_monitor, daemon=True).start()
    threading.Thread(target=usb_monitor, daemon=True).start()
    threading.Thread(target=serial_reader, daemon=True).start()
    sys.stdout = ShellRedirector()
    sys.stderr = ShellRedirector()

    if debugg:
        print("Debugging mode enabled")

    socketio.run(app, host="0.0.0.0", port=5000, debug=debugg)
