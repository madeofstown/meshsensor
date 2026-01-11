# Backend Migration Guide

This guide explains how to migrate from the old JSON-based backend to the new SQLite database backend.

## Overview

The new backend provides:
- ✅ **SQLite Database**: Persistent, scalable storage
- ✅ **SQLAlchemy ORM**: Type-safe database operations
- ✅ **Comprehensive Logging**: File and console logging with rotation
- ✅ **Automatic Data Retention**: Configurable data cleanup (default: 30 days)
- ✅ **Robust Error Handling**: Graceful degradation and reconnection
- ✅ **Enhanced API**: Filtering, pagination, and query capabilities
- ✅ **Auto-migration**: Existing JSON data is automatically converted

## Prerequisites

```bash
pip install -r new_requirements.txt
```

Key new packages:
- `SQLAlchemy==2.0.23`: ORM for database operations
- `alembic==1.13.1`: Database migrations (optional for future use)

## Migration Steps

### 1. Backup Your Data

```bash
# Backup existing JSON database
cp sensorDB.json sensorDB.json.backup
```

### 2. Update Configuration

Copy `sample.config.json` to `config.json` and update with your settings:

```bash
cp sample.config.json config.json
```

Then edit `config.json`:

```json
{
  "radio_host": "127.0.0.1",
  "node_ids": [305441741, "!1234abcd"],
  "db_file": "sensorDB.db",
  "channel_index": 1,
  "data_retention_days": 30
}
```

**Configuration fields:**
- `radio_host`: IP address of Meshtastic node (see [sample.config.json](sample.config.json))
- `node_ids`: List of node IDs to monitor (see [sample.config.json](sample.config.json))
- `db_file`: Database file location (default: `sensorDB.db`)
- `channel_index`: Meshtastic channel to use (default: 1)
- `data_retention_days`: Keep data for this many days (default: 30)

### 3. First Run - Automatic Migration

```bash
python listener_service.py
```

On startup, the new backend will:
1. Create SQLite database if needed
2. Initialize schema
3. Automatically migrate data from `sensorDB.json` if it exists
4. Log migration progress

**Example output:**
```
2026-01-10 15:30:00 - [root] - INFO - Configuration loaded from config.json
2026-01-10 15:30:00 - [root] - INFO - RADIO_HOST: 10.7.0.97
2026-01-10 15:30:00 - [root] - INFO - NODE_IDS: ['!20b1663e', '!bb788268', '!718b5394']
2026-01-10 15:30:00 - [root] - INFO - Data retention: 30 days
2026-01-10 15:30:00 - [root] - INFO - Database initialized successfully
2026-01-10 15:30:00 - [root] - INFO - Successfully migrated 1542 telemetry records from JSON
2026-01-10 15:30:00 - [root] - INFO - Connecting to Meshtastic at 10.7.0.97...
2026-01-10 15:30:01 - [root] - INFO - Successfully connected to Meshtastic node
```

### 4. Verify Migration

Check the logs for success:

```bash
tail -f listener.log
```

Or query the database:

```bash
curl http://localhost:5001/api/stats
```

Sample response:
```json
{
  "nodes": 3,
  "telemetry_records": 1542,
  "oldest_record": "2025-12-10T10:00:00",
  "newest_record": "2026-01-10T15:30:00"
}
```

### 5. Update Frontend (if needed)

The new backend maintains a legacy `/data` endpoint for backward compatibility, but it's recommended to update the frontend to use new API endpoints for better performance:

**Old approach (loads all data):**
```javascript
fetch('http://localhost:5001/data')
```

**New approach (paginated, filtered):**
```javascript
// Get latest from all nodes
fetch('http://localhost:5001/api/telemetry/latest')

// Get paginated data from specific node
fetch('http://localhost:5001/api/nodes/!20b1663e/telemetry?limit=100&offset=0')

// Query with date range
fetch('http://localhost:5001/api/telemetry?start=2026-01-01T00:00:00Z&end=2026-01-10T00:00:00Z')
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for full endpoint reference.

---

## Database Structure

### SQLite File Location
By default: `sensorDB.db` in the application directory

### Accessing SQLite Data

#### Using SQLite CLI
```bash
# Install sqlite3 (usually pre-installed)
sqlite3 sensorDB.db

# Common queries
.tables                                    # List tables
.schema nodes                             # Show table structure
SELECT COUNT(*) FROM telemetry;           # Count records
SELECT * FROM nodes;                      # List all nodes
```

#### Using Python
```python
from database import DatabaseManager
from models import Node, Telemetry

db = DatabaseManager("sqlite:///sensorDB.db")
session = db.get_session()

# Get all nodes
nodes = session.query(Node).all()
for node in nodes:
    print(f"{node.long_name}: {len(node.telemetry)} records")

# Get recent data (last 24 hours)
from datetime import datetime, timedelta
recent = session.query(Telemetry).filter(
    Telemetry.timestamp > datetime.utcnow() - timedelta(days=1)
).all()
print(f"Last 24 hours: {len(recent)} records")
```

---

## Configuration Options

### `data_retention_days`

Controls how long telemetry data is kept before automatic deletion.

```json
{
  "data_retention_days": 30  // Keep 30 days of data (default)
}
```

**Cleanup behavior:**
- Runs automatically every hour
- Deletes records older than specified days
- Only affects telemetry data, not node definitions
- Configurable per deployment

**Examples:**
```json
{
  "data_retention_days": 7     // Keep 1 week
}
{
  "data_retention_days": 365   // Keep 1 year
}
{
  "data_retention_days": 3650  // Keep 10 years
}
```

---

## Troubleshooting

### Issue: "Failed to connect to Meshtastic"

**Symptom:** Connection errors in logs

**Solution:**
1. Verify radio IP in config: `radio_host`
2. Check that Meshtastic TCP server is running
3. Verify network connectivity: `ping 10.7.0.97`
4. Check firewall rules

### Issue: "Old data not migrated"

**Symptom:** Migrating from JSON but `sensorDB.json` not found

**Solution:**
- Migration is optional; if file doesn't exist, new DB starts empty
- If you have a backup, restore it: `cp sensorDB.json.backup sensorDB.json`
- Restart listener service to trigger migration

### Issue: Database locked errors

**Symptom:** SQLite "database is locked" errors in logs

**Solution:**
- Close any other applications accessing the database
- Ensure only one listener service instance is running
- Check file permissions on `sensorDB.db`

### Issue: Out of disk space

**Symptom:** Database writes failing

**Solution:**
- Reduce `data_retention_days` to delete old records faster
- Or manually prune:
  ```python
  from db_migration import DatabaseMigration
  from database import DatabaseManager
  
  db = DatabaseManager("sqlite:///sensorDB.db")
  migration = DatabaseMigration(db)
  migration.prune_old_data(days=7)  # Keep only 7 days
  ```

---

## Performance Considerations

### Database Indexes

The database includes indexes on frequently queried fields:
- `node_id` (single)
- `timestamp` (single)
- `(node_id, timestamp)` (composite)

These speed up filtering by node and time range.

### Query Tips

For best performance:

```python
# ✅ Fast: Uses index
query.filter(Telemetry.node_id == "!20b1663e")

# ✅ Fast: Uses index range
query.filter(Telemetry.timestamp.between(start, end))

# ⚠️ Slower: Full table scan
query.filter(Telemetry.temperature > 70)
```

### Database Size

Typical storage usage:
- Each telemetry record: ~200-300 bytes
- 1000 records/day per node = ~300 KB/day
- 30-day retention for 3 nodes = ~27 MB

---

## Upgrading from Older Versions

If you're upgrading from very old versions:

1. Backup current data: `cp sensorDB.json sensorDB.json.backup`
2. Update all source files
3. Install new dependencies: `pip install -r new_requirements.txt`
4. Run migration: `python listener_service.py`

The migration is idempotent (safe to run multiple times).

---

## Next Steps

- Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference
- Consider adding authentication for production
- Set up automated backups of `sensorDB.db`
- Monitor `listener.log` for health issues
