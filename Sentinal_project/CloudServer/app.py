from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)

# This list will store data sent from your EDR software
real_time_data = []

@app.route('/')
def index():
    return render_template('dashboard.html')

# 1. THE RECEIVER: This is where your EDR sends data
@app.route('/api/report', methods=['POST'])
def report():
    try:
        data = request.get_json()
        
        # We extract lat, lon, and magnitude from your software
        new_entry = {
            "lat": float(data.get('lat')),
            "lon": float(data.get('lon')),
            "color": "#ff0000" if int(data.get('magnitude', 0)) > 200 else "#00ff41",
            "radius": int(data.get('magnitude', 100)) * 2000,
            "is_real": True
        }
        
        # Keep only the last 50 reports so the server doesn't get slow
        real_time_data.insert(0, new_entry)
        if len(real_time_data) > 50:
            real_time_data.pop()
            
        return jsonify({"status": "success", "message": "Data integrated into Mesh"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# 2. THE SENDER: This sends data TO your website map
@app.route('/api/stats')
def stats():
    # We combine our real EDR data with some random "background" mesh data
    background_zones = []
    locations = [[40, -100], [51, 0], [23, 90], [-25, 133]] # Random global spots
    
    for loc in locations:
        background_zones.append({
            "lat": loc[0] + random.uniform(-5, 5),
            "lon": loc[1] + random.uniform(-5, 5),
            "color": "#00ff41",
            "radius": random.randint(400000, 700000),
            "is_real": False
        })

    # Combine both lists and send to the dashboard
    return jsonify({"zones": real_time_data + background_zones})

if __name__ == "__main__":
    # Render requires the port to be dynamic
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
