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
                lifes INTEGER DEFAULT 3
               )
""")

conn.close()

def update_points(user_id: str, points: int, db_path: str=db_path):
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    print(f"Adding one point to user {user_id}")
    cursor.execute("""INSERT INTO users (user_id, points, lifes) 
                      VALUES (?, ?, ?)
                      ON CONFLICT(user_id) DO UPDATE SET points = 1 + excluded.points""", 
                      (user_id, points, 3))
    conn.commit()
    conn.close()

def get_points(user_id: str, db_path: str=db_path) -> int:
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()
    if the_one is not None: # if the user is found
        the_one = the_one[0]
    else:
        print("User not found")
        the_one = 0
        
    conn.close()
    
    return the_one

def update_lifes(user_id: str, reset: bool = False, db_path: str = db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"Updating lifes of user {user_id}")

    if reset:
        # Si reset es True, actualiza siempre los 'lifes' a 2
        cursor.execute("""
            INSERT INTO users (user_id, points, lifes) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lifes = 3
            """, 
            (user_id, 0, 2))
    else:
        # Si reset es False, actualiza solo los 'lifes' mayores a 0
        cursor.execute("""
            INSERT INTO users (user_id, points, lifes) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lifes = lifes - 1
            WHERE lifes > 0
            """, 
            (user_id, 0, 2))

    conn.commit()
    print(f"LIFES: {get_lifes(user_id)}")
    conn.close()
    
def get_lifes(user_id: str, db_path: str=db_path) -> int:
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()
    cursor.execute("SELECT lifes FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()
    if the_one is not None: # if the user is found
        the_one = the_one[0]
    else:
        print("User not found")
        the_one = 3
        
    print(f"the_one: {the_one}")
    conn.close()
    
    return the_one
