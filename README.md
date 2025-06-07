# MeshSensor Telemetry System

MeshSensor is used to collect and visualize environmental metrics from nodes in a Meshtastic network. It includes a Flask-based web dashboard, a listener service for telemetry data, and a database for storing sensor readings.


## Installation

### Prerequisites

- Python 3.8 or higher
- Meshtastic-compatible hardware
- A running Meshtastic TCP server

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/meshsensor.git
   cd meshsensor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the system:
   - Copy `sample.config.json` to `config.json`:
     ```bash
     cp sample.config.json config.json
     ```
   - Edit `config.json` to set your `radio_host`, `node_ids`, and other parameters.

4. Run the system:
   ```bash
   python main.py
   ```

## Usage

### Web Dashboard

Access the dashboard at `http://localhost:5000`. Features include:
- **Latest readings**: View the most recent metrics from all nodes.
- **Node details**: Click on a node to see detailed charts of its telemetry data.
- **Request telemetry**: Trigger a telemetry update from all nodes.

### Listener Service

The listener service runs in the background, collecting telemetry data from the mesh network and storing it in `sensorDB.json`.

### Configuration

Modify `config.json` to customize the system:
```json
{
  "radio_host": "127.0.0.1",
  "node_ids": [305441741, "!1234abcd"],
  "db_file": "sensorDB.json",
  "channel_index": 1
}
```

### Database

Telemetry data is stored in `sensorDB.json`. The database includes:
- Node information (ID, name, telemetry data)
- Environmental metrics (temperature, humidity, etc.)

## Development

### File Structure

- `app.py`: Flask web application for the dashboard.
- `listener_service.py`: Background service for collecting telemetry data.
- `shared_functions.py`: Utility functions for processing telemetry.
- `data_modules.py`: Data models for nodes and telemetry.
- `templates/`: HTML templates for the web dashboard.
- `static/`: Static assets (echarts.min.js).

## License

This project is licensed under the [Unlicense](LICENSE).

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss changes.

## Acknowledgments

- [Meshtastic](https://meshtastic.org): Open-source mesh network platform.
- [Flask](https://flask.palletsprojects.com): Python web framework.
- [ECharts](https://echarts.apache.org): Charting library for data visualization.

---
Feel free to reach out if you have any questions or suggestions!
