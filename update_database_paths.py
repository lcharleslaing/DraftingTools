#!/usr/bin/env python3
"""
Simple script to update database paths after restoring projects at home
"""

import sqlite3
import os
import sys

def update_database_paths(new_base_path):
    """Update all job_directory paths in the database to the new base path"""
    
    # Ensure the path ends with a slash
    if not new_base_path.endswith('/') and not new_base_path.endswith('\\'):
        new_base_path += '/'
    
    # Connect to database
    db_path = 'drafting_tools.db'
    if not os.path.exists(db_path):
        print(f"ERROR: Database file '{db_path}' not found!")
        print("Make sure you're running this from the DraftingTools directory.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"=== UPDATING DATABASE PATHS ===")
    print(f"New base path: {new_base_path}")
    print()
    
    # Get all projects
    cursor.execute("SELECT job_number, customer_name, customer_location, job_directory FROM projects")
    projects = cursor.fetchall()
    
    if not projects:
        print("No projects found in database!")
        return False
    
    updated_count = 0
    
    for job_num, customer, location, old_path in projects:
        if not old_path or not old_path.startswith("F:/"):
            print(f"SKIP Job {job_num}: Invalid or non-F:/ path - {old_path}")
            continue
        
        # Extract the relative path from F:/...
        relative_path = old_path[3:]  # Remove "F:/"
        new_path = new_base_path + relative_path
        
        # Update the database
        cursor.execute("""
            UPDATE projects 
            SET job_directory = ? 
            WHERE job_number = ?
        """, (new_path, job_num))
        
        print(f"UPDATED Job {job_num}: {customer} - {location}")
        print(f"  Old: {old_path}")
        print(f"  New: {new_path}")
        print()
        
        updated_count += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"=== UPDATE COMPLETE ===")
    print(f"Updated {updated_count} project paths")
    print(f"Database saved: {db_path}")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python update_database_paths.py <new_base_path>")
        print()
        print("Examples:")
        print("  python update_database_paths.py C:/Projects/")
        print("  python update_database_paths.py D:/Work/Projects/")
        print("  python update_database_paths.py C:\\Projects\\")
        sys.exit(1)
    
    new_base_path = sys.argv[1]
    
    # Convert backslashes to forward slashes for consistency
    new_base_path = new_base_path.replace('\\', '/')
    
    success = update_database_paths(new_base_path)
    
    if success:
        print()
        print("✅ Database paths updated successfully!")
        print("Your drafting tools should now work with the restored projects.")
    else:
        print()
        print("❌ Failed to update database paths.")
        sys.exit(1)

if __name__ == "__main__":
    main()
