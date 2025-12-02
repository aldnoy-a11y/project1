import sqlite3

def init_db():
    conn = sqlite3.connect("licenses.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT UNIQUE,
        hwid TEXT,
        plan TEXT,
        expires_at TEXT,
        status TEXT DEFAULT 'active',
        user TEXT DEFAULT ''


    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized!")
