# Installation & Deployment Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Access to Meshtastic radio (TCP interface)
- ~100 MB disk space for database

## Step-by-Step Installation

### 1. Prepare Environment

```bash
# Navigate to project directory
cd meshsensor

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r new_requirements.txt

# Verify installation
python3 -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
```

**Expected output:**
```
SQLAlchemy: 2.0.23
```

### 3. Configure Application

Edit `config.json`:

```json
{
  "radio_host": "10.7.0.97",                    // Your Meshtastic radio IP
  "node_ids": ["!20b1663e", "!bb788268"],       // Nodes to monitor
  "db_file": "sensorDB.db",                     // SQLite database
  "channel_index": 1,                           // Mesh channel
  "data_retention_days": 30                     // Data retention policy
}
```

**Configuration Guide:**

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `radio_host` | string | `10.7.0.97` | IP or hostname of Meshtastic TCP server |
| `node_ids` | array | `["!abc123", "!def456"]` | Node IDs to monitor (can be hex or numeric) |
| `db_file` | string | `sensorDB.db` | SQLite database filename |
| `channel_index` | integer | `1` | Meshtastic channel for requests |
| `data_retention_days` | integer | `30` | Days of data to keep (old data auto-deleted) |

### 4. Migrate Existing Data (if applicable)

If upgrading from the old JSON-based system:

```bash
# The system will automatically detect and migrate sensorDB.json
# Just start the service - migration runs automatically on first run
python listener_service.py
```

You'll see in the logs:
```
INFO - Successfully migrated 1542 telemetry records from JSON
```

### 5. Start the Application

**Option A: Run both services together (Recommended)**
```bash
python main.py
```

This will start:
- Listener service (backend API on port 5001)
- Dashboard (frontend on port 5000)

**Option B: Run services separately**

Terminal 1 (Backend):
```bash
python listener_service.py
```

Terminal 2 (Frontend):
```bash
python app.py
```

### 6. Verify Installation

**Check service health:**
```bash
# Health check
curl http://localhost:5001/health

# Should return:
# {"status":"healthy","timestamp":"...","radio_connected":true}
```

**Check database:**
```bash
# Get statistics
curl http://localhost:5001/api/stats

# Should return node count and telemetry records
```

**Access dashboard:**
Open browser to: http://localhost:5000

---

## Upgrading from Version 1.0

### If You Have Existing JSON Data

1. **Backup your data:**
   ```bash
   cp sensorDB.json sensorDB.json.backup
   ```

2. **Install new requirements:**
   ```bash
   pip install -r new_requirements.txt
   ```

3. **Update configuration:**
   ```json
   {
     "db_file": "sensorDB.db",           // Changed from sensorDB.json
     "data_retention_days": 30           // New field
   }
   ```

4. **First run (auto-migration):**
   ```bash
   python main.py
   ```

5. **Verify migration:**
   ```bash
   curl http://localhost:5001/api/stats
   sqlite3 sensorDB.db "SELECT COUNT(*) FROM telemetry;"
   ```

---

## Database Management

### Inspect Database

```bash
# Open SQLite shell
sqlite3 sensorDB.db

# Useful commands
.tables                              # List tables
.schema nodes                        # Show nodes table structure
.schema telemetry                    # Show telemetry table structure
SELECT COUNT(*) FROM telemetry;      # Count records
SELECT * FROM nodes;                 # List all nodes
```

### Backup Database

```bash
# Single backup
cp sensorDB.db sensorDB.db.backup

# Timestamped backup
cp sensorDB.db sensorDB.db.backup.$(date +%Y%m%d_%H%M%S)

# Scheduled backup (cron)
# Add to crontab: 0 2 * * * cp /path/to/sensorDB.db /backup/sensorDB.db.$(date +\%Y\%m\%d)
```

### Clean Old Data Manually

```python
from database import DatabaseManager
from db_migration import DatabaseMigration

db = DatabaseManager("sqlite:///sensorDB.db")
migration = DatabaseMigration(db)

# Delete data older than 7 days
deleted = migration.prune_old_data(days=7)
print(f"Deleted {deleted} records")
```

---

## Production Deployment

### Using Systemd (Linux)

Create `/etc/systemd/system/meshsensor.service`:

```ini
[Unit]
Description=MeshSensor Backend
After=network.target

[Service]
Type=simple
User=meshsensor
WorkingDirectory=/opt/meshsensor
ExecStart=/opt/meshsensor/.venv/bin/python /opt/meshsensor/listener_service.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl start meshsensor
sudo systemctl enable meshsensor
sudo systemctl status meshsensor
```

Monitor logs:
```bash
sudo journalctl -u meshsensor -f
```

### Using Docker (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY new_requirements.txt .
RUN pip install --no-cache-dir -r new_requirements.txt

COPY . .

EXPOSE 5000 5001

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t meshsensor .
docker run -d -p 5000:5000 -p 5001:5001 -v /opt/meshsensor/data:/app --name meshsensor meshsensor
```

### Using Gunicorn (WSGI)

For production, use a proper WSGI server:

```bash
pip install gunicorn

# Run Flask app with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

Then run listener service in separate process:
```bash
python listener_service.py
```

---

## Monitoring & Logging

### Log Files

Location: `listener.log` (in application directory)

**Monitor in real-time:**
```bash
tail -f listener.log
```

**View recent errors:**
```bash
tail -f listener.log | grep ERROR
```

**Count events:**
```bash
grep "Stored telemetry" listener.log | wc -l
```

### Check Service Status

```bash
# All services
curl http://localhost:5001/health | jq

# Database stats
curl http://localhost:5001/api/stats | jq

# Active nodes
curl http://localhost:5001/api/nodes | jq

# Latest readings
curl http://localhost:5001/api/telemetry/latest | jq
```

### Performance Monitoring

```bash
# Database size
ls -lh sensorDB.db

# Disk usage
df -h /

# Memory usage
ps aux | grep listener_service.py

# Network connections
netstat -tuln | grep 500[01]
```

---

## Troubleshooting

### Issue: "No module named 'sqlalchemy'"

**Solution:**
```bash
pip install -r new_requirements.txt
```

### Issue: "Connection refused" to Meshtastic

**Solution:**
1. Verify radio IP: `ping 10.7.0.97`
2. Check TCP interface running: `netstat -tuln | grep :4403`
3. Update config: `radio_host: "10.7.0.97"`

### Issue: "Database is locked"

**Solution:**
- Close any other database connections
- Ensure only one listener process running: `ps aux | grep listener`
- Check file permissions: `ls -l sensorDB.db`

### Issue: Slow API responses

**Solution:**
1. Check database size: `ls -lh sensorDB.db`
2. Prune old data: Reduce `data_retention_days`
3. Add indexes: Already included in models
4. Use pagination: Limit query results to 100-500

### Issue: No data appearing

**Solution:**
1. Check radio connection: `curl http://localhost:5001/health`
2. Verify node IDs: `echo $NODE_IDS` from config
3. Request fresh data: `curl -X POST http://localhost:5001/api/telemetry/request`
4. Check logs: `tail -f listener.log`

---

## Common Operations

### Check Database Stats
```bash
curl http://localhost:5001/api/stats | jq '.telemetry_records'
```

### Get Latest from One Node
```bash
curl "http://localhost:5001/api/nodes/!20b1663e/telemetry?limit=1"
```

### Export Last 7 Days (via Python)
```python
import json
import requests
from datetime import datetime, timedelta

end = datetime.utcnow()
start = end - timedelta(days=7)

response = requests.get(
    'http://localhost:5001/api/telemetry',
    params={
        'start': start.isoformat() + 'Z',
        'end': end.isoformat() + 'Z',
        'limit': 10000
    }
)

data = response.json()
with open('telemetry_export.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### Restart Services
```bash
# If using main.py
pkill -f "python main.py"
python main.py

# If using systemd
sudo systemctl restart meshsensor
```

---

## Performance Tuning

### Increase Data Retention
```json
{
  "data_retention_days": 365
}
```
(Note: Increases disk usage)

### Decrease Retention to Save Space
```json
{
  "data_retention_days": 7
}
```

### Enable Debug Logging
In `listener_service.py`, change:
```python
console_handler.setLevel(logging.DEBUG)  # More verbose output
```

### Batch API Requests
Instead of many single requests, use query endpoints:
```bash
# Get 1000 records at once
curl "http://localhost:5001/api/telemetry?limit=1000"
```

---

## Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install -r new_requirements.txt`
- [ ] config.json updated with radio host
- [ ] config.json updated with node IDs
- [ ] Database created: `ls -l sensorDB.db`
- [ ] Health check passes: `curl http://localhost:5001/health`
- [ ] Dashboard accessible: http://localhost:5000
- [ ] Telemetry data flowing: `curl http://localhost:5001/api/telemetry/latest`
- [ ] Logs show activity: `tail -f listener.log`
- [ ] No errors in logs

---

## Support & Documentation

- **API Reference:** See `API_DOCUMENTATION.md`
- **Migration Details:** See `MIGRATION_GUIDE.md`
- **Architecture:** See `BACKEND_REFACTOR.md`
- **Quick Answers:** See `QUICK_REFERENCE.md`
- **Application Logs:** Check `listener.log`

---

## Getting Help

1. **Check logs first:** `tail -f listener.log`
2. **Review documentation:** See documentation files above
3. **Test endpoints:** Use curl to test API
4. **Inspect database:** Use SQLite CLI
5. **Check configuration:** Verify config.json settings

---

**Installation Complete!** 🎉

Your MeshSensor backend is ready to use. Access the dashboard at http://localhost:5000
