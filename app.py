from flask import Flask, request, jsonify, render_template
import time
import requests

app = Flask(__name__)

ESP_IP = "http://192.168.1.13"   # CHANGE THIS

data_store = []
last_seen = 0

@app.route("/")
def home():
    return render_template("index.html")

# -------- RECEIVE LIVE DATA --------
@app.route("/api/data")
def receive():
    global data_store, last_seen

    last_seen = time.time()

    record = request.args.get("data")

    parts = record.split(",")

    data_store.append({
        "id": len(data_store) + 1,
        "sensor1": parts[0],
        "sensor2": parts[1],
        "sensor3": parts[2],
        "timestamp": parts[3]   # NO CHANGE
    })

    return "OK"

# -------- STATUS --------
@app.route("/status")
def status():
    diff = time.time() - last_seen
    state = "Connected" if diff < 20 else "Disconnected"

    return jsonify({
        "status": state,
        "last_seen_seconds": int(diff)
    })

# -------- LIVE DATA --------
@app.route("/data")
def data():
    return jsonify(list(reversed(data_store[-50:])))

# -------- FULL SD DATA --------
@app.route("/data_all")
def data_all():
    try:
        r = requests.get(f"{ESP_IP}/sddata", timeout=5)
        return jsonify(r.json())
    except:
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
