#!/usr/bin/env python3
"""
Simple Project Backup Script
Backs up all project directories from the database.
"""

import os
import sqlite3
import shutil
import json
from datetime import datetime
from database_setup import DatabaseManager

def backup_all_projects():
    """Backup all projects from the database"""
    print("=== PROJECT BACKUP SCRIPT ===")
    
    # Configuration
    source_base_path = "F:/"
    backup_base_path = "./ProjectBackup"
    
    print(f"Source Base Path: {source_base_path}")
    print(f"Backup Base Path: {backup_base_path}")
    print()
    
    # Create backup directory
    os.makedirs(backup_base_path, exist_ok=True)
    
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
    
    # Create alias mapping
    mapping = {
        "backup_created": datetime.now().isoformat(),
        "source_base_path": source_base_path,
        "backup_base_path": backup_base_path,
        "projects": []
    }
    
    successful = 0
    failed = 0
    
    for job_num, customer, location, job_dir in projects:
        if not job_dir or not job_dir.startswith(source_base_path):
            print(f"[WARNING] Job {job_num}: Invalid directory path - {job_dir}")
            failed += 1
            continue
            
        if not os.path.exists(job_dir):
            print(f"[WARNING] Job {job_num}: Directory not found - {job_dir}")
            failed += 1
            continue
        
        # Create relative path structure
        relative_path = job_dir[len(source_base_path):].lstrip('/')
        backup_path = os.path.join(backup_base_path, relative_path)
        
        try:
            # Create parent directories
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy the entire directory
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.copytree(job_dir, backup_path)
            
            print(f"[OK] Job {job_num}: {customer} - {location}")
            print(f"   From: {job_dir}")
            print(f"   To:   {backup_path}")
            
            # Add to mapping
            mapping["projects"].append({
                "job_number": job_num,
                "customer_name": customer,
                "customer_location": location,
                "original_path": job_dir,
                "backup_path": backup_path,
                "relative_path": relative_path
            })
            
            successful += 1
            
        except Exception as e:
            print(f"[ERROR] Job {job_num}: Error - {str(e)}")
            failed += 1
        
        print()
    
    # Save mapping file
    alias_path = os.path.join(backup_base_path, "ALIAS_MAPPING.txt")
    with open(alias_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print("=== BACKUP SUMMARY ===")
    print(f"[SUCCESS] Successful: {successful}")
    print(f"[FAILED] Failed: {failed}")
    print(f"[BACKUP] Backup Location: {backup_base_path}")
    print(f"[MAPPING] Alias Mapping: {alias_path}")
    print()
    print("=== RESTORATION INSTRUCTIONS ===")
    print("1. Copy the entire 'ProjectBackup' folder to your home PC")
    print("2. Run: python restore_projects.py <new_base_path>")
    print("3. Example: python restore_projects.py C:/Projects")
    print("4. This will create the same structure under your new base path")
    
    return successful, failed

if __name__ == "__main__":
    backup_all_projects()
