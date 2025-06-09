import os
import json
import requests
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.urandom(24)

LISTENER_URL = "http://localhost:5001"

def fetch_sensor_data():
    try:
        response = requests.get(f"{LISTENER_URL}/data", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️ Error fetching sensor data: {e}")
        return {"nodes": []}

@app.route('/')
def dashboard():
    raw = fetch_sensor_data()
    chart_data = {'temperature': {}, 'relativeHumidity': {}}
    latest_metrics = {}
    last_seen = {}
    now = datetime.now(timezone.utc)
    latest_time = 0

    for node in raw.get("nodes", []):
        name = node.get("longName", "Unknown").strip()
        telemetry = sorted(node.get("telemetry", []), key=lambda x: x["time"], reverse=True)

        latest_metrics[name] = {'temperature': None, 'relativeHumidity': None}
        last_seen[name] = "Never"

        if not telemetry:
            continue

        latest = telemetry[0]
        latest_time = max(latest_time, latest["time"])
        delta = now - datetime.fromtimestamp(latest["time"], tz=timezone.utc)
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        last_seen[name] = f"{minutes} min {seconds} sec ago" if minutes else f"{seconds} sec ago"

        metrics = latest["environmentMetrics"]
        latest_metrics[name] = {
            'temperature': metrics.get("temperature"),
            'relativeHumidity': metrics.get("relativeHumidity")
        }

        for t in telemetry:
            ts = datetime.fromtimestamp(t["time"], tz=timezone.utc).isoformat()
            for k in chart_data:
                v = t["environmentMetrics"].get(k)
                if v is not None:
                    chart_data[k].setdefault(name, []).append([ts, v])

    return render_template("dashboard.html",
        chart_data=chart_data,
        latest_metrics=latest_metrics,
        last_seen=last_seen,
        latest_time=latest_time
    )

@app.route('/nodes')
def nodes_list():
    raw = fetch_sensor_data()
    return jsonify([
        {"name": node.get("longName", "Unnamed").strip(), "id": node.get("nodeID")}
        for node in raw.get("nodes", [])
    ])

@app.route('/node/<int:node_id>')
def node_detail(node_id):
    raw = fetch_sensor_data()
    for node in raw.get("nodes", []):
        if node.get("nodeID") == node_id:
            metrics = {}
            for t in node.get("telemetry", []):
                ts = datetime.fromtimestamp(t["time"], tz=timezone.utc).isoformat()
                for k, v in t.get("environmentMetrics", {}).items():
                    metrics.setdefault(k, []).append((ts, v))
            return render_template(
                "node_detail.html",
                node_id=node_id,
                node_name=node.get("longName", "Unknown"),
                metrics=metrics
            )
    return "Node not found", 404


@app.route('/trigger', methods=['POST'])
def trigger_telemetry():
    try:
        response = requests.post(f"{LISTENER_URL}/requestTelemetry", timeout=10)
        if response.ok:
            flash("📡 Telemetry request sent to listener.")
        else:
            flash(f"❌ Listener error: {response.text}")
    except Exception as e:
        flash(f"❌ Cannot reach telemetry listener: {str(e)}")
    return redirect(url_for('dashboard'))

@app.route('/latest-data')
def latest_data():
    raw = fetch_sensor_data()
    latest_metrics = {}
    last_seen = {}
    now = datetime.now(timezone.utc)
    last_timestamps = {}

    for node in raw.get("nodes", []):
        name = node.get("longName", "Unknown").strip()
        telemetry = sorted(node.get("telemetry", []), key=lambda x: x["time"], reverse=True)

        latest_metrics[name] = {'temperature': None, 'relativeHumidity': None}
        last_seen[name] = "Never"

        if telemetry:
            latest = telemetry[0]
            last_timestamps[name] = latest["time"]

            delta = now - datetime.fromtimestamp(latest["time"], tz=timezone.utc)
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            last_seen[name] = f"{minutes} min {seconds} sec ago" if minutes else f"{seconds} sec ago"

            metrics = latest["environmentMetrics"]
            latest_metrics[name] = {
                'temperature': metrics.get("temperature"),
                'relativeHumidity': metrics.get("relativeHumidity")
            }

    latest_time = max(last_timestamps.values(), default=0)

    return jsonify({
        "metrics": latest_metrics,
        "lastSeen": last_seen,
        "lastTimestamps": last_timestamps,
        "lastUpdated": latest_time
    })

@app.route('/latest-chart-data')
def latest_chart_data():
    raw = fetch_sensor_data()
    chart_points = {}

    for node in raw.get("nodes", []):
        name = node.get("longName", "Unknown").strip()
        telemetry = node.get("telemetry", [])
        if not telemetry:
            continue

        latest = sorted(telemetry, key=lambda x: x["time"], reverse=True)[0]
        ts = datetime.fromtimestamp(latest["time"], tz=timezone.utc).isoformat()

        for metric, value in latest["environmentMetrics"].items():
            if value is not None:
                chart_points.setdefault(metric, {}).setdefault(name, []).append([ts, value])

    return jsonify(chart_points)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
