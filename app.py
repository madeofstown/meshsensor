import os
import json
import datetime
import data_modules
import requests
from flask import Flask, render_template, jsonify, redirect, url_for, flash
from datetime import datetime, timezone

# Load config
with open("config.json") as f:
    config = json.load(f)

RADIO_HOST = config["radio_host"]
NODE_IDS = config["node_ids"]
DB_FILE = config["db_file"]

app = Flask(__name__)
app.secret_key = os.urandom(24)

def load_raw_data():
    try:
        with open(DB_FILE) as f:
            content = f.read().strip()
            if not content or content == "{}":
                raise ValueError("sensorDB.json is empty or missing required fields.")
            return data_modules.SensorDataBase.from_json(content)
    except Exception as e:
        print(f"Error loading sensor DB: {e}")
        return data_modules.SensorDataBase([])


def convert_timestamp(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

@app.route('/')
def dashboard():
    data = load_raw_data()
    chart_data = {'temperature': {}, 'relativeHumidity': {}}
    latest_metrics = {}
    last_seen = {}
    now = datetime.now(timezone.utc)
    latest_timestamp = 0

    for node in data.nodes:
        name = node.longName.strip()
        telemetry = sorted(node.telemetry, key=lambda x: x.time, reverse=True)
        latest_metrics[name] = {'temperature': None, 'relativeHumidity': None}
        last_seen[name] = "Never"
        if not telemetry:
            continue

        latest = telemetry[0]
        metrics = latest.environmentMetrics

        latest_metrics[name] = {
            'temperature': metrics.get('temperature'),
            'relativeHumidity': metrics.get('relativeHumidity')
        }

        last_time = datetime.fromtimestamp(latest.time, tz=timezone.utc)
        delta = now - last_time
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        last_seen[name] = f"{minutes} min {seconds} sec ago" if minutes else f"{seconds} sec ago"

        latest_timestamp = max(latest_timestamp, latest.time)

        for t in telemetry:
            ts = datetime.fromtimestamp(t.time, tz=timezone.utc).isoformat()
            for key in chart_data:
                value = t.environmentMetrics.get(key)
                if value is not None:
                    chart_data[key].setdefault(name, []).append((ts, value))

    return render_template(
        "dashboard.html",
        chart_data=chart_data,
        latest_metrics=latest_metrics,
        last_seen=last_seen,
        latest_time=int(latest_timestamp)
    )

@app.route('/node/<int:node_id>')
def node_detail(node_id):
    data = load_raw_data()
    for node in data.nodes:
        if node.nodeID == node_id:
            metrics = {}
            for t in node.telemetry:
                ts = convert_timestamp(t.time)
                for k, v in t.environmentMetrics.items():
                    metrics.setdefault(k, []).append((ts, v))
            return render_template("node_detail.html", node_id=node.nodeID, node_name=node.longName, metrics=metrics)
    return "Node not found", 404

@app.route('/nodes')
def nodes_list():
    data = load_raw_data()
    return jsonify([
        {"name": node.longName.strip(), "id": node.nodeID}
        for node in data.nodes
    ])

@app.route('/trigger', methods=['POST'])
def trigger_telemetry():
    try:
        response = requests.post("http://localhost:5001/requestTelemetry", timeout=20)
        if response.ok:
            flash("📡 Telemetry request sent to listener.")
        else:
            flash(f"❌ Listener error: {response.text}")
    except requests.RequestException as e:
        flash(f"❌ Cannot reach telemetry listener: {str(e)}")
    return redirect(url_for('dashboard'))

@app.route('/latest-data')
def latest_data():
    data = load_raw_data()
    latest_metrics = {}
    last_seen = {}
    last_timestamps = {}
    now = datetime.now(timezone.utc)

    for node in data.nodes:
        name = node.longName.strip()
        telemetry = sorted(node.telemetry, key=lambda x: x.time, reverse=True)
        latest_metrics[name] = {'temperature': None, 'relativeHumidity': None}
        last_seen[name] = "Never"
        if not telemetry:
            continue

        latest = telemetry[0]
        metrics = latest.environmentMetrics

        latest_metrics[name] = {
            'temperature': metrics.get('temperature'),
            'relativeHumidity': metrics.get('relativeHumidity')
        }

        last_time = datetime.fromtimestamp(latest.time, tz=timezone.utc)
        delta = now - last_time
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        last_seen[name] = f"{minutes} min {seconds} sec ago" if minutes else f"{seconds} sec ago"
        last_timestamps[name] = int(latest.time)

    latest_timestamp = max(
        (t.time for node in data.nodes for t in node.telemetry),
        default=0
    )

    return jsonify({
        "metrics": latest_metrics,
        "lastSeen": last_seen,
        "lastTimestamps": last_timestamps,
        "lastUpdated": int(latest_timestamp)
    })

@app.route('/latest-chart-data')
def latest_chart_data():
    data = load_raw_data()
    chart_points = {}

    for node in data.nodes:
        name = node.longName.strip()
        if not node.telemetry:
            continue
        latest = sorted(node.telemetry, key=lambda x: x.time, reverse=True)[0]
        timestamp = datetime.fromtimestamp(latest.time, tz=timezone.utc).isoformat()

        for metric, value in latest.environmentMetrics.items():
            if value is not None:
                chart_points.setdefault(metric, {}).setdefault(name, []).append([timestamp, value])

    return jsonify(chart_points)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
