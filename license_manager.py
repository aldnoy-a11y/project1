import sqlite3
import datetime
import secrets

def generate_key():
    return secrets.token_hex(8).upper()

def create_license(plan="month"):
    conn = sqlite3.connect("licenses.db")
    c = conn.cursor()

    key = generate_key()

    now = datetime.datetime.now()
    if plan == "day":
        expires = now + datetime.timedelta(days=1)
    elif plan == "week":
        expires = now + datetime.timedelta(weeks=1)
    else:
        expires = now + datetime.timedelta(days=30)

    c.execute("INSERT INTO licenses (license_key, plan, expires_at) VALUES (?, ?, ?)",
              (key, plan, expires.isoformat()))

    conn.commit()
    conn.close()

    return key, expires

if __name__ == "__main__":
    k, e = create_license("month")
    print("New key:", k)
    print("Expires:", e)
