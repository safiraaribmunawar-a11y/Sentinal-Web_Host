from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)

# This list acts as your temporary "Mesh Database"
# It stores real hits sent from your EDR software
mesh_registry = []

@app.route('/')
def index():
    return render_template('dashboard.html')

# --- 1. THE RECEIVER (For your EDR software) ---
@app.route('/api/report', methods=['POST'])
def report():
    try:
        data = request.get_json()
        
        # Extracting data from your EDR transmission
        new_hit = {
            "lat": float(data.get('lat', 23.81)),
            "lon": float(data.get('lon', 90.41)),
            "magnitude": int(data.get('magnitude', 100)),
            "id": random.randint(1000, 9999)
        }
        
        # Color logic based on magnitude
        if new_hit['magnitude'] > 200:
            new_hit['color'] = "#ff0000" # Critical
        elif new_hit['magnitude'] > 50:
            new_hit['color'] = "#ffff00" # Elevated
        else:
            new_hit['color'] = "#00ff41" # Safe
            
        new_hit['radius'] = new_hit['magnitude'] * 2000

        # Add to the start of the list
        mesh_registry.insert(0, new_hit)
        
        # Keep only the last 100 hits to stay fast
        if len(mesh_registry) > 100:
            mesh_registry.pop()
            
        print(f"Mesh Update: New hit at {new_hit['lat']}, {new_hit['lon']}")
        return jsonify({"status": "Success", "received": new_hit}), 200
        
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

# --- 2. THE SENDER (For the Website Map) ---
@app.route('/api/stats')
def stats():
    # If the list is empty, we show one 'dummy' point so the map isn't blank
    if not mesh_registry:
        return jsonify({"zones": [{
            "lat": 23.81, "lon": 90.41, 
            "color": "#00ff41", "radius": 500000
        }]})
        
    return jsonify({"zones": mesh_registry})

if __name__ == "__main__":
    # Standard dynamic port for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
