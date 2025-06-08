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
CH_INDEX = config["channel_index"]

# Load DB
try:
    db = data_modules.SensorDataBase.from_json_file(DB_FILE)
except Exception:
    db = data_modules.SensorDataBase([])

iface = None  # Global interface object

# Handle incoming telemetry
def onReceive(packet, interface):
    if (
        packet["decoded"]["portnum"] == "TELEMETRY_APP" and
        (packet["fromId"] or packet["from"]) in NODE_IDS and
        "environmentMetrics" in packet["decoded"]["telemetry"]
    ):
        print(f"📥 Received telemetry from {packet['fromId']}")
        processTelemetry(packet, interface, db, DB_FILE)

# Handle connection loss
def onConnectionLost():
    global iface
    print("⚠️ Connection to Meshtastic lost. Reconnecting...")
    try:
        iface.close()
    except:
        pass
    time.sleep(2)
    connect_to_radio()

# Connect or reconnect to radio
def connect_to_radio():
    global iface
    while True:
        try:
            iface = meshtastic.tcp_interface.TCPInterface(RADIO_HOST)
            pub.subscribe(onReceive, "meshtastic.receive")
            pub.subscribe(onConnectionLost, "meshtastic.connection.lost")
            print("✅ Connected to Meshtastic Node.")
            break
        except Exception as e:
            print(f"❌ Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

# Flask microservice
listener_app = Flask(__name__)

@listener_app.route("/requestTelemetry", methods=["POST"])
def trigger_telemetry():
    def background_request():
        try:
            requestTelemetry(iface, NODE_IDS, CH_INDEX)
            print("📡 Sent telemetry requests.")
        except Exception as e:
            print(f"❌ Error during telemetry request: {e}")
    threading.Thread(target=background_request).start()
    return jsonify({"status": "ok", "message": "Telemetry request started."})

# Start Flask
def run_listener():
    listener_app.run(port=5001, debug=False, use_reloader=False)

# Start everything
if __name__ == "__main__":
    print("🚀 Starting MeshSensor listener service...")
    connect_to_radio()
    threading.Thread(target=run_listener).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if iface:
            iface.close()
        print("🔌 Listener stopped.")
