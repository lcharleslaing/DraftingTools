#!/usr/bin/env python3
"""
Check backup status
"""

import os
import json
from database_setup import DatabaseManager
import sqlite3

def check_backup_status():
    """Check the current backup status"""
    backup_path = "./ProjectBackup"
    alias_file = os.path.join(backup_path, "ALIAS_MAPPING.txt")
    
    print("=== BACKUP STATUS CHECK ===")
    print(f"Backup Path: {backup_path}")
    print()
    
    # Check if backup directory exists
    if not os.path.exists(backup_path):
        print("Backup directory not found!")
        return
    
    # Check if alias mapping exists
    if os.path.exists(alias_file):
        print("Backup completed! Alias mapping file found.")
        with open(alias_file, 'r') as f:
            mapping = json.load(f)
        
        print(f"Backup created: {mapping['backup_created']}")
        print(f"Projects backed up: {len(mapping['projects'])}")
        print()
        
        for project in mapping['projects']:
            job_num = project['job_number']
            customer = project['customer_name']
            location = project['customer_location']
            backup_dir = project['backup_path']
            
            if os.path.exists(backup_dir):
                print(f"[OK] Job {job_num}: {customer} - {location}")
            else:
                print(f"[MISSING] Job {job_num}: {customer} - {location}")
    else:
        print("Backup in progress...")
        
        # Count what's been backed up so far
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
        
        backed_up = 0
        for job_num, customer, location, job_dir in projects:
            if job_dir and job_dir.startswith("F:/"):
                relative_path = job_dir[3:]  # Remove "F:/"
                backup_dir = os.path.join(backup_path, relative_path)
                if os.path.exists(backup_dir):
                    backed_up += 1
                    print(f"[OK] Job {job_num}: {customer} - {location}")
        
        print(f"\nProgress: {backed_up}/{len(projects)} projects backed up")

if __name__ == "__main__":
    check_backup_status()
