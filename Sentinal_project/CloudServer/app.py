from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import time
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Global registry with timestamp support
mesh_registry = []

def get_country_from_coords(lat, lon):
    """
    Basic coordinate-to-country mapping.
    Expand this list as more devices from different countries connect.
    """
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
    """
    Color based on number of SEVERE reports from devices in that country.
    Blue   = 1-49   (some threat activity)
    Yellow = 50-199 (elevated regional threat)
    Red    = 200+   (critical regional threat)
    """
    if severe_count >= 200:
        return "red"
    elif severe_count >= 50:
        return "yellow"
    elif severe_count >= 1:
        return "blue"
    return "green"  # secure / no reports

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/report', methods=['POST'])
def report():
    try:
        data = request.get_json()
        lat = float(data.get('lat', 23.81))
        lon = float(data.get('lon', 90.41))
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

    # Remove reports older than 60 seconds
    mesh_registry = [h for h in mesh_registry if now - h['timestamp'] < 60]

    # Count SEVERE reports per country
    severe_counts = defaultdict(int)
    for hit in mesh_registry:
        if hit['severity'] == 'SEVERE':
            severe_counts[hit['country']] += 1

    # Build country summary
    country_summary = {}
    for country, count in severe_counts.items():
        if country == "Unknown":
            continue
        country_summary[country] = {
            "severe_count": count,
            "color": get_severity_color(count)
        }

    # Also include countries with non-severe reports (show as green/blue)
    for hit in mesh_registry:
        c = hit['country']
        if c != "Unknown" and c not in country_summary:
            country_summary[c] = {
                "severe_count": 0,
                "color": "green"
            }

    return jsonify({
        "zones": mesh_registry,
        "countries": country_summary,
        "total_severe": sum(severe_counts.values()),
        "total_devices": len(set(h['device_id'] for h in mesh_registry))
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

