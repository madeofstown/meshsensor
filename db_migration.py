"""
Simple database migration and upgrade utilities.
"""

import logging
from datetime import datetime, timedelta
from database import DatabaseManager
from models import Telemetry, Node

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handles database schema migrations and data management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def migrate_from_json(self, json_db_path="sensorDB.json"):
        """
        Migrate data from old JSON format to SQLite database.
        
        Args:
            json_db_path: Path to old sensorDB.json file
        """
        import json
        
        try:
            with open(json_db_path, 'r') as f:
                old_db = json.load(f)
        except FileNotFoundError:
            logger.info(f"No existing JSON database found at {json_db_path}")
            return
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON database: {e}")
            return
        
        session = self.db_manager.get_session()
        try:
            migrated_count = 0
            
            for node_data in old_db.get("nodes", []):
                node_id = str(node_data.get("nodeID"))
                
                # Check if node already exists
                existing_node = session.query(Node).filter(
                    Node.node_id == node_id
                ).first()
                
                if not existing_node:
                    node = Node(
                        node_id=node_id,
                        long_name=node_data.get("longName", "Unknown"),
                        short_name=node_data.get("shortName", "N/A")
                    )
                    session.add(node)
                    session.flush()
                else:
                    node = existing_node
                
                # Migrate telemetry entries
                for tel_data in node_data.get("telemetry", []):
                    env_metrics = tel_data.get("environmentMetrics", {})
                    
                    telemetry = Telemetry(
                        node_id=node_id,
                        timestamp=datetime.fromtimestamp(tel_data.get("time", 0)),
                        temperature=env_metrics.get("temperature"),
                        relative_humidity=env_metrics.get("relativeHumidity"),
                        barometric_pressure=env_metrics.get("barometricPressure"),
                        iaq=env_metrics.get("iaq"),
                        iaq_accuracy=env_metrics.get("iaqAccuracy")
                    )
                    session.add(telemetry)
                    migrated_count += 1
            
            session.commit()
            logger.info(f"Successfully migrated {migrated_count} telemetry records from JSON")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error during migration: {e}")
            raise
        finally:
            session.close()
    
    def prune_old_data(self, days=30):
        """
        Delete telemetry data older than specified days.
        
        Args:
            days: Number of days of data to keep
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = session.query(Telemetry).filter(
                Telemetry.timestamp < cutoff_date
            ).delete()
            session.commit()
            logger.info(f"Pruned {deleted_count} telemetry records older than {days} days")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"Error pruning data: {e}")
            raise
        finally:
            session.close()
    
    def get_database_stats(self):
        """Get statistics about the database."""
        session = self.db_manager.get_session()
        try:
            node_count = session.query(Node).count()
            telemetry_count = session.query(Telemetry).count()
            
            oldest_record = session.query(Telemetry).order_by(
                Telemetry.timestamp.asc()
            ).first()
            newest_record = session.query(Telemetry).order_by(
                Telemetry.timestamp.desc()
            ).first()
            
            return {
                "nodes": node_count,
                "telemetry_records": telemetry_count,
                "oldest_record": oldest_record.timestamp.isoformat() if oldest_record else None,
                "newest_record": newest_record.timestamp.isoformat() if newest_record else None
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            session.close()
