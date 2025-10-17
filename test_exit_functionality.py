#!/usr/bin/env python3
"""
Test script to verify the exit functionality works properly
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import time
import psutil
import sqlite3

class TestExitApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Test Exit Functionality")
        self.root.geometry("400x300")
        
        # Track child processes
        self.child_processes = []
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create test widgets"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Exit Functionality Test", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = ttk.Label(main_frame, text="This app tests the improved exit functionality.\nClick 'Start Test Process' to launch a child process,\nthen click 'Test Exit' to test the cleanup.", 
                              justify="center")
        desc_label.pack(pady=(0, 20))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Start Test Process", command=self.start_test_process).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Test Exit", command=self.test_exit).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=self.root.quit).pack(side="left", padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=20)
        
    def start_test_process(self):
        """Start a test child process"""
        try:
            # Start a simple Python process that will run for a while
            process = subprocess.Popen([sys.executable, "-c", 
                "import time; print('Test process started'); time.sleep(30); print('Test process finished')"])
            self.child_processes.append(process)
            self.status_var.set(f"Started test process (PID: {process.pid})")
        except Exception as e:
            self.status_var.set(f"Error starting process: {e}")
    
    def test_exit(self):
        """Test the exit functionality"""
        try:
            # Get list of running related processes
            running_processes = self.get_running_related_processes()
            
            if running_processes:
                process_list = "\n".join([f"• {proc.info.get('name', 'Unknown')} (PID: {proc.info.get('pid', 'Unknown')})" for proc in running_processes])
                message = f"Test Exit - This will close all test processes:\n\n{process_list}\n\nContinue?"
            else:
                message = "Test Exit - No processes found to close.\n\nContinue?"
            
            if messagebox.askyesno("Test Exit", message):
                # Show progress dialog
                self.show_exit_progress()
                
                # Find and close all related processes
                self.close_all_related_processes()
                
                # Hide progress dialog
                self.hide_exit_progress()
                
                self.status_var.set("Exit test completed successfully!")
        except Exception as e:
            self.status_var.set(f"Error in test exit: {e}")
    
    def get_running_related_processes(self):
        """Get list of currently running related processes"""
        try:
            current_pid = os.getpid()
            related_processes = []
            
            # Use a more conservative approach to avoid permission errors
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        pid = proc.info['pid']
                        if pid != current_pid:
                            # Get command line safely with timeout protection
                            try:
                                cmdline = proc.cmdline()
                                if cmdline:
                                    cmdline_str = ' '.join(cmdline).lower()
                                    # Look for our test processes
                                    if 'test_exit_functionality.py' in cmdline_str or 'time.sleep' in cmdline_str:
                                        related_processes.append(proc)
                                        print(f"Found related process: PID {pid} - {cmdline_str}")
                            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.TimeoutExpired):
                                # Skip processes we can't access
                                continue
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
                    continue
            
            return related_processes
        except Exception as e:
            print(f"Error getting running processes: {e}")
            return []
    
    def close_all_related_processes(self):
        """Find and close all related processes"""
        try:
            # Get current process ID to avoid closing ourselves
            current_pid = os.getpid()
            print(f"Current PID: {current_pid}")
            
            # First, try to close tracked child processes
            self.close_tracked_processes()
            
            # Find processes by command line (safer approach) with timeout
            related_pids = self.find_related_processes_by_cmdline(current_pid)
            
            # Combine and deduplicate PIDs
            all_pids = list(set(related_pids))
            
            print(f"Found {len(all_pids)} related processes to close: {all_pids}")
            
            # Close all found processes with overall timeout
            closed_count = 0
            start_time = time.time()
            timeout_seconds = 10  # Maximum 10 seconds for process cleanup
            
            for pid in all_pids:
                # Check if we've exceeded timeout
                if time.time() - start_time > timeout_seconds:
                    print(f"Timeout reached, stopping process cleanup")
                    break
                
                if self.close_process_by_pid(pid):
                    closed_count += 1
            
            print(f"Successfully closed {closed_count} processes")
            
        except Exception as e:
            print(f"Error in close_all_related_processes: {e}")
            # Fallback: just close tracked processes
            self.close_tracked_processes()
    
    def close_tracked_processes(self):
        """Close all tracked child processes"""
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
    
    def find_related_processes_by_cmdline(self, current_pid):
        """Find related processes by examining command lines"""
        related_pids = []
        try:
            # Use a more conservative approach to avoid permission errors
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        pid = proc.info['pid']
                        if pid != current_pid:
                            # Get command line safely
                            try:
                                cmdline = proc.cmdline()
                                if cmdline:
                                    cmdline_str = ' '.join(cmdline).lower()
                                    if any(script in cmdline_str for script in [
                                        'test_exit_functionality.py', 'time.sleep'
                                    ]):
                                        related_pids.append(pid)
                                        print(f"Found related process by cmdline: PID {pid}")
                            except (psutil.AccessDenied, psutil.NoSuchProcess):
                                continue
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"Error finding processes by cmdline: {e}")
        
        return related_pids
    
    def close_process_by_pid(self, pid):
        """Safely close a process by PID"""
        try:
            proc = psutil.Process(pid)
            print(f"Attempting to close process: PID {pid}")
            
            # Try graceful termination first
            proc.terminate()
            
            # Wait for graceful shutdown
            try:
                proc.wait(timeout=3)
                print(f"Successfully closed process: PID {pid}")
                return True
            except psutil.TimeoutExpired:
                # Force kill if it doesn't close gracefully
                print(f"Force killing process: PID {pid}")
                proc.kill()
                try:
                    proc.wait(timeout=1)
                    print(f"Force killed process: PID {pid}")
                    return True
                except psutil.TimeoutExpired:
                    print(f"Failed to kill process: PID {pid}")
                    return False
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error closing process PID {pid}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error closing process PID {pid}: {e}")
            return False
    
    def show_exit_progress(self):
        """Show a progress dialog during exit process"""
        try:
            # Create a simple progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Exiting...")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            # Center the window
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Progress label
            progress_label = tk.Label(progress_window, text="Closing applications...", font=("Arial", 10))
            progress_label.pack(pady=20)
            
            # Progress bar
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill='x')
            progress_bar.start()
            
            # Update the window
            progress_window.update()
            
            # Store reference for cleanup
            self.exit_progress_window = progress_window
            
        except Exception as e:
            print(f"Error showing exit progress: {e}")
    
    def hide_exit_progress(self):
        """Hide the exit progress dialog"""
        try:
            if hasattr(self, 'exit_progress_window'):
                self.exit_progress_window.destroy()
                delattr(self, 'exit_progress_window')
        except Exception as e:
            print(f"Error hiding exit progress: {e}")

def main():
    app = TestExitApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()
