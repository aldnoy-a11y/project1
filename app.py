from flask import Flask, render_template, request, jsonify, redirect
import sqlite3
import datetime
import time
import secrets
app = Flask(__name__)
DB_FILE = "licenses.db"


def generate_key():
    return secrets.token_hex(8).upper()
# ------------------ DATABASE HELPER ------------------

def get_db():
    return sqlite3.connect(DB_FILE)


# ------------------ LICENSE CHECK API ------------------

@app.route("/check", methods=["POST"])
def check_license():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "no_json"})

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error", "message": "missing_fields"})

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id, hwid, plan, expires_at, status, user FROM licenses WHERE license_key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "invalid_key"})

    lic_id, saved_hwid, plan, expires_at, status, user = row

    if status != "active":
        return jsonify({"status": "inactive"})

    expires = datetime.datetime.fromisoformat(expires_at)
    now = datetime.datetime.now()

    if now > expires:
        return jsonify({"status": "expired"})

    # First time HWID binding
    if not saved_hwid:
        c.execute("UPDATE licenses SET hwid=? WHERE id=?", (hwid, lic_id))
        conn.commit()
    else:
        if saved_hwid != hwid:
            return jsonify({"status": "hwid_mismatch"})

    days_left = (expires - now).days

    return jsonify({
        "status": "ok",
        "user": user,
        "plan": plan,
        "expires_at": expires_at,
        "days_left": days_left
    })


# ------------------ ADMIN PAGES ------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin_dashboard():
    return render_template("dashboard.html")


@app.route("/admin/list")
def admin_list():
    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("SELECT license_key, user, plan, expires_at, status, hwid FROM licenses")
        rows = c.fetchall()

    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            return "❌ ERROR: 'licenses' table was not found.<br><br>Create the table first.", 500
        else:
            return f"Database Error: {e}", 500

    # Build list for template
    licenses = []
    for r in rows:
        licenses.append({
            "license_key": r[0],
            "user": r[1],
            "plan": r[2],
            "expires_at": r[3],
            "status": r[4],
            "hwid": r[5]
        })

    return render_template("list_keys.html", keys=licenses)


@app.route("/admin/add", methods=["GET", "POST"])
def admin_add():
    if request.method == "POST":
        
        user = request.form.get("user")
        plan = request.form.get("plan")

        if not user or not plan:
            return "Missing fields", 400

        # Determine days based on plan
        if plan == "1day":
            days = 1
        elif plan == "1week":
            days = 7
        elif plan == "1month":
            days = 30
        elif plan == "1year":
            days = 365
        elif plan == "custom":
            custom_days = request.form.get("custom_days")
            if not custom_days:
                return "Missing custom days", 400
            days = int(custom_days)
        else:
            return "Invalid plan", 400

        # Generate key + expiration
        key = generate_key()
        expires = datetime.datetime.now() + datetime.timedelta(days=days)

        conn = get_db()
        c = conn.cursor()

        c.execute("""
            INSERT INTO licenses (license_key, user, plan, expires_at, status, hwid)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, user, plan, expires.isoformat(), "active", ""))

        conn.commit()
        conn.close()

        return redirect("/admin/list")

    return render_template("add_key.html")


@app.route("/admin/edit/<key>", methods=["GET", "POST"])
def admin_edit(key):
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        user = request.form["user"]
        plan = request.form["plan"]
        expires = request.form["expires"]
        status = request.form["status"]

        c.execute("""
            UPDATE licenses
            SET user=?, plan=?, expires_at=?, status=?
            WHERE license_key=?
        """, (user, plan, expires, status, key))

        conn.commit()
        return redirect("/admin/list")

    c.execute("SELECT user, plan, expires_at, status FROM licenses WHERE license_key=?", (key,))
    row = c.fetchone()

    data = {
        "user": row[0],
        "plan": row[1],
        "expires_at": row[2],
        "status": row[3]
    }

    return render_template("edit_key.html", key=key, data=data)


@app.route("/admin/delete/<key>")
def admin_delete(key):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM licenses WHERE license_key=?", (key,))
    conn.commit()

    return redirect("/admin/list")


# ------------------ RUN SERVER ------------------

if __name__ == "__main__":
    app.run(port=80)