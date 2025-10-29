"""
Database Relationship Exporter
Exports all database tables with relationships clearly visible.
Supports multiple formats: hierarchical JSON, CSV per table, and HTML visualization.
"""

import sqlite3
import json
import csv
import os
from datetime import datetime
from collections import defaultdict


class DatabaseRelationshipExporter:
    def __init__(self, db_path="drafting_tools.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.relationships = {}
        self.table_info = {}
        self.export_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_table_schema(self):
        """Get schema information for all tables including foreign keys"""
        # Get all tables
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in self.cursor.fetchall()]
        
        schema_info = {}
        foreign_keys = defaultdict(list)
        
        for table in tables:
            # Get table structure
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = []
            primary_keys = []
            
            for col in self.cursor.fetchall():
                col_info = {
                    'name': col[1],
                    'type': col[2],
                    'not_null': bool(col[3]),
                    'default_value': col[4],
                    'pk': bool(col[5])
                }
                columns.append(col_info)
                if col_info['pk']:
                    primary_keys.append(col_info['name'])
            
            # Get foreign keys
            self.cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = []
            for fk in self.cursor.fetchall():
                fk_info = {
                    'id': fk[0],
                    'seq': fk[1],
                    'from_column': fk[2],
                    'to_table': fk[3],
                    'to_column': fk[4],
                    'on_update': fk[5],
                    'on_delete': fk[6]
                }
                fks.append(fk_info)
                # Track relationships
                foreign_keys[table].append({
                    'from_column': fk_info['from_column'],
                    'to_table': fk_info['to_table'],
                    'to_column': fk_info['to_column'],
                    'on_delete': fk_info['on_delete']
                })
            
            schema_info[table] = {
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': fks
            }
        
        self.table_info = schema_info
        self.relationships = dict(foreign_keys)
        return schema_info
    
    def export_flat_json(self, output_dir="db_exports"):
        """Export all tables as flat JSON (similar to existing export)"""
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"all_tables_flat_{self.export_timestamp}.json")
        
        data = {}
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in self.cursor.fetchall()]
        
        for table in tables:
            self.cursor.execute(f"SELECT * FROM {table}")
            rows = self.cursor.fetchall()
            data[table] = [dict(row) for row in rows]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"[OK] Flat JSON exported: {output_file}")
        return output_file
    
    def export_hierarchical_json(self, output_dir="db_exports"):
        """Export data in hierarchical format showing relationships"""
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"relationships_hierarchical_{self.export_timestamp}.json")
        
        # Start with reference tables (no foreign keys pointing to them)
        root_tables = set()
        child_tables = set()
        
        for table, fks in self.relationships.items():
            for fk in fks:
                child_tables.add(fk['to_table'])
        
        for table in self.table_info.keys():
            if table not in child_tables:
                root_tables.add(table)
        
        # Build hierarchical structure
        exported = {}
        
        def export_table(table_name, parent_ref=None):
            """Recursively export table with its relationships"""
            if table_name in exported:
                return None  # Already exported, avoid cycles
            
            exported[table_name] = True
            
            # Get all rows
            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = [dict(row) for row in self.cursor.fetchall()]
            
            # For each row, find related data
            table_data = []
            for row in rows:
                row_data = dict(row)
                
                # Find child relationships (tables that reference this table)
                for other_table, fks in self.relationships.items():
                    if other_table != table_name:
                        for fk in fks:
                            if fk['to_table'] == table_name:
                                # Get matching rows
                                from_col = fk['from_column']
                                to_col = fk['to_column']
                                
                                # Determine which column to match on
                                if table_name == 'projects':
                                    if 'id' in row_data:
                                        match_value = row_data['id']
                                    elif 'job_number' in row_data:
                                        match_value = row_data['job_number']
                                    else:
                                        continue
                                else:
                                    if to_col in row_data:
                                        match_value = row_data[to_col]
                                    else:
                                        continue
                                
                                # Find related rows
                                if from_col == 'job_number' and isinstance(match_value, str):
                                    self.cursor.execute(
                                        f"SELECT * FROM {other_table} WHERE {from_col} = ?",
                                        (match_value,)
                                    )
                                elif isinstance(match_value, int):
                                    self.cursor.execute(
                                        f"SELECT * FROM {other_table} WHERE {from_col} = ?",
                                        (match_value,)
                                    )
                                else:
                                    continue
                                
                                related_rows = [dict(r) for r in self.cursor.fetchall()]
                                if related_rows:
                                    relation_name = f"{other_table}_via_{from_col}"
                                    row_data[relation_name] = related_rows
                
                # Find parent relationships (this table references others)
                if table_name in self.relationships:
                    for fk in self.relationships[table_name]:
                        from_col = fk['from_column']
                        to_table = fk['to_table']
                        to_col = fk['to_column']
                        
                        if from_col in row_data and row_data[from_col]:
                            if to_table == 'designers' or to_table == 'engineers':
                                self.cursor.execute(
                                    f"SELECT * FROM {to_table} WHERE {to_col} = ?",
                                    (row_data[from_col],)
                                )
                            elif to_table == 'projects':
                                # Projects can be referenced by id or job_number
                                if from_col.endswith('_id') or from_col == 'project_id':
                                    self.cursor.execute(
                                        f"SELECT * FROM {to_table} WHERE id = ?",
                                        (row_data[from_col],)
                                    )
                                else:
                                    self.cursor.execute(
                                        f"SELECT * FROM {to_table} WHERE {to_col} = ?",
                                        (row_data[from_col],)
                                    )
                            else:
                                continue
                            
                            parent_row = self.cursor.fetchone()
                            if parent_row:
                                row_data[f"_parent_{to_table}"] = dict(parent_row)
                
                table_data.append(row_data)
            
            return table_data if table_data else None
        
        # Export starting from root tables
        result = {
            'export_metadata': {
                'timestamp': self.export_timestamp,
                'database_file': self.db_path,
                'export_type': 'hierarchical_with_relationships'
            },
            'schema_info': self.table_info,
            'relationships_map': self.relationships,
            'data': {}
        }
        
        # Export all tables
        for table in sorted(self.table_info.keys()):
            table_data = export_table(table)
            if table_data:
                result['data'][table] = table_data
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"[OK] Hierarchical JSON exported: {output_file}")
        return output_file
    
    def export_csv_files(self, output_dir="db_exports"):
        """Export each table as a separate CSV file"""
        os.makedirs(output_dir, exist_ok=True)
        csv_dir = os.path.join(output_dir, f"csv_tables_{self.export_timestamp}")
        os.makedirs(csv_dir, exist_ok=True)
        
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in self.cursor.fetchall()]
        
        csv_files = []
        for table in tables:
            csv_file = os.path.join(csv_dir, f"{table}.csv")
            
            self.cursor.execute(f"SELECT * FROM {table}")
            rows = self.cursor.fetchall()
            
            if rows:
                # Get column names
                columns = [description[0] for description in self.cursor.description]
                
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
                
                csv_files.append(csv_file)
                print(f"[OK] CSV exported: {csv_file} ({len(rows)} rows)")
        
        return csv_dir
    
    def export_relationship_diagram_html(self, output_dir="db_exports"):
        """Create an HTML file showing relationships visually"""
        os.makedirs(output_dir, exist_ok=True)
        html_file = os.path.join(output_dir, f"relationships_diagram_{self.export_timestamp}.html")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Relationship Diagram - {self.export_timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .metadata {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .table-section {{
            background: white;
            margin-bottom: 20px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .table-name {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .columns {{
            margin-bottom: 20px;
        }}
        .column {{
            padding: 8px;
            margin: 5px 0;
            border-left: 4px solid #3498db;
            background: #ecf0f1;
        }}
        .column.pk {{
            border-left-color: #e74c3c;
            font-weight: bold;
        }}
        .column.fk {{
            border-left-color: #f39c12;
        }}
        .relationships {{
            margin-top: 15px;
        }}
        .relationship {{
            padding: 10px;
            margin: 10px 0;
            background: #fff3cd;
            border-left: 4px solid #f39c12;
            border-radius: 4px;
        }}
        .relationship-detail {{
            font-size: 14px;
            color: #555;
            margin-top: 5px;
        }}
        .stats {{
            display: inline-block;
            margin-left: 10px;
            padding: 5px 10px;
            background: #3498db;
            color: white;
            border-radius: 4px;
            font-size: 12px;
        }}
        .no-data {{
            color: #999;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Database Relationship Diagram</h1>
        <p>Database: {os.path.basename(self.db_path)} | Exported: {self.export_timestamp}</p>
    </div>
    
    <div class="metadata">
        <h3>Export Information</h3>
        <p><strong>Database File:</strong> {self.db_path}</p>
        <p><strong>Export Timestamp:</strong> {self.export_timestamp}</p>
        <p><strong>Total Tables:</strong> {len(self.table_info)}</p>
        <p><strong>Total Relationships:</strong> {sum(len(fks) for fks in self.relationships.values())}</p>
    </div>
"""
        
        # Add each table
        for table_name in sorted(self.table_info.keys()):
            table = self.table_info[table_name]
            
            # Get row count
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            html_content += f"""
    <div class="table-section">
        <div class="table-name">
            {table_name}
            <span class="stats">{row_count} rows</span>
        </div>
        
        <div class="columns">
            <h3>Columns:</h3>
"""
            
            for col in table['columns']:
                col_class = ""
                if col['pk']:
                    col_class = "pk"
                elif any(fk['from_column'] == col['name'] for fk in table['foreign_keys']):
                    col_class = "fk"
                
                col_details = f"{col['name']} ({col['type']})"
                if col['not_null']:
                    col_details += " NOT NULL"
                if col['pk']:
                    col_details += " [PRIMARY KEY]"
                
                html_content += f"""
            <div class="column {col_class}">
                {col_details}
            </div>
"""
            
            # Show relationships
            if table_name in self.relationships:
                html_content += """
        <div class="relationships">
            <h3>Foreign Key Relationships:</h3>
"""
                for fk in self.relationships[table_name]:
                    html_content += f"""
            <div class="relationship">
                <strong>{table_name}.{fk['from_column']}</strong> → 
                <strong>{fk['to_table']}.{fk['to_column']}</strong>
                <div class="relationship-detail">
                    On Delete: {fk['on_delete'] or 'NO ACTION'}
                </div>
            </div>
"""
            
            # Show reverse relationships (who references this table)
            referenced_by = []
            for other_table, fks in self.relationships.items():
                for fk in fks:
                    if fk['to_table'] == table_name:
                        referenced_by.append({
                            'table': other_table,
                            'column': fk['from_column'],
                            'on_delete': fk['on_delete']
                        })
            
            if referenced_by:
                html_content += """
            <h3>Referenced By:</h3>
"""
                for ref in referenced_by:
                    html_content += f"""
            <div class="relationship">
                <strong>{ref['table']}.{ref['column']}</strong> → 
                <strong>{table_name}</strong>
                <div class="relationship-detail">
                    On Delete: {ref['on_delete'] or 'NO ACTION'}
                </div>
            </div>
"""
            
            html_content += """
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[OK] HTML diagram exported: {html_file}")
        return html_file
    
    def export_all(self, output_dir="db_exports"):
        """Export all formats"""
        print(f"\n{'='*60}")
        print(f"Database Relationship Exporter")
        print(f"{'='*60}")
        print(f"Database: {self.db_path}\n")
        
        self.connect()
        
        try:
            print("Analyzing database schema...")
            self.get_table_schema()
            print(f"Found {len(self.table_info)} tables")
            print(f"Found {sum(len(fks) for fks in self.relationships.values())} foreign key relationships\n")
            
            print("Exporting...\n")
            
            # Export all formats
            flat_json = self.export_flat_json(output_dir)
            hierarchical_json = self.export_hierarchical_json(output_dir)
            csv_dir = self.export_csv_files(output_dir)
            html_diagram = self.export_relationship_diagram_html(output_dir)
            
            print(f"\n{'='*60}")
            print("Export Complete!")
            print(f"{'='*60}")
            print(f"\nExported files:")
            print(f"  - Flat JSON: {flat_json}")
            print(f"  - Hierarchical JSON: {hierarchical_json}")
            print(f"  - CSV files: {csv_dir}")
            print(f"  - HTML Diagram: {html_diagram}")
            print(f"\nOpen the HTML file in a browser to view relationships visually!")
            print(f"{'='*60}\n")
            
            return {
                'flat_json': flat_json,
                'hierarchical_json': hierarchical_json,
                'csv_dir': csv_dir,
                'html_diagram': html_diagram
            }
            
        finally:
            self.close()


if __name__ == "__main__":
    import sys
    
    # Allow specifying database path as argument
    db_path = sys.argv[1] if len(sys.argv) > 1 else "drafting_tools.db"
    
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found!")
        sys.exit(1)
    
    exporter = DatabaseRelationshipExporter(db_path)
    exporter.export_all()

