#!/usr/bin/env python3
"""
Retry failed backup for specific project
"""

import os
import shutil
import json
from database_setup import DatabaseManager
import sqlite3

def retry_failed_backup(job_number):
    """Retry backup for a specific failed project"""
    print(f"=== RETRYING BACKUP FOR JOB {job_number} ===")
    
    # Get project info from database
    db_manager = DatabaseManager()
    conn = sqlite3.connect(db_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT job_number, customer_name, customer_location, job_directory
        FROM projects 
        WHERE job_number = ?
    ''', (job_number,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"Job {job_number} not found in database!")
        return False
    
    job_num, customer, location, job_dir = result
    
    if not job_dir or not job_dir.startswith("F:/"):
        print(f"Invalid directory path: {job_dir}")
        return False
        
    if not os.path.exists(job_dir):
        print(f"Directory not found: {job_dir}")
        return False
    
    # Create backup path
    source_base_path = "F:/"
    backup_base_path = "./ProjectBackup"
    relative_path = job_dir[len(source_base_path):].lstrip('/')
    backup_path = os.path.join(backup_base_path, relative_path)
    
    print(f"From: {job_dir}")
    print(f"To:   {backup_path}")
    print()
    
    try:
        # Remove existing backup if it exists
        if os.path.exists(backup_path):
            print("Removing existing partial backup...")
            shutil.rmtree(backup_path)
        
        # Create parent directories
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copy with error handling for locked files
        print("Copying files (skipping locked files)...")
        copy_with_skip(job_dir, backup_path)
        
        print(f"[SUCCESS] Job {job_number}: {customer} - {location}")
        
        # Update the alias mapping file
        update_alias_mapping(job_number, customer, location, job_dir, backup_path, relative_path)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Job {job_number}: Error - {str(e)}")
        return False

def copy_with_skip(src, dst):
    """Copy directory tree, skipping files that can't be accessed"""
    os.makedirs(dst, exist_ok=True)
    
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        
        try:
            if os.path.isdir(src_path):
                copy_with_skip(src_path, dst_path)
            else:
                # Try to copy the file
                try:
                    shutil.copy2(src_path, dst_path)
                except (PermissionError, OSError) as e:
                    print(f"  Skipping locked file: {src_path} - {str(e)}")
                    # Create a placeholder file
                    with open(dst_path + ".LOCKED", 'w') as f:
                        f.write(f"Original file locked: {src_path}\nError: {str(e)}")
        except Exception as e:
            print(f"  Error with {src_path}: {str(e)}")

def update_alias_mapping(job_number, customer, location, original_path, backup_path, relative_path):
    """Update the alias mapping file with the retried project"""
    alias_file = "./ProjectBackup/ALIAS_MAPPING.txt"
    
    if os.path.exists(alias_file):
        with open(alias_file, 'r') as f:
            mapping = json.load(f)
    else:
        mapping = {
            "backup_created": "2025-10-10T16:45:40.427774",
            "source_base_path": "F:/",
            "backup_base_path": "./ProjectBackup",
            "projects": []
        }
    
    # Add or update the project entry
    project_entry = {
        "job_number": job_number,
        "customer_name": customer,
        "customer_location": location,
        "original_path": original_path,
        "backup_path": backup_path,
        "relative_path": relative_path
    }
    
    # Remove existing entry if it exists
    mapping["projects"] = [p for p in mapping["projects"] if p["job_number"] != job_number]
    
    # Add new entry
    mapping["projects"].append(project_entry)
    
    # Save updated mapping
    with open(alias_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Updated alias mapping file with job {job_number}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python retry_failed_backup.py <job_number>")
        print("Example: python retry_failed_backup.py 35354")
        sys.exit(1)
    
    job_number = sys.argv[1]
    retry_failed_backup(job_number)
