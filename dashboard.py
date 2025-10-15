import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import psutil
import sqlite3

class DashboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drafting Tools Dashboard")
        self.root.state('zoomed')  # Maximized window
        self.root.minsize(1200, 800)
        
        # Track child processes
        self.child_processes = []
        
        # Configure style
        self.setup_styles()
        
        # Create main interface
        self.create_widgets()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
        
        # Schedule periodic cleanup of finished processes
        self.schedule_cleanup()
        
        # Center the window
        self.center_window()
    
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
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = ttk.Label(title_frame, text="Drafting Tools Dashboard", 
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Project Management & Product Configuration Suite", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(5, 0))
        
        # Applications grid
        apps_frame = ttk.Frame(main_frame)
        apps_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        apps_frame.columnconfigure(0, weight=1)
        apps_frame.columnconfigure(1, weight=1)
        apps_frame.rowconfigure(0, weight=1)
        apps_frame.rowconfigure(1, weight=1)
        
        # Application buttons
        self.create_app_buttons(apps_frame)
        
        # Control buttons
        self.create_control_buttons(main_frame)
    
    def create_app_buttons(self, parent):
        """Create application launch buttons as custom tiles"""
        # Configure grid to have 2 columns
        for i in range(2):
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
        self.create_app_tile(parent, 1, 0, "🖨️", "Print Package Management", 
                           "Manage drawing print packages\nwith global search and print queue", 
                           self.launch_print_package)
        
        # Drafting Drawing Checklist
        self.create_app_tile(parent, 1, 1, "✅", "Drafting Drawing Checklist", 
                               "Quality control checklist for\ncommon drafting mistakes", 
                               self.launch_drafting_checklist)
    
    def create_app_tile(self, parent, row, col, icon, title, description, command):
        """Create a consistent app tile with icon, title, description, and counter"""
        # Create outer container for scale effect
        container = tk.Frame(parent, bg='#f5f5f5')
        container.grid(row=row, column=col, padx=15, pady=15, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tile frame with consistent size
        tile_frame = tk.Frame(container, relief='raised', borderwidth=2, 
                             bg='white', highlightthickness=1, highlightbackground='#d0d0d0')
        tile_frame.pack(fill=tk.BOTH, expand=True)
        
        # Set minimum size for consistency
        tile_frame.grid_propagate(False)
        tile_frame.config(width=280, height=180)
        
        # Create clickable button that fills the tile
        btn = tk.Button(tile_frame, relief='flat', bg='white', 
                       activebackground='#E8F0FE', bd=0, cursor='hand2',
                       command=command)
        btn.pack(fill=tk.BOTH, expand=True)
        
        # Icon
        icon_label = tk.Label(btn, text=icon, font=('Arial', 32), 
                            bg='white', fg='#3498db')
        icon_label.pack(pady=(15, 10))
        
        # Title
        title_label = tk.Label(btn, text=title, font=('Arial', 14, 'bold'), 
                             bg='white', fg='#2c3e50')
        title_label.pack(pady=(0, 8))
        
        # Description
        desc_label = tk.Label(btn, text=description, font=('Arial', 11), 
                            bg='white', fg='#7f8c8d', justify='center')
        desc_label.pack(pady=(0, 5))
        
        # Counter at bottom-right
        counter_text = self.get_tile_counter(title)
        counter_label = tk.Label(btn, text=counter_text, font=('Arial', 10, 'normal'), 
                               bg='white', fg='#555555', anchor='e')
        counter_label.pack(side=tk.BOTTOM, anchor='se', padx=8, pady=8)
        
        # Store references for hover effects
        all_widgets = [btn, icon_label, title_label, desc_label, counter_label]
        
        # Hover effects with scale and color change
        def on_enter(e):
            # Change background to light accent
            for widget in all_widgets:
                widget.config(bg='#E8F0FE')
            # Scale up effect (simulated by changing relief and border)
            tile_frame.config(relief='raised', borderwidth=3, highlightbackground='#3498db')
        
        def on_leave(e):
            # Restore original background
            for widget in all_widgets:
                widget.config(bg='white')
            # Restore original relief and border
            tile_frame.config(relief='raised', borderwidth=2, highlightbackground='#d0d0d0')
        
        # Bind hover events to all widgets
        for widget in all_widgets:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
    
    def get_tile_counter(self, tile_title):
        """Get dynamic counter for each tile"""
        try:
            conn = sqlite3.connect('drafting_tools.db')
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
                # Count configurations
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
            
            elif "Drafting Drawing Checklist" in tile_title:
                # Count active projects with checklist items
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
            
            else:
                conn.close()
                return ""
        except Exception as e:
            print(f"Error getting counter: {e}")
            return ""
    
    def create_control_buttons(self, parent):
        """Create control buttons at the bottom - right-aligned, evenly spaced"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(30, 0))
        
        # Create a right-aligned container for buttons
        button_container = ttk.Frame(control_frame)
        button_container.pack(side=tk.RIGHT)
        
        # All buttons right-aligned with consistent sizing and spacing
        about_btn = ttk.Button(button_container, text="About", 
                              command=self.show_about, style='Control.TButton')
        about_btn.pack(side=tk.LEFT, padx=5)
        
        running_btn = ttk.Button(button_container, text="Show Running Apps", 
                                command=self.show_running_apps, style='Control.TButton')
        running_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = ttk.Button(button_container, text="Exit Application", 
                             command=self.exit_application, style='Control.TButton')
        exit_btn.pack(side=tk.LEFT, padx=5)
    
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
            # Get list of currently running related processes
            running_processes = self.get_running_related_processes()
            
            if running_processes:
                process_list = "\n".join([f"• {proc.info.get('name', 'Unknown')} (PID: {proc.info.get('pid', 'Unknown')})" for proc in running_processes])
                message = f"Are you sure you want to exit the Drafting Tools Suite?\n\nThis will close all open applications:\n\n{process_list}\n\nContinue?"
            else:
                message = "Are you sure you want to exit the Drafting Tools Suite?"
            
            if messagebox.askyesno("Exit Application", message):
                # Find and close all related processes
                self.close_all_related_processes()
                
                # Close the main window
                self.root.quit()
        except Exception as e:
            print(f"Error in exit_application: {e}")
            # Fallback: just close the main window
            self.root.quit()
    
    def get_running_related_processes(self):
        """Get list of currently running related processes"""
        try:
            current_pid = os.getpid()
            related_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline:
                            cmdline_str = ' '.join(cmdline).lower()
                            # More flexible matching - look for our script names anywhere in the command line
                            if any(script in cmdline_str for script in ['projects.py', 'product_configurations.py', 'print_package.py', 'dashboard.py']):
                                if proc.info['pid'] != current_pid:  # Don't include ourselves
                                    related_processes.append(proc)
                                    print(f"Found related process: PID {proc.info['pid']} - {cmdline_str}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
                    continue
            
            return related_processes
        except Exception as e:
            print(f"Error getting running processes: {e}")
            return []
    
    def close_all_related_processes(self):
        """Find and close all related drafting tools processes"""
        try:
            # Get current process ID to avoid closing ourselves
            current_pid = os.getpid()
            print(f"Current PID: {current_pid}")
            
            # Find all Python processes running our scripts
            related_processes = []
            all_python_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            all_python_processes.append(f"PID {proc.info['pid']}: {cmdline_str}")
                            
                            # More flexible matching - look for our script names anywhere in the command line
                            if any(script in cmdline_str.lower() for script in ['projects.py', 'product_configurations.py', 'print_package.py', 'dashboard.py']):
                                if proc.info['pid'] != current_pid:  # Don't close ourselves
                                    related_processes.append(proc)
                                    print(f"Found related process: PID {proc.info['pid']} - {cmdline_str}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
                    continue
            
            # Also try to find by window title (Windows-specific)
            try:
                import win32gui
                import win32process
                
                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if any(title in window_title for title in ['Product Configurations', 'Project Management', 'Print Package Management', 'Drafting Tools']):
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            if pid != current_pid:
                                # Find the process object
                                for proc in psutil.process_iter(['pid']):
                                    if proc.info['pid'] == pid:
                                        if proc not in related_processes:
                                            related_processes.append(proc)
                                            print(f"Found by window title: PID {pid} - {window_title}")
                                        break
                    return True
                
                win32gui.EnumWindows(enum_windows_callback, [])
            except ImportError:
                print("win32gui not available, skipping window title detection")
            except Exception as e:
                print(f"Error in window title detection: {e}")
            
            print(f"All Python processes found:")
            for proc_info in all_python_processes:
                print(f"  {proc_info}")
            
            print(f"Related processes to close: {len(related_processes)}")
            
            # Close all related processes
            for proc in related_processes:
                try:
                    print(f"Attempting to close process: {proc.info['pid']} - {' '.join(proc.info['cmdline'])}")
                    proc.terminate()
                    # Give it a moment to close gracefully
                    try:
                        proc.wait(timeout=3)
                        print(f"Successfully closed process: {proc.info['pid']}")
                    except psutil.TimeoutExpired:
                        # Force kill if it doesn't close gracefully
                        print(f"Force killing process: {proc.info['pid']}")
                        proc.kill()
                        print(f"Force killed process: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    print(f"Error closing process {proc.info['pid']}: {e}")
            
            print(f"Closed {len(related_processes)} related processes")
            
            # If no processes were found, try a more aggressive approach
            if len(related_processes) == 0:
                print("No processes found with standard detection, trying aggressive approach...")
                self.aggressive_process_cleanup(current_pid)
            
        except Exception as e:
            print(f"Error finding related processes: {e}")
            # Fallback: try to close tracked processes
            for process in self.child_processes:
                try:
                    if process.poll() is None:  # Process is still running
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                except Exception as e:
                    print(f"Error closing tracked process: {e}")
            
            self.child_processes.clear()
    
    def aggressive_process_cleanup(self, current_pid):
        """More aggressive approach to find and close related processes"""
        try:
            print("Attempting aggressive process cleanup...")
            killed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        if proc.info['pid'] != current_pid:
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline:
                                cmdline_str = ' '.join(cmdline)
                                # Look for any indication this might be our app
                                if any(indicator in cmdline_str.lower() for indicator in [
                                    'product_configurations', 'projects', 'print_package', 'dashboard',
                                    'drafting', 'tkinter', 'gui'
                                ]):
                                    print(f"Aggressively closing: PID {proc.info['pid']} - {cmdline_str}")
                                    proc.terminate()
                                    try:
                                        proc.wait(timeout=2)
                                        killed_count += 1
                                    except psutil.TimeoutExpired:
                                        proc.kill()
                                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
                    continue
            
            print(f"Aggressive cleanup killed {killed_count} processes")
            
        except Exception as e:
            print(f"Error in aggressive cleanup: {e}")
    
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