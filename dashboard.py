import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import psutil

class DashboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drafting Tools Dashboard")
        self.root.state('zoomed')  # Full screen
        self.root.minsize(1200, 800)
        # Make fullscreen the default but keep window controls
        self.root.attributes('-fullscreen', True)
        
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
        
        # Configure button styles
        style.configure('Dashboard.TButton', 
                       font=('Arial', 12, 'bold'),
                       padding=(20, 15))
        
        style.configure('App.TButton',
                       font=('Arial', 14, 'bold'),
                       padding=(30, 20))
        
        # Configure frame styles
        style.configure('Title.TLabel',
                       font=('Arial', 24, 'bold'),
                       foreground='darkblue')
        
        style.configure('Subtitle.TLabel',
                       font=('Arial', 16),
                       foreground='darkgray')
    
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
        """Create application launch buttons"""
        # Projects Management
        projects_btn = ttk.Button(parent, text="📋 Projects Management\n\nTrack project workflows,\njob numbers, and\ncustomer details", 
                                 command=self.launch_projects, style='App.TButton')
        projects_btn.grid(row=0, column=0, padx=20, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Product Configurations
        config_btn = ttk.Button(parent, text="⚙️ Product Configurations\n\nHeater, Tank & Pump\nconfiguration management\nand specifications", 
                               command=self.launch_configurations, style='App.TButton')
        config_btn.grid(row=0, column=1, padx=20, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Placeholder for future apps
        future_btn = ttk.Button(parent, text="🔧 Additional Tools\n\nMore drafting tools\ncoming soon...", 
                               command=self.show_coming_soon, style='App.TButton')
        future_btn.grid(row=1, column=0, padx=20, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Database Management
        db_btn = ttk.Button(parent, text="🗄️ Database Management\n\nBackup, restore, and\nmaintain database", 
                           command=self.launch_db_management, style='App.TButton')
        db_btn.grid(row=1, column=1, padx=20, pady=20, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def create_control_buttons(self, parent):
        """Create control buttons at the bottom"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Exit fullscreen button
        exit_fullscreen_btn = ttk.Button(control_frame, text="Exit Fullscreen", 
                                        command=self.toggle_fullscreen, style='Dashboard.TButton')
        exit_fullscreen_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Exit application button
        exit_btn = ttk.Button(control_frame, text="Exit Application", 
                             command=self.exit_application, style='Dashboard.TButton')
        exit_btn.pack(side=tk.RIGHT)
        
        # Show running apps button
        running_btn = ttk.Button(control_frame, text="Show Running Apps", 
                                command=self.show_running_apps, style='Dashboard.TButton')
        running_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # About button
        about_btn = ttk.Button(control_frame, text="About", 
                              command=self.show_about, style='Dashboard.TButton')
        about_btn.pack(side=tk.RIGHT, padx=(0, 10))
    
    def launch_projects(self):
        """Launch the Projects Management application"""
        try:
            # Check if projects.py exists
            if os.path.exists('projects.py'):
                process = subprocess.Popen([sys.executable, 'projects.py'])
                self.child_processes.append(process)
                # Clean up finished processes
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "projects.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Projects Management:\n{str(e)}")
    
    def launch_configurations(self):
        """Launch the Product Configurations application"""
        try:
            # Check if product_configurations.py exists
            if os.path.exists('product_configurations.py'):
                process = subprocess.Popen([sys.executable, 'product_configurations.py'])
                self.child_processes.append(process)
                # Clean up finished processes
                self.cleanup_finished_processes()
            else:
                messagebox.showerror("Error", "product_configurations.py not found in current directory")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Product Configurations:\n{str(e)}")
    
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
        # Get list of currently running related processes
        running_processes = self.get_running_related_processes()
        
        if running_processes:
            process_list = "\n".join([f"• {proc.info['name']} (PID: {proc.info['pid']})" for proc in running_processes])
            message = f"Are you sure you want to exit the Drafting Tools Suite?\n\nThis will close all open applications:\n\n{process_list}\n\nContinue?"
        else:
            message = "Are you sure you want to exit the Drafting Tools Suite?"
        
        if messagebox.askyesno("Exit Application", message):
            # Find and close all related processes
            self.close_all_related_processes()
            
            # Close the main window
            self.root.quit()
    
    def get_running_related_processes(self):
        """Get list of currently running related processes"""
        try:
            current_pid = os.getpid()
            related_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmdline_str = ' '.join(cmdline).lower()
                            # More flexible matching - look for our script names anywhere in the command line
                            if any(script in cmdline_str for script in ['projects.py', 'product_configurations.py', 'dashboard.py']):
                                if proc.info['pid'] != current_pid:  # Don't include ourselves
                                    related_processes.append(proc)
                                    print(f"Found related process: PID {proc.info['pid']} - {cmdline_str}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
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
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            all_python_processes.append(f"PID {proc.info['pid']}: {cmdline_str}")
                            
                            # More flexible matching - look for our script names anywhere in the command line
                            if any(script in cmdline_str.lower() for script in ['projects.py', 'product_configurations.py', 'dashboard.py']):
                                if proc.info['pid'] != current_pid:  # Don't close ourselves
                                    related_processes.append(proc)
                                    print(f"Found related process: PID {proc.info['pid']} - {cmdline_str}")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Also try to find by window title (Windows-specific)
            try:
                import win32gui
                import win32process
                
                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if any(title in window_title for title in ['Product Configurations', 'Project Management', 'Drafting Tools']):
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
                            cmdline = proc.info['cmdline']
                            if cmdline:
                                cmdline_str = ' '.join(cmdline)
                                # Look for any indication this might be our app
                                if any(indicator in cmdline_str.lower() for indicator in [
                                    'product_configurations', 'projects', 'dashboard',
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
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
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