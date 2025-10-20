#!/usr/bin/env python3
"""
Print Package Management Application
Manages drawing print packages for projects with global search and print functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import subprocess
import sys
from datetime import datetime
import json

class PrintPackageApp:
    def __init__(self, job_number=None):
        self.root = tk.Tk()
        self.root.title("Print Package Management - Drafting Tools")
        self.root.state('zoomed')  # Maximized window
        
        # Store job number for preloading
        self.preload_job_number = job_number
        self.root.minsize(1200, 800)
        
        # Initialize database
        self.init_database()
        
        # Create main interface
        self.create_widgets()
        
        # Add keyboard shortcuts for fullscreen toggle
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen() if self.root.attributes('-fullscreen') else None)
        
        # Load initial data
        self.load_projects()
        
        # Initialize current project
        self.current_project = None
        
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main container - use full screen
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(main_frame, text="Print Package Management", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Create resizable paned window for adjustable panels
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Create frames for each panel
        project_list_container = ttk.Frame(paned_window)
        drawings_container = ttk.Frame(paned_window)
        
        # Add frames to paned window
        paned_window.add(project_list_container, weight=1)
        paned_window.add(drawings_container, weight=3)
        
        # Left side - Project list
        self.create_project_list_panel(project_list_container)
        
        # Right side - Drawings management
        self.create_drawings_panel(drawings_container)
        
    def create_project_list_panel(self, parent):
        """Create the project list panel on the left side"""
        # Project list frame
        project_frame = ttk.LabelFrame(parent, text="Projects", padding=10)
        project_frame.pack(fill=tk.BOTH, expand=True)
        
        # Search frame
        search_frame = ttk.Frame(project_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.project_search_var = tk.StringVar()
        self.project_search_var.trace('w', self.filter_projects)
        search_entry = ttk.Entry(search_frame, textvariable=self.project_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Refresh button
        refresh_btn = ttk.Button(search_frame, text="Refresh", command=self.load_projects)
        refresh_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Show/Hide Completed toggle (jobs with drawings considered completed here)
        self.show_completed = False
        self.toggle_completed_btn = ttk.Button(search_frame, text="Show Completed", command=self.toggle_completed)
        self.toggle_completed_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        # Project list treeview
        columns = ('Job Number', 'Customer', 'Drawings Count')
        self.project_tree = ttk.Treeview(project_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.project_tree.heading('Job Number', text='Job Number')
        self.project_tree.heading('Customer', text='Customer')
        self.project_tree.heading('Drawings Count', text='Drawings Count')
        
        self.project_tree.column('Job Number', width=100)
        self.project_tree.column('Customer', width=200)
        self.project_tree.column('Drawings Count', width=100)
        
        # Scrollbar for project list
        project_scrollbar = ttk.Scrollbar(project_frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=project_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        project_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.project_tree.bind('<<TreeviewSelect>>', self.on_project_select)
        
    def create_drawings_panel(self, parent):
        """Create the drawings management panel on the right side"""
        # Drawings frame
        drawings_frame = ttk.LabelFrame(parent, text="Drawings Management", padding=10)
        drawings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current job display
        job_frame = ttk.Frame(drawings_frame)
        job_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(job_frame, text="Current Job:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        self.current_job_label = ttk.Label(job_frame, text="None Selected", font=('Arial', 12))
        self.current_job_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Global search frame
        search_frame = ttk.Frame(drawings_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Global Search:").pack(side=tk.LEFT)
        self.global_search_var = tk.StringVar()
        self.global_search_var.trace('w', self.search_global_drawings)
        global_search_entry = ttk.Entry(search_frame, textvariable=self.global_search_var, width=30)
        global_search_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Add drawing frame
        add_frame = ttk.Frame(drawings_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(add_frame, text="Add Drawing:").pack(side=tk.LEFT)
        self.drawing_path_var = tk.StringVar()
        path_entry = ttk.Entry(add_frame, textvariable=self.drawing_path_var, width=40)
        path_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        browse_btn = ttk.Button(add_frame, text="Browse", command=self.browse_drawing)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        add_btn = ttk.Button(add_frame, text="Add to Current Job", command=self.add_drawing)
        add_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Drawings list
        drawings_list_frame = ttk.Frame(drawings_frame)
        drawings_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current job drawings
        current_drawings_frame = ttk.LabelFrame(drawings_list_frame, text="Current Job Drawings", padding=5)
        current_drawings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Current drawings treeview (with Printed column)
        current_columns = ('Printed', 'Drawing Name', 'Type', 'Path', 'Actions')
        self.current_drawings_tree = ttk.Treeview(current_drawings_frame, columns=current_columns, show='headings', height=8)
        
        # Configure columns
        self.current_drawings_tree.heading('Printed', text='Printed')
        self.current_drawings_tree.heading('Drawing Name', text='Drawing Name')
        self.current_drawings_tree.heading('Type', text='Type')
        self.current_drawings_tree.heading('Path', text='Path')
        self.current_drawings_tree.heading('Actions', text='Actions')
        
        self.current_drawings_tree.column('Printed', width=70, anchor='center')
        self.current_drawings_tree.column('Drawing Name', width=200)
        self.current_drawings_tree.column('Type', width=80)
        self.current_drawings_tree.column('Path', width=300)
        self.current_drawings_tree.column('Actions', width=120)
        
        # Scrollbar for current drawings
        current_scrollbar = ttk.Scrollbar(current_drawings_frame, orient=tk.VERTICAL, command=self.current_drawings_tree.yview)
        self.current_drawings_tree.configure(yscrollcommand=current_scrollbar.set)
        
        # Pack current drawings treeview
        self.current_drawings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        current_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind clicks (toggle printed), double-click and right-click events for current drawings
        self.current_drawings_tree.bind('<Button-1>', self.on_current_drawing_click)
        self.current_drawings_tree.bind('<Double-1>', self.on_current_drawing_double_click)
        self.current_drawings_tree.bind('<Button-3>', self.on_current_drawing_right_click)
        
        # Global search results
        global_drawings_frame = ttk.LabelFrame(drawings_list_frame, text="Global Search Results", padding=5)
        global_drawings_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Global drawings treeview
        global_columns = ('Job Number', 'Drawing Name', 'Type', 'Path', 'Actions')
        self.global_drawings_tree = ttk.Treeview(global_drawings_frame, columns=global_columns, show='headings', height=8)
        
        # Configure columns
        self.global_drawings_tree.heading('Job Number', text='Job Number')
        self.global_drawings_tree.heading('Drawing Name', text='Drawing Name')
        self.global_drawings_tree.heading('Type', text='Type')
        self.global_drawings_tree.heading('Path', text='Path')
        self.global_drawings_tree.heading('Actions', text='Actions')
        
        self.global_drawings_tree.column('Job Number', width=100)
        self.global_drawings_tree.column('Drawing Name', width=150)
        self.global_drawings_tree.column('Type', width=80)
        self.global_drawings_tree.column('Path', width=250)
        self.global_drawings_tree.column('Actions', width=120)
        
        # Scrollbar for global drawings
        global_scrollbar = ttk.Scrollbar(global_drawings_frame, orient=tk.VERTICAL, command=self.global_drawings_tree.yview)
        self.global_drawings_tree.configure(yscrollcommand=global_scrollbar.set)
        
        # Pack global drawings treeview
        self.global_drawings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        global_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click and right-click events for global drawings
        self.global_drawings_tree.bind('<Double-1>', self.on_global_drawing_double_click)
        self.global_drawings_tree.bind('<Button-3>', self.on_global_drawing_right_click)
        
        # Action buttons
        action_frame = ttk.Frame(drawings_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Dashboard button
        dashboard_btn = ttk.Button(action_frame, text="🏠 Dashboard", command=self.open_dashboard)
        dashboard_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        print_all_btn = ttk.Button(action_frame, text="Print All Current Job", command=self.print_all_current)
        print_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(action_frame, text="Clear Current Job", command=self.clear_current_drawings)
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        export_btn = ttk.Button(action_frame, text="Export Package", command=self.export_package)
        export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        import_btn = ttk.Button(action_frame, text="Import Package", command=self.import_package)
        import_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        printer_setup_btn = ttk.Button(action_frame, text="Printer Setup", command=self.setup_printers)
        printer_setup_btn.pack(side=tk.LEFT, padx=(0, 5))
        
    def init_database(self):
        """Initialize the database connection"""
        self.conn = sqlite3.connect('drafting_tools.db')
        
        # Create printer configuration table if it doesn't exist
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS printer_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_size TEXT NOT NULL UNIQUE,
                printer_name TEXT NOT NULL,
                paper_type TEXT,
                orientation TEXT DEFAULT 'Portrait',
                created_date TEXT,
                updated_date TEXT
            )
        ''')
        self.conn.commit()
        
        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='printer_config'")
        if cursor.fetchone():
            print("Printer configuration table created successfully")
        else:
            print("ERROR: Failed to create printer configuration table")
        
        # Ensure drawings table has a 'printed' column for checkbox state
        try:
            cursor.execute("PRAGMA table_info(drawings)")
            cols = [r[1] for r in cursor.fetchall()]
            if 'printed' not in cols:
                cursor.execute("ALTER TABLE drawings ADD COLUMN printed INTEGER DEFAULT 0")
                self.conn.commit()
        except Exception:
            pass
        
    def load_projects(self):
        """Load all projects from the projects table"""
        try:
            cursor = self.conn.cursor()
            
            # Check if drawings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='drawings'
            """)
            drawings_table_exists = cursor.fetchone() is not None
            
            if drawings_table_exists:
                # Get all projects with drawing counts and completion state
                cursor.execute("""
                    SELECT p.job_number, p.customer_name, 
                           COALESCE(COUNT(d.id), 0) as drawing_count,
                           CASE 
                               WHEN (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                                    OR rd.is_completed = 1
                                    OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                               THEN 1 ELSE 0 END AS is_completed
                    FROM projects p
                    LEFT JOIN drawings d ON p.job_number = d.job_number
                    LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                    GROUP BY p.job_number, p.customer_name
                    ORDER BY p.job_number
                """)
            else:
                # Just get projects without drawing counts
                cursor.execute("""
                    SELECT job_number, customer_name
                    FROM projects 
                    ORDER BY job_number
                """)
            
            projects = cursor.fetchall()
            
            # Clear existing items
            for item in self.project_tree.get_children():
                self.project_tree.delete(item)
            
            # Add projects to tree
            for project in projects:
                if drawings_table_exists:
                    job_number, customer_name, drawing_count, is_completed = project
                    customer = customer_name or "Unknown"
                    # Hide completed projects unless toggle is on
                    if self.show_completed or int(is_completed) == 0:
                        self.project_tree.insert('', 'end', values=(
                            job_number,
                            customer,
                            drawing_count
                        ))
                else:
                    job_number, customer_name = project
                    customer = customer_name or "Unknown"
                    # Without drawings table, always show
                    self.project_tree.insert('', 'end', values=(job_number, customer, 0))
            
        except Exception as e:
            print(f"Error loading projects: {e}")
    
    def filter_projects(self, *args):
        """Filter projects based on search term"""
        search_term = self.project_search_var.get().lower()
        
        # Clear existing items
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # Reload all projects and filter
        try:
            cursor = self.conn.cursor()
            
            # Check if drawings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='drawings'
            """)
            drawings_table_exists = cursor.fetchone() is not None
            
            if drawings_table_exists:
                cursor.execute("""
                    SELECT p.job_number, p.customer_name, 
                           COALESCE(COUNT(d.id), 0) as drawing_count,
                           CASE 
                               WHEN (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                                    OR rd.is_completed = 1
                                    OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                               THEN 1 ELSE 0 END AS is_completed
                    FROM projects p
                    LEFT JOIN drawings d ON p.job_number = d.job_number
                    LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                    GROUP BY p.job_number, p.customer_name
                    ORDER BY p.job_number
                """)
            else:
                cursor.execute("""
                    SELECT job_number, customer_name
                    FROM projects 
                    ORDER BY job_number
                """)
            
            projects = cursor.fetchall()
            
            for project in projects:
                if drawings_table_exists:
                    job_number, customer_name, drawing_count, is_completed = project
                    customer = customer_name or "Unknown"
                    
                    # Filter based on search term
                    if (search_term in str(job_number).lower() or 
                        search_term in customer.lower()):
                        if self.show_completed or int(is_completed) == 0:
                            self.project_tree.insert('', 'end', values=(
                                job_number,
                                customer,
                                drawing_count
                            ))
                else:
                    job_number, customer_name = project
                    customer = customer_name or "Unknown"
                    
                    # Filter based on search term
                    if (search_term in str(job_number).lower() or 
                        search_term in customer.lower()):
                        self.project_tree.insert('', 'end', values=(job_number, customer, 0))
            
        except Exception as e:
            print(f"Error filtering projects: {e}")

    def toggle_completed(self):
        """Toggle showing/hiding projects with drawings (completed)"""
        self.show_completed = not self.show_completed
        self.toggle_completed_btn.config(text=('Hide Completed' if self.show_completed else 'Show Completed'))
        self.load_projects()
    
    def on_project_select(self, event):
        """Handle project selection"""
        selection = self.project_tree.selection()
        if selection:
            item = self.project_tree.item(selection[0])
            job_number = item['values'][0]
            customer = item['values'][1]
            self.current_project = job_number
            
            # Update current job label
            self.current_job_label.config(text=f"{job_number} - {customer}")
            
            # Load drawings for this project
            self.load_current_drawings()
    
    def load_current_drawings(self):
        """Load drawings for the current project"""
        if not self.current_project:
            return
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT drawing_name, drawing_type, drawing_path, file_extension, COALESCE(printed,0)
                FROM drawings 
                WHERE job_number = ?
                ORDER BY drawing_name
            """, (self.current_project,))
            
            drawings = cursor.fetchall()
            
            # Clear existing items
            for item in self.current_drawings_tree.get_children():
                self.current_drawings_tree.delete(item)
            
            # Add drawings to tree
            for drawing in drawings:
                drawing_name, drawing_type, drawing_path, file_extension, printed = drawing
                display_type = drawing_type or file_extension or "Unknown"
                
                # Add to tree with action text
                item = self.current_drawings_tree.insert('', 'end', values=(
                    '✅' if printed else '☐',
                    drawing_name,
                    display_type,
                    drawing_path,
                    "Open | Print | Delete"  # Action text
                ))
                
                # Store the drawing path for later use
                self.current_drawings_tree.set(item, 'Actions', 'Open | Print | Delete')
            
        except Exception as e:
            print(f"Error loading current drawings: {e}")
    
    def search_global_drawings(self, *args):
        """Search for drawings globally across all jobs"""
        search_term = self.global_search_var.get().lower()
        
        if not search_term:
            # Clear global search results
            for item in self.global_drawings_tree.get_children():
                self.global_drawings_tree.delete(item)
            return
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT job_number, drawing_name, drawing_type, drawing_path, file_extension
                FROM drawings 
                WHERE LOWER(drawing_name) LIKE ? OR LOWER(drawing_path) LIKE ?
                ORDER BY job_number, drawing_name
            """, (f'%{search_term}%', f'%{search_term}%'))
            
            drawings = cursor.fetchall()
            
            # Clear existing items
            for item in self.global_drawings_tree.get_children():
                self.global_drawings_tree.delete(item)
            
            # Add drawings to tree
            for drawing in drawings:
                job_number, drawing_name, drawing_type, drawing_path, file_extension = drawing
                display_type = drawing_type or file_extension or "Unknown"
                
                # Add to tree
                self.global_drawings_tree.insert('', 'end', values=(
                    job_number,
                    drawing_name,
                    display_type,
                    drawing_path,
                    ""  # Actions column
                ))
            
        except Exception as e:
            print(f"Error searching global drawings: {e}")
    
    def browse_drawing(self):
        """Browse for a drawing file"""
        filename = filedialog.askopenfilename(
            title="Select Drawing File",
            filetypes=[
                ("Drawing files", "*.dwg *.idw *.pdf"),
                ("AutoCAD files", "*.dwg"),
                ("Inventor files", "*.idw"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            # Normalize the path to ensure it's properly formatted
            normalized_path = os.path.normpath(filename)
            self.drawing_path_var.set(normalized_path)
    
    def add_drawing(self):
        """Add a drawing to the current job"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        drawing_path = self.drawing_path_var.get().strip()
        if not drawing_path:
            messagebox.showwarning("Warning", "Please enter or browse for a drawing path")
            return
        
        # Remove quotes if present (from copy/paste)
        drawing_path = drawing_path.strip('"\'')
        
        # Normalize the path to handle different path formats
        drawing_path = os.path.normpath(drawing_path)
        
        if not os.path.exists(drawing_path):
            # Try to provide more helpful error message
            error_msg = f"Drawing file does not exist:\n{drawing_path}\n\nPlease check the file path and try again."
            messagebox.showerror("Error", error_msg)
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Extract drawing information
            drawing_name = os.path.basename(drawing_path)
            file_extension = os.path.splitext(drawing_path)[1].lower()
            
            # Determine drawing type based on extension
            if file_extension == '.dwg':
                drawing_type = 'AutoCAD'
            elif file_extension == '.idw':
                drawing_type = 'Inventor'
            elif file_extension == '.pdf':
                drawing_type = 'PDF'
            else:
                drawing_type = 'Other'
            
            # Insert drawing
            cursor.execute("""
                INSERT INTO drawings (job_number, drawing_path, drawing_name, drawing_type, 
                                   file_extension, added_date, added_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.current_project, drawing_path, drawing_name, drawing_type, 
                  file_extension, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User"))
            
            self.conn.commit()
            
            # Clear the path entry
            self.drawing_path_var.set("")
            
            # Refresh the current drawings list
            self.load_current_drawings()
            
            # Refresh the project list to update drawing counts
            self.load_projects()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add drawing: {str(e)}")
    
    def open_drawing(self, drawing_path):
        """Open a drawing file"""
        try:
            if os.path.exists(drawing_path):
                os.startfile(drawing_path)
            else:
                messagebox.showerror("Error", "Drawing file not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open drawing: {str(e)}")
    
    def print_drawing(self, drawing_path):
        """Print a drawing file directly to the correct printer"""
        try:
            if os.path.exists(drawing_path):
                # Detect paper size and get appropriate printer
                paper_size = self.detect_paper_size_from_drawing(drawing_path)
                printer_name = self.get_printer_for_size(paper_size)
                
                if printer_name:
                    # Ask for quantity
                    quantity = self.get_print_quantity()
                    if quantity is None:  # User cancelled
                        return
                    
                    # Print directly to the configured printer
                    success = self.print_file_direct(drawing_path, printer_name, quantity)
                    
                    if success:
                        print(f"Printed {quantity} copies of {os.path.basename(drawing_path)} (Size {paper_size}) to {printer_name}")
                        messagebox.showinfo("Success", 
                                          f"Successfully printed {quantity} copies of {os.path.basename(drawing_path)} to {printer_name}")
                    else:
                        messagebox.showerror("Error", f"Failed to print {os.path.basename(drawing_path)}")
                else:
                    messagebox.showinfo("Info", "Print cancelled - no printer selected")
            else:
                messagebox.showerror("Error", "Drawing file not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print drawing: {str(e)}")
    
    def get_print_quantity(self):
        """Get print quantity from user"""
        try:
            from tkinter import simpledialog
            
            quantity = simpledialog.askinteger(
                "Print Quantity",
                "How many copies would you like to print?",
                initialvalue=1,
                minvalue=1,
                maxvalue=10
            )
            return quantity
        except Exception as e:
            print(f"Error getting quantity: {e}")
            return 1
    
    def print_file_direct(self, file_path, printer_name, quantity=1):
        """Print file directly to specified printer"""
        try:
            print(f"Printing {quantity} copies of {os.path.basename(file_path)} to {printer_name}")
            
            # Get file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.dwg':
                # For DWG files, we need to use AutoCAD or a different approach
                return self.print_dwg_file(file_path, printer_name, quantity)
            elif file_ext == '.idw':
                # For IDW files, we need to use Inventor or a different approach
                return self.print_idw_file(file_path, printer_name, quantity)
            else:
                # For other files (PDF, etc.), use Windows Shell
                return self.print_other_file(file_path, printer_name, quantity)
                
        except Exception as e:
            print(f"Error printing file: {e}")
            return False
    
    def print_dwg_file(self, dwg_path, printer_name, quantity=1):
        """Print DWG file using AutoCAD or fallback method"""
        try:
            print(f"Attempting to print DWG file: {os.path.basename(dwg_path)}")
            
            # Try to use AutoCAD to print
            try:
                import win32api
                
                # Try to open with AutoCAD and print
                result = win32api.ShellExecute(
                    0,  # hwnd
                    "open",  # operation
                    dwg_path,  # file
                    None,  # parameters
                    None,  # directory
                    1  # show command (SW_SHOWNORMAL)
                )
                
                if result > 32:  # Success
                    print(f"Opened DWG file in AutoCAD - user can print manually")
                    messagebox.showinfo("DWG File Opened", 
                                      f"DWG file opened in AutoCAD.\n\n"
                                      f"Please print {quantity} copies manually to {printer_name}.\n\n"
                                      f"File: {os.path.basename(dwg_path)}")
                    return True
                else:
                    print(f"Failed to open DWG file: {result}")
                    return False
                    
            except Exception as e:
                print(f"Error opening DWG file: {e}")
                return False
                
        except Exception as e:
            print(f"Error printing DWG file: {e}")
            return False
    
    def print_idw_file(self, idw_path, printer_name, quantity=1):
        """Open IDW in Inventor for manual printing with iLogic rules."""
        try:
            print(f"Opening {os.path.basename(idw_path)} in Inventor for manual printing...")
            
            # Just open the file in Inventor - let user handle the printing
            import win32api
            
            result = win32api.ShellExecute(
                0,  # hwnd
                "open",  # operation
                idw_path,  # file
                None,  # parameters
                None,  # directory
                1  # show command (SW_SHOWNORMAL)
            )
            
            if result > 32:  # Success
                print(f"Opened {os.path.basename(idw_path)} in Inventor")
                messagebox.showinfo("IDW File Opened", 
                                  f"IDW file opened in Inventor.\n\n"
                                  f"Please use the iLogic rules to print {quantity} copies:\n\n"
                                  f"• A-size: PrintDraftingPrinterLetter.vb\n"
                                  f"• B-size: PrintDraftingPrinter11x17.vb\n"
                                  f"• C-size: Plotter18x24.vb\n"
                                  f"• D-size: Plotter24x36.vb\n\n"
                                  f"File: {os.path.basename(idw_path)}")
                return True
            else:
                print(f"Failed to open IDW file: {result}")
                messagebox.showerror("Error", f"Failed to open {os.path.basename(idw_path)} in Inventor")
                return False
                
        except Exception as e:
            print(f"Error opening IDW file: {e}")
            messagebox.showerror("Error", f"Failed to open IDW file: {str(e)}")
            return False
    
    def print_other_file(self, file_path, printer_name, quantity=1):
        """Print other file types (PDF, etc.) using Windows Shell"""
        try:
            # Use Windows Shell to print file directly
            import win32api
            
            # Print multiple copies
            for i in range(quantity):
                result = win32api.ShellExecute(
                    0,  # hwnd
                    "print",  # operation
                    file_path,  # file
                    f'/d:"{printer_name}"',  # parameters
                    None,  # directory
                    0  # show command
                )
                
                if result > 32:  # Success
                    print(f"Successfully sent copy {i+1}/{quantity} to {printer_name}")
                else:
                    print(f"Failed to print copy {i+1} to {printer_name}: {result}")
                    return False
            
            return True
                
        except ImportError:
            # Fallback: Use subprocess
            try:
                for i in range(quantity):
                    result = subprocess.run([
                        'cmd', '/c', 'print', f'/d:"{printer_name}"', file_path
                    ], check=False, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"Successfully printed copy {i+1}/{quantity} to {printer_name}")
                    else:
                        print(f"Print command failed for copy {i+1}: {result.stderr}")
                        return False
                return True
            except Exception as e:
                print(f"Subprocess print failed: {e}")
                return False
        except Exception as e:
            print(f"Error printing file: {e}")
            return False
    
    def convert_drawing_to_pdf(self, drawing_path, paper_size):
        """Convert drawing file to PDF and save in job folder"""
        try:
            if not self.current_project:
                messagebox.showwarning("Warning", "No project selected")
                return None
            
            # Get job directory
            cursor = self.conn.cursor()
            cursor.execute("SELECT job_directory FROM projects WHERE job_number = ?", (self.current_project,))
            job_dir_result = cursor.fetchone()
            
            if not job_dir_result or not job_dir_result[0]:
                messagebox.showwarning("Warning", "Job directory not found")
                return None
            
            job_directory = job_dir_result[0]
            
            # Create PDF export folder
            pdf_folder = os.path.join(job_directory, f"{self.current_project}-Supporting BOM Drawing Package Exports")
            if not os.path.exists(pdf_folder):
                os.makedirs(pdf_folder, exist_ok=True)
                print(f"Created PDF export folder: {pdf_folder}")
            
            # Generate PDF filename
            drawing_name = os.path.splitext(os.path.basename(drawing_path))[0]
            pdf_filename = f"{self.current_project}-{drawing_name}.pdf"
            pdf_path = os.path.join(pdf_folder, pdf_filename)
            
            # Check if PDF already exists
            if os.path.exists(pdf_path):
                print(f"PDF already exists: {pdf_path}")
                return pdf_path
            
            # Get file extension
            file_ext = os.path.splitext(drawing_path)[1].lower()
            
            if file_ext == '.dwg':
                # Convert AutoCAD drawing to PDF using Windows print to PDF
                success = self.print_dwg_to_pdf(drawing_path, pdf_path, paper_size)
            elif file_ext == '.idw':
                # Convert Inventor drawing to PDF using Windows print to PDF
                success = self.print_idw_to_pdf(drawing_path, pdf_path, paper_size)
            elif file_ext == '.pdf':
                # Already a PDF, just copy it
                import shutil
                shutil.copy2(drawing_path, pdf_path)
                success = True
            else:
                # Unsupported file type
                messagebox.showerror("Error", f"Unsupported file type: {file_ext}")
                return None
            
            if success and os.path.exists(pdf_path):
                print(f"Successfully created PDF: {pdf_path}")
                return pdf_path
            else:
                print(f"Failed to create PDF: {pdf_path}")
                return None
                
        except Exception as e:
            print(f"Error converting drawing to PDF: {e}")
            return None
    
    def print_dwg_to_pdf(self, dwg_path, pdf_path, paper_size):
        """Print DWG file to PDF and save to specified location"""
        try:
            print(f"Printing {os.path.basename(dwg_path)} to PDF...")
            
            # For now, let's use a simpler approach - just copy the DWG and rename it
            # This is a placeholder until we can implement proper PDF conversion
            import shutil
            
            # Create a temporary PDF file with drawing info
            temp_pdf = pdf_path.replace('.pdf', '_temp.pdf')
            
            try:
                from reportlab.lib.pagesizes import letter, legal, A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.units import inch
                
                # Get paper size dimensions
                size_dimensions = {
                    'A': (11, 8.5),    # 8.5T x 11W (landscape)
                    'B': (17, 11),     # 11T x 17W (landscape) 
                    'C': (24, 18),     # 18T x 24W (landscape)
                    'D': (36, 24)      # 24T x 36W (landscape)
                }
                
                width, height = size_dimensions.get(paper_size, (11, 8.5))
                
                # Create PDF with drawing info
                c = canvas.Canvas(temp_pdf, pagesize=(width * inch, height * inch))
                
                # Add content
                c.setFont("Helvetica-Bold", 24)
                c.drawString(1 * inch, height * inch - 1.5 * inch, f"DRAWING: {os.path.basename(dwg_path)}")
                
                c.setFont("Helvetica", 16)
                c.drawString(1 * inch, height * inch - 2.5 * inch, f"Original File: {dwg_path}")
                c.drawString(1 * inch, height * inch - 3 * inch, f"Paper Size: {paper_size} ({width}\" x {height}\")")
                c.drawString(1 * inch, height * inch - 3.5 * inch, f"Converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                c.drawString(1 * inch, height * inch - 4 * inch, f"Job Number: {self.current_project}")
                c.drawString(1 * inch, height * inch - 4.5 * inch, f"NOTE: This is a placeholder PDF. The actual drawing")
                c.drawString(1 * inch, height * inch - 5 * inch, f"should be opened and printed manually.")
                
                # Add border
                c.rect(0.5 * inch, 0.5 * inch, (width - 1) * inch, (height - 1) * inch)
                
                # Add corner marks
                corner_size = 0.5 * inch
                c.rect(0.5 * inch, 0.5 * inch, corner_size, corner_size)
                c.rect((width - 1) * inch, 0.5 * inch, corner_size, corner_size)
                c.rect(0.5 * inch, (height - 1) * inch, corner_size, corner_size)
                c.rect((width - 1) * inch, (height - 1) * inch, corner_size, corner_size)
                
                c.save()
                
                # Move to final location
                shutil.move(temp_pdf, pdf_path)
                print(f"Created PDF placeholder: {pdf_path}")
                return True
                
            except ImportError:
                # Fallback: create a simple text file
                txt_path = pdf_path.replace('.pdf', '.txt')
                with open(txt_path, 'w') as f:
                    f.write(f"DRAWING: {os.path.basename(dwg_path)}\n")
                    f.write(f"Original File: {dwg_path}\n")
                    f.write(f"Paper Size: {paper_size}\n")
                    f.write(f"Converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Job Number: {self.current_project}\n")
                    f.write(f"NOTE: This is a placeholder. The actual drawing should be opened and printed manually.\n")
                print(f"Created text placeholder: {txt_path}")
                return True
            
        except Exception as e:
            print(f"Error creating DWG PDF: {e}")
            return False
    
    def print_idw_to_pdf(self, idw_path, pdf_path, paper_size):
        """Print IDW file to PDF and save to specified location"""
        try:
            print(f"Printing {os.path.basename(idw_path)} to PDF...")
            
            # For now, let's use a simpler approach - just copy the IDW and rename it
            # This is a placeholder until we can implement proper PDF conversion
            import shutil
            
            # Create a temporary PDF file with drawing info
            temp_pdf = pdf_path.replace('.pdf', '_temp.pdf')
            
            try:
                from reportlab.lib.pagesizes import letter, legal, A4
                from reportlab.pdfgen import canvas
                from reportlab.lib.units import inch
                
                # Get paper size dimensions
                size_dimensions = {
                    'A': (11, 8.5),    # 8.5T x 11W (landscape)
                    'B': (17, 11),     # 11T x 17W (landscape) 
                    'C': (24, 18),     # 18T x 24W (landscape)
                    'D': (36, 24)      # 24T x 36W (landscape)
                }
                
                width, height = size_dimensions.get(paper_size, (11, 8.5))
                
                # Create PDF with drawing info
                c = canvas.Canvas(temp_pdf, pagesize=(width * inch, height * inch))
                
                # Add content
                c.setFont("Helvetica-Bold", 24)
                c.drawString(1 * inch, height * inch - 1.5 * inch, f"DRAWING: {os.path.basename(idw_path)}")
                
                c.setFont("Helvetica", 16)
                c.drawString(1 * inch, height * inch - 2.5 * inch, f"Original File: {idw_path}")
                c.drawString(1 * inch, height * inch - 3 * inch, f"Paper Size: {paper_size} ({width}\" x {height}\")")
                c.drawString(1 * inch, height * inch - 3.5 * inch, f"Converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                c.drawString(1 * inch, height * inch - 4 * inch, f"Job Number: {self.current_project}")
                c.drawString(1 * inch, height * inch - 4.5 * inch, f"NOTE: This is a placeholder PDF. The actual drawing")
                c.drawString(1 * inch, height * inch - 5 * inch, f"should be opened and printed manually.")
                
                # Add border
                c.rect(0.5 * inch, 0.5 * inch, (width - 1) * inch, (height - 1) * inch)
                
                # Add corner marks
                corner_size = 0.5 * inch
                c.rect(0.5 * inch, 0.5 * inch, corner_size, corner_size)
                c.rect((width - 1) * inch, 0.5 * inch, corner_size, corner_size)
                c.rect(0.5 * inch, (height - 1) * inch, corner_size, corner_size)
                c.rect((width - 1) * inch, (height - 1) * inch, corner_size, corner_size)
                
                c.save()
                
                # Move to final location
                shutil.move(temp_pdf, pdf_path)
                print(f"Created PDF placeholder: {pdf_path}")
                return True
                
            except ImportError:
                # Fallback: create a simple text file
                txt_path = pdf_path.replace('.pdf', '.txt')
                with open(txt_path, 'w') as f:
                    f.write(f"DRAWING: {os.path.basename(idw_path)}\n")
                    f.write(f"Original File: {idw_path}\n")
                    f.write(f"Paper Size: {paper_size}\n")
                    f.write(f"Converted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Job Number: {self.current_project}\n")
                    f.write(f"NOTE: This is a placeholder. The actual drawing should be opened and printed manually.\n")
                print(f"Created text placeholder: {txt_path}")
                return True
            
        except Exception as e:
            print(f"Error creating IDW PDF: {e}")
            return False
    
    def convert_autocad_to_pdf(self, dwg_path, pdf_path, paper_size):
        """Convert AutoCAD drawing to PDF using Windows print to PDF"""
        try:
            print(f"Converting {os.path.basename(dwg_path)} to PDF...")
            
            # Use Windows Shell to print DWG directly to PDF
            # This will use the default PDF printer and create a proper PDF
            try:
                import win32api
                import win32print
                
                # Print the DWG file directly to PDF using Windows Shell
                result = win32api.ShellExecute(
                    0,  # hwnd
                    "print",  # operation
                    dwg_path,  # file
                    f'/d:"Microsoft Print to PDF"',  # parameters
                    None,  # directory
                    0  # show command
                )
                
                if result > 32:  # Success
                    print(f"Successfully initiated print to PDF for {os.path.basename(dwg_path)}")
                    return True
                else:
                    print(f"Failed to print DWG to PDF: {result}")
                    return False
                    
            except ImportError:
                # Fallback: Use subprocess to print
                try:
                    result = subprocess.run([
                        'cmd', '/c', 'print', '/d:"Microsoft Print to PDF"', dwg_path
                    ], check=False, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"Successfully printed DWG to PDF")
                        return True
                    else:
                        print(f"Print command failed: {result.stderr}")
                        return False
                except Exception as e:
                    print(f"Subprocess print failed: {e}")
                    return False
            
        except Exception as e:
            print(f"Error converting AutoCAD to PDF: {e}")
            return False
    
    def convert_inventor_to_pdf(self, idw_path, pdf_path, paper_size):
        """Convert Inventor drawing to PDF using Windows print to PDF"""
        try:
            print(f"Converting {os.path.basename(idw_path)} to PDF...")
            
            # Use Windows Shell to print IDW directly to PDF
            # This will use the default PDF printer and create a proper PDF
            try:
                import win32api
                import win32print
                
                # Print the IDW file directly to PDF using Windows Shell
                result = win32api.ShellExecute(
                    0,  # hwnd
                    "print",  # operation
                    idw_path,  # file
                    f'/d:"Microsoft Print to PDF"',  # parameters
                    None,  # directory
                    0  # show command
                )
                
                if result > 32:  # Success
                    print(f"Successfully initiated print to PDF for {os.path.basename(idw_path)}")
                    return True
                else:
                    print(f"Failed to print IDW to PDF: {result}")
                    return False
                    
            except ImportError:
                # Fallback: Use subprocess to print
                try:
                    result = subprocess.run([
                        'cmd', '/c', 'print', '/d:"Microsoft Print to PDF"', idw_path
                    ], check=False, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"Successfully printed IDW to PDF")
                        return True
                    else:
                        print(f"Print command failed: {result.stderr}")
                        return False
                except Exception as e:
                    print(f"Subprocess print failed: {e}")
                    return False
            
        except Exception as e:
            print(f"Error converting Inventor to PDF: {e}")
            return False
    
    def get_paper_dimensions(self, paper_size):
        """Get paper dimensions as a string"""
        size_dimensions = {
            'A': (11, 8.5),    # 8.5T x 11W (landscape)
            'B': (17, 11),     # 11T x 17W (landscape) 
            'C': (24, 18),     # 18T x 24W (landscape)
            'D': (36, 24)      # 24T x 36W (landscape)
        }
        
        width, height = size_dimensions.get(paper_size, (11, 8.5))
        return f"{width}\" x {height}\""
    
    def print_autocad_drawing(self, dwg_path, printer_name, paper_size):
        """Print AutoCAD drawing with proper settings - fit to paper"""
        try:
            # Get paper size dimensions (width x height in inches)
            size_dimensions = {
                'A': (11, 8.5),    # 8.5T x 11W (landscape)
                'B': (17, 11),     # 11T x 17W (landscape) 
                'C': (24, 18),     # 18T x 24W (landscape)
                'D': (36, 24)      # 24T x 36W (landscape)
            }
            
            width, height = size_dimensions.get(paper_size, (11, 8.5))
            
            # Create AutoCAD script for printing with fit to paper
            script_content = f"""
; AutoCAD print script - Fit to Paper
; Open the drawing
OPEN
{dwg_path}
; Start plot command
-PLOT
; Use plotter
Y
; Select printer
{printer_name}
; Paper size (width x height in inches)
{width}x{height}
; Orientation (landscape)
L
; Plot area - EXTENTS (fits entire drawing)
E
; Scale - FIT TO PAPER
F
; Center the plot
Y
; Plot with extents
Y
; Execute plot
Y
; Close drawing
CLOSE
; Quit AutoCAD
QUIT
Y
"""
            
            # Write script to temporary file
            script_file = f"print_script_{paper_size}.scr"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Try different AutoCAD executable paths
            acad_paths = [
                'acad.exe',
                'C:\\Program Files\\Autodesk\\AutoCAD 2024\\acad.exe',
                'C:\\Program Files\\Autodesk\\AutoCAD 2023\\acad.exe',
                'C:\\Program Files\\Autodesk\\AutoCAD 2022\\acad.exe',
                'C:\\Program Files\\Autodesk\\AutoCAD 2021\\acad.exe'
            ]
            
            success = False
            for acad_path in acad_paths:
                try:
                    result = subprocess.run([
                        acad_path, '/s', script_file
                    ], check=False, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        success = True
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            # Clean up script file
            try:
                os.remove(script_file)
            except:
                pass
            
            return success
            
        except Exception as e:
            print(f"Error printing AutoCAD drawing: {e}")
            # Fallback to generic print
            return self.print_generic_file(dwg_path, printer_name)
    
    def print_inventor_drawing(self, idw_path, printer_name, paper_size):
        """Print Inventor drawing with proper settings - fit to paper"""
        try:
            # Get paper size dimensions (width x height in inches)
            size_dimensions = {
                'A': (11, 8.5),    # 8.5T x 11W (landscape)
                'B': (17, 11),     # 11T x 17W (landscape) 
                'C': (24, 18),     # 18T x 24W (landscape)
                'D': (36, 24)      # 24T x 36W (landscape)
            }
            
            width, height = size_dimensions.get(paper_size, (11, 8.5))
            
            # Create Inventor script for printing with fit to paper
            script_content = f"""
; Inventor print script - Fit to Paper
; Open the drawing
OPEN
{idw_path}
; Start print command
PRINT
; Select printer
{printer_name}
; Paper size (width x height in inches)
{width}x{height}
; Orientation (landscape)
LANDSCAPE
; Scale - FIT TO PAPER
FIT
; Print
PRINT
; Close drawing
CLOSE
; Quit Inventor
QUIT
Y
"""
            
            # Write script to temporary file
            script_file = f"inventor_print_{paper_size}.scr"
            with open(script_file, 'w') as f:
                f.write(script_content)
            
            # Try different Inventor executable paths
            inventor_paths = [
                'inventor.exe',
                'C:\\Program Files\\Autodesk\\Inventor 2024\\Bin\\Inventor.exe',
                'C:\\Program Files\\Autodesk\\Inventor 2023\\Bin\\Inventor.exe',
                'C:\\Program Files\\Autodesk\\Inventor 2022\\Bin\\Inventor.exe',
                'C:\\Program Files\\Autodesk\\Inventor 2021\\Bin\\Inventor.exe'
            ]
            
            success = False
            for inventor_path in inventor_paths:
                try:
                    result = subprocess.run([
                        inventor_path, '/s', script_file
                    ], check=False, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        success = True
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            # Clean up script file
            try:
                os.remove(script_file)
            except:
                pass
            
            return success
            
        except Exception as e:
            print(f"Error printing Inventor drawing: {e}")
            # Fallback to generic print
            return self.print_generic_file(idw_path, printer_name)
    
    def print_generic_file(self, file_path, printer_name):
        """Generic file printing fallback"""
        try:
            result = subprocess.run(['cmd', '/c', 'print', f'/d:{printer_name}', file_path], 
                                  check=False, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error printing generic file: {e}")
            return False
    
    def print_with_windows_shell(self, file_path, printer_name, paper_size):
        """Print using Windows Shell API for better compatibility"""
        try:
            import win32api
            import win32print
            
            # Get paper size dimensions
            size_dimensions = {
                'A': (11, 8.5),    # 8.5T x 11W (landscape)
                'B': (17, 11),     # 11T x 17W (landscape) 
                'C': (24, 18),     # 18T x 24W (landscape)
                'D': (36, 24)      # 24T x 36W (landscape)
            }
            
            width, height = size_dimensions.get(paper_size, (11, 8.5))
            
            # Use Windows Shell to print
            win32api.ShellExecute(
                0,
                "print",
                file_path,
                f'/d:"{printer_name}"',
                ".",
                0
            )
            return True
            
        except ImportError:
            # Fallback if win32api not available
            return self.print_generic_file(file_path, printer_name)
        except Exception as e:
            print(f"Error printing with Windows Shell: {e}")
            return self.print_generic_file(file_path, printer_name)
    
    def get_printer_name(self):
        """Get printer name from user or use default"""
        try:
            # Try to get default printer
            import win32print
            default_printer = win32print.GetDefaultPrinter()
            
            # Ask user if they want to use default printer or choose another
            choice = messagebox.askyesnocancel(
                "Print Options",
                f"Default printer: {default_printer}\n\n"
                f"Yes = Use Default Printer\n"
                f"No = Choose Different Printer\n"
                f"Cancel = Print to PDF"
            )
            
            if choice is True:  # Use default printer
                return default_printer
            elif choice is False:  # Choose different printer
                return self.choose_printer()
            else:  # Cancel - print to PDF
                return "Microsoft Print to PDF"
                
        except ImportError:
            # Fallback if win32print not available
            return self.choose_printer()
        except Exception as e:
            print(f"Error getting default printer: {e}")
            return self.choose_printer()
    
    def choose_printer(self):
        """Let user choose a printer"""
        try:
            import win32print
            
            # Get list of available printers
            printers = []
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                printers.append(printer[2])  # printer[2] is the printer name
            
            if not printers:
                messagebox.showwarning("Warning", "No printers found. Using PDF printer.")
                return "Microsoft Print to PDF"
            
            # Create a simple printer selection dialog
            printer_window = tk.Toplevel(self.root)
            printer_window.title("Select Printer")
            printer_window.geometry("400x300")
            printer_window.transient(self.root)
            printer_window.grab_set()
            
            # Center the window
            printer_window.update_idletasks()
            x = (printer_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (printer_window.winfo_screenheight() // 2) - (300 // 2)
            printer_window.geometry(f"400x300+{x}+{y}")
            
            selected_printer = tk.StringVar(value=printers[0])
            
            ttk.Label(printer_window, text="Select Printer:", font=("Arial", 12, "bold")).pack(pady=10)
            
            # Printer listbox
            printer_frame = ttk.Frame(printer_window)
            printer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            printer_listbox = tk.Listbox(printer_frame, font=("Arial", 10))
            printer_listbox.pack(fill=tk.BOTH, expand=True)
            
            for printer in printers:
                printer_listbox.insert(tk.END, printer)
            
            # Bind selection
            def on_select(event):
                selection = printer_listbox.curselection()
                if selection:
                    selected_printer.set(printer_listbox.get(selection[0]))
            
            printer_listbox.bind('<<ListboxSelect>>', on_select)
            
            # Buttons
            button_frame = ttk.Frame(printer_window)
            button_frame.pack(fill=tk.X, padx=20, pady=10)
            
            result = [None]  # Use list to store result from nested function
            
            def on_ok():
                result[0] = selected_printer.get()
                printer_window.destroy()
            
            def on_cancel():
                result[0] = None
                printer_window.destroy()
            
            def on_pdf():
                result[0] = "Microsoft Print to PDF"
                printer_window.destroy()
            
            ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(button_frame, text="Print to PDF", command=on_pdf).pack(side=tk.RIGHT)
            
            # Wait for window to close
            printer_window.wait_window()
            
            return result[0]
            
        except ImportError:
            messagebox.showwarning("Warning", "Printer selection not available. Using PDF printer.")
            return "Microsoft Print to PDF"
        except Exception as e:
            print(f"Error choosing printer: {e}")
            return "Microsoft Print to PDF"
    
    def delete_drawing(self, drawing_path):
        """Delete a drawing from the current job"""
        if not self.current_project:
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this drawing?"):
            try:
                cursor = self.conn.cursor()
                
                cursor.execute("DELETE FROM drawings WHERE job_number = ? AND drawing_path = ?", 
                             (self.current_project, drawing_path))
                
                self.conn.commit()
                
                # Refresh the current drawings list
                self.load_current_drawings()
                
                # Refresh the project list to update drawing counts
                self.load_projects()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete drawing: {str(e)}")

    def on_current_drawing_click(self, event):
        """Toggle printed state when clicking the Printed column"""
        try:
            region = self.current_drawings_tree.identify('region', event.x, event.y)
            if region != 'cell':
                return
            row_id = self.current_drawings_tree.identify_row(event.y)
            col_id = self.current_drawings_tree.identify_column(event.x)
            if not row_id or col_id != '#1':  # '#1' corresponds to 'Printed' column
                return
            drawing_path = self.current_drawings_tree.set(row_id, 'Path')
            current = self.current_drawings_tree.set(row_id, 'Printed')
            new_state = 0 if current == '✅' else 1
            cursor = self.conn.cursor()
            cursor.execute("UPDATE drawings SET printed = ? WHERE job_number = ? AND drawing_path = ?", (new_state, self.current_project, drawing_path))
            self.conn.commit()
            # Update UI
            self.current_drawings_tree.set(row_id, 'Printed', '✅' if new_state else '☐')
        except Exception as e:
            print(f"Error toggling printed state: {e}")

    def clear_all_printed(self):
        """Clear all printed checkboxes for the current job"""
        if not self.current_project:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE drawings SET printed = 0 WHERE job_number = ?", (self.current_project,))
            self.conn.commit()
            self.load_current_drawings()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear checkboxes: {str(e)}")
    
    def print_all_current(self):
        """Print all drawings for the current job"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT drawing_path FROM drawings WHERE job_number = ?", (self.current_project,))
            drawings = cursor.fetchall()
            
            if not drawings:
                messagebox.showinfo("Info", "No drawings found for this project")
                return
            
            # Ask for quantity once for all drawings
            quantity = self.get_print_quantity()
            if quantity is None:  # User cancelled
                return
            
            printed_count = 0
            failed_count = 0
            size_summary = {}
            
            # Print each drawing using size-based printer selection
            for drawing in drawings:
                drawing_path = drawing[0]
                if os.path.exists(drawing_path):
                    try:
                        # Detect paper size and get appropriate printer
                        paper_size = self.detect_paper_size_from_drawing(drawing_path)
                        printer_name = self.get_printer_for_size(paper_size)
                        
                        if printer_name:
                            # Print directly to the configured printer
                            success = self.print_file_direct(drawing_path, printer_name, quantity)
                            if success:
                                printed_count += 1
                                
                                # Track size summary
                                if paper_size not in size_summary:
                                    size_summary[paper_size] = {'count': 0, 'printer': printer_name}
                                size_summary[paper_size]['count'] += 1
                                
                                print(f"Printed {quantity} copies of {os.path.basename(drawing_path)} (Size {paper_size}) to {printer_name}")
                            else:
                                failed_count += 1
                                print(f"Failed to print {os.path.basename(drawing_path)}")
                        else:
                            print(f"No printer configured for size {paper_size}: {drawing_path}")
                            failed_count += 1
                    except Exception as e:
                        print(f"Failed to print {drawing_path}: {e}")
                        failed_count += 1
                else:
                    print(f"File not found: {drawing_path}")
                    failed_count += 1
            
            # Create detailed summary message
            summary_parts = [f"Print job completed!\n\nSuccessfully printed: {printed_count}\nFailed: {failed_count}\nQuantity per drawing: {quantity}"]
            
            if size_summary:
                summary_parts.append("\nSize Summary:")
                for size, info in size_summary.items():
                    summary_parts.append(f"Size {size}: {info['count']} drawings → {info['printer']}")
            
            messagebox.showinfo("Print Complete", "\n".join(summary_parts))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print drawings: {str(e)}")
    
    def clear_current_drawings(self):
        """Clear all drawings for the current job"""
        if not self.current_project:
            return
        
        if messagebox.askyesno("Confirm Clear", f"Are you sure you want to delete all drawings for job {self.current_project}?"):
            try:
                cursor = self.conn.cursor()
                
                cursor.execute("DELETE FROM drawings WHERE job_number = ?", (self.current_project,))
                
                self.conn.commit()
                
                # Refresh the current drawings list
                self.load_current_drawings()
                
                # Refresh the project list to update drawing counts
                self.load_projects()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear drawings: {str(e)}")
    
    def on_current_drawing_double_click(self, event):
        """Handle double-click on current drawings"""
        selection = self.current_drawings_tree.selection()
        if selection:
            item_id = selection[0]
            drawing_path = self.current_drawings_tree.set(item_id, 'Path')
            self.open_drawing(drawing_path)
    
    def on_current_drawing_right_click(self, event):
        """Handle right-click on current drawings"""
        selection = self.current_drawings_tree.selection()
        if selection:
            item_id = selection[0]
            drawing_path = self.current_drawings_tree.set(item_id, 'Path')
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Open", command=lambda: self.open_drawing(drawing_path))
            context_menu.add_command(label="Print", command=lambda: self.print_drawing(drawing_path))
            context_menu.add_separator()
            context_menu.add_command(label="Delete", command=lambda: self.delete_drawing(drawing_path))
            
            # Show context menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def on_global_drawing_double_click(self, event):
        """Handle double-click on global drawings"""
        selection = self.global_drawings_tree.selection()
        if selection:
            item_id = selection[0]
            drawing_path = self.global_drawings_tree.set(item_id, 'Path')
            self.open_drawing(drawing_path)
    
    def on_global_drawing_right_click(self, event):
        """Handle right-click on global drawings"""
        selection = self.global_drawings_tree.selection()
        if selection:
            item_id = selection[0]
            drawing_path = self.global_drawings_tree.set(item_id, 'Path')
            job_number = self.global_drawings_tree.set(item_id, 'Job Number')
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Open", command=lambda: self.open_drawing(drawing_path))
            context_menu.add_command(label="Print", command=lambda: self.print_drawing(drawing_path))
            context_menu.add_separator()
            context_menu.add_command(label="Add to Current Job", command=lambda: self.add_drawing_from_global(drawing_path, job_number))
            
            # Show context menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def add_drawing_from_global(self, drawing_path, source_job_number):
        """Add a drawing from global search to current job"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Get drawing info from source job
            cursor.execute("""
                SELECT drawing_name, drawing_type, file_extension
                FROM drawings 
                WHERE job_number = ? AND drawing_path = ?
            """, (source_job_number, drawing_path))
            
            drawing_info = cursor.fetchone()
            if not drawing_info:
                messagebox.showerror("Error", "Drawing not found in source job")
                return
            
            drawing_name, drawing_type, file_extension = drawing_info
            
            # Add to current job
            cursor.execute("""
                INSERT INTO drawings (job_number, drawing_path, drawing_name, drawing_type, 
                                   file_extension, added_date, added_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.current_project, drawing_path, drawing_name, drawing_type, 
                  file_extension, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "User"))
            
            self.conn.commit()
            
            # Refresh the current drawings list
            self.load_current_drawings()
            
            # Refresh the project list to update drawing counts
            self.load_projects()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add drawing: {str(e)}")
    
    def open_dashboard(self):
        """Open the dashboard application"""
        try:
            if os.path.exists('dashboard.py'):
                subprocess.Popen([sys.executable, 'dashboard.py'])
            else:
                messagebox.showerror("Error", "dashboard.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Dashboard:\n{str(e)}")
    
    def export_package(self):
        """Export the current job's print package to a file"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Get job directory from projects table
            cursor.execute("""
                SELECT job_directory FROM projects WHERE job_number = ?
            """, (self.current_project,))
            job_dir_result = cursor.fetchone()
            
            # Get drawings
            cursor.execute("""
                SELECT drawing_name, drawing_type, drawing_path, file_extension, added_date
                FROM drawings 
                WHERE job_number = ?
                ORDER BY drawing_name
            """, (self.current_project,))
            
            drawings = cursor.fetchall()
            
            if not drawings:
                messagebox.showinfo("Info", "No drawings found for this project")
                return
            
            # Create package data
            package_data = {
                'job_number': self.current_project,
                'export_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'exported_by': 'Print Package Manager',
                'total_drawings': len(drawings),
                'drawings': []
            }
            
            for drawing in drawings:
                drawing_name, drawing_type, drawing_path, file_extension, added_date = drawing
                package_data['drawings'].append({
                    'name': drawing_name,
                    'type': drawing_type,
                    'path': drawing_path,
                    'extension': file_extension,
                    'added_date': added_date
                })
            
            # Determine save location
            if job_dir_result and job_dir_result[0]:
                # Save to job directory
                job_directory = job_dir_result[0]
                if not os.path.exists(job_directory):
                    os.makedirs(job_directory, exist_ok=True)
                filename = os.path.join(job_directory, f"Print_Package_{self.current_project}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            else:
                # Save to current directory as fallback
                filename = f"print_package_{self.current_project}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Print package exported to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export package: {str(e)}")
    
    def import_package(self):
        """Import a print package from JSON file"""
        # Get the initial directory for the file picker
        initial_dir = None
        if self.current_project:
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT job_directory FROM projects WHERE job_number = ?
                """, (self.current_project,))
                job_dir_result = cursor.fetchone()
                
                if job_dir_result and job_dir_result[0] and os.path.exists(job_dir_result[0]):
                    initial_dir = job_dir_result[0]
                else:
                    # Fallback to current working directory
                    initial_dir = os.getcwd()
            except Exception as e:
                print(f"Error getting job directory: {e}")
                initial_dir = os.getcwd()
        else:
            # No project selected, use current working directory
            initial_dir = os.getcwd()
        
        filename = filedialog.askopenfilename(
            title="Select Print Package JSON File",
            initialdir=initial_dir,
            filetypes=[
                ("JSON files", "*.json"),
                ("Print Package files", "Print_Package_*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                package_data = json.load(f)
            
            # Validate package data
            if 'job_number' not in package_data or 'drawings' not in package_data:
                messagebox.showerror("Error", "Invalid print package file format")
                return
            
            # Ask user what to do with the package
            action = messagebox.askyesnocancel(
                "Import Print Package",
                f"Print Package for Job: {package_data.get('job_number', 'Unknown')}\n"
                f"Total Drawings: {len(package_data.get('drawings', []))}\n"
                f"Export Date: {package_data.get('export_date', 'Unknown')}\n\n"
                f"What would you like to do?\n\n"
                f"Yes = Print All Drawings\n"
                f"No = Add to Current Job\n"
                f"Cancel = Just View Package"
            )
            
            if action is True:  # Print all drawings
                self.print_from_package_data(package_data)
            elif action is False:  # Add to current job
                self.add_package_to_current_job(package_data)
            # Cancel = do nothing
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import package: {str(e)}")
    
    def print_from_package_data(self, package_data):
        """Print all drawings from package data"""
        drawings = package_data.get('drawings', [])
        if not drawings:
            messagebox.showinfo("Info", "No drawings found in package")
            return
        
        # Get printer selection once for all drawings
        printed_count = 0
        failed_count = 0
        size_summary = {}
        
        for drawing in drawings:
            drawing_path = drawing.get('path', '')
            drawing_name = drawing.get('name', 'Unknown')
            
            if os.path.exists(drawing_path):
                try:
                    # Detect paper size and get appropriate printer
                    paper_size = self.detect_paper_size_from_drawing(drawing_path)
                    printer_name = self.get_printer_for_size(paper_size)
                    
                    if printer_name:
                        # Convert to PDF and print
                        pdf_path = self.convert_drawing_to_pdf(drawing_path, paper_size)
                        
                        if pdf_path and os.path.exists(pdf_path):
                            success = self.print_pdf_file(pdf_path, printer_name)
                            if success:
                                printed_count += 1
                                
                                # Track size summary
                                if paper_size not in size_summary:
                                    size_summary[paper_size] = {'count': 0, 'printer': printer_name}
                                size_summary[paper_size]['count'] += 1
                                
                                print(f"Printed {drawing_name} (Size {paper_size}) to {printer_name}")
                            else:
                                failed_count += 1
                                print(f"Failed to print {drawing_name}")
                        else:
                            failed_count += 1
                            print(f"Failed to convert {drawing_name} to PDF")
                    else:
                        failed_count += 1
                        print(f"No printer configured for size {paper_size}: {drawing_name}")
                except Exception as e:
                    print(f"Failed to print {drawing_name}: {e}")
                    failed_count += 1
            else:
                print(f"File not found: {drawing_path}")
                failed_count += 1
        
        # Show summary
        summary_text = f"Package print completed!\n\n"
        summary_text += f"Successfully printed: {printed_count}\n"
        summary_text += f"Failed: {failed_count}\n\n"
        
        if size_summary:
            summary_text += "Size breakdown:\n"
            for size, info in size_summary.items():
                summary_text += f"  Size {size}: {info['count']} drawings to {info['printer']}\n"
        
        messagebox.showinfo("Package Print Complete", summary_text)
    
    def add_package_to_current_job(self, package_data):
        """Add drawings from package to current job"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first")
            return
        
        drawings = package_data.get('drawings', [])
        if not drawings:
            messagebox.showinfo("Info", "No drawings found in package")
            return
        
        try:
            cursor = self.conn.cursor()
            added_count = 0
            
            for drawing in drawings:
                drawing_name = drawing.get('name', '')
                drawing_type = drawing.get('type', '')
                drawing_path = drawing.get('path', '')
                file_extension = drawing.get('extension', '')
                
                # Check if drawing already exists in current job
                cursor.execute("""
                    SELECT COUNT(*) FROM drawings 
                    WHERE job_number = ? AND drawing_path = ?
                """, (self.current_project, drawing_path))
                
                if cursor.fetchone()[0] == 0:  # Not already in current job
                    cursor.execute("""
                        INSERT INTO drawings (job_number, drawing_path, drawing_name, drawing_type, 
                                           file_extension, added_date, added_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (self.current_project, drawing_path, drawing_name, drawing_type, 
                          file_extension, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Import"))
                    added_count += 1
            
            self.conn.commit()
            
            # Refresh the current drawings list
            self.load_current_drawings()
            
            # Refresh the project list to update drawing counts
            self.load_projects()
            
            messagebox.showinfo("Import Complete", f"Added {added_count} drawings to current job")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add package to current job: {str(e)}")
    
    def setup_printers(self):
        """Setup printer configuration for different paper sizes"""
        setup_window = tk.Toplevel(self.root)
        setup_window.title("Printer Setup - Paper Size Configuration")
        setup_window.geometry("700x600")
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # Center the window
        setup_window.update_idletasks()
        x = (setup_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (setup_window.winfo_screenheight() // 2) - (600 // 2)
        setup_window.geometry(f"700x600+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(setup_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Printer Configuration", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = ttk.Label(main_frame, 
                              text="Configure printers for different paper sizes.\n"
                                   "A & B sizes typically use one printer, C & D sizes use another.",
                              font=("Arial", 10))
        desc_label.pack(pady=(0, 20))
        
        # Get available printers
        available_printers = self.get_available_printers()
        
        # Paper size configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Paper Size Configuration", padding=15)
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Paper sizes with detailed configuration
        paper_sizes = ['A', 'B', 'C', 'D']
        size_vars = {}
        printer_vars = {}
        orientation_vars = {}
        paper_type_vars = {}
        
        for i, size in enumerate(paper_sizes):
            size_frame = ttk.Frame(config_frame)
            size_frame.pack(fill=tk.X, pady=8)
            
            # Paper size label
            size_label = ttk.Label(size_frame, text=f"Size {size}:", font=("Arial", 12, "bold"), width=8)
            size_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Printer selection
            printer_var = tk.StringVar()
            printer_vars[size] = printer_var
            
            printer_combo = ttk.Combobox(size_frame, textvariable=printer_var, 
                                       values=available_printers, state="readonly", width=30)
            printer_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # Orientation selection
            orientation_var = tk.StringVar()
            orientation_vars[size] = orientation_var
            
            orientation_combo = ttk.Combobox(size_frame, textvariable=orientation_var,
                                           values=['Portrait', 'Landscape'], state="readonly", width=12)
            orientation_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # Paper type selection
            paper_type_var = tk.StringVar()
            paper_type_vars[size] = paper_type_var
            
            paper_type_combo = ttk.Combobox(size_frame, textvariable=paper_type_var,
                                          values=['Standard', 'Bond', 'Tracing', 'Vellum', 'Transparency'], 
                                          state="readonly", width=15)
            paper_type_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            # Load existing configuration
            self.load_printer_config_detailed(size, printer_var, orientation_var, paper_type_var)
        
        # Create buttons frame at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_configuration():
            try:
                cursor = self.conn.cursor()
                saved_count = 0
                
                for size in paper_sizes:
                    printer_name = printer_vars[size].get()
                    orientation = orientation_vars[size].get()
                    paper_type = paper_type_vars[size].get()
                    
                    print(f"Saving {size}: Printer={printer_name}, Orientation={orientation}, PaperType={paper_type}")
                    
                    if printer_name and printer_name.strip():
                        # Insert or update printer configuration
                        cursor.execute('''
                            INSERT OR REPLACE INTO printer_config 
                            (paper_size, printer_name, paper_type, orientation, created_date, updated_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (size, printer_name.strip(), paper_type or 'Standard', orientation or 'Portrait', 
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        saved_count += 1
                        print(f"Saved configuration for size {size}")
                    else:
                        print(f"No printer selected for size {size}")
                
                self.conn.commit()
                
                if saved_count > 0:
                    messagebox.showinfo("Success", f"Printer configuration saved successfully!\n\nSaved {saved_count} printer configurations.")
                    setup_window.destroy()
                else:
                    messagebox.showwarning("Warning", "No printer configurations were saved.\n\nPlease select at least one printer for each paper size you want to use.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
                print(f"Save error: {e}")
        
        def test_print():
            """Test print a sample for each configured size"""
            test_results = []
            for size in paper_sizes:
                printer_name = printer_vars[size].get()
                orientation = orientation_vars[size].get()
                paper_type = paper_type_vars[size].get()
                
                if printer_name:
                    test_results.append(f"Size {size}: {printer_name} | {orientation} | {paper_type}")
                else:
                    test_results.append(f"Size {size}: Not configured")
            
            messagebox.showinfo("Current Configuration", 
                               "Current printer configuration:\n\n" + 
                               "\n".join(test_results))
        
        def test_actual_print():
            """Test print a sample drawing for each configured size"""
            print("=== TEST PRINT STARTED ===")
            test_results = []
            
            # Create test PDFs directly for each size
            for size in paper_sizes:
                printer_name = printer_vars[size].get()
                print(f"Testing size {size}: printer='{printer_name}'")
                
                if printer_name:
                    try:
                        # Create test PDF directly
                        test_pdf = f"test_{size}_size.pdf"
                        success = self.create_test_pdf(test_pdf, size, printer_name, 
                                                     orientation_vars[size].get(), 
                                                     paper_type_vars[size].get())
                        
                        if success and os.path.exists(test_pdf):
                            print(f"Test PDF created: {test_pdf}")
                            
                            # Print the PDF
                            print_success = self.print_pdf_file(test_pdf, printer_name)
                            print(f"Print command success: {print_success}")
                            
                            if print_success:
                                test_results.append(f"Size {size}: Test print sent to {printer_name}")
                            else:
                                test_results.append(f"Size {size}: Print command failed")
                        else:
                            test_results.append(f"Size {size}: Could not create test PDF")
                        
                        # Clean up test file
                        try:
                            if os.path.exists(test_pdf):
                                os.remove(test_pdf)
                                print(f"Cleaned up test file: {test_pdf}")
                        except Exception as e:
                            print(f"Could not remove test file: {e}")
                            
                    except Exception as e:
                        print(f"Exception in test print for size {size}: {e}")
                        test_results.append(f"Size {size}: Test print failed - {str(e)}")
                else:
                    print(f"Size {size}: No printer configured")
                    test_results.append(f"Size {size}: Not configured")
            
            print("=== TEST PRINT COMPLETED ===")
            print(f"Results: {test_results}")
            
            messagebox.showinfo("Test Print Results", 
                               "Test print results:\n\n" + 
                               "\n".join(test_results))
        
        def load_test_data():
            """Load test printer data for demonstration"""
            test_printers = self.get_available_printers()
            if len(test_printers) >= 2:
                # Set test data
                printer_vars['A'].set(test_printers[0] if len(test_printers) > 0 else 'Microsoft Print to PDF')
                printer_vars['B'].set(test_printers[0] if len(test_printers) > 0 else 'Microsoft Print to PDF')
                printer_vars['C'].set(test_printers[1] if len(test_printers) > 1 else test_printers[0] if len(test_printers) > 0 else 'Microsoft Print to PDF')
                printer_vars['D'].set(test_printers[1] if len(test_printers) > 1 else test_printers[0] if len(test_printers) > 0 else 'Microsoft Print to PDF')
                
                # Set all to Landscape
                for size in paper_sizes:
                    orientation_vars[size].set('Landscape')
                    paper_type_vars[size].set('Standard')
                
                messagebox.showinfo("Test Data Loaded", "Test printer configuration loaded.\n\nAll sizes set to Landscape orientation with Standard paper type.")
            else:
                messagebox.showwarning("No Printers", "No printers found. Please install at least one printer to use this feature.")
        
        # Add buttons to the frame
        load_btn = ttk.Button(button_frame, text="Load Test Data", command=load_test_data)
        load_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = ttk.Button(button_frame, text="Save Configuration", command=save_configuration)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        view_btn = ttk.Button(button_frame, text="View Configuration", command=test_print)
        view_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_btn = ttk.Button(button_frame, text="Test Print", command=test_actual_print)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=setup_window.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def create_test_pdf(self, filename, size, printer_name, orientation, paper_type):
        """Create a test PDF file for testing printer configuration"""
        print(f"Creating test PDF: {filename} for size {size}")
        try:
            from reportlab.lib.pagesizes import letter, legal, A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
            
            print("ReportLab imported successfully")
            
            # Define paper sizes (in inches, landscape orientation)
            size_dimensions = {
                'A': (11, 8.5),    # 8.5T x 11W (landscape)
                'B': (17, 11),     # 11T x 17W (landscape) 
                'C': (24, 18),     # 18T x 24W (landscape)
                'D': (36, 24)      # 24T x 36W (landscape)
            }
            
            width, height = size_dimensions.get(size, (11, 8.5))
            print(f"Paper dimensions: {width}\" x {height}\"")
            
            # Create PDF
            c = canvas.Canvas(filename, pagesize=(width * inch, height * inch))
            print(f"Canvas created for {filename}")
            
            # Add content
            c.setFont("Helvetica-Bold", 24)
            c.drawString(1 * inch, height * inch - 1.5 * inch, f"TEST PRINT - SIZE {size}")
            
            c.setFont("Helvetica", 16)
            c.drawString(1 * inch, height * inch - 2.5 * inch, f"Printer: {printer_name}")
            c.drawString(1 * inch, height * inch - 3 * inch, f"Orientation: {orientation}")
            c.drawString(1 * inch, height * inch - 3.5 * inch, f"Paper Type: {paper_type}")
            c.drawString(1 * inch, height * inch - 4 * inch, f"Dimensions: {width}\" x {height}\"")
            c.drawString(1 * inch, height * inch - 4.5 * inch, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Add border
            c.rect(0.5 * inch, 0.5 * inch, (width - 1) * inch, (height - 1) * inch)
            
            # Add corner marks
            corner_size = 0.5 * inch
            c.rect(0.5 * inch, 0.5 * inch, corner_size, corner_size)
            c.rect((width - 1) * inch, 0.5 * inch, corner_size, corner_size)
            c.rect(0.5 * inch, (height - 1) * inch, corner_size, corner_size)
            c.rect((width - 1) * inch, (height - 1) * inch, corner_size, corner_size)
            
            c.save()
            print(f"PDF saved successfully: {filename}")
            return True
            
        except ImportError as e:
            print(f"ReportLab not available: {e}")
            # Fallback if reportlab not available
            try:
                # Create a simple text file as fallback
                txt_filename = filename.replace('.pdf', '.txt')
                with open(txt_filename, 'w') as f:
                    f.write(f"TEST PRINT - SIZE {size}\n")
                    f.write(f"Printer: {printer_name}\n")
                    f.write(f"Orientation: {orientation}\n")
                    f.write(f"Paper Type: {paper_type}\n")
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                print(f"Created text file fallback: {txt_filename}")
                return True
            except Exception as e2:
                print(f"Could not create text file fallback: {e2}")
                return False
        except Exception as e:
            print(f"Error creating test PDF: {e}")
            return False
    
    def print_pdf_file(self, pdf_file, printer_name):
        """Print a PDF file to the specified printer"""
        print(f"Attempting to print {pdf_file} to {printer_name}")
        try:
            # Use Windows print command for PDF
            cmd = ['cmd', '/c', 'print', f'/d:{printer_name}', pdf_file]
            print(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            print(f"Command return code: {result.returncode}")
            print(f"Command stdout: {result.stdout}")
            print(f"Command stderr: {result.stderr}")
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error printing PDF: {e}")
            return False
    
    def get_available_printers(self):
        """Get list of available printers"""
        try:
            import win32print
            printers = []
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                printers.append(printer[2])  # printer[2] is the printer name
            return printers
        except ImportError:
            return ["Microsoft Print to PDF", "Default Printer"]
        except Exception as e:
            print(f"Error getting printers: {e}")
            return ["Microsoft Print to PDF", "Default Printer"]
    
    def load_printer_config(self, paper_size, printer_var):
        """Load existing printer configuration for a paper size"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT printer_name FROM printer_config WHERE paper_size = ?
            """, (paper_size,))
            result = cursor.fetchone()
            if result:
                printer_var.set(result[0])
        except Exception as e:
            print(f"Error loading printer config for {paper_size}: {e}")
    
    def load_printer_config_detailed(self, paper_size, printer_var, orientation_var, paper_type_var):
        """Load existing detailed printer configuration for a paper size"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT printer_name, orientation, paper_type FROM printer_config WHERE paper_size = ?
            """, (paper_size,))
            result = cursor.fetchone()
            if result:
                printer_name, orientation, paper_type = result
                print(f"Loading {paper_size}: Printer={printer_name}, Orientation={orientation}, PaperType={paper_type}")
                printer_var.set(printer_name or '')
                orientation_var.set(orientation or 'Portrait')
                paper_type_var.set(paper_type or 'Standard')
            else:
                # Set defaults
                print(f"No saved config for {paper_size}, setting defaults")
                printer_var.set('')
                orientation_var.set('Portrait')
                paper_type_var.set('Standard')
        except Exception as e:
            print(f"Error loading detailed printer config for {paper_size}: {e}")
            # Set defaults on error
            printer_var.set('')
            orientation_var.set('Portrait')
            paper_type_var.set('Standard')
    
    def get_printer_for_size(self, paper_size):
        """Get the configured printer for a specific paper size"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT printer_name FROM printer_config WHERE paper_size = ?
            """, (paper_size,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                # Fallback to default printer selection
                return self.get_printer_name()
        except Exception as e:
            print(f"Error getting printer for size {paper_size}: {e}")
            return self.get_printer_name()
    
    def detect_paper_size_from_drawing(self, drawing_path):
        """Detect paper size from drawing file"""
        drawing_name = os.path.basename(drawing_path).upper()
        
        # Look for size indicators in filename (case insensitive)
        size_patterns = {
            'A': ['A-SIZE', 'A_SIZE', '_A.', 'SIZE-A', 'SIZE_A', '8.5X11', '8.5X11', 'A4', 'LETTER'],
            'B': ['B-SIZE', 'B_SIZE', '_B.', 'SIZE-B', 'SIZE_B', '11X17', '11X17', 'B4', 'TABLOID'],
            'C': ['C-SIZE', 'C_SIZE', '_C.', 'SIZE-C', 'SIZE_C', '18X24', '18X24', 'C4', '18X24'],
            'D': ['D-SIZE', 'D_SIZE', '_D.', 'SIZE-D', 'SIZE_D', '24X36', '24X36', 'D4', '24X36']
        }
        
        for size, patterns in size_patterns.items():
            for pattern in patterns:
                if pattern in drawing_name:
                    print(f"Detected size {size} from pattern '{pattern}' in filename: {drawing_name}")
                    return size
        
        # If no pattern found, try to detect from file size or other methods
        # For now, default to A size
        print(f"No size pattern found in filename: {drawing_name}, defaulting to A")
        return 'A'
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        else:
            self.root.attributes('-fullscreen', True)
    
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        self.root.attributes('-fullscreen', False)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Print Package Management Application')
    parser.add_argument('--job', type=str, help='Job number to preload')
    args = parser.parse_args()
    
    app = PrintPackageApp(job_number=args.job)
    
    # If job number provided, show it in the interface
    if args.job:
        print(f"Print Package Management opened with job number: {args.job}")
    
    app.run()
