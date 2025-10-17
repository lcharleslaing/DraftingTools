#!/usr/bin/env python3
"""
Print Package Workflow Engine
Handles stage transitions, auto-copying, and reviewer tracking
"""

import sqlite3
import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

class PrintPackageWorkflow:
    def __init__(self, db_path="drafting_tools.db"):
        self.db_path = db_path
        
        # Define the 8-stage workflow
        self.stages = {
            0: {"name": "Drafting-Print Package", "description": "Original print package (never modified)"},
            1: {"name": "Engineer Review", "description": "Engineering review and markups"},
            2: {"name": "Engineering QC Review", "description": "Engineering quality control review"},
            3: {"name": "Drafting Updates (ENG)", "description": "Drafting implements engineering changes"},
            4: {"name": "Lead Designer Review", "description": "Lead designer review"},
            5: {"name": "Production OPS Review", "description": "Production operations review"},
            6: {"name": "Drafting Updates (OPS)", "description": "Drafting implements operations changes"},
            7: {"name": "FINAL Print Package (Approved)", "description": "Final approved package for Dee"}
        }
        
        # Define workflow transitions
        self.transitions = {
            0: [1],  # Stage 0 -> Stage 1
            1: [2],  # Stage 1 -> Stage 2
            2: [3],  # Stage 2 -> Stage 3
            3: [4, 5],  # Stage 3 -> Stage 4 & 5 (parallel)
            4: [6],  # Stage 4 -> Stage 6
            5: [6],  # Stage 5 -> Stage 6
            6: [7],  # Stage 6 -> Stage 7
            7: []    # Stage 7 is final
        }
    
    def get_review_info(self, job_number: str) -> Optional[Dict]:
        """Get Print Package Review information for a job"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT review_id, status, current_stage, initialized_by, 
                       initialized_date, completed_date, notes
                FROM print_package_reviews 
                WHERE job_number = ?
            ''', (job_number,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'review_id': result[0],
                    'status': result[1],
                    'current_stage': result[2],
                    'initialized_by': result[3],
                    'initialized_date': result[4],
                    'completed_date': result[5],
                    'notes': result[6]
                }
            return None
            
        except Exception as e:
            print(f"Error getting review info: {e}")
            return None
    
    def get_workflow_status(self, job_number: str) -> List[Dict]:
        """Get workflow status for all stages of a job"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stage, stage_name, reviewer, department, status, 
                       started_date, completed_date, notes
                FROM print_package_workflow 
                WHERE job_number = ?
                ORDER BY stage
            ''', (job_number,))
            
            results = cursor.fetchall()
            conn.close()
            
            workflow = []
            for result in results:
                stage, stage_name, reviewer, department, status, started_date, completed_date, notes = result
                workflow.append({
                    'stage': stage,
                    'stage_name': stage_name,
                    'reviewer': reviewer,
                    'department': department,
                    'status': status,
                    'started_date': started_date,
                    'completed_date': completed_date,
                    'notes': notes
                })
            
            return workflow
            
        except Exception as e:
            print(f"Error getting workflow status: {e}")
            return []
    
    def get_files_for_stage(self, job_number: str, stage: int) -> List[Dict]:
        """Get all files for a specific stage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the review_id first
            cursor.execute('SELECT review_id FROM print_package_reviews WHERE job_number = ?', (job_number,))
            review_result = cursor.fetchone()
            
            if not review_result:
                conn.close()
                return []
            
            review_id = review_result[0]
            
            # Get files for this stage
            stage_column = f"stage_{stage}_path"
            cursor.execute(f'''
                SELECT file_name, {stage_column}, file_size, created_date
                FROM print_package_files 
                WHERE review_id = ? AND {stage_column} IS NOT NULL
                ORDER BY file_name
            ''', (review_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            files = []
            for result in results:
                file_name, stage_path, file_size, created_date = result
                files.append({
                    'file_name': file_name,
                    'stage_path': stage_path,
                    'file_size': file_size,
                    'created_date': created_date,
                    'exists': os.path.exists(stage_path) if stage_path else False
                })
            
            return files
            
        except Exception as e:
            print(f"Error getting files for stage {stage}: {e}")
            return []
    
    def advance_to_next_stage(self, job_number: str, current_stage: int, 
                            reviewer: str, department: str, notes: str = "") -> bool:
        """Advance workflow to the next stage(s)"""
        try:
            # Get review info
            review_info = self.get_review_info(job_number)
            if not review_info:
                print(f"No review found for job {job_number}")
                return False
            
            review_id = review_info['review_id']
            
            # Check if current stage is completed
            if not self.is_stage_completed(job_number, current_stage):
                print(f"Stage {current_stage} is not completed yet")
                return False
            
            # Get next stages
            next_stages = self.transitions.get(current_stage, [])
            if not next_stages:
                print(f"Stage {current_stage} is the final stage")
                return False
            
            # Copy files to next stages
            success = True
            for next_stage in next_stages:
                if not self.copy_files_to_stage(job_number, current_stage, next_stage):
                    success = False
                    print(f"Failed to copy files to stage {next_stage}")
            
            if not success:
                return False
            
            # Update workflow records
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Mark current stage as completed
            cursor.execute('''
                UPDATE print_package_workflow 
                SET status = 'completed', completed_date = ?, notes = ?
                WHERE review_id = ? AND stage = ?
            ''', (datetime.now().isoformat(), notes, review_id, current_stage))
            
            # Start next stages
            for next_stage in next_stages:
                cursor.execute('''
                    UPDATE print_package_workflow 
                    SET status = 'in_progress', started_date = ?, reviewer = ?, department = ?
                    WHERE review_id = ? AND stage = ?
                ''', (datetime.now().isoformat(), reviewer, department, review_id, next_stage))
            
            # Update current stage in review record
            new_current_stage = max(next_stages) if next_stages else current_stage
            cursor.execute('''
                UPDATE print_package_reviews 
                SET current_stage = ?
                WHERE review_id = ?
            ''', (new_current_stage, review_id))
            
            conn.commit()
            conn.close()
            
            print(f"Successfully advanced job {job_number} from stage {current_stage} to stages {next_stages}")
            return True
            
        except Exception as e:
            print(f"Error advancing workflow: {e}")
            return False
    
    def copy_files_to_stage(self, job_number: str, from_stage: int, to_stage: int) -> bool:
        """Copy files from one stage to another"""
        try:
            # Get review info
            review_info = self.get_review_info(job_number)
            if not review_info:
                return False
            
            review_id = review_info['review_id']
            
            # Get job directory
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT job_directory FROM projects WHERE job_number = ?', (job_number,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            job_directory = result[0]
            conn.close()
            
            # Construct paths
            pp_base_path = os.path.join(job_directory, "4. Drafting", "PP-Print Packages")
            from_stage_path = os.path.join(pp_base_path, f"{from_stage}-{self.stages[from_stage]['name']}")
            to_stage_path = os.path.join(pp_base_path, f"{to_stage}-{self.stages[to_stage]['name']}")
            
            # Ensure destination directory exists
            os.makedirs(to_stage_path, exist_ok=True)
            
            # Get files from source stage
            from_column = f"stage_{from_stage}_path"
            to_column = f"stage_{to_stage}_path"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                SELECT file_name, {from_column}
                FROM print_package_files 
                WHERE review_id = ? AND {from_column} IS NOT NULL
            ''', (review_id,))
            
            files = cursor.fetchall()
            
            # Copy files
            for file_name, source_path in files:
                if os.path.exists(source_path):
                    dest_path = os.path.join(to_stage_path, file_name)
                    shutil.copy2(source_path, dest_path)
                    
                    # Update database with new path
                    cursor.execute(f'''
                        UPDATE print_package_files 
                        SET {to_column} = ?
                        WHERE review_id = ? AND file_name = ?
                    ''', (dest_path, review_id, file_name))
            
            conn.commit()
            conn.close()
            
            print(f"Copied files from stage {from_stage} to stage {to_stage}")
            return True
            
        except Exception as e:
            print(f"Error copying files: {e}")
            return False
    
    def is_stage_completed(self, job_number: str, stage: int) -> bool:
        """Check if a stage is completed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status FROM print_package_workflow 
                WHERE job_number = ? AND stage = ?
            ''', (job_number, stage))
            
            result = cursor.fetchone()
            conn.close()
            
            return result and result[0] == 'completed'
            
        except Exception as e:
            print(f"Error checking stage completion: {e}")
            return False
    
    def complete_stage(self, job_number: str, stage: int, reviewer: str, 
                      department: str, notes: str = "") -> bool:
        """Mark a stage as completed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get review_id
            cursor.execute('SELECT review_id FROM print_package_reviews WHERE job_number = ?', (job_number,))
            review_result = cursor.fetchone()
            
            if not review_result:
                conn.close()
                return False
            
            review_id = review_result[0]
            
            # Update workflow record
            cursor.execute('''
                UPDATE print_package_workflow 
                SET status = 'completed', completed_date = ?, reviewer = ?, department = ?, notes = ?
                WHERE review_id = ? AND stage = ?
            ''', (datetime.now().isoformat(), reviewer, department, notes, review_id, stage))
            
            conn.commit()
            conn.close()
            
            print(f"Stage {stage} completed by {reviewer} ({department})")
            return True
            
        except Exception as e:
            print(f"Error completing stage: {e}")
            return False
    
    def get_pending_reviews(self, department: str = None) -> List[Dict]:
        """Get all pending reviews, optionally filtered by department"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if department:
                cursor.execute('''
                    SELECT p.job_number, p.customer_name, pw.stage, pw.stage_name, 
                           pw.department, pw.started_date, pw.notes
                    FROM print_package_workflow pw
                    JOIN print_package_reviews pr ON pw.review_id = pr.review_id
                    JOIN projects p ON pr.job_number = p.job_number
                    WHERE pw.status = 'in_progress' AND pw.department = ?
                    ORDER BY pw.started_date ASC
                ''', (department,))
            else:
                cursor.execute('''
                    SELECT p.job_number, p.customer_name, pw.stage, pw.stage_name, 
                           pw.department, pw.started_date, pw.notes
                    FROM print_package_workflow pw
                    JOIN print_package_reviews pr ON pw.review_id = pr.review_id
                    JOIN projects p ON pr.job_number = p.job_number
                    WHERE pw.status = 'in_progress'
                    ORDER BY pw.started_date ASC
                ''')
            
            results = cursor.fetchall()
            conn.close()
            
            pending = []
            for result in results:
                job_number, customer_name, stage, stage_name, dept, started_date, notes = result
                pending.append({
                    'job_number': job_number,
                    'customer_name': customer_name,
                    'stage': stage,
                    'stage_name': stage_name,
                    'department': dept,
                    'started_date': started_date,
                    'notes': notes
                })
            
            return pending
            
        except Exception as e:
            print(f"Error getting pending reviews: {e}")
            return []
    
    def get_workflow_summary(self, job_number: str) -> Dict:
        """Get a complete workflow summary for a job"""
        try:
            review_info = self.get_review_info(job_number)
            if not review_info:
                return {}
            
            workflow_status = self.get_workflow_status(job_number)
            
            # Calculate progress
            total_stages = len(self.stages)
            completed_stages = sum(1 for stage in workflow_status if stage['status'] == 'completed')
            progress_percentage = (completed_stages / total_stages) * 100
            
            # Get current stage info
            current_stage = review_info['current_stage']
            current_stage_info = next(
                (stage for stage in workflow_status if stage['stage'] == current_stage), 
                None
            )
            
            return {
                'review_info': review_info,
                'workflow_status': workflow_status,
                'progress_percentage': progress_percentage,
                'completed_stages': completed_stages,
                'total_stages': total_stages,
                'current_stage_info': current_stage_info,
                'is_complete': current_stage == 7 and current_stage_info and current_stage_info['status'] == 'completed'
            }
            
        except Exception as e:
            print(f"Error getting workflow summary: {e}")
            return {}

def main():
    """Test the workflow engine"""
    workflow = PrintPackageWorkflow()
    
    # Test getting pending reviews
    pending = workflow.get_pending_reviews()
    print(f"Pending reviews: {len(pending)}")
    
    for review in pending:
        print(f"  {review['job_number']} - {review['stage_name']} ({review['department']})")

if __name__ == "__main__":
    main()
