# EDR System — Setup & Usage Guide

## Overview
This EDR (Endpoint Detection & Response) monitors your computer for:
- **CPU spikes** (sudden or sustained high usage)
- **Memory growth** (gradual or abrupt increases)
- **Network spikes** (data exfiltration, DDoS, scanning)

It uses a **history-based rule scorer + Isolation Forest ML model** to assign a threat score (0.0–1.0) and classifies into three levels:

| Level    | Score      | LED    | Meaning                        |
|----------|------------|--------|--------------------------------|
| SECURE   | < 0.45     | 🟢 Green  | Normal operation               |
| ELEVATED | 0.45–0.75  | 🟡 Yellow | Suspicious, monitoring closely |
| SEVERE   | > 0.75     | 🔴 Red    | Active threat detected         |

---

## Python EDR Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `config.py`
Edit these key settings:
```python
DEVICE_ID     = "my-laptop1"        # Unique name for this device
REPORT_URL    = "https://your-app.onrender.com"  # Your Render backend
ARDUINO_PORT  = "COM3"                # Windows: COM3, COM4... / Linux: /dev/ttyUSB0
SECURITY_CODE = "7391"                # Code to cancel a SEVERE alert
```

Or use environment variables:
```bash
set EDR_DEVICE_ID=laptop1
set EDR_REPORT_URL=https://sentinel-mesh.onrender.com
set EDR_ARDUINO_PORT=COM3
set EDR_SECURITY_CODE=7391
set EDR_DEVICE_LAT=23.81
set EDR_DEVICE_LON=90.41
```

### 3. Run
```bash
python edr_main.py
```

The system will:
1. Collect a 30-second baseline of your normal usage
2. Begin monitoring every 5 seconds
3. Send reports to your dashboard on severity changes
4. Send a heartbeat every 5 minutes

---

## Arduino Setup

### Hardware Required
- Arduino Uno (or Nano/Mega)
- Green LED + 220Ω resistor → Pin 9
- Yellow LED + 220Ω resistor → Pin 10
- Red LED + 220Ω resistor → Pin 11
- Piezo buzzer → Pin 6
- Toggle switch (kill switch) → Pin 2 + GND
- 4×4 Matrix Keypad → Rows: Pins 3,4,5,7 | Cols: A0,A1,A2,A3

### Library Required
Install in Arduino IDE: **Keypad** by Mark Stanley & Alexander Brevig

### Upload
1. Open `arduino/edr_controller.ino` in Arduino IDE
2. Select your board and port
3. Upload

### How the Hardware Works

| Action | What Happens |
|--------|-------------|
| PC detects ELEVATED | Yellow LED on |
| PC detects SEVERE | Yellow LED blinks fast + buzzer beeps with 20s countdown |
| Enter correct code + `#` on keypad in time | Warning cancelled, stays yellow |
| 20s timeout without correct code | Red LED + long alarm |
| Flip kill switch | Immediate green LED, sends KILL:1 to PC → resets to SECURE |

**Keypad usage:**
- Type your security code digits
- Press `#` to submit
- Press `*` to clear and start over

---

## Dashboard API

The EDR sends POST requests to your Render backend:

### `POST /api/report`
```json
{
  "device_id": "my-laptop",
  "timestamp": "2025-01-01T12:00:00Z",
  "severity": "SEVERE",
  "threat_score": 0.87,
  "breakdown": {
    "cpu_score": 0.9,
    "memory_score": 0.3,
    "network_score": 0.8,
    "ml_score": 0.75,
    "indicators": ["CPU spike: 94.2%", "Network spike: ↑52.3 MB/s ↓1.2 MB/s"]
  },
  "metrics": {
    "cpu_percent": 94.2,
    "mem_percent": 68.0,
    "net_bytes_recv_rate": 1258291,
    "net_bytes_sent_rate": 54855373
  }
}
```

### `POST /api/heartbeat`
```json
{
  "device_id": "my-laptop",
  "timestamp": "2025-01-01T12:05:00Z",
  "type": "heartbeat",
  "severity": "SECURE",
  "cpu_percent": 12.3,
  "mem_percent": 45.1
}
```

---

## File Structure
```
edr/
├── edr_main.py       # Entry point, main loop
├── config.py         # All configuration
├── monitor.py        # CPU/memory/network data collection
├── detector.py       # Rule scoring + Isolation Forest ML
├── arduino_comm.py   # Serial communication with Arduino
├── reporter.py       # HTTP reports to Render dashboard
├── requirements.txt
└── arduino/
    └── edr_controller.ino   # Arduino sketch
```
