from app.data.db import connect_database
from pathlib import Path
import sqlite3

# Point to the DATA/users.txt file
# project_root / DATA / users.txt
DATA_DIR = Path(__file__).resolve().parents[2] / "DATA"


def get_user_by_username(username):
    """Retrieve user by username."""
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def insert_user(username, password_hash, role='user'):
    """Insert new user."""
    conn = connect_database()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, role),
    )
    conn.commit()
    conn.close()


def migrate_users_from_file(filepath=DATA_DIR / "users.txt"):
    """
    Migrate users from users.txt to the database.
    """
    if not filepath.exists():
        print(f"⚠️  File not found: {filepath}")
        print("   No users to migrate.")
        return

    conn = connect_database()
    cursor = conn.cursor()
    migrated_count = 0

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # username,password_hash
            parts = line.split(",")
            if len(parts) >= 2:
                username = parts[0]
                password_hash = parts[1]

                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO users (username, password_hash, role) "
                        "VALUES (?, ?, ?)",
                        (username, password_hash, "user"),
                    )
                    if cursor.rowcount > 0:
                        migrated_count += 1
                except sqlite3.Error as e:
                    print(f"Error migrating user {username}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Migrated {migrated_count} users from {filepath.name}")
