"""
SQLAlchemy models for MeshSensor telemetry data.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Node(Base):
    """Represents a Meshtastic node in the mesh network."""
    
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True)
    node_id = Column(String(50), unique=True, nullable=False, index=True)
    long_name = Column(String(255))
    short_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    telemetry = relationship("Telemetry", back_populates="node", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Node(node_id={self.node_id}, name={self.long_name})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "nodeID": self.node_id,
            "longName": self.long_name or "Unknown",
            "shortName": self.short_name or "N/A"
        }


class Telemetry(Base):
    """Represents environmental telemetry data from a node."""
    
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True)
    node_id = Column(String(50), ForeignKey("nodes.node_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float)
    relative_humidity = Column(Float)
    barometric_pressure = Column(Float)
    iaq = Column(Float)
    iaq_accuracy = Column(Integer)
    voltage = Column(Float)
    current = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_packet = Column(String)  # For debugging/future use
    
    # Relationships
    node = relationship("Node", back_populates="telemetry")
    
    # Composite index for common queries
    __table_args__ = (
        Index("idx_node_timestamp", "node_id", "timestamp"),
    )
    
    def __repr__(self):
        return f"<Telemetry(node_id={self.node_id}, timestamp={self.timestamp}, temp={self.temperature})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "nodeID": self.node_id,
            "timestamp": int(self.timestamp.timestamp()) if self.timestamp else None,
            "time": int(self.timestamp.timestamp()) if self.timestamp else None,
            "environmentMetrics": {
                "temperature": self.temperature,
                "relativeHumidity": self.relative_humidity,
                "barometricPressure": self.barometric_pressure,
                "iaq": self.iaq,
                "iaqAccuracy": self.iaq_accuracy
            },
            "voltage": self.voltage,
            "current": self.current
        }
