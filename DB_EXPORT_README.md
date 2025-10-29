# Database Relationship Exporter

A comprehensive tool to export your entire database with all relationships clearly visible.

## Quick Start

Simply run:
```bash
python db_relationship_exporter.py
```

Or specify a different database:
```bash
python db_relationship_exporter.py path/to/other_database.db
```

## What It Exports

The tool creates **4 types of exports** in the `db_exports/` folder:

### 1. **Flat JSON** (`all_tables_flat_*.json`)
   - All tables exported as a simple flat structure
   - Each table has an array of all its rows
   - Similar to the existing `master_data.json` format

### 2. **Hierarchical JSON** (`relationships_hierarchical_*.json`)
   - **Most useful for seeing relationships!**
   - Includes complete schema information
   - Shows all foreign key relationships mapped
   - Data organized to show parent-child relationships
   - Each row includes nested related data from child tables
   - Each row includes parent reference data

### 3. **CSV Files** (`csv_tables_*/`)
   - One CSV file per table
   - Easy to open in Excel or other tools
   - All 52 tables exported separately
   - Row counts shown for each file

### 4. **HTML Relationship Diagram** (`relationships_diagram_*.html`)
   - **Visual representation of all relationships**
   - Open in any web browser
   - Shows:
     - All tables with their columns
     - Primary keys (highlighted in red)
     - Foreign keys (highlighted in orange)
     - Relationships mapped (which table references which)
     - Row counts for each table
     - "On Delete" cascade rules

## Understanding the Relationships

The tool identifies **3 types of relationships**:

1. **Parent References**: Shows what table a row references (via foreign keys)
2. **Child References**: Shows what other tables reference this table
3. **Relationship Metadata**: Includes cascade rules and join information

## Example Use Cases

- **Data Migration**: See all relationships before moving data
- **Database Auditing**: Understand the complete schema structure
- **Documentation**: HTML diagram serves as visual documentation
- **Analysis**: CSV files can be analyzed in Excel/Power BI
- **Backup**: JSON exports can be used for data backup/restore

## Files Created

Each export run creates a timestamped folder structure:
```
db_exports/
├── all_tables_flat_20251029_094933.json
├── relationships_hierarchical_20251029_094933.json
├── csv_tables_20251029_094933/
│   ├── projects.csv
│   ├── designers.csv
│   ├── initial_redline.csv
│   └── ... (all 52 tables)
└── relationships_diagram_20251029_094933.html
```

## Integration

You can import this tool into other scripts:

```python
from db_relationship_exporter import DatabaseRelationshipExporter

exporter = DatabaseRelationshipExporter("drafting_tools.db")
results = exporter.export_all()
# Returns dict with paths to all exported files
```

## Notes

- The tool automatically detects all tables and foreign key relationships
- No data is modified - read-only operations only
- All exports are timestamped to prevent overwrites
- UTF-8 encoding used for international character support

