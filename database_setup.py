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
        # Pragmas for integrity and performance
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
        except Exception:
            pass
        
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
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
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
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
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
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        
        # Create d365_bom_entry table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS d365_bom_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                entry_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        ''')
        
        # Create peter_weck_review table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peter_weck_review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                fixed_errors_date TEXT,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
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
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
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
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
            )
        ''')
        
        # Create print_packages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                package_name TEXT,
                created_date TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
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
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
            )
        ''')

        # --------------------------------------------
        # Project Workflow Templates (versioned)
        # --------------------------------------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                is_active INTEGER DEFAULT 0,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, version)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_template_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                order_index INTEGER NOT NULL,
                department TEXT NOT NULL,
                group_name TEXT,
                title TEXT NOT NULL,
                planned_duration_days INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_workflow_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                template_id INTEGER,
                template_step_id INTEGER,
                order_index INTEGER NOT NULL,
                department TEXT NOT NULL,
                group_name TEXT,
                title TEXT NOT NULL,
                start_flag INTEGER DEFAULT 0,
                start_ts TEXT,
                completed_flag INTEGER DEFAULT 0,
                completed_ts TEXT,
                transfer_to_name TEXT,
                transfer_to_ts TEXT,
                received_from_name TEXT,
                received_from_ts TEXT,
                planned_due_date TEXT,
                actual_completed_date TEXT,
                actual_duration_days INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE SET NULL,
                FOREIGN KEY (template_step_id) REFERENCES workflow_template_steps(id) ON DELETE SET NULL
            )
        ''')

        # Add missing columns to project_workflow_steps for existing databases
        try:
            cursor.execute("ALTER TABLE project_workflow_steps ADD COLUMN transfer_to_ts TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE project_workflow_steps ADD COLUMN received_from_ts TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wt_active ON workflow_templates(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wts_template ON workflow_template_steps(template_id, order_index)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pws_project ON project_workflow_steps(project_id, order_index)')
        except Exception:
            pass

        # Seed a default "Standard" template if none exists
        cursor.execute('SELECT COUNT(*) FROM workflow_templates')
        cnt = cursor.fetchone()[0]
        if cnt == 0:
            cursor.execute('INSERT INTO workflow_templates (name, version, is_active) VALUES (?, ?, ?)',
                           ('Standard', 1, 1))
            # No default steps; user can define via settings

        conn.commit()
        
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
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
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
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
            )
        ''')
        
        # Create print_package_reviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_package_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_number TEXT NOT NULL,
                review_id TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'initialized',
                current_stage INTEGER DEFAULT 0,
                initialized_by TEXT NOT NULL,
                initialized_date TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_date TEXT,
                notes TEXT,
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
            )
        ''')
        
        # Create print_package_files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_package_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT NOT NULL,
                job_number TEXT NOT NULL,
                file_name TEXT NOT NULL,
                original_path TEXT NOT NULL,
                stage_0_path TEXT,
                stage_1_path TEXT,
                stage_2_path TEXT,
                stage_3_path TEXT,
                stage_4_path TEXT,
                stage_5_path TEXT,
                stage_6_path TEXT,
                stage_7_path TEXT,
                file_size INTEGER,
                file_type TEXT DEFAULT 'pdf',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (review_id) REFERENCES print_package_reviews (review_id) ON DELETE CASCADE,
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
            )
        ''')
        
        # Create print_package_workflow table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS print_package_workflow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT NOT NULL,
                job_number TEXT NOT NULL,
                stage INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                reviewer TEXT,
                department TEXT,
                status TEXT DEFAULT 'pending',
                started_date TEXT,
                completed_date TEXT,
                notes TEXT,
                FOREIGN KEY (review_id) REFERENCES print_package_reviews (review_id) ON DELETE CASCADE,
                FOREIGN KEY (job_number) REFERENCES projects (job_number) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        
        # Create helpful indexes (idempotent)
        try:
            idx_statements = [
                # Projects and lookups
                "CREATE INDEX IF NOT EXISTS idx_projects_job_number ON projects(job_number)",
                "CREATE INDEX IF NOT EXISTS idx_projects_assigned_to_id ON projects(assigned_to_id)",
                "CREATE INDEX IF NOT EXISTS idx_projects_engineer_id ON projects(project_engineer_id)",
                "CREATE INDEX IF NOT EXISTS idx_projects_due_date ON projects(due_date)",
                # Workflow tables by project_id
                "CREATE INDEX IF NOT EXISTS idx_initial_redline_project ON initial_redline(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_redline_updates_project ON redline_updates(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_ops_review_project ON ops_review(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_d365_bom_entry_project ON d365_bom_entry(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_peter_weck_review_project ON peter_weck_review(project_id)",
                "CREATE INDEX IF NOT EXISTS idx_release_to_dee_project ON release_to_dee(project_id)",
                # Drawings/print packages
                "CREATE INDEX IF NOT EXISTS idx_drawings_job_number ON drawings(job_number)",
                "CREATE INDEX IF NOT EXISTS idx_print_packages_job_number ON print_packages(job_number)",
                "CREATE INDEX IF NOT EXISTS idx_pp_reviews_job_number ON print_package_reviews(job_number)",
                "CREATE INDEX IF NOT EXISTS idx_pp_workflow_review ON print_package_workflow(review_id)",
                "CREATE INDEX IF NOT EXISTS idx_pp_workflow_job_stage ON print_package_workflow(job_number, stage)",
                "CREATE INDEX IF NOT EXISTS idx_pp_files_review ON print_package_files(review_id)",
                "CREATE INDEX IF NOT EXISTS idx_pp_files_job ON print_package_files(job_number)",
                # D365 tables by job
                "CREATE INDEX IF NOT EXISTS idx_d365_cfg_job ON d365_import_configs(job_number)",
                "CREATE INDEX IF NOT EXISTS idx_d365_part_job ON d365_part_numbers(job_number)",
                "CREATE INDEX IF NOT EXISTS idx_d365_param_job ON d365_import_params(job_number)",
            ]
            for stmt in idx_statements:
                try:
                    cursor.execute(stmt)
                except Exception:
                    pass
            conn.commit()
        except Exception:
            pass
        finally:
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
