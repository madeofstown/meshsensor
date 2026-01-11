# Quick Reference Card

## Getting Started

### Installation (5 minutes)
```bash
pip install -r new_requirements.txt
python main.py
```

Dashboard: http://localhost:5000
API: http://localhost:5001

---

## Key Files

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy ORM models |
| `database.py` | Database connection & management |
| `db_migration.py` | Migration & data retention |
| `listener_service.py` | Main backend service |
| `app.py` | Web dashboard |
| `main.py` | Service orchestrator |
| `sensorDB.db` | SQLite database |
| `listener.log` | Application logs |

---

## Important API Endpoints

### Latest Data
```bash
curl http://localhost:5001/api/telemetry/latest
```

### Node History (paginated)
```bash
curl "http://localhost:5001/api/nodes/!20b1663e/telemetry?limit=100"
```

### Time Range Query
```bash
curl "http://localhost:5001/api/telemetry?start=2026-01-01T00:00:00Z&end=2026-01-10T00:00:00Z"
```

### Request Fresh Telemetry
```bash
curl -X POST http://localhost:5001/api/telemetry/request
```

### Health Check
```bash
curl http://localhost:5001/health
```

---

## Configuration (config.json)

```json
{
  "radio_host": "10.7.0.97",        // Meshtastic TCP server
  "node_ids": ["!20b1663e", ...],   // Nodes to monitor
  "db_file": "sensorDB.db",         // SQLite file
  "channel_index": 1,               // Mesh channel
  "data_retention_days": 30         // Days to keep data
}
```

---

## Logging

**Console (Real-time):**
```bash
tail -f listener.log
```

**File Location:** `listener.log`
- Max: 5MB per file
- Backups: 5 files kept
- Level: DEBUG and higher

---

## Database

### Inspect with SQLite CLI
```bash
sqlite3 sensorDB.db
sqlite> SELECT COUNT(*) FROM telemetry;
sqlite> SELECT * FROM nodes;
```

### Python Query
```python
from database import DatabaseManager
from models import Telemetry
from datetime import datetime, timedelta

db = DatabaseManager()
session = db.get_session()

# Recent data
recent = session.query(Telemetry).filter(
    Telemetry.timestamp > datetime.utcnow() - timedelta(hours=1)
).all()

session.close()
```

---

## Data Retention

Configured in `config.json`:
- Default: 30 days
- Auto-cleanup: Every hour
- Only affects telemetry, not nodes

Manual pruning:
```python
from database import DatabaseManager
from db_migration import DatabaseMigration

db = DatabaseManager()
migration = DatabaseMigration(db)
migration.prune_old_data(days=7)  # Keep only 7 days
```

---

## Troubleshooting

### Service Won't Start
1. Check `listener.log` for errors
2. Verify radio_host is reachable: `ping 10.7.0.97`
3. Ensure dependencies installed: `pip install -r new_requirements.txt`

### No Data Appearing
1. Check radio connection: `curl http://localhost:5001/health`
2. Verify node IDs in config
3. Request fresh data: `curl -X POST http://localhost:5001/api/telemetry/request`

### Database Issues
1. Check file permissions: `ls -l sensorDB.db`
2. Verify disk space: `df -h`
3. Check for locks: Only one listener instance should run

---

## Useful Commands

### Database Statistics
```bash
curl http://localhost:5001/api/stats | jq
```

### List All Nodes
```bash
curl http://localhost:5001/api/nodes | jq
```

### Watch Logs (real-time)
```bash
tail -f listener.log | grep -E "ERROR|INFO"
```

### Database Size
```bash
ls -lh sensorDB.db
```

### Backup Database
```bash
cp sensorDB.db sensorDB.db.backup.$(date +%s)
```

---

## Documentation Files

- **API_DOCUMENTATION.md** - Complete REST API reference
- **MIGRATION_GUIDE.md** - Detailed migration instructions
- **BACKEND_REFACTOR.md** - Architecture and overview
- **REFACTOR_SUMMARY.md** - Implementation summary

---

## Performance Tips

1. **Use Pagination:**
   - Limit requests to 100-500 records
   - Use offset for browsing

2. **Filter by Node:**
   - Query single node instead of all
   - Faster responses

3. **Time-based Queries:**
   - Use start/end filters
   - Reduces database load

4. **Data Retention:**
   - Set appropriate retention_days
   - Prevents disk fill-up

---

## Production Checklist

- [ ] Update `radio_host` in config
- [ ] Set correct `node_ids`
- [ ] Set appropriate `data_retention_days`
- [ ] Monitor `listener.log`
- [ ] Set up automated backups
- [ ] Test all endpoints
- [ ] Verify telemetry flowing in
- [ ] Plan for database growth
- [ ] Consider authentication
- [ ] Set up monitoring/alerts

---

## Support

For detailed information, see:
- API_DOCUMENTATION.md (endpoints & examples)
- MIGRATION_GUIDE.md (setup & troubleshooting)
- listener.log (detailed logs)
- Code comments (implementation details)

---

Last Updated: 2026-01-10
Version: 2.0.0
