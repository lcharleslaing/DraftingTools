import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import sqlite3
from db_utils import get_connection
from settings import SettingsManager
from help_utils import show_help

class DashboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drafting Tools Dashboard")
        self.root.state('zoomed')  # Maximized window
        self.root.minsize(1200, 800)
        
        # Track child processes
        self.child_processes = []
        
        # Initialize settings manager
        self.settings_manager = SettingsManager()
        
        # Configure style
        self.setup_styles()
        
        # CREATE BUTTONS FIRST - BEFORE ANYTHING ELSE
        self.create_buttons_immediately()
        
        # Create main interface
        self.create_widgets()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
        
        # Schedule periodic cleanup of finished processes
        self.schedule_cleanup()
        
        # Center the window
        self.center_window()
    
    def create_buttons_immediately(self):
        """Create buttons immediately on root window - GUARANTEED TO WORK"""
        # Create a simple frame for buttons
        self.button_frame = tk.Frame(self.root, bg='red', height=60)  # Red background to make it visible
        self.button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # Create buttons with bright colors to make them visible
        self.about_btn = tk.Button(self.button_frame, text="ABOUT", 
                                  command=self.show_about, 
                                  bg='yellow', fg='black', font=('Arial', 12, 'bold'))
        self.about_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        self.running_btn = tk.Button(self.button_frame, text="RUNNING APPS", 
                                    command=self.show_running_apps, 
                                    bg='orange', fg='black', font=('Arial', 12, 'bold'))
        self.running_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        self.exit_btn = tk.Button(self.button_frame, text="EXIT", 
                                 command=self.exit_application, 
                                 bg='red', fg='white', font=('Arial', 12, 'bold'))
        self.exit_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        print("IMMEDIATE buttons created with bright colors - they MUST be visible!")
    
    def update_user_display(self):
        """Update the user display in the header"""
        current_user = self.settings_manager.current_user
        current_dept = self.settings_manager.current_department
        
        if current_user:
            display_text = f"User: {current_user}"
            if current_dept:
                display_text += f" ({current_dept})"
            self.user_label.config(text=display_text)
        else:
            self.user_label.config(text="User: Not Set")
    
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
    
    def setup_styles(self):
        """Setup custom styles for the dashboard"""
        style = ttk.Style()
        
        # Configure control button styles (bottom buttons)
        style.configure('Control.TButton', 
                       font=('Arial', 11),
                       padding=(15, 8),
                       width=15)
        
        # Configure app tile styles
        style.configure('AppTile.TFrame',
                       relief='raised',
                       borderwidth=2)
        
        # Configure frame styles
        style.configure('Title.TLabel',
                       font=('Arial', 24, 'bold'),
                       foreground='darkblue')
        
        style.configure('Subtitle.TLabel',
                       font=('Arial', 16),
                       foreground='darkgray')
        
        # App tile title style
        style.configure('TileTitle.TLabel',
                       font=('Arial', 14, 'bold'),
                       foreground='#2c3e50')
        
        # App tile description style
        style.configure('TileDesc.TLabel',
                       font=('Arial', 11),
                       foreground='#7f8c8d')
    
    def create_widgets(self):
        """Create the main dashboard widgets"""
        # Create a simple layout with buttons at the bottom
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        title_label = ttk.Label(header_frame, text="Drafting Tools Dashboard", 
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Project Management & Product Configuration Suite", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # User info
        user_frame = ttk.Frame(header_frame)
        user_frame.pack(side=tk.RIGHT)
        
        self.user_label = ttk.Label(user_frame, text="User: Not Set", 
                                   font=('Arial', 12, 'bold'))
        self.user_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        settings_btn = ttk.Button(user_frame, text="⚙️ Settings", 
                                 command=self.open_settings)
        settings_btn.pack(side=tk.RIGHT)
        
        self.update_user_display()
        # Help button
        ttk.Button(header_frame, text='Help', command=lambda: show_help(self.root, 'Dashboard', 'Click tiles to open apps. Use the bottom controls to view running apps or exit. The app bar provides navigation across apps.')).pack(pady=(6,0))
        
        # Apps container
        apps_container = ttk.Frame(self.root)
        apps_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Apps grid
        apps_frame = ttk.Frame(apps_container)
        apps_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid
        for i in range(3):
            apps_frame.columnconfigure(i, weight=1)
        for i in range(4):
            apps_frame.rowconfigure(i, weight=1)
        
        self.create_app_buttons(apps_frame)
        
        # Control buttons are already created in __init__
    
    def create_app_buttons(self, parent):
        """Create application launch buttons as custom tiles"""
        # Configure grid to have 3 columns
        for i in range(3):
            parent.columnconfigure(i, weight=1, uniform="tile")
        
        # Projects Management
        self.create_app_tile(parent, 0, 0, "📋", "Projects Management", 
                           "Track project workflows,\njob numbers, and customer details", 
                           self.launch_projects)
        
        # Product Configurations
        self.create_app_tile(parent, 0, 1, "⚙️", "Product Configurations", 
                           "Heater, Tank & Pump configuration\nmanagement and specifications", 
                           self.launch_configurations)
        
        # Print Package Management
        self.create_app_tile(parent, 0, 2, "🖨️", "Print Package Management", 
                           "Manage drawing print packages\nwith global search and print queue", 
                           self.launch_print_package)
        
        # D365 Import Formatter
        self.create_app_tile(parent, 1, 0, "📊", "D365 Import Formatter", 
                               "Generate D365 BOM import data\nwith Excel-like calculations", 
                               self.launch_d365_import)
        
        # Project File Monitor
        self.create_app_tile(parent, 1, 1, "🔍", "Project File Monitor", 
                               "Monitor file changes and recreate\nproject structures for testing", 
                               self.launch_project_monitor)
        
        # Drawing Reviews
        self.create_app_tile(parent, 1, 2, "📝", "Drawing Reviews", 
                               "Digital drawing review and markup\nwith tablet support and audit trail", 
                               self.launch_drawing_reviews)
        
        # Drafting Drawing Checklist
        self.create_app_tile(parent, 2, 0, "✅", "Drafting Drawing Checklist", 
                               "Quality control checklist for\ncommon drafting mistakes", 
                               self.launch_drafting_checklist)
        
        # Project Resource Allocation
        self.create_app_tile(parent, 2, 1, "📊", "Project Resource Allocation", 
                               "Strategic logging and tracking\nof resource allocation per customer", 
                               self.launch_resource_allocation)
        
        # Workflow Manager
        self.create_app_tile(parent, 2, 2, "⚙️", "Workflow Manager", 
                               "Manage Print Package Review\nworkflows and stage transitions", 
                               self.launch_workflow_manager)
        
        # Coil Verification Tool
        self.create_app_tile(parent, 3, 0, "🔍", "Coil Verification Tool", 
                               "Search and verify coil part numbers\nby Heater/Tank, Material & Diameter", 
                               self.launch_coil_verification)
        
        # Reserved placeholder for future app
    
    def create_app_tile(self, parent, row, col, icon, title, description, command):
        """Create a simple button with formatted title"""
        # Create a frame to hold the button content
        btn_frame = tk.Frame(parent, relief='raised', borderwidth=2, bg='white')
        btn_frame.grid(row=row, column=col, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Make the entire frame clickable
        def on_click(event):
            command()
        
        btn_frame.bind('<Button-1>', on_click)
        btn_frame.bind('<Enter>', lambda e: btn_frame.config(cursor='hand2'))
        btn_frame.bind('<Leave>', lambda e: btn_frame.config(cursor=''))
        
        # Icon (larger)
        icon_label = tk.Label(btn_frame, text=icon, font=('Arial', 24), bg='white')
        icon_label.pack(pady=(10, 5))
        
        # Title (bold and larger)
        title_label = tk.Label(btn_frame, text=title, font=('Arial', 14, 'bold'), bg='white')
        title_label.pack(pady=(0, 5))
        title_label.bind('<Button-1>', on_click)
        title_label.bind('<Enter>', lambda e: btn_frame.config(cursor='hand2'))
        title_label.bind('<Leave>', lambda e: btn_frame.config(cursor=''))
        
        # Description (normal size, non-bold)
        desc_label = tk.Label(btn_frame, text=description, font=('Arial', 10), 
                             bg='white', wraplength=200, justify='center')
        desc_label.pack(pady=(0, 10))
        desc_label.bind('<Button-1>', on_click)
        desc_label.bind('<Enter>', lambda e: btn_frame.config(cursor='hand2'))
        desc_label.bind('<Leave>', lambda e: btn_frame.config(cursor=''))
    
    def get_tile_counter(self, tile_title):
        """Get dynamic counter for each tile"""
        try:
            conn = get_connection('drafting_tools.db')
            cursor = conn.cursor()
            
            if "Projects Management" in tile_title:
                # Count active projects (not completed) based on release_to_dee/completion
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM projects p
                    LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                    WHERE NOT (
                        (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                        OR rd.is_completed = 1
                        OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                    )
                """)
                count = cursor.fetchone()[0]
                conn.close()
                return f"{count} Active Project{'s' if count != 1 else ''}"
            
            elif "Product Configurations" in tile_title:
                # Count configurations, guard table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='heater_configurations'")
                if cursor.fetchone() is None:
                    conn.close()
                    return "0 Configurations"
                cursor.execute("SELECT COUNT(DISTINCT job_number) FROM heater_configurations")
                count = cursor.fetchone()[0]
                conn.close()
                return f"{count} Configuration{'s' if count != 1 else ''}"
            
            elif "Print Package" in tile_title:
                # Count jobs that have drawings (i.e., print packages)
                # Prefer the 'drawings' table if it exists; otherwise fall back to 'print_packages'
                try:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='drawings'
                    """)
                    drawings_exists = cursor.fetchone() is not None

                    if drawings_exists:
                        cursor.execute("SELECT COUNT(DISTINCT job_number) FROM drawings")
                        count = cursor.fetchone()[0]
                    else:
                        cursor.execute("""
                            SELECT name FROM sqlite_master 
                            WHERE type='table' AND name='print_packages'
                        """)
                        print_packages_exists = cursor.fetchone() is not None
                        if print_packages_exists:
                            cursor.execute("SELECT COUNT(DISTINCT job_number) FROM print_packages")
                            count = cursor.fetchone()[0]
                        else:
                            count = 0
                finally:
                    conn.close()
                return f"{count} Print Package{'s' if count != 1 else ''}"
            
            elif "D365 Import Formatter" in tile_title:
                # Count D365 import configurations, guard table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='d365_import_configs'")
                if cursor.fetchone() is None:
                    conn.close()
                    return "0 Configurations"
                cursor.execute("SELECT COUNT(DISTINCT job_number) FROM d365_import_configs")
                count = cursor.fetchone()[0]
                conn.close()
                return f"{count} Configuration{'s' if count != 1 else ''}"
            
            elif "Drafting Drawing Checklist" in tile_title:
                # Count active projects with checklist items, guard table existence
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_checklist_status'")
                if cursor.fetchone() is None:
                    conn.close()
                    return "0 Active Projects"
                cursor.execute("""
                    SELECT COUNT(DISTINCT p.job_number)
                    FROM projects p
                    LEFT JOIN release_to_dee rd ON rd.project_id = p.id
                    LEFT JOIN project_checklist_status pcs ON p.job_number = pcs.job_number
                    WHERE NOT (
                        (COALESCE(p.released_to_dee, rd.release_date) IS NOT NULL AND COALESCE(p.released_to_dee, rd.release_date) != '')
                        OR rd.is_completed = 1
                        OR (p.completion_date IS NOT NULL AND p.completion_date != '')
                    )
                    AND pcs.job_number IS NOT NULL
                """)
                count = cursor.fetchone()[0]
                conn.close()
                return f"{count} Active Project{'s' if count != 1 else ''}"
            
            elif "Coil Verification Tool" in tile_title:
                # Count coil specifications in the verification database
                try:
                    coil_conn = sqlite3.connect('coil_verification.db')
                    coil_cursor = coil_conn.cursor()
                    coil_cursor.execute("SELECT COUNT(*) FROM coil_specifications")
                    count = coil_cursor.fetchone()[0]
                    coil_conn.close()
                    return f"{count} Coil Spec{'s' if count != 1 else ''}"
                except:
                    return "Database Not Ready"
            
            else:
                conn.close()
                return ""
        except Exception as e:
            print(f"Error getting counter: {e}")
            return ""
    
    
    
    def launch_projects(self):
        """Launch the Projects Management application"""
        try:
            if os.path.exists('projects.py'):
                process = subprocess.Popen([sys.executable, 'projects.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "projects.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Projects Management:\n{str(e)}")
    
    def launch_configurations(self):
        """Launch the Product Configurations application"""
        try:
            if os.path.exists('product_configurations.py'):
                process = subprocess.Popen([sys.executable, 'product_configurations.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "product_configurations.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Product Configurations:\n{str(e)}")
    
    def launch_print_package(self):
        """Launch the Print Package Management application"""
        try:
            if os.path.exists('print_package.py'):
                process = subprocess.Popen([sys.executable, 'print_package.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "print_package.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Print Package Management:\n{str(e)}")

    def launch_d365_import(self):
        """Launch the D365 Import Formatter application"""
        try:
            if os.path.exists('d365_import_formatter.py'):
                process = subprocess.Popen([sys.executable, 'd365_import_formatter.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "d365_import_formatter.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch D365 Import Formatter:\n{str(e)}")
    
    def launch_drafting_checklist(self):
        """Launch the Drafting Drawing Checklist application"""
        try:
            if os.path.exists('drafting_items_to_look_for.py'):
                process = subprocess.Popen([sys.executable, 'drafting_items_to_look_for.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "drafting_items_to_look_for.py not found in current directory")
        except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Drafting Drawing Checklist:\n{str(e)}")
    
    def launch_project_monitor(self):
        """Launch the Project File Monitor application"""
        try:
            if os.path.exists('project_monitor.py'):
                process = subprocess.Popen([sys.executable, 'project_monitor.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "project_monitor.py not found in current directory")
        except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Project File Monitor:\n{str(e)}")
    
    def launch_drawing_reviews(self):
        """Launch the Drawing Reviews application"""
        try:
            if os.path.exists('drawing_reviews.py'):
                process = subprocess.Popen([sys.executable, 'drawing_reviews.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "drawing_reviews.py not found in current directory")
        except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Drawing Reviews:\n{str(e)}")
    
    def launch_resource_allocation(self):
        """Launch the Project Resource Allocation application"""
        try:
            if os.path.exists('resource_allocation.py'):
                process = subprocess.Popen([sys.executable, 'resource_allocation.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showinfo("Coming Soon", "Project Resource Allocation app is in development!\n\nThis will track:\n• Time spent per customer\n• File-based activity logging\n• Resource allocation analytics\n• Strategic insights")
        except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Resource Allocation:\n{str(e)}")
    
    def launch_workflow_manager(self):
        """Launch the Workflow Manager application"""
        try:
            if os.path.exists('workflow_manager.py'):
                process = subprocess.Popen([sys.executable, 'workflow_manager.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "workflow_manager.py not found in current directory")
        except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Workflow Manager:\n{str(e)}")
    
    def launch_coil_verification(self):
        """Launch the Coil Verification Tool application"""
        try:
            if os.path.exists('coil_verification_tool.py'):
                process = subprocess.Popen([sys.executable, 'coil_verification_tool.py'])
                self.child_processes.append(process)
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "coil_verification_tool.py not found in current directory")
        except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Coil Verification Tool:\n{str(e)}")
    
    def cleanup_finished_processes(self):
        """Remove finished processes from the tracking list"""
        self.child_processes = [p for p in self.child_processes if p.poll() is None]
    
    def schedule_cleanup(self):
        """Schedule periodic cleanup of finished processes"""
        self.cleanup_finished_processes()
        # Schedule next cleanup in 5 seconds
        self.root.after(5000, self.schedule_cleanup)
    
    def launch_db_management(self):
        """Launch database management (placeholder)"""
        messagebox.showinfo("Database Management", 
                           "Database management features:\n\n"
                           "• Automatic backup on app exit\n"
                           "• Data export to JSON\n"
                           "• Database cleanup and maintenance\n"
                           "• Master database synchronization\n\n"
                           "These features are built into each application.")
    
    def show_coming_soon(self):
        """Show coming soon message"""
        messagebox.showinfo("Coming Soon", 
                           "Additional drafting tools will be added:\n\n"
                           "• Drawing management\n"
                           "• Material specifications\n"
                           "• Cost estimation tools\n"
                           "• Report generation\n\n"
                           "Stay tuned for updates!")
    
    def launch_shit_bricks_sideways(self):
        """Placeholder launcher for SHIT BRICKS SIDEWAYS tile"""
        self.show_coming_soon()
    
    def get_running_related_processes(self):
        """Get list of running processes related to drafting tools"""
        try:
            import psutil
            related_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline_str = ' '.join(proc.info['cmdline'])
                        if any(app in cmdline_str for app in ['projects.py', 'product_configurations.py', 
                                                             'print_package.py', 'd365_import_formatter.py',
                                                             'drafting_items_to_look_for.py', 'project_monitor.py',
                                                             'drawing_reviews.py', 'workflow_manager.py']):
                            related_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return related_processes
        except ImportError:
            # Fallback if psutil is not available
            return []
    
    def show_running_apps(self):
        """Show currently running applications"""
        running_processes = self.get_running_related_processes()
        
        if running_processes:
            process_list = []
            for proc in running_processes:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else 'Unknown'
                process_list.append(f"• {proc.info['name']} (PID: {proc.info['pid']})\n  {cmdline}")
            
            message = f"Currently Running Applications:\n\n" + "\n\n".join(process_list)
        else:
            message = "No Drafting Tools applications are currently running.\n\nOnly the Dashboard is active."
        
        messagebox.showinfo("Running Applications", message)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
Drafting Tools Suite v1.0

A comprehensive project management and product configuration system for drafting workflows.

Features:
• Project workflow tracking
• Job number management
• Customer information management
• Product configuration (Heater, Tank, Pump)
• Database integration
• Full-screen applications
• Export/Import capabilities
• Process management - closes all apps when exiting

Developed for CECO Environmental Corp
        """
        messagebox.showinfo("About Drafting Tools Suite", about_text)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        else:
            self.root.attributes('-fullscreen', True)
    
    def exit_application(self):
        """Exit the application and close all related windows"""
        try:
            # Simple confirmation dialog
            if messagebox.askyesno("Exit Application", "Are you sure you want to exit the Drafting Tools Suite?"):
                # Close tracked child processes first
                self.close_tracked_processes()
                # Also close any other related processes detected via psutil
                try:
                    for proc in self.get_running_related_processes():
                        try:
                            proc.terminate()
                            proc.wait(timeout=2)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                except Exception:
                    pass
                
                # Close the main window
                self.root.quit()
        except Exception as e:
            print(f"Error in exit_application: {e}")
            # Fallback: just close the main window
            self.root.quit()
    
    def close_tracked_processes(self):
        """Close all tracked child processes (simple and safe approach)"""
        try:
            for process in self.child_processes:
                try:
                    if process.poll() is None:  # Process is still running
                        print(f"Closing tracked process: {process.pid}")
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                            print(f"Successfully closed tracked process: {process.pid}")
                        except subprocess.TimeoutExpired:
                            print(f"Force killing tracked process: {process.pid}")
                            process.kill()
                except Exception as e:
                    print(f"Error closing tracked process {process.pid}: {e}")
            
            self.child_processes.clear()
        except Exception as e:
            print(f"Error closing tracked processes: {e}")
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def run(self):
        """Run the dashboard application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
