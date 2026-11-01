"""Tiny SQLite layer: seeds sample users/products and offers a health ping."""
import os
import sqlite3

from . import config


def get_conn() -> sqlite3.Connection:
    folder = os.path.dirname(config.DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, role TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)")
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
                [
                    ("Asha Rao", "asha@example.com", "admin"),
                    ("Ravi Kumar", "ravi@example.com", "editor"),
                    ("Meera Nair", "meera@example.com", "viewer"),
                    ("John Doe", "john@example.com", "viewer"),
                ],
            )
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                [
                    ("Laptop", 55999.0, 25),
                    ("Mechanical Keyboard", 4999.0, 120),
                    ("Wireless Mouse", 1299.0, 300),
                    ("27-inch Monitor", 15999.0, 40),
                ],
            )


def fetch_all(sql: str) -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


def ping() -> bool:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return True
    except Exception:
        return False
