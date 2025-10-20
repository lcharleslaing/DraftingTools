import pandas as pd
import sqlite3
import re
from typing import Dict, List

class ExcelCoilDataProcessor:
    def __init__(self, excel_file_path: str, db_path: str = "coil_verification.db"):
        self.excel_file_path = excel_file_path
        self.db_path = db_path
        self.conn = None
        
    def connect_db(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
    def create_tables(self):
        """Create database tables for coil data"""
        cursor = self.conn.cursor()
        
        # Main coil specifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coil_specifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_number TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                material_type TEXT NOT NULL,  -- SS304, SS316
                diameter_inches REAL NOT NULL,  -- actual tank/heater diameter (can be fractional)
                component_type TEXT NOT NULL,  -- HEATER, TANK
                length_inches REAL NOT NULL,
                square_feet REAL NOT NULL,
                gauge TEXT,
                sheet_size TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Search index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_part_number ON coil_specifications(part_number)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_material_diameter ON coil_specifications(material_type, diameter_inches)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_component_type ON coil_specifications(component_type)
        """)
        
        self.conn.commit()
        
    def parse_excel_data(self) -> List[Dict]:
        """Parse the Excel file using the exact diameter values provided by the user"""
        records: List[Dict] = []
        
        # Exact diameter values from all sheets (removing duplicates)
        all_diameters = [
            28.25, 31.125, 36, 40, 42, 42.875, 48, 48.875, 51.75, 54, 54.625, 57.125,
            60, 60.625, 63.125, 66, 66.125, 69, 69.125, 72, 73.125, 76, 78, 79.125,
            81.125, 82, 84, 88, 90, 93.125, 94, 96, 99.125, 100, 102, 105.125,
            108, 111.125, 114, 117.125, 120, 123.125, 126, 129.125, 132, 135.125,
            138, 141.125, 144, 147.125, 150, 156, 162, 168
        ]
        
        # Sort diameters for consistency
        all_diameters.sort()
        
        print(f"Using {len(all_diameters)} unique diameter values")
        
        # Read all sheets from the Excel file
        excel_file = pd.ExcelFile(self.excel_file_path)
        
        # Process each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"Processing sheet: {sheet_name}")
            
            # Skip the Complete List sheet - we'll get data from individual sheets
            if sheet_name == "Complete List":
                continue
                
            # Check if this is one of our diameter sheets
            match = re.match(r'(48|60|72)\s+Sheet\s+-\s+(SS\d+)$', sheet_name)
            if not match:
                continue
                
            sheet_width = int(match.group(1))
            material = match.group(2)  # SS304 or SS316
            
            print(f"Processing {sheet_name} - Sheet Width: {sheet_width}, Material: {material}")
            
            # Read the sheet data
            df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name, header=None)
            
            # Process each row starting from row 3 (index 2)
            for index, row in df.iterrows():
                if index < 2:  # Skip header rows
                    continue
                    
                # Check if we have data in this row
                if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]):
                    continue
                    
                try:
                    # Get diameter from column A
                    diameter_value = float(row.iloc[0])
                    
                    # Only process if this diameter is in our approved list
                    if diameter_value not in all_diameters:
                        print(f"Skipping diameter {diameter_value} - not in approved list")
                        continue
                    
                    # Get length from column B
                    length_value = float(row.iloc[1])
                    
                    # Get part number from column C
                    part_number = str(row.iloc[2]) if not pd.isna(row.iloc[2]) else None
                    
                    # Get description from column D
                    description = str(row.iloc[3]) if not pd.isna(row.iloc[3]) else None
                    
                    # Get square feet from column E
                    square_feet = float(row.iloc[4]) if not pd.isna(row.iloc[4]) else None
                    
                    # Only add record if we have all the required data
                    if part_number and description and square_feet:
                        # Determine component type based on diameter
                        # HEATER: specific heater diameters from the Heaters sheet
                        heater_diameters = [28.25, 31.125, 36, 40, 42, 42.875, 48, 48.875, 51.75, 54, 54.625, 57.125, 60, 60.625, 63.125, 66, 66.125, 69, 69.125, 72, 73.125, 76, 78, 79.125, 81.125, 82, 84, 88, 90, 93.125, 94, 96, 99.125, 100, 102, 105.125, 108, 111.125, 114, 117.125, 120, 123.125, 126, 129.125, 132, 135.125, 138, 141.125, 144, 147.125, 150, 156, 162, 168]
                        component_type = "HEATER" if diameter_value in heater_diameters else "TANK"
                        
                        record = {
                            'part_number': part_number,
                            'description': description,
                            'material_type': material,
                            'diameter_inches': diameter_value,
                            'component_type': component_type,
                            'length_inches': length_value,
                            'square_feet': square_feet,
                            'gauge': '12GA',
                            'sheet_size': f"{sheet_width}\"",
                        }
                        records.append(record)
                        print(f"Added: {part_number} - {description}")
                        
                except (ValueError, TypeError) as e:
                    print(f"Skipping row {index} due to error: {e}")
                    continue
        
        return records
    
    def insert_coil_data(self, records: List[Dict]):
        """Insert coil records into database"""
        cursor = self.conn.cursor()
        
        # Clear existing data first
        cursor.execute("DELETE FROM coil_specifications")
        print("Cleared existing data from database")
        
        for record in records:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO coil_specifications 
                    (part_number, description, material_type, diameter_inches, component_type, 
                     length_inches, square_feet, gauge, sheet_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['part_number'],
                    record['description'],
                    record['material_type'],
                    record['diameter_inches'],
                    record['component_type'],
                    record['length_inches'],
                    record['square_feet'],
                    record['gauge'],
                    record['sheet_size']
                ))
            except Exception as e:
                print(f"Error inserting record {record['part_number']}: {e}")
        
        self.conn.commit()
    
    def process_and_load(self):
        """Main method to process Excel and load into database"""
        print("Connecting to database...")
        self.connect_db()
        
        print("Creating tables...")
        self.create_tables()
        
        print("Parsing Excel data...")
        records = self.parse_excel_data()
        
        print(f"Found {len(records)} coil records")
        
        print("Inserting data into database...")
        self.insert_coil_data(records)
        
        print("Data loading complete!")
        
        # Print summary
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM coil_specifications")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT material_type, diameter_inches, component_type, COUNT(*) FROM coil_specifications GROUP BY material_type, diameter_inches, component_type")
        summary = cursor.fetchall()
        
        print(f"\nDatabase Summary:")
        print(f"Total records: {total_count}")
        print("\nBreakdown by Material/Diameter/Component:")
        for row in summary:
            print(f"  {row[0]} {row[1]}\" {row[2]}: {row[3]} records")
        
        self.conn.close()

def main():
    processor = ExcelCoilDataProcessor("HEATER-TANK COIL LENGTHS.xlsx")
    processor.process_and_load()

if __name__ == "__main__":
    main()
