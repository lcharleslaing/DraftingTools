#!/usr/bin/env python3
"""
Project Backup Script
Backs up all project directories from the database to a portable backup location.
Handles F:/ drive mapping by using configurable base paths.
"""

import os
import sqlite3
import shutil
import json
from datetime import datetime
from pathlib import Path
from database_setup import DatabaseManager

class ProjectBackup:
    def __init__(self, backup_base_path=None, source_base_path="F:/"):
        """
        Initialize the backup system
        
        Args:
            backup_base_path: Where to store the backup (default: ./ProjectBackup)
            source_base_path: The base path to replace (default: "F:/")
        """
        self.db_manager = DatabaseManager()
        self.source_base_path = source_base_path.rstrip('/')
        self.backup_base_path = backup_base_path or os.path.join(os.getcwd(), "ProjectBackup")
        self.alias_path = os.path.join(self.backup_base_path, "ALIAS_MAPPING.txt")
        
        # Create backup directory
        os.makedirs(self.backup_base_path, exist_ok=True)
        
    def get_all_projects(self):
        """Get all projects from the database"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT job_number, customer_name, customer_location, job_directory
            FROM projects 
            ORDER BY job_number
        ''')
        
        projects = cursor.fetchall()
        conn.close()
        return projects
    
    def create_alias_mapping(self, projects):
        """Create an alias mapping file for easy restoration"""
        mapping = {
            "backup_created": datetime.now().isoformat(),
            "source_base_path": self.source_base_path,
            "backup_base_path": self.backup_base_path,
            "projects": []
        }
        
        for job_num, customer, location, job_dir in projects:
            if job_dir and job_dir.startswith(self.source_base_path):
                # Extract the relative path
                relative_path = job_dir[len(self.source_base_path):].lstrip('/')
                backup_path = os.path.join(self.backup_base_path, relative_path)
                
                mapping["projects"].append({
                    "job_number": job_num,
                    "customer_name": customer,
                    "customer_location": location,
                    "original_path": job_dir,
                    "backup_path": backup_path,
                    "relative_path": relative_path
                })
        
        # Save mapping file
        with open(self.alias_path, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        return mapping
    
    def backup_project(self, job_num, customer, location, job_dir):
        """Backup a single project directory"""
        if not job_dir or not os.path.exists(job_dir):
            print(f"⚠️  Job {job_num}: Directory not found - {job_dir}")
            return False
        
        # Create relative path structure
        relative_path = job_dir[len(self.source_base_path):].lstrip('/')
        backup_path = os.path.join(self.backup_base_path, relative_path)
        
        try:
            # Create parent directories
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy the entire directory
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.copytree(job_dir, backup_path)
            
            print(f"✅ Job {job_num}: {customer} - {location}")
            print(f"   From: {job_dir}")
            print(f"   To:   {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Job {job_num}: Error - {str(e)}")
            return False
    
    def backup_all_projects(self):
        """Backup all projects from the database"""
        print("=== PROJECT BACKUP SCRIPT ===")
        print(f"Source Base Path: {self.source_base_path}")
        print(f"Backup Base Path: {self.backup_base_path}")
        print()
        
        projects = self.get_all_projects()
        print(f"Found {len(projects)} projects in database")
        print()
        
        # Create alias mapping
        mapping = self.create_alias_mapping(projects)
        print("📝 Created alias mapping file")
        print()
        
        # Backup each project
        successful = 0
        failed = 0
        
        for job_num, customer, location, job_dir in projects:
            if self.backup_project(job_num, customer, location, job_dir):
                successful += 1
            else:
                failed += 1
            print()
        
        print("=== BACKUP SUMMARY ===")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Backup Location: {self.backup_base_path}")
        print(f"📝 Alias Mapping: {self.alias_path}")
        print()
        print("=== RESTORATION INSTRUCTIONS ===")
        print("1. Copy the entire backup folder to your home PC")
        print("2. Run the restore script with your desired base path")
        print("3. Update the database paths if needed")
        
        return successful, failed

def restore_projects(backup_path, new_base_path):
    """
    Restore projects from backup to a new base path
    
    Args:
        backup_path: Path to the backup folder
        new_base_path: New base path (e.g., "C:/Projects" or "D:/Work")
    """
    alias_file = os.path.join(backup_path, "ALIAS_MAPPING.txt")
    
    if not os.path.exists(alias_file):
        print("❌ Alias mapping file not found!")
        return
    
    with open(alias_file, 'r') as f:
        mapping = json.load(f)
    
    print("=== PROJECT RESTORATION ===")
    print(f"Backup Path: {backup_path}")
    print(f"New Base Path: {new_base_path}")
    print()
    
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

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        # Restoration mode
        if len(sys.argv) < 4:
            print("Usage: python backup_projects.py restore <backup_path> <new_base_path>")
            print("Example: python backup_projects.py restore ./ProjectBackup C:/Projects")
            sys.exit(1)
        
        backup_path = sys.argv[2]
        new_base_path = sys.argv[3]
        restore_projects(backup_path, new_base_path)
    
    else:
        # Backup mode
        backup_base = input("Enter backup location (press Enter for ./ProjectBackup): ").strip()
        if not backup_base:
            backup_base = "./ProjectBackup"
        
        source_base = input("Enter source base path (press Enter for F:/): ").strip()
        if not source_base:
            source_base = "F:/"
        
        backup_system = ProjectBackup(backup_base, source_base)
        backup_system.backup_all_projects()
