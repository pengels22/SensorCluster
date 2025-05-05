import psutil
import time
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from PIL import ImageDraw, ImageFont, Image
import logging
# Define the name of the script to monitor
TARGET_SCRIPT = "Server-V3.py"  # Change this to your actual script name

# Set up OLED
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)
font = ImageFont.load_default()
logging.basicConfig(
    filename="/home/pi/Cluster/Pi/watchdog.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
def is_script_running(script_name):
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if script_name in ' '.join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def display_message(msg):
    with Image.new("1", device.size) as image:
        draw = ImageDraw.Draw(image)
        draw.rectangle(device.bounding_box, outline=0, fill=0)
        draw.text((10, 25), msg, font=font, fill=255)
        device.display(image)

# Main loop
while True:
    if not is_script_running(TARGET_SCRIPT):
        logging.info("Checking server status...")
        logging.warning("Server is NOT running")
        logging.info("Server is running")
        display_message("Server is NOT running")
    time.sleep(10)  # Check every 10 seconds
