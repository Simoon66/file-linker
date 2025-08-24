import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Tuple

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_code TEXT UNIQUE NOT NULL,
                    file_id TEXT NOT NULL,
                    file_name TEXT,
                    file_type TEXT,
                    message_id INTEGER NOT NULL,
                    uploaded_by INTEGER NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    batch_id TEXT DEFAULT NULL
                )
            ''')
            
            # Create banned users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    banned_by INTEGER NOT NULL,
                    ban_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create batch groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_groups (
                    batch_id TEXT PRIMARY KEY,
                    batch_name TEXT,
                    created_by INTEGER NOT NULL,
                    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_file(self, file_id: str, file_name: str, file_type: str, 
                  message_id: int, uploaded_by: int, batch_id: str = None) -> str:
        """Save file information and return unique code"""
        file_code = str(uuid.uuid4())[:8]  # Short unique code
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO files (file_code, file_id, file_name, file_type, 
                                 message_id, uploaded_by, batch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (file_code, file_id, file_name, file_type, message_id, uploaded_by, batch_id))
            
            conn.commit()
        
        return file_code
    
    def get_file(self, file_code: str) -> Optional[Tuple]:
        """Get file information by code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_id, file_name, file_type, message_id, uploaded_by
                FROM files WHERE file_code = ?
            ''', (file_code,))
            
            result = cursor.fetchone()
            return result
    
    def create_batch_group(self, batch_name: str, created_by: int) -> str:
        """Create a new batch group and return batch_id"""
        batch_id = str(uuid.uuid4())[:8]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO batch_groups (batch_id, batch_name, created_by)
                VALUES (?, ?, ?)
            ''', (batch_id, batch_name, created_by))
            conn.commit()
        
        return batch_id
    
    def get_batch_files(self, batch_id: str) -> list:
        """Get all files in a batch"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT file_id, file_name, file_type, message_id, uploaded_by
                FROM files WHERE batch_id = ?
            ''', (batch_id,))
            return cursor.fetchall()
    
    def ban_user(self, user_id: int, banned_by: int):
        """Ban a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO banned_users (user_id, banned_by)
                VALUES (?, ?)
            ''', (user_id, banned_by))
            conn.commit()
    
    def unban_user(self, user_id: int):
        """Unban a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def get_file_stats(self) -> dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM files')
            total_files = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM banned_users')
            total_banned = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM batch_groups')
            total_batches = cursor.fetchone()[0]
            
            return {
                "total_files": total_files,
                "total_banned": total_banned,
                "total_batches": total_batches
            }
