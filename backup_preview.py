#!/usr/bin/env python3
"""
Project Backup Preview Script
Shows what would be backed up without actually copying files.
"""

import os
import sqlite3
from database_setup import DatabaseManager

def preview_backup():
    """Preview what would be backed up"""
    print("=== PROJECT BACKUP PREVIEW ===")
    
    # Configuration
    source_base_path = "F:/"
    backup_base_path = "./ProjectBackup"
    
    print(f"Source Base Path: {source_base_path}")
    print(f"Backup Base Path: {backup_base_path}")
    print()
    
    # Get projects from database
    db_manager = DatabaseManager()
    conn = sqlite3.connect(db_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT job_number, customer_name, customer_location, job_directory
        FROM projects 
        ORDER BY job_number
    ''')
    
    projects = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(projects)} projects in database")
    print()
    
    total_size = 0
    existing_dirs = 0
    missing_dirs = 0
    
    for job_num, customer, location, job_dir in projects:
        if not job_dir or not job_dir.startswith(source_base_path):
            print(f"[SKIP] Job {job_num}: Invalid directory path - {job_dir}")
            continue
            
        if not os.path.exists(job_dir):
            print(f"[MISSING] Job {job_num}: Directory not found - {job_dir}")
            missing_dirs += 1
            continue
        
        # Calculate directory size
        try:
            dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                          for dirpath, dirnames, filenames in os.walk(job_dir)
                          for filename in filenames)
            total_size += dir_size
            
            # Convert to MB
            size_mb = dir_size / (1024 * 1024)
            
            print(f"[FOUND] Job {job_num}: {customer} - {location}")
            print(f"   Directory: {job_dir}")
            print(f"   Size: {size_mb:.1f} MB")
            print(f"   Backup to: {backup_base_path}/{job_dir[3:]}")
            existing_dirs += 1
            
        except Exception as e:
            print(f"[ERROR] Job {job_num}: Error calculating size - {str(e)}")
            missing_dirs += 1
        
        print()
    
    print("=== BACKUP PREVIEW SUMMARY ===")
    print(f"[FOUND] Directories found: {existing_dirs}")
    print(f"[MISSING] Directories missing: {missing_dirs}")
    print(f"[TOTAL] Total size: {total_size / (1024 * 1024):.1f} MB")
    print(f"[BACKUP] Would backup to: {backup_base_path}")
    print()
    
    if existing_dirs > 0:
        print("=== TO ACTUALLY BACKUP ===")
        print("Run: python backup_projects_simple.py")
        print()
        print("=== TO RESTORE ON HOME PC ===")
        print("1. Copy the 'ProjectBackup' folder to your home PC")
        print("2. Run: python restore_projects.py C:/Projects")
        print("3. This will create the same structure under C:/Projects")
        print("4. Update database paths if needed")
    else:
        print("No directories found to backup!")

if __name__ == "__main__":
    preview_backup()
