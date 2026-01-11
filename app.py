import os
import json
import logging
import requests
import time
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LISTENER_URL = "http://localhost:5001"
REQUEST_TIMEOUT = 5

def unix_to_local(timestamp):
    """Convert Unix timestamp to local datetime string."""
    if timestamp is None:
        return "Never"
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return "Invalid"
    except (ValueError, OSError, OverflowError):
        return "Invalid"

def fetch_sensor_data():
    """Fetch sensor data from listener service (legacy format for compatibility)."""
    try:
        response = requests.get(f"{LISTENER_URL}/data", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching sensor data")
        return {"nodes": []}
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to listener service")
        return {"nodes": []}
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        return {"nodes": []}

def fetch_latest_telemetry():
    """Fetch latest telemetry from all nodes."""
    try:
        response = requests.get(f"{LISTENER_URL}/api/telemetry/latest", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        logger.error(f"Error fetching latest telemetry: {e}")
        return []

def fetch_nodes():
    """Fetch list of all nodes."""
    try:
        response = requests.get(f"{LISTENER_URL}/api/nodes", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("nodes", [])
    except Exception as e:
        logger.error(f"Error fetching nodes: {e}")
        return []

@app.route('/')
def dashboard():
    raw = fetch_sensor_data()
    chart_data = {'temperature': {}, 'relativeHumidity': {}}
    latest_metrics = {}
    last_seen = {}
    now = datetime.now(timezone.utc)
    latest_time = 0

    def parse_timestamp(tel):
        """Extract Unix timestamp from telemetry data."""
        # Try timestamp field first, then time field for backward compatibility
        ts = tel.get("timestamp") or tel.get("time")
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return datetime.utcnow()

    for node in raw.get("nodes", []):
        name = node.get("longName", "Unknown").strip()
        telemetry = node.get("telemetry", [])
        telemetry = sorted(telemetry, key=parse_timestamp, reverse=True)

        latest_metrics[name] = {'temperature': None, 'relativeHumidity': None}
        last_seen[name] = "Never"

        if not telemetry:
            continue

        latest = telemetry[0]
        latest_ts = parse_timestamp(latest)
        latest_time = max(latest_time, latest_ts.timestamp())
        last_seen[name] = unix_to_local(latest_ts.timestamp())

        metrics = latest.get("environmentMetrics", {})
        latest_metrics[name] = {
            'temperature': metrics.get("temperature"),
            'relativeHumidity': metrics.get("relativeHumidity")
        }

        for t in telemetry:
            ts_obj = parse_timestamp(t)
            ts_unix = ts_obj.timestamp()
            for k in chart_data:
                v = t.get("environmentMetrics", {}).get(k)
                if v is not None:
                    chart_data[k].setdefault(name, []).append([ts_unix, v])

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

@app.route('/node/<node_id>')
def node_detail(node_id):
    """Display detail page for a specific node."""
    raw = fetch_sensor_data()
    
    def parse_timestamp(tel):
        ts = tel.get("timestamp") or tel.get("time")
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return datetime.utcnow()
    
    for node in raw.get("nodes", []):
        if node.get("nodeID") == node_id or str(node.get("id")) == str(node_id):
            metrics = {}
            for t in node.get("telemetry", []):
                ts_obj = parse_timestamp(t)
                ts_str = ts_obj.strftime("%Y-%m-%d %H:%M:%S")
                for k, v in t.get("environmentMetrics", {}).items():
                    metrics.setdefault(k, []).append((ts_str, v))
            return render_template(
                "node_detail.html",
                node_id=node_id,
                node_name=node.get("longName", "Unknown"),
                metrics=metrics
            )
    return "Node not found", 404


@app.route('/trigger', methods=['POST'])
def trigger_telemetry():
    """Trigger telemetry request from all nodes."""
    try:
        response = requests.post(f"{LISTENER_URL}/api/telemetry/request", timeout=10)
        if response.status_code in (200, 202):  # 202 Accepted
            flash("📡 Telemetry request sent to listener.")
            logger.info("Telemetry request triggered")
        else:
            flash(f"❌ Listener error: {response.text}")
            logger.warning(f"Listener returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        flash("❌ Cannot connect to telemetry listener")
        logger.error("Cannot reach listener service")
    except Exception as e:
        flash(f"❌ Error: {str(e)}")
        logger.error(f"Error triggering telemetry: {e}")
    return redirect(url_for('dashboard'))

@app.route('/latest-data')
def latest_data():
    """Get latest telemetry for all nodes."""
    raw = fetch_sensor_data()
    latest_metrics = {}
    last_seen = {}
    last_timestamps = {}
    
    def parse_timestamp(tel):
        ts = tel.get("timestamp") or tel.get("time")
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return datetime.utcnow()

    for node in raw.get("nodes", []):
        name = node.get("longName", "Unknown").strip()
        telemetry = sorted(node.get("telemetry", []), key=parse_timestamp, reverse=True)

        latest_metrics[name] = {'temperature': None, 'relativeHumidity': None}
        last_seen[name] = "Never"

        if telemetry:
            latest = telemetry[0]
            ts_obj = parse_timestamp(latest)
            ts_unix = ts_obj.timestamp()
            last_timestamps[name] = ts_unix
            last_seen[name] = unix_to_local(ts_unix)

            metrics = latest.get("environmentMetrics", {})
            latest_metrics[name] = {
                'temperature': metrics.get("temperature"),
                'relativeHumidity': metrics.get("relativeHumidity")
            }

    latest_time = max((datetime.fromisoformat(v.replace('Z', '+00:00')).timestamp() for v in last_timestamps.values()), default=0)

    return jsonify({
        "metrics": latest_metrics,
        "lastSeen": last_seen,
        "lastTimestamps": last_timestamps,
        "lastUpdated": latest_time
    })

@app.route('/latest-chart-data')
def latest_chart_data():
    """Get latest chart data point from each node."""
    raw = fetch_sensor_data()
    chart_points = {}
    
    def parse_timestamp(tel):
        ts = tel.get("timestamp") or tel.get("time")
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return datetime.utcnow()

    for node in raw.get("nodes", []):
        name = node.get("longName", "Unknown").strip()
        telemetry = node.get("telemetry", [])
        if not telemetry:
            continue

        latest = sorted(telemetry, key=parse_timestamp, reverse=True)[0]
        ts_obj = parse_timestamp(latest)
        ts_unix = ts_obj.timestamp()

        for metric, value in latest.get("environmentMetrics", {}).items():
            if value is not None:
                chart_points.setdefault(metric, {}).setdefault(name, []).append([ts_unix, value])

    return jsonify(chart_points)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
