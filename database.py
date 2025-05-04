import sqlite3
from contextlib import contextmanager
from config import Config
import os

class Database:
    def __init__(self, db_name=Config.DATABASE_NAME):
        self.db_name = db_name
        self._initialize_db()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT CHECK(role IN ('admin', 'worker', 'pending')),
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица проектов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT NOT NULL,
                    description TEXT,
                    design_pdf_path TEXT,
                    lock_code TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица расчетов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calculations (
                    calculation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    project_id INTEGER,
                    material_type TEXT,
                    area REAL,
                    thickness REAL,
                    quantity REAL,
                    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (project_id) REFERENCES projects(project_id)
                )
            ''')
            
            # Таблица сообщений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    recipient_id INTEGER,
                    text TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(user_id),
                    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
    
    # Методы для работы с пользователями
    def add_user(self, user_id, username, first_name, last_name, role='pending'):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, role))
            conn.commit()
    
    def get_user(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def update_user_role(self, user_id, role):
        with self._get_connection() as conn:
            conn.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
            conn.commit()
    
    def get_pending_workers(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE role = "pending"')
            return cursor.fetchall()
    
    def get_all_workers(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE role = "worker"')
            return cursor.fetchall()
    
    # Методы для работы с проектами
    def add_project(self, address, description, design_pdf_path, lock_code, created_by):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (address, description, design_pdf_path, lock_code, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (address, description, design_pdf_path, lock_code, created_by))
            conn.commit()
            return cursor.lastrowid
    
    def get_projects(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, u.first_name, u.last_name 
                FROM projects p
                JOIN users u ON p.created_by = u.user_id
                ORDER BY p.created_at DESC
            ''')
            return cursor.fetchall()
    
    def get_project(self, project_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
            return cursor.fetchone()
    
    # Методы для работы с расчетами
    def add_calculation(self, user_id, project_id, material_type, area, thickness, quantity):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO calculations (user_id, project_id, material_type, area, thickness, quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, project_id, material_type, area, thickness, quantity))
            conn.commit()
    
    def get_user_calculations(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.*, p.address 
                FROM calculations c
                LEFT JOIN projects p ON c.project_id = p.project_id
                WHERE c.user_id = ?
                ORDER BY c.calculation_date DESC
            ''', (user_id,))
            return cursor.fetchall()
    
    # Методы для работы с сообщениями
    def add_message(self, sender_id, recipient_id, text):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO messages (sender_id, recipient_id, text)
                VALUES (?, ?, ?)
            ''', (sender_id, recipient_id, text))
            conn.commit()
    
    def get_user_messages(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, u.first_name as sender_name 
                FROM messages m
                JOIN users u ON m.sender_id = u.user_id
                WHERE m.recipient_id = ?
                ORDER BY m.sent_at DESC
            ''', (user_id,))
            return cursor.fetchall()