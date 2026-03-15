import os
import sqlite3
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from datetime import datetime
from pathlib import Path

def derive_fernet_key(password: str, salt: bytes) -> Fernet:
    """
    Derives a Fernet key from a password and salt using PBKDF2.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)

def init_db(db_path: str):
    """
    Initializes the SQLite database and ensures the directory exists.
    """
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vault_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                ciphertext TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def get_or_create_salt(db_path: str) -> bytes:
    """
    Retrieves the salt from the meta table or generates a new one if it doesn't exist.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM meta WHERE key = 'salt'")
        row = cursor.fetchone()
        if row:
            return bytes.fromhex(row[0])
        else:
            salt = os.urandom(16)
            cursor.execute("INSERT INTO meta (key, value) VALUES ('salt', ?)", (salt.hex(),))
            conn.commit()
            return salt

def encrypt_and_save(fernet: Fernet, db_path: str, label: str, plaintext: str):
    """
    Encrypts the plaintext and saves it to the database under the given label.
    """
    label = label.strip().lower()
    ciphertext = fernet.encrypt(plaintext.encode()).decode()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vault_entries (label, ciphertext, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(label) DO UPDATE SET
                ciphertext = excluded.ciphertext,
                updated_at = excluded.updated_at
        ''', (label, ciphertext, datetime.utcnow().isoformat()))
        conn.commit()

def decrypt_entry(fernet: Fernet, db_path: str, label: str) -> str | None:
    """
    Decrypts the entry for the given label.
    """
    label = label.strip().lower()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ciphertext FROM vault_entries WHERE label = ?", (label,))
        row = cursor.fetchone()
        if row:
            try:
                decrypted = fernet.decrypt(row[0].encode()).decode()
                return decrypted
            except Exception:
                return None
    return None

def get_all_labels(db_path: str) -> list[str]:
    """
    Returns a list of all labels in the vault, sorted alphabetically.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT label FROM vault_entries ORDER BY label ASC")
        return [row[0] for row in cursor.fetchall()]

def search_entries(fernet: Fernet, db_path: str, keywords: list[str]) -> dict[str, str]:
    """
    Searches for entries matching the keywords and returns a dictionary of label: decrypted_plaintext.
    """
    results = {}
    if not keywords:
        return results
        
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for keyword in keywords:
            keyword = f"%{keyword.strip().lower()}%"
            cursor.execute("SELECT label, ciphertext FROM vault_entries WHERE label LIKE ?", (keyword,))
            for label, ciphertext in cursor.fetchall():
                if label not in results:
                    try:
                        decrypted = fernet.decrypt(ciphertext.encode()).decode()
                        results[label] = decrypted
                    except Exception:
                        continue
    return results

def delete_entry(db_path: str, label: str) -> bool:
    """
    Deletes the entry for the given label.
    """
    label = label.strip().lower()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vault_entries WHERE label = ?", (label,))
        conn.commit()
        return cursor.rowcount > 0
