import os
import sqlite3

def verify_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")

def verify_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            pass
    else:
        print(f"File '{file_path}' already exists.")

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASES_PATH = os.path.join(base_dir, 'databases')
verify_directory_exists(os.path.dirname(DATABASES_PATH))

def connect_db(db_id: str):
    path = os.path.join(DATABASES_PATH, db_id, 'sqlite3', db_id + ".db")
    verify_file_exists(path)
    conn = sqlite3.connect(path)
    
    return conn

def create_table(db_id: str):
    conn = connect_db(db_id)
    cursor = conn.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY, 
                    points INTEGER DEFAULT 0,
                    asked_questions INTEGER DEFAULT 0,
                    lives INTEGER DEFAULT 3
                )
    """)

    conn.close()
    
# create_table("NKTQNH")

def update_points(user_id: str, db_id: str, points: int):
    conn = connect_db(db_id)
    cursor = conn.cursor()
    print(f"Adding one point to user {user_id}")
    
    cursor.execute("""
        INSERT INTO users (user_id, points, asked_questions, lives) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET points = points + 1
    """, (user_id, points, 0, 3))
    
    conn.commit()
    conn.close()

def get_points(user_id: str, db_id: str) -> int:
    conn = connect_db(db_id)
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

def update_asked_questions(user_id: str, db_id: str):
    conn = connect_db(db_id)
    cursor = conn.cursor()
    print(f"Adding one question to user {user_id}")
    
    cursor.execute("""
        INSERT INTO users (user_id, points, asked_questions, lives) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET asked_questions = asked_questions + 1
    """, (user_id, 0, 1, 3))
    
    conn.commit()
    conn.close()

def get_asked_questions(user_id: str, db_id: str) -> int:
    conn = connect_db(db_id)
    cursor = conn.cursor()
    cursor.execute("SELECT asked_questions FROM users WHERE user_id=?", (user_id,))
    the_one = cursor.fetchone()
    if the_one is not None: # if the user is found
        the_one = the_one[0]
    else:
        print("User not found")
        the_one = 0
        
    conn.close()
    
    return the_one

def update_lives(user_id: str, db_id: str, reset: bool = False):
    conn = connect_db(db_id)
    cursor = conn.cursor()
    print(f"Updating lives of user {user_id}")

    if reset:
        # Si reset es True, actualiza siempre los 'lives' a 2
        cursor.execute("""
            INSERT INTO users (user_id, points, asked_questions, lives) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lives = 3
            """, 
            (user_id, 0, 0, 2))
    else:
        # Si reset es False, actualiza solo los 'lives' mayores a 0
        cursor.execute("""
            INSERT INTO users (user_id, points, asked_questions, lives) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lives = lives - 1
            WHERE lives > 0
            """, 
            (user_id, 0, 0, 2))

    conn.commit()
    print(f"LIVES: {get_lives(user_id, db_id)}")
    conn.close()
    
def get_lives(user_id: str, db_id: str) -> int:
    conn = connect_db(db_id)
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
