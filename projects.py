import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
from database_setup import DatabaseManager

class ProjectsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Management - Drafting Tools")
        self.root.geometry("1200x800")
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        self.create_widgets()
        self.load_projects()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Title
        title_label = ttk.Label(self.main_frame, text="Project Management", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Project details
        self.create_project_form()
        
        # Right panel - Project list
        self.create_project_list()
        
        # Bottom panel - Action buttons
        self.create_action_buttons()
    
    def create_project_form(self):
        """Create the project form panel"""
        form_frame = ttk.LabelFrame(self.main_frame, text="Project Details", padding="10")
        form_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Job Number
        ttk.Label(form_frame, text="Job Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.job_number_var = tk.StringVar()
        self.job_number_entry = ttk.Entry(form_frame, textvariable=self.job_number_var, width=20)
        self.job_number_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Assigned To
        ttk.Label(form_frame, text="Assigned To:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.assigned_to_var = tk.StringVar()
        self.assigned_to_combo = ttk.Combobox(form_frame, textvariable=self.assigned_to_var, 
                                            state="readonly", width=17)
        self.assigned_to_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Assignment Date
        ttk.Label(form_frame, text="Assignment Date:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.assignment_date_var = tk.StringVar()
        self.assignment_date_entry = ttk.Entry(form_frame, textvariable=self.assignment_date_var, width=20)
        self.assignment_date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Start Date
        ttk.Label(form_frame, text="Start Date:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(form_frame, textvariable=self.start_date_var, width=20)
        self.start_date_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Completion Date
        ttk.Label(form_frame, text="Completion Date:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.completion_date_var = tk.StringVar()
        self.completion_date_entry = ttk.Entry(form_frame, textvariable=self.completion_date_var, width=20)
        self.completion_date_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Total Duration
        ttk.Label(form_frame, text="Total Duration:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.duration_var = tk.StringVar()
        self.duration_label = ttk.Label(form_frame, textvariable=self.duration_var, 
                                       foreground="blue", font=('Arial', 10, 'bold'))
        self.duration_label.grid(row=5, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Released to Dee
        ttk.Label(form_frame, text="Released to Dee:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.released_to_dee_var = tk.StringVar()
        self.released_to_dee_entry = ttk.Entry(form_frame, textvariable=self.released_to_dee_var, width=20)
        self.released_to_dee_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Redline Updates Section
        redline_frame = ttk.LabelFrame(form_frame, text="Redline Updates", padding="5")
        redline_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Initial Redline
        self.initial_redline_var = tk.BooleanVar()
        ttk.Checkbutton(redline_frame, text="Initial Redline", 
                       variable=self.initial_redline_var).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(redline_frame, text="Engineer:").grid(row=1, column=0, sticky=tk.W)
        self.initial_engineer_var = tk.StringVar()
        self.initial_engineer_combo = ttk.Combobox(redline_frame, textvariable=self.initial_engineer_var, 
                                                 state="readonly", width=15)
        self.initial_engineer_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(redline_frame, text="Date:").grid(row=2, column=0, sticky=tk.W)
        self.initial_date_var = tk.StringVar()
        self.initial_date_entry = ttk.Entry(redline_frame, textvariable=self.initial_date_var, width=15)
        self.initial_date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Load dropdown data
        self.load_dropdown_data()
        
        # Bind events
        self.start_date_var.trace('w', self.calculate_duration)
        self.completion_date_var.trace('w', self.calculate_duration)
        self.assignment_date_var.trace('w', self.set_start_date)
    
    def create_project_list(self):
        """Create the project list panel"""
        list_frame = ttk.LabelFrame(self.main_frame, text="Projects", padding="10")
        list_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        
        # Search frame
        search_frame = ttk.Frame(list_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        self.search_var.trace('w', self.filter_projects)
        
        # Treeview for projects
        columns = ('Job Number', 'Assigned To', 'Start Date', 'Duration', 'Status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_project_select)
    
    def create_action_buttons(self):
        """Create action buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save Project", command=self.save_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Project", command=self.delete_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Refresh", command=self.load_projects).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Export JSON", command=self.export_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Import JSON", command=self.import_data).pack(side=tk.LEFT, padx=(0, 5))
    
    def load_dropdown_data(self):
        """Load data for dropdown menus"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Load designers
        cursor.execute("SELECT name FROM designers ORDER BY name")
        designers = [row[0] for row in cursor.fetchall()]
        self.assigned_to_combo['values'] = designers
        
        # Load engineers
        cursor.execute("SELECT name FROM engineers ORDER BY name")
        engineers = [row[0] for row in cursor.fetchall()]
        self.initial_engineer_combo['values'] = engineers
        
        conn.close()
    
    def load_projects(self):
        """Load projects from database"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT p.job_number, d.name, p.start_date, p.total_duration_days, 
               CASE WHEN p.completion_date IS NOT NULL THEN 'Completed' ELSE 'In Progress' END as status
        FROM projects p
        LEFT JOIN designers d ON p.assigned_to_id = d.id
        ORDER BY p.assignment_date DESC
        """
        
        cursor.execute(query)
        projects = cursor.fetchall()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert projects
        for project in projects:
            duration = f"{project[3]} days" if project[3] else "N/A"
            self.tree.insert('', 'end', values=(
                project[0], project[1] or "N/A", project[2] or "N/A", 
                duration, project[4]
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
    
    def on_project_select(self, event):
        """Handle project selection"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        job_number = item['values'][0]
        self.load_project_details(job_number)
    
    def load_project_details(self, job_number):
        """Load details for selected project"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT p.job_number, d.name, p.assignment_date, p.start_date, 
               p.completion_date, p.total_duration_days, p.released_to_dee
        FROM projects p
        LEFT JOIN designers d ON p.assigned_to_id = d.id
        WHERE p.job_number = ?
        """
        
        cursor.execute(query, (job_number,))
        project = cursor.fetchone()
        
        if project:
            self.job_number_var.set(project[0])
            self.assigned_to_var.set(project[1] or "")
            self.assignment_date_var.set(project[2] or "")
            self.start_date_var.set(project[3] or "")
            self.completion_date_var.set(project[4] or "")
            self.duration_var.set(f"{project[5]} days" if project[5] else "N/A")
            self.released_to_dee_var.set(project[6] or "")
        
        conn.close()
    
    def new_project(self):
        """Clear form for new project"""
        self.job_number_var.set("")
        self.assigned_to_var.set("")
        self.assignment_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.start_date_var.set("")
        self.completion_date_var.set("")
        self.duration_var.set("")
        self.released_to_dee_var.set("")
        self.initial_redline_var.set(False)
        self.initial_engineer_var.set("")
        self.initial_date_var.set("")
    
    def save_project(self):
        """Save project to database"""
        if not self.job_number_var.get():
            messagebox.showerror("Error", "Job number is required!")
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
            
            # Calculate duration
            duration = None
            if self.start_date_var.get() and self.completion_date_var.get():
                try:
                    start = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
                    end = datetime.strptime(self.completion_date_var.get(), "%Y-%m-%d")
                    duration = (end - start).days
                except ValueError:
                    pass
            
            # Insert or update project
            cursor.execute("""
                INSERT OR REPLACE INTO projects 
                (job_number, assigned_to_id, assignment_date, start_date, completion_date, 
                 total_duration_days, released_to_dee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.job_number_var.get(),
                designer_id,
                self.assignment_date_var.get() or None,
                self.start_date_var.get() or None,
                self.completion_date_var.get() or None,
                duration,
                self.released_to_dee_var.get() or None
            ))
            
            conn.commit()
            messagebox.showinfo("Success", "Project saved successfully!")
            self.load_projects()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
        finally:
            conn.close()
    
    def delete_project(self):
        """Delete selected project"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this project?"):
            item = self.tree.item(selection[0])
            job_number = item['values'][0]
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM projects WHERE job_number = ?", (job_number,))
                conn.commit()
                messagebox.showinfo("Success", "Project deleted successfully!")
                self.load_projects()
                self.new_project()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete project: {str(e)}")
            finally:
                conn.close()
    
    def calculate_duration(self, *args):
        """Calculate project duration"""
        start_date = self.start_date_var.get()
        completion_date = self.completion_date_var.get()
        
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
        if not self.start_date_var.get() and self.assignment_date_var.get():
            self.start_date_var.set(self.assignment_date_var.get())
    
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
