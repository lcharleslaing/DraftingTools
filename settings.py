#!/usr/bin/env python3
"""
Settings Management for Drafting Tools Suite
Manages users, departments, and application settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui_prefs import bind_tree_column_persistence
from database_setup import DatabaseManager
from database_setup import DatabaseManager
import sqlite3
import json
import os
from datetime import datetime

class SettingsManager:
    def __init__(self, db_path="drafting_tools.db"):
        self.db_path = db_path
        self.init_database()
        self.load_settings()
    
    def init_database(self):
        """Initialize settings tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                email TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create departments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color_code TEXT DEFAULT '#FF0000',
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create app_settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                updated_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admin_sessions table for tracking admin access
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Insert default departments if they don't exist
        default_departments = [
            ('Drafting', 'Drawing creation and updates', '#0000FF'),
            ('Engineering', 'Engineering review and approval', '#FF0000'),
            ('Production', 'Production operations review', '#00FF00'),
            ('Quality', 'Quality control and inspection', '#FFA500'),
            ('Management', 'Management oversight', '#800080')
        ]
        
        for dept_name, description, color in default_departments:
            cursor.execute('''
                INSERT OR IGNORE INTO departments (name, description, color_code)
                VALUES (?, ?, ?)
            ''', (dept_name, description, color))
        
        conn.commit()
        conn.close()
    
    def load_settings(self):
        """Load settings from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load current user
        cursor.execute('SELECT setting_value FROM app_settings WHERE setting_key = ?', ('current_user',))
        result = cursor.fetchone()
        self.current_user = result[0] if result else None
        
        # Load current department
        cursor.execute('SELECT setting_value FROM app_settings WHERE setting_key = ?', ('current_department',))
        result = cursor.fetchone()
        self.current_department = result[0] if result else None
        
        conn.close()
    
    def save_setting(self, key, value):
        """Save a setting to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO app_settings (setting_key, setting_value, updated_date)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def set_current_user(self, username):
        """Set the current user"""
        self.current_user = username
        self.save_setting('current_user', username)
    
    def set_current_department(self, department):
        """Set the current department"""
        self.current_department = department
        self.save_setting('current_department', department)
    
    def get_users(self):
        """Get all active users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, full_name, department, email
            FROM users 
            WHERE is_active = 1
            ORDER BY full_name
        ''')
        
        users = cursor.fetchall()
        conn.close()
        return users
    
    def get_departments(self):
        """Get all active departments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, description, color_code
            FROM departments 
            WHERE is_active = 1
            ORDER BY name
        ''')
        
        departments = cursor.fetchall()
        conn.close()
        return departments
    
    def add_user(self, username, full_name, department, email=""):
        """Add a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, full_name, department, email)
                VALUES (?, ?, ?, ?)
            ''', (username, full_name, department, email))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def add_department(self, name, description="", color_code="#FF0000"):
        """Add a new department"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO departments (name, description, color_code)
                VALUES (?, ?, ?)
            ''', (name, description, color_code))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def set_admin_password(self, password):
        """Set or update the admin password"""
        import hashlib
        # Hash the password for security
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.save_setting('admin_password', hashed_password)
        return True
    
    def verify_admin_password(self, password):
        """Verify the admin password"""
        import hashlib
        stored_hash = self.get_setting('admin_password')
        if not stored_hash:
            return False
        
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        return stored_hash == input_hash
    
    def get_setting(self, key):
        """Get a setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT setting_value FROM app_settings WHERE setting_key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def create_admin_session(self):
        """Create a new admin session"""
        import uuid
        from datetime import datetime, timedelta
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Set expiration to 8 hours from now
        expires_date = datetime.now() + timedelta(hours=8)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean up expired sessions first
        cursor.execute('DELETE FROM admin_sessions WHERE expires_date < ?', (datetime.now().isoformat(),))
        
        # Insert new session
        cursor.execute('''
            INSERT INTO admin_sessions (session_id, expires_date)
            VALUES (?, ?)
        ''', (session_id, expires_date.isoformat()))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def verify_admin_session(self, session_id):
        """Verify if admin session is valid"""
        if not session_id:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM admin_sessions 
            WHERE session_id = ? AND expires_date > ? AND is_active = 1
        ''', (session_id, datetime.now().isoformat()))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] > 0 if result else False
    
    def invalidate_admin_session(self, session_id):
        """Invalidate an admin session"""
        if not session_id:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE admin_sessions 
            SET is_active = 0 
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def delete_user(self, username):
        """Delete a user (admin only)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False
    
    def delete_department(self, name):
        """Delete a department (admin only)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM departments WHERE name = ?', (name,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            return False

    # ------------------------ People (Designers/Engineers) ------------------------
    def get_departments_map(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name")
        rows = cur.fetchall(); conn.close()
        return {name: did for did, name in rows}

    def get_designers(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM designers ORDER BY name")
        rows = [r[0] for r in cur.fetchall()]
        conn.close()
        return rows

    def get_designers_with_dept(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT d.name, COALESCE(dep.name, '') as department
                FROM designers d
                LEFT JOIN departments dep ON dep.id = d.department_id
                ORDER BY d.name
                """
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            cur.execute("SELECT name, '' as department FROM designers ORDER BY name")
            rows = cur.fetchall()
        conn.close(); return rows

    def add_designer(self, name, department: str = ""):
        if not name:
            return False
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            dep_id = None
            if department:
                cur.execute("SELECT id FROM departments WHERE name = ?", (department,))
                row = cur.fetchone(); dep_id = row[0] if row else None
            if dep_id is not None:
                cur.execute("INSERT OR IGNORE INTO designers(name, department_id) VALUES (?, ?)", (name.strip(), dep_id))
            else:
                cur.execute("INSERT OR IGNORE INTO designers(name) VALUES (?)", (name.strip(),))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def delete_designer(self, name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM designers WHERE name = ?", (name,))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def rename_designer(self, old_name, new_name):
        if not new_name:
            return False
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("UPDATE designers SET name = ? WHERE name = ?", (new_name.strip(), old_name))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def set_designer_department(self, name, department: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            dep_id = None
            if department:
                cur.execute("SELECT id FROM departments WHERE name = ?", (department,))
                row = cur.fetchone(); dep_id = row[0] if row else None
            cur.execute("UPDATE designers SET department_id = ? WHERE name = ?", (dep_id, name))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def get_engineers(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM engineers ORDER BY name")
        rows = [r[0] for r in cur.fetchall()]
        conn.close()
        return rows

    def get_engineers_with_dept(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT e.name, COALESCE(dep.name, '') as department
                FROM engineers e
                LEFT JOIN departments dep ON dep.id = e.department_id
                ORDER BY e.name
                """
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            cur.execute("SELECT name, '' as department FROM engineers ORDER BY name")
            rows = cur.fetchall()
        conn.close(); return rows

    def add_engineer(self, name, department: str = ""):
        if not name:
            return False
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            dep_id = None
            if department:
                cur.execute("SELECT id FROM departments WHERE name = ?", (department,))
                row = cur.fetchone(); dep_id = row[0] if row else None
            if dep_id is not None:
                cur.execute("INSERT OR IGNORE INTO engineers(name, department_id) VALUES (?, ?)", (name.strip(), dep_id))
            else:
                cur.execute("INSERT OR IGNORE INTO engineers(name) VALUES (?)", (name.strip(),))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def delete_engineer(self, name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM engineers WHERE name = ?", (name,))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def rename_engineer(self, old_name, new_name):
        if not new_name:
            return False
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute("UPDATE engineers SET name = ? WHERE name = ?", (new_name.strip(), old_name))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    def set_engineer_department(self, name, department: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            dep_id = None
            if department:
                cur.execute("SELECT id FROM departments WHERE name = ?", (department,))
                row = cur.fetchone(); dep_id = row[0] if row else None
            cur.execute("UPDATE engineers SET department_id = ? WHERE name = ?", (dep_id, name))
            conn.commit(); conn.close(); return True
        except Exception:
            conn.close(); return False

    # ---------------- Consolidated People helpers ----------------
    def get_all_people_with_dept(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT d.name AS name, COALESCE(dep.name,'') AS department, 'Designer' AS type
                FROM designers d
                LEFT JOIN departments dep ON dep.id = d.department_id
                UNION ALL
                SELECT e.name AS name, COALESCE(dep.name,'') AS department, 'Engineer' AS type
                FROM engineers e
                LEFT JOIN departments dep ON dep.id = e.department_id
                ORDER BY name
                """
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            cur.execute("SELECT name, '' as department, 'Designer' as type FROM designers")
            drows = cur.fetchall()
            cur.execute("SELECT name, '' as department, 'Engineer' as type FROM engineers")
            erows = cur.fetchall(); rows = sorted(drows + erows, key=lambda r: r[0])
        conn.close(); return rows

    def get_all_people_with_dept_filtered(self, department: str|None):
        if not department or department in ('<All>', 'All Departments'):
            return self.get_all_people_with_dept()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT d.name, COALESCE(dep.name,''), 'Designer'
                FROM designers d
                LEFT JOIN departments dep ON dep.id = d.department_id
                WHERE dep.name = ?
                UNION ALL
                SELECT e.name, COALESCE(dep.name,''), 'Engineer'
                FROM engineers e
                LEFT JOIN departments dep ON dep.id = e.department_id
                WHERE dep.name = ?
                ORDER BY 1
                """,
                (department, department)
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            rows = []
        conn.close(); return rows

    def add_person(self, name: str, person_type: str, department: str = ""):
        if (person_type or '').lower().startswith('des'):
            return self.add_designer(name, department)
        return self.add_engineer(name, department)

    def delete_person(self, name: str, person_type: str):
        if (person_type or '').lower().startswith('des'):
            return self.delete_designer(name)
        return self.delete_engineer(name)

    def rename_person(self, old_name: str, new_name: str, person_type: str):
        if (person_type or '').lower().startswith('des'):
            return self.rename_designer(old_name, new_name)
        return self.rename_engineer(old_name, new_name)

    def set_person_department(self, name: str, person_type: str, department: str):
        if (person_type or '').lower().startswith('des'):
            return self.set_designer_department(name, department)
        return self.set_engineer_department(name, department)

class SettingsApp:
    def __init__(self, parent=None):
        self.settings_manager = SettingsManager()
        try:
            DatabaseManager(self.settings_manager.db_path)
        except Exception:
            pass
        self.admin_session_id = None  # Track admin session
        
        if parent:
            self.root = parent
        else:
            self.root = tk.Tk()
            self.root.title("Settings - Drafting Tools")
        # Start maximized/fullscreen like other apps
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                pass
        try:
            self.root.minsize(1000, 700)
        except Exception:
            pass
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        """Create the settings interface"""
        # Main notebook for different settings sections
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Users tab
        self.users_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.users_frame, text="Users")
        self.create_users_tab()
        
        # Departments tab
        self.departments_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.departments_frame, text="Departments")
        self.create_departments_tab()
        
        # Current User tab
        self.current_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.current_frame, text="Current User")
        self.create_current_user_tab()

        # Admin tab
        self.admin_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.admin_frame, text="🔐 Admin")
        self.create_admin_tab()

        # People tab (Unified)
        self.people_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.people_frame, text="People")
        self.create_people_tab()
    
    def create_users_tab(self):
        """Create users management tab"""
        # Add user section
        add_frame = ttk.LabelFrame(self.users_frame, text="Add New User", padding=10)
        add_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(add_frame, text="Username:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.username_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.username_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Full Name:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.fullname_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.fullname_var, width=25).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Department:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.user_dept_var = tk.StringVar()
        self.user_dept_combo = ttk.Combobox(add_frame, textvariable=self.user_dept_var, width=18)
        self.user_dept_combo.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Email:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.email_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.email_var, width=25).grid(row=1, column=3, padx=5, pady=2)
        
        ttk.Button(add_frame, text="Add User", command=self.add_user).grid(row=2, column=0, columnspan=4, pady=10)
        
        # Admin controls
        admin_frame = ttk.LabelFrame(self.users_frame, text="Admin Controls", padding=10)
        admin_frame.pack(fill="x", padx=10, pady=5)
        
        self.admin_btn_frame = ttk.Frame(admin_frame)
        self.admin_btn_frame.pack(fill="x")
        
        self.delete_user_btn = ttk.Button(self.admin_btn_frame, text="Delete Selected User", 
                                         command=self.delete_user, state="disabled")
        self.delete_user_btn.pack(side="left", padx=5)
        
        self.admin_status_label = ttk.Label(self.admin_btn_frame, text="Admin access required", 
                                           foreground="red")
        self.admin_status_label.pack(side="left", padx=10)
        
        # Users list
        list_frame = ttk.LabelFrame(self.users_frame, text="Current Users", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview for users
        columns = ("username", "full_name", "department", "email")
        self.users_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("full_name", text="Full Name")
        self.users_tree.heading("department", text="Department")
        self.users_tree.heading("email", text="Email")
        
        self.users_tree.column("username", width=120)
        self.users_tree.column("full_name", width=200)
        self.users_tree.column("department", width=120)
        self.users_tree.column("email", width=200)
        
        self.users_tree.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        try:
            bind_tree_column_persistence(self.users_tree, 'settings.users_tree', self.root)
        except Exception:
            pass
    
    def create_departments_tab(self):
        """Create departments management tab"""
        # Add department section
        add_frame = ttk.LabelFrame(self.departments_frame, text="Add New Department", padding=10)
        add_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(add_frame, text="Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.dept_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.dept_name_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Description:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.dept_desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.dept_desc_var, width=30).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(add_frame, text="Color Code:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.dept_color_var = tk.StringVar(value="#FF0000")
        ttk.Entry(add_frame, textvariable=self.dept_color_var, width=20).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(add_frame, text="Add Department", command=self.add_department).grid(row=2, column=0, columnspan=4, pady=10)
        
        # Admin controls
        admin_frame = ttk.LabelFrame(self.departments_frame, text="Admin Controls", padding=10)
        admin_frame.pack(fill="x", padx=10, pady=5)
        
        self.dept_admin_btn_frame = ttk.Frame(admin_frame)
        self.dept_admin_btn_frame.pack(fill="x")
        
        self.delete_dept_btn = ttk.Button(self.dept_admin_btn_frame, text="Delete Selected Department", 
                                         command=self.delete_department, state="disabled")
        self.delete_dept_btn.pack(side="left", padx=5)
        
        self.dept_admin_status_label = ttk.Label(self.dept_admin_btn_frame, text="Admin access required", 
                                                foreground="red")
        self.dept_admin_status_label.pack(side="left", padx=10)
        
        # Departments list
        list_frame = ttk.LabelFrame(self.departments_frame, text="Current Departments", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview for departments
        columns = ("name", "description", "color_code")
        self.dept_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.dept_tree.heading("name", text="Name")
        self.dept_tree.heading("description", text="Description")
        self.dept_tree.heading("color_code", text="Color Code")
        
        self.dept_tree.column("name", width=150)
        self.dept_tree.column("description", width=300)
        self.dept_tree.column("color_code", width=100)
        
        self.dept_tree.pack(fill="both", expand=True)
        try:
            bind_tree_column_persistence(self.dept_tree, 'settings.dept_tree', self.root)
        except Exception:
            pass
    
    def create_current_user_tab(self):
        """Create current user selection tab"""
        main_frame = ttk.Frame(self.current_frame)
        main_frame.pack(expand=True)
        
        # Current user selection
        user_frame = ttk.LabelFrame(main_frame, text="Select Current User", padding=20)
        user_frame.pack(pady=20)
        
        ttk.Label(user_frame, text="Username:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.current_user_var = tk.StringVar()
        self.current_user_combo = ttk.Combobox(user_frame, textvariable=self.current_user_var, width=30)
        self.current_user_combo.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(user_frame, text="Department:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.current_dept_var = tk.StringVar()
        self.current_dept_combo = ttk.Combobox(user_frame, textvariable=self.current_dept_var, width=30)
        self.current_dept_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Button(user_frame, text="Save Current User", command=self.save_current_user).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Status display
        status_frame = ttk.LabelFrame(main_frame, text="Current Status", padding=20)
        status_frame.pack(fill="x", pady=20)
        
        self.status_text = tk.Text(status_frame, height=6, width=60)
        self.status_text.pack(fill="both", expand=True)
    
    def load_data(self):
        """Load data into the interface"""
        # Load users
        users = self.settings_manager.get_users()
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        for user in users:
            self.users_tree.insert("", "end", values=user)
        
        # Load departments
        departments = self.settings_manager.get_departments()
        for item in self.dept_tree.get_children():
            self.dept_tree.delete(item)
        
        for dept in departments:
            self.dept_tree.insert("", "end", values=dept)
        
        # Load current user data
        users_list = [user[0] for user in users]
        self.current_user_combo['values'] = users_list
        if self.settings_manager.current_user:
            self.current_user_var.set(self.settings_manager.current_user)
        
        dept_list = [dept[0] for dept in departments]
        self.current_dept_combo['values'] = dept_list
        if self.settings_manager.current_department:
            self.current_dept_var.set(self.settings_manager.current_department)
        
        # Update user department combo
        self.user_dept_combo['values'] = dept_list
        # Update add-person department combos to include all created departments
        if hasattr(self, 'designers_dep_combo_add'):
            self.designers_dep_combo_add['values'] = dept_list
        if hasattr(self, 'engineers_dep_combo_add'):
            self.engineers_dep_combo_add['values'] = dept_list
        
        # Update status
        self.update_status()

        # Load unified people list
        if hasattr(self, 'people_tree'):
            self._reload_people_tree()

    # ---------------- People Tab ----------------
    def create_people_tab(self):
        container = ttk.Frame(self.people_frame, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)

        # Filter row
        filt = ttk.Frame(container)
        filt.pack(fill=tk.X)
        ttk.Label(filt, text="Filter by Department:").pack(side=tk.LEFT)
        self.people_filter_var = tk.StringVar(value='All Departments')
        self.people_filter_combo = ttk.Combobox(filt, textvariable=self.people_filter_var, width=24, state='readonly')
        dept_names = ['All Departments'] + [d[0] for d in self.settings_manager.get_departments()]
        self.people_filter_combo['values'] = dept_names
        self.people_filter_combo.pack(side=tk.LEFT, padx=(6,0))
        self.people_filter_combo.bind('<<ComboboxSelected>>', lambda _e: self._reload_people_tree())

        # Add row
        add = ttk.Frame(container)
        add.pack(fill=tk.X, pady=(6,6))
        ttk.Label(add, text="Name:").pack(side=tk.LEFT)
        self.person_name_var = tk.StringVar()
        ttk.Entry(add, textvariable=self.person_name_var, width=22).pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(add, text="Type:").pack(side=tk.LEFT)
        self.person_type_var = tk.StringVar(value='Designer')
        self.person_type_combo = ttk.Combobox(add, textvariable=self.person_type_var, values=['Designer','Engineer'], width=12, state='readonly')
        self.person_type_combo.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(add, text="Department:").pack(side=tk.LEFT)
        self.person_dep_var = tk.StringVar()
        self.person_dep_combo = ttk.Combobox(add, textvariable=self.person_dep_var, width=18, state='readonly')
        self.person_dep_combo['values'] = [d[0] for d in self.settings_manager.get_departments()]
        self.person_dep_combo.pack(side=tk.LEFT, padx=(4,8))
        ttk.Button(add, text="Add", command=self._on_add_person).pack(side=tk.LEFT)

        # Tree
        cols = ('name','type','department')
        self.people_tree = ttk.Treeview(container, columns=cols, show='headings', height=16)
        for c in cols:
            self.people_tree.heading(c, text=c.capitalize())
        self.people_tree.pack(fill=tk.BOTH, expand=True, pady=(6,6))

        # Inline edits: name and department
        def on_double_click(event):
            item = self.people_tree.selection()
            if not item:
                return
            col = self.people_tree.identify_column(event.x)
            if col == '#1':
                # edit name
                x,y,w,h = self.people_tree.bbox(item[0], '#1')
                current = self.people_tree.set(item[0], 'name'); ptype = self.people_tree.set(item[0], 'type')
                e = ttk.Entry(self.people_tree); e.place(x=x,y=y,width=w,height=h); e.insert(0,current); e.focus_set()
                def commit(_e=None):
                    new_val = e.get().strip(); e.destroy()
                    if new_val and new_val != current:
                        self.settings_manager.rename_person(current, new_val, ptype); self._reload_people_tree()
                e.bind('<Return>', commit); e.bind('<FocusOut>', lambda _e: e.destroy())
            elif col == '#3':
                # change department
                x,y,w,h = self.people_tree.bbox(item[0], '#3')
                current = self.people_tree.set(item[0], 'department'); name = self.people_tree.set(item[0], 'name'); ptype = self.people_tree.set(item[0], 'type')
                cb = ttk.Combobox(self.people_tree, values=[d[0] for d in self.settings_manager.get_departments()], state='readonly')
                cb.place(x=x,y=y,width=w,height=h)
                if current:
                    cb.set(current)
                cb.focus_set()
                def commit_dep(_e=None):
                    val = cb.get().strip(); cb.destroy();
                    if val:
                        self.settings_manager.set_person_department(name, ptype, val); self._reload_people_tree()
                cb.bind('<<ComboboxSelected>>', commit_dep); cb.bind('<FocusOut>', lambda _e: cb.destroy())
        self.people_tree.bind('<Double-1>', on_double_click)

        # Actions
        actions = ttk.Frame(container)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text='Delete Selected', command=self._on_delete_person).pack(side=tk.LEFT)

    def _reload_people_tree(self):
        dept = self.people_filter_var.get() if hasattr(self, 'people_filter_var') else 'All Departments'
        rows = self.settings_manager.get_all_people_with_dept_filtered(dept)
        for iid in self.people_tree.get_children():
            self.people_tree.delete(iid)
        for name, dep, ptype in rows:
            self.people_tree.insert('', 'end', values=(name, ptype, dep))

    def _on_add_person(self):
        name = (self.person_name_var.get() or '').strip()
        ptype = (self.person_type_var.get() or 'Designer').strip()
        dep = (self.person_dep_var.get() or '').strip()
        if not name:
            messagebox.showerror('Error', 'Enter a name'); return
        if not dep:
            messagebox.showerror('Error', 'Choose a department'); return
        if self.settings_manager.add_person(name, ptype, dep):
            self.person_name_var.set(''); self.person_dep_var.set(''); self._reload_people_tree()
        else:
            messagebox.showerror('Error', 'Failed to add person (duplicate or DB error)')

    def _on_delete_person(self):
        sel = self.people_tree.selection()
        if not sel:
            return
        name = self.people_tree.set(sel[0], 'name'); ptype = self.people_tree.set(sel[0], 'type')
        if messagebox.askyesno('Delete', f"Delete {ptype.lower()} '{name}'?"):
            if self.settings_manager.delete_person(name, ptype):
                self._reload_people_tree()
            else:
                messagebox.showerror('Error', 'Failed to delete person')

    def _build_people_panel(self, parent, kind='designer'):
        add_frame = ttk.Frame(parent)
        add_frame.pack(fill=tk.X)
        ttk.Label(add_frame, text="Name:").pack(side=tk.LEFT)
        var = tk.StringVar()
        entry = ttk.Entry(add_frame, textvariable=var, width=24)
        entry.pack(side=tk.LEFT, padx=(4,6))
        # Department selector for add
        ttk.Label(add_frame, text="Department:").pack(side=tk.LEFT, padx=(8,2))
        dep_var = tk.StringVar()
        dep_combo = ttk.Combobox(add_frame, textvariable=dep_var, width=18, state='readonly')
        dep_names = [d[0] for d in self.settings_manager.get_departments()]
        dep_combo['values'] = dep_names
        dep_combo.pack(side=tk.LEFT)
        if kind == 'designer':
            ttk.Button(add_frame, text="Add", command=lambda: self._on_add_designer(var, dep_var)).pack(side=tk.LEFT, padx=(6,0))
            self.designers_dep_combo_add = dep_combo
        else:
            ttk.Button(add_frame, text="Add", command=lambda: self._on_add_engineer(var, dep_var)).pack(side=tk.LEFT, padx=(6,0))
            self.engineers_dep_combo_add = dep_combo

        cols = ("name", "department")
        tree = ttk.Treeview(parent, columns=cols, show='headings', height=12)
        tree.heading('name', text='Name')
        tree.heading('department', text='Department')
        tree.pack(fill=tk.BOTH, expand=True, pady=(6,6))

        # Assign Department controls
        assign_frame = ttk.Frame(parent)
        assign_frame.pack(fill=tk.X, pady=(0,6))
        ttk.Label(assign_frame, text="Set Department for Selected:").pack(side=tk.LEFT)
        set_dep_var = tk.StringVar()
        set_dep_combo = ttk.Combobox(assign_frame, textvariable=set_dep_var, width=18, state='readonly')
        set_dep_combo['values'] = [d[0] for d in self.settings_manager.get_departments()]
        set_dep_combo.pack(side=tk.LEFT, padx=(4,6))
        if kind == 'designer':
            ttk.Button(assign_frame, text="Assign", command=lambda: self._on_assign_designer_department(tree, set_dep_var)).pack(side=tk.LEFT)
            self.designers_dep_combo_assign = set_dep_combo
        else:
            ttk.Button(assign_frame, text="Assign", command=lambda: self._on_assign_engineer_department(tree, set_dep_var)).pack(side=tk.LEFT)
            self.engineers_dep_combo_assign = set_dep_combo

        btns = ttk.Frame(parent)
        btns.pack(fill=tk.X)
        if kind == 'designer':
            self.designers_tree = tree
            ttk.Button(btns, text="Delete Selected", command=self._on_delete_designer).pack(side=tk.LEFT)
        else:
            self.engineers_tree = tree
            ttk.Button(btns, text="Delete Selected", command=self._on_delete_engineer).pack(side=tk.LEFT)

        # Inline edit on double-click
        def on_double_click(event):
            item = tree.selection()
            if not item:
                return
            col_idx = tree.identify_column(event.x)
            if col_idx == '#1':
                # Edit name
                x, y, w, h = tree.bbox(item[0], '#1')
                current = tree.set(item[0], 'name')
                e = ttk.Entry(tree)
                e.place(x=x, y=y, width=w, height=h)
                e.insert(0, current)
                e.focus_set()
                def commit(_ev=None):
                    new_val = e.get().strip(); e.destroy()
                    if not new_val or new_val == current:
                        return
                    if kind == 'designer':
                        self.settings_manager.rename_designer(current, new_val)
                    else:
                        self.settings_manager.rename_engineer(current, new_val)
                    self.load_data()
                e.bind('<Return>', commit)
                e.bind('<FocusOut>', lambda _e: e.destroy())
            elif col_idx == '#2':
                # Change department via combobox overlay
                x, y, w, h = tree.bbox(item[0], '#2')
                current_name = tree.set(item[0], 'name')
                current_dep = tree.set(item[0], 'department')
                cb = ttk.Combobox(tree, values=[d[0] for d in self.settings_manager.get_departments()], state='readonly')
                cb.place(x=x, y=y, width=w, height=h)
                if current_dep:
                    cb.set(current_dep)
                cb.focus_set()
                def commit_dep(_ev=None):
                    val = cb.get().strip(); cb.destroy()
                    if kind == 'designer':
                        self.settings_manager.set_designer_department(current_name, val)
                    else:
                        self.settings_manager.set_engineer_department(current_name, val)
                    self.load_data()
                cb.bind('<<ComboboxSelected>>', commit_dep)
                cb.bind('<FocusOut>', lambda _e: cb.destroy())
        tree.bind('<Double-1>', on_double_click)

    def _on_add_designer(self, var, dep_var):
        name = (var.get() or '').strip()
        if not name:
            return
        dep = (dep_var.get() or '').strip()
        if self.settings_manager.add_designer(name, dep):
            var.set(''); dep_var.set(''); self.load_data()
        else:
            messagebox.showerror("Error", "Failed to add designer (duplicate or DB error)")

    def _on_delete_designer(self):
        sel = self.designers_tree.selection()
        if not sel:
            return
        name = self.designers_tree.set(sel[0], 'name')
        if messagebox.askyesno("Delete", f"Delete designer '{name}'?"):
            if self.settings_manager.delete_designer(name):
                self.load_data()
            else:
                messagebox.showerror("Error", "Failed to delete designer")

    def _on_add_engineer(self, var, dep_var):
        name = (var.get() or '').strip()
        if not name:
            return
        dep = (dep_var.get() or '').strip()
        if self.settings_manager.add_engineer(name, dep):
            var.set(''); dep_var.set(''); self.load_data()
        else:
            messagebox.showerror("Error", "Failed to add engineer (duplicate or DB error)")

    def _on_delete_engineer(self):
        sel = self.engineers_tree.selection()
        if not sel:
            return
        name = self.engineers_tree.set(sel[0], 'name')
        if messagebox.askyesno("Delete", f"Delete engineer '{name}'?"):
            if self.settings_manager.delete_engineer(name):
                self.load_data()
            else:
                messagebox.showerror("Error", "Failed to delete engineer")

    def _on_assign_designer_department(self, tree, dep_var):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a designer first.")
            return
        name = tree.set(sel[0], 'name')
        dep = (dep_var.get() or '').strip()
        if not dep:
            messagebox.showerror("Department", "Choose a department.")
            return
        if self.settings_manager.set_designer_department(name, dep):
            self.load_data()
        else:
            messagebox.showerror("Error", "Failed to assign department")

    def _on_assign_engineer_department(self, tree, dep_var):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select an engineer first.")
            return
        name = tree.set(sel[0], 'name')
        dep = (dep_var.get() or '').strip()
        if not dep:
            messagebox.showerror("Department", "Choose a department.")
            return
        if self.settings_manager.set_engineer_department(name, dep):
            self.load_data()
        else:
            messagebox.showerror("Error", "Failed to assign department")
    
    def add_user(self):
        """Add a new user"""
        username = self.username_var.get().strip()
        full_name = self.fullname_var.get().strip()
        department = self.user_dept_var.get().strip()
        email = self.email_var.get().strip()
        
        if not all([username, full_name, department]):
            messagebox.showerror("Error", "Please fill in Username, Full Name, and Department")
            return
        
        if self.settings_manager.add_user(username, full_name, department, email):
            messagebox.showinfo("Success", f"User '{username}' added successfully!")
            self.clear_user_form()
            self.load_data()
        else:
            messagebox.showerror("Error", f"Username '{username}' already exists!")
    
    def add_department(self):
        """Add a new department"""
        name = self.dept_name_var.get().strip()
        description = self.dept_desc_var.get().strip()
        color = self.dept_color_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a department name")
            return
        
        if self.settings_manager.add_department(name, description, color):
            messagebox.showinfo("Success", f"Department '{name}' added successfully!")
            self.clear_department_form()
            self.load_data()
        else:
            messagebox.showerror("Error", f"Department '{name}' already exists!")
    
    def save_current_user(self):
        """Save current user selection"""
        username = self.current_user_var.get().strip()
        department = self.current_dept_var.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please select a username")
            return
        
        self.settings_manager.set_current_user(username)
        if department:
            self.settings_manager.set_current_department(department)
        
        messagebox.showinfo("Success", f"Current user set to: {username}")
        self.update_status()
    
    def clear_user_form(self):
        """Clear the user form"""
        self.username_var.set("")
        self.fullname_var.set("")
        self.user_dept_var.set("")
        self.email_var.set("")
    
    def clear_department_form(self):
        """Clear the department form"""
        self.dept_name_var.set("")
        self.dept_desc_var.set("")
        self.dept_color_var.set("#FF0000")
    
    def update_status(self):
        """Update the status display"""
        self.status_text.delete(1.0, tk.END)
        
        status = f"Current User: {self.settings_manager.current_user or 'Not Set'}\n"
        status += f"Current Department: {self.settings_manager.current_department or 'Not Set'}\n\n"
        
        users = self.settings_manager.get_users()
        status += f"Total Users: {len(users)}\n"
        
        departments = self.settings_manager.get_departments()
        status += f"Total Departments: {len(departments)}\n\n"
        
        status += "Available Users:\n"
        for user in users:
            status += f"  • {user[1]} ({user[0]}) - {user[2]}\n"
        
        self.status_text.insert(1.0, status)
    
    def set_admin_password(self):
        """Set or change the admin password"""
        password = self.new_password_var.get().strip()
        
        if not password:
            messagebox.showerror("Error", "Please enter a password")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long")
            return
        
        if self.settings_manager.set_admin_password(password):
            messagebox.showinfo("Success", "Admin password set successfully!")
            self.new_password_var.set("")
            self.update_session_info()
        else:
            messagebox.showerror("Error", "Failed to set admin password")
    
    def login_admin(self):
        """Login as admin"""
        password = self.login_password_var.get().strip()
        
        if not password:
            messagebox.showerror("Error", "Please enter the admin password")
            return
        
        if self.settings_manager.verify_admin_password(password):
            # Create admin session
            self.admin_session_id = self.settings_manager.create_admin_session()
            self.admin_login_status.config(text="Logged in as Admin", foreground="green")
            self.login_password_var.set("")
            
            # Enable admin controls
            self.enable_admin_controls(True)
            self.update_session_info()
            
            messagebox.showinfo("Success", "Admin access granted!")
        else:
            messagebox.showerror("Error", "Invalid admin password")
            self.login_password_var.set("")
    
    def logout_admin(self):
        """Logout from admin session"""
        if self.admin_session_id:
            self.settings_manager.invalidate_admin_session(self.admin_session_id)
            self.admin_session_id = None
        
        self.admin_login_status.config(text="Not logged in", foreground="red")
        self.enable_admin_controls(False)
        self.update_session_info()
        messagebox.showinfo("Logged Out", "Admin session ended")
    
    def enable_admin_controls(self, enabled):
        """Enable or disable admin controls"""
        state = "normal" if enabled else "disabled"
        self.delete_user_btn.config(state=state)
        self.delete_dept_btn.config(state=state)
        
        if enabled:
            self.admin_status_label.config(text="Admin access active", foreground="green")
            self.dept_admin_status_label.config(text="Admin access active", foreground="green")
        else:
            self.admin_status_label.config(text="Admin access required", foreground="red")
            self.dept_admin_status_label.config(text="Admin access required", foreground="red")
    
    def update_session_info(self):
        """Update session information display"""
        self.session_info_text.delete(1.0, tk.END)
        
        if self.admin_session_id and self.settings_manager.verify_admin_session(self.admin_session_id):
            info = "✅ ADMIN SESSION ACTIVE\n\n"
            info += f"Session ID: {self.admin_session_id[:8]}...\n"
            info += f"Status: Active\n"
            info += f"Expires: 8 hours from login\n\n"
            info += "Admin controls are enabled for:\n"
            info += "• Delete users\n"
            info += "• Delete departments\n"
            info += "• Manage all settings"
        else:
            info = "❌ NO ADMIN SESSION\n\n"
            info += "To access admin controls:\n"
            info += "1. Set an admin password (if not set)\n"
            info += "2. Enter the password to login\n"
            info += "3. Admin session lasts 8 hours\n\n"
            info += "Admin controls allow:\n"
            info += "• Delete users\n"
            info += "• Delete departments\n"
            info += "• Manage all settings"
        
        self.session_info_text.insert(1.0, info)
    
    def delete_user(self):
        """Delete selected user (admin only)"""
        if not self.admin_session_id or not self.settings_manager.verify_admin_session(self.admin_session_id):
            messagebox.showerror("Error", "Admin access required")
            return
        
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        
        item = self.users_tree.item(selection[0])
        username = item['values'][0]
        full_name = item['values'][1]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete user '{full_name}' ({username})?\n\n"
                              "This action cannot be undone!"):
            if self.settings_manager.delete_user(username):
                messagebox.showinfo("Success", f"User '{username}' deleted successfully!")
                self.load_data()
            else:
                messagebox.showerror("Error", f"Failed to delete user '{username}'")
    
    def delete_department(self):
        """Delete selected department (admin only)"""
        if not self.admin_session_id or not self.settings_manager.verify_admin_session(self.admin_session_id):
            messagebox.showerror("Error", "Admin access required")
            return
        
        selection = self.dept_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a department to delete")
            return
        
        item = self.dept_tree.item(selection[0])
        dept_name = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete department '{dept_name}'?\n\n"
                              "This action cannot be undone!"):
            if self.settings_manager.delete_department(dept_name):
                messagebox.showinfo("Success", f"Department '{dept_name}' deleted successfully!")
                self.load_data()
            else:
                messagebox.showerror("Error", f"Failed to delete department '{dept_name}'")
    
    def create_admin_tab(self):
        """Create admin management tab"""
        # Password management section
        password_frame = ttk.LabelFrame(self.admin_frame, text="Admin Password Management", padding=20)
        password_frame.pack(fill="x", padx=10, pady=10)
        
        # Set new password
        ttk.Label(password_frame, text="Set/Change Admin Password:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.new_password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=self.new_password_var, show="*", width=30)
        password_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(password_frame, text="Set Password", command=self.set_admin_password).grid(row=0, column=2, padx=5, pady=5)
        
        # Admin login section
        login_frame = ttk.LabelFrame(self.admin_frame, text="Admin Login", padding=20)
        login_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(login_frame, text="Enter Admin Password:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.login_password_var = tk.StringVar()
        login_entry = ttk.Entry(login_frame, textvariable=self.login_password_var, show="*", width=30)
        login_entry.grid(row=0, column=1, padx=5, pady=5)
        login_entry.bind('<Return>', lambda e: self.login_admin())
        
        ttk.Button(login_frame, text="Login", command=self.login_admin).grid(row=0, column=2, padx=5, pady=5)
        
        # Admin status
        self.admin_login_status = ttk.Label(login_frame, text="Not logged in", foreground="red")
        self.admin_login_status.grid(row=1, column=0, columnspan=3, pady=10)
        
        # Session info
        session_frame = ttk.LabelFrame(self.admin_frame, text="Session Information", padding=20)
        session_frame.pack(fill="x", padx=10, pady=10)
        
        self.session_info_text = tk.Text(session_frame, height=6, width=60)
        self.session_info_text.pack(fill="both", expand=True)
        
        # Logout button
        ttk.Button(session_frame, text="Logout", command=self.logout_admin).pack(pady=10)
        
        # Update session info
        self.update_session_info()

def main():
    """Main function to run settings app standalone"""
    app = SettingsApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()
