from flask import Flask, request, jsonify, render_template
import mysql.connector
import time
import os

app = Flask(__name__)

# -------- CONFIG --------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 4000)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "connection_timeout": 10
}

API_KEY = os.getenv("API_KEY")

# -------- GLOBAL STATE --------
last_seen = 0
collect_data = True

# -------- DB CONNECTION --------
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

# -------- RECEIVE DATA --------
@app.route("/api/data")
def receive_data():
    global last_seen, collect_data

    last_seen = time.time()

    key = request.args.get("key")
    if key != API_KEY:
        return "Invalid API Key", 403

    if not collect_data:
        return "Stopped"

    try:
        s1 = float(request.args.get("s1"))
        s2 = float(request.args.get("s2"))
        s3 = float(request.args.get("s3"))
    except:
        return "Invalid sensor values", 400

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO sensor_db (sensor1, sensor2, sensor3) VALUES (%s,%s,%s)",
            (s1, s2, s3)
        )

        db.commit()
        cursor.close()
        db.close()

        return "Saved"

    except Exception as e:
        print("DB ERROR:", e)
        return "Error", 500

# -------- STATUS --------
@app.route("/status")
def status():
    global last_seen

    if last_seen == 0:
        return jsonify({"status": "Disconnected", "last_seen_seconds": 0})

    diff = time.time() - last_seen

    state = "Connected" if diff < 20 else "Disconnected"

    return jsonify({
        "status": state,
        "last_seen_seconds": int(diff)
    })

# -------- START / STOP --------
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

# -------- GET DATA --------
@app.route("/data")
def get_data():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, sensor1, sensor2, sensor3, timestamp
            FROM sensor_db
            ORDER BY id DESC
            LIMIT 100
        """)

        data = cursor.fetchall()

        # ✅ NO timezone conversion
        for row in data:
            if row["timestamp"]:
                row["timestamp"] = row["timestamp"].strftime("%d/%m/%Y %H:%M:%S")

        cursor.close()
        db.close()

        return jsonify(data)

    except Exception as e:
        print("DATA ERROR:", e)
        return jsonify([])

# -------- SEARCH --------
@app.route("/search", methods=["POST"])
def search():
    start = request.form.get("start")
    end = request.form.get("end")

    if start:
        start = start.replace("T", " ")
    if end:
        end = end.replace("T", " ")

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, sensor1, sensor2, sensor3, timestamp
            FROM sensor_db
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY id DESC
        """, (start, end))

        data = cursor.fetchall()

        for row in data:
            if row["timestamp"]:
                row["timestamp"] = row["timestamp"].strftime("%d/%m/%Y %H:%M:%S")

        cursor.close()
        db.close()

        return jsonify(data)

    except Exception as e:
        print("SEARCH ERROR:", e)
        return jsonify([])

# -------- LOAD ALL --------
@app.route("/data_all")
def get_all_data():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, sensor1, sensor2, sensor3, timestamp
            FROM sensor_db
            ORDER BY id DESC
        """)

        data = cursor.fetchall()

        for row in data:
            if row["timestamp"]:
                row["timestamp"] = row["timestamp"].strftime("%d/%m/%Y %H:%M:%S")

        cursor.close()
        db.close()

        return jsonify(data)

    except Exception as e:
        print("DATA_ALL ERROR:", e)
        return jsonify([])

# -------- DOWNLOAD --------
@app.route("/download", methods=["POST"])
def download():
    import csv
    from io import StringIO

    start = request.form.get("start")
    end = request.form.get("end")

    if start:
        start = start.replace("T", " ")
    if end:
        end = end.replace("T", " ")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, sensor1, sensor2, sensor3, timestamp
        FROM sensor_db
        WHERE timestamp BETWEEN %s AND %s
        ORDER BY id DESC
    """, (start, end))

    data = cursor.fetchall()

    for row in data:
        if row["timestamp"]:
            row["timestamp"] = row["timestamp"].strftime("%d/%m/%Y %H:%M:%S")

    si = StringIO()
    writer = csv.writer(si)

    writer.writerow(["ID", "Sensor1", "Sensor2", "Sensor3", "Timestamp"])

    for row in data:
        writer.writerow([
            row["id"],
            row["sensor1"],
            row["sensor2"],
            row["sensor3"],
            row["timestamp"]
        ])

    cursor.close()
    db.close()

    return si.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=data.csv'
    }

# -------- QUERY --------
@app.route("/query", methods=["POST"])
def run_query():
    query = request.form.get("query")

    if not query:
        return jsonify({"error": "No query provided"})

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(query)

        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()

            for row in data:
                if "timestamp" in row and row["timestamp"]:
                    row["timestamp"] = row["timestamp"].strftime("%d/%m/%Y %H:%M:%S")

            result = data
        else:
            db.commit()
            result = {
                "message": "Query executed successfully",
                "rows_affected": cursor.rowcount
            }

        cursor.close()
        db.close()

        return jsonify(result)

    except Exception as e:
        print("QUERY ERROR:", e)
        return jsonify([])

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
