from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import time
import json
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Persistent storage file
REGISTRY_FILE = "mesh_registry.json"

def load_registry():
    """Load registry from file, return empty list if not found."""
    try:
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load registry: {e}")
    return []

def save_registry(registry):
    """Save registry to file."""
    try:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f)
    except Exception as e:
        print(f"[WARN] Could not save registry: {e}")

# Load on startup
mesh_registry = load_registry()
print(f"[STARTUP] Loaded {len(mesh_registry)} existing reports from disk.")

def get_country_from_coords(lat, lon):
    if 20 <= lat <= 27 and 88 <= lon <= 93:
        return "Bangladesh"
    if 24 <= lat <= 50 and -125 <= lon <= -66:
        return "United States"
    if 49 <= lat <= 61 and -9 <= lon <= 2:
        return "United Kingdom"
    if 41 <= lat <= 51 and -5 <= lon <= 10:
        return "France"
    if 47 <= lat <= 55 and 6 <= lon <= 15:
        return "Germany"
    if 36 <= lat <= 47 and 6 <= lon <= 19:
        return "Italy"
    if 35 <= lat <= 44 and -10 <= lon <= 5:
        return "Spain"
    if 43 <= lat <= 70 and 19 <= lon <= 68:
        return "Russia"
    if 8 <= lat <= 37 and 68 <= lon <= 98:
        return "India"
    if 18 <= lat <= 54 and 73 <= lon <= 135:
        return "China"
    if 30 <= lat <= 46 and 129 <= lon <= 146:
        return "Japan"
    if -35 <= lat <= -10 and 113 <= lon <= 154:
        return "Australia"
    if 42 <= lat <= 83 and -141 <= lon <= -52:
        return "Canada"
    if -34 <= lat <= 5 and -74 <= lon <= -34:
        return "Brazil"
    return "Unknown"

def get_severity_color(severe_count):
    if severe_count >= 200:
        return "red"
    elif severe_count >= 50:
        return "yellow"
    elif severe_count >= 1:
        return "blue"
    return "green"

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/report', methods=['POST'])
def report():
    global mesh_registry
    try:
        data = request.get_json()
        lat      = float(data.get('lat', 23.81))
        lon      = float(data.get('lon', 90.41))
        severity = data.get('severity', 'SECURE').upper()

        new_hit = {
            "lat":        lat,
            "lon":        lon,
            "country":    get_country_from_coords(lat, lon),
            "magnitude":  int(data.get('magnitude', 0)),
            "device_id":  data.get('device_id', 'unknown'),
            "severity":   severity,
            "timestamp":  time.time()
        }
        mesh_registry.append(new_hit)
        save_registry(mesh_registry)  # persist to disk
        print(f"[REPORT] {new_hit['device_id']} | {new_hit['country']} | {severity} | magnitude={new_hit['magnitude']}")
        return jsonify({"status": "Success"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    try:
        data = request.get_json()
        print(f"[HEARTBEAT] {data.get('device_id')} | {data.get('severity')} | CPU={data.get('cpu_percent')}%")
        return jsonify({"status": "alive"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/api/stats')
def stats():
    global mesh_registry
    now = time.time()

    # Keep SEVERE reports for 24 hours, others for 60 seconds
    mesh_registry = [
        h for h in mesh_registry
        if (h['severity'] == 'SEVERE' and now - h['timestamp'] < 86400)
        or (h['severity'] != 'SEVERE' and now - h['timestamp'] < 60)
    ]
    save_registry(mesh_registry)

    # Count SEVERE reports per country
    severe_counts = defaultdict(int)
    for hit in mesh_registry:
        if hit['severity'] == 'SEVERE':
            severe_counts[hit['country']] += 1

    country_summary = {}
    for country, count in severe_counts.items():
        if country == "Unknown":
            continue
        country_summary[country] = {
            "severe_count": count,
            "color": get_severity_color(count)
        }

    for hit in mesh_registry:
        c = hit['country']
        if c != "Unknown" and c not in country_summary:
            country_summary[c] = {
                "severe_count": 0,
                "color": "green"
            }

    return jsonify({
        "zones":         mesh_registry,
        "countries":     country_summary,
        "total_severe":  sum(severe_counts.values()),
        "total_devices": len(set(h['device_id'] for h in mesh_registry))
    })

@app.route('/api/clear', methods=['POST'])
def clear():
    """Admin endpoint to manually clear all reports."""
    global mesh_registry
    mesh_registry = []
    save_registry(mesh_registry)
    return jsonify({"status": "cleared"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
