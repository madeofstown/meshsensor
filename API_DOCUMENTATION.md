# MeshSensor Backend API Documentation

## Overview

The MeshSensor listener service provides a robust REST API for accessing telemetry data from Meshtastic nodes. The backend uses SQLite with SQLAlchemy ORM for reliable data storage and includes automatic data retention policies.

## Base URL

```
http://localhost:5001
```

## Authentication

Currently, no authentication is required. Consider adding authentication in production environments.

---

## Endpoints

### Health & Status

#### GET `/health`
Check if the listener service is running and radio connection status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-10T15:30:45.123456",
  "radio_connected": true
}
```

#### GET `/api/stats`
Get database statistics.

**Response (200 OK):**
```json
{
  "nodes": 3,
  "telemetry_records": 1542,
  "oldest_record": "2026-01-01T10:00:00",
  "newest_record": "2026-01-10T15:30:00"
}
```

---

### Nodes

#### GET `/api/nodes`
Get list of all nodes in the network.

**Response (200 OK):**
```json
{
  "nodes": [
    {
      "id": 1,
      "nodeID": "!20b1663e",
      "longName": "Front Porch Sensor",
      "shortName": "Porch"
    },
    {
      "id": 2,
      "nodeID": "!bb788268",
      "longName": "Garage Sensor",
      "shortName": "Garage"
    }
  ]
}
```

---

### Telemetry Data

#### GET `/api/nodes/<node_id>/telemetry`
Get telemetry history for a specific node with pagination.

**Parameters:**
- `node_id` (path): The node ID (e.g., `!20b1663e`)
- `limit` (query, default: 100, max: 1000): Number of records to return
- `offset` (query, default: 0): Pagination offset

**Example:**
```
GET /api/nodes/!20b1663e/telemetry?limit=50&offset=0
```

**Response (200 OK):**
```json
{
  "node": {
    "id": 1,
    "nodeID": "!20b1663e",
    "longName": "Front Porch Sensor",
    "shortName": "Porch"
  },
  "telemetry": [
    {
      "id": 100,
      "nodeID": "!20b1663e",
      "timestamp": "2026-01-10T15:30:00",
      "environmentMetrics": {
        "temperature": 72.5,
        "relativeHumidity": 45.2,
        "barometricPressure": 1013.25,
        "iaq": 50,
        "iaqAccuracy": 3
      },
      "voltage": 4.15,
      "current": 0.05
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 523
  }
}
```

**Errors:**
- `404 Not Found`: Node does not exist
- `400 Bad Request`: Invalid query parameters

---

#### GET `/api/telemetry/latest`
Get the most recent telemetry reading from all nodes.

**Response (200 OK):**
```json
{
  "data": [
    {
      "node": {
        "id": 1,
        "nodeID": "!20b1663e",
        "longName": "Front Porch Sensor",
        "shortName": "Porch"
      },
      "latest": {
        "id": 523,
        "nodeID": "!20b1663e",
        "timestamp": "2026-01-10T15:30:00",
        "environmentMetrics": {
          "temperature": 72.5,
          "relativeHumidity": 45.2,
          "barometricPressure": 1013.25,
          "iaq": 50,
          "iaqAccuracy": 3
        },
        "voltage": 4.15,
        "current": 0.05
      }
    }
  ]
}
```

---

#### GET `/api/telemetry`
Query telemetry data with filters (date range, node, pagination).

**Parameters:**
- `start` (query, optional): Start timestamp (ISO 8601 format, e.g., `2026-01-01T00:00:00Z`)
- `end` (query, optional): End timestamp (ISO 8601 format)
- `node_id` (query, optional): Filter by node ID
- `limit` (query, default: 100, max: 1000): Number of records
- `offset` (query, default: 0): Pagination offset

**Examples:**
```
# Get last 100 records from a specific node
GET /api/telemetry?node_id=!20b1663e&limit=100

# Get data from last 7 days
GET /api/telemetry?start=2026-01-03T00:00:00Z&end=2026-01-10T00:00:00Z

# Pagination through all data from a node
GET /api/telemetry?node_id=!20b1663e&limit=500&offset=500
```

**Response (200 OK):**
```json
{
  "telemetry": [
    {
      "id": 523,
      "nodeID": "!20b1663e",
      "timestamp": "2026-01-10T15:30:00",
      "environmentMetrics": {
        "temperature": 72.5,
        "relativeHumidity": 45.2,
        "barometricPressure": 1013.25,
        "iaq": 50,
        "iaqAccuracy": 3
      },
      "voltage": 4.15,
      "current": 0.05
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total": 1542
  }
}
```

**Errors:**
- `400 Bad Request`: Invalid timestamp format or query parameters

---

### Telemetry Requests

#### POST `/api/telemetry/request`
Trigger fresh telemetry request from all configured nodes.

**Request:**
```bash
curl -X POST http://localhost:5001/api/telemetry/request
```

**Response (202 Accepted):**
```json
{
  "status": "ok",
  "message": "Telemetry request initiated"
}
```

The telemetry request is processed asynchronously. Responses will be received within a few seconds if nodes are online.

---

### Legacy Endpoints

#### GET `/data`
Legacy endpoint for backward compatibility with the old frontend.

Provides data in the original JSON format expected by existing frontend code.

**Response (200 OK):**
```json
{
  "nodes": [
    {
      "nodeID": "!20b1663e",
      "longName": "Front Porch Sensor",
      "shortName": "Porch",
      "telemetry": [...]
    }
  ]
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Human-readable error message"
}
```

### Common Status Codes
- `200 OK`: Successful request
- `202 Accepted`: Request accepted but not yet processed
- `400 Bad Request`: Invalid parameters or malformed request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Data Format

### Timestamp Format
All timestamps are in ISO 8601 format with UTC timezone:
- Format: `YYYY-MM-DDTHH:MM:SS` or `YYYY-MM-DDTHH:MM:SSZ`
- Example: `2026-01-10T15:30:45.123456Z`

### Telemetry Metrics
Environmental metrics that may be present in responses:
- `temperature`: Temperature in Fahrenheit (float)
- `relativeHumidity`: Relative humidity percentage (float, 0-100)
- `barometricPressure`: Atmospheric pressure in hPa (float)
- `iaq`: Indoor Air Quality index (int, 0-500)
- `iaqAccuracy`: IAQ accuracy level (int, 0-3)

---

## Rate Limiting

Currently, no rate limiting is enforced. For production use, consider implementing rate limiting.

---

## Configuration

The listener service is configured via `config.json`:

```json
{
  "radio_host": "10.7.0.97",
  "node_ids": ["!20b1663e", "!bb788268"],
  "db_file": "sensorDB.db",
  "channel_index": 1,
  "data_retention_days": 30
}
```

- `radio_host`: IP/hostname of Meshtastic TCP interface
- `node_ids`: List of node IDs to monitor
- `db_file`: SQLite database file path
- `channel_index`: Meshtastic channel to use
- `data_retention_days`: How many days of data to keep (older records are auto-deleted)

---

## Database

### Storage
- **Type**: SQLite (file-based) by default
- **Location**: `sensorDB.db` (configurable)
- **Auto-migration**: Old JSON data is automatically migrated on first run

### Tables

#### `nodes`
```
- id: Integer primary key
- node_id: Unique node identifier string
- long_name: Full node name
- short_name: Short node name
- created_at: Timestamp when node was first seen
- last_seen: Timestamp of last telemetry
```

#### `telemetry`
```
- id: Integer primary key
- node_id: Foreign key to nodes.node_id
- timestamp: UTC timestamp of reading
- temperature: Fahrenheit (float)
- relative_humidity: Percentage (float)
- barometric_pressure: hPa (float)
- iaq: IAQ index (float)
- iaq_accuracy: IAQ accuracy level (integer)
- voltage: Supply voltage (float)
- current: Current draw (float)
- created_at: Database insertion timestamp
- raw_packet: Original packet (for debugging)
```

### Data Retention
Data older than `data_retention_days` (default: 30) is automatically deleted every hour.

---

## Logging

The listener service maintains detailed logs:

- **Console**: INFO level and above
- **File**: `listener.log` (DEBUG level and above)
  - Rotating file handler: 5MB max per file, keeps 5 backups
  - Located in the application directory

---

## Future Enhancements

- [ ] Authentication/authorization
- [ ] Rate limiting
- [ ] WebSocket support for real-time updates
- [ ] Data aggregation endpoints (hourly/daily averages)
- [ ] Export to CSV/Parquet
- [ ] Multi-user support
- [ ] MariaDB/MySQL backend support
