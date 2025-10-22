import sqlite3

def get_connection(db_path: str = "drafting_tools.db") -> sqlite3.Connection:
    """Return a SQLite connection with helpful PRAGMAs enabled.

    - foreign_keys=ON to enforce FK constraints (including ON DELETE CASCADE)
    - journal_mode=WAL for better concurrency in a desktop app
    - synchronous=NORMAL for speed/safety tradeoff acceptable on local disks
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")
    except Exception:
        pass
    return conn

