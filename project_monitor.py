import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import subprocess
import platform
from database_setup import DatabaseManager
from scroll_utils import bind_mousewheel_to_treeview
from ui_prefs import bind_tree_column_persistence
from notes_utils import open_add_note_dialog
from app_nav import add_app_bar
from help_utils import add_help_button
from directory_picker import DirectoryPicker

class ProjectMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Project File Monitor - Drafting Tools")
        self.root.geometry("1400x900")
        
        # Try to maximize window
        try:
            self.root.state('zoomed')
        except:
            pass
        
        self.db_manager = DatabaseManager()
        self.current_project = None
        self.file_data = {}  # Store file metadata
        self.last_scan_time = None
        
        # Initialize database tables
        self.init_database()
        
        # Load existing project data
        self.load_project_data()
        
        try:
            add_app_bar(self.root, current_app='project_monitor')
        except Exception:
            pass
        self.create_widgets()
        self.refresh_projects()
        
        # Start background monitoring
        self.start_background_monitoring()
        
        # Clean up any duplicate deletion records
        self.cleanup_duplicate_deletions()
        
        # Clean up any duplicate file changes records
        self.cleanup_duplicate_changes()
        
        # Initialize logging
        self.setup_logging()
    
    def cleanup_duplicate_deletions(self):
        """Clean up duplicate deletion records in the database"""
        try:
            conn = self.get_database_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # Find and remove duplicate deletion records, keeping only the most recent one
            cursor.execute('''
                DELETE FROM file_changes 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM file_changes 
                    WHERE change_type = 'deleted' AND acknowledged = 0
                    GROUP BY job_number, file_path
                ) AND change_type = 'deleted' AND acknowledged = 0
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error cleaning up duplicate deletions: {e}")
    
    def cleanup_duplicate_changes(self):
        """Clean up duplicate file changes records in the database"""
        try:
            conn = self.get_database_connection()
            if not conn:
                return
            cursor = conn.cursor()
            
            # Remove duplicate file changes, keeping only the most recent for each file_path + change_type combination
            cursor.execute('''
                DELETE FROM file_changes 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM file_changes 
                    WHERE acknowledged = 0
                    GROUP BY job_number, file_path, change_type
                ) AND acknowledged = 0
            ''')
            
            conn.commit()
            conn.close()
            print("Cleaned up duplicate file changes records")
        except Exception as e:
            print(f"Error cleaning up duplicate changes: {e}")
    
    def setup_logging(self):
        """Setup logging for file changes"""
        import logging
        from datetime import datetime
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filename with date
        log_filename = os.path.join(log_dir, f"project_monitor_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Project File Monitor started")
    
    def log_file_change(self, job_number, file_path, change_type, details=""):
        """Log a file change event with user-friendly descriptions"""
        if hasattr(self, 'logger'):
            # Convert technical details to user-friendly descriptions
            friendly_details = self.format_change_details(change_type, details)
            self.logger.info(f"JOB:{job_number} | {change_type.upper()} | {file_path} | {friendly_details}")
    
    def format_change_details(self, change_type, details):
        """Convert technical details to user-friendly descriptions"""
        if change_type == "updated":
            if "Hash:" in details and "Time:" in details:
                hash_changed = "True" in details.split("Hash:")[1].split(",")[0]
                time_changed = "True" in details.split("Time:")[1]
                
                if hash_changed and time_changed:
                    return "Content changed & File modified"
                elif hash_changed and not time_changed:
                    return "Content changed (same time)"
                elif not hash_changed and time_changed:
                    return "File modified (same content)"
                else:
                    return "File updated"
            else:
                return "File updated"
        
        elif change_type == "new":
            if "Size:" in details:
                size_bytes = int(details.split("Size:")[1].split(" bytes")[0])
                size_mb = size_bytes / (1024 * 1024)
                if size_mb >= 1:
                    return f"New file ({size_mb:.1f} MB)"
                else:
                    size_kb = size_bytes / 1024
                    return f"New file ({size_kb:.1f} KB)"
            else:
                return "New file added"
        
        elif change_type == "deleted":
            return "File removed from project"
        
        else:
            return details
    
    def clean_database(self):
        """Manually clean up duplicate records in the database"""
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
            cursor = conn.cursor()
            
            # Clean up duplicate file changes
            cursor.execute('''
                DELETE FROM file_changes 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM file_changes 
                    WHERE acknowledged = 0
                    GROUP BY job_number, file_path, change_type
                ) AND acknowledged = 0
            ''')
            changes_removed = cursor.rowcount
            
            # Clean up duplicate deletions
            cursor.execute('''
                DELETE FROM file_changes 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM file_changes 
                    WHERE change_type = 'deleted' AND acknowledged = 0
                    GROUP BY job_number, file_path
                ) AND change_type = 'deleted' AND acknowledged = 0
            ''')
            deletions_removed = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Database Cleaned", 
                f"Removed {changes_removed} duplicate file changes and {deletions_removed} duplicate deletions.\n\n"
                "Please refresh the projects list to see updated counts.")
            
            # Refresh the projects list
            self.refresh_projects()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clean database: {str(e)}")
    
    def clear_false_changes(self):
        """Clear all unacknowledged changes that may be false positives"""
        if messagebox.askyesno("Clear False Changes", 
            "This will clear ALL unacknowledged changes for ALL projects.\n\n"
            "This should only be used if the monitoring system incorrectly flagged files as changed.\n\n"
            "Are you sure you want to continue?"):
            try:
                conn = self.get_database_connection()
                if not conn:
                    messagebox.showerror("Error", "Could not connect to database")
                    return
                cursor = conn.cursor()
                
                # Clear all unacknowledged changes
                cursor.execute('''
                    UPDATE file_changes 
                    SET acknowledged = 1 
                    WHERE acknowledged = 0
                ''')
                
                changes_cleared = cursor.rowcount
                conn.commit()
                conn.close()
                
                messagebox.showinfo("False Changes Cleared", 
                    f"Cleared {changes_cleared} unacknowledged changes.\n\n"
                    "All projects will now show 0 unread changes.\n"
                    "Please run 'Scan All' to re-establish the baseline.")
                
                # Refresh the projects list
                self.refresh_projects()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear false changes: {str(e)}")
    
    def init_database(self):
        """Initialize database tables for project monitoring"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Create project_structure table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_structure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                created_date TEXT,
                modified_date TEXT,
                file_hash TEXT,
                is_directory BOOLEAN DEFAULT 0,
                parent_path TEXT,
                scan_date TEXT,
                UNIQUE(job_number, file_path)
            )
        ''')
        
        # Create file_changes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                file_path TEXT NOT NULL,
                change_type TEXT NOT NULL,  -- 'new', 'updated', 'deleted'
                old_hash TEXT,
                new_hash TEXT,
                change_date TEXT,
                acknowledged BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create project_scan_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                scan_date TEXT NOT NULL,
                files_scanned INTEGER,
                changes_detected INTEGER,
                scan_duration REAL
            )
        ''')
        
        # Add project_status column to projects table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE projects ADD COLUMN project_status TEXT DEFAULT "active"')
        except sqlite3.OperationalError:
            # Column already exists
            pass
        
        conn.commit()
        conn.close()
    
    def load_project_data(self):
        """Load project data from JSON backup if exists"""
        backup_path = Path("backup/master_data.json")
        if backup_path.exists():
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    self.project_data = json.load(f)
            except Exception as e:
                print(f"Error loading project data: {e}")
                self.project_data = {}
        else:
            self.project_data = {}
    
    def create_widgets(self):
        """Create the main UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create paned window for resizable panels
        paned = ttk.PanedWindow(main_frame, orient="horizontal")
        paned.pack(fill="both", expand=True)
        
        # Left panel - Projects list
        self.create_projects_panel(paned)
        
        # Right panel - File updates
        self.create_files_panel(paned)
        
        # Bottom status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")
    
    def create_projects_panel(self, parent):
        """Create the left panel with projects list"""
        projects_frame = ttk.LabelFrame(parent, text="Projects (Sorted by Unread Changes)", padding=10)
        parent.add(projects_frame, weight=0)
        try:
            add_help_button(projects_frame, 'Projects Pane', 'Shows jobs with unread file changes first. Right‑click to add a note.').pack(anchor='ne')
        except Exception:
            pass
        
        # Projects treeview
        columns = ("file_count", "unread_changes", "job_number", "customer", "due_date")
        self.projects_tree = ttk.Treeview(projects_frame, columns=columns, show="headings", height=25)
        
        # Configure columns
        self.projects_tree.heading("file_count", text="Files")
        self.projects_tree.heading("unread_changes", text="Unread Changes")
        self.projects_tree.heading("job_number", text="Job #")
        self.projects_tree.heading("customer", text="Customer")
        self.projects_tree.heading("due_date", text="Due Date")
        
        self.projects_tree.column("file_count", width=60, anchor="center")
        self.projects_tree.column("unread_changes", width=100, anchor="center")
        self.projects_tree.column("job_number", width=80, anchor="center")
        self.projects_tree.column("customer", width=180, anchor="w")
        self.projects_tree.column("due_date", width=100, anchor="center")
        
        # Configure tags for unread changes highlighting
        self.projects_tree.tag_configure("has_unread", background="#FFF3CD", foreground="#856404")  # Light yellow background
        self.projects_tree.tag_configure("no_unread", background="white")
        
        # Add vertical scrollbar for projects list
        proj_scroll = ttk.Scrollbar(projects_frame, orient="vertical", command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=proj_scroll.set)
        self.projects_tree.pack(side="left", fill="both", expand=True)
        proj_scroll.pack(side="right", fill="y")
        bind_mousewheel_to_treeview(self.projects_tree)
        bind_tree_column_persistence(self.projects_tree, 'project_monitor.projects_tree', self.root)
        self.projects_tree.bind("<<TreeviewSelect>>", self.on_project_select)
        # Right-click: add note
        self.projects_ctx = tk.Menu(projects_frame, tearoff=0)
        self.projects_ctx.add_command(label="Add New Note…", command=self.add_note_for_selected_job)
        self.projects_ctx.add_command(label="Open in Job Notes", command=self.open_job_in_job_notes)
        self.projects_tree.bind('<Button-3>', self._on_projects_tree_right_click)
        
        # Buttons frame
        btn_frame = ttk.Frame(projects_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_projects).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Sort by Files", command=self.sort_by_files).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Mark Complete", command=self.mark_project_complete).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Scan Selected", command=self.scan_selected_project).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Scan All", command=self.scan_all_projects).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Clean Database", command=self.clean_database).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Clear False Changes", command=self.clear_false_changes).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Recreate Structure", command=self.recreate_structure).pack(side="left")
    
    def create_files_panel(self, parent):
        """Create the right panel with file updates"""
        files_frame = ttk.LabelFrame(parent, text="File Updates", padding=10)
        parent.add(files_frame, weight=1)
        try:
            add_help_button(files_frame, 'Files Pane', 'Displays project files and detected changes. Double‑click to open; use actions for context.').pack(anchor='ne')
        except Exception:
            pass
        
        # Create frame for treeview and scrollbars
        tree_frame = ttk.Frame(files_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # File updates treeview
        columns = ("file_name", "file_path", "file_type", "created_date", "modified_date", "status", "action")
        self.files_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=25)
        
        # Configure columns
        self.files_tree.heading("file_name", text="File Name")
        self.files_tree.heading("file_path", text="File Path")
        self.files_tree.heading("file_type", text="Type")
        self.files_tree.heading("created_date", text="Created")
        self.files_tree.heading("modified_date", text="Modified")
        self.files_tree.heading("status", text="Status")
        self.files_tree.heading("action", text="Action")
        
        self.files_tree.column("file_name", width=200, anchor="w")
        self.files_tree.column("file_path", width=300, anchor="w")
        self.files_tree.column("file_type", width=80, anchor="center")
        self.files_tree.column("created_date", width=120, anchor="center")
        self.files_tree.column("modified_date", width=120, anchor="center")
        self.files_tree.column("status", width=100, anchor="center")
        self.files_tree.column("action", width=80, anchor="center")
        
        # Configure tags for color coding
        self.files_tree.tag_configure("new_file", foreground="green", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("updated_file", foreground="green", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("locked_file", foreground="orange", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("file_in_use", foreground="red", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("deleted_file", foreground="red", font=("Arial", 9, "bold"))
        self.files_tree.tag_configure("no_changes", foreground="black")
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.files_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.files_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        bind_mousewheel_to_treeview(self.files_tree)
        bind_tree_column_persistence(self.files_tree, 'project_monitor.files_tree', self.root)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Configure grid for proper scrolling
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to open file
        self.files_tree.bind("<Double-1>", self.open_file)
        
        # Create right-click context menu
        self.create_context_menu()
        
        # Add buttons frame
        btn_frame = ttk.Frame(files_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(btn_frame, text="Refresh Updates", command=self.refresh_file_updates).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Mark Selected Read", command=self.mark_selected_read).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Mark All Read", command=self.mark_all_read).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Export Changes", command=self.export_changes).pack(side="left")
        ttk.Button(btn_frame, text="Debug DB", command=self.debug_database).pack(side="left", padx=(5, 0))
        
        # Add info label about locked files
        info_label = ttk.Label(btn_frame, text="💡 Tip: Close files in other applications to avoid scanning issues", 
                              foreground="gray", font=("Arial", 9))
        info_label.pack(side="right")
    
    def create_context_menu(self):
        """Create right-click context menu for files"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open File", command=self.open_file)
        self.context_menu.add_command(label="Mark as Read", command=self.mark_selected_read)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
        
        # Create a separate context menu for files in use
        self.context_menu_in_use = tk.Menu(self.root, tearoff=0)
        self.context_menu_in_use.add_command(label="File is being edited by someone else", state="disabled")
        self.context_menu_in_use.add_separator()
        self.context_menu_in_use.add_command(label="Show in Explorer", command=self.show_in_explorer)
        
        # Bind right-click to show context menu
        self.files_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under the cursor
        item = self.files_tree.identify_row(event.y)
        if item:
            self.files_tree.selection_set(item)
            
            # Check if the file is in use (has ~ symbol)
            item_data = self.files_tree.item(item)
            file_name = item_data['values'][0]  # file_name is in column 0
            file_in_use = file_name.startswith("~")
            
            # Show appropriate context menu
            if file_in_use:
                self.context_menu_in_use.post(event.x_root, event.y_root)
            else:
                self.context_menu.post(event.x_root, event.y_root)
    
    def show_in_explorer(self):
        """Show selected file in Windows Explorer"""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        try:
            item = self.files_tree.item(selection[0])
            file_path = item['values'][1]  # file_path is in column 1
            
            # Get the full path
            conn = self.get_database_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            cursor.execute('SELECT job_directory FROM projects WHERE job_number = ?', (self.current_project,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                full_path = os.path.join(result[0], file_path)
                if os.path.exists(full_path):
                    # Open in Windows Explorer
                    os.startfile(os.path.dirname(full_path))
                else:
                    messagebox.showerror("Error", f"File not found: {full_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show in Explorer: {str(e)}")
    
    def refresh_projects(self):
        """Refresh the projects list from database"""
        # Clear existing items
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)
        
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Get active projects with due dates, sorted by unread changes (primary) then file count (secondary)
            cursor.execute('''
                SELECT p.job_number, p.customer_name, p.due_date,
                       COALESCE(fc.unread_changes, 0) as unread_changes,
                       COALESCE(ps.file_count, 0) as file_count
                FROM projects p
                LEFT JOIN (
                    SELECT job_number, COUNT(DISTINCT file_path) as unread_changes
                    FROM file_changes 
                    WHERE acknowledged = 0 AND change_type != 'deleted'
                    AND file_path NOT LIKE '%.bak'
                    AND file_path NOT LIKE '%.tmp'
                    AND file_path NOT LIKE '%.~%'
                    AND file_path NOT LIKE '%~%'
                    GROUP BY job_number
                ) fc ON p.job_number = fc.job_number
                LEFT JOIN (
                    SELECT job_number, COUNT(*) as file_count
                    FROM project_structure 
                    WHERE is_directory = 0
                    GROUP BY job_number
                ) ps ON p.job_number = ps.job_number
                WHERE p.job_number IS NOT NULL 
                AND (p.project_status IS NULL OR p.project_status = 'active')
                ORDER BY 
                    unread_changes DESC,
                    file_count DESC,
                    CASE 
                        WHEN p.due_date IS NULL OR p.due_date = '' THEN 1
                        ELSE 0
                    END,
                    p.due_date ASC
            ''')
            
            projects = cursor.fetchall()
            
            # Process projects (file counts and unread changes already included in query)
            for project in projects:
                job_number, customer, due_date, unread_changes, file_count = project
                customer = customer or "Unknown Customer"
                due_date = due_date or "No Due Date"
                
                # Apply tag based on unread changes
                tag = "has_unread" if unread_changes > 0 else "no_unread"
                self.projects_tree.insert("", "end", values=(file_count, unread_changes, job_number, customer, due_date), tags=(tag,))
            
            conn.close()
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load projects: {str(e)}")
            self.status_var.set("Error loading projects")

    def _on_projects_tree_right_click(self, event):
        iid = self.projects_tree.identify_row(event.y)
        if iid:
            self.projects_tree.selection_set(iid)
            try:
                self.projects_ctx.tk_popup(event.x_root, event.y_root)
            finally:
                self.projects_ctx.grab_release()

    def add_note_for_selected_job(self):
        sel = self.projects_tree.selection()
        job_number = None
        if sel:
            vals = self.projects_tree.item(sel[0], 'values')
            if vals:
                job_number = vals[2]  # third column is job_number
        open_add_note_dialog(self.root, str(job_number) if job_number else None)

    def open_job_in_job_notes(self):
        try:
            import sys, os, subprocess
            sel = self.projects_tree.selection()
            job_arg = []
            if sel:
                vals = self.projects_tree.item(sel[0], 'values')
                if vals:
                    job_arg = ["--job", str(vals[2])]
            if os.path.exists('job_notes.py'):
                subprocess.Popen([sys.executable, 'job_notes.py'] + job_arg)
            else:
                messagebox.showerror("Error", "job_notes.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Job Notes: {e}")
    
    def sort_by_files(self):
        """Sort projects by number of files (descending)"""
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Get active projects with file counts, sorted by file count descending
            cursor.execute('''
                SELECT p.job_number, p.customer_name, p.due_date,
                       COALESCE(fc.unread_changes, 0) as unread_changes,
                       COALESCE(ps.file_count, 0) as file_count
                FROM projects p
                LEFT JOIN (
                    SELECT job_number, COUNT(DISTINCT file_path) as unread_changes
                    FROM file_changes 
                    WHERE acknowledged = 0 AND change_type != 'deleted'
                    AND file_path NOT LIKE '%.bak'
                    AND file_path NOT LIKE '%.tmp'
                    AND file_path NOT LIKE '%.~%'
                    AND file_path NOT LIKE '%~%'
                    GROUP BY job_number
                ) fc ON p.job_number = fc.job_number
                LEFT JOIN (
                    SELECT job_number, COUNT(*) as file_count
                    FROM project_structure 
                    WHERE is_directory = 0
                    GROUP BY job_number
                ) ps ON p.job_number = ps.job_number
                WHERE p.job_number IS NOT NULL 
                AND (p.project_status IS NULL OR p.project_status = 'active')
                ORDER BY file_count DESC, unread_changes DESC, p.due_date ASC
            ''')
            
            projects = cursor.fetchall()
            
            # Clear existing items
            for item in self.projects_tree.get_children():
                self.projects_tree.delete(item)
            
            # Insert sorted projects
            for project in projects:
                job_number, customer, due_date, unread_changes, file_count = project
                customer = customer or "Unknown Customer"
                due_date = due_date or "No Due Date"
                
                # Apply tag based on unread changes
                tag = "has_unread" if unread_changes > 0 else "no_unread"
                self.projects_tree.insert("", "end", values=(file_count, unread_changes, job_number, customer, due_date), tags=(tag,))
            
            conn.close()
            self.status_var.set("Projects sorted by file count (highest first)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sort projects: {str(e)}")
            self.status_var.set("Error sorting projects")
    
    def mark_project_complete(self):
        """Mark the selected project as completed"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        # Confirm the action
        if messagebox.askyesno("Mark Project Complete", 
                              f"Are you sure you want to mark project {self.current_project} as completed?\n\n"
                              "This will stop monitoring this project for changes."):
            try:
                conn = self.get_database_connection()
                if not conn:
                    messagebox.showerror("Error", "Could not connect to database")
                    return
                
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE projects 
                    SET project_status = 'completed' 
                    WHERE job_number = ?
                ''', (self.current_project,))
                
                conn.commit()
                conn.close()
                
                # Refresh the projects list to remove completed project
                self.refresh_projects()
                self.status_var.set(f"Project {self.current_project} marked as completed")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mark project complete: {str(e)}")
    
    def scan_selected_project(self):
        """Scan only the currently selected project"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        # Get project directory
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute('SELECT job_directory FROM projects WHERE job_number = ?', (self.current_project,))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                messagebox.showerror("Error", f"No project directory found for project {self.current_project}")
                return
            
            job_directory = result[0]
            if not os.path.exists(job_directory):
                messagebox.showerror("Error", f"Project directory does not exist:\n{job_directory}")
                return
            
            # Show progress and scan
            self.status_var.set(f"Scanning project {self.current_project}...")
            self.root.update()  # Update UI immediately
            
            # Run scan in background thread
            def scan_thread():
                try:
                    changes = self.scan_project_directory(self.current_project, job_directory)
                    self.root.after(0, lambda: self.status_var.set(f"Scan complete for {self.current_project}. Found {changes} changes."))
                    self.root.after(0, self.refresh_projects)  # Update file counts
                    self.root.after(0, lambda: self.load_file_updates(self.current_project))  # Refresh file list
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Scan failed"))
            
            threading.Thread(target=scan_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan project: {str(e)}")
    
    def on_project_select(self, event):
        """Handle project selection"""
        selection = self.projects_tree.selection()
        if not selection:
            return
        
        item = self.projects_tree.item(selection[0])
        # Updated to handle new column order: file_count, unread_changes, job_number, customer, due_date
        job_number = item['values'][2]  # job_number is now index 2
        self.current_project = job_number
        
        # Load file updates for selected project
        self.load_file_updates(job_number)
        self.status_var.set(f"Selected project: {job_number}")
    
    def load_file_updates(self, job_number):
        """Load file updates for the selected project"""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Get recent file changes for this project (deduplicated, excluding deleted files and backup files)
            cursor.execute('''
                SELECT file_path, change_type, MAX(change_date) as change_date, acknowledged
                FROM file_changes
                WHERE job_number = ? AND acknowledged = 0 AND change_type != 'deleted'
                AND file_path NOT LIKE '%.bak'
                AND file_path NOT LIKE '%.tmp'
                AND file_path NOT LIKE '%.~%'
                AND file_path NOT LIKE '%~%'
                GROUP BY file_path, change_type
                ORDER BY change_date DESC
            ''', (job_number,))
            
            changes = cursor.fetchall()
            
            # Get current file structure for metadata
            cursor.execute('''
                SELECT file_path, file_name, file_type, created_date, modified_date, file_hash
                FROM project_structure
                WHERE job_number = ? AND is_directory = 0
                ORDER BY modified_date DESC
            ''', (job_number,))
            
            files = cursor.fetchall()
            
            # Create a dictionary for quick lookup of file metadata
            file_metadata = {file_data[0]: file_data for file_data in files}
            
            conn.close()
            
            # All changes are now non-deleted (deleted files excluded from query)
            other_changes = changes
            deleted_files = []  # No deleted files to process
            
            # Process files for display
            
            # Create a set of changed files for quick lookup
            changed_files = {change[0]: change[1] for change in other_changes}
            
            # Add ALL files from project_structure, highlighting changed ones
            changed_count = 0
            for file_data in files:
                file_path, file_name, file_type, created_date, modified_date, file_hash = file_data
                
                # Check if file is in use (has ~ symbol)
                file_in_use = file_name.startswith("~")
                
                # Determine status
                if file_in_use:
                    status = "In Use"
                    status_color = "red"
                elif file_path in changed_files:
                    # File has changes
                    change_type = changed_files[file_path]
                    if change_type == "new":
                        status = "New File"
                        status_color = "green"
                    else:  # updated
                        status = "Updated"
                        status_color = "green"
                    changed_count += 1
                else:
                    # Check if file was locked during last scan
                    if file_hash == "locked_file":
                        status = "Locked"
                        status_color = "orange"
                    else:
                        status = "No Changes"
                        status_color = "black"
                
                # Format dates
                created_date = self.format_date(created_date)
                modified_date = self.format_date(modified_date)
                
                # Insert into tree with appropriate tag
                if status_color == "red":  # File in use
                    tag = "file_in_use"
                elif status_color == "green":
                    if status == "New File":
                        tag = "new_file"
                    else:  # Updated
                        tag = "updated_file"
                elif status_color == "orange":  # Locked
                    tag = "locked_file"
                else:  # No changes
                    tag = "no_changes"
                
                item_id = self.files_tree.insert("", "end", values=(
                    file_name, file_path, file_type, created_date, modified_date, status, "Open"
                ), tags=(tag,))
            
            # Add any new files that aren't in project_structure yet
            new_files_added = 0
            for change in other_changes:
                file_path, change_type, change_date, acknowledged = change
                if file_path not in file_metadata:  # Only add if not already shown
                    new_files_added += 1
                    file_name = os.path.basename(file_path)
                    file_type = os.path.splitext(file_name)[1]
                    
                    # Check if file is in use (has ~ symbol)
                    file_in_use = file_name.startswith("~")
                    
                    # Determine status
                    if file_in_use:
                        status = "In Use"
                        status_color = "red"
                    elif change_type == "new":
                        status = "New File"
                        status_color = "green"
                    else:  # updated
                        status = "Updated"
                        status_color = "green"
                    
                    # Format dates
                    created_date = self.format_date(change_date)
                    modified_date = self.format_date(change_date)
                    
                    # Insert into tree with appropriate tag
                    if status_color == "red":  # File in use
                        tag = "file_in_use"
                    elif status_color == "green":
                        if status == "New File":
                            tag = "new_file"
                        else:  # Updated
                            tag = "updated_file"
                    
                    item_id = self.files_tree.insert("", "end", values=(
                        file_name, file_path, file_type, created_date, modified_date, status, "Open"
                    ), tags=(tag,))
            
            # Deleted files are no longer displayed (excluded from monitoring)
            
            # Update status
            total_files = len(files) + new_files_added
            total_changes = len(other_changes)
            # Count actual items in the tree
            tree_items = self.files_tree.get_children()
            green_items = 0
            for item in tree_items:
                tags = self.files_tree.item(item, 'tags')
                if 'updated_file' in tags or 'new_file' in tags:
                    green_items += 1
            
            # Summary completed
            
            if total_files == 0:
                self.status_var.set(f"No files found for project {job_number} - Run 'Scan All' first")
                # Show a helpful message
                self.show_no_files_message(job_number)
            else:
                self.status_var.set(f"Loaded {total_files} files ({total_changes} with changes) for project {job_number}")
                
        except Exception as e:
            print(f"Error loading file updates for {job_number}: {e}")
            messagebox.showerror("Error", f"Failed to load file updates: {str(e)}")
            self.status_var.set("Error loading file updates")
    
    def show_no_files_message(self, job_number):
        """Show a helpful message when no files are found for a project"""
        # Insert a helpful message in the files tree
        self.files_tree.insert("", "end", values=(
            "No files found", 
            f"Project {job_number} has not been scanned yet", 
            "", 
            "", 
            "", 
            "Run 'Scan All' to scan this project", 
            ""
        ))
    
    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return "Unknown"
        
        try:
            # Parse ISO format date
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str
    
    def scan_all_projects(self):
        """Scan all projects for file changes"""
        self.status_var.set("Scanning all projects...")
        
        # Run scan in background thread
        def scan_thread():
            try:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Get all projects with job directories
                cursor.execute('''
                    SELECT job_number, job_directory
                    FROM projects
                    WHERE job_directory IS NOT NULL AND job_directory != ''
                ''')
                
                projects = cursor.fetchall()
                conn.close()
                
                total_changes = 0
                for i, (job_number, job_directory) in enumerate(projects):
                    if os.path.exists(job_directory):
                        # Update status to show current project being scanned
                        self.root.after(0, lambda jn=job_number, idx=i+1, total=len(projects): 
                                      self.status_var.set(f"Scanning project {jn} ({idx}/{total})..."))
                        
                        changes = self.scan_project_directory(job_number, job_directory)
                        total_changes += changes
                        
                        # Add small delay between projects to reduce database contention
                        if i < len(projects) - 1:  # Don't delay after last project
                            time.sleep(0.5)
                
                self.root.after(0, lambda: self.status_var.set(f"Scan complete. Found {total_changes} changes."))
                self.root.after(0, self.refresh_projects)
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Scan failed"))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def scan_project_directory(self, job_number, directory_path):
        """Scan a project directory for changes"""
        changes_detected = 0
        start_time = time.time()
        
        try:
            # Use a database connection with timeout and retry logic
            conn = self.get_database_connection()
            if not conn:
                print(f"Could not connect to database for {job_number}")
                return 0
                
            cursor = conn.cursor()
            
            # Get existing file hashes
            cursor.execute('''
                SELECT file_path, file_hash, modified_date
                FROM project_structure
                WHERE job_number = ?
            ''', (job_number,))
            
            existing_files = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
            
            # Get all current files in directory
            current_files = set()
            file_count = 0
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    
                    # Skip backup files
                    if (file.endswith('.bak') or file.endswith('.tmp') or 
                        file.startswith('~') or '.~' in file or '~' in file):
                        continue
                    
                    current_files.add(relative_path)
                    file_count += 1
                    
                    try:
                        # Get file stats
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        modified_time = stat.st_mtime
                        
                        # Handle Windows file timestamps properly
                        # On Windows: st_ctime = change time, st_mtime = modification time
                        # We need to ensure created_time <= modified_time
                        if platform.system() == "Windows":
                            # On Windows, use the earlier timestamp as "created"
                            # This prevents impossible "created after modified" scenarios
                            created_time = min(stat.st_ctime, stat.st_mtime)
                        else:
                            # On Unix-like systems, st_ctime is usually creation time
                            created_time = stat.st_ctime
                        
                        # Final safety check: ensure created <= modified
                        if created_time > modified_time:
                            created_time = modified_time
                        
                        # Calculate file hash (with retry for locked files)
                        file_hash = self.calculate_file_hash(file_path)
                        
                        # Check if file exists in database
                        if relative_path in existing_files:
                            old_hash, old_modified = existing_files[relative_path]
                            
                            # Convert old_modified from ISO format to Unix timestamp for comparison
                            try:
                                if old_modified:
                                    # Parse ISO format datetime and convert to Unix timestamp
                                    old_datetime = datetime.fromisoformat(old_modified.replace('Z', '+00:00'))
                                    old_modified_float = old_datetime.timestamp()
                                else:
                                    old_modified_float = 0
                            except (ValueError, TypeError, AttributeError):
                                old_modified_float = 0
                            
                            # Check if file has changed (but skip if file is locked)
                            hash_changed = old_hash != file_hash
                            time_changed = abs(old_modified_float - modified_time) > 1.0
                            
                            if file_hash != "locked_file" and (hash_changed or time_changed):
                                # File has been updated (allow 1 second tolerance for timestamp precision)
                                self.record_file_change(cursor, job_number, relative_path, "updated", old_hash, file_hash)
                                changes_detected += 1
                                # Log and show in console
                                print(f"📝 UPDATED: {file}")
                                self.log_file_change(job_number, relative_path, "updated", f"Hash: {hash_changed}, Time: {time_changed}")
                        else:
                            # New file (but skip if locked)
                            if file_hash != "locked_file":
                                self.record_file_change(cursor, job_number, relative_path, "new", None, file_hash)
                                changes_detected += 1
                                # Log and show in console
                                print(f"🆕 NEW FILE: {file}")
                                self.log_file_change(job_number, relative_path, "new", f"Size: {file_size} bytes")
                        
                        # Update or insert file record (even for locked files, use modification time)
                        cursor.execute('''
                            INSERT OR REPLACE INTO project_structure
                            (job_number, file_path, file_name, file_type, file_size, 
                             created_date, modified_date, file_hash, is_directory, parent_path, scan_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            job_number, relative_path, file, 
                            os.path.splitext(file)[1], file_size,
                            datetime.fromtimestamp(created_time).isoformat(),
                            datetime.fromtimestamp(modified_time).isoformat(),
                            file_hash, False, os.path.dirname(relative_path),
                            datetime.now().isoformat()
                        ))
                        
                    except (OSError, IOError) as e:
                        # Skip files that can't be read
                        print(f"Skipping file {file}: {e}")
                        continue
            
            # Check for deleted files
            deleted_files = set(existing_files.keys()) - current_files
            for deleted_file in deleted_files:
                print(f"File deleted: {deleted_file}")
                
                # Check if deletion is already recorded
                cursor.execute('''
                    SELECT COUNT(*) FROM file_changes 
                    WHERE job_number = ? AND file_path = ? AND change_type = 'deleted' AND acknowledged = 0
                ''', (job_number, deleted_file))
                
                if cursor.fetchone()[0] == 0:
                    # Only record if not already recorded
                    self.record_file_change(cursor, job_number, deleted_file, "deleted", existing_files[deleted_file][0], None)
                    changes_detected += 1
                    # Log and show in console
                    print(f"🗑️  DELETED: {os.path.basename(deleted_file)}")
                    self.log_file_change(job_number, deleted_file, "deleted", f"Previously: {existing_files[deleted_file][0]}")
                
                # Remove from project_structure table
                cursor.execute('''
                    DELETE FROM project_structure 
                    WHERE job_number = ? AND file_path = ?
                ''', (job_number, deleted_file))
            
            # Don't clear change records - we want them to persist until acknowledged
            # Only clear them when explicitly marked as read
            
            # Record scan history
            scan_duration = time.time() - start_time
            cursor.execute('''
                INSERT INTO project_scan_history
                (job_number, scan_date, files_scanned, changes_detected, scan_duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (job_number, datetime.now().isoformat(), file_count, changes_detected, scan_duration))
            
            conn.commit()
            conn.close()
            
            # Print scan summary
            if changes_detected > 0:
                print(f"\n✅ SCAN COMPLETE: {job_number} - {changes_detected} changes detected")
            else:
                print(f"\n✅ SCAN COMPLETE: {job_number} - No changes")
            
        except Exception as e:
            print(f"Error scanning {job_number}: {e}")
        
        return changes_detected
    
    def get_database_connection(self, timeout=30):
        """Get a database connection with retry logic for locked database"""
        max_retries = 10  # Increased retries
        retry_delay = 0.5  # Start with shorter delay
        
        for attempt in range(max_retries):
            try:
                # Use WAL mode for better concurrency
                conn = sqlite3.connect(
                    self.db_manager.db_path, 
                    timeout=timeout,
                    check_same_thread=False,
                    isolation_level=None  # Autocommit mode
                )
                
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                
                # Test the connection
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower():
                    print(f"Database locked, retrying in {retry_delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, 5)  # Gradual increase, max 5 seconds
                else:
                    print(f"Database error: {e}")
                    return None
            except Exception as e:
                print(f"Unexpected database error: {e}")
                return None
        
        print("Failed to connect to database after all retries")
        return None
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of file with retry logic for locked files"""
        hash_md5 = hashlib.md5()
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                return hash_md5.hexdigest()
            except (OSError, IOError) as e:
                if "being used by another process" in str(e).lower() or "access is denied" in str(e).lower():
                    if attempt < max_retries - 1:
                        print(f"File {os.path.basename(file_path)} is locked, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        print(f"File {os.path.basename(file_path)} is locked, skipping hash calculation")
                        return "locked_file"
                else:
                    print(f"Error reading {os.path.basename(file_path)}: {e}")
                    return ""
        
        return ""
    
    def record_file_change(self, cursor, job_number, file_path, change_type, old_hash, new_hash):
        """Record a file change in the database"""
        cursor.execute('''
            INSERT INTO file_changes
            (job_number, file_path, change_type, old_hash, new_hash, change_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job_number, file_path, change_type, old_hash, new_hash, datetime.now().isoformat()))
    
    def open_file(self, event):
        """Open the selected file"""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        item = self.files_tree.item(selection[0])
        relative_path = item['values'][1]  # Relative file path
        file_name = item['values'][0]  # File name
        
        # Check if file is in use (has ~ symbol)
        if file_name.startswith("~"):
            messagebox.showwarning("File In Use", "This file is currently being edited by someone else. Please wait for them to finish.")
            return
        
        try:
            # Get the full path by combining project directory with relative path
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute('SELECT job_directory FROM projects WHERE job_number = ?', (self.current_project,))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                messagebox.showerror("Error", "No project directory found for this project")
                return
            
            # Construct full path
            full_path = os.path.join(result[0], relative_path)
            
            if not os.path.exists(full_path):
                messagebox.showerror("Error", f"File not found: {full_path}")
                return
            
            # Open the file
            if platform.system() == "Windows":
                os.startfile(full_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", full_path])
            else:  # Linux
                subprocess.run(["xdg-open", full_path])
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def recreate_structure(self):
        """Recreate project folder structure"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        # Get project directory
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT job_directory FROM projects WHERE job_number = ?', (self.current_project,))
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                messagebox.showerror("Error", "No project directory found for this project")
                return
            
            source_dir = result[0]
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not get project directory: {str(e)}")
            return
        
        # Let user choose destination
        dest_dir = filedialog.askdirectory(title="Choose destination for recreated structure")
        if not dest_dir:
            return
        
        # Create the recreated structure
        self.create_recreated_structure(source_dir, dest_dir, self.current_project)
    
    def create_recreated_structure(self, source_dir, dest_dir, job_number):
        """Create recreated project structure"""
        try:
            # Create main project folder
            project_folder = os.path.join(dest_dir, f"Project_{job_number}")
            os.makedirs(project_folder, exist_ok=True)
            
            # Copy directory structure
            for root, dirs, files in os.walk(source_dir):
                # Calculate relative path
                rel_path = os.path.relpath(root, source_dir)
                dest_path = os.path.join(project_folder, rel_path)
                
                # Create directory
                os.makedirs(dest_path, exist_ok=True)
                
                # Copy files
                for file in files:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_path, file)
                    
                    try:
                        # Copy file
                        import shutil
                        shutil.copy2(src_file, dest_file)
                    except Exception as e:
                        print(f"Could not copy {src_file}: {e}")
            
            # Create the excel extraction script
            self.create_excel_extraction_script(project_folder)
            
            messagebox.showinfo("Success", f"Project structure recreated in:\n{project_folder}")
            self.status_var.set(f"Structure recreated for project {job_number}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to recreate structure: {str(e)}")
    
    def create_excel_extraction_script(self, project_folder):
        """Create the excel extraction script in the project folder"""
        # Copy the standalone script
        script_path = os.path.join(project_folder, "excel_extract_duplicate.py")
        try:
            import shutil
            shutil.copy2("excel_extract_duplicate.py", script_path)
        except:
            # If copy fails, create the script content
            with open("excel_extract_duplicate.py", 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
    
    def refresh_file_updates(self):
        """Refresh file updates for current project"""
        if self.current_project:
            self.load_file_updates(self.current_project)
            self.status_var.set("File updates refreshed")
    
    def mark_all_read(self):
        """Mark all file changes as read/acknowledged"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE file_changes 
                SET acknowledged = 1 
                WHERE job_number = ? AND acknowledged = 0
            ''', (self.current_project,))
            conn.commit()
            conn.close()
            
            self.load_file_updates(self.current_project)
            self.status_var.set("All changes marked as read")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark changes as read: {str(e)}")
    
    def mark_selected_read(self):
        """Mark the selected file as read/acknowledged"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        # Get selected file from tree
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        try:
            # Get file path from selected item
            item = self.files_tree.item(selection[0])
            file_path = item['values'][1]  # file_path is in column 1
            
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Get the file name to handle both regular and deleted files
            file_name = item['values'][0]  # file_name is in column 0
            status = item['values'][5]  # status is in column 5
            
            if status == "Deleted":
                # For deleted files, mark all deletion records as acknowledged
                cursor.execute('''
                    UPDATE file_changes 
                    SET acknowledged = 1 
                    WHERE job_number = ? AND file_path = ? AND change_type = 'deleted' AND acknowledged = 0
                ''', (self.current_project, file_path))
            else:
                # For regular files, mark all change records as acknowledged
                cursor.execute('''
                    UPDATE file_changes 
                    SET acknowledged = 1 
                    WHERE job_number = ? AND file_path = ? AND acknowledged = 0
                ''', (self.current_project, file_path))
            
            conn.commit()
            conn.close()
            
            # Refresh the file list to update colors
            self.load_file_updates(self.current_project)
            self.status_var.set(f"Marked {os.path.basename(file_path)} as read")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark file as read: {str(e)}")
    
    def export_changes(self):
        """Export file changes to JSON"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Get all changes for current project
            cursor.execute('''
                SELECT file_path, change_type, change_date, acknowledged
                FROM file_changes
                WHERE job_number = ?
                ORDER BY change_date DESC
            ''', (self.current_project,))
            
            changes = cursor.fetchall()
            conn.close()
            
            # Prepare export data
            export_data = {
                "project": self.current_project,
                "export_date": datetime.now().isoformat(),
                "changes": []
            }
            
            for change in changes:
                export_data["changes"].append({
                    "file_path": change[0],
                    "change_type": change[1],
                    "change_date": change[2],
                    "acknowledged": bool(change[3])
                })
            
            # Save to file
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"project_{self.current_project}_changes.json"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Changes exported to {filename}")
                self.status_var.set(f"Changes exported to {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export changes: {str(e)}")
    
    def debug_database(self):
        """Debug method to check what's in the database"""
        try:
            conn = self.get_database_connection()
            if not conn:
                messagebox.showerror("Error", "Could not connect to database")
                return
                
            cursor = conn.cursor()
            
            # Check if project_structure table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_structure'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                debug_info = "project_structure table does not exist!"
                messagebox.showinfo("Database Debug", debug_info)
                conn.close()
                return
            
            # Check project_structure table
            cursor.execute("SELECT COUNT(*) FROM project_structure")
            total_files = cursor.fetchone()[0]
            
            # Check by job number
            cursor.execute("SELECT job_number, COUNT(*) FROM project_structure GROUP BY job_number")
            job_counts = cursor.fetchall()
            
            # Check file_changes table
            cursor.execute("SELECT COUNT(*) FROM file_changes")
            total_changes = cursor.fetchone()[0]
            
            # Check table structure
            cursor.execute("PRAGMA table_info(project_structure)")
            columns = cursor.fetchall()
            
            # Sample data
            cursor.execute("SELECT * FROM project_structure LIMIT 5")
            sample_data = cursor.fetchall()
            
            conn.close()
            
            # Show debug info
            debug_info = f"Database Debug Info:\n\n"
            debug_info += f"project_structure table exists: {table_exists is not None}\n"
            debug_info += f"Total files in database: {total_files}\n"
            debug_info += f"Total changes tracked: {total_changes}\n\n"
            debug_info += "Table columns:\n"
            for col in columns:
                debug_info += f"  {col[1]} ({col[2]})\n"
            debug_info += "\nFiles per project:\n"
            for job, count in job_counts:
                debug_info += f"  {job}: {count} files\n"
            debug_info += "\nSample data (first 5 rows):\n"
            for row in sample_data:
                debug_info += f"  {row}\n"
            
            messagebox.showinfo("Database Debug", debug_info)
            
        except Exception as e:
            messagebox.showerror("Error", f"Debug failed: {str(e)}")
    
    def start_background_monitoring(self):
        """Start background monitoring of file changes"""
        def monitor_loop():
            while True:
                try:
                    if self.current_project:
                        # Check for changes every 5 seconds for responsive monitoring
                        time.sleep(5)
                        self.check_for_changes()
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def check_for_changes(self):
        """Check for file changes in current project"""
        if not self.current_project:
            return
        
        try:
            conn = self.get_database_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            cursor.execute('SELECT job_directory FROM projects WHERE job_number = ?', (self.current_project,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] and os.path.exists(result[0]):
                changes = self.scan_project_directory(self.current_project, result[0])
                if changes > 0:
                    # Update UI in main thread
                    self.root.after(0, lambda: self.load_file_updates(self.current_project))
                    self.root.after(0, lambda: self.status_var.set(f"Found {changes} new changes"))
        
        except Exception as e:
            print(f"Error checking changes: {e}")

def main():
    root = tk.Tk()
    app = ProjectMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
