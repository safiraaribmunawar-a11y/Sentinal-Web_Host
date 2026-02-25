from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)

# Global registry with timestamp support
mesh_registry = []

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/report', methods=['POST'])
def report():
    try:
        data = request.get_json()
        new_hit = {
            "lat": float(data.get('lat', 23.81)),
            "lon": float(data.get('lon', 90.41)),
            "magnitude": int(data.get('magnitude', 0)),
            "timestamp": time.time()  # Marks the exact moment of the attack
        }
        mesh_registry.append(new_hit)
        return jsonify({"status": "Success"}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/api/stats')
def stats():
    global mesh_registry
    now = time.time()
    
    # AUTO-RESET: Remove any report older than 10 seconds
    mesh_registry = [hit for hit in mesh_registry if now - hit['timestamp'] < 10]
    
    return jsonify({"zones": mesh_registry})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
