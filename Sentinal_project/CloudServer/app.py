from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
import requests as req
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Supabase config
SUPABASE_URL = "https://aimddblfkkzvsykzcaae.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFpbWRkYmxma2t6dnN5a3pjYWFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQwMzUwMDYsImV4cCI6MjA4OTYxMTAwNn0.4n5dpXSc7wknonOoOWEgsAqE6nIhtQ5N2jv--ZQWjsA"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def db_insert(record):
    """Insert a report into Supabase."""
    try:
        r = req.post(
            f"{SUPABASE_URL}/rest/v1/reports",
            headers=HEADERS,
            json=record,
            timeout=10
        )
        if r.status_code not in (200, 201):
            print(f"[DB ERROR] Insert failed: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"[DB ERROR] {e}")

def db_fetch():
    """Fetch all reports from last 24 hours."""
    try:
        cutoff = time.time() - 86400  # 24 hours ago
        r = req.get(
            f"{SUPABASE_URL}/rest/v1/reports?timestamp=gte.{cutoff}&order=timestamp.desc&limit=1000",
            headers=HEADERS,
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        print(f"[DB ERROR] Fetch failed: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"[DB ERROR] {e}")
    return []

def db_clear():
    """Delete all reports."""
    try:
        r = req.delete(
            f"{SUPABASE_URL}/rest/v1/reports?id=gte.0",
            headers=HEADERS,
            timeout=10
        )
        if r.status_code not in (200, 204):
            print(f"[DB ERROR] Clear failed: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"[DB ERROR] {e}")

def get_country_from_coords(lat, lon):
    if 20.7 <= lat <= 26.7 and 88.0 <= lon <= 92.7:
        return "Bangladesh"
    if 49.9 <= lat <= 60.9 and -8.2 <= lon <= 1.8:
        return "United Kingdom"
    if 51.4 <= lat <= 55.4 and -10.5 <= lon <= -6.0:
        return "Ireland"
    if 36.8 <= lat <= 42.2 and -9.5 <= lon <= -6.2:
        return "Portugal"
    if 35.9 <= lat <= 43.8 and -9.3 <= lon <= 4.3:
        return "Spain"
    if 42.3 <= lat <= 51.1 and -4.8 <= lon <= 8.2:
        return "France"
    if 47.3 <= lat <= 55.1 and 5.9 <= lon <= 15.0:
        return "Germany"
    if 36.6 <= lat <= 47.1 and 6.6 <= lon <= 18.5:
        return "Italy"
    if 50.7 <= lat <= 53.6 and 3.3 <= lon <= 7.2:
        return "Netherlands"
    if 49.5 <= lat <= 51.5 and 2.5 <= lon <= 6.4:
        return "Belgium"
    if 45.8 <= lat <= 47.8 and 5.9 <= lon <= 10.5:
        return "Switzerland"
    if 46.4 <= lat <= 49.0 and 9.5 <= lon <= 17.2:
        return "Austria"
    if 49.0 <= lat <= 54.9 and 14.1 <= lon <= 24.2:
        return "Poland"
    if 44.4 <= lat <= 52.4 and 22.1 <= lon <= 40.2:
        return "Ukraine"
    if 55.3 <= lat <= 69.1 and 11.1 <= lon <= 24.2:
        return "Sweden"
    if 57.9 <= lat <= 71.2 and 4.5 <= lon <= 31.1:
        return "Norway"
    if 59.8 <= lat <= 70.1 and 20.0 <= lon <= 31.6:
        return "Finland"
    if 35.8 <= lat <= 42.1 and 26.0 <= lon <= 44.8:
        return "Turkey"
    if 16.4 <= lat <= 32.2 and 36.5 <= lon <= 55.7:
        return "Saudi Arabia"
    if 23.7 <= lat <= 37.1 and 60.9 <= lon <= 77.8:
        return "Pakistan"
    if 8.1 <= lat <= 35.5 and 68.1 <= lon <= 97.4:
        return "India"
    if 18.2 <= lat <= 53.6 and 73.5 <= lon <= 135.1:
        return "China"
    if 24.2 <= lat <= 45.7 and 122.9 <= lon <= 145.8:
        return "Japan"
    if 33.1 <= lat <= 38.6 and 124.6 <= lon <= 129.6:
        return "South Korea"
    if -11.0 <= lat <= 6.1 and 95.0 <= lon <= 141.0:
        return "Indonesia"
    if -43.7 <= lat <= -10.7 and 113.2 <= lon <= 153.6:
        return "Australia"
    if -47.3 <= lat <= -34.4 and 166.4 <= lon <= 178.6:
        return "New Zealand"
    if 24.4 <= lat <= 49.4 and -125.0 <= lon <= -66.9:
        return "United States"
    if 41.7 <= lat <= 83.1 and -141.0 <= lon <= -52.6:
        return "Canada"
    if 14.5 <= lat <= 32.7 and -117.1 <= lon <= -86.7:
        return "Mexico"
    if -33.8 <= lat <= 5.3 and -73.9 <= lon <= -34.8:
        return "Brazil"
    if -55.1 <= lat <= -21.8 and -73.6 <= lon <= -53.6:
        return "Argentina"
    if -34.8 <= lat <= -22.1 and 16.5 <= lon <= 32.9:
        return "South Africa"
    if 4.3 <= lat <= 13.9 and 2.7 <= lon <= 14.7:
        return "Nigeria"
    if 22.0 <= lat <= 31.7 and 24.7 <= lon <= 37.1:
        return "Egypt"
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
    try:
        data = request.get_json()
        lat      = float(data.get('lat', 23.81))
        lon      = float(data.get('lon', 90.41))
        severity = data.get('severity', 'SECURE').upper()

        record = {
            "lat":       lat,
            "lon":       lon,
            "country":   get_country_from_coords(lat, lon),
            "magnitude": int(data.get('magnitude', 0)),
            "device_id": data.get('device_id', 'unknown'),
            "severity":  severity,
            "timestamp": time.time()
        }
        db_insert(record)
        print(f"[REPORT] {record['device_id']} | {record['country']} | {severity} | magnitude={record['magnitude']}")
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
    reports = db_fetch()

    # Count SEVERE reports per country
    severe_counts = defaultdict(int)
    for hit in reports:
        if hit.get('severity') == 'SEVERE':
            severe_counts[hit.get('country', 'Unknown')] += 1

    country_summary = {}
    for country, count in severe_counts.items():
        if country == "Unknown":
            continue
        country_summary[country] = {
            "severe_count": count,
            "color": get_severity_color(count)
        }

    for hit in reports:
        c = hit.get('country', 'Unknown')
        if c != "Unknown" and c not in country_summary:
            country_summary[c] = {
                "severe_count": 0,
                "color": "green"
            }

    return jsonify({
        "zones":         reports,
        "countries":     country_summary,
        "total_severe":  sum(severe_counts.values()),
        "total_devices": len(set(h.get('device_id') for h in reports))
    })

@app.route('/api/clear', methods=['POST'])
def clear():
    db_clear()
    return jsonify({"status": "cleared"}), 200

@app.route('/download/sentinel_setup.bat')
def download_setup():
    """Serve the Windows setup batch file."""
    return send_from_directory('downloads', 'sentinel_setup.bat',
                               as_attachment=True,
                               download_name='sentinel_setup.bat')

@app.route('/download/<filename>')
def download_file(filename):
    """Serve EDR Python files for the installer to download."""
    allowed = [
        'edr_main.py', 'monitor.py', 'detector.py',
        'arduino_comm.py', 'reporter.py', 'config.py', 'requirements.txt'
    ]
    if filename not in allowed:
        return "Not found", 404
    return send_from_directory('downloads', filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
