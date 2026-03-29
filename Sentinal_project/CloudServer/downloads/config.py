"""
EDR Configuration
Edit these values to match your setup.
"""

import uuid
import os


class Config:
    # --- Device Identity ---
    # Unique ID for this device — auto-generated on first run, or set manually
    DEVICE_ID ="Laptop-1"

    # --- Device Location (used for map reporting) ---
    # Dhaka, Bangladesh coordinates — change if your device is elsewhere
    DEVICE_LAT = float(os.environ.get("EDR_LAT", "58.503"))
    DEVICE_LON = float(os.environ.get("EDR_LON", "81.818"))

    # --- Reporting ---
    # Your Render backend URL
    REPORT_URL = os.environ.get("EDR_REPORT_URL", "https://sentinel-mesh.onrender.com")
    REPORT_TIMEOUT = 120  # seconds

    # --- Heartbeat ---
    HEARTBEAT_INTERVAL = 30  # Send alive ping every 5 minutes (seconds)

    # --- Arduino ---
    ARDUINO_PORT = os.environ.get("EDR_ARDUINO_PORT", "COM3")  # Windows: COM3, Linux: /dev/ttyUSB0
    ARDUINO_BAUD = 9600
    SECURITY_CODE = os.environ.get("EDR_SECURITY_CODE", "1234")  # Change this!

    # --- Detection Thresholds (0.0 - 1.0 score scale) ---
    THRESHOLD_ELEVATED = 0.35
    THRESHOLD_SEVERE = 0.50

    # --- Scoring Weights ---
    WEIGHT_CPU = 0.30
    WEIGHT_MEMORY = 0.25
    WEIGHT_NETWORK = 0.25
    WEIGHT_ML = 0.20

    # --- History ---
    HISTORY_WINDOW = 60       # Number of snapshots to keep
    BASELINE_DURATION = 120

    # --- Polling ---
    POLL_INTERVAL = 5         # Seconds between each snapshot

    # --- Score Smoothing ---
    # Number of recent scores to average — prevents flip-flopping between severities
    SMOOTHING_WINDOW = 2      # Average last 4 readings (20 seconds worth)

    # --- Severe Cooldown ---
    # Seconds before a new SEVERE warning can trigger after one already fired
    SEVERE_COOLDOWN =1200     # 5 minutes

    # --- Network Spike Detection ---
    NET_SPIKE_MULTIPLIER = 5.0   # Flag if traffic > 5x baseline average
    NET_ABS_THRESHOLD_MB = 50    # Also flag if > 50 MB/s regardless

    # --- CPU Spike Detection ---
    CPU_SPIKE_MULTIPLIER = 2.5
    CPU_ABS_THRESHOLD = 85.0    # Also flag if > 85%

    # --- Memory Growth Detection ---
    MEM_GROWTH_THRESHOLD = 0.15  # Flag if memory grows > 15% over history window
    MEM_ABS_THRESHOLD = 90.0     # Also flag if > 90% used