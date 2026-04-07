from flask import Flask, request, jsonify, render_template
import time
import os
from datetime import timedelta, datetime
import csv


app = Flask(__name__)

# -------- CONFIG --------
DATA_FILE = "data.csv"
API_KEY = os.getenv("API_KEY")

# -------- STATE --------
last_seen = 0
collect_data = True

# -------- INIT FILE --------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id","sensor1","sensor2","sensor3","timestamp"])

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

# -------- RECEIVE DATA --------



@app.route('/api/data')
def receive_data():
    try:
        # -------- API KEY CHECK --------
        key = request.args.get('key', '')
        if key != API_KEY:
            return "Unauthorized", 403

        # -------- SENSOR VALUES --------
        s1 = request.args.get('s1', '0')
        s2 = request.args.get('s2', '0')
        s3 = request.args.get('s3', '0')

        # -------- TIME HANDLING --------
        timestamp = request.args.get('time')

        if not timestamp:
            # fallback to IST
            now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        # -------- DATABASE INSERT --------
        cursor = db.cursor()

        query = """
        INSERT INTO sensor_db (s1, s2, s3, timestamp)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(query, (s1, s2, s3, timestamp))
        db.commit()

        print("✅ Data Saved:", s1, s2, s3, timestamp)

        return "OK", 200

    except Exception as e:
        print("❌ API ERROR:", e)
        return "ERROR", 500


# -------- STATUS --------
@app.route("/status")
def status():
    if last_seen == 0:
        return jsonify({"status": "Disconnected", "last_seen_seconds": 0})

    diff = time.time() - last_seen
    state = "Connected" if diff < 20 else "Disconnected"

    return jsonify({"status": state, "last_seen_seconds": int(diff)})

# -------- START/STOP --------
@app.route("/start")
def start():
    global collect_data
    collect_data = True
    return "Started"

@app.route("/stop")
def stop():
    global collect_data
    collect_data = False
    return "Stopped"

# -------- READ DATA --------
def read_data():
    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    return list(reversed(data))

# -------- GET DATA --------
@app.route("/data")
def get_data():
    return jsonify(read_data()[:100])

# -------- LOAD ALL --------
@app.route("/data_all")
def data_all():
    return jsonify(read_data())

# -------- SEARCH --------
@app.route("/search", methods=["POST"])
def search():
    start = request.form.get("start")
    end = request.form.get("end")

    start_dt = datetime.strptime(start.replace("T"," "), "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(end.replace("T"," "), "%Y-%m-%d %H:%M")

    result = []

    for row in read_data():
        t = datetime.strptime(row["timestamp"], "%d/%m/%Y %H:%M:%S")
        if start_dt <= t <= end_dt:
            result.append(row)

    return jsonify(result)

# -------- DOWNLOAD --------
@app.route("/download", methods=["POST"])
def download():
    with open(DATA_FILE, "r") as f:
        data = f.read()

    return data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=data.csv'
    }

# -------- CUSTOM QUERY (LIMITED) --------
@app.route("/query", methods=["POST"])
def query():
    q = request.form.get("query").lower()

    if "delete" in q:
        open(DATA_FILE, "w").write("id,sensor1,sensor2,sensor3,timestamp\n")
        return jsonify({"message":"All data deleted","rows_affected":0})

    return jsonify({"error":"Only DELETE supported"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
