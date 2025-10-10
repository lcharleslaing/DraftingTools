import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
from database_setup import DatabaseManager
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

class ProjectCoverSheet:
    def __init__(self, job_number, db_manager):
        self.job_number = job_number
        self.db_manager = db_manager
        self.project_data = None
        self.workflow_data = None
        
    def load_project_data(self):
        """Load project and workflow data from database"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Load main project data
        query = """
        SELECT p.job_number, p.job_directory, p.customer_name, p.customer_location,
               d.name as assigned_to, p.assignment_date, p.start_date, p.completion_date, 
               p.total_duration_days, p.released_to_dee
        FROM projects p
        LEFT JOIN designers d ON p.assigned_to_id = d.id
        WHERE p.job_number = ?
        """
        
        cursor.execute(query, (self.job_number,))
        self.project_data = cursor.fetchone()
        
        if not self.project_data:
            conn.close()
            return False
            
        # Get project ID for workflow data
        cursor.execute("SELECT id FROM projects WHERE job_number = ?", (self.job_number,))
        project_id = cursor.fetchone()[0]
        
        # Load workflow data
        self.workflow_data = {}
        
        # Initial redline
        cursor.execute("""
            SELECT ir.redline_date, e.name, ir.is_completed
            FROM initial_redline ir
            LEFT JOIN engineers e ON ir.engineer_id = e.id
            WHERE ir.project_id = ?
        """, (project_id,))
        initial_result = cursor.fetchone()
        self.workflow_data['initial_redline'] = initial_result if initial_result else None
        
        # Redline updates
        cursor.execute("""
            SELECT ru.update_cycle, ru.update_date, e.name, ru.is_completed
            FROM redline_updates ru
            LEFT JOIN engineers e ON ru.engineer_id = e.id
            WHERE ru.project_id = ?
            ORDER BY ru.update_cycle
        """, (project_id,))
        redline_updates_result = cursor.fetchall()
        self.workflow_data['redline_updates'] = redline_updates_result if redline_updates_result else []
        
        # OPS review
        cursor.execute("""
            SELECT review_date, is_completed
            FROM ops_review
            WHERE project_id = ?
        """, (project_id,))
        ops_result = cursor.fetchone()
        self.workflow_data['ops_review'] = ops_result if ops_result else None
        
        # Peter Weck review
        cursor.execute("""
            SELECT fixed_errors_date, is_completed
            FROM peter_weck_review
            WHERE project_id = ?
        """, (project_id,))
        peter_result = cursor.fetchone()
        self.workflow_data['peter_weck'] = peter_result if peter_result else None
        
        # Release to Dee
        cursor.execute("""
            SELECT release_date, missing_prints_date, d365_updates_date, 
                   other_notes, other_date, is_completed
            FROM release_to_dee
            WHERE project_id = ?
        """, (project_id,))
        release_result = cursor.fetchone()
        self.workflow_data['release_to_dee'] = release_result if release_result else None
        
        conn.close()
        return True
    
    def get_project_status(self):
        """Determine project status based on dates"""
        if self.project_data[7]:  # completion_date
            return "Completed"
        elif self.project_data[6]:  # start_date
            return "In Progress"
        else:
            return "Assigned"
    
    def format_date(self, date_str):
        """Format date string for display"""
        if not date_str:
            return "Not Set"
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%m/%d/%Y")
        except:
            return date_str
    
    def format_duration(self, days):
        """Format duration for display"""
        if not days:
            return "N/A"
        return f"{days} days"
    
    def create_cover_sheet_docx(self, output_path):
        """Create the project cover sheet as a Word document"""
        doc = Document()
        
        # Set page orientation to landscape
        section = doc.sections[0]
        section.page_width = Inches(11)  # Landscape width
        section.page_height = Inches(8.5)  # Landscape height
        
        # Set default font to Calibri
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Inches(0.1)
        
        # Job Number (BIG & no label)
        job_para = doc.add_paragraph()
        job_run = job_para.add_run(str(self.job_number))  # Convert to string
        job_run.font.name = 'Calibri'
        job_run.font.size = Inches(0.35)  # Large font
        job_run.bold = True
        job_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add some space
        doc.add_paragraph()
        
        # Customer Name and Location (BIG & no label)
        customer_name = self.project_data[2] or "Not Set"
        customer_location = self.project_data[3] or "Not Set"
        
        customer_para = doc.add_paragraph()
        customer_run = customer_para.add_run(customer_name)
        customer_run.font.name = 'Calibri'
        customer_run.font.size = Inches(0.2)
        customer_run.bold = True
        customer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        location_para = doc.add_paragraph()
        location_run = location_para.add_run(customer_location)
        location_run.font.name = 'Calibri'
        location_run.font.size = Inches(0.2)
        location_run.bold = True
        location_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add some space
        doc.add_paragraph()
        
        # Status (BIG & with label) - Updated format
        status = self.get_project_status()
        start_date = self.format_date(self.project_data[6]) if self.project_data[6] else "Not Set"
        
        status_para = doc.add_paragraph()
        if status == "In Progress":
            status_text = f"Status: {status}, Started: {start_date}"
        else:
            status_text = f"Status: {status}"
        status_run = status_para.add_run(status_text)
        status_run.font.name = 'Calibri'
        status_run.font.size = Inches(0.18)
        status_run.bold = True
        status_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add some space
        doc.add_paragraph()
        
        # Project Workflow Section - Latest Update/Next Up
        workflow_heading = doc.add_paragraph()
        workflow_run = workflow_heading.add_run("PROJECT WORKFLOW (Latest Update/Next Up)")
        workflow_run.font.name = 'Calibri'
        workflow_run.font.size = Inches(0.12)
        workflow_run.bold = True
        
        # Find latest completed and next pending
        latest_completed = None
        next_pending = None
        
        # Check redline updates for latest completed
        redline_updates = self.workflow_data.get('redline_updates', [])
        if redline_updates and isinstance(redline_updates, list):
            for update in reversed(redline_updates):  # Check from latest to earliest
                if isinstance(update, (list, tuple)) and len(update) >= 4:
                    if update[3]:  # is_completed
                        latest_completed = ("Redline Update", update[0], update[2], update[1])
                        break
        
        # Check other workflow steps
        workflow_steps = [
            ("Initial Redline", self.workflow_data.get('initial_redline')),
            ("OPS Review", self.workflow_data.get('ops_review')),
            ("Peter Weck Review", self.workflow_data.get('peter_weck')),
            ("Release to Dee", self.workflow_data.get('release_to_dee'))
        ]
        
        for step_name, step_data in workflow_steps:
            if step_data and isinstance(step_data, (list, tuple)) and len(step_data) >= 2:
                if step_data[1]:  # is_completed
                    if not latest_completed:  # Only set if no redline update is completed
                        latest_completed = (step_name, None, step_data[1] if len(step_data) > 2 else None, step_data[0])
                else:  # Not completed
                    if not next_pending:
                        next_pending = (step_name, None, step_data[1] if len(step_data) > 2 else None, step_data[0])
        
        # Display latest completed
        if latest_completed:
            step_name, step_num, engineer, date = latest_completed
            if step_num:
                doc.add_paragraph(f"   Update {step_num}: ✓ Completed")
            else:
                doc.add_paragraph(f"{step_name}: ✓ Completed")
            if engineer:
                doc.add_paragraph(f"   Engineer: {engineer}")
            if date:
                doc.add_paragraph(f"   Date: {self.format_date(date)}")
        
        # Display next pending
        if next_pending:
            step_name, step_num, engineer, date = next_pending
            if step_num:
                doc.add_paragraph(f"   Update {step_num}: ○ Pending")
            else:
                doc.add_paragraph(f"{step_name}: ○ Pending")
            if engineer:
                doc.add_paragraph(f"   Engineer: {engineer}")
            if date:
                doc.add_paragraph(f"   Date: {self.format_date(date)}")
        
        # Footer with generation date
        doc.add_paragraph()
        footer_para = doc.add_paragraph()
        footer_run = footer_para.add_run(f"Generated: {datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
        footer_run.font.name = 'Calibri'
        footer_run.font.size = Inches(0.08)
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Save the document
        doc.save(output_path)
        return True

def print_project_cover_sheet(job_number, db_manager):
    """Main function to create and print project cover sheet"""
    try:
        print(f"DEBUG: Starting cover sheet creation for job {job_number}")
        cover_sheet = ProjectCoverSheet(job_number, db_manager)
        
        if not cover_sheet.load_project_data():
            messagebox.showerror("Error", f"Project {job_number} not found!")
            return False
        
        print(f"DEBUG: Project data loaded successfully")
        print(f"DEBUG: Workflow data: {cover_sheet.workflow_data}")
        
        # Get job directory from project data
        job_directory = cover_sheet.project_data[1]  # job_directory is at index 1
        
        if not job_directory or not os.path.exists(job_directory):
            # Fallback to current directory if job directory not found
            output_dir = os.getcwd()
            messagebox.showwarning("Warning", f"Job directory not found. Saving to: {output_dir}")
        else:
            output_dir = job_directory
        
        # Create timestamped reports folder
        timestamp_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_folder = os.path.join(output_dir, f"Status_Reports_{timestamp_folder}")
        
        # Create the reports folder if it doesn't exist
        os.makedirs(reports_folder, exist_ok=True)
        
        # Create output filename
        output_filename = f"Project_Status_Report_{job_number}_{timestamp_folder}.docx"
        output_path = os.path.join(reports_folder, output_filename)
        
        print(f"DEBUG: About to create Word document at {output_path}")
        
        # Create Word document
        if cover_sheet.create_cover_sheet_docx(output_path):
            print(f"DEBUG: Word document created successfully")
            # Record the cover sheet generation date in the database
            try:
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE projects 
                    SET last_cover_sheet_date = ? 
                    WHERE job_number = ?
                """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_number))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning: Could not update cover sheet date: {e}")
            
            messagebox.showinfo("Success", f"Status report created: {output_filename}\nSaved to: {reports_folder}")
            
            # Open the Word document
            import subprocess
            subprocess.run(['start', output_path], shell=True)
            return True
        else:
            messagebox.showerror("Error", "Failed to create status report")
            return False
            
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to create status report: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the cover sheet generation
    db_manager = DatabaseManager()
    print_project_cover_sheet("35354", db_manager)
