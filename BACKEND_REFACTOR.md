# MeshSensor - Refactored Backend

## What's New

This is a **major refactor** of the MeshSensor backend with the following improvements:

### 🎯 Core Improvements

1. **SQLite Database Backend**
   - Replaced JSON file storage with SQLite for reliability and scalability
   - Automatic data persistence with proper indexing
   - Support for future MariaDB/MySQL migration

2. **Robust REST API**
   - Comprehensive endpoints for data access
   - Query filtering (by node, date range)
   - Pagination support for large datasets
   - Health checks and statistics

3. **Professional Logging**
   - Structured logging with file rotation
   - Separate console (INFO) and file (DEBUG) levels
   - Log files in `listener.log`

4. **Error Handling & Recovery**
   - Exponential backoff reconnection logic
   - Graceful handling of connection loss
   - Detailed error logging for debugging

5. **Automatic Data Retention**
   - Configurable data retention period (default: 30 days)
   - Automatic cleanup of old records every hour
   - Prevents unbounded database growth

6. **Backward Compatibility**
   - Automatic migration of existing JSON data
   - Legacy `/data` endpoint still works
   - Existing frontend code continues to function

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r new_requirements.txt
```

### 2. Update Configuration

Update `config.json`:

```json
{
  "radio_host": "10.7.0.97",
  "node_ids": ["!20b1663e", "!bb788268", "!718b5394"],
  "db_file": "sensorDB.db",
  "channel_index": 1,
  "data_retention_days": 30
}
```

### 3. Run the Application

```bash
python main.py
```

On first run:
- SQLite database is created
- Old JSON data is automatically migrated
- Services start and connect to Meshtastic radio

Access the dashboard: http://localhost:5000

---

## Architecture

### Components

```
main.py (Orchestrator)
├── listener_service.py (Backend)
│   ├── database.py (SQLAlchemy setup)
│   ├── models.py (Data models)
│   └── db_migration.py (Migration utilities)
└── app.py (Frontend/Dashboard)
```

### Data Flow

```
Meshtastic Radio
    ↓
listener_service.py (Packet Handler)
    ↓
SQLite Database (sensorDB.db)
    ↓
REST API (:5001)
    ↓
Web Dashboard (:5000)
```

---

## API Endpoints

### Health & Stats

- `GET /health` - Service health check
- `GET /api/stats` - Database statistics

### Nodes

- `GET /api/nodes` - List all nodes

### Telemetry

- `GET /api/nodes/<id>/telemetry` - Node telemetry (paginated)
- `GET /api/telemetry/latest` - Latest from all nodes
- `GET /api/telemetry` - Query with filters
- `POST /api/telemetry/request` - Request fresh telemetry

### Backward Compatibility

- `GET /data` - Legacy endpoint (all data)

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete reference.

---

## Configuration

### Main Settings (config.json)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `radio_host` | string | `127.0.0.1` | Meshtastic TCP host |
| `node_ids` | array | `[]` | Node IDs to monitor |
| `db_file` | string | `sensorDB.db` | SQLite database file |
| `channel_index` | int | `1` | Meshtastic channel |
| `data_retention_days` | int | `30` | Days of data to keep |

---

## Logging

### Log Locations

- **Console**: INFO level (important events)
- **File**: `listener.log` (DEBUG level, all details)
  - Max 5MB per file
  - Keeps 5 backup files

### Example Log Output

```
2026-01-10 15:30:00 - [root] - INFO - Configuration loaded from config.json
2026-01-10 15:30:00 - [root] - INFO - Database initialized successfully
2026-01-10 15:30:01 - [root] - INFO - Successfully migrated 1542 telemetry records
2026-01-10 15:30:02 - [root] - INFO - Successfully connected to Meshtastic node
2026-01-10 15:30:15 - [root] - INFO - Stored telemetry from Porch: temp=72.5°F, humidity=45.2%
```

---

## Database

### Schema

**nodes table:**
- `id` - Primary key
- `node_id` - Unique node identifier (e.g., "!20b1663e")
- `long_name` - Full node name
- `short_name` - Short name
- `created_at` - First seen
- `last_seen` - Last telemetry timestamp

**telemetry table:**
- `id` - Primary key
- `node_id` - Foreign key to nodes
- `timestamp` - UTC timestamp
- `temperature` - Fahrenheit
- `relative_humidity` - Percentage
- `barometric_pressure` - hPa
- `iaq` - Air quality index
- `voltage` - Supply voltage
- `current` - Current draw

### Querying

SQLite can be queried directly:

```bash
sqlite3 sensorDB.db

# View schema
.schema

# Count records
SELECT COUNT(*) FROM telemetry;

# Recent data (last hour)
SELECT * FROM telemetry 
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;
```

### Data Retention

Automatic cleanup runs every hour:
- Deletes telemetry older than `data_retention_days`
- Preserves node definitions
- Configurable cleanup is in `db_migration.py`

Manual cleanup:

```python
from database import DatabaseManager
from db_migration import DatabaseMigration

db = DatabaseManager()
migration = DatabaseMigration(db)
migration.prune_old_data(days=7)  # Keep only 7 days
```

---

## Migration from Old Version

1. **Backup existing data:**
   ```bash
   cp sensorDB.json sensorDB.json.backup
   ```

2. **Install new requirements:**
   ```bash
   pip install -r new_requirements.txt
   ```

3. **Update config.json:**
   - Change `db_file` from `sensorDB.json` to `sensorDB.db`
   - Add `data_retention_days` field

4. **First run (auto-migration):**
   ```bash
   python listener_service.py
   ```
   
   The system automatically:
   - Creates SQLite database
   - Imports all JSON data
   - Logs migration status

5. **Verify:**
   ```bash
   curl http://localhost:5001/api/stats
   ```

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed instructions.

---

## Troubleshooting

### Connection Issues

**Error:** "Connection failed: Connection refused"
- Verify Meshtastic TCP server is running
- Check `radio_host` in config.json
- Ping the radio: `ping 10.7.0.97`

### Database Issues

**Error:** "database is locked"
- Close other apps accessing the database
- Ensure only one listener instance is running

**Error:** "Out of disk space"
- Reduce `data_retention_days` in config
- Or manually prune old data

### Performance Issues

**Database is slow:**
- Check `listener.log` for errors
- Consider reducing data retention period
- Use pagination in API queries

---

## Files Changed

### New Files

- `models.py` - SQLAlchemy ORM models
- `database.py` - Database connection management
- `db_migration.py` - Migration and retention utilities
- `API_DOCUMENTATION.md` - Full API reference
- `MIGRATION_GUIDE.md` - Migration instructions

### Modified Files

- `listener_service.py` - Complete rewrite with DB integration
- `app.py` - Updated to use new API endpoints
- `main.py` - Improved orchestration and logging
- `config.json` - Added `data_retention_days` field
- `new_requirements.txt` - Added SQLAlchemy and alembic

### Deprecated Files (kept for reference)

- `data_modules.py` - Replaced by models.py
- `shared_functions.py` - Integrated into listener_service.py
- `listener_service_old.py` - Original implementation

---

## Next Steps

1. **Production Deployment:**
   - Add authentication to API endpoints
   - Use production WSGI server (gunicorn, uWSGI)
   - Set up automated backups of `sensorDB.db`

2. **Enhancements:**
   - Data aggregation endpoints (hourly/daily averages)
   - WebSocket support for real-time updates
   - Export to CSV/Parquet format
   - Multi-user support

3. **Database Migration:**
   - Switch to MariaDB for larger deployments
   - Update connection string in `database.py`

4. **Monitoring:**
   - Set up log aggregation
   - Monitor disk usage for database growth
   - Alert on connection failures

---

## Support & Documentation

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration and setup
- Check `listener.log` for detailed logs
- Review code comments in `listener_service.py` and `models.py`

---

## Version Info

- Backend Version: 2.0.0
- Database: SQLite with SQLAlchemy ORM
- Python: 3.8+
- Last Updated: 2026-01-10
