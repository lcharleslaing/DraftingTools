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
from datetime import datetime
import json

class PrintPackageApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Print Package Management - Drafting Tools")
        self.root.state('zoomed')  # Full screen
        self.root.minsize(1200, 800)
        # Make fullscreen the default but keep window controls
        self.root.attributes('-fullscreen', True)
        
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
        
        # Create main content area with project list and drawings
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Project list
        self.create_project_list_panel(content_frame)
        
        # Right side - Drawings management
        self.create_drawings_panel(content_frame)
        
    def create_project_list_panel(self, parent):
        """Create the project list panel on the left side"""
        # Project list frame
        project_frame = ttk.LabelFrame(parent, text="Projects", padding=10)
        project_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
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
        drawings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
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
        
        # Current drawings treeview
        current_columns = ('Drawing Name', 'Type', 'Path', 'Actions')
        self.current_drawings_tree = ttk.Treeview(current_drawings_frame, columns=current_columns, show='headings', height=8)
        
        # Configure columns
        self.current_drawings_tree.heading('Drawing Name', text='Drawing Name')
        self.current_drawings_tree.heading('Type', text='Type')
        self.current_drawings_tree.heading('Path', text='Path')
        self.current_drawings_tree.heading('Actions', text='Actions')
        
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
        
        # Bind double-click and right-click events for current drawings
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
        
        print_all_btn = ttk.Button(action_frame, text="Print All Current Job", command=self.print_all_current)
        print_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(action_frame, text="Clear Current Job", command=self.clear_current_drawings)
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        export_btn = ttk.Button(action_frame, text="Export Package", command=self.export_package)
        export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        import_btn = ttk.Button(action_frame, text="Import Package", command=self.import_package)
        import_btn.pack(side=tk.LEFT, padx=(0, 5))
        
    def init_database(self):
        """Initialize the database connection"""
        self.conn = sqlite3.connect('drafting_tools.db')
        
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
                # Get all projects with drawing counts
                cursor.execute("""
                    SELECT p.job_number, p.customer_name, 
                           COALESCE(COUNT(d.id), 0) as drawing_count
                    FROM projects p
                    LEFT JOIN drawings d ON p.job_number = d.job_number
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
                    job_number, customer_name, drawing_count = project
                    customer = customer_name or "Unknown"
                    
                    # Add to tree
                    self.project_tree.insert('', 'end', values=(
                        job_number,
                        customer,
                        drawing_count
                    ))
                else:
                    job_number, customer_name = project
                    customer = customer_name or "Unknown"
                    
                    # Add to tree with 0 drawings
                    self.project_tree.insert('', 'end', values=(
                        job_number,
                        customer,
                        0
                    ))
            
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
                           COALESCE(COUNT(d.id), 0) as drawing_count
                    FROM projects p
                    LEFT JOIN drawings d ON p.job_number = d.job_number
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
                    job_number, customer_name, drawing_count = project
                    customer = customer_name or "Unknown"
                    
                    # Filter based on search term
                    if (search_term in str(job_number).lower() or 
                        search_term in customer.lower()):
                        
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
                        
                        self.project_tree.insert('', 'end', values=(
                            job_number,
                            customer,
                            0
                        ))
            
        except Exception as e:
            print(f"Error filtering projects: {e}")
    
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
                SELECT drawing_name, drawing_type, drawing_path, file_extension
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
                drawing_name, drawing_type, drawing_path, file_extension = drawing
                display_type = drawing_type or file_extension or "Unknown"
                
                # Add to tree with action text
                item = self.current_drawings_tree.insert('', 'end', values=(
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
        """Print a drawing file"""
        try:
            if os.path.exists(drawing_path):
                # Use Windows print command
                subprocess.run(['cmd', '/c', 'print', '/d:Microsoft Print to PDF', drawing_path], 
                             check=False, capture_output=True)
            else:
                messagebox.showerror("Error", "Drawing file not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print drawing: {str(e)}")
    
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
            
            # Print each drawing
            for drawing in drawings:
                drawing_path = drawing[0]
                if os.path.exists(drawing_path):
                    subprocess.run(['cmd', '/c', 'print', '/d:Microsoft Print to PDF', drawing_path], 
                                 check=False, capture_output=True)
            
            messagebox.showinfo("Success", f"Queued {len(drawings)} drawings for printing")
            
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
            item = self.current_drawings_tree.item(selection[0])
            drawing_path = item['values'][2]  # Path is in column 2
            self.open_drawing(drawing_path)
    
    def on_current_drawing_right_click(self, event):
        """Handle right-click on current drawings"""
        selection = self.current_drawings_tree.selection()
        if selection:
            item = self.current_drawings_tree.item(selection[0])
            drawing_path = item['values'][2]  # Path is in column 2
            
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
            item = self.global_drawings_tree.item(selection[0])
            drawing_path = item['values'][3]  # Path is in column 3
            self.open_drawing(drawing_path)
    
    def on_global_drawing_right_click(self, event):
        """Handle right-click on global drawings"""
        selection = self.global_drawings_tree.selection()
        if selection:
            item = self.global_drawings_tree.item(selection[0])
            drawing_path = item['values'][3]  # Path is in column 3
            job_number = item['values'][0]  # Job number is in column 0
            
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
        
        printed_count = 0
        failed_count = 0
        
        for drawing in drawings:
            drawing_path = drawing.get('path', '')
            drawing_name = drawing.get('name', 'Unknown')
            
            if os.path.exists(drawing_path):
                try:
                    subprocess.run(['cmd', '/c', 'print', '/d:Microsoft Print to PDF', drawing_path], 
                                 check=False, capture_output=True)
                    printed_count += 1
                except Exception as e:
                    print(f"Failed to print {drawing_name}: {e}")
                    failed_count += 1
            else:
                print(f"File not found: {drawing_path}")
                failed_count += 1
        
        messagebox.showinfo("Print Complete", 
                           f"Printing completed!\n\n"
                           f"Successfully printed: {printed_count}\n"
                           f"Failed: {failed_count}")
    
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
    app = PrintPackageApp()
    app.run()
