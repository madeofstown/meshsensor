# Timestamp Strategy - Backend Sends Unix, Frontend Converts

## Overview

The MeshSensor system now uses a clean, simple timestamp strategy:

- **Backend (listener_service.py):** Returns Unix timestamps (integer seconds since epoch)
- **Frontend (app.py):** Converts to local time for display
- **Database (SQLite):** Stores as datetime objects, converts on serialization

## Why This Approach?

✅ **Simple and Standard**
- Unix timestamps are the universal standard for APIs
- No format confusion or parsing complexity

✅ **Timezone Aware**
- Frontend automatically converts to user's local timezone
- No hardcoded UTC offsets

✅ **Efficient**
- Integer timestamps are fast to transmit
- Easy to work with in JavaScript charts

✅ **Backward Compatible**
- Both `timestamp` and `time` fields returned for compatibility
- Legacy code continues to work

## Implementation

### Backend Changes

**models.py - Telemetry.to_dict():**
```python
"timestamp": int(self.timestamp.timestamp()) if self.timestamp else None,
"time": int(self.timestamp.timestamp()) if self.timestamp else None,
```

Both fields return the same Unix timestamp for compatibility.

### Frontend Changes

**app.py - Conversion Function:**
```python
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
```

**app.py - Usage in Routes:**
- `dashboard()`: `last_seen[name] = unix_to_local(ts_unix)`
- `latest_data()`: `last_seen[name] = unix_to_local(ts_unix)`
- `node_detail()`: `ts_str = ts_obj.strftime("%Y-%m-%d %H:%M:%S")`
- `latest_chart_data()`: Uses `ts_unix` for x-axis values

## Data Flow Example

### 1. Backend Stores
```python
# Database stores datetime
2026-01-10 15:30:00 UTC

# to_dict() converts to Unix
1736520600
```

### 2. API Returns
```json
{
  "timestamp": 1736520600,
  "time": 1736520600,
  "environmentMetrics": {...}
}
```

### 3. Frontend Displays
```python
# unix_to_local converts to local time
datetime.fromtimestamp(1736520600)
# User's timezone, e.g.: 2026-01-10 10:30:00 (if EST)
```

### 4. Charts Use Raw Values
```python
# X-axis values are Unix timestamps
[[1736520600, 22.5], [1736521200, 22.3], ...]
# Chart library handles human-readable display
```

## API Response Format

### Telemetry Endpoint
```json
{
  "id": 1,
  "nodeID": "123456",
  "timestamp": 1736520600,
  "time": 1736520600,
  "environmentMetrics": {
    "temperature": 22.5,
    "relativeHumidity": 45.2,
    "barometricPressure": 1013.25,
    "iaq": 50,
    "iaqAccuracy": 3
  },
  "voltage": 4.2,
  "current": 0.15
}
```

### Latest Data Endpoint
```json
{
  "metrics": {
    "Node A": {
      "temperature": 22.5,
      "relativeHumidity": 45.2
    }
  },
  "lastSeen": {
    "Node A": "2026-01-10 15:30:00"
  },
  "lastTimestamps": {
    "Node A": 1736520600
  }
}
```

## Testing

### Quick Test
```bash
# Start backend
python listener_service.py

# In another terminal, test API
curl http://localhost:5001/api/telemetry/latest

# Check response has Unix timestamp
# Look for "timestamp": 1736520600
```

### Verify Conversion
```bash
python -c "from datetime import datetime; print(datetime.fromtimestamp(1736520600))"
# Output: 2026-01-10 15:30:00 (local timezone)
```

## Advantages Over Previous Approach

| Aspect | Previous (ISO 8601) | Current (Unix) |
|--------|-------------------|----------------|
| Format | `"2026-01-10T15:30:00Z"` | `1736520600` |
| Parsing | Complex (timezone aware) | Simple (integer) |
| Timezone | Fixed (UTC in string) | Dynamic (user's local) |
| Charts | Need special handling | Native support |
| Size | Larger (string) | Smaller (integer) |
| Standard | ISO 8601 | Unix epoch |

## Future Improvements

### 1. Millisecond Precision
If needed, use `int(self.timestamp.timestamp() * 1000)` for milliseconds.

### 2. Timezone Support
Add optional `?timezone=EST` parameter to convert on backend:
```python
if timezone_param:
    ts = self.timestamp.astimezone(timezone_obj)
```

### 3. Batch Conversion
For high-frequency data, send raw Unix timestamps and let frontend batch convert:
```python
# Single conversion for 1000 points instead of 1000 conversions
timestamps = [t[0] for t in data]
converted = [unix_to_local(t) for t in timestamps]
```

## Notes

- Always verify `timestamp` is not None before converting
- Use `datetime.fromtimestamp()` (local) not `datetime.utcfromtimestamp()` (UTC)
- Chart libraries (echarts, etc.) handle Unix timestamps natively
- Database continues to store datetime for query efficiency

## References

- [Unix Epoch](https://en.wikipedia.org/wiki/Unix_time)
- [Python datetime](https://docs.python.org/3/library/datetime.html)
- [JavaScript timestamp handling](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date)
