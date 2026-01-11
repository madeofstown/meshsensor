"""
MeshSensor Listener Service - Refactored Backend
Listens to Meshtastic telemetry packets and stores them in SQLite database.
Provides REST API for data access.
"""

import logging
import logging.handlers
import json
import threading
import time
import traceback
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from pubsub import pub
import meshtastic
import meshtastic.tcp_interface

from database import DatabaseManager
from models import Node, Telemetry
from db_migration import DatabaseMigration

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_file="listener.log"):
    """Configure logging with both file and console output."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logging()

# ============================================================================
# CONFIGURATION
# ============================================================================

def load_config(config_path="config.json"):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration: {e}")
        raise


config = load_config()
RADIO_HOST = config.get("radio_host", "127.0.0.1")
NODE_IDS = [str(nid) for nid in config.get("node_ids", [])]
DB_FILE = config.get("db_file", "sensorDB.db")
CH_INDEX = config.get("channel_index", 1)
RETENTION_DAYS = config.get("data_retention_days", 30)

logger.info(f"RADIO_HOST: {RADIO_HOST}")
logger.info(f"NODE_IDS: {NODE_IDS}")
logger.info(f"Data retention: {RETENTION_DAYS} days")

# ============================================================================
# DATABASE SETUP
# ============================================================================

db_manager = DatabaseManager(f"sqlite:///{DB_FILE}")
db_manager.init_db()

# Attempt migration from old JSON format
try:
    migration = DatabaseMigration(db_manager)
    migration.migrate_from_json("sensorDB.json")
except Exception as e:
    logger.warning(f"Could not migrate from JSON: {e}")

# ============================================================================
# MESHTASTIC INTERFACE
# ============================================================================

iface = None
connection_lock = threading.Lock()


def normalize_node_id(node_id):
    """Normalize node ID to string format."""
    if isinstance(node_id, int):
        return f"!{node_id:08x}"
    return str(node_id)


def is_watched_node(node_id):
    """Check if a node ID is in the watched list."""
    normalized = normalize_node_id(node_id)
    return normalized in NODE_IDS or str(node_id) in NODE_IDS


def on_receive(packet, interface):
    """Handle incoming Meshtastic packets."""
    try:
        # Check if this is a telemetry packet
        if packet.get("decoded", {}).get("portnum") != "TELEMETRY_APP":
            return
        
        # Check if it's from a watched node
        from_id = packet.get("fromId") or packet.get("from")
        if not is_watched_node(from_id):
            return
        
        # Check if it contains environment metrics
        telemetry_data = packet.get("decoded", {}).get("telemetry", {})
        if "environmentMetrics" not in telemetry_data:
            return
        
        # Process the telemetry
        process_telemetry(packet, interface)
        
    except Exception as e:
        logger.error(f"Error in on_receive: {e}", exc_info=True)


def process_telemetry(packet, interface):
    """Extract and store telemetry data in database."""
    session = db_manager.get_session()
    try:
        # Extract packet information
        from_id = packet.get("fromId") or packet.get("from")
        node_id = normalize_node_id(from_id)
        timestamp = datetime.fromtimestamp(
            packet.get("decoded", {}).get("telemetry", {}).get("time", time.time()),
            tz=timezone.utc
        )
        env_metrics = packet.get("decoded", {}).get("telemetry", {}).get("environmentMetrics", {})
        
        # Get or create node
        node = session.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            # Get node details from interface if available
            long_name = "Unknown"
            short_name = "N/A"
            
            for iface_node in interface.nodes.values():
                if str(iface_node.get("num")) == str(from_id):
                    long_name = iface_node.get("user", {}).get("longName", "Unknown")
                    short_name = iface_node.get("user", {}).get("shortName", "N/A")
                    break
            
            node = Node(
                node_id=node_id,
                long_name=long_name,
                short_name=short_name
            )
            session.add(node)
            session.flush()
            logger.info(f"Created new node: {node_id} ({long_name})")
        else:
            # Update last_seen
            node.last_seen = datetime.utcnow()
        
        # Create telemetry record
        telemetry = Telemetry(
            node_id=node_id,
            timestamp=timestamp,
            temperature=env_metrics.get("temperature"),
            relative_humidity=env_metrics.get("relativeHumidity"),
            barometric_pressure=env_metrics.get("barometricPressure"),
            iaq=env_metrics.get("iaq"),
            iaq_accuracy=env_metrics.get("iaqAccuracy")
        )
        session.add(telemetry)
        session.commit()
        
        logger.info(
            f"Stored telemetry from {node.short_name}: "
            f"temp={telemetry.temperature}°F, humidity={telemetry.relative_humidity}%"
        )
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing telemetry: {e}", exc_info=True)
    finally:
        session.close()


def on_connection_lost():
    """Handle connection loss to Meshtastic radio."""
    global iface
    logger.warning("Connection to Meshtastic lost. Reconnecting...")
    with connection_lock:
        try:
            if iface:
                iface.close()
        except Exception as e:
            logger.debug(f"Error closing interface: {e}")
        
        time.sleep(2)
        connect_to_radio()


def connect_to_radio():
    """Connect to Meshtastic radio with automatic reconnection."""
    global iface
    
    retry_count = 0
    max_retries = 10
    retry_delay = 5
    
    while retry_count < max_retries:
        try:
            with connection_lock:
                logger.info(f"Connecting to Meshtastic at {RADIO_HOST}...")
                iface = meshtastic.tcp_interface.TCPInterface(hostname=RADIO_HOST)
                
                # Subscribe to events
                pub.subscribe(on_receive, "meshtastic.receive")
                pub.subscribe(on_connection_lost, "meshtastic.connection.lost")
                
                logger.info("Successfully connected to Meshtastic node")
                retry_count = 0
                return
                
        except Exception as e:
            retry_count += 1
            wait_time = retry_delay * (2 ** min(retry_count - 1, 3))  # Exponential backoff
            logger.error(
                f"Connection failed (attempt {retry_count}/{max_retries}): {e}. "
                f"Retrying in {wait_time} seconds..."
            )
            time.sleep(wait_time)
    
    logger.critical("Failed to connect to Meshtastic after multiple attempts")
    raise RuntimeError("Could not connect to Meshtastic radio")


def request_telemetry():
    """Request fresh telemetry from all configured nodes."""
    if not iface:
        logger.warning("Interface not connected, cannot request telemetry")
        return
    
    try:
        for node_id in NODE_IDS:
            # Handle both string and numeric node IDs
            dest_id = node_id
            if node_id.startswith("!"):
                dest_id = int(node_id[1:], 16)
            
            iface.sendTelemetry(
                destinationId=dest_id,
                wantResponse=True,
                channelIndex=CH_INDEX,
                telemetryType="environment_metrics"
            )
            logger.debug(f"Requested telemetry from {node_id}")
        
        logger.info("Telemetry requests sent to all nodes")
    except Exception as e:
        logger.error(f"Error requesting telemetry: {e}", exc_info=True)


# ============================================================================
# FLASK API
# ============================================================================

listener_app = Flask(__name__)


@listener_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "radio_connected": iface is not None
    }), 200


@listener_app.route("/api/nodes", methods=["GET"])
def get_nodes():
    """Get list of all nodes."""
    session = db_manager.get_session()
    try:
        nodes = session.query(Node).all()
        return jsonify({
            "nodes": [node.to_dict() for node in nodes]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching nodes: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@listener_app.route("/api/nodes/<node_id>/telemetry", methods=["GET"])
def get_node_telemetry(node_id):
    """Get telemetry for a specific node with pagination."""
    session = db_manager.get_session()
    try:
        # Query parameters
        limit = min(int(request.args.get("limit", 100)), 1000)
        offset = int(request.args.get("offset", 0))
        
        node = session.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            return jsonify({"error": "Node not found"}), 404
        
        # Get telemetry with pagination
        query = session.query(Telemetry).filter(
            Telemetry.node_id == node_id
        ).order_by(Telemetry.timestamp.desc())
        
        total_count = query.count()
        telemetry_records = query.limit(limit).offset(offset).all()
        
        return jsonify({
            "node": node.to_dict(),
            "telemetry": [t.to_dict() for t in telemetry_records],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": "Invalid query parameters"}), 400
    except Exception as e:
        logger.error(f"Error fetching node telemetry: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@listener_app.route("/api/telemetry/latest", methods=["GET"])
def get_latest_telemetry():
    """Get latest telemetry from all nodes."""
    session = db_manager.get_session()
    try:
        nodes = session.query(Node).all()
        result = []
        
        for node in nodes:
            latest = session.query(Telemetry).filter(
                Telemetry.node_id == node.node_id
            ).order_by(Telemetry.timestamp.desc()).first()
            
            if latest:
                result.append({
                    "node": node.to_dict(),
                    "latest": latest.to_dict()
                })
        
        return jsonify({"data": result}), 200
    except Exception as e:
        logger.error(f"Error fetching latest telemetry: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@listener_app.route("/api/telemetry", methods=["GET"])
def query_telemetry():
    """
    Query telemetry with filters.
    
    Query parameters:
    - start: ISO format timestamp (inclusive)
    - end: ISO format timestamp (inclusive)
    - node_id: Filter by node ID
    - limit: Max records to return (default 100, max 1000)
    - offset: Pagination offset (default 0)
    """
    session = db_manager.get_session()
    try:
        limit = min(int(request.args.get("limit", 100)), 1000)
        offset = int(request.args.get("offset", 0))
        start_str = request.args.get("start")
        end_str = request.args.get("end")
        node_id = request.args.get("node_id")
        
        query = session.query(Telemetry)
        
        # Apply filters
        if start_str:
            try:
                start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                query = query.filter(Telemetry.timestamp >= start)
            except ValueError:
                return jsonify({"error": "Invalid start timestamp format"}), 400
        
        if end_str:
            try:
                end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                query = query.filter(Telemetry.timestamp <= end)
            except ValueError:
                return jsonify({"error": "Invalid end timestamp format"}), 400
        
        if node_id:
            query = query.filter(Telemetry.node_id == node_id)
        
        total_count = query.count()
        records = query.order_by(Telemetry.timestamp.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            "telemetry": [t.to_dict() for t in records],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count
            }
        }), 200
    except ValueError as e:
        return jsonify({"error": "Invalid query parameters"}), 400
    except Exception as e:
        logger.error(f"Error querying telemetry: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@listener_app.route("/api/telemetry/request", methods=["POST"])
def trigger_telemetry():
    """Trigger telemetry request from all nodes."""
    def background_request():
        try:
            request_telemetry()
        except Exception as e:
            logger.error(f"Error in background telemetry request: {e}")
    
    threading.Thread(target=background_request, daemon=True).start()
    return jsonify({"status": "ok", "message": "Telemetry request initiated"}), 202


@listener_app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get database statistics."""
    try:
        migration = DatabaseMigration(db_manager)
        stats = migration.get_database_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


@listener_app.route("/data", methods=["GET"])
def get_data_legacy():
    """Legacy endpoint for backward compatibility with old frontend."""
    session = db_manager.get_session()
    try:
        nodes = session.query(Node).all()
        result = {
            "nodes": []
        }
        
        for node in nodes:
            telemetry = session.query(Telemetry).filter(
                Telemetry.node_id == node.node_id
            ).order_by(Telemetry.timestamp.desc()).all()
            
            node_dict = {
                "nodeID": node.node_id,
                "longName": node.long_name,
                "shortName": node.short_name,
                "telemetry": [t.to_dict() for t in telemetry]
            }
            result["nodes"].append(node_dict)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching legacy data: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ============================================================================
# MAIN
# ============================================================================

def run_listener(host="0.0.0.0", port=5001):
    """Run the Flask listener service."""
    logger.info(f"Starting Flask API on {host}:{port}")
    listener_app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("MeshSensor Listener Service Starting")
    logger.info("=" * 70)
    
    try:
        # Connect to radio
        connect_to_radio()
        
        # Start periodic data cleanup
        def periodic_cleanup():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    migration = DatabaseMigration(db_manager)
                    migration.prune_old_data(RETENTION_DAYS)
                except Exception as e:
                    logger.error(f"Error in periodic cleanup: {e}")
        
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        
        # Start Flask
        flask_thread = threading.Thread(target=run_listener, daemon=False)
        flask_thread.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        if iface:
            try:
                iface.close()
            except:
                pass
        db_manager.close_session()
        logger.info("Listener service stopped")
