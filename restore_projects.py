#!/usr/bin/env python3
"""
Project Restore Script
Restores projects from backup to a new base path.
"""

import os
import sys
import shutil
import json
from pathlib import Path

def restore_projects(new_base_path):
    """
    Restore projects from backup to a new base path
    
    Args:
        new_base_path: New base path (e.g., "C:/Projects" or "D:/Work")
    """
    backup_path = "./ProjectBackup"
    alias_file = os.path.join(backup_path, "ALIAS_MAPPING.txt")
    
    if not os.path.exists(alias_file):
        print("❌ Alias mapping file not found!")
        print(f"Expected: {alias_file}")
        print("Make sure you're running this from the directory containing the ProjectBackup folder")
        return
    
    with open(alias_file, 'r') as f:
        mapping = json.load(f)
    
    print("=== PROJECT RESTORATION ===")
    print(f"Backup Path: {backup_path}")
    print(f"New Base Path: {new_base_path}")
    print(f"Original Base Path: {mapping['source_base_path']}")
    print()
    
    # Create new base directory
    os.makedirs(new_base_path, exist_ok=True)
    
    successful = 0
    failed = 0
    
    for project in mapping["projects"]:
        job_num = project["job_number"]
        customer = project["customer_name"]
        location = project["customer_location"]
        relative_path = project["relative_path"]
        
        # Create new path
        new_project_path = os.path.join(new_base_path, relative_path)
        backup_project_path = project["backup_path"]
        
        try:
            # Create parent directories
            os.makedirs(os.path.dirname(new_project_path), exist_ok=True)
            
            # Copy from backup to new location
            if os.path.exists(new_project_path):
                shutil.rmtree(new_project_path)
            shutil.copytree(backup_project_path, new_project_path)
            
            print(f"✅ Job {job_num}: {customer} - {location}")
            print(f"   Restored to: {new_project_path}")
            successful += 1
            
        except Exception as e:
            print(f"❌ Job {job_num}: Error - {str(e)}")
            failed += 1
        
        print()
    
    print("=== RESTORATION SUMMARY ===")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 New Base Path: {new_base_path}")
    print()
    print("=== NEXT STEPS ===")
    print("1. Update your database paths if needed")
    print("2. Update any hardcoded F:/ paths in your scripts")
    print("3. Test the applications with the new paths")

def update_database_paths(new_base_path, db_path="drafting_tools.db"):
    """
    Update database paths from F:/ to new base path
    
    Args:
        new_base_path: New base path
        db_path: Path to the database file
    """
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update job_directory paths
    cursor.execute("SELECT job_number, job_directory FROM projects")
    projects = cursor.fetchall()
    
    updated = 0
    for job_num, old_path in projects:
        if old_path and old_path.startswith("F:/"):
            # Replace F:/ with new base path
            relative_path = old_path[3:]  # Remove "F:/"
            new_path = os.path.join(new_base_path, relative_path).replace("\\", "/")
            
            cursor.execute("""
                UPDATE projects 
                SET job_directory = ? 
                WHERE job_number = ?
            """, (new_path, job_num))
            
            print(f"Updated Job {job_num}: {old_path} -> {new_path}")
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated} database paths")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_projects.py <new_base_path>")
        print("Example: python restore_projects.py C:/Projects")
        print("Example: python restore_projects.py D:/Work")
        sys.exit(1)
    
    new_base_path = sys.argv[1]
    
    # Restore projects
    restore_projects(new_base_path)
    
    # Ask if user wants to update database
    print("\n" + "="*50)
    update_db = input("Do you want to update the database paths? (y/n): ").strip().lower()
    if update_db == 'y':
        update_database_paths(new_base_path)
        print("✅ Database paths updated!")
    else:
        print("ℹ️  Database paths not updated. You may need to update them manually.")
