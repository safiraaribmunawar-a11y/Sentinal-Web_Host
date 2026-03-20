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
    # More specific countries first to avoid overlap

    # Bangladesh
    if 20.7 <= lat <= 26.7 and 88.0 <= lon <= 92.7:
        return "Bangladesh"

    # United Kingdom
    if 49.9 <= lat <= 60.9 and -8.2 <= lon <= 1.8:
        return "United Kingdom"

    # Ireland
    if 51.4 <= lat <= 55.4 and -10.5 <= lon <= -6.0:
        return "Ireland"

    # Portugal
    if 36.8 <= lat <= 42.2 and -9.5 <= lon <= -6.2:
        return "Portugal"

    # Spain
    if 35.9 <= lat <= 43.8 and -9.3 <= lon <= 4.3:
        return "Spain"

    # France
    if 42.3 <= lat <= 51.1 and -4.8 <= lon <= 8.2:
        return "France"

    # Germany
    if 47.3 <= lat <= 55.1 and 5.9 <= lon <= 15.0:
        return "Germany"

    # Italy
    if 36.6 <= lat <= 47.1 and 6.6 <= lon <= 18.5:
        return "Italy"

    # Netherlands
    if 50.7 <= lat <= 53.6 and 3.3 <= lon <= 7.2:
        return "Netherlands"

    # Belgium
    if 49.5 <= lat <= 51.5 and 2.5 <= lon <= 6.4:
        return "Belgium"

    # Switzerland
    if 45.8 <= lat <= 47.8 and 5.9 <= lon <= 10.5:
        return "Switzerland"

    # Austria
    if 46.4 <= lat <= 49.0 and 9.5 <= lon <= 17.2:
        return "Austria"

    # Poland
    if 49.0 <= lat <= 54.9 and 14.1 <= lon <= 24.2:
        return "Poland"

    # Ukraine
    if 44.4 <= lat <= 52.4 and 22.1 <= lon <= 40.2:
        return "Ukraine"

    # Sweden
    if 55.3 <= lat <= 69.1 and 11.1 <= lon <= 24.2:
        return "Sweden"

    # Norway
    if 57.9 <= lat <= 71.2 and 4.5 <= lon <= 31.1:
        return "Norway"

    # Finland
    if 59.8 <= lat <= 70.1 and 20.0 <= lon <= 31.6:
        return "Finland"

    # Turkey
    if 35.8 <= lat <= 42.1 and 26.0 <= lon <= 44.8:
        return "Turkey"

    # Saudi Arabia
    if 16.4 <= lat <= 32.2 and 36.5 <= lon <= 55.7:
        return "Saudi Arabia"

    # Pakistan
    if 23.7 <= lat <= 37.1 and 60.9 <= lon <= 77.8:
        return "Pakistan"

    # India (check before China due to overlap)
    if 8.1 <= lat <= 35.5 and 68.1 <= lon <= 97.4:
        return "India"

    # China
    if 18.2 <= lat <= 53.6 and 73.5 <= lon <= 135.1:
        return "China"

    # Japan
    if 24.2 <= lat <= 45.7 and 122.9 <= lon <= 145.8:
        return "Japan"

    # South Korea
    if 33.1 <= lat <= 38.6 and 124.6 <= lon <= 129.6:
        return "South Korea"

    # Indonesia
    if -11.0 <= lat <= 6.1 and 95.0 <= lon <= 141.0:
        return "Indonesia"

    # Australia
    if -43.7 <= lat <= -10.7 and 113.2 <= lon <= 153.6:
        return "Australia"

    # New Zealand
    if -47.3 <= lat <= -34.4 and 166.4 <= lon <= 178.6:
        return "New Zealand"

    # Canada
    if 41.7 <= lat <= 83.1 and -141.0 <= lon <= -52.6:
        return "Canada"

    # United States
    if 24.4 <= lat <= 49.4 and -125.0 <= lon <= -66.9:
        return "United States"

    # Mexico
    if 14.5 <= lat <= 32.7 and -117.1 <= lon <= -86.7:
        return "Mexico"

    # Brazil
    if -33.8 <= lat <= 5.3 and -73.9 <= lon <= -34.8:
        return "Brazil"

    # Argentina
    if -55.1 <= lat <= -21.8 and -73.6 <= lon <= -53.6:
        return "Argentina"

    # South Africa
    if -34.8 <= lat <= -22.1 and 16.5 <= lon <= 32.9:
        return "South Africa"

    # Nigeria
    if 4.3 <= lat <= 13.9 and 2.7 <= lon <= 14.7:
        return "Nigeria"

    # Egypt
    if 22.0 <= lat <= 31.7 and 24.7 <= lon <= 37.1:
        return "Egypt"

    # Russia — must be last as it is enormous and overlaps many ranges
    if 41.2 <= lat <= 81.9 and 19.6 <= lon <= 180.0:
        return "Russia"

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
