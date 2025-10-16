import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="drafting_tools.db"):
        self.db_path = db_path
        self.backup_path = "backup"
        self.master_db_path = os.path.join(self.backup_path, "master_drafting_tools.db")
        self.master_json_path = os.path.join(self.backup_path, "master_data.json")
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_path, exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """Initialize the database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create designers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS designers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create engineers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engineers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT UNIQUE NOT NULL,
                job_directory TEXT,
                customer_name TEXT,
                customer_name_directory TEXT,
                customer_location TEXT,
                customer_location_directory TEXT,
                assigned_to_id INTEGER,
                assignment_date TEXT,
                start_date TEXT,
                completion_date TEXT,
                total_duration_days INTEGER,
                released_to_dee TEXT,
                FOREIGN KEY (assigned_to_id) REFERENCES designers (id)
            )
        ''')
        
        # Create initial_redline table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS initial_redline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                engineer_id INTEGER,
                redline_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (engineer_id) REFERENCES engineers (id)
            )
        ''')
        
        # Create redline_updates table (for multiple update cycles)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redline_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                engineer_id INTEGER,
                update_date TEXT,
                update_cycle INTEGER,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id),
                FOREIGN KEY (engineer_id) REFERENCES engineers (id)
            )
        ''')
        
        # Create ops_review table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ops_review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                review_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Create d365_bom_entry table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS d365_bom_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                entry_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Create peter_weck_review table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peter_weck_review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                fixed_errors_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Create release_to_dee table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS release_to_dee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                release_date TEXT,
                missing_prints_date TEXT,
                d365_updates_date TEXT,
                other_notes TEXT,
                other_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')
        
        # Create app_order table for dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_order (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT UNIQUE NOT NULL,
                display_order INTEGER,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Insert default data
        self.insert_default_data(cursor)
        
        # Add missing columns if they don't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE redline_updates ADD COLUMN update_cycle INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE redline_updates ADD COLUMN is_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE ops_review ADD COLUMN is_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE peter_weck_review ADD COLUMN is_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE release_to_dee ADD COLUMN is_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE release_to_dee ADD COLUMN due_date TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add new project fields if they don't exist
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN job_directory TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN customer_name TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN customer_location TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN customer_name_directory TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN customer_location_directory TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN last_cover_sheet_date TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN due_date TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN project_engineer_id INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create drawings table for print packages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drawings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                drawing_path TEXT NOT NULL,
                drawing_name TEXT NOT NULL,
                drawing_type TEXT,
                file_extension TEXT,
                added_date TEXT,
                added_by TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        # Create print_packages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                package_name TEXT,
                created_date TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        # Create D365 import configurations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS d365_import_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                config_type TEXT NOT NULL,
                config_data TEXT,
                created_date TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        # Create D365 part numbers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS d365_part_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                part_number TEXT NOT NULL,
                description TEXT,
                bom_number TEXT,
                template TEXT,
                product_type TEXT,
                created_date TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        # Create D365 import parameters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS d365_import_params (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                param_type TEXT NOT NULL,
                param_name TEXT NOT NULL,
                param_value TEXT,
                created_date TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_default_data(self, cursor):
        """Insert default data for designers and engineers"""
        # Insert designers
        designers = ['Lee L.', 'Pete W.', 'Mike K.', 'Rich T.']
        for designer in designers:
            cursor.execute('INSERT OR IGNORE INTO designers (name) VALUES (?)', (designer,))
        
        # Insert engineers
        engineers = ['B. Pender', 'T. Stevenson', 'A. Rzonca']
        for engineer in engineers:
            cursor.execute('INSERT OR IGNORE INTO engineers (name) VALUES (?)', (engineer,))
        
        # Insert default app order
        default_apps = [
            ('projects', 1),
            ('dashboard', 2)
        ]
        for app_name, order in default_apps:
            cursor.execute('INSERT OR IGNORE INTO app_order (app_name, display_order) VALUES (?, ?)', 
                         (app_name, order))
    
    def backup_database(self):
        """Backup database to master location"""
        import shutil
        if os.path.exists(self.db_path):
            shutil.copy2(self.db_path, self.master_db_path)
            print(f"Database backed up to {self.master_db_path}")
    
    def restore_database(self):
        """Restore database from master location"""
        import shutil
        if os.path.exists(self.master_db_path):
            shutil.copy2(self.master_db_path, self.db_path)
            print(f"Database restored from {self.master_db_path}")
    
    def export_to_json(self):
        """Export all data to JSON file"""
        import json
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        data = {}
        for table in tables:
            table_name = table['name']
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            data[table_name] = [dict(row) for row in rows]
        
        with open(self.master_json_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        conn.close()
        print(f"Data exported to {self.master_json_path}")
    
    def import_from_json(self):
        """Import data from JSON file"""
        import json
        if not os.path.exists(self.master_json_path):
            return
        
        with open(self.master_json_path, 'r') as f:
            data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for table_name, rows in data.items():
            if not rows:
                continue
            
            # Clear existing data
            cursor.execute(f"DELETE FROM {table_name}")
            
            # Insert new data
            for row in rows:
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['?' for _ in row])
                values = list(row.values())
                cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        
        conn.commit()
        conn.close()
        print(f"Data imported from {self.master_json_path}")

if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
