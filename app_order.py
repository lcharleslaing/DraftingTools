import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from database_setup import DatabaseManager
from ui_prefs import bind_tree_column_persistence
from app_nav import add_app_bar
from help_utils import add_help_button

class AppOrderManager:
    def __init__(self, root):
        self.root = root
        self.root.title("App Order Manager - Drafting Tools")
        self.root.geometry("600x400")
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                pass
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Create main frame
        try:
            add_app_bar(self.root, current_app='app_order')
        except Exception:
            pass
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
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
        # Title
        title_label = ttk.Label(self.main_frame, text="App Order Manager", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Apps list frame
        list_frame = ttk.LabelFrame(self.main_frame, text="Available Apps", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        try:
            add_help_button(list_frame, 'App Order', 'Reorder and toggle visibility of apps on the Dashboard.').grid(row=0, column=0, sticky='ne')
        except Exception:
            pass
        
        # Treeview for apps
        columns = ('App Name', 'Display Order', 'Active')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        try:
            bind_tree_column_persistence(self.tree, 'app_order.tree', self.root)
        except Exception:
            pass
        
        # Control frame
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=2, column=0, pady=(20, 0))
        
        # Add new app frame
        add_frame = ttk.LabelFrame(control_frame, text="Add New App", padding="5")
        add_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(add_frame, text="App Name:").grid(row=0, column=0, sticky=tk.W)
        self.new_app_var = tk.StringVar()
        self.new_app_entry = ttk.Entry(add_frame, textvariable=self.new_app_var, width=20)
        self.new_app_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(add_frame, text="Order:").grid(row=1, column=0, sticky=tk.W)
        self.new_order_var = tk.StringVar()
        self.new_order_entry = ttk.Entry(add_frame, textvariable=self.new_order_var, width=10)
        self.new_order_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Button(add_frame, text="Add App", command=self.add_app).grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Edit frame
        edit_frame = ttk.LabelFrame(control_frame, text="Edit Selected App", padding="5")
        edit_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Label(edit_frame, text="New Order:").grid(row=0, column=0, sticky=tk.W)
        self.edit_order_var = tk.StringVar()
        self.edit_order_entry = ttk.Entry(edit_frame, textvariable=self.edit_order_var, width=10)
        self.edit_order_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        self.active_var = tk.BooleanVar()
        ttk.Checkbutton(edit_frame, text="Active", variable=self.active_var).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Button(edit_frame, text="Update", command=self.update_app).grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Move Up", command=self.move_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Move Down", command=self.move_down).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete App", command=self.delete_app).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Refresh", command=self.load_apps).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Export JSON", command=self.export_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Import JSON", command=self.import_data).pack(side=tk.LEFT, padx=(0, 5))
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_app_select)
    
    def load_apps(self):
        """Load apps from database"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT app_name, display_order, is_active 
            FROM app_order 
            ORDER BY display_order
        """)
        apps = cursor.fetchall()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert apps
        for app in apps:
            active_status = "Yes" if app[2] else "No"
            self.tree.insert('', 'end', values=(app[0], app[1], active_status))
        
        conn.close()
    
    def on_app_select(self, event):
        """Handle app selection"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        app_name = item['values'][0]
        order = item['values'][1]
        active = item['values'][2] == "Yes"
        
        self.edit_order_var.set(order)
        self.active_var.set(active)
    
    def add_app(self):
        """Add new app"""
        app_name = self.new_app_var.get().strip()
        order = self.new_order_var.get().strip()
        
        if not app_name:
            messagebox.showerror("Error", "App name is required!")
            return
        
        if not order.isdigit():
            messagebox.showerror("Error", "Order must be a number!")
            return
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO app_order (app_name, display_order, is_active)
                VALUES (?, ?, 1)
            """, (app_name, int(order)))
            
            conn.commit()
            messagebox.showinfo("Success", "App added successfully!")
            self.load_apps()
            self.new_app_var.set("")
            self.new_order_var.set("")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "App name already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add app: {str(e)}")
        finally:
            conn.close()
    
    def update_app(self):
        """Update selected app"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to update!")
            return
        
        item = self.tree.item(selection[0])
        app_name = item['values'][0]
        new_order = self.edit_order_var.get().strip()
        
        if not new_order.isdigit():
            messagebox.showerror("Error", "Order must be a number!")
            return
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE app_order 
                SET display_order = ?, is_active = ?
                WHERE app_name = ?
            """, (int(new_order), self.active_var.get(), app_name))
            
            conn.commit()
            messagebox.showinfo("Success", "App updated successfully!")
            self.load_apps()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update app: {str(e)}")
        finally:
            conn.close()
    
    def delete_app(self):
        """Delete selected app"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this app?"):
            item = self.tree.item(selection[0])
            app_name = item['values'][0]
            
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM app_order WHERE app_name = ?", (app_name,))
                conn.commit()
                messagebox.showinfo("Success", "App deleted successfully!")
                self.load_apps()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete app: {str(e)}")
            finally:
                conn.close()
    
    def move_up(self):
        """Move selected app up in order"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to move!")
            return
        
        item = self.tree.item(selection[0])
        app_name = item['values'][0]
        current_order = int(item['values'][1])
        
        if current_order <= 1:
            messagebox.showwarning("Warning", "App is already at the top!")
            return
        
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            # Swap with the app above
            cursor.execute("""
                UPDATE app_order 
                SET display_order = CASE 
                    WHEN app_name = ? THEN display_order - 1
                    WHEN display_order = ? - 1 THEN display_order + 1
                    ELSE display_order
                END
            """, (app_name, current_order))
            
            conn.commit()
            self.load_apps()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move app: {str(e)}")
        finally:
            conn.close()
    
    def move_down(self):
        """Move selected app down in order"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an app to move!")
            return
        
        item = self.tree.item(selection[0])
        app_name = item['values'][0]
        current_order = int(item['values'][1])
        
        # Get max order
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT MAX(display_order) FROM app_order")
            max_order = cursor.fetchone()[0]
            
            if current_order >= max_order:
                messagebox.showwarning("Warning", "App is already at the bottom!")
                return
            
            # Swap with the app below
            cursor.execute("""
                UPDATE app_order 
                SET display_order = CASE 
                    WHEN app_name = ? THEN display_order + 1
                    WHEN display_order = ? + 1 THEN display_order - 1
                    ELSE display_order
                END
            """, (app_name, current_order))
            
            conn.commit()
            self.load_apps()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move app: {str(e)}")
        finally:
            conn.close()
    
    def export_data(self):
        """Export data to JSON"""
        self.db_manager.export_to_json()
        messagebox.showinfo("Success", "Data exported to JSON successfully!")
    
    def import_data(self):
        """Import data from JSON"""
        self.db_manager.import_from_json()
        self.load_apps()
        messagebox.showinfo("Success", "Data imported from JSON successfully!")
    
    def on_closing(self):
        """Handle application closing"""
        self.db_manager.backup_database()
        self.db_manager.export_to_json()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = AppOrderManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
