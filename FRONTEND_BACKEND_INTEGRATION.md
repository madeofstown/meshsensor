# Frontend-Backend Integration Guide

## Overview

The backend (listener service) returns Unix timestamps in all API responses. The frontend (Flask dashboard in `app.py`) automatically converts these timestamps to local time for display.

## Key Integration Changes

### 1. Timestamp Format

**Backend Format:** Unix timestamps (integers, seconds since epoch)
```json
{
  "timestamp": 1736520600,
  "time": 1736520600
}
```

**Frontend Display:** Local time strings
```
2026-01-10 15:30:00
```

**Conversion Function:**
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

This is used automatically in:
- Dashboard last_seen times
- Node detail view timestamps
- Latest data endpoint
- Chart data processing

### 2. API Endpoints

**Frontend uses these backend endpoints:**

| Endpoint | Use | Format |
|----------|-----|--------|
| `GET /data` | Legacy format for dashboard | JSON with nodes array |
| `GET /health` | Health checks | JSON with status |
| `GET /api/nodes` | Node listing | JSON array |
| `GET /api/telemetry/latest` | Latest readings | JSON with data array |
| `POST /api/telemetry/request` | Request fresh data | JSON response |

### 2. API Response Format

All backend API endpoints return Unix timestamps:

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

The frontend's `parse_timestamp()` function extracts the Unix timestamp and converts it using `unix_to_local()` for display.

## Architecture

### Data Flow
```
Meshtastic Radio
        ↓
 listener_service.py (Backend)
  - Receives packets
  - Stores in SQLite database
  - Returns Unix timestamps in API
        ↓
 /data endpoint (legacy format)
        ↓
 app.py (Frontend)
  - Parses Unix timestamps
  - Converts to local time: unix_to_local()
  - Displays in templates
        ↓
 Browser displays: "2026-01-10 15:30:00"
```

### Timestamp Processing

**Backend:**
1. Receives Meshtastic packet with Unix timestamp
2. Stores in database as datetime object
3. Converts to Unix integer in `to_dict()`: `int(self.timestamp.timestamp())`
4. Returns via API endpoint

**Frontend:**
1. Receives JSON with Unix timestamp
2. `parse_timestamp()` extracts timestamp field
3. Uses datetime for sorting/calculations
4. `unix_to_local()` converts to readable string for display
5. Charts use raw Unix timestamps for x-axis values

## Implementation Details

### Start Both Services

**Option 1: Unified startup (recommended)**
```bash
python main.py
```
This starts both backend and frontend together.

**Option 2: Separate terminals**

Terminal 1 (Backend):
```bash
python listener_service.py
```

Terminal 2 (Frontend):
```bash
python app.py
```

### Verify Integration

Run the integration test:
```bash
python test_integration.py
```

This will verify:
- ✅ Backend is running and healthy
- ✅ API endpoints respond correctly
- ✅ Data format is correct
- ✅ Timestamps are properly formatted

### Access Dashboard

Open browser to: http://localhost:5000

## What the Frontend Does

### Routes and Their Functionality

#### `GET /` - Main Dashboard
- Displays live charts of temperature and humidity
- Shows latest readings from all nodes
- Features "Request Telemetry" button
- Updates every time page is accessed

#### `GET /nodes` - JSON Node List
- Returns list of all nodes with IDs
- Used by JavaScript for dynamic updates

#### `GET /node/<node_id>` - Node Detail Page
- Shows detailed historical data for specific node
- Displays all environmental metrics
- Supports string or integer node IDs

#### `POST /trigger` - Request Telemetry
- Sends request to backend to fetch fresh data
- Calls `/api/telemetry/request` endpoint
- Shows success/error messages

#### `GET /latest-data` - JSON Latest Metrics
- Returns JSON with latest reading from each node
- Includes last seen timestamps
- Used by JavaScript for real-time updates

#### `GET /latest-chart-data` - JSON Chart Points
- Returns latest single data point per node per metric
- Format: `{metric: {node: [[timestamp, value]]}}`
- Used for chart updates

## Error Handling

### Timestamp Conversion
- If timestamp is None: returns "Never"
- If timestamp is invalid: returns "Invalid"
- Frontend gracefully handles missing timestamps
- Never crashes on bad timestamp data

### Connection Errors
If backend is not running, frontend gracefully degrades:
- Returns empty datasets
- Logs errors to console
- Shows flash messages to user
- Continues to function

## Configuration

### LISTENER_URL
Set in `app.py`:
```python
LISTENER_URL = "http://localhost:5001"
REQUEST_TIMEOUT = 5
```

Change if backend runs on different host/port.

## Testing

### Quick Verification

```bash
# Check backend is running
curl http://localhost:5001/health

# Check frontend is running
curl http://localhost:5000/

# Check latest telemetry
curl http://localhost:5001/api/telemetry/latest
```

### Full Integration Test
```bash
python test_integration.py
```

Output shows:
- Backend health status
- Connected nodes
- Latest readings
- Database statistics

## Troubleshooting

### "Cannot connect to listener service"
- Check backend is running: `python listener_service.py`
- Verify LISTENER_URL in app.py
- Check firewall allows port 5001

### "No data appearing"
1. Verify backend has data: `curl http://localhost:5001/api/stats`
2. Check Meshtastic connection: `curl http://localhost:5001/health`
3. Request fresh telemetry: `curl -X POST http://localhost:5001/api/telemetry/request`
4. Wait a few seconds for data to arrive

### Dashboard shows "Never" for last_seen
- Data hasn't arrived yet
- Request telemetry with button
- Check logs: `tail -f listener.log`

### Charts don't display
- Check browser console for JavaScript errors
- Verify timestamp format with: `python test_integration.py`
- Try refreshing page

## Performance Considerations

### Frontend
- Dashboard page loads all telemetry for all nodes
- For large datasets, consider pagination in templates
- JavaScript rendering can be slow with 1000+ data points

### Backend
- `/data` endpoint sends all telemetry (consider pagination)
- Use `/api/telemetry` with filters for large queries
- Paginate with `limit` and `offset` parameters

## Future Improvements

1. **Real-time Updates**
   - WebSocket support
   - Server-sent events (SSE)
   - Live chart updates

2. **Performance**
   - Pagination in templates
   - Lazy loading of historical data
   - AJAX chart updates

3. **Features**
   - Date range selector
   - Node filtering
   - Export to CSV
   - Alert thresholds

4. **UI/UX**
   - Better error messages
   - Loading indicators
   - Responsive design
   - Dark mode

## Summary

✅ **Integration Status: Complete**

The frontend and backend are fully integrated and working together:
- ✅ Data flows from backend to frontend
- ✅ Timestamp formats handled correctly
- ✅ Legacy format support for backward compatibility
- ✅ All error cases handled gracefully
- ✅ Performance optimized for typical deployments

The system is ready for deployment and use!
