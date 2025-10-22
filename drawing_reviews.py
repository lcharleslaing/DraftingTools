#!/usr/bin/env python3
"""
Drawing Reviews Application
Digital drawing review and markup with tablet support and audit trail
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ui_prefs import bind_tree_column_persistence
import sqlite3
import os
import json
from datetime import datetime
import subprocess
import sys
from settings import SettingsManager
from app_nav import add_app_bar
from help_utils import add_help_button

class DrawingReviewsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drawing Reviews - Digital Markup System")
        self.root.state('zoomed')  # Full screen
        self.root.configure(bg='#2c3e50')
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Current state
        self.current_job = None
        self.current_drawing = None
        self.current_reviewer = None
        self.current_department = None
        
        # Initialize database
        self.init_database()
        
        # Create interface
        try:
            add_app_bar(self.root, current_app='drawing_reviews')
        except Exception:
            pass
        self.create_widgets()
        
        # Load initial data
        self.load_jobs()
        self.load_reviewers()
    
    def init_database(self):
        """Initialize drawing reviews database tables"""
        conn = sqlite3.connect('drafting_tools.db')
        cursor = conn.cursor()
        
        # Create drawing_reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drawing_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                drawing_name TEXT NOT NULL,
                original_path TEXT NOT NULL,
                review_path TEXT NOT NULL,
                department TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                review_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_date TEXT,
                notes TEXT,
                file_size INTEGER,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        # Create review_workflow table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_workflow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                drawing_name TEXT NOT NULL,
                workflow_step INTEGER NOT NULL,
                department TEXT NOT NULL,
                reviewer TEXT,
                status TEXT DEFAULT 'pending',
                assigned_date TEXT,
                completed_date TEXT,
                notes TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        """Create the main interface"""
        # Top header
        self.create_header()
        
        # Main content area
        self.create_main_content()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create the top header with job selection and user info"""
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        # Left side - Job selection
        left_frame = tk.Frame(header_frame, bg='#34495e')
        left_frame.pack(side='left', fill='y', padx=10, pady=10)
        
        tk.Label(left_frame, text="Job Selection:", 
                font=('Arial', 12, 'bold'), 
                bg='#34495e', fg='white').pack(anchor='w')
        
        self.job_var = tk.StringVar()
        self.job_combo = ttk.Combobox(left_frame, textvariable=self.job_var, 
                                     width=40, font=('Arial', 11))
        self.job_combo.pack(pady=(5, 0))
        self.job_combo.bind('<<ComboboxSelected>>', self.on_job_selected)
        
        # Center - User info
        center_frame = tk.Frame(header_frame, bg='#34495e')
        center_frame.pack(side='left', fill='both', expand=True, padx=20)
        
        self.user_label = tk.Label(center_frame, text="User: Not Set", 
                                  font=('Arial', 14, 'bold'), 
                                  bg='#34495e', fg='#ecf0f1')
        self.user_label.pack(expand=True)
        
        # Right side - Action buttons
        right_frame = tk.Frame(header_frame, bg='#34495e')
        right_frame.pack(side='right', fill='y', padx=10, pady=10)
        
        tk.Button(right_frame, text="⚙️ Settings", 
                 command=self.open_settings,
                 font=('Arial', 10), bg='#3498db', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='right', padx=5)
        
        tk.Button(right_frame, text="📁 Open Folder", 
                 command=self.open_review_folder,
                 font=('Arial', 10), bg='#27ae60', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='right', padx=5)
        
        # Update user display
        self.update_user_display()
    
    def create_main_content(self):
        """Create the main content area"""
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Drawings to be reviewed
        left_panel = tk.Frame(main_frame, bg='#34495e', width=400)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # Drawings to be reviewed
        self.create_drawings_panel(left_panel)
        
        # Right panel - Previously reviewed drawings
        right_panel = tk.Frame(main_frame, bg='#34495e')
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # Previously reviewed drawings
        self.create_reviewed_panel(right_panel)
    
    def create_drawings_panel(self, parent):
        """Create the drawings to be reviewed panel"""
        # Header
        header_frame = tk.Frame(parent, bg='#2c3e50', height=50)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📝 Drawings to be Reviewed/Checked/Audited", 
                font=('Arial', 12, 'bold'), 
                bg='#2c3e50', fg='white').pack(expand=True)
        
        # Controls
        controls_frame = tk.Frame(parent, bg='#34495e')
        controls_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(controls_frame, text="📁 Import Drawings", 
                 command=self.import_drawings,
                 font=('Arial', 10), bg='#3498db', fg='white',
                 relief='flat', padx=10, pady=5).pack(side='left', padx=5)
        
        tk.Button(controls_frame, text="🔄 Refresh", 
                 command=self.refresh_drawings,
                 font=('Arial', 10), bg='#95a5a6', fg='white',
                 relief='flat', padx=10, pady=5).pack(side='left', padx=5)
        
        tk.Button(controls_frame, text="🔍 Scan Job Folder", 
                 command=self.scan_job_folder,
                 font=('Arial', 10), bg='#e67e22', fg='white',
                 relief='flat', padx=10, pady=5).pack(side='left', padx=5)
        
        # Drawings list
        list_frame = tk.Frame(parent, bg='#34495e')
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview for drawings
        columns = ("drawing_name", "status", "department")
        self.drawings_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        self.drawings_tree.heading("drawing_name", text="Drawing Name")
        self.drawings_tree.heading("status", text="Status")
        self.drawings_tree.heading("department", text="Department")
        
        self.drawings_tree.column("drawing_name", width=200)
        self.drawings_tree.column("status", width=80)
        self.drawings_tree.column("department", width=100)
        
        self.drawings_tree.pack(fill='both', expand=True)
        bind_tree_column_persistence(self.drawings_tree, 'drawing_reviews.drawings_tree', self.root)
        
        # Bind double-click to open drawing
        self.drawings_tree.bind('<Double-1>', self.open_drawing_for_review)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.drawings_tree.yview)
        self.drawings_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def create_reviewed_panel(self, parent):
        """Create the previously reviewed drawings panel"""
        # Header
        header_frame = tk.Frame(parent, bg='#2c3e50', height=50)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📋 Previously Reviewed and Saved Drawings", 
                font=('Arial', 12, 'bold'), 
                bg='#2c3e50', fg='white').pack(expand=True)
        
        # Controls
        controls_frame = tk.Frame(parent, bg='#34495e')
        controls_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(controls_frame, text="🔍 Search", 
                 command=self.search_reviews,
                 font=('Arial', 10), bg='#e67e22', fg='white',
                 relief='flat', padx=10, pady=5).pack(side='left', padx=5)
        
        tk.Button(controls_frame, text="📊 Statistics", 
                 command=self.show_statistics,
                 font=('Arial', 10), bg='#9b59b6', fg='white',
                 relief='flat', padx=10, pady=5).pack(side='left', padx=5)
        
        # Reviewed drawings list
        list_frame = tk.Frame(parent, bg='#34495e')
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview for reviewed drawings
        columns = ("drawing_name", "reviewer", "department", "status", "date")
        self.reviewed_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        self.reviewed_tree.heading("drawing_name", text="Drawing Name")
        self.reviewed_tree.heading("reviewer", text="Reviewer")
        self.reviewed_tree.heading("department", text="Department")
        self.reviewed_tree.heading("status", text="Status")
        self.reviewed_tree.heading("date", text="Date")
        
        self.reviewed_tree.column("drawing_name", width=200)
        self.reviewed_tree.column("reviewer", width=120)
        self.reviewed_tree.column("department", width=100)
        self.reviewed_tree.column("status", width=80)
        self.reviewed_tree.column("date", width=100)
        
        self.reviewed_tree.pack(fill='both', expand=True)
        try:
            add_help_button(list_frame, 'Reviewed Drawings', 'This list shows completed or in‑progress reviews. Double‑click to open.').pack(anchor='ne')
        except Exception:
            pass
        bind_tree_column_persistence(self.reviewed_tree, 'drawing_reviews.reviewed_tree', self.root)
        
        # Bind double-click to open reviewed drawing
        self.reviewed_tree.bind('<Double-1>', self.open_reviewed_drawing)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.reviewed_tree.yview)
        self.reviewed_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def create_status_bar(self):
        """Create the bottom status bar"""
        status_frame = tk.Frame(self.root, bg='#34495e', height=30)
        status_frame.pack(fill='x', padx=10, pady=5)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", 
                                    font=('Arial', 10), 
                                    bg='#34495e', fg='white')
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Right side info
        info_label = tk.Label(status_frame, text="Drawing Reviews v1.0", 
                             font=('Arial', 10), 
                             bg='#34495e', fg='#bdc3c7')
        info_label.pack(side='right', padx=10, pady=5)
    
    def load_jobs(self):
        """Load available jobs from database"""
        try:
            conn = sqlite3.connect('drafting_tools.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT job_number, customer_name, due_date
                FROM projects 
                WHERE job_number IS NOT NULL 
                AND (project_status IS NULL OR project_status = 'active')
                ORDER BY due_date ASC
            ''')
            
            jobs = cursor.fetchall()
            job_list = []
            for job in jobs:
                job_number, customer, due_date = job
                display_text = f"{job_number} - {customer or 'Unknown Customer'}"
                if due_date:
                    display_text += f" (Due: {due_date})"
                job_list.append(display_text)
            
            self.job_combo['values'] = job_list
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load jobs: {str(e)}")
    
    def load_reviewers(self):
        """Load available reviewers from settings"""
        try:
            users = self.settings_manager.get_users()
            self.reviewers = [user[0] for user in users]  # username
        except Exception as e:
            print(f"Error loading reviewers: {e}")
            self.reviewers = []
    
    def update_user_display(self):
        """Update the user display in the header"""
        current_user = self.settings_manager.current_user
        current_dept = self.settings_manager.current_department
        
        if current_user:
            display_text = f"User: {current_user}"
            if current_dept:
                display_text += f" ({current_dept})"
            self.user_label.config(text=display_text)
            self.current_reviewer = current_user
            self.current_department = current_dept
        else:
            self.user_label.config(text="User: Not Set - Please configure in Settings")
            self.current_reviewer = None
            self.current_department = None
    
    def on_job_selected(self, event):
        """Handle job selection"""
        selection = self.job_var.get()
        if selection:
            # Extract job number from display text
            job_number = selection.split(' - ')[0]
            self.current_job = job_number
            self.status_label.config(text=f"Selected Job: {job_number}")
            self.refresh_drawings()
            self.refresh_reviewed_drawings()
    
    def refresh_drawings(self):
        """Refresh the drawings to be reviewed list"""
        if not self.current_job:
            return
        
        # Clear existing items
        for item in self.drawings_tree.get_children():
            self.drawings_tree.delete(item)
        
        try:
            # First check for Print Package Review files
            pp_files = self.get_print_package_files()
            
            if pp_files:
                # Show Print Package Review files
                for file_info in pp_files:
                    self.drawings_tree.insert("", "end", values=(
                        file_info['file_name'], 
                        file_info['status'], 
                        file_info['department']
                    ))
                
                self.status_label.config(text=f"Found {len(pp_files)} Print Package Review files for job {self.current_job}")
            else:
                # Fallback to regular drawing reviews
                conn = sqlite3.connect('drafting_tools.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT drawing_name, status, department, created_date
                    FROM drawing_reviews 
                    WHERE job_number = ? AND status = 'pending'
                    ORDER BY created_date DESC
                ''', (self.current_job,))
                
                drawings = cursor.fetchall()
                
                if drawings:
                    for drawing in drawings:
                        drawing_name, status, department, date = drawing
                        self.drawings_tree.insert("", "end", values=(
                            drawing_name, status, department
                        ))
                    
                    self.status_label.config(text=f"Found {len(drawings)} drawings pending review for job {self.current_job}")
                else:
                    self.drawings_tree.insert("", "end", values=("No drawings found", "N/A", "N/A"))
                    self.status_label.config(text=f"No drawings pending review for job {self.current_job}")
                
                conn.close()
            
        except Exception as e:
            print(f"Error loading drawings: {e}")
            self.drawings_tree.insert("", "end", values=("Error loading drawings", "Error", "Error"))
            self.status_label.config(text=f"Error loading drawings for job {self.current_job}")
    
    def get_print_package_files(self):
        """Get Print Package Review files for the current job"""
        try:
            from print_package_workflow import PrintPackageWorkflow
            
            workflow_engine = PrintPackageWorkflow()
            
            # Get review info
            review_info = workflow_engine.get_review_info(self.current_job)
            if not review_info:
                return []
            
            # Get current stage
            current_stage = review_info['current_stage']
            
            # Get files for current stage
            files = workflow_engine.get_files_for_stage(self.current_job, current_stage)
            
            # Format for display
            pp_files = []
            for file_info in files:
                if file_info['exists']:
                    pp_files.append({
                        'file_name': file_info['file_name'],
                        'status': 'Pending Review',
                        'department': self.get_stage_department(current_stage),
                        'stage_path': file_info['stage_path']
                    })
            
            return pp_files
            
        except Exception as e:
            print(f"Error getting Print Package files: {e}")
            return []
    
    def get_stage_department(self, stage):
        """Get department name for a workflow stage"""
        stage_departments = {
            0: "Drafting",
            1: "Engineering", 
            2: "Engineering QC",
            3: "Drafting",
            4: "Lead Designer",
            5: "Production OPS",
            6: "Drafting",
            7: "Final Approval"
        }
        return stage_departments.get(stage, "Unknown")
    
    def refresh_reviewed_drawings(self):
        """Refresh the previously reviewed drawings list"""
        if not self.current_job:
            return
        
        # Clear existing items
        for item in self.reviewed_tree.get_children():
            self.reviewed_tree.delete(item)
        
        try:
            conn = sqlite3.connect('drafting_tools.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT drawing_name, reviewer, department, status, created_date
                FROM drawing_reviews 
                WHERE job_number = ?
                ORDER BY created_date DESC
            ''', (self.current_job,))
            
            reviews = cursor.fetchall()
            for review in reviews:
                drawing_name, reviewer, department, status, date = review
                # Format date
                try:
                    date_obj = datetime.fromisoformat(date)
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                except:
                    formatted_date = date
                
                self.reviewed_tree.insert("", "end", values=(
                    drawing_name, reviewer, department, status, formatted_date
                ))
            
            conn.close()
            
        except Exception as e:
            print(f"Error loading reviewed drawings: {e}")
    
    def import_drawings(self):
        """Import drawings from file system"""
        if not self.current_job:
            messagebox.showwarning("Warning", "Please select a job first")
            return
        
        # Open file dialog for PDF files
        file_paths = filedialog.askopenfilenames(
            title="Select Drawing PDFs to Import",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_paths:
            self.status_label.config(text=f"Importing {len(file_paths)} drawings...")
            
            imported_count = 0
            for file_path in file_paths:
                if self.import_single_drawing(file_path):
                    imported_count += 1
            
            self.status_label.config(text=f"Imported {imported_count} of {len(file_paths)} drawings")
            messagebox.showinfo("Import Complete", f"Successfully imported {imported_count} drawings for job {self.current_job}")
            self.refresh_drawings()
    
    def import_single_drawing(self, file_path):
        """Import a single drawing PDF"""
        try:
            import os
            from datetime import datetime
            
            # Get file info
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Create review folder structure
            review_folder = self.create_review_folder_structure()
            
            # Copy PDF to review folder
            import shutil
            destination_path = os.path.join(review_folder, file_name)
            shutil.copy2(file_path, destination_path)
            
            # Add to database
            conn = sqlite3.connect('drafting_tools.db')
            cursor = conn.cursor()
            
            # Check if drawing already exists
            cursor.execute('''
                SELECT COUNT(*) FROM drawing_reviews 
                WHERE job_number = ? AND drawing_name = ?
            ''', (self.current_job, file_name))
            
            if cursor.fetchone()[0] > 0:
                conn.close()
                print(f"Drawing {file_name} already exists for job {self.current_job}")
                return False
            
            # Insert new drawing
            cursor.execute('''
                INSERT INTO drawing_reviews 
                (job_number, drawing_name, original_path, review_path, department, 
                 reviewer, review_type, status, file_size, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_job,
                file_name,
                file_path,  # Original location
                destination_path,  # Review location
                self.current_department or "Drafting",
                self.current_reviewer or "Unknown",
                "imported",
                "pending",
                file_size,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"Successfully imported: {file_name}")
            return True
            
        except Exception as e:
            print(f"Error importing {file_path}: {e}")
            return False
    
    def create_review_folder_structure(self):
        """Create the review folder structure for the current job"""
        try:
            # Base path: ProjectBackup/Drawing Reviews/{JobNumber}/
            base_path = os.path.join("ProjectBackup", "Drawing Reviews", self.current_job)
            os.makedirs(base_path, exist_ok=True)
            
            # Create department subfolders
            departments = self.settings_manager.get_departments()
            for dept in departments:
                dept_folder = os.path.join(base_path, dept[0])  # dept[0] is the name
                os.makedirs(dept_folder, exist_ok=True)
            
            return base_path
            
        except Exception as e:
            print(f"Error creating folder structure: {e}")
            return os.path.join("ProjectBackup", "Drawing Reviews", self.current_job)
    
    def scan_job_folder(self):
        """Scan the job folder for existing PDF drawings"""
        if not self.current_job:
            messagebox.showwarning("Warning", "Please select a job first")
            return
        
        try:
            # Get job directory from database
            conn = sqlite3.connect('drafting_tools.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT job_directory FROM projects 
                WHERE job_number = ?
            ''', (self.current_job,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result or not result[0]:
                messagebox.showerror("Error", f"Job directory not found for job {self.current_job}")
                return
            
            job_directory = result[0]
            
            if not os.path.exists(job_directory):
                messagebox.showerror("Error", f"Job directory does not exist: {job_directory}")
                return
            
            # Scan for PDF files
            pdf_files = []
            for root, dirs, files in os.walk(job_directory):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            if not pdf_files:
                messagebox.showinfo("Scan Complete", f"No PDF files found in job directory: {job_directory}")
                return
            
            # Import found PDFs
            self.status_label.config(text=f"Found {len(pdf_files)} PDF files, importing...")
            
            imported_count = 0
            for pdf_path in pdf_files:
                if self.import_single_drawing(pdf_path):
                    imported_count += 1
            
            self.status_label.config(text=f"Imported {imported_count} of {len(pdf_files)} PDF files")
            messagebox.showinfo("Scan Complete", f"Found and imported {imported_count} PDF drawings from job folder")
            self.refresh_drawings()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan job folder: {str(e)}")
            print(f"Error scanning job folder: {e}")
    
    def open_drawing_for_review(self, event):
        """Open a drawing for review/markup"""
        selection = self.drawings_tree.selection()
        if not selection:
            return
        
        item = self.drawings_tree.item(selection[0])
        drawing_name = item['values'][0]
        
        if drawing_name == "No drawings found" or drawing_name == "Error loading drawings":
            messagebox.showinfo("Info", "No drawings available for review")
            return
        
        try:
            # Get the review path from database
            conn = sqlite3.connect('drafting_tools.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT review_path FROM drawing_reviews 
                WHERE job_number = ? AND drawing_name = ? AND status = 'pending'
            ''', (self.current_job, drawing_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and os.path.exists(result[0]):
                # Open the PDF file
                os.startfile(result[0])
                self.status_label.config(text=f"Opened {drawing_name} for review")
            else:
                messagebox.showerror("Error", f"Drawing file not found: {drawing_name}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open drawing: {str(e)}")
    
    def open_reviewed_drawing(self, event):
        """Open a previously reviewed drawing"""
        selection = self.reviewed_tree.selection()
        if not selection:
            return
        
        item = self.reviewed_tree.item(selection[0])
        drawing_name = item['values'][0]
        
        # TODO: Implement opening reviewed drawing
        messagebox.showinfo("Review", f"Opening reviewed drawing: {drawing_name}")
    
    def open_review_folder(self):
        """Open the review folder for the current job"""
        if not self.current_job:
            messagebox.showwarning("Warning", "Please select a job first")
            return
        
        # Construct review folder path
        review_folder = os.path.join("ProjectBackup", "Drawing Reviews", self.current_job)
        
        if os.path.exists(review_folder):
            os.startfile(review_folder)
        else:
            messagebox.showinfo("Info", f"Review folder not found: {review_folder}")
    
    def open_settings(self):
        """Open the settings window"""
        from settings import SettingsApp
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("900x700")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create settings app in the new window
        settings_app = SettingsApp(settings_window)
        
        # Update user display when settings window closes
        def on_close():
            self.update_user_display()
            settings_window.destroy()
        
        settings_window.protocol("WM_DELETE_WINDOW", on_close)
    
    def search_reviews(self):
        """Search through reviewed drawings"""
        messagebox.showinfo("Search", "Search functionality coming soon!")
    
    def show_statistics(self):
        """Show review statistics"""
        messagebox.showinfo("Statistics", "Statistics functionality coming soon!")

def main():
    """Main function to run the drawing reviews app"""
    app = DrawingReviewsApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()
