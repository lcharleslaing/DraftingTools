import tkinter as tk
from tkinter import ttk, messagebox
from ui_prefs import bind_tree_column_persistence
import sqlite3
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import getpass
from app_nav import add_app_bar
from help_utils import add_help_button

class CoilVerificationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Coil Verification Tool - Drafting Tools")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                pass
        
        # Database connection
        self.db_path = "coil_verification.db"
        self.conn = None
        
        # Connect to database first
        self.connect_database()
        
        # Create main interface
        try:
            add_app_bar(self.root, current_app='coil_verification')
        except Exception:
            pass
        self.create_widgets()
        
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
        """Get all available diameters from the database sorted by Heater/Tank, Material, Diameter"""
        if not self.conn:
            print("No database connection available for diameters")
            return []
        
        try:
            cursor = self.conn.cursor()
            
            # First, check if table exists and has data
            cursor.execute("SELECT COUNT(*) FROM coil_specifications")
            count = cursor.fetchone()[0]
            print(f"Total records in database: {count}")
            
            if count == 0:
                print("No data in coil_specifications table - please run excel_coil_setup.py first")
                return []
            
            cursor.execute("""
                SELECT DISTINCT component_type, material_type, diameter_inches 
                FROM coil_specifications 
                ORDER BY component_type, material_type, diameter_inches
            """)
            results = cursor.fetchall()
            
            print(f"Found {len(results)} diameter combinations")
            
            # Create formatted diameter list
            diameter_list = []
            for row in results:
                component, material, diameter = row
                # Format: "HEATER - SS304 - 28.25"
                formatted = f"{component} - {material} - {diameter}\""
                diameter_list.append(formatted)
                print(f"Added diameter: {formatted}")
            
            print(f"Total diameter options: {len(diameter_list)}")
            return diameter_list
        except Exception as e:
            print(f"Error getting diameters: {e}")
            # Fallback - return some basic diameters
            fallback_diameters = [
                "HEATER - SS304 - 28.25\"",
                "HEATER - SS304 - 31.125\"",
                "TANK - SS304 - 48\"",
                "TANK - SS304 - 60\"",
                "TANK - SS316 - 48\"",
                "TANK - SS316 - 60\""
            ]
            print(f"Using fallback diameters: {len(fallback_diameters)}")
            return fallback_diameters
    
    def get_available_materials(self, sheet_size=None):
        """Get available materials based on sheet size selection"""
        if not self.conn:
            return ["SS304", "SS316", "ALL"]
        
        try:
            cursor = self.conn.cursor()
            if sheet_size and sheet_size != "ALL":
                # Extract sheet size number (48, 60, 72)
                sheet_num = int(sheet_size.replace('"', ''))
                cursor.execute("""
                    SELECT DISTINCT material_type 
                    FROM coil_specifications 
                    WHERE sheet_size = ?
                    ORDER BY material_type
                """, (f"{sheet_num}\"",))
            else:
                cursor.execute("""
                    SELECT DISTINCT material_type 
                    FROM coil_specifications 
                    ORDER BY material_type
                """)
            
            results = cursor.fetchall()
            materials = [row[0] for row in results]
            return ["ALL"] + materials
        except Exception as e:
            print(f"Error getting materials: {e}")
            return ["SS304", "SS316", "ALL"]
    
    def get_filtered_diameters(self, sheet_size=None, material_type=None):
        """Get available diameters based on sheet size and material selection"""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            query = "SELECT DISTINCT diameter_inches FROM coil_specifications WHERE 1=1"
            params = []
            
            if sheet_size and sheet_size != "ALL":
                # Extract sheet size number (48, 60, 72)
                sheet_num = int(sheet_size.replace('"', ''))
                query += " AND sheet_size = ?"
                params.append(f"{sheet_num}\"")
            
            if material_type and material_type != "ALL":
                query += " AND material_type = ?"
                params.append(material_type)
            
            query += " ORDER BY diameter_inches"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            diameter_list = []
            for row in results:
                diameter = row[0]
                # Format: "28.25""
                formatted = f"{diameter}\""
                diameter_list.append(formatted)
            
            return diameter_list
        except Exception as e:
            print(f"Error getting filtered diameters: {e}")
            return []
    
    def on_sheet_size_changed(self, event=None):
        """Handle sheet size selection change"""
        sheet_size = self.sheet_size_var.get()
        print(f"Sheet size changed to: {sheet_size}")
        
        # Update materials dropdown
        materials = self.get_available_materials(sheet_size)
        self.material_combo['values'] = materials
        self.material_combo.set("ALL")
        
        # Clear and update diameter dropdown
        self.diameter_var.set("")
        self.update_diameter_dropdown()
    
    def on_material_changed(self, event=None):
        """Handle material type selection change"""
        sheet_size = self.sheet_size_var.get()
        material = self.material_var.get()
        print(f"Material changed to: {material}")
        
        # Update diameter dropdown
        self.diameter_var.set("")
        self.update_diameter_dropdown()
    
    def update_diameter_dropdown(self):
        """Update diameter dropdown based on current selections"""
        sheet_size = self.sheet_size_var.get()
        material = self.material_var.get()
        
        diameters = self.get_filtered_diameters(sheet_size, material)
        self.diameter_combo['values'] = diameters
        
        print(f"Updated diameter dropdown with {len(diameters)} options")
    
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
        
        # Sheet Size
        ttk.Label(params_frame, text="Sheet Size:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.sheet_size_var = tk.StringVar()
        self.sheet_size_combo = ttk.Combobox(params_frame, textvariable=self.sheet_size_var, 
                                            values=["48\"", "60\"", "72\"", "ALL"], state="readonly", width=15)
        self.sheet_size_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.sheet_size_combo.set("ALL")
        self.sheet_size_combo.bind('<<ComboboxSelected>>', self.on_sheet_size_changed)
        
        # Material Type
        ttk.Label(params_frame, text="Material:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.material_var = tk.StringVar()
        self.material_combo = ttk.Combobox(params_frame, textvariable=self.material_var,
                                          values=self.get_available_materials(), state="readonly", width=15)
        self.material_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        self.material_combo.set("ALL")
        self.material_combo.bind('<<ComboboxSelected>>', self.on_material_changed)
        
        # Diameter
        ttk.Label(params_frame, text="Diameter:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.diameter_var = tk.StringVar()
        self.diameter_combo = ttk.Combobox(params_frame, textvariable=self.diameter_var,
                                          values=self.get_available_diameters(), state="readonly", width=25)
        self.diameter_combo.grid(row=0, column=5, sticky=tk.W, padx=(0, 20))
        # No default selection - user must choose
        
        
        # Search buttons frame
        button_frame = ttk.Frame(search_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        search_btn = ttk.Button(button_frame, text="Search Coils", command=self.search_coils)
        search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="Clear Search", command=self.clear_search)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = ttk.Button(button_frame, text="Refresh Diameters", command=self.refresh_diameters)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
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
        try:
            # Place help using grid to avoid mixing managers within results_frame
            add_help_button(results_frame, 'Search Results', 'Use filters above to search; results show part numbers and details. Double‑click rows for actions.').grid(row=0, column=2, sticky='ne')
        except Exception:
            pass
        
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
        h_scrollbar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        bind_tree_column_persistence(self.results_tree, 'coil_verification.results_tree', self.root)
        
        # Configure grid weights
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Create right-click context menu
        self.create_context_menu()
        
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
            
            sheet_size = self.sheet_size_var.get()
            if sheet_size != "ALL":
                # Extract sheet size number (48, 60, 72)
                sheet_num = int(sheet_size.replace('"', ''))
                query += " AND sheet_size = ?"
                params.append(f"{sheet_num}\"")
            
            material = self.material_var.get()
            if material != "ALL":
                query += " AND material_type = ?"
                params.append(material)
            
            diameter = self.diameter_var.get()
            if diameter and diameter.strip():
                # Parse the diameter string: "28.25""
                try:
                    diameter_value = float(diameter.replace('"', ''))
                    query += " AND diameter_inches = ?"
                    params.append(diameter_value)
                except ValueError:
                    messagebox.showwarning("Warning", "Invalid diameter value selected")
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
        self.sheet_size_var.set("ALL")
        self.material_var.set("ALL")
        self.diameter_var.set("")  # Clear diameter selection
        self.part_number_var.set("")
        
        # Reset dropdowns to show all options
        materials = self.get_available_materials()
        self.material_combo['values'] = materials
        self.update_diameter_dropdown()
        
        # Clear results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.status_var.set("Search cleared - Ready for new search")
    
    def refresh_diameters(self):
        """Refresh the diameter dropdown with current database data"""
        try:
            # Update diameter dropdown based on current selections
            self.update_diameter_dropdown()
            
            # Also refresh materials dropdown
            sheet_size = self.sheet_size_var.get()
            materials = self.get_available_materials(sheet_size)
            self.material_combo['values'] = materials
            
            self.status_var.set("Refreshed all dropdowns with current database data")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh dropdowns:\n{str(e)}")
            self.status_var.set("Failed to refresh dropdowns")
    
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
    
    def create_context_menu(self):
        """Create right-click context menu for the search results"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy Part Number", command=self.copy_part_number)
        self.context_menu.add_command(label="Copy Description", command=self.copy_description)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Add to Notes", command=self.add_to_notes)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy All Selected", command=self.copy_all_selected)
        
        # Bind right-click event to treeview
        self.results_tree.bind("<Button-3>", self.show_context_menu)  # Button-3 is right-click on Windows
        self.results_tree.bind("<Button-2>", self.show_context_menu)  # Button-2 is right-click on Mac/Linux
    
    def show_context_menu(self, event):
        """Show context menu at cursor position"""
        # Select the item under the cursor
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            # Show context menu
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def copy_part_number(self):
        """Copy the part number of the selected row to clipboard"""
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            values = self.results_tree.item(item, 'values')
            if values:
                part_number = values[0]  # Part Number is the first column
                self.root.clipboard_clear()
                self.root.clipboard_append(part_number)
                self.status_var.set(f"Copied Part Number: {part_number}")
    
    def copy_description(self):
        """Copy the description of the selected row to clipboard"""
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            values = self.results_tree.item(item, 'values')
            if values:
                description = values[1]  # Description is the second column
                self.root.clipboard_clear()
                self.root.clipboard_append(description)
                self.status_var.set(f"Copied Description: {description}")
    
    def copy_all_selected(self):
        """Copy all data from the selected row to clipboard"""
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            values = self.results_tree.item(item, 'values')
            if values:
                # Format: Part Number | Description | Material | Diameter | Component | Length | Square Feet | Gauge
                formatted_text = " | ".join(str(v) for v in values)
                self.root.clipboard_clear()
                self.root.clipboard_append(formatted_text)
                self.status_var.set("Copied all data from selected row")

    def add_to_notes(self):
        """Add coil verification note to a job's notes"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a coil result first")
            return
        
        item = selection[0]
        values = self.results_tree.item(item, 'values')
        if not values:
            messagebox.showwarning("Warning", "No coil data selected")
            return
        
        part_number = values[0]
        description = values[1]
        
        # Create and show the notes dialog
        self.show_notes_dialog(part_number, description)
    
    def show_notes_dialog(self, part_number, description):
        """Show dialog to select job and add Kemco P/N"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Coil Verification to Job Notes")
        dialog.geometry("600x600")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Add Coil Verification to Job Notes", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Coil info frame
        coil_frame = ttk.LabelFrame(main_frame, text="Coil Information", padding="10")
        coil_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(coil_frame, text=f"Part Number: {part_number}").pack(anchor=tk.W)
        ttk.Label(coil_frame, text=f"Description: {description}").pack(anchor=tk.W)
        
        # Job selection frame
        job_frame = ttk.LabelFrame(main_frame, text="Job Selection", padding="10")
        job_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Job search
        ttk.Label(job_frame, text="Search Job:").pack(anchor=tk.W)
        job_search_var = tk.StringVar()
        job_search_entry = ttk.Entry(job_frame, textvariable=job_search_var, width=30)
        job_search_entry.pack(fill=tk.X, pady=(5, 10))
        job_search_entry.bind('<KeyRelease>', lambda e: self.filter_jobs(job_search_var.get(), job_listbox))
        
        # Job listbox
        ttk.Label(job_frame, text="Select Job:").pack(anchor=tk.W)
        listbox_frame = ttk.Frame(job_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        job_listbox = tk.Listbox(listbox_frame, height=8)
        job_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=job_listbox.yview)
        job_listbox.configure(yscrollcommand=job_scrollbar.set)
        
        job_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        job_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load jobs
        self.load_jobs(job_listbox)
        
        # Kemco P/N frame
        kemco_frame = ttk.LabelFrame(main_frame, text="Kemco Part Number", padding="10")
        kemco_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(kemco_frame, text="Kemco P/N:").pack(anchor=tk.W)
        kemco_var = tk.StringVar()
        kemco_entry = ttk.Entry(kemco_frame, textvariable=kemco_var, width=30)
        kemco_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        def add_note():
            selected_indices = job_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Warning", "Please select a job")
                return
            
            kemco_pn = kemco_var.get().strip()
            if not kemco_pn:
                messagebox.showwarning("Warning", "Please enter a Kemco P/N")
                return
            
            selected_job = job_listbox.get(selected_indices[0])
            job_number = selected_job.split(' - ')[0]  # Extract job number from "12345 - Customer Name"
            
            # Add the note
            self.add_verification_note(job_number, kemco_pn, part_number, description)
            dialog.destroy()
        
        ttk.Button(button_frame, text="Add to Notes", command=add_note).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def load_jobs(self, listbox):
        """Load all jobs into the listbox"""
        try:
            # Connect to main database
            main_conn = sqlite3.connect("drafting_tools.db")
            cursor = main_conn.cursor()
            
            cursor.execute("""
                SELECT job_number, customer_name, customer_location 
                FROM projects 
                ORDER BY job_number DESC
            """)
            jobs = cursor.fetchall()
            
            listbox.delete(0, tk.END)
            for job_number, customer_name, customer_location in jobs:
                display_text = f"{job_number} - {customer_name or 'Unknown Customer'}"
                if customer_location:
                    display_text += f" ({customer_location})"
                listbox.insert(tk.END, display_text)
            
            main_conn.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load jobs: {str(e)}")
    
    def filter_jobs(self, search_text, listbox):
        """Filter jobs based on search text"""
        try:
            # Connect to main database
            main_conn = sqlite3.connect("drafting_tools.db")
            cursor = main_conn.cursor()
            
            if search_text.strip():
                cursor.execute("""
                    SELECT job_number, customer_name, customer_location 
                    FROM projects 
                    WHERE job_number LIKE ? OR customer_name LIKE ? OR customer_location LIKE ?
                    ORDER BY job_number DESC
                """, (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"))
            else:
                cursor.execute("""
                    SELECT job_number, customer_name, customer_location 
                    FROM projects 
                    ORDER BY job_number DESC
                """)
            
            jobs = cursor.fetchall()
            
            listbox.delete(0, tk.END)
            for job_number, customer_name, customer_location in jobs:
                display_text = f"{job_number} - {customer_name or 'Unknown Customer'}"
                if customer_location:
                    display_text += f" ({customer_location})"
                listbox.insert(tk.END, display_text)
            
            main_conn.close()
            
        except Exception as e:
            print(f"Error filtering jobs: {e}")
    
    def add_verification_note(self, job_number, kemco_pn, coil_part_number, coil_description):
        """Add verification note to the job's notes"""
        try:
            # Connect to main database
            main_conn = sqlite3.connect("drafting_tools.db")
            cursor = main_conn.cursor()
            
            # Create job_notes table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_notes (
                    job_number TEXT PRIMARY KEY,
                    notes TEXT
                )
            """)
            
            # Get current notes
            cursor.execute("SELECT notes FROM job_notes WHERE job_number = ?", (job_number,))
            result = cursor.fetchone()
            current_notes = result[0] if result and result[0] else ""
            
            # Create verification note
            current_time = datetime.now().strftime("%Y-%m-%d @ %I:%M %p")
            current_user = getpass.getuser()
            
            verification_note = f"\n{current_time} - {current_user}\n** Verified Coil size was correct on the drawings for {kemco_pn}\n"
            
            # Append to existing notes
            new_notes = current_notes + verification_note
            
            # Save updated notes
            cursor.execute("""
                INSERT OR REPLACE INTO job_notes (job_number, notes) 
                VALUES (?, ?)
            """, (job_number, new_notes))
            
            main_conn.commit()
            main_conn.close()
            
            messagebox.showinfo("Success", f"Coil verification note added to job {job_number}")
            self.status_var.set(f"Added verification note for {kemco_pn} to job {job_number}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add verification note: {str(e)}")
            self.status_var.set("Failed to add verification note")

    def on_closing(self):
        """Handle application closing"""
        if self.conn:
            self.conn.close()
        self.root.destroy()

def main():
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Coil Verification Tool')
    parser.add_argument('--job', type=str, help='Job number to preload')
    args = parser.parse_args()
    
    root = tk.Tk()
    app = CoilVerificationTool(root)
    
    # If job number provided, show it in status
    if args.job:
        app.status_var.set(f"Ready - Job {args.job} preloaded. Select search parameters and click Search Coils")
        print(f"Coil Verification Tool opened with job number: {args.job}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
