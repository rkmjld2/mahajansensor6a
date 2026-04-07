from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

# -------- STORAGE --------
live_data = []
full_data = []
last_seen = 0

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

# -------- RECEIVE LIVE DATA --------
@app.route("/api/data")
def receive_live():
    global live_data, last_seen

    last_seen = time.time()

    record = request.args.get("data")
    parts = record.split(",")

    live_data.append({
        "id": len(live_data) + 1,
        "sensor1": parts[0],
        "sensor2": parts[1],
        "sensor3": parts[2],
        "timestamp": parts[3]
    })

    return "OK"

# -------- RECEIVE SD FULL DATA --------
@app.route("/api/sddata", methods=["POST"])
def receive_sd():

    global full_data

    data = request.get_json()

    full_data = data   # replace full dataset

    return jsonify({"status": "SD data updated", "records": len(full_data)})

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
    return jsonify(list(reversed(live_data[-50:])))

# -------- FULL DATA --------
@app.route("/data_all")
def data_all():
    return jsonify(full_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
