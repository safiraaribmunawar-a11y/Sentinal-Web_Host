from flask import Flask, render_template, jsonify
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/stats')
def stats():
    zones = []
    locations = [[40, -100], [51, 0], [23, 90], [23, 77], [-25, 133], [35, 140]]
    for loc in locations:
        attacks = random.randint(10, 400)
        color = "#00ff41" if attacks < 50 else ("#ffff00" if attacks < 200 else "#ff0000")
        zones.append({
            "lat": loc[0] + random.uniform(-2, 2),
            "lon": loc[1] + random.uniform(-2, 2),
            "color": color,
            "radius": random.randint(600000, 1100000)
        })
    return jsonify({"zones": zones})

if __name__ == "__main__":
    # The 'PORT' part is required for Render to work
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)