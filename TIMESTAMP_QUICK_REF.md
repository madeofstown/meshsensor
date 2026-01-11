# Quick Timestamp Reference

## Cheat Sheet

### Backend (listener_service.py / models.py)
- **Receives:** Unix timestamp from Meshtastic radio
- **Stores:** `datetime` object in SQLite
- **Sends:** Unix integer via `to_dict()`

```python
# In models.py to_dict()
"timestamp": int(self.timestamp.timestamp())
```

### Frontend (app.py)
- **Receives:** Unix integer from `/data` endpoint
- **Parses:** Extract from `"timestamp"` or `"time"` field
- **Converts:** `unix_to_local()` → human readable
- **Displays:** "2026-01-10 15:30:00" in templates

```python
# Parse: Extract Unix timestamp from telemetry
ts = tel.get("timestamp") or tel.get("time")

# Convert: Show human-readable time
display_time = unix_to_local(ts)
```

## API Response Examples

### GET /api/telemetry/latest
```json
{
  "timestamp": 1736520600,
  "environmentMetrics": {"temperature": 22.5}
}
```

### GET /latest-data
```json
{
  "lastSeen": {
    "Node A": "2026-01-10 15:30:00"
  }
}
```

### GET /latest-chart-data
```json
{
  "temperature": {
    "Node A": [[1736520600, 22.5], [1736521200, 22.3]]
  }
}
```

## Common Tasks

### Add New Route with Timestamps
```python
@app.route('/my-endpoint')
def my_endpoint():
    data = fetch_sensor_data()
    
    def parse_timestamp(tel):
        ts = tel.get("timestamp") or tel.get("time")
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        return datetime.utcnow()
    
    for node in data.get("nodes", []):
        for telemetry in node.get("telemetry", []):
            ts_obj = parse_timestamp(telemetry)
            ts_str = unix_to_local(ts_obj.timestamp())
            # Use ts_str for display, ts_obj for calculations
```

### Convert Timestamp in Template
```html
<!-- In Jinja2 template -->
<p>Last seen: {{ last_seen['Node A'] }}</p>
<!-- Already converted by unix_to_local() in app.py -->
```

### Chart Data Points
```python
# Backend sends (already Unix timestamps)
[[1736520600, 22.5], [1736521200, 22.3]]

# Chart library displays automatically
# X-axis shows "Jan 10, 3:30 PM" etc.
```

## Error Handling

### Handle Missing Timestamp
```python
ts = tel.get("timestamp") or tel.get("time")
if not ts:
    ts = datetime.utcnow().timestamp()
```

### Handle Invalid Timestamp
```python
try:
    display = unix_to_local(ts)
except:
    display = "Invalid"
```

## Database Details

| Aspect | SQLite Column | API Response | Frontend Display |
|--------|---------------|--------------|-----------------|
| Type | `DateTime` | `int` | `str` |
| Example | `2026-01-10 15:30:00` | `1736520600` | `"2026-01-10 15:30:00"` |
| Why | Query efficiency | Standard API | User readable |

## Debugging

### Check Backend Response
```bash
curl http://localhost:5001/api/telemetry/latest | python -m json.tool | grep timestamp
```

### Verify Conversion
```bash
python -c "from datetime import datetime; print(datetime.fromtimestamp(1736520600))"
```

### Test Frontend Route
```bash
curl http://localhost:5000/latest-data
# Check "lastSeen" is human-readable strings
```

## Summary

- **Backend**: Returns Unix integers
- **Frontend**: Converts to local time strings
- **Charts**: Use Unix timestamps natively
- **Display**: Human-readable "YYYY-MM-DD HH:MM:SS" format
