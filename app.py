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
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    start = data.get("start")
    end = data.get("end")

    result = []

    for r in full_data:
        if start <= r["timestamp"] <= end:
            result.append(r)

    return jsonify(result)
# -------- RECEIVE LIVE DATA --------
@app.route("/api/data")
def receive_live():
    global live_data, last_seen

    last_seen = time.time()

    record = request.args.get("data")

    try:
        parts = record.split(",")

        # ✅ validate ONLY sensors
        s1 = float(parts[0])
        s2 = float(parts[1])
        s3 = float(parts[2])

        ts = parts[3]   # keep as string

        live_data.append({
            "id": len(live_data) + 1,
            "sensor1": s1,
            "sensor2": s2,
            "sensor3": s3,
            "timestamp": ts
        })

        return "OK"

    except Exception as e:
        print("Error:", e)
        return "Invalid sensor values", 400


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
