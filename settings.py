#!/usr/bin/env python3
"""
Settings Management for Drafting Tools Suite
Manages users, departments, and application settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
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

class SettingsApp:
    def __init__(self, parent=None):
        self.settings_manager = SettingsManager()
        self.admin_session_id = None  # Track admin session
        
        if parent:
            self.root = parent
        else:
            self.root = tk.Tk()
            self.root.title("Settings - Drafting Tools")
            self.root.geometry("800x600")
        
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
        
        # Update status
        self.update_status()
    
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
