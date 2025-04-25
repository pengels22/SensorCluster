import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

SCRIPT_PATH = "/home/pi/Cluster/Pi/Server-V3.py"
SERVICE_NAME = "sensorcluster.service"

class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith("Server-V3.py"):
            print(f"🔄 Detected change in {event.src_path}. Restarting service...")
            subprocess.run(["sudo", "systemctl", "restart", SERVICE_NAME])

if __name__ == "__main__":
    path = os.path.dirname(SCRIPT_PATH)
    print(f"👀 Watching for changes in {path}...")
    
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
