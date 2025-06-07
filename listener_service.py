from flask import Flask, jsonify
import time
import threading
import json
from pubsub import pub
import meshtastic
import meshtastic.tcp_interface
import threading
import data_modules
from shared_functions import processTelemetry, requestTelemetry, addNode

# Load config
with open("config.json") as f:
    config = json.load(f)

RADIO_HOST = config["radio_host"]
NODE_IDS = config["node_ids"]
DB_FILE = config["db_file"]
channel_index = config["channel_index"]

# Load DB
try:
    db = data_modules.SensorDataBase.from_json_file(DB_FILE)
except Exception:
    db = data_modules.SensorDataBase([])

# TCP connection (single, long-lived)
iface = meshtastic.tcp_interface.TCPInterface(RADIO_HOST)

# Telemetry receiver
def onReceive(packet, interface):
    if (
        packet["decoded"]["portnum"] == "TELEMETRY_APP" and
        packet["fromId"] in NODE_IDS and
        "environmentMetrics" in packet["decoded"]["telemetry"]
    ):
        print(f"📥 Received telemetry from {packet['fromId']}")
        processTelemetry(packet, interface, db, DB_FILE)

pub.subscribe(onReceive, "meshtastic.receive")

# Flask microservice
listener_app = Flask(__name__)

@listener_app.route("/requestTelemetry", methods=["POST"])
def trigger_telemetry():
    def background_request():
        try:
            requestTelemetry(iface, NODE_IDS, channel_index)
            print("📡 Sent telemetry requests.")
        except Exception as e:
            print(f"❌ Error during telemetry request: {e}")

    threading.Thread(target=background_request).start()
    return jsonify({"status": "ok", "message": "Telemetry request started."})


# Start Flask + keep listener alive
def run_listener():
    listener_app.run(port=5001, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("🚀 Starting telemetry listener service on port 5001...")
    threading.Thread(target=run_listener).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        iface.close()
        print("🔌 Listener stopped.")
