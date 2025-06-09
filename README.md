# MeshSensor

MeshSensor collects and visualizes environmental telemetry data from nodes in a Meshtastic network. It includes:

- A **Flask-based web dashboard** to view live sensor data and charts.
- A **listener service** that interfaces with a Meshtastic node via TCP, receives and stores environment metrics from a list of configured nodes, and serves that data to the web dashboard. 

![meshsensor_screenshot](https://github.com/user-attachments/assets/421efcd2-bdc7-4ca1-8790-82f8e9e54dcc)

---

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Meshtastic-compatible hardware
- A running Meshtastic TCP server

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/madeofstown/meshsensor.git
   cd meshsensor
   ```

2. **Create a Python virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   ```bash
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration:**
   - Copy and customize the sample config:
     ```bash
     cp sample.config.json config.json
     ```
   - Edit `config.json`:
     ```json
     {
       "radio_host": "127.0.0.1",
       "node_ids": [305441741, "!1234abcd"],
       "db_file": "sensorDB.json",
       "channel_index": 1
     }
     ```

4. **Start the system:**
   ```bash
   python main.py
   ```

---

## 🚀 Usage

### Web Dashboard

Open your browser to [http://localhost:5000](http://localhost:5000) to access the dashboard.

Features:
- 📈 **Live charts** on the dashboard tracking of temperature (in Fahrenheit) and humidity per node
- 🔁 **Request telemetry** manually via button
- 🔍 **Per-node pages** for viewing detailed historical data for all environment metrics 


### Listener Service

The listener:
- Subscribes to Meshtastic’s telemetry messages
- Automatically reconnects on disconnect
- Stores data in `sensorDB.json`
- Provides endpoints for dashboard access

---

## ⚙️ Configuration

Update `config.json` to customize behavior:
- `radio_host`: Hostname or IP of the Meshtastic TCP interface
- `node_ids`: List of node IDs to collect telemetry from
- `db_file`: Path to the telemetry database (JSON)
- `channel_index`: Channel to use for requesting telemetry

---

## 📁 Project Structure

```text
meshsensor/
├── app.py                # Web dashboard (Flask)
├── listener_service.py   # Telemetry listener + data provider
├── shared_functions.py   # Utilities for telemetry processing
├── data_modules.py       # Data classes for nodes and metrics
├── config.json           # Your configuration
├── sensorDB.json         # Telemetry database (auto-generated)
├── templates/
│   ├── dashboard.html    # Main dashboard template
│   └── node_detail.html  # Per-node chart page
└── static/
    ├── css/
    ├── js/
    │   ├── dashboard.js
    │   └── echarts.min.js
```

---

## 🧪 Development Notes

- The **dashboard polls** the listener service for the latest data.
- The **frontend renders temperature in Fahrenheit** and converts timestamps to the browser’s local timezone.
- If `sensorDB.json` is missing or empty, the app will initialize with no data.

---

## 📜 License

This project is licensed under the [Unlicense](LICENSE).

---

## 🤝 Contributing

Pull requests and feature suggestions are welcome! Open an issue to discuss changes before submitting. I also request that you test any changes on a Raspberry Pi running standard Raspberry Pi OS as that is the primary intended platform.

---

## 🙏 Acknowledgments

- [Meshtastic](https://meshtastic.org)
- [Flask](https://flask.palletsprojects.com)
- [ECharts](https://echarts.apache.org)
