from flask import Flask, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)

def get_db():
    return sqlite3.connect("licenses.db")

@app.route("/check", methods=["POST"])
def check_license():
    data = request.json

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error", "message": "missing_fields"})

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id, hwid, expires_at, status FROM licenses WHERE license_key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "invalid_key"})

    license_id, saved_hwid, expires_at, status = row

    if status != "active":
        return jsonify({"status": "inactive"})

    expires = datetime.datetime.fromisoformat(expires_at)
    now = datetime.datetime.now()

    if now > expires:
        return jsonify({"status": "expired"})

    if saved_hwid is None or saved_hwid == "":
        c.execute("UPDATE licenses SET hwid=? WHERE id=?", (hwid, license_id))
        conn.commit()
    else:
        if saved_hwid != hwid:
            return jsonify({"status": "hwid_mismatch"})

    days_left = (expires - now).days

    return jsonify({
        "status": "ok",
        "expires_at": expires_at,
        "days_left": days_left
    })

if __name__ == "__main__":
    app.run(port=80)
