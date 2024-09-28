import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'sqlite3', 'qag_se_system.db')
print(f"dirname: {os.path.dirname(__file__)}")
print(f"db_path: {db_path}")
conn = sqlite3.connect(db_path)

cursor = conn.cursor()

cursor.execute("""
               CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, 
                points INTEGER DEFAULT 0)
""")

conn.close()

def update_points(user_id: str, points: int, db_path: str=db_path):
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    print(f"Adding one point to user {user_id}")
    cursor.execute("""INSERT INTO users (user_id, points) 
                      VALUES (?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET points = 1 + excluded.points""", 
                      (user_id, points))
    conn.commit()
    conn.close()

def get_points(user_id: str, db_path: str=db_path) -> int:
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()[0]
    conn.close()
    
    return the_one

