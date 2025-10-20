import json
import sqlite3
import re
from typing import Dict, List, Tuple, Optional

class CoilDataProcessor:
    def __init__(self, json_file_path: str, db_path: str = "coil_verification.db"):
        self.json_file_path = json_file_path
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
                diameter_inches INTEGER NOT NULL,  -- 48, 60, 72
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
        
    def parse_json_data(self) -> List[Dict]:
        """Parse the JSON file and extract coil data"""
        with open(self.json_file_path, 'r') as f:
            data = json.load(f)
        
        coil_records = []
        
        # Process each sheet
        for sheet_name, sheet_data in data.items():
            if sheet_name == "Complete List":
                continue  # Skip the summary sheet
                
            # Extract material type and diameter from sheet name
            # Format: "48 Sheet - SS304" or "60 Sheet - SS316"
            match = re.match(r'(\d+)\s+Sheet\s+-\s+(SS\d+)', sheet_name)
            if not match:
                continue
                
            diameter = int(match.group(1))
            material = match.group(2)
            
            # Process the sheet data
            records = self._process_sheet_data(sheet_data, diameter, material)
            coil_records.extend(records)
            
        return coil_records
    
    def _process_sheet_data(self, sheet_data: Dict, diameter: int, material: str) -> List[Dict]:
        """Process individual sheet data to extract coil records"""
        records = []
        
        # Find all diameter values (column A) that are actual data
        diameter_values = []
        for cell_ref, cell_data in sheet_data.items():
            if cell_ref.startswith('A') and 'value' in cell_data and isinstance(cell_data['value'], (int, float)):
                row_num = self._get_row_number(cell_ref)
                if row_num >= 3:  # Skip header rows
                    diameter_value = cell_data['value']
                    # Filter out material codes (304, 316) and other non-diameter values
                    if 10 <= diameter_value <= 200:  # Reasonable diameter range
                        diameter_values.append((row_num, diameter_value))
        
        # Sort by row number
        diameter_values.sort(key=lambda x: x[0])
        
        for row_num, diameter_value in diameter_values:
            # Get actual part number and description from JSON
            part_cell = f"C{row_num}"
            desc_cell = f"D{row_num}"
            length_cell = f"B{row_num}"
            sqft_cell = f"E{row_num}"
            
            # Extract actual values from JSON
            part_number = None
            description = None
            length = None
            square_feet = None
            
            # Get part number - calculate from formula
            if part_cell in sheet_data and 'formula' in sheet_data[part_cell]:
                part_number = self._calculate_part_number_from_formula(sheet_data[part_cell]['formula'], material, diameter, diameter_value)
            elif part_cell in sheet_data and 'value' in sheet_data[part_cell]:
                part_number = sheet_data[part_cell]['value']
            
            # Get description - calculate from formula
            if desc_cell in sheet_data and 'formula' in sheet_data[desc_cell]:
                description = self._calculate_description_from_formula(sheet_data[desc_cell]['formula'], material, diameter, diameter_value)
            elif desc_cell in sheet_data and 'value' in sheet_data[desc_cell]:
                description = sheet_data[desc_cell]['value']
            
            # Get length
            if length_cell in sheet_data and 'value' in sheet_data[length_cell]:
                length = sheet_data[length_cell]['value']
            elif length_cell in sheet_data and 'formula' in sheet_data[length_cell]:
                length = self._calculate_length_from_diameter(diameter_value)
            
            # Get square feet
            if sqft_cell in sheet_data and 'value' in sheet_data[sqft_cell]:
                square_feet = sheet_data[sqft_cell]['value']
            elif sqft_cell in sheet_data and 'formula' in sheet_data[sqft_cell]:
                square_feet = self._calculate_square_feet_from_values(diameter_value, length)
            
            # Determine component type based on diameter
            component_type = self._determine_component_type_from_diameter(diameter_value)
            
            # Only add record if we have valid part number and description
            if part_number and description and length and square_feet:
                record = {
                    'part_number': part_number,
                    'description': description,
                    'material_type': material,
                    'diameter_inches': diameter_value,
                    'component_type': component_type,
                    'length_inches': length,
                    'square_feet': square_feet,
                    'gauge': "12GA",
                    'sheet_size': f"{diameter}\""
                }
                records.append(record)
                print(f"Added record: {part_number} - {description} - Length: {length}")
        
        return records
    
    def _get_row_number(self, cell_ref: str) -> int:
        """Extract row number from cell reference like 'A3'"""
        match = re.match(r'[A-Z]+(\d+)', cell_ref)
        return int(match.group(1)) if match else 0
    
    def _calculate_length_from_diameter(self, diameter_value: float) -> float:
        """Calculate length from diameter using the Excel formula logic"""
        try:
            import math
            # Formula: =CEILING((PI()*(A3-0.1094))+2,0.25)
            # CEILING rounds UP to the nearest 0.25
            raw_length = (math.pi * (diameter_value - 0.1094)) + 2
            # Round UP to nearest 0.25
            return math.ceil(raw_length * 4) / 4
        except:
            return 0.0
    
    def _generate_part_number(self, material: str, diameter: float, length: float) -> str:
        """Generate part number based on material, diameter, and length"""
        try:
            # Format: 304-12-48-150.25 (example from user requirement)
            material_code = "304" if material == "SS304" else "316"
            return f"{material_code}-12-{diameter}-{length}"
        except:
            return f"{material_code}-12-{diameter}-UNKNOWN"
    
    def _calculate_part_number_from_formula(self, formula: str, material: str, sheet_diameter: int, actual_diameter: float) -> str:
        """Calculate part number from Excel formula"""
        try:
            # Formula: =_xlfn.CONCAT($A$1,"-",12,"-",$B$1,"-",$B3)
            # Where $A$1 = "SS304 48\" SHEET", $B$1 = "48", $B3 = calculated length
            material_code = "304" if material == "SS304" else "316"
            length = self._calculate_length_from_diameter(actual_diameter)
            return f"{material_code}-12-{sheet_diameter}-{length}"
        except:
            material_code = "304" if material == "SS304" else "316"
            return f"{material_code}-12-{sheet_diameter}-UNKNOWN"
    
    def _calculate_description_from_formula(self, formula: str, material: str, sheet_diameter: int, actual_diameter: float) -> str:
        """Calculate description from Excel formula"""
        try:
            # Formula: =_xlfn.CONCAT(D$2," X ",$B3)
            # Where D$2 = "SHEET, 304, 12GA, 48\"", $B3 = calculated length
            length = self._calculate_length_from_diameter(actual_diameter)
            return f"SHEET, {material}, 12GA, {sheet_diameter}\" X {length}"
        except:
            return f"SHEET, {material}, 12GA, {sheet_diameter}\" X UNKNOWN"
    
    def _generate_description(self, material: str, diameter: float, length: float) -> str:
        """Generate description based on material, diameter, and length"""
        try:
            return f"SHEET, {material}, 12GA, {diameter}\" X {length}"
        except:
            return f"SHEET, {material}, 12GA, {diameter}\" X UNKNOWN"
    
    def _calculate_square_feet_from_values(self, diameter: float, length: float) -> float:
        """Calculate square feet from diameter and length"""
        try:
            import math
            # Formula: =MROUND(($B$1*B3)/144,0.25)
            square_feet = (diameter * length) / 144
            return round(square_feet * 4) / 4
        except:
            return 0.0
    
    def _determine_component_type_from_diameter(self, diameter_value: float) -> str:
        """Determine if this is for HEATER or TANK based on diameter"""
        # Business rule: smaller diameters are typically heaters, larger are tanks
        if diameter_value <= 30:
            return "HEATER"
        else:
            return "TANK"
    
    def _extract_gauge(self, description: str) -> str:
        """Extract gauge from description"""
        match = re.search(r'(\d+GA)', description)
        return match.group(1) if match else "12GA"
    
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
        """Main method to process JSON and load into database"""
        print("Connecting to database...")
        self.connect_db()
        
        print("Creating tables...")
        self.create_tables()
        
        print("Parsing JSON data...")
        records = self.parse_json_data()
        
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
    processor = CoilDataProcessor("HEATER-TANK COIL LENGTHS.json")
    processor.process_and_load()

if __name__ == "__main__":
    main()
