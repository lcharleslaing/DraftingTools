import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
from typing import List, Dict, Optional, Tuple

class CoilVerificationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Coil Verification Tool - Drafting Tools")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Database connection
        self.db_path = "coil_verification.db"
        self.conn = None
        
        # Create main interface
        self.create_widgets()
        self.connect_database()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def connect_database(self):
        """Connect to the coil verification database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            print("Connected to coil verification database")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to connect to database:\n{str(e)}")
    
    def get_available_diameters(self):
        """Get all available diameters from the database"""
        if not self.conn:
            return ["ALL"]
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT diameter_inches FROM coil_specifications ORDER BY diameter_inches")
            diameters = [str(row[0]) for row in cursor.fetchall()]
            return ["ALL"] + diameters
        except Exception as e:
            print(f"Error getting diameters: {e}")
            return ["ALL"]
    
    def create_widgets(self):
        """Create the main interface widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Coil Verification Tool", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search Parameters", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Search parameters grid
        params_frame = ttk.Frame(search_frame)
        params_frame.pack(fill=tk.X)
        
        # Component Type
        ttk.Label(params_frame, text="Component Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.component_var = tk.StringVar()
        component_combo = ttk.Combobox(params_frame, textvariable=self.component_var, 
                                      values=["HEATER", "TANK", "ALL"], state="readonly", width=15)
        component_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        component_combo.set("ALL")
        
        # Material Type
        ttk.Label(params_frame, text="Material:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.material_var = tk.StringVar()
        material_combo = ttk.Combobox(params_frame, textvariable=self.material_var,
                                     values=["SS304", "SS316", "ALL"], state="readonly", width=15)
        material_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        material_combo.set("ALL")
        
        # Diameter
        ttk.Label(params_frame, text="Diameter:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.diameter_var = tk.StringVar()
        diameter_combo = ttk.Combobox(params_frame, textvariable=self.diameter_var,
                                     values=self.get_available_diameters(), state="readonly", width=15)
        diameter_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        diameter_combo.set("ALL")
        
        # Coil Length
        ttk.Label(params_frame, text="Coil Length:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.length_var = tk.StringVar()
        length_entry = ttk.Entry(params_frame, textvariable=self.length_var, width=15)
        length_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        # Length tolerance
        ttk.Label(params_frame, text="Tolerance:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10))
        self.tolerance_var = tk.StringVar()
        tolerance_combo = ttk.Combobox(params_frame, textvariable=self.tolerance_var,
                                      values=["0.25", "0.5", "1.0", "2.0"], state="readonly", width=10)
        tolerance_combo.grid(row=1, column=3, sticky=tk.W, padx=(0, 20))
        tolerance_combo.set("0.25")
        
        # Search buttons frame
        button_frame = ttk.Frame(search_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        search_btn = ttk.Button(button_frame, text="Search Coils", command=self.search_coils)
        search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="Clear Search", command=self.clear_search)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Part number search frame
        part_search_frame = ttk.LabelFrame(search_frame, text="Part Number Lookup", padding="5")
        part_search_frame.pack(fill=tk.X, pady=(10, 0))
        
        part_search_inner = ttk.Frame(part_search_frame)
        part_search_inner.pack(fill=tk.X)
        
        ttk.Label(part_search_inner, text="Part Number:").pack(side=tk.LEFT, padx=(0, 10))
        self.part_number_var = tk.StringVar()
        part_entry = ttk.Entry(part_search_inner, textvariable=self.part_number_var, width=20)
        part_entry.pack(side=tk.LEFT, padx=(0, 10))
        part_entry.bind('<Return>', lambda e: self.search_by_part_number())
        
        part_search_btn = ttk.Button(part_search_inner, text="Lookup Part", command=self.search_by_part_number)
        part_search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results treeview
        columns = ('Part Number', 'Description', 'Material', 'Diameter', 'Component', 'Length (in)', 'Square Feet', 'Gauge')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for treeview and scrollbars
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select search parameters and click Search Coils")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def search_coils(self):
        """Search for coils based on selected parameters"""
        if not self.conn:
            messagebox.showerror("Error", "Database connection not available")
            return
        
        try:
            # Build query based on selected parameters
            query = "SELECT * FROM coil_specifications WHERE 1=1"
            params = []
            
            component = self.component_var.get()
            if component != "ALL":
                query += " AND component_type = ?"
                params.append(component)
            
            material = self.material_var.get()
            if material != "ALL":
                query += " AND material_type = ?"
                params.append(material)
            
            diameter = self.diameter_var.get()
            if diameter != "ALL":
                query += " AND diameter_inches = ?"
                params.append(float(diameter))
            
            # Add coil length search with tolerance
            length_str = self.length_var.get().strip()
            if length_str:
                try:
                    target_length = float(length_str)
                    tolerance = float(self.tolerance_var.get())
                    min_length = target_length - tolerance
                    max_length = target_length + tolerance
                    query += " AND length_inches BETWEEN ? AND ?"
                    params.extend([min_length, max_length])
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid coil length value. Please enter a number.")
                    return
            
            query += " ORDER BY component_type, material_type, diameter_inches, length_inches"
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Clear existing results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Populate results
            for row in results:
                self.results_tree.insert('', 'end', values=(
                    row['part_number'],
                    row['description'],
                    row['material_type'],
                    f"{row['diameter_inches']}\"",
                    row['component_type'],
                    f"{row['length_inches']:.2f}",
                    f"{row['square_feet']:.2f}",
                    row['gauge']
                ))
            
            self.status_var.set(f"Found {len(results)} coil(s) matching search criteria")
            
        except Exception as e:
            messagebox.showerror("Search Error", f"Error searching coils:\n{str(e)}")
            self.status_var.set("Search failed")
    
    def search_by_part_number(self):
        """Search for a specific part number"""
        part_number = self.part_number_var.get().strip()
        if not part_number:
            messagebox.showwarning("Warning", "Please enter a part number")
            return
        
        if not self.conn:
            messagebox.showerror("Error", "Database connection not available")
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM coil_specifications 
                WHERE part_number LIKE ? 
                ORDER BY component_type, material_type, diameter_inches
            """, (f"%{part_number}%",))
            results = cursor.fetchall()
            
            # Clear existing results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            if results:
                # Populate results
                for row in results:
                    self.results_tree.insert('', 'end', values=(
                        row['part_number'],
                        row['description'],
                        row['material_type'],
                        f"{row['diameter_inches']}\"",
                        row['component_type'],
                        f"{row['length_inches']:.2f}",
                        f"{row['square_feet']:.2f}",
                        row['gauge']
                    ))
                
                self.status_var.set(f"Found {len(results)} coil(s) matching part number '{part_number}'")
            else:
                self.status_var.set(f"No coils found matching part number '{part_number}'")
                
        except Exception as e:
            messagebox.showerror("Search Error", f"Error searching part number:\n{str(e)}")
            self.status_var.set("Part number search failed")
    
    def clear_search(self):
        """Clear search parameters and results"""
        self.component_var.set("ALL")
        self.material_var.set("ALL")
        self.diameter_var.set("ALL")
        self.length_var.set("")
        self.tolerance_var.set("0.25")
        self.part_number_var.set("")
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.status_var.set("Search cleared - Ready for new search")
    
    def get_database_stats(self):
        """Get database statistics"""
        if not self.conn:
            return "Database not connected"
        
        try:
            cursor = self.conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM coil_specifications")
            total = cursor.fetchone()[0]
            
            # Breakdown by component type
            cursor.execute("SELECT component_type, COUNT(*) FROM coil_specifications GROUP BY component_type")
            components = cursor.fetchall()
            
            # Breakdown by material
            cursor.execute("SELECT material_type, COUNT(*) FROM coil_specifications GROUP BY material_type")
            materials = cursor.fetchall()
            
            # Breakdown by diameter
            cursor.execute("SELECT diameter_inches, COUNT(*) FROM coil_specifications GROUP BY diameter_inches ORDER BY diameter_inches")
            diameters = cursor.fetchall()
            
            stats = f"Database Statistics:\n"
            stats += f"Total Records: {total}\n\n"
            
            stats += "By Component Type:\n"
            for comp, count in components:
                stats += f"  {comp}: {count}\n"
            
            stats += "\nBy Material:\n"
            for mat, count in materials:
                stats += f"  {mat}: {count}\n"
            
            stats += "\nBy Diameter:\n"
            for dia, count in diameters:
                stats += f"  {dia}\": {count}\n"
            
            return stats
            
        except Exception as e:
            return f"Error getting statistics: {str(e)}"
    
    def on_closing(self):
        """Handle application closing"""
        if self.conn:
            self.conn.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = CoilVerificationTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
