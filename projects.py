import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import os
import subprocess
import sys
import shutil
from database_setup import DatabaseManager
from date_picker import DateEntry
from directory_picker import DirectoryPicker, FilePicker

class CollapsibleFrame(ttk.Frame):
    """A collapsible frame widget"""
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header frame with toggle button
        self.header = ttk.Frame(self, relief='raised', style='CollapsibleHeader.TFrame')
        self.header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 2))
        self.header.columnconfigure(1, weight=1)
        
        # Toggle button (arrow)
        self.toggle_var = tk.StringVar(value="▼")
        self.toggle_btn = ttk.Button(self.header, textvariable=self.toggle_var, 
                                     width=3, command=self.toggle)
        self.toggle_btn.grid(row=0, column=0, padx=(5, 5))
        
        # Title label
        self.title_label = ttk.Label(self.header, text=text, 
                                     font=('Arial', 11, 'bold'))
        self.title_label.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Content frame
        self.content = ttk.Frame(self, padding="10")
        self.content.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content.columnconfigure(0, weight=1)
        
        self.collapsed = False
    
    def toggle(self):
        """Toggle the collapsed state"""
        if self.collapsed:
            self.content.grid()
            self.toggle_var.set("▼")
            self.collapsed = False
        else:
            self.content.grid_remove()
            self.toggle_var.set("▶")
            self.collapsed = True

class ProjectsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Management - Drafting Tools")
        
        # Maximize window (not fullscreen, keeps controls)
        self.root.state('zoomed')  # Windows maximized
        
        # Set minimum size
        self.root.minsize(1200, 800)
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Initialize current project tracking
        self.current_project = None
        
        # Configure root grid weights for full expansion
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=0)  # Title row (fixed)
        root.rowconfigure(1, weight=100)  # Main content (expands)
        root.rowconfigure(2, weight=0)  # Separator (fixed)
        root.rowconfigure(3, weight=0)  # Footer (fixed)
        
        self.create_widgets()
        self.load_projects()

        # Ensure table to track file timestamps per project
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS file_timestamps (
                    job_number TEXT NOT NULL,
                    path TEXT NOT NULL,
                    last_mtime REAL NOT NULL,
                    acknowledged INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY(job_number, path)
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception:
            pass
        
        # Add keyboard shortcuts for fullscreen toggle
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen() if self.root.attributes('-fullscreen') else None)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    
    def create_widgets(self):
        """Create all GUI widgets with proper layout"""
        # Initialize redline update BooleanVars FIRST
        for cycle in range(1, 5):
            setattr(self, f"redline_update_{cycle}_var", tk.BooleanVar())
        
        # Row 0: Title
        title_label = ttk.Label(self.root, text="Project Management - Complete Workflow", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 10), padx=20, sticky=(tk.W, tk.E))
        
        # Row 1: Main content area (expands to fill space)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(0, 10))
        
        # Container frames for each section
        self.project_list_container = ttk.Frame(main_paned)
        self.project_details_container = ttk.Frame(main_paned)
        self.workflow_container = ttk.Frame(main_paned)
        self.quick_access_container = ttk.Frame(main_paned)
        
        # Add containers to paned window - they will expand vertically
        main_paned.add(self.project_list_container, weight=1)
        main_paned.add(self.project_details_container, weight=1)
        main_paned.add(self.workflow_container, weight=1)
        main_paned.add(self.quick_access_container, weight=1)
        
        # Create panels inside containers
        self.create_project_list_panel()
        self.create_project_details_panel()
        self.create_workflow_panel()
        self.create_quick_access_panel()
        
        # Row 2: Fixed footer with action buttons
        self.create_action_buttons()
        
        # Load dropdown data after all widgets are created
        self.load_dropdown_data()
    
    def create_project_list_panel(self):
        """Create the project list panel"""
        list_frame = ttk.LabelFrame(self.project_list_container, text="Projects", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        
        # Search and sort frame - combined for compact layout
        search_sort_frame = ttk.Frame(list_frame)
        search_sort_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        search_sort_frame.columnconfigure(1, weight=1)
        
        # Search row
        ttk.Label(search_sort_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_sort_frame, textvariable=self.search_var, width=25)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 0))
        self.search_var.trace('w', self.filter_projects)
        
        # Sort buttons row - directly under search (toggle functionality)
        self.job_sort_ascending = True  # Track sort direction for job numbers
        self.customer_sort_ascending = True  # Track sort direction for customers
        self.due_date_sort_ascending = True  # Track sort direction for due dates
        
        sort_btn_frame = ttk.Frame(search_sort_frame)
        sort_btn_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(3, 0))
        
        self.sort_job_btn = ttk.Button(sort_btn_frame, text="Job # ↑", command=self.sort_by_job_number, width=10)
        self.sort_job_btn.grid(row=0, column=0, padx=(0, 3), sticky=tk.W)
        
        self.sort_customer_btn = ttk.Button(sort_btn_frame, text="Customer ↑", command=self.sort_by_customer, width=12)
        self.sort_customer_btn.grid(row=0, column=1, padx=(0, 3), sticky=tk.W)
        
        self.sort_due_date_btn = ttk.Button(sort_btn_frame, text="Due Date ↑", command=self.sort_by_due_date, width=12)
        self.sort_due_date_btn.grid(row=0, column=2, padx=(0, 0), sticky=tk.W)
        
        # Treeview for projects - show due date, days until due, and status
        columns = ('Job Number', 'Customer', 'Due Date', 'Due in', 'Status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=18)
        
        # Configure tags for row highlighting
        self.tree.tag_configure('selected', background='#E8F0FE', font=('Arial', 9, 'bold'))
        
        # Set column widths
        self.tree.heading('Job Number', text='Job Number')
        self.tree.column('Job Number', width=80, minwidth=80)
        
        self.tree.heading('Customer', text='Customer')
        self.tree.column('Customer', width=150, minwidth=100)
        
        self.tree.heading('Due Date', text='Due Date')
        self.tree.column('Due Date', width=100, minwidth=80)
        
        self.tree.heading('Due in', text='Due in (Days)')
        self.tree.column('Due in', width=100, minwidth=80)
        
        self.tree.heading('Status', text='Status')
        self.tree.column('Status', width=100, minwidth=80)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_project_select)
    
    def create_project_details_panel(self):
        """Create the project details panel"""
        details_frame = ttk.LabelFrame(self.project_details_container, text="Project Details", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        details_frame.columnconfigure(1, weight=1)
        
        # Job Number
        ttk.Label(details_frame, text="Job Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.job_number_var = tk.StringVar()
        self.job_number_entry = ttk.Entry(details_frame, textvariable=self.job_number_var, width=25)
        self.job_number_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Job Directory
        ttk.Label(details_frame, text="Job Directory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.job_directory_picker = DirectoryPicker(details_frame, width=25)
        self.job_directory_picker.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Customer Name
        ttk.Label(details_frame, text="Customer Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.customer_name_var = tk.StringVar()
        self.customer_name_entry = ttk.Entry(details_frame, textvariable=self.customer_name_var, width=50)
        self.customer_name_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Customer Name Path (moved below)
        self.customer_name_picker = DirectoryPicker(details_frame, width=50)
        self.customer_name_picker.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Customer Location
        ttk.Label(details_frame, text="Customer Location:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.customer_location_var = tk.StringVar()
        self.customer_location_entry = ttk.Entry(details_frame, textvariable=self.customer_location_var, width=50)
        self.customer_location_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Customer Location Path (moved below)
        self.customer_location_picker = DirectoryPicker(details_frame, width=50)
        self.customer_location_picker.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Assigned To
        ttk.Label(details_frame, text="Assigned to:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.assigned_to_var = tk.StringVar()
        self.assigned_to_combo = ttk.Combobox(details_frame, textvariable=self.assigned_to_var, 
                                            state="readonly", width=22)
        self.assigned_to_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Project Engineer
        ttk.Label(details_frame, text="Project Engineer:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.project_engineer_var = tk.StringVar()
        self.project_engineer_combo = ttk.Combobox(details_frame, textvariable=self.project_engineer_var, 
                                                 state="readonly", width=22)
        self.project_engineer_combo.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Assignment Date
        ttk.Label(details_frame, text="Assignment Date:").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.assignment_date_entry = DateEntry(details_frame, width=25)
        self.assignment_date_entry.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Due Date
        ttk.Label(details_frame, text="Due Date:").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.due_date_entry = DateEntry(details_frame, width=25)
        self.due_date_entry.grid(row=9, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Start Date
        ttk.Label(details_frame, text="Start Date:").grid(row=10, column=0, sticky=tk.W, pady=2)
        self.start_date_entry = DateEntry(details_frame, width=25)
        self.start_date_entry.grid(row=10, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Completion Date
        ttk.Label(details_frame, text="Completion Date:").grid(row=11, column=0, sticky=tk.W, pady=2)
        self.completion_date_entry = DateEntry(details_frame, width=25)
        self.completion_date_entry.grid(row=11, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Total Duration
        ttk.Label(details_frame, text="Total Project Duration:").grid(row=12, column=0, sticky=tk.W, pady=2)
        self.duration_var = tk.StringVar()
        self.duration_label = ttk.Label(details_frame, textvariable=self.duration_var, 
                                       foreground="blue", font=('Arial', 10, 'bold'))
        self.duration_label.grid(row=12, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Released to Dee
        ttk.Label(details_frame, text="Released to Dee:").grid(row=13, column=0, sticky=tk.W, pady=2)
        self.released_to_dee_entry = DateEntry(details_frame, width=25)
        self.released_to_dee_entry.grid(row=13, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Bind events
        self.start_date_entry.var.trace('w', self.calculate_duration)
        self.completion_date_entry.var.trace('w', self.calculate_duration)
        self.assignment_date_entry.var.trace('w', self.set_start_date)
        
        # Auto-save on any field change
        self.job_number_var.trace('w', self.auto_save)
        self.customer_name_var.trace('w', self.auto_save)
        self.customer_location_var.trace('w', self.auto_save)
        self.assigned_to_var.trace('w', self.auto_save)
        self.project_engineer_var.trace('w', self.auto_save)
        self.start_date_entry.var.trace('w', self.auto_save)
        self.completion_date_entry.var.trace('w', self.auto_save)
        self.due_date_entry.var.trace('w', self.auto_save)
        self.released_to_dee_entry.var.trace('w', self.auto_save)
        
        # Auto-save for directory pickers
        self.job_directory_picker.var.trace('w', self.auto_extract_and_save)
        self.customer_name_picker.var.trace('w', self.auto_save)
        self.customer_location_picker.var.trace('w', self.auto_save)
        
        # Add specifications section below project details
        self.create_specifications_section(details_frame)
    
    def create_specifications_section(self, parent_frame):
        """Create the specifications section below project details"""
        # Add separator
        separator = ttk.Separator(parent_frame, orient='horizontal')
        separator.grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))
        
        # Configure parent frame columns to use full width
        parent_frame.columnconfigure(0, weight=3)  # Buttons take 3/4 of space
        parent_frame.columnconfigure(1, weight=1)  # Inputs take 1/4 of space
        
        # Specifications label
        specs_label = ttk.Label(parent_frame, text="Specifications", font=('Arial', 12, 'bold'))
        specs_label.grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=(5, 10))
        
        # Initialize specifications buttons list and input fields
        self.spec_buttons = []
        self.spec_input_fields = {}
        
        # Create specifications content
        self.update_specifications(parent_frame)
    
    def update_specifications(self, parent_frame=None):
        """Update the specifications panel based on available files"""
        if parent_frame is None:
            return
            
        # Clear existing buttons and input fields
        for button in self.spec_buttons:
            button.destroy()
        self.spec_buttons.clear()
        
        for field in self.spec_input_fields.values():
            field.destroy()
        self.spec_input_fields.clear()
        
        # Check if we have a job directory
        if not hasattr(self, 'job_directory_picker') or not self.job_directory_picker.get():
            no_data_label = ttk.Label(parent_frame, 
                                    text="No project selected", 
                                    foreground="gray", justify="center")
            no_data_label.grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20)
            self.spec_buttons.append(no_data_label)
            return
        
        # Look for Heater Design file in Quick Access
        heater_design_file = None
        if hasattr(self, 'engineering_general_docs') and self.engineering_general_docs:
            for file_path in self.engineering_general_docs:
                filename = os.path.basename(file_path).upper()
                # Check if filename contains "HEATER DESIGN" OR if file has a "Heater Design" sheet inside
                if "HEATER DESIGN" in filename or self.has_heater_design_sheet(file_path):
                    heater_design_file = file_path
                    print(f"Found Heater Design file: {filename}")
                    break
        
        # Can Size specification
        can_size_value = "No Heater Design"
        can_size_button_state = "disabled"
        button_color = "#FFB6C1"  # Light pink for no file
        button_text_color = "black"
        
        if heater_design_file and os.path.exists(heater_design_file):
            try:
                # Read Excel file to get Can Size from "Heater Design" sheet
                can_size_value = self.read_excel_can_size(heater_design_file)
                if can_size_value:
                    can_size_button_state = "normal"
                    button_color = "#90EE90"  # Light green for file with value
                    button_text_color = "black"
                else:
                    button_color = "#FFB6C1"  # Light pink for file but no value
                    button_text_color = "black"
            except Exception as e:
                print(f"Error reading Heater Design file: {e}")
                can_size_value = "Error reading file"
                button_color = "#FFB6C1"  # Light pink for error
                button_text_color = "black"
        
        # Add Heater Specs group (now includes Can Size at the top)
        self.create_heater_specs_group(parent_frame, heater_design_file, 
                                       can_size_value, can_size_button_state, 
                                       button_color, button_text_color)
    
    def create_heater_specs_group(self, parent_frame, heater_design_file, 
                                  can_size_value=None, can_size_button_state="disabled",
                                  can_color="#FFB6C1", can_text_color="black"):
        """Create the Heater Specs group with dimension buttons"""
        # Heater Specs label
        heater_specs_label = ttk.Label(parent_frame, text="Heater Specs", font=('Arial', 11, 'bold'), foreground="darkblue")
        heater_specs_label.grid(row=17, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        self.spec_buttons.append(heater_specs_label)
        
        # Can Size button at top of Heater Specs
        if can_size_value is not None:
            can_size_btn = tk.Button(parent_frame, 
                                    text=f"Can Size: {can_size_value}",
                                    state=can_size_button_state,
                                    command=lambda: self.open_heater_design_file(heater_design_file) if heater_design_file else None,
                                    width=60, height=1,
                                    font=('Arial', 9),
                                    relief='raised', bd=1, 
                                    cursor='hand2' if can_size_button_state == "normal" else 'arrow',
                                    bg=can_color, fg=can_text_color,
                                    activebackground=can_color, activeforeground=can_text_color)
            can_size_btn.grid(row=18, column=0, sticky=(tk.W, tk.E), pady=1, padx=(0, 10))
            self.spec_buttons.append(can_size_btn)
        
        # Define the heater dimension specifications
        heater_specs = [
            ("Heater Diameter", "H13"),
            ("Heater Height", "B31"),
            ("Can Height", "C33"),
            ("Packing Rings Bottom", "D41"),
            ("Packing Rings Height", "D31"),
            ("Packing Rings to Spray Nozzle", "D25"),
            ("Stack Diameter", "H14")
        ]
        
        # Add Spray Nozzle Size and Length from Engineering Design file
        spray_nozzle_size = self.get_spray_nozzle_size_from_engineering_design()
        spray_nozzle_length = self.get_spray_nozzle_length_from_engineering_design()
        
        # Check for manual specs first, then use found values
        manual_size = self.get_saved_manual_spec("Spray Nozzle Size")
        if spray_nozzle_size:
            heater_specs.append(("Spray Nozzle Size", spray_nozzle_size))
        elif manual_size:
            heater_specs.append(("Spray Nozzle Size", f"Manual: {manual_size}"))
        else:
            heater_specs.append(("Spray Nozzle Size", "No Size Found"))
            
        manual_length = self.get_saved_manual_spec("Spray Nozzle Length")
        if spray_nozzle_length:
            heater_specs.append(("Spray Nozzle Length", spray_nozzle_length))
        elif manual_length:
            heater_specs.append(("Spray Nozzle Length", f"Manual: {manual_length}"))
        else:
            heater_specs.append(("Spray Nozzle Length", "No Length Found"))
        
        # Add Spray Nozzle P/N from Spray Nozzles file
        spray_nozzle_pn = self.read_spray_nozzle_pn_from_files()
        manual_pn = self.get_saved_manual_spec("Spray Nozzle P/N")
        if spray_nozzle_pn:
            heater_specs.append(("Spray Nozzle P/N", spray_nozzle_pn))
        elif manual_pn:
            heater_specs.append(("Spray Nozzle P/N", f"Manual: {manual_pn}"))
        else:
            # Add "No Spray Nozzle Found" if no match found
            heater_specs.append(("Spray Nozzle P/N", "No Spray Nozzle Found"))
        
        # Create buttons for each spec
        for i, (spec_name, cell_ref_or_value) in enumerate(heater_specs):
            # Check if this is a pre-formatted value (Spray Nozzle specs) or a cell reference
            if spec_name in ["Spray Nozzle P/N", "Spray Nozzle Size", "Spray Nozzle Length"]:
                spec_value = cell_ref_or_value  # This is already the formatted value
            else:
                spec_value = self.read_heater_spec_value(heater_design_file, cell_ref_or_value)
                if not spec_value:
                    spec_value = "No Data"
                # Prefer saved manual value if present (applies to all heater specs)
                manual_override = self.get_saved_manual_spec(spec_name)
                if manual_override:
                    spec_value = f"Manual: {manual_override}"
            
            # Determine button color and state
            if spec_value and spec_value not in ["No Spray Nozzle Found", "No Size Found", "No Length Found", "No Data"]:
                if spec_value.startswith("Manual:"):
                    button_color = "#FFE082"  # Light yellow for manual values
                else:
                    button_color = "#90EE90"  # Light green for found values
                button_state = "normal"
                cursor_type = "hand2"
            elif spec_value in ["No Spray Nozzle Found", "No Size Found", "No Length Found", "No Data"]:
                button_color = "#FFB6C1"  # Light pink for "No [item] Found" or "No Data"
                button_state = "disabled"
                cursor_type = "arrow"
            else:
                button_color = "#FFB6C1"  # Light pink for no value
                button_state = "disabled"
                cursor_type = "arrow"
            
            # Create button (much wider to fill all available space)
            spec_btn = tk.Button(parent_frame, 
                               text=f"{spec_name}: {spec_value or 'No Data'}",
                               state=button_state,
                               command=lambda file=heater_design_file: self.open_heater_design_file(file) if file else None,
                               width=60, height=1,
                               font=('Arial', 9),
                               relief='raised', bd=1,
                               cursor=cursor_type,
                               bg=button_color, fg="black",
                               activebackground=button_color, activeforeground="black")
            spec_btn.grid(row=18+i, column=0, sticky=(tk.W, tk.E), pady=1, padx=(0, 10))
            
            # Add right-click context menu
            self.create_spec_context_menu(spec_btn, spec_name, parent_frame, 18+i)
            
            self.spec_buttons.append(spec_btn)
            
            # Add input field for missing values (all "No Data" or "No [Item] Found" cases)
            if spec_value in ["No Spray Nozzle Found", "No Size Found", "No Length Found", "No Data"] or not spec_value:
                self.create_spec_input_field(parent_frame, spec_name, 18+i, 1)  # Column 1 for right side
    
    def create_spec_context_menu(self, button, spec_name, parent_frame, row):
        """Create right-click context menu for specification buttons"""
        def show_context_menu(event):
            context_menu = tk.Menu(self.root, tearoff=0)
            
            # Add Edit option
            context_menu.add_command(label="Edit", 
                                   command=lambda: self.edit_spec_value(spec_name, parent_frame, row))
            
            # Add Delete option (only if manual value exists)
            if self.get_saved_manual_spec(spec_name):
                context_menu.add_command(label="Delete", 
                                       command=lambda: self.delete_manual_spec(spec_name))
            
            # Add separator and refresh option
            context_menu.add_separator()
            context_menu.add_command(label="Refresh", 
                                   command=lambda: self.update_specifications(parent_frame))
            
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        button.bind("<Button-3>", show_context_menu)  # Right-click
    
    def edit_spec_value(self, spec_name, parent_frame, row):
        """Edit a specification value"""
        current_value = self.get_saved_manual_spec(spec_name)
        if current_value:
            # Remove "Manual:" prefix if present
            if current_value.startswith("Manual: "):
                current_value = current_value[8:]
        else:
            current_value = ""
        
        # Create edit dialog
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit {spec_name}")
        edit_window.geometry("400x150")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # Center the window
        edit_window.update_idletasks()
        x = (edit_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (edit_window.winfo_screenheight() // 2) - (150 // 2)
        edit_window.geometry(f"400x150+{x}+{y}")
        
        # Label
        ttk.Label(edit_window, text=f"Enter new value for {spec_name}:", font=('Arial', 10)).pack(pady=10)
        
        # Input field
        input_var = tk.StringVar(value=current_value)
        input_entry = ttk.Entry(edit_window, textvariable=input_var, width=40, font=('Arial', 10))
        input_entry.pack(pady=10)
        input_entry.focus()
        input_entry.select_range(0, tk.END)
        
        # Buttons
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Save", 
                command=lambda: self.save_edit_spec(spec_name, input_var.get(), edit_window),
                width=10, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Cancel", 
                command=edit_window.destroy,
                width=10, bg='#f44336', fg='white').pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save
        input_entry.bind('<Return>', lambda e: self.save_edit_spec(spec_name, input_var.get(), edit_window))
    
    def save_edit_spec(self, spec_name, value, window):
        """Save edited specification value"""
        if not value.strip():
            messagebox.showwarning("Warning", f"Please enter a value for {spec_name}")
            return
        
        self.save_manual_spec(spec_name, value)
        window.destroy()
    
    def delete_manual_spec(self, spec_name):
        """Delete a manual specification value for the current job"""
        job_number = str(self.job_number_var.get()).strip()
        if not job_number:
            return
        conn = sqlite3.connect(self.db_manager.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manual_specs (
                job_number TEXT NOT NULL,
                spec_name TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY(job_number, spec_name)
            )
        """)
        cur.execute("DELETE FROM manual_specs WHERE job_number = ? AND spec_name = ?", (job_number, spec_name))
        conn.commit()
        conn.close()
        messagebox.showinfo("Deleted", f"{spec_name} manual value deleted")
        # Refresh the specifications
        self.update_specifications(self.project_details_container.winfo_children()[0])
    
    def create_spec_input_field(self, parent_frame, spec_name, row, column=1):
        """Create an input field for manual entry of missing specifications"""
        # Create input frame for right side - positioned next to the button
        input_frame = tk.Frame(parent_frame)
        input_frame.grid(row=row, column=column, sticky=(tk.W, tk.E), pady=1, padx=(0, 0))
        
        # Input field (wider to use more space)
        input_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=input_var, width=25, font=('Arial', 9))
        input_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save button (wider for better visibility)
        save_btn = tk.Button(input_frame, text="Save", 
                           command=lambda: self.save_manual_spec(spec_name, input_var.get()),
                           width=8, height=1, font=('Arial', 9, 'bold'),
                           bg='#4CAF50', fg='white', relief='raised', bd=1)
        save_btn.pack(side=tk.LEFT, padx=(0, 0))
        
        # Store the input field for later reference
        self.spec_input_fields[spec_name] = input_frame
        
        # Load any previously saved value
        saved_value = self.get_saved_manual_spec(spec_name)
        if saved_value:
            input_var.set(saved_value)
        else:
            # Add placeholder text
            input_entry.insert(0, f"Enter value...")
            input_entry.bind('<FocusIn>', lambda e: input_entry.delete(0, tk.END) if input_entry.get() == f"Enter value..." else None)
            input_entry.bind('<FocusOut>', lambda e: input_entry.insert(0, f"Enter value...") if not input_entry.get() else None)
    
    def save_manual_spec(self, spec_name, value):
        """Save a manually entered specification value for the current job"""
        if not value.strip():
            messagebox.showwarning("Warning", f"Please enter a value for {spec_name}")
            return
        job_number = str(self.job_number_var.get()).strip()
        if not job_number:
            messagebox.showwarning("Warning", "No job number selected")
            return
        conn = sqlite3.connect(self.db_manager.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manual_specs (
                job_number TEXT NOT NULL,
                spec_name TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY(job_number, spec_name)
            )
        """)
        cur.execute("INSERT OR REPLACE INTO manual_specs (job_number, spec_name, value) VALUES (?, ?, ?)",
                    (job_number, spec_name, value.strip()))
        conn.commit()
        conn.close()
        messagebox.showinfo("Saved", f"{spec_name} saved as: {value.strip()}")
        # Update the specifications to show the saved value
        self.update_specifications(self.project_details_container.winfo_children()[0])
    
    def get_saved_manual_spec(self, spec_name):
        """Get a previously saved manual specification value for the current job"""
        job_number = str(self.job_number_var.get()).strip()
        if not job_number:
            return None
        conn = sqlite3.connect(self.db_manager.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manual_specs (
                job_number TEXT NOT NULL,
                spec_name TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY(job_number, spec_name)
            )
        """)
        cur.execute("SELECT value FROM manual_specs WHERE job_number = ? AND spec_name = ?", (job_number, spec_name))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    
    def read_heater_spec_value(self, file_path, cell_ref):
        """Read a specific cell value from the Heater Cross Section sheet"""
        if not file_path or not os.path.exists(file_path):
            return None
            
        try:
            import openpyxl
            
            # Load the workbook
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # Look for "Heater Cross Section" sheet
            cross_section_sheet = None
            for sheet_name in workbook.sheetnames:
                if "Heater Cross Section" in sheet_name:
                    cross_section_sheet = workbook[sheet_name]
                    break
            
            if not cross_section_sheet:
                print(f"No 'Heater Cross Section' sheet found in {file_path}")
                return None
            
            # Get the value from the specified cell
            cell_value = cross_section_sheet[cell_ref].value
            if cell_value is not None:
                print(f"Found {cell_ref}: {cell_value}")
                return str(cell_value)
            else:
                print(f"No value found in cell {cell_ref}")
                return None
            
        except Exception as e:
            print(f"Error reading cell {cell_ref} from {file_path}: {e}")
            return None
    
    def read_spray_nozzle_pn_from_files(self):
        """Read Spray Nozzle P/N by getting nozzle specs from Engineering Design file and looking up in Spray Nozzles file"""
        # First, find the Engineering Design file to get nozzle size and length
        engineering_design_file = None
        spray_nozzles_file = None
        
        if hasattr(self, 'engineering_general_docs') and self.engineering_general_docs:
            for file_path in self.engineering_general_docs:
                filename = os.path.basename(file_path).upper()
                if "ENGINEERING DESIGN" in filename:
                    engineering_design_file = file_path
                    print(f"Found Engineering Design file: {filename}")
                elif "SPRAY NOZZLES" in filename:
                    spray_nozzles_file = file_path
                    print(f"Found Spray Nozzles file: {filename}")
        
        if not engineering_design_file:
            print("No Engineering Design file found")
            return None
            
        if not spray_nozzles_file:
            print("No Spray Nozzles file found")
            return None
        
        # Get nozzle size and length from Engineering Design file
        nozzle_size = self.get_nozzle_size_from_heater_design(engineering_design_file)
        nozzle_length = self.get_nozzle_length_from_heater_design(engineering_design_file)
        
        if not nozzle_size or not nozzle_length:
            print(f"Could not get Nozzle Size or Length from Engineering Design file")
            return None
        
        # Now look up the part numbers in the Spray Nozzles file
        return self.lookup_spray_nozzle_pn(spray_nozzles_file, nozzle_size, nozzle_length)
    
    def get_spray_nozzle_size_from_engineering_design(self):
        """Get Spray Nozzle Size from Engineering Design file"""
        if hasattr(self, 'engineering_general_docs') and self.engineering_general_docs:
            for file_path in self.engineering_general_docs:
                filename = os.path.basename(file_path).upper()
                if "ENGINEERING DESIGN" in filename:
                    return self.get_nozzle_size_from_heater_design(file_path)
        return None
    
    def get_spray_nozzle_length_from_engineering_design(self):
        """Get Spray Nozzle Length from Engineering Design file"""
        if hasattr(self, 'engineering_general_docs') and self.engineering_general_docs:
            for file_path in self.engineering_general_docs:
                filename = os.path.basename(file_path).upper()
                if "ENGINEERING DESIGN" in filename:
                    return self.get_nozzle_length_from_heater_design(file_path)
        return None
    
    def lookup_spray_nozzle_pn(self, spray_nozzles_file, nozzle_size, nozzle_length):
        """Look up Spray Nozzle P/N in the Spray Nozzles file using size and length"""
        if not spray_nozzles_file or not os.path.exists(spray_nozzles_file):
            return None
            
        try:
            import openpyxl
            
            # Load the Spray Nozzles workbook
            workbook = openpyxl.load_workbook(spray_nozzles_file, data_only=True)
            
            # Look for "Spray Nozzles" sheet or "Nozzle Selection" sheet or use Sheet1
            spray_nozzles_sheet = None
            for sheet_name in workbook.sheetnames:
                if "Spray Nozzles" in sheet_name or "Nozzle Selection" in sheet_name:
                    spray_nozzles_sheet = workbook[sheet_name]
                    print(f"Found sheet: {sheet_name}")
                    break
            
            # If no "Spray Nozzles" or "Nozzle Selection" sheet found, try Sheet1
            if not spray_nozzles_sheet and "Sheet1" in workbook.sheetnames:
                spray_nozzles_sheet = workbook["Sheet1"]
                print(f"Using Sheet1 for Spray Nozzles data")
            
            if not spray_nozzles_sheet:
                print(f"No 'Spray Nozzles', 'Nozzle Selection', or 'Sheet1' sheet found in {spray_nozzles_file}")
                return None
            
            # Search for matching row based on Nozzle Size (Column A) and Nozzle Length (Column P)
            print(f"Searching for matching row in {spray_nozzles_sheet.max_row} rows...")
            print(f"Looking for Nozzle Size: {nozzle_size}, Nozzle Length: {nozzle_length}")
            
            for row in range(1, spray_nozzles_sheet.max_row + 1):
                cell_a = spray_nozzles_sheet[f'A{row}']  # Nozzle Size
                cell_p = spray_nozzles_sheet[f'P{row}']  # Nozzle Length
                
                # Debug: Print what we find in each row
                if cell_a.value or cell_p.value:
                    print(f"Row {row}: A='{cell_a.value}', P='{cell_p.value}'")
                
                # Check if both cells have values and match our criteria
                if cell_a.value and cell_p.value:
                    # Convert to strings and compare
                    size_match = str(cell_a.value).strip() == str(nozzle_size).strip()
                    length_match = str(cell_p.value).strip() == str(nozzle_length).strip()
                    
                    print(f"Row {row} - Size match: {size_match}, Length match: {length_match}")
                    
                    if size_match and length_match:
                        # Found the matching row! Get the part numbers from columns B and C
                        cell_b = spray_nozzles_sheet[f'B{row}']
                        cell_c = spray_nozzles_sheet[f'C{row}']
                        
                        if cell_b.value and cell_c.value:
                            column_b_value = str(cell_b.value).strip()
                            column_c_value = str(cell_c.value).strip()
                            spray_pn = f"{column_b_value}-{column_c_value}"
                            print(f"Found Spray Nozzle P/N: {spray_pn} in matching row {row}")
                            return spray_pn
            
            print(f"No matching row found for Nozzle Size: {nozzle_size}, Length: {nozzle_length}")
            return None
            
        except Exception as e:
            print(f"Error looking up Spray Nozzle P/N: {e}")
            return None
    
    def read_spray_nozzle_pn(self, file_path):
        """Read Spray Nozzle P/N by matching Nozzle Size and Length from Heater Design sheet"""
        if not file_path or not os.path.exists(file_path):
            return None
            
        try:
            import openpyxl
            
            # Load the workbook
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # First, get the Nozzle Size and Length from the Heater Design sheet
            nozzle_size = self.get_nozzle_size_from_heater_design(file_path)
            nozzle_length = self.get_nozzle_length_from_heater_design(file_path)
            
            if not nozzle_size or not nozzle_length:
                print(f"Could not get Nozzle Size or Length from Heater Design sheet")
                return None
            
            print(f"Looking for Nozzle Size: {nozzle_size}, Nozzle Length: {nozzle_length}")
            
            # Look for "Spray Nozzles" sheet or "Nozzle Selection" sheet or use Sheet1
            spray_nozzles_sheet = None
            for sheet_name in workbook.sheetnames:
                if "Spray Nozzles" in sheet_name or "Nozzle Selection" in sheet_name:
                    spray_nozzles_sheet = workbook[sheet_name]
                    print(f"Found sheet: {sheet_name}")
                    break
            
            # If no "Spray Nozzles" or "Nozzle Selection" sheet found, try Sheet1
            if not spray_nozzles_sheet and "Sheet1" in workbook.sheetnames:
                spray_nozzles_sheet = workbook["Sheet1"]
                print(f"Using Sheet1 for Spray Nozzles data")
            
            if not spray_nozzles_sheet:
                print(f"No 'Spray Nozzles', 'Nozzle Selection', or 'Sheet1' sheet found in {file_path}")
                return None
            
            # Search for matching row based on Nozzle Size (Column A) and Nozzle Length (Column P)
            print(f"Searching for matching row in {spray_nozzles_sheet.max_row} rows...")
            
            for row in range(1, spray_nozzles_sheet.max_row + 1):
                cell_a = spray_nozzles_sheet[f'A{row}']  # Nozzle Size
                cell_p = spray_nozzles_sheet[f'P{row}']  # Nozzle Length
                
                # Debug: Print what we find in each row
                if cell_a.value or cell_p.value:
                    print(f"Row {row}: A='{cell_a.value}', P='{cell_p.value}'")
                
                # Check if both cells have values and match our criteria
                if cell_a.value and cell_p.value:
                    # Convert to strings and compare
                    size_match = str(cell_a.value).strip() == str(nozzle_size).strip()
                    length_match = str(cell_p.value).strip() == str(nozzle_length).strip()
                    
                    print(f"Row {row} - Size match: {size_match}, Length match: {length_match}")
                    
                    if size_match and length_match:
                        # Found the matching row! Get the part numbers from columns B and C
                        cell_b = spray_nozzles_sheet[f'B{row}']
                        cell_c = spray_nozzles_sheet[f'C{row}']
                        
                        if cell_b.value and cell_c.value:
                            column_b_value = str(cell_b.value).strip()
                            column_c_value = str(cell_c.value).strip()
                            spray_pn = f"{column_b_value}-{column_c_value}"
                            print(f"Found Spray Nozzle P/N: {spray_pn} in matching row {row}")
                            return spray_pn
            
            print(f"No matching row found for Nozzle Size: {nozzle_size}, Length: {nozzle_length}")
            return None
            
        except Exception as e:
            print(f"Error reading Spray Nozzle P/N from {file_path}: {e}")
            return None
    
    def get_nozzle_size_from_heater_design(self, file_path):
        """Get Nozzle Size from L22 in Heater Design sheet"""
        try:
            import openpyxl
            
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # Look for "Heater Design" sheet
            heater_sheet = None
            for sheet_name in workbook.sheetnames:
                if "Heater Design" in sheet_name:
                    heater_sheet = workbook[sheet_name]
                    break
            
            if not heater_sheet:
                print(f"No 'Heater Design' sheet found for nozzle size")
                return None
            
            # Get value from L22
            cell_l22 = heater_sheet['L22']
            if cell_l22.value:
                nozzle_size = str(cell_l22.value).strip()
                print(f"Found Nozzle Size: {nozzle_size}")
                return nozzle_size
            
            return None
            
        except Exception as e:
            print(f"Error getting nozzle size: {e}")
            return None
    
    def get_nozzle_length_from_heater_design(self, file_path):
        """Get Nozzle Length from L21 in Heater Design sheet"""
        try:
            import openpyxl
            
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # Look for "Heater Design" sheet
            heater_sheet = None
            for sheet_name in workbook.sheetnames:
                if "Heater Design" in sheet_name:
                    heater_sheet = workbook[sheet_name]
                    break
            
            if not heater_sheet:
                print(f"No 'Heater Design' sheet found for nozzle length")
                return None
            
            # Get value from L21
            cell_l21 = heater_sheet['L21']
            if cell_l21.value:
                nozzle_length = str(cell_l21.value).strip()
                print(f"Found Nozzle Length: {nozzle_length}")
                return nozzle_length
            
            return None
            
        except Exception as e:
            print(f"Error getting nozzle length: {e}")
            return None
    
    def has_heater_design_sheet(self, file_path):
        """Check if an Excel file has a 'Heater Design' sheet inside it"""
        try:
            import openpyxl
            
            # Load the workbook
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # Check if any sheet name contains "Heater Design"
            for sheet_name in workbook.sheetnames:
                if "Heater Design" in sheet_name:
                    print(f"Found 'Heater Design' sheet in file: {os.path.basename(file_path)}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error checking for Heater Design sheet in {file_path}: {e}")
            return False
    
    def read_excel_can_size(self, file_path):
        """Read Can Size from Excel file (column I, value from column L) on 'Heater Design' sheet"""
        try:
            import openpyxl
            
            # Load the workbook
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # Look for "Heater Design" sheet specifically
            heater_sheet = None
            for sheet_name in workbook.sheetnames:
                if "Heater Design" in sheet_name:
                    heater_sheet = workbook[sheet_name]
                    break
            
            if not heater_sheet:
                print(f"No 'Heater Design' sheet found in {file_path}")
                return None
            
            # Method 1: Look for "Can Size:" in column I and get value from column L
            for row in range(1, heater_sheet.max_row + 1):
                cell_i = heater_sheet[f'I{row}']
                if cell_i.value and "Can Size" in str(cell_i.value):
                    # Get the value from column L in the same row
                    cell_l = heater_sheet[f'L{row}']
                    if cell_l.value:
                        print(f"Found Can Size: {cell_l.value} in row {row} (method 1)")
                        return str(cell_l.value)
            
            # Method 2: Check cell L48 directly (fallback)
            cell_l48 = heater_sheet['L48']
            if cell_l48.value:
                print(f"Found Can Size: {cell_l48.value} in cell L48 (method 2)")
                return str(cell_l48.value)
            
            print(f"No 'Can Size:' found in column I or L48 of Heater Design sheet")
            return None
            
        except Exception as e:
            print(f"Error reading Excel file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def open_heater_design_file(self, file_path):
        """Open the Heater Design file"""
        if file_path and os.path.exists(file_path):
            self.open_path(file_path)
        else:
            messagebox.showwarning("Warning", "Heater Design file not found!")
    
    def create_workflow_panel(self):
        """Create the workflow tracking panel with collapsible sections"""
        # Main container
        main_container = ttk.Frame(self.workflow_container)
        main_container.pack(fill=tk.BOTH, expand=True, padx=(0, 5))
        main_container.columnconfigure(0, weight=1)
        
        # Toolbar at the top
        self.create_workflow_toolbar(main_container)
        
        # Scrollable workflow content
        canvas = tk.Canvas(main_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        workflow_frame = ttk.Frame(canvas)
        
        workflow_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=workflow_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Make canvas expand to fill width
        def _configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', _configure_canvas)
        
        # Enable mouse wheel scrolling
        self._bind_mousewheel(canvas, workflow_frame)
        
        main_container.rowconfigure(1, weight=1)
        workflow_frame.columnconfigure(0, weight=1)
        
        # Section 1: Drafting & Redline Updates
        self.drafting_section = CollapsibleFrame(workflow_frame, "Drafting & Redline Updates")
        self.drafting_section.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.create_drafting_redline_content(self.drafting_section.content)
        
        # Section 2: Production & OPS Review  
        self.production_section = CollapsibleFrame(workflow_frame, "Production & OPS Review")
        self.production_section.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.create_production_ops_content(self.production_section.content)
        
        # Section 3: D365 & Release
        self.release_section = CollapsibleFrame(workflow_frame, "D365 & Release")
        self.release_section.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.create_d365_release_content(self.release_section.content)
    
    def create_workflow_toolbar(self, parent):
        """Create toolbar with print button"""
        toolbar = ttk.Frame(parent, relief='raised', padding="5")
        toolbar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        toolbar.columnconfigure(0, weight=1)
        
        # Title on the left
        title_label = ttk.Label(toolbar, text="Project Workflow", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Print button on the right
        self.cover_sheet_btn = ttk.Button(toolbar, text="🖨️ Print Status Report", 
                                         command=self.print_cover_sheet,
                                         style='Accent.TButton')
        self.cover_sheet_btn.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
    
    def create_cover_sheet_button(self, parent):
        """Create the cover sheet print button"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        
        # Cover sheet button - will be updated based on project status
        self.cover_sheet_btn = ttk.Button(button_frame, text="📄 Print Status Report", 
                                         command=self.print_cover_sheet, width=25)
        self.cover_sheet_btn.grid(row=0, column=0, pady=5)
        
        # Initialize button state
        self.update_cover_sheet_button()
    
    def print_cover_sheet(self):
        """Print the project cover sheet"""
        if not self.current_project:
            messagebox.showwarning("Warning", "Please select a project first!")
            return
        
        try:
            from project_cover_sheet import print_project_cover_sheet
            print_project_cover_sheet(self.current_project, self.db_manager)
        except ImportError:
            messagebox.showerror("Error", "Cover sheet module not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print cover sheet: {str(e)}")
    
    def update_release_due_display(self, *args):
        """Update the Release to Dee due date display"""
        try:
            due_date_str = self.release_due_date_entry.get()
            if not due_date_str:
                self.release_due_display_var.set("")
                return
            
            # Parse the due date
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            
            # Calculate difference
            delta = (due_date - today).days
            
            if delta == 0:
                display_text = "Due TODAY"
                color = "red"
            elif delta > 0:
                display_text = f"Due in {delta} day{'s' if delta != 1 else ''}"
                color = "blue" if delta > 3 else "orange"
            else:
                display_text = f"Due {abs(delta)} day{'s' if abs(delta) != 1 else ''} ago"
                color = "red"
            
            self.release_due_display_var.set(display_text)
            self.release_due_display_label.config(foreground=color)
            
        except (ValueError, AttributeError):
            self.release_due_display_var.set("")
    
    def update_cover_sheet_button(self):
        """Update the cover sheet button appearance based on project status"""
        if not hasattr(self, 'cover_sheet_btn'):
            return
            
        if not self.current_project:
            self.cover_sheet_btn.config(text="📄 Print Status Report", 
                                      style="TButton")
            return
        
        # Check if there are recent updates that warrant a new report
        has_updates = self.check_for_recent_updates()
        
        if has_updates:
            # Make button stand out with different color/text
            self.cover_sheet_btn.config(text="🆕 Print NEW Status Report", 
                                      style="Accent.TButton")
            # Try to make it more visually distinct
            try:
                self.cover_sheet_btn.configure(background='#ff6b6b', foreground='white')
            except:
                pass  # Fallback if styling doesn't work
        else:
            self.cover_sheet_btn.config(text="📄 Print Status Report", 
                                      style="TButton")
            # Reset to default styling
            try:
                self.cover_sheet_btn.configure(background='', foreground='')
            except:
                pass
    
    def check_for_recent_updates(self):
        """Check if there are recent updates since last report"""
        if not self.current_project:
            return False
            
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            # Get the last cover sheet date
            cursor.execute("""
                SELECT last_cover_sheet_date FROM projects 
                WHERE job_number = ?
            """, (self.current_project,))
            result = cursor.fetchone()
            last_cover_sheet_date = result[0] if result and result[0] else None
            
            if not last_cover_sheet_date:
                # No cover sheet generated yet, so there are "updates"
                conn.close()
                return True
            
            # Check if any workflow data has been updated since last cover sheet
            from datetime import datetime
            last_date = datetime.strptime(last_cover_sheet_date, "%Y-%m-%d %H:%M:%S")
            
            # Get project ID
            cursor.execute("SELECT id FROM projects WHERE job_number = ?", (self.current_project,))
            project_id = cursor.fetchone()[0]
            
            # Check for recent updates in workflow tables
            tables_to_check = [
                ("initial_redline", "redline_date"),
                ("redline_updates", "update_date"),
                ("ops_review", "review_date"),
                ("peter_weck_review", "fixed_errors_date"),
                ("release_to_dee", "release_date")
            ]
            
            for table, date_column in tables_to_check:
                cursor.execute(f"""
                    SELECT {date_column} FROM {table} 
                    WHERE project_id = ? AND {date_column} IS NOT NULL
                """, (project_id,))
                dates = cursor.fetchall()
                
                for date_row in dates:
                    if date_row[0]:
                        try:
                            update_date = datetime.strptime(date_row[0], "%Y-%m-%d")
                            if update_date > last_date:
                                conn.close()
                                return True
                        except ValueError:
                            # Skip invalid dates
                            continue
            
            conn.close()
            return False
            
        except Exception as e:
            print(f"Error checking for updates: {e}")
            # Default to showing updates available
            return True
    
    def create_initial_redline_section(self, parent, row):
        """Create initial redline section"""
        section_frame = ttk.LabelFrame(parent, text="1. Drafting Drawing Package to Engineering for Initial Review", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # Initial Redline checkbox
        self.initial_redline_var = tk.BooleanVar()
        ttk.Checkbutton(section_frame, text="Initial Redline", 
                       variable=self.initial_redline_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Engineer dropdown
        ttk.Label(section_frame, text="Engineer:").grid(row=1, column=0, sticky=tk.W)
        self.initial_engineer_var = tk.StringVar()
        self.initial_engineer_combo = ttk.Combobox(section_frame, textvariable=self.initial_engineer_var, 
                                                 state="readonly", width=20)
        self.initial_engineer_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Date
        ttk.Label(section_frame, text="Date:").grid(row=2, column=0, sticky=tk.W)
        self.initial_date_entry = DateEntry(section_frame, width=20)
        self.initial_date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
    
    def create_redline_updates_section(self, parent, row):
        """Create redline updates section"""
        section_frame = ttk.LabelFrame(parent, text="2. Redline Updates", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # Update 1
        self.create_redline_update(section_frame, 0, "Redline Update 1")
        self.create_redline_update(section_frame, 1, "Redline Update 2")
        self.create_redline_update(section_frame, 2, "Redline Update 3")
        self.create_redline_update(section_frame, 3, "Redline Update 4")
    
    def create_redline_update(self, parent, row, title):
        """Create a single redline update"""
        update_frame = ttk.Frame(parent)
        update_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
        update_frame.columnconfigure(1, weight=1)
        
        # Checkbox
        var_name = f"redline_update_{row+1}_var"
        # Don't create BooleanVar here - it's already created in __init__
        ttk.Checkbutton(update_frame, text=title, 
                       variable=getattr(self, var_name)).grid(row=0, column=0, sticky=tk.W)
        
        # Engineer dropdown
        ttk.Label(update_frame, text="Engineer:").grid(row=1, column=0, sticky=tk.W)
        engineer_var_name = f"redline_update_{row+1}_engineer_var"
        setattr(self, engineer_var_name, tk.StringVar())
        combo = ttk.Combobox(update_frame, textvariable=getattr(self, engineer_var_name), 
                           state="readonly", width=15)
        combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Store the combo reference for later use
        combo_name = f"redline_update_{row+1}_engineer_combo"
        setattr(self, combo_name, combo)
        
        # Date
        ttk.Label(update_frame, text="Date:").grid(row=2, column=0, sticky=tk.W)
        date_entry_name = f"redline_update_{row+1}_date_entry"
        date_entry = DateEntry(update_frame, width=15)
        date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        setattr(self, date_entry_name, date_entry)
    
    def create_ops_review_section(self, parent, row):
        """Create OPS review section"""
        section_frame = ttk.LabelFrame(parent, text="3. To Production for OPS Review", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # OPS Review checkbox
        self.ops_review_var = tk.BooleanVar()
        ttk.Checkbutton(section_frame, text="OPS Review Updates", 
                       variable=self.ops_review_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Date
        ttk.Label(section_frame, text="Updated:").grid(row=1, column=0, sticky=tk.W)
        self.ops_review_date_entry = DateEntry(section_frame, width=20)
        self.ops_review_date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
    
    def create_d365_bom_section(self, parent, row):
        """Create D365 BOM Entry section"""
        section_frame = ttk.LabelFrame(parent, text="4. D365 BOM Entry", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # D365 BOM Entry checkbox
        self.d365_bom_var = tk.BooleanVar()
        ttk.Checkbutton(section_frame, text="D365 BOM Entry", 
                       variable=self.d365_bom_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Date
        ttk.Label(section_frame, text="Date:").grid(row=1, column=0, sticky=tk.W)
        self.d365_bom_date_entry = DateEntry(section_frame, width=20)
        self.d365_bom_date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
    
    def create_peter_weck_section(self, parent, row):
        """Create Peter Weck review section"""
        section_frame = ttk.LabelFrame(parent, text="5. PETER WECK Review", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # Fixed Errors checkbox
        self.peter_weck_var = tk.BooleanVar()
        ttk.Checkbutton(section_frame, text="Fixed Errors", 
                       variable=self.peter_weck_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Date
        ttk.Label(section_frame, text="Date:").grid(row=1, column=0, sticky=tk.W)
        self.peter_weck_date_entry = DateEntry(section_frame, width=20)
        self.peter_weck_date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
    
    def create_release_to_dee_section(self, parent, row):
        """Create Release to Dee section"""
        section_frame = ttk.LabelFrame(parent, text="6. Release to Dee", padding="5")
        section_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        section_frame.columnconfigure(1, weight=1)
        
        # Fixed Errors checkbox
        self.release_fixed_errors_var = tk.BooleanVar()
        ttk.Checkbutton(section_frame, text="Fixed Errors", 
                       variable=self.release_fixed_errors_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Missing Prints
        ttk.Label(section_frame, text="Missing Prints:").grid(row=1, column=0, sticky=tk.W)
        self.missing_prints_date_entry = DateEntry(section_frame, width=20)
        self.missing_prints_date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # D365 Updates
        ttk.Label(section_frame, text="D365 Updates:").grid(row=2, column=0, sticky=tk.W)
        self.d365_updates_date_entry = DateEntry(section_frame, width=20)
        self.d365_updates_date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Other
        ttk.Label(section_frame, text="Other:").grid(row=3, column=0, sticky=tk.W)
        self.other_notes_var = tk.StringVar()
        self.other_notes_entry = ttk.Entry(section_frame, textvariable=self.other_notes_var, width=20)
        self.other_notes_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(section_frame, text="Date:").grid(row=4, column=0, sticky=tk.W)
        self.other_date_entry = DateEntry(section_frame, width=20)
        self.other_date_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Due Date with auto-updating display
        ttk.Label(section_frame, text="Due Date:").grid(row=5, column=0, sticky=tk.W)
        self.release_due_date_entry = DateEntry(section_frame, width=20)
        self.release_due_date_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Due date display (auto-updating)
        self.release_due_display_var = tk.StringVar()
        self.release_due_display_label = ttk.Label(section_frame, textvariable=self.release_due_display_var, 
                                                   foreground="blue", font=('Arial', 9, 'italic'))
        self.release_due_display_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
        # Set up auto-save traces for all workflow fields
        self.setup_workflow_autosave()
    
    def create_drafting_redline_content(self, parent):
        """Create content for Drafting & Redline Updates section"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # Initial Redline
        ttk.Label(parent, text="Initial Redline:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        row += 1
        
        self.initial_redline_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Completed", variable=self.initial_redline_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=6)
        row += 1
        
        ttk.Label(parent, text="Engineer:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.initial_engineer_var = tk.StringVar()
        self.initial_engineer_combo = ttk.Combobox(parent, textvariable=self.initial_engineer_var, state="readonly", width=25)
        self.initial_engineer_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        ttk.Label(parent, text="Date:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.initial_date_entry = DateEntry(parent, width=25)
        self.initial_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        # Redline Updates
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        ttk.Label(parent, text="Redline Updates:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        row += 1
        
        for i in range(1, 5):
            checkbox_var = tk.BooleanVar()
            setattr(self, f"redline_update_{i}_var", checkbox_var)
            ttk.Checkbutton(parent, text=f"Update {i}", variable=checkbox_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=6)
            row += 1
            
            ttk.Label(parent, text="Engineer:").grid(row=row, column=0, sticky=tk.W, pady=6)
            engineer_var = tk.StringVar()
            setattr(self, f"redline_update_{i}_engineer_var", engineer_var)
            combo = ttk.Combobox(parent, textvariable=engineer_var, state="readonly", width=25)
            setattr(self, f"redline_update_{i}_engineer_combo", combo)
            combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
            row += 1
            
            ttk.Label(parent, text="Date:").grid(row=row, column=0, sticky=tk.W, pady=6)
            date_entry = DateEntry(parent, width=25)
            setattr(self, f"redline_update_{i}_date_entry", date_entry)
            date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
            row += 1
            
            if i < 4:
                ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=6)
                row += 1
    
    def create_production_ops_content(self, parent):
        """Create content for Production & OPS Review section"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # OPS Review
        ttk.Label(parent, text="OPS Review:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        row += 1
        
        self.ops_review_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="OPS Review Updates", variable=self.ops_review_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=6)
        row += 1
        
        ttk.Label(parent, text="Updated:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.ops_review_date_entry = DateEntry(parent, width=25)
        self.ops_review_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        # Peter Weck Review
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        ttk.Label(parent, text="Peter Weck Review:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        row += 1
        
        self.peter_weck_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Fixed Errors", variable=self.peter_weck_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=6)
        row += 1
        
        ttk.Label(parent, text="Date:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.peter_weck_date_entry = DateEntry(parent, width=25)
        self.peter_weck_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
    
    def create_d365_release_content(self, parent):
        """Create content for D365 & Release section"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # D365 BOM Entry
        ttk.Label(parent, text="D365 BOM Entry:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        row += 1
        
        self.d365_bom_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="D365 BOM Entry", variable=self.d365_bom_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=6)
        row += 1
        
        ttk.Label(parent, text="Date:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.d365_bom_date_entry = DateEntry(parent, width=25)
        self.d365_bom_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        # Release to Dee
        ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        ttk.Label(parent, text="Release to Dee:", font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))
        row += 1
        
        self.release_fixed_errors_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Fixed Errors", variable=self.release_fixed_errors_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=6)
        row += 1
        
        ttk.Label(parent, text="Missing Prints:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.missing_prints_date_entry = DateEntry(parent, width=25)
        self.missing_prints_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        ttk.Label(parent, text="D365 Updates:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.d365_updates_date_entry = DateEntry(parent, width=25)
        self.d365_updates_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        ttk.Label(parent, text="Other:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.other_notes_var = tk.StringVar()
        self.other_notes_entry = ttk.Entry(parent, textvariable=self.other_notes_var, width=25)
        self.other_notes_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        ttk.Label(parent, text="Date:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.other_date_entry = DateEntry(parent, width=25)
        self.other_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        ttk.Label(parent, text="Due Date:").grid(row=row, column=0, sticky=tk.W, pady=6)
        self.release_due_date_entry = DateEntry(parent, width=25)
        self.release_due_date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=6)
        row += 1
        
        # Due date display
        self.release_due_display_var = tk.StringVar()
        self.release_due_display_label = ttk.Label(parent, textvariable=self.release_due_display_var, 
                                                   foreground="blue", font=('Arial', 9, 'italic'))
        self.release_due_display_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
        # Set up auto-save
        self.setup_workflow_autosave()
    
    def setup_workflow_autosave(self):
        """Set up auto-save traces for all workflow fields"""
        # Auto-save for initial redline
        if hasattr(self, 'initial_redline_var'):
            self.initial_redline_var.trace('w', self.auto_save)
        if hasattr(self, 'initial_engineer_var'):
            self.initial_engineer_var.trace('w', self.auto_save)
        if hasattr(self, 'initial_date_entry'):
            self.initial_date_entry.var.trace('w', self.auto_save)
        
        # Auto-save for redline updates
        for i in range(1, 5):
            var_name = f"redline_update_{i}_var"
            engineer_var_name = f"redline_update_{i}_engineer_var"
            date_entry_name = f"redline_update_{i}_date_entry"
            
            if hasattr(self, var_name):
                getattr(self, var_name).trace('w', self.auto_save)
            if hasattr(self, engineer_var_name):
                getattr(self, engineer_var_name).trace('w', self.auto_save)
            if hasattr(self, date_entry_name):
                getattr(self, date_entry_name).var.trace('w', self.auto_save)
        
        # Auto-save for OPS review
        if hasattr(self, 'ops_review_var'):
            self.ops_review_var.trace('w', self.auto_save)
        if hasattr(self, 'ops_review_date_entry'):
            self.ops_review_date_entry.var.trace('w', self.auto_save)
        
        # Auto-save for D365 BOM Entry
        if hasattr(self, 'd365_bom_var'):
            self.d365_bom_var.trace('w', self.auto_save)
        if hasattr(self, 'd365_bom_date_entry'):
            self.d365_bom_date_entry.var.trace('w', self.auto_save)
        
        # Auto-save for Peter Weck review
        if hasattr(self, 'peter_weck_var'):
            self.peter_weck_var.trace('w', self.auto_save)
        if hasattr(self, 'peter_weck_date_entry'):
            self.peter_weck_date_entry.var.trace('w', self.auto_save)
        
        # Auto-save for release to Dee
        if hasattr(self, 'release_fixed_errors_var'):
            self.release_fixed_errors_var.trace('w', self.auto_save)
        if hasattr(self, 'missing_prints_date_entry'):
            self.missing_prints_date_entry.var.trace('w', self.auto_save)
        if hasattr(self, 'd365_updates_date_entry'):
            self.d365_updates_date_entry.var.trace('w', self.auto_save)
        if hasattr(self, 'other_notes_var'):
            self.other_notes_var.trace('w', self.auto_save)
        if hasattr(self, 'other_date_entry'):
            self.other_date_entry.var.trace('w', self.auto_save)
        if hasattr(self, 'release_due_date_entry'):
            self.release_due_date_entry.var.trace('w', self.auto_save)
            self.release_due_date_entry.var.trace('w', self.update_release_due_display)
    
    def create_quick_access_panel(self):
        """Create the quick access panel for files and folders with scrolling"""
        main_container = ttk.LabelFrame(self.quick_access_container, text="Quick Access", padding="5")
        main_container.pack(fill=tk.BOTH, expand=True)
        main_container.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Create frame inside canvas for content
        self.access_frame = ttk.Frame(canvas)
        self.access_frame.columnconfigure(0, weight=1)
        
        # Store canvas reference for later updates
        self.quick_access_canvas = canvas
        
        # Configure canvas scrolling with better region calculation
        def update_scroll_region(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.access_frame.bind("<Configure>", update_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=self.access_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid canvas and scrollbar (always show scrollbar)
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Adjust canvas window width when canvas resizes
        def _configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', _configure_canvas)
        
        # Enable mouse wheel scrolling
        self._bind_mousewheel(canvas, self.access_frame)
        
        # Initialize empty quick access area
        self.quick_access_buttons = []
        self.update_quick_access()
    
    def update_quick_access(self):
        """Update the quick access panel based on current project data"""
        # Clear existing buttons
        for button in self.quick_access_buttons:
            button.destroy()
        self.quick_access_buttons.clear()
        
        row = 0
        # Track paths and new/changed flags for this project
        changed_paths = set()
        def track_path(path):
            if not path:
                return False
            try:
                if os.path.exists(path):
                    mtime = os.path.getmtime(path)
                else:
                    return False
                conn = sqlite3.connect(self.db_manager.db_path)
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS file_timestamps (
                        job_number TEXT NOT NULL,
                        path TEXT NOT NULL,
                        last_mtime REAL NOT NULL,
                        acknowledged INTEGER NOT NULL DEFAULT 1,
                        PRIMARY KEY(job_number, path)
                    )
                """)
                job_num = str(self.job_number_var.get()).strip()
                cur.execute("SELECT last_mtime, acknowledged FROM file_timestamps WHERE job_number=? AND path=?", (job_num, path))
                rowx = cur.fetchone()
                is_changed = False
                if rowx is None:
                    cur.execute("INSERT OR REPLACE INTO file_timestamps(job_number, path, last_mtime, acknowledged) VALUES(?,?,?,0)", (job_num, path, mtime))
                    is_changed = True
                else:
                    prev_mtime, acknowledged = rowx
                    if abs(mtime - prev_mtime) > 1e-6:
                        cur.execute("UPDATE file_timestamps SET last_mtime=?, acknowledged=0 WHERE job_number=? AND path=?", (mtime, job_num, path))
                        is_changed = True
                    elif acknowledged == 0:
                        is_changed = True
                conn.commit(); conn.close()
                if is_changed:
                    changed_paths.add(path)
                return is_changed
            except Exception:
                return False
        
        def style_button(btn, path):
            if path and path in changed_paths:
                try:
                    btn.configure(style='Changed.TButton')
                except Exception:
                    s = ttk.Style()
                    s.configure('Changed.TButton', background='#FFB74D')
                    btn.configure(style='Changed.TButton')
        
        # Job Directory button - use job number as button text
        job_dir = self.job_directory_picker.get()
        job_number = self.job_number_var.get()
        if job_dir and job_number:
            icon = "📁" if os.path.isdir(job_dir) else "📄"
            button_text = f"{icon} {job_number}"
            button = ttk.Button(self.access_frame, text=button_text, 
                              command=self.open_job_directory)
            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
            self.quick_access_buttons.append(button)
            row += 1
        
        # Customer Name button - use directory picker value if available
        customer_name = self.customer_name_var.get()
        customer_name_dir = self.customer_name_picker.get()
        
        if customer_name_dir:  # Use directory picker value first
            if os.path.exists(customer_name_dir):
                icon = "📁" if os.path.isdir(customer_name_dir) else "📄"
                # Just show the customer name from the text field, not the folder basename
                button_text = f"{icon} {customer_name}"
            else:
                icon = "📁"
                button_text = f"{icon} {customer_name}"
        elif customer_name:  # Fall back to text field value
            if os.path.exists(customer_name):
                icon = "📁" if os.path.isdir(customer_name) else "📄"
                button_text = f"{icon} {customer_name}"
            else:
                icon = "📁"
                button_text = f"{icon} {customer_name}"
        else:
            customer_name_dir = None
            button_text = None
        
        if button_text:
            path0 = customer_name_dir or customer_name
            changed = track_path(path0)
            button = ttk.Button(self.access_frame, text=button_text, 
                              command=lambda p=path0: self.open_customer_name_path(p))
            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
            style_button(button, path0 if changed else None)
            self.quick_access_buttons.append(button)
            row += 1
        
        # Customer Location button - use directory picker value if available
        customer_location = self.customer_location_var.get()
        customer_location_dir = self.customer_location_picker.get()
        
        if customer_location_dir:  # Use directory picker value first
            if os.path.exists(customer_location_dir):
                icon = "📁" if os.path.isdir(customer_location_dir) else "📄"
                # Just show the customer location from the text field, not the folder basename
                button_text = f"{icon} {customer_location}"
            else:
                icon = "📁"
                button_text = f"{icon} {customer_location}"
        elif customer_location:  # Fall back to text field value
            if os.path.exists(customer_location):
                icon = "📁" if os.path.isdir(customer_location) else "📄"
                button_text = f"{icon} {customer_location}"
            else:
                icon = "📁"
                button_text = f"{icon} {customer_location}"
        else:
            customer_location_dir = None
            button_text = None
        
        if button_text:
            path1 = customer_location_dir or customer_location
            changed = track_path(path1)
            button = ttk.Button(self.access_frame, text=button_text, 
                              command=lambda p=path1: self.open_customer_location_path(p))
            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
            style_button(button, path1 if changed else None)
            self.quick_access_buttons.append(button)
            row += 1
        
        # KOM AND OC FORM section - always show if job directory is loaded
        if hasattr(self, 'job_directory_picker') and self.job_directory_picker.get():
            if hasattr(self, 'kom_oc_form_path') and self.kom_oc_form_path and os.path.exists(self.kom_oc_form_path):
                button_text = f"📊 KOM AND OC FORM"
                button = ttk.Button(self.access_frame, text=button_text, 
                                  command=self.open_kom_oc_form)
                button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                self.quick_access_buttons.append(button)
                row += 1
            else:
                # No KOM file found - show placeholder
                kom_placeholder = ttk.Label(self.access_frame, text="KOM AND OC FORM: NOT FOUND", 
                                         font=('Arial', 9), foreground="gray")
                kom_placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                self.quick_access_buttons.append(kom_placeholder)
                row += 1
        
        # Sales documents section - always show if job directory is loaded
        if hasattr(self, 'job_directory_picker') and self.job_directory_picker.get():
            # Add SALES divider
            sales_label = ttk.Label(self.access_frame, text="SALES", font=('Arial', 10, 'bold'), foreground="blue")
            sales_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(10, 5))
            self.quick_access_buttons.append(sales_label)
            row += 1
            
            # Check if there are any sales files
            has_sales_files = (hasattr(self, 'proposal_docs') and self.proposal_docs) or (hasattr(self, 'other_docs') and self.other_docs)
            
            if has_sales_files:
                # Proposal documents buttons - automatically added when job directory is loaded
                if hasattr(self, 'proposal_docs') and self.proposal_docs:
                    for doc_path in self.proposal_docs:
                        # Use actual filename with truncation
                        filename = os.path.basename(doc_path)
                        # Remove file extension and truncate if too long
                        name_without_ext = os.path.splitext(filename)[0]
                        # Increase max length to 35 to show more of the filename
                        if len(name_without_ext) > 35:
                            display_name = name_without_ext[:32] + "..."
                        else:
                            display_name = name_without_ext
                        
                        button_text = f"📄 {display_name}"
                        button = ttk.Button(self.access_frame, text=button_text, 
                                          command=lambda path=doc_path: self.open_proposal_doc(path))
                        button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(button)
                        row += 1
                
                # Other important documents buttons - automatically added when job directory is loaded
                if hasattr(self, 'other_docs') and self.other_docs:
                    for icon, filename, file_path in self.other_docs:
                        # Create shorter, consistent button labels
                        button_text = self.create_short_button_text(icon, filename)
                        button = ttk.Button(self.access_frame, text=button_text, 
                                          command=lambda path=file_path: self.open_other_doc(path))
                        button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(button)
                        row += 1
            else:
                # No sales files found - show placeholder
                placeholder_label = ttk.Label(self.access_frame, text="SALES: NOT PROCESSED", 
                                           font=('Arial', 9), foreground="gray", style="Placeholder.TLabel")
                placeholder_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                self.quick_access_buttons.append(placeholder_label)
                row += 1
        
        # Engineering documents section - always show if job directory is loaded
        if hasattr(self, 'job_directory_picker') and self.job_directory_picker.get():
            # Add ENGINEERING divider
            engineering_label = ttk.Label(self.access_frame, text="ENGINEERING", font=('Arial', 10, 'bold'), foreground="green")
            engineering_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(10, 5))
            self.quick_access_buttons.append(engineering_label)
            row += 1
            
            # Check if there are any engineering files
            has_engineering_files = (hasattr(self, 'engineering_general_docs') and self.engineering_general_docs) or (hasattr(self, 'engineering_releases_docs') and self.engineering_releases_docs)
            
            if has_engineering_files:
                # General Design subsection
                if hasattr(self, 'engineering_general_docs') and self.engineering_general_docs:
                    general_label = ttk.Label(self.access_frame, text="General Design", font=('Arial', 9, 'bold'), foreground="darkgreen")
                    general_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                    self.quick_access_buttons.append(general_label)
                    row += 1
                    
                    for file_path in self.engineering_general_docs:
                        filename = os.path.basename(file_path)
                        button_text = self.create_short_button_text("📊", filename)
                        button = ttk.Button(self.access_frame, text=button_text, 
                                          command=lambda path=file_path: self.open_engineering_doc(path))
                        button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(button)
                        row += 1
                else:
                    # No General Design files - show placeholder
                    general_placeholder = ttk.Label(self.access_frame, text="General Design: NOT PROCESSED", 
                                                 font=('Arial', 8), foreground="gray")
                    general_placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                    self.quick_access_buttons.append(general_placeholder)
                    row += 1
                
                # Releases subsection
                if hasattr(self, 'engineering_releases_docs') and self.engineering_releases_docs:
                    releases_label = ttk.Label(self.access_frame, text="Releases", font=('Arial', 9, 'bold'), foreground="darkgreen")
                    releases_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                    self.quick_access_buttons.append(releases_label)
                    row += 1
                    
                    for file_path in self.engineering_releases_docs:
                        filename = os.path.basename(file_path)
                        button_text = self.create_short_button_text("📄", filename)
                        button = ttk.Button(self.access_frame, text=button_text, 
                                          command=lambda path=file_path: self.open_engineering_doc(path))
                        button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(button)
                        row += 1
                else:
                    # No Releases files - show placeholder
                    releases_placeholder = ttk.Label(self.access_frame, text="Releases: NOT PROCESSED", 
                                                   font=('Arial', 8), foreground="gray")
                    releases_placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                    self.quick_access_buttons.append(releases_placeholder)
                    row += 1
            else:
                # No engineering files found at all - show main placeholder
                engineering_placeholder = ttk.Label(self.access_frame, text="ENGINEERING: NOT PROCESSED", 
                                                 font=('Arial', 9), foreground="gray")
                engineering_placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                self.quick_access_buttons.append(engineering_placeholder)
                row += 1
        
        # Drafting documents section - always show if job directory is loaded
        if hasattr(self, 'job_directory_picker') and self.job_directory_picker.get():
            # Add DRAFTING divider
            drafting_label = ttk.Label(self.access_frame, text="DRAFTING", font=('Arial', 10, 'bold'), foreground="purple")
            drafting_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(10, 5))
            self.quick_access_buttons.append(drafting_label)
            row += 1
            
            # Check for Systems folder
            job_dir = self.job_directory_picker.get()
            systems_dir = os.path.join(job_dir, "4. Drafting", "Systems")
            
            if os.path.exists(systems_dir) and os.path.isdir(systems_dir):
                # Systems subsection
                systems_label = ttk.Label(self.access_frame, text="Systems", font=('Arial', 9, 'bold'), foreground="darkviolet")
                systems_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                self.quick_access_buttons.append(systems_label)
                row += 1
                
                # Scan for .dwg files
                dwg_files = []
                try:
                    for file in os.listdir(systems_dir):
                        if file.lower().endswith('.dwg'):
                            dwg_files.append(os.path.join(systems_dir, file))
                except Exception as e:
                    print(f"Error scanning drafting systems directory: {e}")
                
                if dwg_files:
                    # Sort by name
                    dwg_files.sort(key=lambda x: os.path.basename(x).lower())
                    
                    for file_path in dwg_files:
                        filename = os.path.basename(file_path)
                        button_text = self.create_short_button_text("📐", filename)
                        button = ttk.Button(self.access_frame, text=button_text, 
                                          command=lambda path=file_path: self.open_drafting_doc(path))
                        button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(button)
                        row += 1
                else:
                    # No .dwg files found
                    placeholder = ttk.Label(self.access_frame, text="Systems: No DWG files found", 
                                         font=('Arial', 8), foreground="gray")
                    placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                    self.quick_access_buttons.append(placeholder)
                    row += 1
                
                # Package subsection
                package_dir = os.path.join(job_dir, "4. Drafting", "Package")
                if os.path.exists(package_dir) and os.path.isdir(package_dir):
                    package_label = ttk.Label(self.access_frame, text="Package", font=('Arial', 9, 'bold'), foreground="darkviolet")
                    package_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                    self.quick_access_buttons.append(package_label)
                    row += 1
                    
                    # Scan for .dwf and .dwg files
                    package_files = []
                    try:
                        for file in os.listdir(package_dir):
                            if file.lower().endswith(('.dwf', '.dwg')):
                                package_files.append(os.path.join(package_dir, file))
                    except Exception as e:
                        print(f"Error scanning drafting package directory: {e}")
                    
                    if package_files:
                        # Sort by name
                        package_files.sort(key=lambda x: os.path.basename(x).lower())
                        
                        for file_path in package_files:
                            filename = os.path.basename(file_path)
                            # Use different icon for .dwf vs .dwg
                            icon = "📦" if filename.lower().endswith('.dwf') else "📐"
                            button_text = self.create_short_button_text(icon, filename)
                            button = ttk.Button(self.access_frame, text=button_text, 
                                              command=lambda path=file_path: self.open_drafting_doc(path))
                            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                            self.quick_access_buttons.append(button)
                            row += 1
                    else:
                        # No package files found
                        placeholder = ttk.Label(self.access_frame, text="Package: No files found", 
                                             font=('Arial', 8), foreground="gray")
                        placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(placeholder)
                        row += 1
                
                # Fabs subsection
                fabs_dir = os.path.join(job_dir, "4. Drafting", "Fabs")
                if os.path.exists(fabs_dir) and os.path.isdir(fabs_dir):
                    fabs_label = ttk.Label(self.access_frame, text="Fabs", font=('Arial', 9, 'bold'), foreground="darkviolet")
                    fabs_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                    self.quick_access_buttons.append(fabs_label)
                    row += 1
                    
                    # Get customer and location info from job_dir path
                    # Parse: F:\Customer\Location\JobNum\4. Drafting\Fabs
                    # to get: C:\$WorkingFolder\Jobs F\Customer\Location\JobNum\4. Drafting\Fabs
                    customer_name = self.customer_name_var.get()
                    customer_location = self.customer_location_var.get()
                    job_number = self.job_number_var.get()
                    
                    # Build working folder path
                    working_fabs_dir = None
                    if customer_name and customer_location and job_number:
                        working_fabs_dir = os.path.join(r"C:\$WorkingFolder\Jobs F", 
                                                       customer_name, customer_location, 
                                                       job_number, "4. Drafting", "Fabs")
                    
                    # Scan for files in specific order: .dwf (for .idw lookup), then .dwg, then excel files
                    idw_files = []  # Changed from dwf_files
                    dwg_files = []
                    excel_files = []
                    
                    try:
                        for file in os.listdir(fabs_dir):
                            file_lower = file.lower()
                            file_path = os.path.join(fabs_dir, file)
                            
                            if file_lower.endswith('.dwf'):
                                # For .dwf files, look for corresponding .idw in working folder
                                base_name = os.path.splitext(file)[0]
                                idw_name = base_name + '.idw'
                                
                                if working_fabs_dir and os.path.exists(working_fabs_dir):
                                    idw_path = os.path.join(working_fabs_dir, idw_name)
                                    if os.path.exists(idw_path):
                                        idw_files.append((file, idw_path))  # Store display name and actual path
                                    else:
                                        # .idw not found, still add but will open .dwf
                                        idw_files.append((file, file_path))
                                else:
                                    # Working folder not available, use .dwf
                                    idw_files.append((file, file_path))
                            elif file_lower.endswith('.dwg'):
                                dwg_files.append(file_path)
                            elif file_lower.endswith(('.xls', '.xlsx', '.xlsm')):
                                excel_files.append(file_path)
                    except Exception as e:
                        print(f"Error scanning drafting fabs directory: {e}")
                    
                    # Sort each category
                    idw_files.sort(key=lambda x: x[0].lower())  # Sort by display name
                    dwg_files.sort(key=lambda x: os.path.basename(x).lower())
                    excel_files.sort(key=lambda x: os.path.basename(x).lower())
                    
                    # Display .idw files first
                    if idw_files:
                        for display_name, actual_path in idw_files:
                            # Show .idw in the button text if it's actually an .idw file
                            if actual_path.lower().endswith('.idw'):
                                button_filename = os.path.splitext(display_name)[0] + '.idw'
                                icon = "🔧"  # Inventor icon
                            else:
                                button_filename = display_name
                                icon = "📦"  # .dwf fallback
                            
                            button_text = self.create_short_button_text(icon, button_filename)
                            button = ttk.Button(self.access_frame, text=button_text, 
                                              command=lambda path=actual_path: self.open_drafting_doc(path))
                            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                            self.quick_access_buttons.append(button)
                            row += 1
                    
                    # Then .dwg files
                    if dwg_files:
                        for file_path in dwg_files:
                            filename = os.path.basename(file_path)
                            button_text = self.create_short_button_text("📐", filename)
                            button = ttk.Button(self.access_frame, text=button_text, 
                                              command=lambda path=file_path: self.open_drafting_doc(path))
                            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                            self.quick_access_buttons.append(button)
                            row += 1
                    
                    # Check for D365 Import file
                    has_d365_import = False
                    if excel_files:
                        for file_path in excel_files:
                            filename = os.path.basename(file_path).upper()
                            if "D365 IMPORT" in filename:
                                has_d365_import = True
                                break
                    
                    # Show "NEW D365 Import" button if file doesn't exist
                    if not has_d365_import:
                        new_d365_btn = tk.Button(self.access_frame, text="📊 NEW D365 Import", 
                                                bg='#28a745', fg='white',
                                                font=('Arial', 9, 'bold'),
                                                relief='raised', bd=2, cursor='hand2',
                                                activebackground='#218838', activeforeground='white',
                                                command=lambda: self.create_d365_import(fabs_dir))
                        new_d365_btn.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(new_d365_btn)
                        row += 1
                    
                    # Check for Transmittal Notice DWG file
                    has_transmittal = False
                    if dwg_files:
                        for file_path in dwg_files:
                            filename = os.path.basename(file_path).upper()
                            if "TRANSMITTAL NOTICE" in filename or "TRANMITTAL NOTICE" in filename:
                                has_transmittal = True
                                break
                    
                    # Show "NEW Transmittal Notice" button if file doesn't exist
                    if not has_transmittal:
                        new_transmittal_btn = tk.Button(self.access_frame, text="📐 NEW Transmittal Notice", 
                                                bg='#28a745', fg='white',
                                                font=('Arial', 9, 'bold'),
                                                relief='raised', bd=2, cursor='hand2',
                                                activebackground='#218838', activeforeground='white',
                                                command=lambda: self.create_transmittal_notice(fabs_dir))
                        new_transmittal_btn.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(new_transmittal_btn)
                        row += 1
                    
                    # Display Excel files
                    if excel_files:
                        for file_path in excel_files:
                            filename = os.path.basename(file_path)
                            button_text = self.create_short_button_text("📊", filename)
                            button = ttk.Button(self.access_frame, text=button_text, 
                                              command=lambda path=file_path: self.open_drafting_doc(path))
                            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                            self.quick_access_buttons.append(button)
                            row += 1
                    
                    if not idw_files and not dwg_files and not excel_files:
                        # No fabs files found
                        placeholder = ttk.Label(self.access_frame, text="Fabs: No files found", 
                                             font=('Arial', 8), foreground="gray")
                        placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(placeholder)
                        row += 1
                
                # Burn Table Files subsection
                burn_dir = os.path.join(job_dir, "4. Drafting", "Burn Table Files")
                if os.path.exists(burn_dir) and os.path.isdir(burn_dir):
                    burn_label = ttk.Label(self.access_frame, text="Burn Table Files", font=('Arial', 9, 'bold'), foreground="darkviolet")
                    burn_label.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(5, 2))
                    self.quick_access_buttons.append(burn_label)
                    row += 1
                    
                    # Scan for .dwg files only
                    burn_files = []
                    try:
                        for file in os.listdir(burn_dir):
                            if file.lower().endswith('.dwg'):
                                burn_files.append(os.path.join(burn_dir, file))
                    except Exception as e:
                        print(f"Error scanning burn table files directory: {e}")
                    
                    if burn_files:
                        # Sort by name
                        burn_files.sort(key=lambda x: os.path.basename(x).lower())
                        
                        for file_path in burn_files:
                            filename = os.path.basename(file_path)
                            button_text = self.create_short_button_text("🔥", filename)
                            button = ttk.Button(self.access_frame, text=button_text, 
                                              command=lambda path=file_path: self.open_drafting_doc(path))
                            button.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                            self.quick_access_buttons.append(button)
                            row += 1
                    else:
                        # No burn table files found
                        placeholder = ttk.Label(self.access_frame, text="Burn Table Files: No DWG files found", 
                                             font=('Arial', 8), foreground="gray")
                        placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                        self.quick_access_buttons.append(placeholder)
                        row += 1
            else:
                # Systems folder doesn't exist
                placeholder = ttk.Label(self.access_frame, text="DRAFTING: NOT PROCESSED", 
                                     font=('Arial', 9), foreground="gray")
                placeholder.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
                self.quick_access_buttons.append(placeholder)
                row += 1
        
        # If no quick access items, show a message
        if not self.quick_access_buttons:
            label = ttk.Label(self.access_frame, text="No quick access items\navailable for this project", 
                            foreground="gray", justify="center")
            label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=20)
            self.quick_access_buttons.append(label)
        
        # Update scroll region after all buttons are added
        if hasattr(self, 'quick_access_canvas'):
            self.access_frame.update_idletasks()
            self.quick_access_canvas.configure(scrollregion=self.quick_access_canvas.bbox("all"))
    
    def create_action_buttons(self):
        """Create compact footer toolbar with uniform buttons"""
        # Separator line above footer
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Footer toolbar frame - pinned to bottom
        footer_frame = tk.Frame(self.root, bg='#f5f5f5', relief='flat', bd=0, height=45)
        footer_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        footer_frame.grid_propagate(False)
        
        # Inner container for buttons
        button_container = tk.Frame(footer_frame, bg='#f5f5f5')
        button_container.pack(side=tk.LEFT, padx=10, pady=6)
        
        # Dashboard button with accent style
        dashboard_btn = tk.Button(button_container, text="🏠 Dashboard", 
                                  command=self.open_dashboard,
                                  width=12, height=1,
                                  bg='#2196F3', fg='white',
                                  font=('Arial', 9),
                                  relief='raised', bd=1, cursor='hand2',
                                  activebackground='#1976D2', activeforeground='white')
        dashboard_btn.pack(side=tk.LEFT, padx=(0, 10))
        self._add_button_hover_effect(dashboard_btn, '#2196F3', '#1976D2')
        
        # All other buttons with consistent styling
        buttons = [
            ("New Project", self.new_project),
            ("Save Project", self.save_project),
            ("Delete Project", self.delete_project),
            ("Clean & Fix Data", self.clean_duplicates),
            ("Reset Database", self.reset_database),
            ("Refresh", self.load_projects),
            ("Export JSON", self.export_data),
            ("Import JSON", self.import_data)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_container, text=text, command=command,
                          width=12, height=1,
                          bg='#ffffff', fg='#333333',
                          font=('Arial', 9),
                          relief='raised', bd=1, cursor='hand2',
                          activebackground='#E3F2FD', activeforeground='#1976D2')
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self._add_button_hover_effect(btn, '#ffffff', '#E3F2FD')
    
    def _add_button_hover_effect(self, button, normal_bg, hover_bg):
        """Add subtle hover effect to a button"""
        def on_enter(e):
            button.config(bg=hover_bg)
        
        def on_leave(e):
            button.config(bg=normal_bg)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
    
    def open_job_directory(self):
        """Open the job directory"""
        directory = self.job_directory_picker.get()
        if directory and os.path.exists(directory):
            self.open_path(directory)
        else:
            messagebox.showwarning("Warning", "No valid job directory selected!")
    
    def open_customer_name_path(self, path):
        """Open customer name path (from directory picker or text field)"""
        print(f"DEBUG: Opening customer name path: '{path}'")
        if path and os.path.exists(path):
            print(f"DEBUG: Opening direct path: {path}")
            self.open_path(path)
        elif path:
            print(f"DEBUG: Path doesn't exist, searching for folder: {path}")
            self.search_and_open_folder(path)
        else:
            print("DEBUG: No customer name path provided")
            messagebox.showwarning("Warning", "No customer name path provided!")
    
    def open_customer_location_path(self, path):
        """Open customer location path (from directory picker or text field)"""
        print(f"DEBUG: Opening customer location path: '{path}'")
        if path and os.path.exists(path):
            print(f"DEBUG: Opening direct path: {path}")
            self.open_path(path)
        elif path:
            print(f"DEBUG: Path doesn't exist, searching for folder: {path}")
            self.search_and_open_folder(path)
        else:
            print("DEBUG: No customer location path provided")
            messagebox.showwarning("Warning", "No customer location path provided!")
    
    def open_customer_name(self):
        """Open customer name path (legacy method)"""
        customer_name = self.customer_name_var.get()
        print(f"DEBUG: Customer name = '{customer_name}'")
        if customer_name:
            if os.path.exists(customer_name):
                print(f"DEBUG: Opening direct path: {customer_name}")
                self.open_path(customer_name)
            else:
                print(f"DEBUG: Searching for folder: {customer_name}")
                self.search_and_open_folder(customer_name)
        else:
            print("DEBUG: No customer name entered")
            messagebox.showwarning("Warning", "No customer name entered!")
    
    def open_customer_location(self):
        """Open customer location path (legacy method)"""
        customer_location = self.customer_location_var.get()
        print(f"DEBUG: Customer location = '{customer_location}'")
        if customer_location:
            if os.path.exists(customer_location):
                print(f"DEBUG: Opening direct path: {customer_location}")
                self.open_path(customer_location)
            else:
                print(f"DEBUG: Searching for folder: {customer_location}")
                self.search_and_open_folder(customer_location)
        else:
            print("DEBUG: No customer location entered")
            messagebox.showwarning("Warning", "No customer location entered!")
    
    def open_path(self, path):
        """Open a file or directory path"""
        try:
            # Mark acknowledged for this file so the orange state clears
            try:
                job_num = str(self.job_number_var.get()).strip()
                conn = sqlite3.connect(self.db_manager.db_path)
                cur = conn.cursor()
                cur.execute("UPDATE file_timestamps SET acknowledged=1 WHERE job_number=? AND path=?", (job_num, path))
                conn.commit(); conn.close()
            except Exception:
                pass
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
            # Refresh to update button styles
            self.update_quick_access()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open path: {str(e)}")
    
    def search_and_open_folder(self, name):
        """Search for and open a folder by name"""
        print(f"DEBUG: Searching for folder: '{name}'")
        
        # Common search locations
        search_paths = [
            os.path.join(os.path.expanduser("~"), "Documents", "Projects", name),
            os.path.join(os.path.expanduser("~"), "Desktop", name),
            os.path.join("C:", "Projects", name),
            os.path.join("C:", "Users", os.getenv("USERNAME", ""), "Documents", name),
            os.path.join(os.path.expanduser("~"), "Documents", name),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", name),
            os.path.join("C:", "Users", os.getenv("USERNAME", ""), "OneDrive", "Documents", name),
            os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", name),
            os.path.join("C:", "Users", os.getenv("USERNAME", ""), "OneDrive", "Desktop", name)
        ]
        
        print(f"DEBUG: Checking {len(search_paths)} search paths...")
        for i, path in enumerate(search_paths):
            print(f"DEBUG: Checking path {i+1}: {path}")
            if os.path.exists(path):
                print(f"DEBUG: Found folder at: {path}")
                self.open_path(path)
                return
        
        # If not found, try to create a folder and open it
        print(f"DEBUG: Folder not found, creating new folder...")
        new_folder = os.path.join(os.path.expanduser("~"), "Documents", "Projects", name)
        try:
            os.makedirs(new_folder, exist_ok=True)
            print(f"DEBUG: Created new folder: {new_folder}")
            self.open_path(new_folder)
        except Exception as e:
            print(f"DEBUG: Failed to create folder: {e}")
            messagebox.showinfo("Info", f"Folder for '{name}' not found. Please create it manually or use the directory picker to select an existing folder.")
    
    def clean_duplicates(self):
        """Remove duplicate projects and clean job numbers"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            print("DEBUG: Starting database cleanup...")
            
            # First, get all projects
            cursor.execute("SELECT id, job_number FROM projects")
            projects = cursor.fetchall()
            print(f"DEBUG: Found {len(projects)} projects to check")
            
            cleaned_count = 0
            for project_id, job_number in projects:
                original = str(job_number)
                print(f"DEBUG: Processing project {project_id}: '{original}'")
                
                # Clean the job number
                clean_job_number = str(job_number).strip()
                if ' ' in clean_job_number:
                    # Extract just the numeric part
                    parts = clean_job_number.split()
                    for part in parts:
                        if part.isdigit() and len(part) == 5:
                            clean_job_number = part
                            break
                
                print(f"DEBUG: Cleaned '{original}' to '{clean_job_number}'")
                
                # Update if different
                if clean_job_number != original:
                    print(f"DEBUG: Updating project {project_id} from '{original}' to '{clean_job_number}'")
                    cursor.execute("UPDATE projects SET job_number = ? WHERE id = ?", 
                                 (clean_job_number, project_id))
                    cleaned_count += 1
                else:
                    print(f"DEBUG: No change needed for project {project_id}")
            
            print(f"DEBUG: Updated {cleaned_count} job numbers")
            
            # Find duplicates after cleaning
            cursor.execute("""
                SELECT job_number, COUNT(*) as count
                FROM projects 
                GROUP BY job_number 
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            print(f"DEBUG: Found {len(duplicates)} duplicate groups")
            
            duplicate_count = 0
            if duplicates:
                # Remove duplicates, keeping the one with the highest ID (most recent)
                for job_number, count in duplicates:
                    print(f"DEBUG: Removing {count-1} duplicates for job {job_number}")
                    cursor.execute("""
                        DELETE FROM projects 
                        WHERE job_number = ? AND id NOT IN (
                            SELECT MAX(id) FROM projects WHERE job_number = ?
                        )
                    """, (job_number, job_number))
                    duplicate_count += count - 1
            
            conn.commit()
            print(f"DEBUG: Cleanup complete - {cleaned_count} cleaned, {duplicate_count} duplicates removed")
            messagebox.showinfo("Success", f"Cleaned {cleaned_count} job numbers and removed {duplicate_count} duplicate project(s)!")
            self.load_projects()
            
        except Exception as e:
            print(f"DEBUG: Error during cleanup: {e}")
            messagebox.showerror("Error", f"Failed to clean duplicates: {str(e)}")
        finally:
            conn.close()
    
    def reset_database(self):
        """Reset the database by recreating it"""
        if messagebox.askyesno("Confirm Reset", 
                              "Are you sure you want to reset the database? This will delete ALL data!"):
            try:
                # Close current connection
                if hasattr(self, 'db_manager'):
                    self.db_manager.close()
                
                # Delete the database file
                import os
                if os.path.exists(self.db_manager.db_path):
                    os.remove(self.db_manager.db_path)
                    print(f"DEBUG: Deleted database file: {self.db_manager.db_path}")
                
                # Recreate the database
                self.db_manager = DatabaseManager()
                print("DEBUG: Recreated database")
                
                # Reload projects (will be empty)
                self.load_projects()
                self.new_project()
                
                messagebox.showinfo("Success", "Database reset successfully!")
                
            except Exception as e:
                print(f"DEBUG: Error resetting database: {e}")
                messagebox.showerror("Error", f"Failed to reset database: {str(e)}")
    
    def auto_extract_and_save(self, *args):
        """Auto-extract customer info from job directory and save"""
        job_dir = self.job_directory_picker.get()
        if job_dir and os.path.exists(job_dir):
            self.extract_customer_info_from_path(job_dir)
        
        # Also auto-save
        self.auto_save()
    
    def extract_customer_info_from_path(self, job_dir):
        """Extract customer name and location from job directory path"""
        try:
            # Normalize the path and split into parts
            normalized_path = os.path.normpath(job_dir)
            path_parts = normalized_path.split(os.sep)
            
            print(f"DEBUG: Extracting from path: {normalized_path}")
            print(f"DEBUG: Path parts: {path_parts}")
            
            # Find the job number (should be the last part)
            job_number = path_parts[-1] if path_parts else ""
            
            # Customer location is one level up from job number
            customer_location = path_parts[-2] if len(path_parts) >= 2 else ""
            
            # Customer name is two levels up from job number
            customer_name = path_parts[-3] if len(path_parts) >= 3 else ""
            
            print(f"DEBUG: Extracted - Job: {job_number}, Location: {customer_location}, Name: {customer_name}")
            
            # Set the extracted values
            if customer_name:
                self.customer_name_var.set(customer_name.upper())
                self.customer_name_picker.set(os.path.dirname(os.path.dirname(job_dir)))
            
            if customer_location:
                self.customer_location_var.set(customer_location.upper())
                self.customer_location_picker.set(os.path.dirname(job_dir))
            
            # Automatically find and add KOM AND OC FORM Excel file
            self.find_and_add_kom_oc_form(job_dir)
            
            # Automatically find and add Proposal Word documents
            self.find_and_add_proposal_docs(job_dir)
            
            # Automatically find and add other important files
            self.find_and_add_other_docs(job_dir)
            
            # Automatically find and add engineering files
            self.find_and_add_engineering_docs(job_dir)
            
            # Update quick access panel
            self.update_quick_access()
            
        except Exception as e:
            print(f"DEBUG: Error extracting customer info: {e}")
    
    def find_and_add_kom_oc_form(self, job_dir):
        """Find and add KOM AND OC FORM Excel file to quick access"""
        try:
            print(f"DEBUG: Looking for KOM AND OC FORM file in: {job_dir}")
            
            # Get job number from the directory path
            job_number = os.path.basename(job_dir)
            
            # Look for Excel files with "KOM AND OC FORM" in the filename
            for file in os.listdir(job_dir):
                if file.endswith('.xlsx') and 'KOM AND OC FORM' in file.upper():
                    kom_file_path = os.path.join(job_dir, file)
                    print(f"DEBUG: Found KOM AND OC FORM file: {kom_file_path}")
                    
                    # Store the file path for quick access
                    self.kom_oc_form_path = kom_file_path
                    return
            
            print(f"DEBUG: No KOM AND OC FORM file found in {job_dir}")
            self.kom_oc_form_path = None
            
        except Exception as e:
            print(f"DEBUG: Error finding KOM AND OC FORM file: {e}")
            self.kom_oc_form_path = None
    
    def open_kom_oc_form(self):
        """Open the KOM AND OC FORM Excel file"""
        if hasattr(self, 'kom_oc_form_path') and self.kom_oc_form_path and os.path.exists(self.kom_oc_form_path):
            print(f"DEBUG: Opening KOM AND OC FORM file: {self.kom_oc_form_path}")
            self.open_path(self.kom_oc_form_path)
        else:
            messagebox.showwarning("Warning", "KOM AND OC FORM file not found!")
    
    def find_and_add_proposal_docs(self, job_dir):
        """Find and add Proposal Word documents from 1. Sales\\Order folder"""
        try:
            print(f"DEBUG: Looking for Proposal documents in: {job_dir}")
            
            # Look for 1. Sales\Order folder
            sales_order_path = os.path.join(job_dir, "1. Sales", "Order")
            
            if not os.path.exists(sales_order_path):
                print(f"DEBUG: Sales\\Order folder not found: {sales_order_path}")
                self.proposal_docs = []
                return
            
            print(f"DEBUG: Found Sales\\Order folder: {sales_order_path}")
            
            # Look for Word documents with "Proposal" in the filename
            proposal_files = []
            print(f"DEBUG: Listing all files in {sales_order_path}:")
            for file in os.listdir(sales_order_path):
                print(f"DEBUG: Found file: '{file}'")
                if (file.endswith('.docx') or file.endswith('.doc')):
                    print(f"DEBUG: File is Word document: {file}")
                    if 'Proposal' in file.upper():
                        proposal_file_path = os.path.join(sales_order_path, file)
                        proposal_files.append(proposal_file_path)
                        print(f"DEBUG: Found Proposal document: {proposal_file_path}")
                    else:
                        print(f"DEBUG: File does not contain 'Proposal': {file}")
                else:
                    print(f"DEBUG: File is not Word document: {file}")
            
            # Store the proposal files for quick access
            self.proposal_docs = proposal_files
            print(f"DEBUG: Found {len(proposal_files)} Proposal documents")
            
        except Exception as e:
            print(f"DEBUG: Error finding Proposal documents: {e}")
            self.proposal_docs = []
    
    def open_proposal_doc(self, doc_path):
        """Open a specific Proposal Word document"""
        if doc_path and os.path.exists(doc_path):
            print(f"DEBUG: Opening Proposal document: {doc_path}")
            self.open_path(doc_path)
        else:
            messagebox.showwarning("Warning", "Proposal document not found!")
    
    def find_and_add_other_docs(self, job_dir):
        """Find and add other important files from 1. Sales\\Order folder"""
        try:
            print(f"DEBUG: Looking for other important files in: {job_dir}")
            
            # Look for 1. Sales\Order folder
            sales_order_path = os.path.join(job_dir, "1. Sales", "Order")
            
            if not os.path.exists(sales_order_path):
                print(f"DEBUG: Sales\\Order folder not found: {sales_order_path}")
                self.other_docs = []
                return
            
            print(f"DEBUG: Found Sales\\Order folder: {sales_order_path}")
            
            # Look for other important files
            other_files = []
            print(f"DEBUG: Listing all files in {sales_order_path}:")
            for file in os.listdir(sales_order_path):
                print(f"DEBUG: Found file: '{file}'")
                file_path = os.path.join(sales_order_path, file)
                
                # Check for Excel files with "Cost" or "Template" in filename
                if (file.endswith('.xlsx') or file.endswith('.xls')) and ('Cost' in file.upper() or 'Template' in file.upper()):
                    other_files.append(('📊', file, file_path))
                    print(f"DEBUG: Found Cost/Template Excel file: {file}")
                
                # Check for PDF files
                elif file.endswith('.pdf'):
                    other_files.append(('📄', file, file_path))
                    print(f"DEBUG: Found PDF file: {file}")
                
                # Check for any other Word documents (not already captured as proposals)
                elif (file.endswith('.docx') or file.endswith('.doc')) and 'Proposal' not in file.upper():
                    # Double-check that this file wasn't already captured as a proposal
                    is_proposal = False
                    if hasattr(self, 'proposal_docs') and self.proposal_docs:
                        for proposal_path in self.proposal_docs:
                            if os.path.basename(proposal_path) == file:
                                is_proposal = True
                                break
                    
                    if not is_proposal:
                        other_files.append(('📄', file, file_path))
                        print(f"DEBUG: Found other Word document: {file}")
                    else:
                        print(f"DEBUG: Skipping {file} - already captured as proposal")
            
            # Store the other files for quick access
            self.other_docs = other_files
            print(f"DEBUG: Found {len(other_files)} other important files")
            
        except Exception as e:
            print(f"DEBUG: Error finding other files: {e}")
            self.other_docs = []
    
    def open_other_doc(self, doc_path):
        """Open a specific other document"""
        if doc_path and os.path.exists(doc_path):
            print(f"DEBUG: Opening document: {doc_path}")
            self.open_path(doc_path)
        else:
            messagebox.showwarning("Warning", "Document not found!")
    
    def find_and_add_engineering_docs(self, job_dir):
        """Find and add engineering documents from 3. Engineering folders"""
        try:
            print(f"DEBUG: Looking for engineering documents in: {job_dir}")
            
            # Look for 3. Engineering folder
            engineering_path = os.path.join(job_dir, "3. Engineering")
            
            if not os.path.exists(engineering_path):
                print(f"DEBUG: Engineering folder not found: {engineering_path}")
                self.engineering_general_docs = []
                self.engineering_releases_docs = []
                return
            
            print(f"DEBUG: Found Engineering folder: {engineering_path}")
            
            # Find General Design files
            general_design_path = os.path.join(engineering_path, "General Design")
            self.engineering_general_docs = []
            
            if os.path.exists(general_design_path):
                print(f"DEBUG: Found General Design folder: {general_design_path}")
                for file in os.listdir(general_design_path):
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        file_path = os.path.join(general_design_path, file)
                        self.engineering_general_docs.append(file_path)
                        print(f"DEBUG: Found General Design file: {file}")
            
            # Find Releases files
            releases_path = os.path.join(engineering_path, "Releases")
            self.engineering_releases_docs = []
            
            if os.path.exists(releases_path):
                print(f"DEBUG: Found Releases folder: {releases_path}")
                for file in os.listdir(releases_path):
                    file_path = os.path.join(releases_path, file)
                    self.engineering_releases_docs.append(file_path)
                    print(f"DEBUG: Found Releases file: {file}")
            
            print(f"DEBUG: Found {len(self.engineering_general_docs)} General Design files")
            print(f"DEBUG: Found {len(self.engineering_releases_docs)} Releases files")
            
        except Exception as e:
            print(f"DEBUG: Error finding engineering documents: {e}")
            self.engineering_general_docs = []
            self.engineering_releases_docs = []
    
    def open_engineering_doc(self, doc_path):
        """Open a specific engineering document"""
        if doc_path and os.path.exists(doc_path):
            print(f"DEBUG: Opening engineering document: {doc_path}")
            self.open_path(doc_path)
        else:
            messagebox.showwarning("Warning", "Engineering document not found!")
    
    def open_drafting_doc(self, doc_path):
        """Open a specific drafting document (.dwg file)"""
        if doc_path and os.path.exists(doc_path):
            print(f"DEBUG: Opening drafting document: {doc_path}")
            self.open_path(doc_path)
        else:
            messagebox.showwarning("Warning", "Drafting document not found!")
    
    def create_d365_import(self, fabs_dir):
        """Create a new D365 Import file by copying the Excel file and renaming it"""
        try:
            # Source Excel file (not template)
            source_file = r"C:\excel\templates\XXXXX D365 IMPORT.xlsx"
            
            print(f"DEBUG: Source file: {source_file}")
            print(f"DEBUG: Source exists: {os.path.exists(source_file)}")
            
            # Check if source file exists
            if not os.path.exists(source_file):
                messagebox.showerror("File Not Found", 
                                   f"D365 Import file not found at:\n{source_file}")
                return
            
            # Get job number
            job_number = self.job_number_var.get()
            print(f"DEBUG: Job number: {job_number}")
            
            if not job_number:
                messagebox.showerror("Error", "Job number is required to create D365 Import file.")
                return
            
            # Create new filename
            new_filename = f"{job_number} D365 IMPORT.xlsx"
            new_file_path = os.path.join(fabs_dir, new_filename)
            
            print(f"DEBUG: Target path: {new_file_path}")
            print(f"DEBUG: Target exists: {os.path.exists(new_file_path)}")
            
            # Check if file already exists
            if os.path.exists(new_file_path):
                messagebox.showinfo("File Exists", 
                                  f"D365 Import file already exists:\n{new_filename}")
                return
            
            # Copy the Excel file to the new location with new name
            print(f"DEBUG: About to copy from {source_file} to {new_file_path}")
            shutil.copy2(source_file, new_file_path)
            print(f"DEBUG: Copy completed")
            print(f"DEBUG: New file exists: {os.path.exists(new_file_path)}")
            
            # Refresh Quick Access to remove the green button and show the new file
            self.update_quick_access()
            
            messagebox.showinfo("Success", 
                              f"D365 Import file created successfully!\n\n{new_filename}\n\nThe file is ready in the Fabs folder.\nClick the file button in Quick Access to open it.")
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to create D365 Import file:\n{str(e)}")
            print(f"ERROR creating D365 Import file: {e}")
            import traceback
            traceback.print_exc()
    
    def create_transmittal_notice(self, fabs_dir):
        """Create a new Transmittal Notice DWG by copying the template and renaming it"""
        try:
            # Source DWG file
            source_file = r"C:\Users\llaing\OneDrive - CECO Environmental Corp\Drafting Standards\Release Process\Drawing Release Form (Blue).dwg"
            
            print(f"DEBUG: Source file: {source_file}")
            print(f"DEBUG: Source exists: {os.path.exists(source_file)}")
            
            # Check if source file exists
            if not os.path.exists(source_file):
                messagebox.showerror("File Not Found", 
                                   f"Transmittal Notice template not found at:\n{source_file}")
                return
            
            # Get job number
            job_number = self.job_number_var.get()
            print(f"DEBUG: Job number: {job_number}")
            
            if not job_number:
                messagebox.showerror("Error", "Job number is required to create Transmittal Notice.")
                return
            
            # Create new filename
            new_filename = f"{job_number} TRANMITTAL NOTICE.dwg"
            new_file_path = os.path.join(fabs_dir, new_filename)
            
            print(f"DEBUG: Target path: {new_file_path}")
            print(f"DEBUG: Target exists: {os.path.exists(new_file_path)}")
            
            # Check if file already exists
            if os.path.exists(new_file_path):
                messagebox.showinfo("File Exists", 
                                  f"Transmittal Notice already exists:\n{new_filename}")
                return
            
            # Copy the DWG file to the new location with new name
            print(f"DEBUG: About to copy from {source_file} to {new_file_path}")
            shutil.copy2(source_file, new_file_path)
            print(f"DEBUG: Copy completed")
            print(f"DEBUG: New file exists: {os.path.exists(new_file_path)}")
            
            # Refresh Quick Access to remove the green button and show the new file
            self.update_quick_access()
            
            messagebox.showinfo("Success", 
                              f"Transmittal Notice created successfully!\n\n{new_filename}\n\nThe file is ready in the Fabs folder.\nClick the file button in Quick Access to open it.")
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to create Transmittal Notice:\n{str(e)}")
            print(f"ERROR creating Transmittal Notice: {e}")
            import traceback
            traceback.print_exc()
    
    def create_short_button_text(self, icon, filename):
        """Create short, consistent button text for files"""
        # Remove file extension
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1].upper()
        
        # Consistent labels for specific file types
        if 'PROPOSAL' in filename.upper():
            return f"{icon} Proposal"
        elif 'ENGINEERING DESIGN' in filename.upper():
            return f"{icon} Engineering Design"
        elif 'PRESSURE DROP CALCULATOR' in filename.upper():
            return f"{icon} Pressure Drop Calculator"
        elif 'SPRAY NOZZLES' in filename.upper():
            return f"{icon} Spray Nozzles"
        elif 'ELECTRICAL RELEASE' in filename.upper():
            return f"{icon} Electrical Release{file_ext}"
        elif 'GAS TRAIN RELEASE' in filename.upper():
            return f"{icon} Gas Train Release{file_ext}"
        elif 'MECHANICAL RELEASE' in filename.upper():
            return f"{icon} Mechanical Release{file_ext}"
        elif 'HEATER RELEASE' in filename.upper():
            return f"{icon} Heater Release{file_ext}"
        elif 'TANK RELEASE' in filename.upper():
            return f"{icon} Tank Release{file_ext}"
        else:
            # For all other files, show filename (truncated if too long)
            if len(name_without_ext) > 25:
                return f"{icon} {name_without_ext[:22]}..."
            else:
                return f"{icon} {name_without_ext}"
    
    def auto_save(self, *args):
        """Auto-save project when any field changes"""
        # Don't auto-save while loading project details
        if hasattr(self, '_loading_project') and self._loading_project:
            return
            
        # Only auto-save if we have a valid 5-digit job number
        job_number = self.job_number_var.get().strip()
        if self.is_valid_job_number(job_number):
            try:
                self.save_project_silent()
                # Update cover sheet button after saving
                self.update_cover_sheet_button()
            except Exception as e:
                print(f"Auto-save failed: {e}")
    
    def is_valid_job_number(self, job_number):
        """Validate that job number is exactly 5 digits"""
        if not job_number:
            return False
        # Remove any whitespace and check if it's exactly 5 digits
        clean_number = job_number.strip()
        return clean_number.isdigit() and len(clean_number) == 5
    
    def save_project_silent(self):
        """Save project without showing success message"""
        job_number = self.job_number_var.get().strip()
        if not self.is_valid_job_number(job_number):
            return
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            # Get designer ID
            designer_id = None
            if self.assigned_to_var.get():
                cursor.execute("SELECT id FROM designers WHERE name = ?", (self.assigned_to_var.get(),))
                result = cursor.fetchone()
                if result:
                    designer_id = result[0]
            
            # Get project engineer ID
            project_engineer_id = None
            if self.project_engineer_var.get():
                cursor.execute("SELECT id FROM engineers WHERE name = ?", (self.project_engineer_var.get(),))
                result = cursor.fetchone()
                if result:
                    project_engineer_id = result[0]
            
            # Calculate duration
            duration = None
            if self.start_date_entry.get() and self.completion_date_entry.get():
                try:
                    start = datetime.strptime(self.start_date_entry.get(), "%Y-%m-%d")
                    end = datetime.strptime(self.completion_date_entry.get(), "%Y-%m-%d")
                    duration = (end - start).days
                except ValueError:
                    pass
            
            # Insert or update project
            cursor.execute("""
                INSERT OR REPLACE INTO projects 
                (job_number, job_directory, customer_name, customer_name_directory, 
                 customer_location, customer_location_directory, assigned_to_id, project_engineer_id,
                 assignment_date, start_date, completion_date, 
                 total_duration_days, released_to_dee, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_number,
                self.job_directory_picker.get() or None,
                self.customer_name_var.get().upper() or None,
                self.customer_name_picker.get() or None,
                self.customer_location_var.get().upper() or None,
                self.customer_location_picker.get() or None,
                designer_id,
                project_engineer_id,
                self.assignment_date_entry.get() or None,
                self.start_date_entry.get() or None,
                self.completion_date_entry.get() or None,
                duration,
                self.released_to_dee_entry.get() or None,
                self.due_date_entry.get() or None
            ))
            
            # Get project ID
            cursor.execute("SELECT id FROM projects WHERE job_number = ?", (job_number,))
            project_id = cursor.fetchone()[0]
            
            # Save workflow data
            self.save_workflow_data(cursor, project_id)
            
            conn.commit()
            
        except Exception as e:
            print(f"Silent save failed: {e}")
        finally:
            conn.close()
    
    def load_dropdown_data(self):
        """Load data for dropdown menus"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Load designers
        cursor.execute("SELECT name FROM designers ORDER BY name")
        designers = [row[0] for row in cursor.fetchall()]
        if hasattr(self, 'assigned_to_combo'):
            self.assigned_to_combo['values'] = designers
        
        # Load engineers
        cursor.execute("SELECT name FROM engineers ORDER BY name")
        engineers = [row[0] for row in cursor.fetchall()]
        if hasattr(self, 'initial_engineer_combo'):
            self.initial_engineer_combo['values'] = engineers
        
        # Set engineers for project engineer combo
        if hasattr(self, 'project_engineer_combo'):
            self.project_engineer_combo['values'] = engineers
        
        # Set engineers for all redline update combos
        for i in range(1, 5):
            combo_name = f"redline_update_{i}_engineer_combo"
            if hasattr(self, combo_name):
                getattr(self, combo_name)['values'] = engineers
        
        conn.close()
    
    def load_projects(self):
        """Load projects from database"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT p.job_number, p.customer_name, p.due_date, p.completion_date,
               CASE 
                   WHEN p.completion_date IS NOT NULL AND p.completion_date != '' THEN 'Completed'
                   WHEN p.start_date IS NOT NULL AND p.start_date != '' THEN 'In Progress'
                   WHEN p.assignment_date IS NOT NULL AND p.assignment_date != '' THEN 'Assigned'
                   ELSE 'Not Assigned'
               END as status
        FROM projects p
        ORDER BY 
            CASE WHEN p.due_date IS NULL OR p.due_date = '' THEN 1 ELSE 0 END,
            p.due_date ASC
        """
        
        cursor.execute(query)
        projects = cursor.fetchall()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert projects
        for project in projects:
            job_number = project[0]
            customer_name = project[1]
            due_date = project[2] if project[2] else ""
            completion_date = project[3]
            status = project[4]
            
            # Calculate days until due
            days_until_due = ""
            if due_date and not completion_date:
                try:
                    due = datetime.strptime(due_date, "%Y-%m-%d")
                    today = datetime.now()
                    days_diff = (due - today).days
                    
                    if days_diff < 0:
                        days_until_due = f"{abs(days_diff)} overdue"
                    elif days_diff == 0:
                        days_until_due = "Today"
                    else:
                        days_until_due = str(days_diff)
                except:
                    days_until_due = ""
            
            self.tree.insert('', 'end', values=(
                job_number,
                customer_name,
                due_date,
                days_until_due,
                status
            ))
        
        conn.close()
    
    def filter_projects(self, *args):
        """Filter projects based on search term"""
        search_term = self.search_var.get().lower()
        
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if any(search_term in str(value).lower() for value in values):
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)
    
    def sort_by_job_number(self):
        """Sort projects by job number (toggle ascending/descending)"""
        # Get all current items and their values
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            items.append(values)
        
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort by job number (convert to int for proper numeric sorting)
        # Handle both numeric and non-numeric job numbers
        def job_sort_key(x):
            job_num = str(x[0]).strip()
            if job_num.isdigit():
                return int(job_num)
            else:
                # For non-numeric, try to extract first sequence of digits
                import re
                digits = re.findall(r'\d+', job_num)
                if digits:
                    return int(digits[0])
                else:
                    return 0
        
        # Sort with current direction
        sorted_items = sorted(items, key=job_sort_key, reverse=not self.job_sort_ascending)
        
        # Toggle direction for next time
        self.job_sort_ascending = not self.job_sort_ascending
        
        # Update button text to show current direction
        direction = "↑" if self.job_sort_ascending else "↓"
        self.sort_job_btn.config(text=f"Job # {direction}")
        
        # Add sorted items back
        for item in sorted_items:
            self.tree.insert('', 'end', values=item)
    
    def sort_by_customer(self):
        """Sort projects by customer name (toggle ascending/descending)"""
        # Get all current items and their values
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            items.append(values)
        
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort by customer name (case-insensitive)
        sorted_items = sorted(items, key=lambda x: x[1].upper() if x[1] else "", reverse=not self.customer_sort_ascending)
        
        # Toggle direction for next time
        self.customer_sort_ascending = not self.customer_sort_ascending
        
        # Update button text to show current direction
        direction = "↑" if self.customer_sort_ascending else "↓"
        self.sort_customer_btn.config(text=f"Customer {direction}")
        
        # Add sorted items back
        for item in sorted_items:
            self.tree.insert('', 'end', values=item)
    
    def sort_by_due_date(self):
        """Sort projects by due date - earliest on top when ascending"""
        # Get all projects with due dates from database
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT job_number, customer_name, due_date, completion_date,
                   CASE 
                       WHEN completion_date IS NOT NULL AND completion_date != '' THEN 'Completed'
                       WHEN start_date IS NOT NULL AND start_date != '' THEN 'In Progress'
                       WHEN assignment_date IS NOT NULL AND assignment_date != '' THEN 'Assigned'
                       ELSE 'Not Assigned'
                   END as status
            FROM projects
            ORDER BY 
                CASE 
                    WHEN due_date IS NULL OR due_date = '' THEN 1
                    ELSE 0
                END,
                due_date """ + ("ASC" if self.due_date_sort_ascending else "DESC") + """
        """)
        
        projects = cursor.fetchall()
        conn.close()
        
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add sorted items back
        for project in projects:
            job_num, customer, due_date, completion_date, status = project
            
            # Calculate days until due
            days_until_due = ""
            if due_date and not completion_date:
                try:
                    due = datetime.strptime(due_date, "%Y-%m-%d")
                    today = datetime.now()
                    days_diff = (due - today).days
                    
                    if days_diff < 0:
                        days_until_due = f"{abs(days_diff)} overdue"
                    elif days_diff == 0:
                        days_until_due = "Today"
                    else:
                        days_until_due = str(days_diff)
                except:
                    days_until_due = ""
            
            self.tree.insert('', 'end', values=(job_num, customer or '', due_date or '', 
                                               days_until_due, status))
        
        # Toggle direction for next time
        self.due_date_sort_ascending = not self.due_date_sort_ascending
        
        # Update button text to show current direction
        direction = "↑" if self.due_date_sort_ascending else "↓"
        self.sort_due_date_btn.config(text=f"Due Date {direction}")
    
    def on_project_select(self, event):
        """Handle project selection with row highlighting"""
        selection = self.tree.selection()
        if not selection:
            print("DEBUG: No selection")
            return
        
        # Remove 'selected' tag from all items
        for item in self.tree.get_children():
            self.tree.item(item, tags=())
        
        # Add 'selected' tag to selected item
        self.tree.item(selection[0], tags=('selected',))
        
        item = self.tree.item(selection[0])
        job_number = item['values'][0]
        print(f"DEBUG: Selected project: {job_number}")
        
        # Set current project before loading details
        self.current_project = job_number
        
        self.load_project_details(job_number)
    
    def clear_workflow_data(self):
        """Clear all workflow data before loading new project"""
        # Temporarily disable auto-save to prevent saving empty values
        self._loading_project = True
        
        # Clear initial redline
        self.initial_redline_var.set(False)
        self.initial_engineer_var.set("")
        self.initial_date_entry.set("")
        
        # Clear redline updates
        for i in range(1, 5):
            if hasattr(self, f"redline_update_{i}_var"):
                getattr(self, f"redline_update_{i}_var").set(False)
            if hasattr(self, f"redline_update_{i}_engineer_var"):
                getattr(self, f"redline_update_{i}_engineer_var").set("")
            if hasattr(self, f"redline_update_{i}_date_entry"):
                getattr(self, f"redline_update_{i}_date_entry").set("")
        
        # Clear OPS review
        self.ops_review_var.set(False)
        self.ops_review_date_entry.set("")
        
        # Clear D365 BOM Entry
        self.d365_bom_var.set(False)
        self.d365_bom_date_entry.set("")
        
        # Clear Peter Weck review
        self.peter_weck_var.set(False)
        self.peter_weck_date_entry.set("")
        
        # Clear release to Dee
        self.release_fixed_errors_var.set(False)
        self.missing_prints_date_entry.set("")
        self.d365_updates_date_entry.set("")
        self.other_notes_var.set("")
        self.other_date_entry.set("")
        self.release_due_date_entry.set("")
        self.release_due_display_var.set("")

    def load_project_details(self, job_number):
        """Load details for selected project"""
        print(f"DEBUG: Loading project details for: {job_number}")
        
        # Clean the job number (remove any extra text)
        clean_job_number = str(job_number).strip()
        if ' ' in clean_job_number:
            # Extract just the numeric part
            parts = clean_job_number.split()
            for part in parts:
                if part.isdigit() and len(part) == 5:
                    clean_job_number = part
                    break
        
        print(f"DEBUG: Cleaned job number: {clean_job_number}")
        
        # Clear workflow data first to prevent showing old data
        self.clear_workflow_data()
        
        # Temporarily disable auto-save to prevent interference
        self._loading_project = True
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Load main project data
        query = """
        SELECT p.job_number, p.job_directory, p.customer_name, p.customer_name_directory,
               p.customer_location, p.customer_location_directory, d.name, e.name,
               p.assignment_date, p.start_date, p.completion_date, 
               p.total_duration_days, p.released_to_dee, p.due_date
        FROM projects p
        LEFT JOIN designers d ON p.assigned_to_id = d.id
        LEFT JOIN engineers e ON p.project_engineer_id = e.id
        WHERE p.job_number = ?
        """
        
        cursor.execute(query, (clean_job_number,))
        project = cursor.fetchone()
        
        print(f"DEBUG: Project data loaded: {project}")
        
        if project:
            self.job_number_var.set(project[0])
            self.job_directory_picker.set(project[1] or "")
            self.customer_name_var.set(project[2] or "")
            self.customer_name_picker.set(project[3] or "")
            self.customer_location_var.set(project[4] or "")
            self.customer_location_picker.set(project[5] or "")
            self.assigned_to_var.set(project[6] or "")
            self.project_engineer_var.set(project[7] or "")
            self.assignment_date_entry.set(project[8] or "")
            self.start_date_entry.set(project[9] or "")
            self.completion_date_entry.set(project[10] or "")
            self.duration_var.set(f"{project[11]} days" if project[11] else "N/A")
            self.released_to_dee_entry.set(project[12] or "")
            self.due_date_entry.set(project[13] or "")
        
        # Load workflow data
        self.load_workflow_data(clean_job_number, cursor)
        
        # Update quick access panel
        self.update_quick_access()
        
        # Update specifications panel
        self.update_specifications(self.project_details_container.winfo_children()[0])
        
        # Update cover sheet button
        self.update_cover_sheet_button()
        
        # Re-enable auto-save
        self._loading_project = False
        
        conn.close()
    
    def load_workflow_data(self, job_number, cursor):
        """Load workflow data for selected project"""
        # Get project ID
        cursor.execute("SELECT id FROM projects WHERE job_number = ?", (job_number,))
        project_result = cursor.fetchone()
        if not project_result:
            return
        
        project_id = project_result[0]
        
        # Load initial redline
        cursor.execute("""
            SELECT ir.redline_date, e.name, ir.is_completed
            FROM initial_redline ir
            LEFT JOIN engineers e ON ir.engineer_id = e.id
            WHERE ir.project_id = ?
        """, (project_id,))
        initial_redline = cursor.fetchone()
        
        if initial_redline:
            self.initial_redline_var.set(bool(initial_redline[2]))
            self.initial_engineer_var.set(initial_redline[1] or "")
            self.initial_date_entry.set(initial_redline[0] or "")
        
        # Load redline updates
        cursor.execute("""
            SELECT ru.update_cycle, ru.update_date, e.name, ru.is_completed
            FROM redline_updates ru
            LEFT JOIN engineers e ON ru.engineer_id = e.id
            WHERE ru.project_id = ?
            ORDER BY ru.update_cycle
        """, (project_id,))
        redline_updates = cursor.fetchall()
        
        for update in redline_updates:
            cycle = update[0]
            if 1 <= cycle <= 4:
                # Only set the values if the widgets exist
                if hasattr(self, f"redline_update_{cycle}_var"):
                    getattr(self, f"redline_update_{cycle}_var").set(bool(update[3]))
                if hasattr(self, f"redline_update_{cycle}_engineer_var"):
                    getattr(self, f"redline_update_{cycle}_engineer_var").set(update[2] or "")
                if hasattr(self, f"redline_update_{cycle}_date_entry"):
                    getattr(self, f"redline_update_{cycle}_date_entry").set(update[1] or "")
        
        # Load OPS review
        cursor.execute("""
            SELECT review_date, is_completed
            FROM ops_review
            WHERE project_id = ?
        """, (project_id,))
        ops_review = cursor.fetchone()
        
        if ops_review:
            self.ops_review_var.set(bool(ops_review[1]))
            self.ops_review_date_entry.set(ops_review[0] or "")
        
        # Load D365 BOM Entry
        cursor.execute("""
            SELECT entry_date, is_completed
            FROM d365_bom_entry
            WHERE project_id = ?
        """, (project_id,))
        d365_bom = cursor.fetchone()
        
        if d365_bom:
            self.d365_bom_var.set(bool(d365_bom[1]))
            self.d365_bom_date_entry.set(d365_bom[0] or "")
        
        # Load Peter Weck review
        cursor.execute("""
            SELECT fixed_errors_date, is_completed
            FROM peter_weck_review
            WHERE project_id = ?
        """, (project_id,))
        peter_weck = cursor.fetchone()
        
        if peter_weck:
            self.peter_weck_var.set(bool(peter_weck[1]))
            self.peter_weck_date_entry.set(peter_weck[0] or "")
        
        # Load release to Dee
        cursor.execute("""
            SELECT release_date, missing_prints_date, d365_updates_date, 
                   other_notes, other_date, due_date, is_completed
            FROM release_to_dee
            WHERE project_id = ?
        """, (project_id,))
        release_data = cursor.fetchone()
        
        if release_data:
            self.release_fixed_errors_var.set(bool(release_data[6]))
            self.missing_prints_date_entry.set(release_data[1] or "")
            self.d365_updates_date_entry.set(release_data[2] or "")
            self.other_notes_var.set(release_data[3] or "")
            self.other_date_entry.set(release_data[4] or "")
            self.release_due_date_entry.set(release_data[5] or "")
            # Update the due date display
            self.update_release_due_display()
    
    def new_project(self):
        """Clear form for new project"""
        # Clear main project fields
        self.job_number_var.set("")
        self.job_directory_picker.set("")
        self.customer_name_var.set("")
        self.customer_name_picker.set("")
        self.customer_location_var.set("")
        self.customer_location_picker.set("")
        self.assigned_to_var.set("")
        self.assignment_date_entry.set(datetime.now().strftime("%Y-%m-%d"))
        self.start_date_entry.set("")
        self.completion_date_entry.set("")
        self.duration_var.set("")
        self.released_to_dee_entry.set("")
        
        # Clear workflow fields
        self.initial_redline_var.set(False)
        self.initial_engineer_var.set("")
        self.initial_date_entry.set("")
        
        for i in range(1, 5):
            getattr(self, f"redline_update_{i}_var").set(False)
            setattr(self, f"redline_update_{i}_engineer_var", tk.StringVar(""))
            if hasattr(self, f"redline_update_{i}_date_entry"):
                getattr(self, f"redline_update_{i}_date_entry").set("")
        
        self.ops_review_var.set(False)
        self.ops_review_date_entry.set("")
        self.peter_weck_var.set(False)
        self.peter_weck_date_entry.set("")
        self.release_fixed_errors_var.set(False)
        self.missing_prints_date_entry.set("")
        self.d365_updates_date_entry.set("")
        self.other_notes_var.set("")
        self.other_date_entry.set("")
        
        # Clear KOM file path and all document lists
        if hasattr(self, 'kom_oc_form_path'):
            self.kom_oc_form_path = None
        if hasattr(self, 'proposal_docs'):
            self.proposal_docs = []
        if hasattr(self, 'other_docs'):
            self.other_docs = []
        if hasattr(self, 'engineering_general_docs'):
            self.engineering_general_docs = []
        if hasattr(self, 'engineering_releases_docs'):
            self.engineering_releases_docs = []
        
        # Update quick access panel
        self.update_quick_access()
    
    def save_project(self):
        """Save project to database"""
        job_number = self.job_number_var.get().strip()
        if not job_number:
            messagebox.showerror("Error", "Job number is required!")
            return
        
        if not self.is_valid_job_number(job_number):
            messagebox.showerror("Error", "Job number must be exactly 5 digits (e.g., 12345)!")
            return
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            # Get designer ID
            designer_id = None
            if self.assigned_to_var.get():
                cursor.execute("SELECT id FROM designers WHERE name = ?", (self.assigned_to_var.get(),))
                result = cursor.fetchone()
                if result:
                    designer_id = result[0]
            
            # Get project engineer ID
            project_engineer_id = None
            if self.project_engineer_var.get():
                cursor.execute("SELECT id FROM engineers WHERE name = ?", (self.project_engineer_var.get(),))
                result = cursor.fetchone()
                if result:
                    project_engineer_id = result[0]
            
            # Calculate duration
            duration = None
            if self.start_date_entry.get() and self.completion_date_entry.get():
                try:
                    start = datetime.strptime(self.start_date_entry.get(), "%Y-%m-%d")
                    end = datetime.strptime(self.completion_date_entry.get(), "%Y-%m-%d")
                    duration = (end - start).days
                except ValueError:
                    pass
            
            # Insert or update project
            cursor.execute("""
                INSERT OR REPLACE INTO projects 
                (job_number, job_directory, customer_name, customer_name_directory, 
                 customer_location, customer_location_directory, assigned_to_id, project_engineer_id,
                 assignment_date, start_date, completion_date, 
                 total_duration_days, released_to_dee, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_number,
                self.job_directory_picker.get() or None,
                self.customer_name_var.get().upper() or None,
                self.customer_name_picker.get() or None,
                self.customer_location_var.get().upper() or None,
                self.customer_location_picker.get() or None,
                designer_id,
                project_engineer_id,
                self.assignment_date_entry.get() or None,
                self.start_date_entry.get() or None,
                self.completion_date_entry.get() or None,
                duration,
                self.released_to_dee_entry.get() or None,
                self.due_date_entry.get() or None
            ))
            
            # Get project ID
            cursor.execute("SELECT id FROM projects WHERE job_number = ?", (self.job_number_var.get(),))
            project_id = cursor.fetchone()[0]
            
            # Save workflow data
            self.save_workflow_data(cursor, project_id)
            
            conn.commit()
            messagebox.showinfo("Success", "Project saved successfully!")
            self.load_projects()
            self.update_quick_access()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
        finally:
            conn.close()
    
    def save_workflow_data(self, cursor, project_id):
        """Save workflow data for the project"""
        # Save initial redline (always save, regardless of checkbox state)
        engineer_id = None
        if self.initial_engineer_var.get():
            cursor.execute("SELECT id FROM engineers WHERE name = ?", (self.initial_engineer_var.get(),))
            result = cursor.fetchone()
            if result:
                engineer_id = result[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO initial_redline 
            (project_id, engineer_id, redline_date, is_completed)
            VALUES (?, ?, ?, ?)
        """, (project_id, engineer_id, self.initial_date_entry.get() or None, self.initial_redline_var.get()))
        
        # Save redline updates (always save all cycles, regardless of checkbox state)
        for i in range(1, 5):
            var_name = f"redline_update_{i}_var"
            engineer_var_name = f"redline_update_{i}_engineer_var"
            date_entry_name = f"redline_update_{i}_date_entry"
            
            engineer_id = None
            if hasattr(self, engineer_var_name) and getattr(self, engineer_var_name).get():
                cursor.execute("SELECT id FROM engineers WHERE name = ?", (getattr(self, engineer_var_name).get(),))
                result = cursor.fetchone()
                if result:
                    engineer_id = result[0]
            
            date_value = None
            if hasattr(self, date_entry_name):
                date_value = getattr(self, date_entry_name).get()
            
            checkbox_value = False
            if hasattr(self, var_name):
                checkbox_value = getattr(self, var_name).get()
            
            cursor.execute("""
                INSERT OR REPLACE INTO redline_updates 
                (project_id, engineer_id, update_date, update_cycle, is_completed)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, engineer_id, date_value, i, checkbox_value))
        
        # Save OPS review (always save, regardless of checkbox state)
        cursor.execute("""
            INSERT OR REPLACE INTO ops_review 
            (project_id, review_date, is_completed)
            VALUES (?, ?, ?)
        """, (project_id, self.ops_review_date_entry.get() or None, self.ops_review_var.get()))
        
        # Save D365 BOM Entry (always save, regardless of checkbox state)
        cursor.execute("""
            INSERT OR REPLACE INTO d365_bom_entry 
            (project_id, entry_date, is_completed)
            VALUES (?, ?, ?)
        """, (project_id, self.d365_bom_date_entry.get() or None, self.d365_bom_var.get()))
        
        # Save Peter Weck review (always save, regardless of checkbox state)
        cursor.execute("""
            INSERT OR REPLACE INTO peter_weck_review 
            (project_id, fixed_errors_date, is_completed)
            VALUES (?, ?, ?)
        """, (project_id, self.peter_weck_date_entry.get() or None, self.peter_weck_var.get()))
        
        # Save release to Dee (always save, regardless of checkbox state)
        cursor.execute("""
            INSERT OR REPLACE INTO release_to_dee 
            (project_id, release_date, missing_prints_date, d365_updates_date, 
             other_notes, other_date, due_date, is_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, self.released_to_dee_entry.get() or None,
             self.missing_prints_date_entry.get() or None,
             self.d365_updates_date_entry.get() or None,
             self.other_notes_var.get() or None,
             self.other_date_entry.get() or None,
             self.release_due_date_entry.get() or None,
             self.release_fixed_errors_var.get()))
    
    def delete_project(self):
        """Delete selected project"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this project?"):
            item = self.tree.item(selection[0])
            job_number = item['values'][0]
            
            # Clean the job number (remove any extra text)
            clean_job_number = str(job_number).strip()
            if ' ' in clean_job_number:
                # Extract just the numeric part
                parts = clean_job_number.split()
                for part in parts:
                    if part.isdigit() and len(part) == 5:
                        clean_job_number = part
                        break
            
            print(f"DEBUG: Deleting project - Original: {job_number}, Cleaned: {clean_job_number}")
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            try:
                # Get project ID
                cursor.execute("SELECT id FROM projects WHERE job_number = ?", (clean_job_number,))
                project_result = cursor.fetchone()
                if project_result:
                    project_id = project_result[0]
                    print(f"DEBUG: Found project ID: {project_id}")
                    
                    # Delete all related workflow data
                    print("DEBUG: Deleting workflow data...")
                    cursor.execute("DELETE FROM initial_redline WHERE project_id = ?", (project_id,))
                    cursor.execute("DELETE FROM redline_updates WHERE project_id = ?", (project_id,))
                    cursor.execute("DELETE FROM ops_review WHERE project_id = ?", (project_id,))
                    cursor.execute("DELETE FROM d365_bom_entry WHERE project_id = ?", (project_id,))
                    cursor.execute("DELETE FROM peter_weck_review WHERE project_id = ?", (project_id,))
                    cursor.execute("DELETE FROM release_to_dee WHERE project_id = ?", (project_id,))
                    print("DEBUG: Workflow data deleted")
                
                # Delete project
                print("DEBUG: Deleting main project...")
                cursor.execute("DELETE FROM projects WHERE job_number = ?", (clean_job_number,))
                rows_deleted = cursor.rowcount
                print(f"DEBUG: Rows deleted: {rows_deleted}")
                
                # Commit changes
                conn.commit()
                print("DEBUG: Changes committed")
                
                if rows_deleted > 0:
                    print("DEBUG: Project deleted successfully")
                    messagebox.showinfo("Success", f"Project {clean_job_number} deleted successfully!")
                    self.load_projects()
                    self.new_project()
                else:
                    print("DEBUG: No project found to delete")
                    messagebox.showwarning("Warning", f"No project found with job number: {clean_job_number}")
                    
            except Exception as e:
                print(f"DEBUG: Error during deletion: {e}")
                print(f"DEBUG: Error type: {type(e)}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to delete project: {str(e)}")
            finally:
                conn.close()
    
    def calculate_duration(self, *args):
        """Calculate project duration"""
        start_date = self.start_date_entry.get()
        completion_date = self.completion_date_entry.get()
        
        if start_date and completion_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(completion_date, "%Y-%m-%d")
                duration = (end - start).days
                self.duration_var.set(f"{duration} days")
            except ValueError:
                self.duration_var.set("Invalid dates")
        else:
            self.duration_var.set("")
    
    def set_start_date(self, *args):
        """Set start date to assignment date if not already set"""
        if not self.start_date_entry.get() and self.assignment_date_entry.get():
            self.start_date_entry.set(self.assignment_date_entry.get())
    
    def open_dashboard(self):
        """Open the dashboard application"""
        try:
            if os.path.exists('dashboard.py'):
                subprocess.Popen([sys.executable, 'dashboard.py'])
            else:
                messagebox.showerror("Error", "dashboard.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Dashboard:\n{str(e)}")
    
    def export_data(self):
        """Export data to JSON"""
        self.db_manager.export_to_json()
        messagebox.showinfo("Success", "Data exported to JSON successfully!")
    
    def import_data(self):
        """Import data from JSON"""
        self.db_manager.import_from_json()
        self.load_projects()
        self.load_dropdown_data()
        messagebox.showinfo("Success", "Data imported from JSON successfully!")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        else:
            self.root.attributes('-fullscreen', True)
    
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        self.root.attributes('-fullscreen', False)
    
    def _bind_mousewheel(self, canvas, frame):
        """Bind mouse wheel scrolling to a canvas"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        # Bind when mouse enters the canvas or frame
        canvas.bind('<Enter>', _bind_to_mousewheel)
        frame.bind('<Enter>', _bind_to_mousewheel)
        
        # Unbind when mouse leaves
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        frame.bind('<Leave>', _unbind_from_mousewheel)
    
    def on_closing(self):
        """Handle application closing"""
        self.db_manager.backup_database()
        self.db_manager.export_to_json()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ProjectsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()