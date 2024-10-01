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
                points INTEGER DEFAULT 0,
                lives INTEGER DEFAULT 3
               )
""")

conn.close()

def update_points(user_id: str, points: int, db_path: str=db_path):
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    print(f"Adding one point to user {user_id}")
    cursor.execute("""INSERT INTO users (user_id, points, lives) 
                      VALUES (?, ?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET points = 1 + excluded.points""", 
                      (user_id, points, 3))
    conn.commit()
    conn.close()

def get_points(user_id: str, db_path: str=db_path) -> int:
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()[0]
    conn.close()
    
    return the_one

def update_lives(user_id: str, db_path: str=db_path):
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    print(f"Updating lives of user {user_id}")

    cursor.execute("""INSERT INTO users (user_id, points, lives) 
                      VALUES (?, ?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET lives = lives - 1
                      WHERE lives > 0""", 
                      (user_id, 0, 2))
    conn.commit()
    
    print(f"LIVES: {get_lives(user_id)}")
    conn.close()
    
def get_lives(user_id: str, db_path: str=db_path) -> int:
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT lives FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()
    if the_one is not None: # if the user is found
        the_one = the_one[0]
    else:
        print("User not found")
        the_one = 3
        
    print(f"the_one: {the_one}")
    conn.close()
    
    return the_one
