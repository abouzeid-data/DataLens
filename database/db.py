import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib
import os
import hmac
import secrets

def _app_data_dir():
    root = os.getenv("DATALENS_DATA_DIR")
    if root:
        path = Path(root)
    elif os.name == "nt" and os.getenv("APPDATA"):
        path = Path(os.getenv("APPDATA")) / "DataLens"
    else:
        path = Path.home() / ".datalens"
    path.mkdir(parents=True, exist_ok=True)
    return path

DB_PATH = Path(os.getenv("DATALENS_DB_PATH", _app_data_dir() / "app.db"))

PBKDF2_ITERATIONS = 260000

def _hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("ascii"),
        PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"

def _legacy_hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _verify_password(password, stored_hash):
    if not stored_hash:
        return False

    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, digest = stored_hash.split("$", 3)
            candidate = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("ascii"),
                int(iterations)
            ).hex()
            return hmac.compare_digest(candidate, digest)
        except Exception:
            return False

    return hmac.compare_digest(_legacy_hash_password(password), stored_hash)

def _hash_reset_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def initialize_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at DATETIME
        )
    ''')
    
    # Try to add new columns to users if they don't exist
    for col, col_type in [
        ('is_admin', 'BOOLEAN DEFAULT 0'),
        ('first_name', 'TEXT'),
        ('last_name', 'TEXT'),
        ('email', 'TEXT'),
        ('use_case', 'TEXT DEFAULT "General"')
    ]:
        try:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
        except sqlite3.OperationalError:
            pass
            
    # Create password_resets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT,
            expires_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Try to add user_id column to analysis_history if it doesn't exist
    try:
        cursor.execute('ALTER TABLE analysis_history ADD COLUMN user_id INTEGER')
    except sqlite3.OperationalError:
        pass # Column already exists
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT,
            timestamp DATETIME,
            row_count INTEGER,
            column_count INTEGER,
            total_revenue REAL,
            report_path TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create user_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            logo_path TEXT,
            brand_color TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create saved_datasets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            file_paths TEXT NOT NULL,
            created_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    return conn

def register_user(username, password, first_name='', last_name='', email='', use_case='General'):
    conn = initialize_db()
    cursor = conn.cursor()
    hashed = _hash_password(password)
    email = (email or '').strip().lower()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, first_name, last_name, email, use_case, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed, first_name, last_name, email, use_case, datetime.now()))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id, None
    except sqlite3.IntegrityError:
        return None, "Username already exists"
    finally:
        conn.close()

def verify_user(username, password):
    conn = initialize_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, use_case, password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    
    if row and _verify_password(password, row[2]):
        if not str(row[2]).startswith("pbkdf2_sha256$"):
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (_hash_password(password), row[0]))
            conn.commit()
        conn.close()
        return row[0], row[1]

    conn.close()
    return None, None

def save_analysis_history(user_id, file_name, row_count, column_count, total_revenue, report_path):
    conn = initialize_db()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO analysis_history (user_id, file_name, timestamp, row_count, column_count, total_revenue, report_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, file_name, timestamp, row_count, column_count, total_revenue, report_path))
    conn.commit()
    conn.close()

def load_analysis_history(user_id):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analysis_history WHERE user_id = ?', (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def get_user_settings(user_id):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('SELECT logo_path, brand_color FROM user_settings WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"logo_path": result[0], "brand_color": result[1]}
    return {"logo_path": None, "brand_color": "#0ea5e9"}

def save_user_settings(user_id, logo_path, brand_color):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_settings (user_id, logo_path, brand_color)
        VALUES (?, ?, ?)
    ''', (user_id, logo_path, brand_color))
    conn.commit()
    conn.close()

def save_dataset(user_id, name, file_paths_json):
    conn = initialize_db()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO saved_datasets (user_id, name, file_paths, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, name, file_paths_json, timestamp))
    conn.commit()
    conn.close()

def get_saved_datasets(user_id):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, file_paths, created_at FROM saved_datasets WHERE user_id = ?', (user_id,))
    datasets = cursor.fetchall()
    conn.close()
    return datasets

def delete_saved_dataset(dataset_id, user_id):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM saved_datasets WHERE id = ? AND user_id = ?', (dataset_id, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, is_admin, created_at FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def admin_delete_user(user_id):
    conn = initialize_db()
    cursor = conn.cursor()
    # Delete related data first due to foreign keys
    cursor.execute('DELETE FROM saved_datasets WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM user_settings WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM analysis_history WHERE user_id = ?', (user_id,))
    # Delete the user
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def admin_reset_password(user_id, new_password):
    conn = initialize_db()
    cursor = conn.cursor()
    hashed = _hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed, user_id))
    conn.commit()
    conn.close()

def is_user_admin(user_id):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return bool(row[0])
    return False

# --- Password Reset Functions ---
import secrets
from datetime import timedelta

def create_password_reset_token(email):
    conn = initialize_db()
    cursor = conn.cursor()
    email = (email or '').strip().lower()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None, "Email not found"
        
    user_id = row[0]
    token = secrets.token_urlsafe(32)
    token_hash = _hash_reset_token(token)
    expires_at = datetime.now() + timedelta(hours=1)
    
    cursor.execute('DELETE FROM password_resets WHERE user_id = ?', (user_id,))
    cursor.execute('INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)',
                   (user_id, token_hash, expires_at))
    conn.commit()
    conn.close()
    return token, None

def validate_reset_token(token):
    conn = initialize_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, expires_at FROM password_resets WHERE token = ?', (_hash_reset_token(token),))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None, "Invalid token"
        
    expires_at = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S.%f")
    if datetime.now() > expires_at:
        return None, "Token expired"
        
    return row[0], None

def reset_password_with_token(token, new_password):
    user_id, error = validate_reset_token(token)
    if error:
        return False, error
        
    conn = initialize_db()
    cursor = conn.cursor()
    hashed = _hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed, user_id))
    # Invalidate token
    cursor.execute('DELETE FROM password_resets WHERE token = ?', (_hash_reset_token(token),))
    conn.commit()
    conn.close()
    return True, None
