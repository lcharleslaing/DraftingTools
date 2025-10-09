import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime

class ProductConfigurationsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Product Configurations - Heater, Tank & Pump")
        self.root.state('zoomed')  # Full screen
        self.root.minsize(1200, 800)
        # Make fullscreen the default but keep window controls
        self.root.attributes('-fullscreen', True)
        
        # Initialize database
        self.init_database()
        
        # Create main interface
        self.create_widgets()
        
        # Add keyboard shortcuts for fullscreen toggle
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen() if self.root.attributes('-fullscreen') else None)
        
        # Load initial data
        self.load_dropdown_data()
        
    def init_database(self):
        """Initialize the database and create tables"""
        conn = sqlite3.connect('drafting_tools.db')
        cursor = conn.cursor()
        
        # Create heater configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heater_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT,
                heater_model TEXT,
                location TEXT,
                heater_diameter TEXT,
                heater_height TEXT,
                heater_stack_diameter TEXT,
                application TEXT,
                material TEXT,
                flanges_316 TEXT,
                burner_model TEXT,
                gas_train_position TEXT,
                heater_mounting TEXT,
                gauge_cocks TEXT,
                temperature_switch TEXT,
                packaging_type TEXT,
                mod_piping_transducer_material TEXT,
                hose_material TEXT,
                modulating_valve TEXT,
                media_frame_height TEXT,
                gas_type TEXT,
                side_manway_option TEXT,
                side_manway_angle TEXT,
                water_inlet_size TEXT,
                water_inlet_angles TEXT,
                suction_fitting_size TEXT,
                suction_fitting_height TEXT,
                suction_fitting_angle TEXT,
                ballast_packing_rings TEXT,
                ballast_packing_rings_height TEXT,
                float_chamber_angle TEXT,
                heater_final_assembly_part_number TEXT,
                hose_length TEXT,
                hose_part_number TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        ''')
        
        # Create dropdown options tables
        self.create_dropdown_tables(cursor)
        
        conn.commit()
        conn.close()
    
    def create_dropdown_tables(self, cursor):
        """Create tables for dropdown options"""
        # Heater models
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heater_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Locations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Heater diameters
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heater_diameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Heater heights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heater_heights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Heater stack diameters
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heater_stack_diameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Applications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Materials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Burner models
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS burner_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Gas train positions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gas_train_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Heater mounting types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heater_mounting_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Gauge cocks types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gauge_cocks_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Temperature switch types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_switch_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Packaging types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packaging_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Mod piping transducer materials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mod_piping_transducer_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Hose materials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hose_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Media frame heights
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_frame_heights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Gas types
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gas_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Populate dropdown tables with initial data
        self.populate_dropdown_data(cursor)
    
    def populate_dropdown_data(self, cursor):
        """Populate dropdown tables with initial data"""
        # Heater models
        heater_models = ['GP', 'RM', 'TE-100', 'TE-NSF']
        for model in heater_models:
            cursor.execute('INSERT OR IGNORE INTO heater_models (name) VALUES (?)', (model,))
        
        # Locations
        locations = ['CANADA', 'US']
        for location in locations:
            cursor.execute('INSERT OR IGNORE INTO locations (name) VALUES (?)', (location,))
        
        # Heater diameters
        diameters = ['30', '42', '54', '60']
        for diameter in diameters:
            cursor.execute('INSERT OR IGNORE INTO heater_diameters (value) VALUES (?)', (diameter,))
        
        # Heater heights
        heights = ['8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18']
        for height in heights:
            cursor.execute('INSERT OR IGNORE INTO heater_heights (value) VALUES (?)', (height,))
        
        # Heater stack diameters
        stack_diameters = ['18', '24', '36']
        for diameter in stack_diameters:
            cursor.execute('INSERT OR IGNORE INTO heater_stack_diameters (value) VALUES (?)', (diameter,))
        
        # Applications
        applications = ['FOOD GRADE', 'STANDARD']
        for app in applications:
            cursor.execute('INSERT OR IGNORE INTO applications (name) VALUES (?)', (app,))
        
        # Materials
        materials = ['304', '316']
        for material in materials:
            cursor.execute('INSERT OR IGNORE INTO materials (name) VALUES (?)', (material,))
        
        # Burner models
        burner_models = [
            'MAXON # 415', 'MAXON # 425', 'MAXON # 442M', 
            'MAXON # 456M', 'MAXON # 487M', 'MAXON # EB-7'
        ]
        for model in burner_models:
            cursor.execute('INSERT OR IGNORE INTO burner_models (name) VALUES (?)', (model,))
        
        # Gas train positions
        positions = ['LEFT SIDE', 'RIGHT SIDE']
        for position in positions:
            cursor.execute('INSERT OR IGNORE INTO gas_train_positions (name) VALUES (?)', (position,))
        
        # Heater mounting types
        mounting_types = ['GRAVITY', 'PUMPED']
        for mounting in mounting_types:
            cursor.execute('INSERT OR IGNORE INTO heater_mounting_types (name) VALUES (?)', (mounting,))
        
        # Gauge cocks types
        gauge_types = ['NSF', 'STANDARD']
        for gauge in gauge_types:
            cursor.execute('INSERT OR IGNORE INTO gauge_cocks_types (name) VALUES (?)', (gauge,))
        
        # Temperature switch types
        temp_switch_types = ['BRASS', 'STAINLESS']
        for temp_switch in temp_switch_types:
            cursor.execute('INSERT OR IGNORE INTO temperature_switch_types (name) VALUES (?)', (temp_switch,))
        
        # Packaging types
        packaging_types = ['MODULAR PIPING', 'STANDARD']
        for packaging in packaging_types:
            cursor.execute('INSERT OR IGNORE INTO packaging_types (name) VALUES (?)', (packaging,))
        
        # Mod piping transducer materials
        transducer_materials = ['NSF', '316']
        for material in transducer_materials:
            cursor.execute('INSERT OR IGNORE INTO mod_piping_transducer_materials (name) VALUES (?)', (material,))
        
        # Hose materials
        hose_materials = ['BRASS ENDS', 'SS316 ENDS']
        for material in hose_materials:
            cursor.execute('INSERT OR IGNORE INTO hose_materials (name) VALUES (?)', (material,))
        
        # Media frame heights
        frame_heights = ['42', '48', '54']
        for height in frame_heights:
            cursor.execute('INSERT OR IGNORE INTO media_frame_heights (value) VALUES (?)', (height,))
        
        # Gas types
        gas_types = ['NATURAL GAS', 'PROPANE']
        for gas in gas_types:
            cursor.execute('INSERT OR IGNORE INTO gas_types (name) VALUES (?)', (gas,))
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main container - use full screen
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Title
        title_label = ttk.Label(main_frame, text="Product Configurations - Heater, Tank & Pump", 
                               font=('Arial', 18, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Product selection and configuration area
        self.create_product_selection_area(main_frame)
        
        # Create notebook for different product types - full width
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Heater configuration tab
        self.create_heater_tab()
        
        # Tank configuration tab (placeholder)
        tank_frame = ttk.Frame(self.notebook)
        self.notebook.add(tank_frame, text="Tank Configurations")
        ttk.Label(tank_frame, text="Tank Configurations - Coming Soon", 
                 font=('Arial', 14)).pack(expand=True)
        
        # Pump configuration tab (placeholder)
        pump_frame = ttk.Frame(self.notebook)
        self.notebook.add(pump_frame, text="Pump Configurations")
        ttk.Label(pump_frame, text="Pump Configurations - Coming Soon", 
                 font=('Arial', 14)).pack(expand=True)
    
    def create_product_selection_area(self, parent):
        """Create product selection and job number area"""
        selection_frame = ttk.LabelFrame(parent, text="Product Selection & Job Number", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Job number selection
        job_frame = ttk.Frame(selection_frame)
        job_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(job_frame, text="Job Number:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.job_number_var = tk.StringVar()
        job_entry = ttk.Entry(job_frame, textvariable=self.job_number_var, width=15, font=('Arial', 12))
        job_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        load_btn = ttk.Button(job_frame, text="Load Configuration", command=self.load_configuration)
        load_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        new_btn = ttk.Button(job_frame, text="New Configuration", command=self.new_configuration)
        new_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Product type selection
        product_frame = ttk.Frame(selection_frame)
        product_frame.pack(fill=tk.X)
        
        ttk.Label(product_frame, text="Product Types for this Job:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        # Checkboxes for product types
        self.heater_enabled = tk.BooleanVar()
        self.tank_enabled = tk.BooleanVar()
        self.pump_enabled = tk.BooleanVar()
        
        heater_check = ttk.Checkbutton(product_frame, text="Heater", variable=self.heater_enabled, 
                                      command=self.update_tabs)
        heater_check.pack(side=tk.LEFT, padx=(0, 20))
        
        tank_check = ttk.Checkbutton(product_frame, text="Tank", variable=self.tank_enabled, 
                                    command=self.update_tabs)
        tank_check.pack(side=tk.LEFT, padx=(0, 20))
        
        pump_check = ttk.Checkbutton(product_frame, text="Pump", variable=self.pump_enabled, 
                                    command=self.update_tabs)
        pump_check.pack(side=tk.LEFT, padx=(0, 20))
        
        # Set defaults
        self.heater_enabled.set(True)  # Heater is usually present
        self.pump_enabled.set(True)    # Pump systems are always present
    
    def update_tabs(self):
        """Update visible tabs based on product selection"""
        # This will be implemented to show/hide tabs based on checkboxes
        pass
    
    def create_heater_tab(self):
        """Create the heater configuration tab"""
        heater_frame = ttk.Frame(self.notebook)
        self.notebook.add(heater_frame, text="Heater Configurations")
        
        # Create scrollable frame with full width
        canvas = tk.Canvas(heater_frame)
        scrollbar = ttk.Scrollbar(heater_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configure scrollable frame for full width
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=1)
        
        # Heater parameters section
        self.create_heater_parameters_section()
        
        # Heater fitting section
        self.create_heater_fitting_section()
        
        # Drawing numbers section
        self.create_drawing_numbers_section()
        
        # Action buttons
        self.create_action_buttons(heater_frame)
        
        # Pack canvas and scrollbar - full width
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_heater_parameters_section(self):
        """Create the heater parameters section"""
        params_frame = ttk.LabelFrame(self.scrollable_frame, text="HEATER PARAMETERS", padding=10)
        params_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure columns for better space utilization
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)
        params_frame.columnconfigure(5, weight=1)
        
        row = 0
        
        # Column 1 - Basic Parameters
        # Heater Model
        ttk.Label(params_frame, text="Heater Model:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.heater_model_var = tk.StringVar()
        self.heater_model_combo = ttk.Combobox(params_frame, textvariable=self.heater_model_var, width=15)
        self.heater_model_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Location
        ttk.Label(params_frame, text="Location:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.location_var = tk.StringVar()
        self.location_combo = ttk.Combobox(params_frame, textvariable=self.location_var, width=15)
        self.location_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Heater Diameter
        ttk.Label(params_frame, text="Heater Diameter:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.heater_diameter_var = tk.StringVar()
        self.heater_diameter_combo = ttk.Combobox(params_frame, textvariable=self.heater_diameter_var, width=15)
        self.heater_diameter_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Heater Height
        ttk.Label(params_frame, text="Heater Height:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.heater_height_var = tk.StringVar()
        self.heater_height_combo = ttk.Combobox(params_frame, textvariable=self.heater_height_var, width=15)
        self.heater_height_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Heater Stack Diameter
        ttk.Label(params_frame, text="Heater Stack Diameter:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.heater_stack_diameter_var = tk.StringVar()
        self.heater_stack_diameter_combo = ttk.Combobox(params_frame, textvariable=self.heater_stack_diameter_var, width=15)
        self.heater_stack_diameter_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Application
        ttk.Label(params_frame, text="Application:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.application_var = tk.StringVar()
        self.application_combo = ttk.Combobox(params_frame, textvariable=self.application_var, width=15)
        self.application_combo.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Material
        ttk.Label(params_frame, text="Material:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.material_var = tk.StringVar()
        self.material_combo = ttk.Combobox(params_frame, textvariable=self.material_var, width=15)
        self.material_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # 316 Flanges
        ttk.Label(params_frame, text="316 Flanges:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.flanges_316_var = tk.StringVar()
        self.flanges_316_combo = ttk.Combobox(params_frame, textvariable=self.flanges_316_var, width=15)
        self.flanges_316_combo.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Column 2 - Burner & Mounting
        # Burner Model
        ttk.Label(params_frame, text="Burner Model:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.burner_model_var = tk.StringVar()
        self.burner_model_combo = ttk.Combobox(params_frame, textvariable=self.burner_model_var, width=15)
        self.burner_model_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Gas Train Position
        ttk.Label(params_frame, text="Gas Train Position:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.gas_train_position_var = tk.StringVar()
        self.gas_train_position_combo = ttk.Combobox(params_frame, textvariable=self.gas_train_position_var, width=15)
        self.gas_train_position_combo.grid(row=1, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Heater Mounting
        ttk.Label(params_frame, text="Heater Mounting:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.heater_mounting_var = tk.StringVar()
        self.heater_mounting_combo = ttk.Combobox(params_frame, textvariable=self.heater_mounting_var, width=15)
        self.heater_mounting_combo.grid(row=2, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Gauge Cocks
        ttk.Label(params_frame, text="Gauge Cocks:").grid(row=3, column=2, sticky=tk.W, pady=2)
        self.gauge_cocks_var = tk.StringVar()
        self.gauge_cocks_combo = ttk.Combobox(params_frame, textvariable=self.gauge_cocks_var, width=15)
        self.gauge_cocks_combo.grid(row=3, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Temperature Switch
        ttk.Label(params_frame, text="Temperature Switch:").grid(row=4, column=2, sticky=tk.W, pady=2)
        self.temperature_switch_var = tk.StringVar()
        self.temperature_switch_combo = ttk.Combobox(params_frame, textvariable=self.temperature_switch_var, width=15)
        self.temperature_switch_combo.grid(row=4, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Packaging Type
        ttk.Label(params_frame, text="Packaging (Mod Piping Typ):").grid(row=5, column=2, sticky=tk.W, pady=2)
        self.packaging_type_var = tk.StringVar()
        self.packaging_type_combo = ttk.Combobox(params_frame, textvariable=self.packaging_type_var, width=15)
        self.packaging_type_combo.grid(row=5, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Mod Piping Transducer Material
        ttk.Label(params_frame, text="Mod Piping Transducer Material:").grid(row=6, column=2, sticky=tk.W, pady=2)
        self.mod_piping_transducer_material_var = tk.StringVar()
        self.mod_piping_transducer_material_combo = ttk.Combobox(params_frame, textvariable=self.mod_piping_transducer_material_var, width=15)
        self.mod_piping_transducer_material_combo.grid(row=6, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Hose Material
        ttk.Label(params_frame, text="Hose Material:").grid(row=7, column=2, sticky=tk.W, pady=2)
        self.hose_material_var = tk.StringVar()
        self.hose_material_combo = ttk.Combobox(params_frame, textvariable=self.hose_material_var, width=15)
        self.hose_material_combo.grid(row=7, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Column 3 - Additional Parameters
        # Modulating Valve
        ttk.Label(params_frame, text="Modulating Valve:").grid(row=0, column=4, sticky=tk.W, pady=2)
        self.modulating_valve_var = tk.StringVar()
        self.modulating_valve_combo = ttk.Combobox(params_frame, textvariable=self.modulating_valve_var, width=15)
        self.modulating_valve_combo.grid(row=0, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Media Frame Height
        ttk.Label(params_frame, text="Media Frame Height (54\" Standard):").grid(row=1, column=4, sticky=tk.W, pady=2)
        self.media_frame_height_var = tk.StringVar()
        self.media_frame_height_combo = ttk.Combobox(params_frame, textvariable=self.media_frame_height_var, width=15)
        self.media_frame_height_combo.grid(row=1, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
    
    def create_heater_fitting_section(self):
        """Create the heater fitting section"""
        fitting_frame = ttk.LabelFrame(self.scrollable_frame, text="HEATER FITTING HEIGHT/ANGLES", padding=10)
        fitting_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure columns for better space utilization
        fitting_frame.columnconfigure(1, weight=1)
        fitting_frame.columnconfigure(3, weight=1)
        fitting_frame.columnconfigure(5, weight=1)
        
        row = 0
        
        # Column 1 - Gas and Manway
        # Gas Type
        ttk.Label(fitting_frame, text="Gas:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.gas_type_var = tk.StringVar()
        self.gas_type_combo = ttk.Combobox(fitting_frame, textvariable=self.gas_type_var, width=15)
        self.gas_type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Side Manway Option
        ttk.Label(fitting_frame, text="Side Manway Option:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.side_manway_option_var = tk.StringVar()
        self.side_manway_option_combo = ttk.Combobox(fitting_frame, textvariable=self.side_manway_option_var, width=15)
        self.side_manway_option_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Side Manway Angle
        ttk.Label(fitting_frame, text="Side Manway Angle (degrees):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.side_manway_angle_var = tk.StringVar()
        side_manway_angle_entry = ttk.Entry(fitting_frame, textvariable=self.side_manway_angle_var, width=15)
        side_manway_angle_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Column 2 - Water Inlet
        # Water Inlet Size
        ttk.Label(fitting_frame, text="Water Inlet Size (inches):").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.water_inlet_size_var = tk.StringVar()
        water_inlet_size_entry = ttk.Entry(fitting_frame, textvariable=self.water_inlet_size_var, width=15)
        water_inlet_size_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Water Inlet Angles
        ttk.Label(fitting_frame, text="Water Inlet Angles (degrees):").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.water_inlet_angles_var = tk.StringVar()
        water_inlet_angles_entry = ttk.Entry(fitting_frame, textvariable=self.water_inlet_angles_var, width=15)
        water_inlet_angles_entry.grid(row=1, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Column 3 - Suction Fitting
        # Suction Fitting Size
        ttk.Label(fitting_frame, text="Suction Fitting Size (inches):").grid(row=0, column=4, sticky=tk.W, pady=2)
        self.suction_fitting_size_var = tk.StringVar()
        suction_fitting_size_entry = ttk.Entry(fitting_frame, textvariable=self.suction_fitting_size_var, width=15)
        suction_fitting_size_entry.grid(row=0, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Suction Fitting Height
        ttk.Label(fitting_frame, text="Suction Fitting Height (inches):").grid(row=1, column=4, sticky=tk.W, pady=2)
        self.suction_fitting_height_var = tk.StringVar()
        suction_fitting_height_entry = ttk.Entry(fitting_frame, textvariable=self.suction_fitting_height_var, width=15)
        suction_fitting_height_entry.grid(row=1, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Suction Fitting Angle
        ttk.Label(fitting_frame, text="Suction Fitting Angle (degrees):").grid(row=2, column=4, sticky=tk.W, pady=2)
        self.suction_fitting_angle_var = tk.StringVar()
        suction_fitting_angle_entry = ttk.Entry(fitting_frame, textvariable=self.suction_fitting_angle_var, width=15)
        suction_fitting_angle_entry.grid(row=2, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Row 2 - Additional Parameters
        # Ballast Packing Rings
        ttk.Label(fitting_frame, text="Ballast Packing Rings (inches):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ballast_packing_rings_var = tk.StringVar()
        ballast_packing_rings_entry = ttk.Entry(fitting_frame, textvariable=self.ballast_packing_rings_var, width=15)
        ballast_packing_rings_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Ballast Packing Rings Height
        ttk.Label(fitting_frame, text="Ballast Packing Rings Height (inches):").grid(row=3, column=2, sticky=tk.W, pady=2)
        self.ballast_packing_rings_height_var = tk.StringVar()
        ballast_packing_rings_height_entry = ttk.Entry(fitting_frame, textvariable=self.ballast_packing_rings_height_var, width=15)
        ballast_packing_rings_height_entry.grid(row=3, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        # Float Chamber Angle
        ttk.Label(fitting_frame, text="Float Chamber Angle (degrees, 225 default):").grid(row=3, column=4, sticky=tk.W, pady=2)
        self.float_chamber_angle_var = tk.StringVar()
        float_chamber_angle_entry = ttk.Entry(fitting_frame, textvariable=self.float_chamber_angle_var, width=15)
        float_chamber_angle_entry.grid(row=3, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
    
    def create_drawing_numbers_section(self):
        """Create the drawing numbers section"""
        drawing_frame = ttk.LabelFrame(self.scrollable_frame, text="DRAWING NUMBERS", padding=10)
        drawing_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure columns for better space utilization
        drawing_frame.columnconfigure(1, weight=1)
        drawing_frame.columnconfigure(3, weight=1)
        drawing_frame.columnconfigure(5, weight=1)
        
        # Row 1 - Part Numbers
        ttk.Label(drawing_frame, text="Heater Final Assembly Part Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.heater_final_assembly_part_number_var = tk.StringVar()
        heater_final_assembly_entry = ttk.Entry(drawing_frame, textvariable=self.heater_final_assembly_part_number_var, width=25)
        heater_final_assembly_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        ttk.Label(drawing_frame, text="Hose Length:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.hose_length_var = tk.StringVar()
        hose_length_entry = ttk.Entry(drawing_frame, textvariable=self.hose_length_var, width=15)
        hose_length_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 20))
        
        ttk.Label(drawing_frame, text="Hose Part Number:").grid(row=0, column=4, sticky=tk.W, pady=2)
        self.hose_part_number_var = tk.StringVar()
        hose_part_number_entry = ttk.Entry(drawing_frame, textvariable=self.hose_part_number_var, width=25)
        hose_part_number_entry.grid(row=0, column=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_btn = ttk.Button(button_frame, text="Save Configuration", command=self.save_configuration)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_btn = ttk.Button(button_frame, text="Delete Configuration", command=self.delete_configuration)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        export_btn = ttk.Button(button_frame, text="Export to JSON", command=self.export_configuration)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    def load_dropdown_data(self):
        """Load data for all dropdowns"""
        conn = sqlite3.connect('drafting_tools.db')
        cursor = conn.cursor()
        
        # Load heater models
        cursor.execute("SELECT name FROM heater_models ORDER BY name")
        heater_models = [row[0] for row in cursor.fetchall()]
        self.heater_model_combo['values'] = heater_models
        
        # Load locations
        cursor.execute("SELECT name FROM locations ORDER BY name")
        locations = [row[0] for row in cursor.fetchall()]
        self.location_combo['values'] = locations
        
        # Load heater diameters
        cursor.execute("SELECT value FROM heater_diameters ORDER BY CAST(value AS INTEGER)")
        diameters = [row[0] for row in cursor.fetchall()]
        self.heater_diameter_combo['values'] = diameters
        
        # Load heater heights
        cursor.execute("SELECT value FROM heater_heights ORDER BY CAST(value AS INTEGER)")
        heights = [row[0] for row in cursor.fetchall()]
        self.heater_height_combo['values'] = heights
        
        # Load heater stack diameters
        cursor.execute("SELECT value FROM heater_stack_diameters ORDER BY CAST(value AS INTEGER)")
        stack_diameters = [row[0] for row in cursor.fetchall()]
        self.heater_stack_diameter_combo['values'] = stack_diameters
        
        # Load applications
        cursor.execute("SELECT name FROM applications ORDER BY name")
        applications = [row[0] for row in cursor.fetchall()]
        self.application_combo['values'] = applications
        
        # Load materials
        cursor.execute("SELECT name FROM materials ORDER BY name")
        materials = [row[0] for row in cursor.fetchall()]
        self.material_combo['values'] = materials
        
        # Load burner models
        cursor.execute("SELECT name FROM burner_models ORDER BY name")
        burner_models = [row[0] for row in cursor.fetchall()]
        self.burner_model_combo['values'] = burner_models
        
        # Load gas train positions
        cursor.execute("SELECT name FROM gas_train_positions ORDER BY name")
        positions = [row[0] for row in cursor.fetchall()]
        self.gas_train_position_combo['values'] = positions
        
        # Load heater mounting types
        cursor.execute("SELECT name FROM heater_mounting_types ORDER BY name")
        mounting_types = [row[0] for row in cursor.fetchall()]
        self.heater_mounting_combo['values'] = mounting_types
        
        # Load gauge cocks types
        cursor.execute("SELECT name FROM gauge_cocks_types ORDER BY name")
        gauge_types = [row[0] for row in cursor.fetchall()]
        self.gauge_cocks_combo['values'] = gauge_types
        
        # Load temperature switch types
        cursor.execute("SELECT name FROM temperature_switch_types ORDER BY name")
        temp_switch_types = [row[0] for row in cursor.fetchall()]
        self.temperature_switch_combo['values'] = temp_switch_types
        
        # Load packaging types
        cursor.execute("SELECT name FROM packaging_types ORDER BY name")
        packaging_types = [row[0] for row in cursor.fetchall()]
        self.packaging_type_combo['values'] = packaging_types
        
        # Load mod piping transducer materials
        cursor.execute("SELECT name FROM mod_piping_transducer_materials ORDER BY name")
        transducer_materials = [row[0] for row in cursor.fetchall()]
        self.mod_piping_transducer_material_combo['values'] = transducer_materials
        
        # Load hose materials
        cursor.execute("SELECT name FROM hose_materials ORDER BY name")
        hose_materials = [row[0] for row in cursor.fetchall()]
        self.hose_material_combo['values'] = hose_materials
        
        # Load media frame heights
        cursor.execute("SELECT value FROM media_frame_heights ORDER BY CAST(value AS INTEGER)")
        frame_heights = [row[0] for row in cursor.fetchall()]
        self.media_frame_height_combo['values'] = frame_heights
        
        # Load gas types
        cursor.execute("SELECT name FROM gas_types ORDER BY name")
        gas_types = [row[0] for row in cursor.fetchall()]
        self.gas_type_combo['values'] = gas_types
        
        # Load Yes/No options for remaining dropdowns
        yes_no_options = ['YES', 'NO']
        self.flanges_316_combo['values'] = yes_no_options
        self.modulating_valve_combo['values'] = yes_no_options
        self.side_manway_option_combo['values'] = yes_no_options
        
        conn.close()
    
    def load_configuration(self):
        """Load configuration for selected job number"""
        job_number = self.job_number_var.get().strip()
        if not job_number:
            messagebox.showwarning("Warning", "Please enter a job number")
            return
        
        conn = sqlite3.connect('drafting_tools.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM heater_configurations 
            WHERE job_number = ? 
            ORDER BY updated_date DESC 
            LIMIT 1
        ''', (job_number,))
        
        config = cursor.fetchone()
        conn.close()
        
        if config:
            # Load the configuration data into the form
            self.heater_model_var.set(config[2] or "")
            self.location_var.set(config[3] or "")
            self.heater_diameter_var.set(config[4] or "")
            self.heater_height_var.set(config[5] or "")
            self.heater_stack_diameter_var.set(config[6] or "")
            self.application_var.set(config[7] or "")
            self.material_var.set(config[8] or "")
            self.flanges_316_var.set(config[9] or "")
            self.burner_model_var.set(config[10] or "")
            self.gas_train_position_var.set(config[11] or "")
            self.heater_mounting_var.set(config[12] or "")
            self.gauge_cocks_var.set(config[13] or "")
            self.temperature_switch_var.set(config[14] or "")
            self.packaging_type_var.set(config[15] or "")
            self.mod_piping_transducer_material_var.set(config[16] or "")
            self.hose_material_var.set(config[17] or "")
            self.modulating_valve_var.set(config[18] or "")
            self.media_frame_height_var.set(config[19] or "")
            self.gas_type_var.set(config[20] or "")
            self.side_manway_option_var.set(config[21] or "")
            self.side_manway_angle_var.set(config[22] or "")
            self.water_inlet_size_var.set(config[23] or "")
            self.water_inlet_angles_var.set(config[24] or "")
            self.suction_fitting_size_var.set(config[25] or "")
            self.suction_fitting_height_var.set(config[26] or "")
            self.suction_fitting_angle_var.set(config[27] or "")
            self.ballast_packing_rings_var.set(config[28] or "")
            self.ballast_packing_rings_height_var.set(config[29] or "")
            self.float_chamber_angle_var.set(config[30] or "")
            self.heater_final_assembly_part_number_var.set(config[31] or "")
            self.hose_length_var.set(config[32] or "")
            self.hose_part_number_var.set(config[33] or "")
            
            messagebox.showinfo("Success", f"Configuration loaded for job {job_number}")
        else:
            messagebox.showinfo("Info", f"No configuration found for job {job_number}")
    
    def new_configuration(self):
        """Clear form for new configuration"""
        # Clear all variables
        self.job_number_var.set("")
        self.heater_model_var.set("")
        self.location_var.set("")
        self.heater_diameter_var.set("")
        self.heater_height_var.set("")
        self.heater_stack_diameter_var.set("")
        self.application_var.set("")
        self.material_var.set("")
        self.flanges_316_var.set("")
        self.burner_model_var.set("")
        self.gas_train_position_var.set("")
        self.heater_mounting_var.set("")
        self.gauge_cocks_var.set("")
        self.temperature_switch_var.set("")
        self.packaging_type_var.set("")
        self.mod_piping_transducer_material_var.set("")
        self.hose_material_var.set("")
        self.modulating_valve_var.set("")
        self.media_frame_height_var.set("")
        self.gas_type_var.set("")
        self.side_manway_option_var.set("")
        self.side_manway_angle_var.set("")
        self.water_inlet_size_var.set("")
        self.water_inlet_angles_var.set("")
        self.suction_fitting_size_var.set("")
        self.suction_fitting_height_var.set("")
        self.suction_fitting_angle_var.set("")
        self.ballast_packing_rings_var.set("")
        self.ballast_packing_rings_height_var.set("")
        self.float_chamber_angle_var.set("")
        self.heater_final_assembly_part_number_var.set("")
        self.hose_length_var.set("")
        self.hose_part_number_var.set("")
    
    def save_configuration(self):
        """Save the current configuration"""
        job_number = self.job_number_var.get().strip()
        if not job_number:
            messagebox.showwarning("Warning", "Please enter a job number")
            return
        
        conn = sqlite3.connect('drafting_tools.db')
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT OR REPLACE INTO heater_configurations (
                job_number, heater_model, location, heater_diameter, heater_height,
                heater_stack_diameter, application, material, flanges_316, burner_model,
                gas_train_position, heater_mounting, gauge_cocks, temperature_switch,
                packaging_type, mod_piping_transducer_material, hose_material,
                modulating_valve, media_frame_height, gas_type, side_manway_option,
                side_manway_angle, water_inlet_size, water_inlet_angles,
                suction_fitting_size, suction_fitting_height, suction_fitting_angle,
                ballast_packing_rings, ballast_packing_rings_height, float_chamber_angle,
                heater_final_assembly_part_number, hose_length, hose_part_number,
                created_date, updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_number,
            self.heater_model_var.get(),
            self.location_var.get(),
            self.heater_diameter_var.get(),
            self.heater_height_var.get(),
            self.heater_stack_diameter_var.get(),
            self.application_var.get(),
            self.material_var.get(),
            self.flanges_316_var.get(),
            self.burner_model_var.get(),
            self.gas_train_position_var.get(),
            self.heater_mounting_var.get(),
            self.gauge_cocks_var.get(),
            self.temperature_switch_var.get(),
            self.packaging_type_var.get(),
            self.mod_piping_transducer_material_var.get(),
            self.hose_material_var.get(),
            self.modulating_valve_var.get(),
            self.media_frame_height_var.get(),
            self.gas_type_var.get(),
            self.side_manway_option_var.get(),
            self.side_manway_angle_var.get(),
            self.water_inlet_size_var.get(),
            self.water_inlet_angles_var.get(),
            self.suction_fitting_size_var.get(),
            self.suction_fitting_height_var.get(),
            self.suction_fitting_angle_var.get(),
            self.ballast_packing_rings_var.get(),
            self.ballast_packing_rings_height_var.get(),
            self.float_chamber_angle_var.get(),
            self.heater_final_assembly_part_number_var.get(),
            self.hose_length_var.get(),
            self.hose_part_number_var.get(),
            current_time,
            current_time
        ))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", f"Configuration saved for job {job_number}")
    
    def delete_configuration(self):
        """Delete the current configuration"""
        job_number = self.job_number_var.get().strip()
        if not job_number:
            messagebox.showwarning("Warning", "Please enter a job number")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the configuration for job {job_number}?"):
            conn = sqlite3.connect('drafting_tools.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM heater_configurations WHERE job_number = ?', (job_number,))
            
            conn.commit()
            conn.close()
            
            self.new_configuration()  # Clear the form
            messagebox.showinfo("Success", f"Configuration deleted for job {job_number}")
    
    def export_configuration(self):
        """Export configuration to JSON"""
        job_number = self.job_number_var.get().strip()
        if not job_number:
            messagebox.showwarning("Warning", "Please enter a job number")
            return
        
        conn = sqlite3.connect('drafting_tools.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM heater_configurations 
            WHERE job_number = ? 
            ORDER BY updated_date DESC 
            LIMIT 1
        ''', (job_number,))
        
        config = cursor.fetchone()
        conn.close()
        
        if config:
            # Convert to dictionary for JSON export
            config_dict = {
                'job_number': config[1],
                'heater_model': config[2],
                'location': config[3],
                'heater_diameter': config[4],
                'heater_height': config[5],
                'heater_stack_diameter': config[6],
                'application': config[7],
                'material': config[8],
                'flanges_316': config[9],
                'burner_model': config[10],
                'gas_train_position': config[11],
                'heater_mounting': config[12],
                'gauge_cocks': config[13],
                'temperature_switch': config[14],
                'packaging_type': config[15],
                'mod_piping_transducer_material': config[16],
                'hose_material': config[17],
                'modulating_valve': config[18],
                'media_frame_height': config[19],
                'gas_type': config[20],
                'side_manway_option': config[21],
                'side_manway_angle': config[22],
                'water_inlet_size': config[23],
                'water_inlet_angles': config[24],
                'suction_fitting_size': config[25],
                'suction_fitting_height': config[26],
                'suction_fitting_angle': config[27],
                'ballast_packing_rings': config[28],
                'ballast_packing_rings_height': config[29],
                'float_chamber_angle': config[30],
                'heater_final_assembly_part_number': config[31],
                'hose_length': config[32],
                'hose_part_number': config[33],
                'created_date': config[34],
                'updated_date': config[35]
            }
            
            import json
            filename = f"heater_config_{job_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            messagebox.showinfo("Success", f"Configuration exported to {filename}")
        else:
            messagebox.showwarning("Warning", f"No configuration found for job {job_number}")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        else:
            self.root.attributes('-fullscreen', True)
    
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        self.root.attributes('-fullscreen', False)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ProductConfigurationsApp()
    app.run()
