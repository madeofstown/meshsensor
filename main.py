import subprocess
import threading
import sys
import signal

flask_cmd = ["python", "app.py"]
listener_cmd = ["python", "listener_service.py"]

def stream_output(prefix, process):
    for line in process.stdout:
        sys.stdout.write(f"[{prefix}] {line.decode()}")
    process.stdout.flush()

flask_proc = subprocess.Popen(flask_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
listener_proc = subprocess.Popen(listener_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

flask_thread = threading.Thread(target=stream_output, args=("Flask", flask_proc))
listener_thread = threading.Thread(target=stream_output, args=("Listener", listener_proc))
flask_thread.start()
listener_thread.start()

def shutdown(signum, frame):
    print("\nShutting down...")
    flask_proc.terminate()
    listener_proc.terminate()
    flask_thread.join()
    listener_thread.join()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

try:
    flask_thread.join()
    listener_thread.join()
except KeyboardInterrupt:
    shutdown(None, None)
