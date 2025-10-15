import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import sys
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab
import io
import subprocess

class DraftingChecklistApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drafting Drawing Checklist - Drafting Tools")
        self.root.state('zoomed')  # Maximized window
        self.root.minsize(1200, 800)
        
        # Initialize database
        self.init_database()
        
        # Create main interface
        self.create_widgets()
        
        # Load initial data
        self.load_projects()
        
        # Initialize current project
        self.current_project = None
        
    def init_database(self):
        """Initialize the database connection and create tables"""
        self.conn = sqlite3.connect('drafting_tools.db')
        cursor = self.conn.cursor()
        
        # Create master checklist items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafting_checklist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                tag TEXT NOT NULL,
                image_path TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        ''')
        
        # Check if tag column exists, if not add it
        try:
            cursor.execute("PRAGMA table_info(drafting_checklist_items)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'tag' not in columns:
                cursor.execute("ALTER TABLE drafting_checklist_items ADD COLUMN tag TEXT DEFAULT ''")
                self.conn.commit()
        except Exception as e:
            print(f"Error adding tag column: {e}")
        
        # Create project checklist status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_checklist_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                checklist_item_id INTEGER NOT NULL,
                is_checked INTEGER DEFAULT 0,
                does_not_apply INTEGER DEFAULT 0,
                checked_date TEXT,
                FOREIGN KEY (checklist_item_id) REFERENCES drafting_checklist_items (id),
                UNIQUE(job_number, checklist_item_id)
            )
        ''')
        
        # Check if does_not_apply column exists, if not add it
        try:
            cursor.execute("PRAGMA table_info(project_checklist_status)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'does_not_apply' not in columns:
                cursor.execute("ALTER TABLE project_checklist_status ADD COLUMN does_not_apply INTEGER DEFAULT 0")
                self.conn.commit()
        except Exception as e:
            print(f"Error adding does_not_apply column: {e}")
        
        self.conn.commit()
        
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(main_frame, text="Drafting Drawing Checklist", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Create resizable paned window
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Project list and settings
        left_container = ttk.Frame(paned_window)
        right_container = ttk.Frame(paned_window)
        
        paned_window.add(left_container, weight=1)
        paned_window.add(right_container, weight=2)
        
        # Left side - Project list
        self.create_project_list_panel(left_container)
        
        # Right side - Checklist management
        self.create_checklist_panel(right_container)
        
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
        
        # Show/Hide Completed toggle
        self.show_completed = False
        self.toggle_completed_btn = ttk.Button(search_frame, text="Show Completed", command=self.toggle_completed)
        self.toggle_completed_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        # Project list treeview
        columns = ('Job Number', 'Customer', 'Items Checked')
        self.project_tree = ttk.Treeview(project_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.project_tree.heading('Job Number', text='Job Number')
        self.project_tree.heading('Customer', text='Customer')
        self.project_tree.heading('Items Checked', text='Items Checked')
        
        self.project_tree.column('Job Number', width=100)
        self.project_tree.column('Customer', width=200)
        self.project_tree.column('Items Checked', width=100)
        
        # Scrollbar for project list
        project_scrollbar = ttk.Scrollbar(project_frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=project_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        project_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.project_tree.bind('<<TreeviewSelect>>', self.on_project_select)
        
    def create_checklist_panel(self, parent):
        """Create the checklist management panel on the right side"""
        # Checklist frame
        checklist_frame = ttk.LabelFrame(parent, text="Checklist Management", padding=10)
        checklist_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current job display
        job_frame = ttk.Frame(checklist_frame)
        job_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(job_frame, text="Current Job:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        self.current_job_label = ttk.Label(job_frame, text="None Selected", font=('Arial', 12))
        self.current_job_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Tab notebook for different views
        self.notebook = ttk.Notebook(checklist_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Project checklist tab
        self.project_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.project_tab, text="Project Checklist")
        
        # Settings tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Create project checklist view
        self.create_project_checklist_view()
        
        # Create settings view
        self.create_settings_view()
        
        # Action buttons
        action_frame = ttk.Frame(checklist_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Dashboard button
        dashboard_btn = ttk.Button(action_frame, text="🏠 Dashboard", command=self.open_dashboard)
        dashboard_btn.pack(side=tk.LEFT, padx=(0, 15))
        
    def create_project_checklist_view(self):
        """Create the project-specific checklist view"""
        # Checklist items frame
        items_frame = ttk.LabelFrame(self.project_tab, text="Checklist Items", padding=5)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for checklist items
        canvas = tk.Canvas(items_frame)
        scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store reference to scrollable frame
        self.checklist_items_frame = scrollable_frame
        
    def create_settings_view(self):
        """Create the settings view for managing master checklist"""
        # Master checklist frame
        master_frame = ttk.LabelFrame(self.settings_tab, text="Master Checklist Items", padding=5)
        master_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add new item frame
        add_frame = ttk.LabelFrame(master_frame, text="Add New Item", padding=5)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        ttk.Label(add_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.new_item_title = tk.StringVar()
        title_entry = ttk.Entry(add_frame, textvariable=self.new_item_title, width=40)
        title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Tag
        ttk.Label(add_frame, text="Tag(s):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.new_item_tag = tk.StringVar()
        tag_entry = ttk.Entry(add_frame, textvariable=self.new_item_tag, width=40)
        tag_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Tag help text
        tag_help = ttk.Label(add_frame, text="(Use comma-separated for multiple tags: title block, dimensions, etc.)", 
                            font=('Arial', 8), foreground='gray')
        tag_help.grid(row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 0))
        
        # Description
        ttk.Label(add_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.new_item_description = tk.StringVar()
        desc_entry = ttk.Entry(add_frame, textvariable=self.new_item_description, width=40)
        desc_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Image handling
        image_frame = ttk.Frame(add_frame)
        image_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(image_frame, text="Image:").pack(side=tk.LEFT)
        self.image_path_var = tk.StringVar()
        image_entry = ttk.Entry(image_frame, textvariable=self.image_path_var, width=30)
        image_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        browse_btn = ttk.Button(image_frame, text="Browse", command=self.browse_image)
        browse_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        paste_btn = ttk.Button(image_frame, text="Paste Screenshot", command=self.paste_screenshot)
        paste_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add button
        add_btn = ttk.Button(image_frame, text="Add Item", command=self.add_master_item)
        add_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Master items list
        list_frame = ttk.LabelFrame(master_frame, text="Current Master Items", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create treeview for master items
        master_columns = ('ID', 'Tag', 'Title', 'Description', 'Has Image')
        self.master_tree = ttk.Treeview(list_frame, columns=master_columns, show='headings', height=10)
        
        # Configure columns
        self.master_tree.heading('ID', text='ID')
        self.master_tree.heading('Tag', text='Tag')
        self.master_tree.heading('Title', text='Title')
        self.master_tree.heading('Description', text='Description')
        self.master_tree.heading('Has Image', text='Has Image')
        
        self.master_tree.column('ID', width=50, minwidth=50)
        self.master_tree.column('Tag', width=100, minwidth=80)
        self.master_tree.column('Title', width=150, minwidth=100)
        self.master_tree.column('Description', width=250, minwidth=150)
        self.master_tree.column('Has Image', width=80, minwidth=60)
        
        # Scrollbar for master items
        master_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.master_tree.yview)
        self.master_tree.configure(yscrollcommand=master_scrollbar.set)
        
        # Pack master treeview
        self.master_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        master_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons for master items
        action_frame = ttk.Frame(list_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        
        edit_btn = ttk.Button(action_frame, text="✏️ Edit Selected", command=self.edit_master_item)
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_btn = ttk.Button(action_frame, text="🗑️ Delete Selected", command=self.delete_master_item)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = ttk.Button(action_frame, text="🔄 Refresh", command=self.load_master_items)
        refresh_btn.pack(side=tk.RIGHT)
        
        # Bind events for master items
        self.master_tree.bind('<Double-1>', self.on_master_item_double_click)
        self.master_tree.bind('<Button-3>', self.on_master_item_right_click)
        
        # Load master items
        self.load_master_items()
        
    def load_projects(self):
        """Load all projects from the projects table"""
        try:
            cursor = self.conn.cursor()
            
            # Get all projects with completion state and checklist counts
            cursor.execute("""
                SELECT p.job_number, p.customer_name, 
                       CASE 
                           WHEN (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                                OR rd.is_completed = 1
                                OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                           THEN 1 ELSE 0 END AS is_completed,
                       COALESCE(checked_count, 0) as checked_count,
                       COALESCE(total_count, 0) as total_count
                FROM projects p
                LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                LEFT JOIN (
                    SELECT job_number, 
                           SUM(CASE WHEN is_checked = 1 THEN 1 ELSE 0 END) as checked_count,
                           COUNT(*) as total_count
                    FROM project_checklist_status pcs
                    JOIN drafting_checklist_items dci ON pcs.checklist_item_id = dci.id
                    GROUP BY job_number
                ) counts ON p.job_number = counts.job_number
                ORDER BY p.job_number
            """)
            
            projects = cursor.fetchall()
            
            # Clear existing items
            for item in self.project_tree.get_children():
                self.project_tree.delete(item)
            
            # Add projects to tree
            for project in projects:
                job_number, customer_name, is_completed, checked_count, total_count = project
                customer = customer_name or "Unknown"
                
                # Hide completed projects unless toggle is on
                if self.show_completed or int(is_completed) == 0:
                    items_text = f"{checked_count}/{total_count}" if total_count > 0 else "0/0"
                    self.project_tree.insert('', 'end', values=(
                        job_number,
                        customer,
                        items_text
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
            
            cursor.execute("""
                SELECT p.job_number, p.customer_name, 
                       CASE 
                           WHEN (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                                OR rd.is_completed = 1
                                OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                           THEN 1 ELSE 0 END AS is_completed,
                       COALESCE(checked_count, 0) as checked_count,
                       COALESCE(total_count, 0) as total_count
                FROM projects p
                LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                LEFT JOIN (
                    SELECT job_number, 
                           SUM(CASE WHEN is_checked = 1 THEN 1 ELSE 0 END) as checked_count,
                           COUNT(*) as total_count
                    FROM project_checklist_status pcs
                    JOIN drafting_checklist_items dci ON pcs.checklist_item_id = dci.id
                    GROUP BY job_number
                ) counts ON p.job_number = counts.job_number
                ORDER BY p.job_number
            """)
            
            projects = cursor.fetchall()
            
            for project in projects:
                job_number, customer_name, is_completed, checked_count, total_count = project
                customer = customer_name or "Unknown"
                
                # Filter based on search term
                if (search_term in str(job_number).lower() or 
                    search_term in customer.lower()):
                    
                    # Honor completed toggle based on project completed status
                    if self.show_completed or int(is_completed) == 0:
                        items_text = f"{checked_count}/{total_count}" if total_count > 0 else "0/0"
                        self.project_tree.insert('', 'end', values=(
                            job_number,
                            customer,
                            items_text
                        ))
            
        except Exception as e:
            print(f"Error filtering projects: {e}")
    
    def toggle_completed(self):
        """Toggle showing/hiding completed projects"""
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
            
            # Switch to Project Checklist tab and load checklist
            self.notebook.select(0)  # Select first tab (Project Checklist)
            
            # Load checklist for this project
            self.load_project_checklist(job_number)
    
    def load_project_checklist(self, job_number):
        """Load checklist items for the selected project"""
        # Clear existing items
        for widget in self.checklist_items_frame.winfo_children():
            widget.destroy()
        
        try:
            cursor = self.conn.cursor()
            
            # Get all master checklist items with their status for this project, sorted by tag
            # Exclude items marked as "does not apply"
            cursor.execute("""
                SELECT dci.id, dci.title, dci.description, dci.tag, dci.image_path,
                       COALESCE(pcs.is_checked, 0) as is_checked,
                       COALESCE(pcs.does_not_apply, 0) as does_not_apply,
                       pcs.checked_date
                FROM drafting_checklist_items dci
                LEFT JOIN project_checklist_status pcs ON dci.id = pcs.checklist_item_id 
                    AND pcs.job_number = ?
                ORDER BY dci.tag, dci.id
            """, (job_number,))
            
            items = cursor.fetchall()
            
            if not items:
                ttk.Label(self.checklist_items_frame, text="No checklist items found. Add items in Settings.", 
                         font=('Arial', 12), foreground='gray').pack(pady=20)
                return
            
            # Create checklist items
            for i, (item_id, title, description, tag, image_path, is_checked, does_not_apply, checked_date) in enumerate(items):
                self.create_checklist_item_widget(item_id, title, description, tag, image_path, 
                                                bool(is_checked), bool(does_not_apply), checked_date, job_number)
                
        except Exception as e:
            print(f"Error loading project checklist: {e}")
            ttk.Label(self.checklist_items_frame, text=f"Error loading checklist: {str(e)}", 
                     font=('Arial', 12), foreground='red').pack(pady=20)
    
    def create_checklist_item_widget(self, item_id, title, description, tag, image_path, is_checked, does_not_apply, checked_date, job_number):
        """Create a widget for a single checklist item"""
        # Format tags for display (support comma-separated)
        if tag and ',' in tag:
            # Multiple tags - format as [tag1, tag2, tag3]
            tags_display = f"[{tag}]"
        else:
            # Single tag
            tags_display = f"[{tag}]" if tag else "[General]"
        
        # Add visual indicator for "Does Not Apply" items
        title_display = f"{tags_display} {title}"
        if does_not_apply:
            title_display += " (DOES NOT APPLY)"
        
        # Main item frame - make it much wider
        item_frame = ttk.LabelFrame(self.checklist_items_frame, text=title_display, padding=10)
        item_frame.pack(fill=tk.X, pady=5)
        
        # Style the frame differently if "Does Not Apply" is checked
        if does_not_apply:
            item_frame.configure(relief="sunken")  # Make it look different
        
        # Single row with all elements
        main_row = ttk.Frame(item_frame)
        main_row.pack(fill=tk.X)
        
        # Left side with verified checkbox
        verified_var = tk.BooleanVar(value=is_checked)
        verified_text = f"Verified - {title}: {description}"
        if len(verified_text) > 100:
            verified_text = f"Verified - {title}: {description[:97]}..."
        
        verified_checkbox = ttk.Checkbutton(main_row, text=verified_text, variable=verified_var,
                                          command=lambda: self.toggle_checklist_item(item_id, job_number, verified_var.get(), 'verified'))
        verified_checkbox.pack(side=tk.LEFT, padx=(0, 20))
        
        # Style the verified checkbox differently if "Does Not Apply" is checked
        if does_not_apply:
            verified_checkbox.configure(state='disabled')  # Gray out the verified checkbox
        
        # Spacer to push right elements to the far right
        spacer = ttk.Frame(main_row)
        spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Right side with Does Not Apply checkbox and View button
        right_frame = ttk.Frame(main_row)
        right_frame.pack(side=tk.RIGHT)
        
        # Does Not Apply checkbox
        not_apply_var = tk.BooleanVar(value=does_not_apply)
        not_apply_checkbox = ttk.Checkbutton(right_frame, text="Does Not Apply", variable=not_apply_var,
                                           command=lambda: self.toggle_checklist_item(item_id, job_number, not_apply_var.get(), 'not_apply'))
        not_apply_checkbox.pack(side=tk.LEFT, padx=(0, 15))
        
        # Style the "Does Not Apply" checkbox to make it more prominent
        if does_not_apply:
            not_apply_checkbox.configure(style='Accent.TCheckbutton')  # Make it stand out
        
        # View image button (if image exists)
        if image_path and os.path.exists(image_path):
            view_btn = ttk.Button(right_frame, text="View Image", 
                                command=lambda: self.view_image(image_path))
            view_btn.pack(side=tk.LEFT)
        
        # Checked date (if checked) - on a separate line below
        if is_checked and checked_date:
            date_label = ttk.Label(item_frame, text=f"Checked on: {checked_date}", 
                                font=('Arial', 9), foreground='green')
            date_label.pack(anchor=tk.W, pady=(5, 0))
    
    def toggle_checklist_item(self, item_id, job_number, is_checked, checkbox_type):
        """Toggle the checked status of a checklist item for a project"""
        try:
            cursor = self.conn.cursor()
            
            if checkbox_type == 'verified':
                if is_checked:
                    # Insert or update to checked, clear does_not_apply
                    cursor.execute("""
                        INSERT OR REPLACE INTO project_checklist_status 
                        (job_number, checklist_item_id, is_checked, does_not_apply, checked_date)
                        VALUES (?, ?, 1, 0, ?)
                    """, (job_number, item_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                else:
                    # Update to unchecked
                    cursor.execute("""
                        UPDATE project_checklist_status 
                        SET is_checked = 0, checked_date = NULL
                        WHERE job_number = ? AND checklist_item_id = ?
                    """, (job_number, item_id))
            
            elif checkbox_type == 'not_apply':
                if is_checked:
                    # Insert or update to does not apply, clear verified
                    cursor.execute("""
                        INSERT OR REPLACE INTO project_checklist_status 
                        (job_number, checklist_item_id, is_checked, does_not_apply, checked_date)
                        VALUES (?, ?, 0, 1, ?)
                    """, (job_number, item_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                else:
                    # Update to not does not apply
                    cursor.execute("""
                        UPDATE project_checklist_status 
                        SET does_not_apply = 0
                        WHERE job_number = ? AND checklist_item_id = ?
                    """, (job_number, item_id))
            
            self.conn.commit()
            
            # Refresh project list to update counts
            self.load_projects()
            
            # If "Does Not Apply" was checked, refresh the checklist to hide the item
            if checkbox_type == 'not_apply' and is_checked:
                self.load_project_checklist(job_number)
            # If "Does Not Apply" was unchecked, refresh the checklist to show the item again
            elif checkbox_type == 'not_apply' and not is_checked:
                self.load_project_checklist(job_number)
            
        except Exception as e:
            print(f"Error toggling checklist item: {e}")
            messagebox.showerror("Error", f"Failed to update checklist item: {str(e)}")
    
    def view_image(self, image_path):
        """View an image in a new window"""
        try:
            # Create image viewer window
            viewer = tk.Toplevel(self.root)
            viewer.title("Checklist Item Image")
            viewer.geometry("800x600")
            
            # Center the window
            viewer.update_idletasks()
            x = (viewer.winfo_screenwidth() // 2) - (800 // 2)
            y = (viewer.winfo_screenheight() // 2) - (600 // 2)
            viewer.geometry(f"800x600+{x}+{y}")
            
            # Load and display image
            image = Image.open(image_path)
            # Resize if too large
            if image.width > 800 or image.height > 600:
                image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            
            # Create canvas for scrolling
            canvas = tk.Canvas(viewer, width=800, height=600)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # Center the image in the canvas
            canvas_width = 800
            canvas_height = 600
            img_width = photo.width()
            img_height = photo.height()
            
            x = (canvas_width - img_width) // 2
            y = (canvas_height - img_height) // 2
            
            canvas.create_image(x, y, anchor=tk.NW, image=photo)
            
            # Keep reference to prevent garbage collection
            viewer.image = photo
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {str(e)}")
    
    def load_master_items(self):
        """Load master checklist items"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT id, title, description, tag, image_path, created_date
                FROM drafting_checklist_items
                ORDER BY tag, id
            """)
            
            items = cursor.fetchall()
            
            # Clear existing items
            for item in self.master_tree.get_children():
                self.master_tree.delete(item)
            
            # Add items to tree
            for item in items:
                item_id, title, description, tag, image_path, created_date = item
                has_image = "Yes" if image_path and os.path.exists(image_path) else "No"
                
                self.master_tree.insert('', 'end', values=(
                    item_id,
                    tag,
                    title,
                    description[:50] + "..." if len(description) > 50 else description,
                    has_image
                ))
                
        except Exception as e:
            print(f"Error loading master items: {e}")
    
    def browse_image(self):
        """Browse for an image file"""
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filename:
            self.image_path_var.set(filename)
    
    def paste_screenshot(self):
        """Paste screenshot from clipboard"""
        try:
            # Try to get image from clipboard
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            
            # Get clipboard data
            try:
                # Try PIL first
                from PIL import ImageGrab
                image = ImageGrab.grabclipboard()
                if image:
                    # Save to temp file
                    temp_path = f"temp_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    image.save(temp_path)
                    self.image_path_var.set(temp_path)
                    root.destroy()
                    return
            except ImportError:
                pass
            
            # Fallback: try tkinter clipboard
            try:
                clipboard_data = root.clipboard_get()
                # This won't work for images, but we'll try
                root.destroy()
                messagebox.showinfo("Info", "Image paste not supported. Please use Browse to select an image file.")
            except:
                root.destroy()
                messagebox.showinfo("Info", "No image found in clipboard. Please use Browse to select an image file.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste screenshot: {str(e)}")
    
    def add_master_item(self):
        """Add a new item to the master checklist"""
        title = self.new_item_title.get().strip()
        tag = self.new_item_tag.get().strip()
        description = self.new_item_description.get().strip()
        image_path = self.image_path_var.get().strip()
        
        if not title or not tag or not description:
            messagebox.showwarning("Warning", "Please enter title, tag, and description")
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Save image if provided
            final_image_path = None
            if image_path and os.path.exists(image_path):
                # Create images directory if it doesn't exist
                images_dir = "checklist_images"
                os.makedirs(images_dir, exist_ok=True)
                
                # Copy image to images directory
                filename = f"item_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(image_path)}"
                final_image_path = os.path.join(images_dir, filename)
                
                # Copy file
                import shutil
                shutil.copy2(image_path, final_image_path)
            
            # Insert new item
            cursor.execute("""
                INSERT INTO drafting_checklist_items (title, description, tag, image_path, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, description, tag, final_image_path, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            self.conn.commit()
            
            # Clear form
            self.new_item_title.set("")
            self.new_item_tag.set("")
            self.new_item_description.set("")
            self.image_path_var.set("")
            
            # Refresh master items list
            self.load_master_items()
            
            # Update all active projects with new item
            self.update_all_projects_with_new_item(cursor.lastrowid)
            
            messagebox.showinfo("Success", "Checklist item added successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add checklist item: {str(e)}")
    
    def update_all_projects_with_new_item(self, new_item_id):
        """Add new checklist item to all active projects"""
        try:
            cursor = self.conn.cursor()
            
            # Get all active projects (not completed)
            cursor.execute("""
                SELECT p.job_number
                FROM projects p
                LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                WHERE NOT (
                    (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                    OR rd.is_completed = 1
                    OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                )
            """)
            
            active_projects = cursor.fetchall()
            print(f"DEBUG: Found {len(active_projects)} active projects")
            print(f"DEBUG: Adding new item {new_item_id} to projects: {[p[0] for p in active_projects]}")
            
            # Add new item to all active projects (unchecked by default)
            added_count = 0
            for (job_number,) in active_projects:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO project_checklist_status 
                        (job_number, checklist_item_id, is_checked, does_not_apply, checked_date)
                        VALUES (?, ?, 0, 0, NULL)
                    """, (job_number, new_item_id))
                    if cursor.rowcount > 0:
                        added_count += 1
                        print(f"DEBUG: Added item {new_item_id} to project {job_number}")
                except Exception as e:
                    print(f"DEBUG: Error adding item {new_item_id} to project {job_number}: {e}")
            
            self.conn.commit()
            print(f"DEBUG: Successfully added item to {added_count} projects")
            
        except Exception as e:
            print(f"Error updating projects with new item: {e}")
    
    def on_master_item_double_click(self, event):
        """Handle double-click on master item"""
        selection = self.master_tree.selection()
        if selection:
            item = self.master_tree.item(selection[0])
            # Get item ID from the first column
            item_id = item['values'][0]
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT image_path FROM drafting_checklist_items WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                if result and result[0] and os.path.exists(result[0]):
                    self.view_image(result[0])
            except Exception as e:
                print(f"Error viewing master item: {e}")
    
    def on_master_item_right_click(self, event):
        """Handle right-click on master item"""
        selection = self.master_tree.selection()
        if selection:
            item = self.master_tree.item(selection[0])
            item_id = item['values'][0]
            title = item['values'][2]  # Title is now in column 2
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="View Image", command=lambda: self.view_master_item_image_by_id(item_id))
            context_menu.add_command(label="Edit", command=self.edit_master_item)
            context_menu.add_separator()
            context_menu.add_command(label="Delete", command=self.delete_master_item)
            
            # Show context menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
    
    def view_master_item_image(self, title):
        """View image for a master item"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT image_path FROM drafting_checklist_items WHERE title = ?", (title,))
            result = cursor.fetchone()
            if result and result[0] and os.path.exists(result[0]):
                self.view_image(result[0])
            else:
                messagebox.showinfo("Info", "No image available for this item")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view image: {str(e)}")
    
    def view_master_item_image_by_id(self, item_id):
        """View image for a master item by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT image_path FROM drafting_checklist_items WHERE id = ?", (item_id,))
            result = cursor.fetchone()
            if result and result[0] and os.path.exists(result[0]):
                self.view_image(result[0])
            else:
                messagebox.showinfo("Info", "No image available for this item")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to view image: {str(e)}")
    
    def edit_master_item(self):
        """Edit the selected master item"""
        selection = self.master_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit")
            return
        
        item = self.master_tree.item(selection[0])
        item_id = item['values'][0]
        
        # Get current item data
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT title, description, tag, image_path 
                FROM drafting_checklist_items 
                WHERE id = ?
            """, (item_id,))
            result = cursor.fetchone()
            
            if not result:
                messagebox.showerror("Error", "Item not found")
                return
            
            title, description, tag, image_path = result
            
            # Create edit dialog
            self.edit_dialog = tk.Toplevel(self.root)
            self.edit_dialog.title("Edit Master Item")
            self.edit_dialog.geometry("500x400")
            self.edit_dialog.transient(self.root)
            self.edit_dialog.grab_set()
            
            # Center the dialog
            self.edit_dialog.update_idletasks()
            x = (self.edit_dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (self.edit_dialog.winfo_screenheight() // 2) - (400 // 2)
            self.edit_dialog.geometry(f"500x400+{x}+{y}")
            
            # Create form
            form_frame = ttk.Frame(self.edit_dialog, padding=20)
            form_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            ttk.Label(form_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.edit_title_var = tk.StringVar(value=title)
            title_entry = ttk.Entry(form_frame, textvariable=self.edit_title_var, width=50)
            title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            
            # Tag
            ttk.Label(form_frame, text="Tag(s):").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.edit_tag_var = tk.StringVar(value=tag)
            tag_entry = ttk.Entry(form_frame, textvariable=self.edit_tag_var, width=50)
            tag_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            
            # Description
            ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=5)
            self.edit_desc_var = tk.StringVar(value=description)
            desc_entry = ttk.Entry(form_frame, textvariable=self.edit_desc_var, width=50)
            desc_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            
            # Image
            ttk.Label(form_frame, text="Image Path:").grid(row=3, column=0, sticky=tk.W, pady=5)
            image_frame = ttk.Frame(form_frame)
            image_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            
            self.edit_image_var = tk.StringVar(value=image_path or "")
            image_entry = ttk.Entry(image_frame, textvariable=self.edit_image_var, width=40)
            image_entry.pack(side=tk.LEFT)
            
            browse_btn = ttk.Button(image_frame, text="Browse", command=self.browse_edit_image)
            browse_btn.pack(side=tk.LEFT, padx=(5, 0))
            
            paste_btn = ttk.Button(image_frame, text="Paste Screenshot", command=self.paste_edit_screenshot)
            paste_btn.pack(side=tk.LEFT, padx=(5, 0))
            
            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.grid(row=4, column=0, columnspan=2, pady=20)
            
            save_btn = ttk.Button(button_frame, text="Save Changes", command=lambda: self.save_edit_item(item_id))
            save_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.edit_dialog.destroy)
            cancel_btn.pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load item for editing: {str(e)}")
    
    def browse_edit_image(self):
        """Browse for image file in edit dialog"""
        filename = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        )
        if filename:
            self.edit_image_var.set(filename)
    
    def paste_edit_screenshot(self):
        """Paste screenshot in edit dialog"""
        try:
            # Get image from clipboard
            image = ImageGrab.grabclipboard()
            if image:
                # Save to temp file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = f"temp_screenshot_{timestamp}.png"
                image.save(temp_path)
                self.edit_image_var.set(temp_path)
                messagebox.showinfo("Success", "Screenshot pasted successfully!")
            else:
                messagebox.showwarning("Warning", "No image found in clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste screenshot: {str(e)}")
    
    def save_edit_item(self, item_id):
        """Save edited master item"""
        try:
            title = self.edit_title_var.get().strip()
            tag = self.edit_tag_var.get().strip()
            description = self.edit_desc_var.get().strip()
            image_path = self.edit_image_var.get().strip()
            
            if not title or not description:
                messagebox.showwarning("Warning", "Title and Description are required")
                return
            
            cursor = self.conn.cursor()
            
            # Update the item
            cursor.execute("""
                UPDATE drafting_checklist_items 
                SET title = ?, description = ?, tag = ?, image_path = ?, updated_date = ?
                WHERE id = ?
            """, (title, description, tag, image_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item_id))
            
            self.conn.commit()
            
            # Close dialog
            self.edit_dialog.destroy()
            
            # Refresh lists
            self.load_master_items()
            if self.current_project:
                self.load_project_checklist(self.current_project)
            
            messagebox.showinfo("Success", "Item updated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update item: {str(e)}")
    
    def delete_master_item(self):
        """Delete the selected master item"""
        selection = self.master_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        item = self.master_tree.item(selection[0])
        item_id = item['values'][0]
        title = item['values'][2]  # Title is now in column 2
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}'?\n\nThis will remove it from all projects."):
            try:
                cursor = self.conn.cursor()
                
                # Get image path before deleting
                cursor.execute("SELECT image_path FROM drafting_checklist_items WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                image_path = result[0] if result else None
                
                # Delete from project checklist status first (foreign key constraint)
                cursor.execute("DELETE FROM project_checklist_status WHERE checklist_item_id = ?", (item_id,))
                
                # Delete the master item
                cursor.execute("DELETE FROM drafting_checklist_items WHERE id = ?", (item_id,))
                
                # Delete image file if it exists
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except:
                        pass  # Ignore file deletion errors
                
                self.conn.commit()
                
                # Refresh lists
                self.load_master_items()
                if self.current_project:
                    self.load_project_checklist(self.current_project)
                self.load_projects()
                
                messagebox.showinfo("Success", "Item deleted successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item: {str(e)}")
    
    def open_dashboard(self):
        """Open the dashboard application"""
        try:
            if os.path.exists('dashboard.py'):
                subprocess.Popen([sys.executable, 'dashboard.py'])
            else:
                messagebox.showerror("Error", "dashboard.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Dashboard:\n{str(e)}")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = DraftingChecklistApp()
    app.run()
