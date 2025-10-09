import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import sys
import os
from database_setup import DatabaseManager

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drafting Tools Dashboard")
        self.root.geometry("1000x700")
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        self.create_widgets()
        self.load_apps()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Header frame
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="Drafting Tools Dashboard", 
                               font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Status frame
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                foreground="green", font=('Arial', 10))
        status_label.grid(row=0, column=0)
        
        # Apps grid frame
        self.apps_frame = ttk.Frame(self.main_frame)
        self.apps_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.apps_frame.columnconfigure(0, weight=1)
        self.apps_frame.rowconfigure(0, weight=1)
        
        # Create scrollable frame for apps
        self.create_scrollable_apps()
        
        # Control frame
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Database info
        info_frame = ttk.LabelFrame(control_frame, text="Database Status", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.db_status_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.db_status_var).grid(row=0, column=0, sticky=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(button_frame, text="Refresh Apps", command=self.load_apps).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Manage App Order", command=self.open_app_order).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Backup Database", command=self.backup_database).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Export JSON", command=self.export_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Import JSON", command=self.import_data).pack(side=tk.LEFT, padx=(0, 5))
    
    def create_scrollable_apps(self):
        """Create scrollable frame for apps"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(self.apps_frame, bg='white')
        scrollbar = ttk.Scrollbar(self.apps_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def load_apps(self):
        """Load and display apps from database"""
        # Clear existing app buttons
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT app_name, display_order, is_active 
            FROM app_order 
            WHERE is_active = 1
            ORDER BY display_order
        """)
        apps = cursor.fetchall()
        
        # Create app buttons in a grid
        row = 0
        col = 0
        max_cols = 3
        
        for app in apps:
            app_name = app[0]
            self.create_app_button(app_name, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Update database status
        self.update_db_status()
        
        conn.close()
    
    def create_app_button(self, app_name, row, col):
        """Create a button for an app"""
        # Determine app details
        app_info = self.get_app_info(app_name)
        
        # Create button frame
        button_frame = ttk.LabelFrame(self.scrollable_frame, text=app_info['title'], 
                                    padding="10", width=250, height=150)
        button_frame.grid(row=row, column=col, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        button_frame.grid_propagate(False)
        
        # App description
        desc_label = ttk.Label(button_frame, text=app_info['description'], 
                              wraplength=200, justify='center')
        desc_label.grid(row=0, column=0, pady=(0, 10))
        
        # Launch button
        launch_button = ttk.Button(button_frame, text=f"Launch {app_name.title()}", 
                                  command=lambda: self.launch_app(app_name))
        launch_button.grid(row=1, column=0, pady=(0, 5))
        
        # Status indicator
        status_label = ttk.Label(button_frame, text=app_info['status'], 
                                foreground=app_info['status_color'])
        status_label.grid(row=2, column=0)
    
    def get_app_info(self, app_name):
        """Get information about an app"""
        app_info = {
            'projects': {
                'title': 'Project Management',
                'description': 'Manage drafting projects, track progress, and monitor completion status.',
                'status': 'Available',
                'status_color': 'green'
            },
            'app_order': {
                'title': 'App Order Manager',
                'description': 'Manage the display order and availability of dashboard apps.',
                'status': 'Available',
                'status_color': 'green'
            },
            'dashboard': {
                'title': 'Dashboard',
                'description': 'Main dashboard for accessing all drafting tools and applications.',
                'status': 'Current App',
                'status_color': 'blue'
            }
        }
        
        return app_info.get(app_name, {
            'title': app_name.title(),
            'description': f'Launch {app_name} application.',
            'status': 'Available',
            'status_color': 'green'
        })
    
    def launch_app(self, app_name):
        """Launch the selected app"""
        try:
            self.status_var.set(f"Launching {app_name}...")
            self.root.update()
            
            # Map app names to their Python files
            app_files = {
                'projects': 'projects.py',
                'app_order': 'app_order.py',
                'dashboard': 'dashboard.py'
            }
            
            if app_name in app_files:
                file_path = app_files[app_name]
                if os.path.exists(file_path):
                    # Launch the app in a new process
                    subprocess.Popen([sys.executable, file_path])
                    self.status_var.set(f"{app_name} launched successfully!")
                else:
                    messagebox.showerror("Error", f"App file {file_path} not found!")
                    self.status_var.set("Ready")
            else:
                messagebox.showerror("Error", f"Unknown app: {app_name}")
                self.status_var.set("Ready")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch {app_name}: {str(e)}")
            self.status_var.set("Ready")
    
    def open_app_order(self):
        """Open the app order manager"""
        self.launch_app('app_order')
    
    def backup_database(self):
        """Backup the database"""
        try:
            self.db_manager.backup_database()
            self.db_manager.export_to_json()
            messagebox.showinfo("Success", "Database backed up successfully!")
            self.status_var.set("Database backed up")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {str(e)}")
            self.status_var.set("Ready")
    
    def export_data(self):
        """Export data to JSON"""
        try:
            self.db_manager.export_to_json()
            messagebox.showinfo("Success", "Data exported to JSON successfully!")
            self.status_var.set("Data exported")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
            self.status_var.set("Ready")
    
    def import_data(self):
        """Import data from JSON"""
        try:
            self.db_manager.import_from_json()
            self.load_apps()
            messagebox.showinfo("Success", "Data imported from JSON successfully!")
            self.status_var.set("Data imported")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")
            self.status_var.set("Ready")
    
    def update_db_status(self):
        """Update database status information"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Get project count
        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]
        
        # Get app count
        cursor.execute("SELECT COUNT(*) FROM app_order WHERE is_active = 1")
        app_count = cursor.fetchone()[0]
        
        # Get last backup info
        backup_exists = os.path.exists(self.db_manager.master_db_path)
        json_exists = os.path.exists(self.db_manager.master_json_path)
        
        status_text = f"Projects: {project_count} | Active Apps: {app_count}"
        if backup_exists and json_exists:
            status_text += " | Backup: Available"
        else:
            status_text += " | Backup: Not Available"
        
        self.db_status_var.set(status_text)
        conn.close()
    
    def on_closing(self):
        """Handle application closing"""
        self.db_manager.backup_database()
        self.db_manager.export_to_json()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
