"""
Database initialization and session management.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles database connection, session management, and initialization."""
    
    def __init__(self, db_url="sqlite:///sensorDB.db"):
        """
        Initialize database manager.
        
        Args:
            db_url: Database URL (default: SQLite file)
                   Examples:
                   - "sqlite:///sensorDB.db" (file-based)
                   - "sqlite:///:memory:" (in-memory)
                   - "mysql+pymysql://user:pass@localhost/meshsensor"
        """
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None
        self._init_engine()
    
    def _init_engine(self):
        """Create SQLAlchemy engine with appropriate configuration."""
        # Use StaticPool for SQLite to avoid threading issues
        if self.db_url.startswith("sqlite"):
            self.engine = create_engine(
                self.db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            # For MySQL/MariaDB
            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
        
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        ))
    
    def init_db(self):
        """Create all tables defined in models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def close_session(self):
        """Close the current session."""
        self.SessionLocal.remove()
    
    def drop_all(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def __enter__(self):
        return self.get_session()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()
