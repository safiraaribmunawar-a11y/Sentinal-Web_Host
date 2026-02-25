from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Global registry to store attack data
mesh_registry = []

@app.route('/')
def index():
    return render_template('dashboard.html')

# RECEIVER: Your EDR software sends data here
@app.route('/api/report', methods=['POST'])
def report():
    try:
        data = request.get_json()
        new_hit = {
            "lat": float(data.get('lat', 23.81)),
            "lon": float(data.get('lon', 90.41)),
            "magnitude": int(data.get('magnitude', 0))
        }
        
        # Add new hit to registry (keeping it simple for the global lookup)
        mesh_registry.append(new_hit)
        
        # Keep only the latest 100 reports to stay fast
        if len(mesh_registry) > 100:
            mesh_registry.pop(0)
            
        return jsonify({"status": "Success", "data": new_hit}), 200
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

# SENDER: The Dashboard pulls data from here
@app.route('/api/stats')
def stats():
    return jsonify({"zones": mesh_registry})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
