import sqlite3

conn = sqlite3.connect('qag_se_system.db')

cursor = conn.cursor()

cursor.execute("""
               CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY, 
                points INTEGER DEFAULT 0)
""")

conn.close()

def update_points(user_id: str, points: int):
    conn = sqlite3.connect('qag_se_system.db')

    cursor = conn.cursor()
    print(f"Adding one point to user {user_id}")
    cursor.execute("""INSERT INTO users (user_id, points) 
                      VALUES (?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET points = 1 + excluded.points""", 
                      (user_id, points))
    conn.commit()
    conn.close()

def get_points(user_id: str):
    conn = sqlite3.connect('qag_se_system.db')

    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()[0]
    conn.close()
    
    return the_one

