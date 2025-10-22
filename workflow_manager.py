#!/usr/bin/env python3
"""
Workflow Manager UI
Provides interface for managing Print Package Review workflows
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from print_package_workflow import PrintPackageWorkflow
from scroll_utils import bind_mousewheel_to_canvas
from ui_prefs import bind_tree_column_persistence
from notes_utils import open_add_note_dialog
from app_nav import add_app_bar
from settings import SettingsManager

class WorkflowManagerApp:
    def __init__(self, parent=None):
        self.workflow_engine = PrintPackageWorkflow()
        self.settings_manager = SettingsManager()
        
        if parent:
            self.root = parent
        else:
            self.root = tk.Tk()
            self.root.title("Print Package Workflow Manager")
            self.root.geometry("1200x800")
            try:
                self.root.state('zoomed')
            except Exception:
                try:
                    self.root.attributes('-zoomed', True)
                except Exception:
                    pass
        
        try:
            add_app_bar(self.root, current_app='workflow_manager')
        except Exception:
            pass
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        """Create the main interface"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Print Package Workflow Manager", 
                font=('Arial', 16, 'bold'), 
                bg='#2c3e50', fg='white').pack(expand=True)
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel - Active Reviews
        left_panel = tk.Frame(main_frame, bg='#34495e', width=400)
        left_panel.pack(side='left', fill='y', padx=(0, 5))
        left_panel.pack_propagate(False)
        
        self.create_active_reviews_panel(left_panel)
        
        # Right panel - Workflow Details
        right_panel = tk.Frame(main_frame, bg='#34495e')
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.create_workflow_details_panel(right_panel)
    
    def create_active_reviews_panel(self, parent):
        """Create the active reviews panel"""
        # Header
        header_frame = tk.Frame(parent, bg='#2c3e50', height=50)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Active Print Package Reviews", 
                font=('Arial', 12, 'bold'), 
                bg='#2c3e50', fg='white').pack(expand=True)
        
        # Controls
        controls_frame = tk.Frame(parent, bg='#34495e')
        controls_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(controls_frame, text="🔄 Refresh", 
                 command=self.refresh_active_reviews,
                 font=('Arial', 10), bg='#3498db', fg='white',
                 relief='flat', padx=10, pady=5).pack(side='left', padx=5)
        
        # Filter by department
        tk.Label(controls_frame, text="Filter:", 
                font=('Arial', 10), bg='#34495e', fg='white').pack(side='left', padx=(10, 5))
        
        self.dept_filter_var = tk.StringVar()
        self.dept_filter_combo = ttk.Combobox(controls_frame, textvariable=self.dept_filter_var, 
                                             width=15, state='readonly')
        self.dept_filter_combo.pack(side='left', padx=5)
        self.dept_filter_combo.bind('<<ComboboxSelected>>', self.on_dept_filter_changed)
        
        # Active reviews list
        list_frame = tk.Frame(parent, bg='#34495e')
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview for active reviews
        columns = ("job_number", "customer", "stage", "department", "status")
        self.reviews_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        self.reviews_tree.heading("job_number", text="Job #")
        self.reviews_tree.heading("customer", text="Customer")
        self.reviews_tree.heading("stage", text="Stage")
        self.reviews_tree.heading("department", text="Department")
        self.reviews_tree.heading("status", text="Status")
        
        self.reviews_tree.column("job_number", width=80)
        self.reviews_tree.column("customer", width=150)
        self.reviews_tree.column("stage", width=100)
        self.reviews_tree.column("department", width=120)
        self.reviews_tree.column("status", width=80)
        
        self.reviews_tree.pack(fill='both', expand=True)
        bind_tree_column_persistence(self.reviews_tree, 'workflow_manager.reviews_tree', self.root)
        # Right-click: add note for job
        self.reviews_ctx = tk.Menu(list_frame, tearoff=0)
        self.reviews_ctx.add_command(label="Add New Note…", command=self.add_note_for_selected_job)
        self.reviews_tree.bind('<Button-3>', self._on_reviews_tree_right_click)
        
        # Bind selection
        self.reviews_tree.bind('<<TreeviewSelect>>', self.on_review_selected)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.reviews_tree.yview)
        self.reviews_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def create_workflow_details_panel(self, parent):
        """Create the workflow details panel"""
        # Header
        header_frame = tk.Frame(parent, bg='#2c3e50', height=50)
        header_frame.pack(fill='x', padx=5, pady=5)
        header_frame.pack_propagate(False)
        
        self.details_title = tk.Label(header_frame, text="Select a review to view details", 
                                     font=('Arial', 12, 'bold'), 
                                     bg='#2c3e50', fg='white')
        self.details_title.pack(expand=True)
        
        # Workflow stages
        stages_frame = tk.Frame(parent, bg='#34495e')
        stages_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create workflow visualization
        self.create_workflow_visualization(stages_frame)
        
        # Action buttons
        action_frame = tk.Frame(parent, bg='#34495e')
        action_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(action_frame, text="✅ Complete Stage", 
                 command=self.complete_current_stage,
                 font=('Arial', 10), bg='#27ae60', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=5)
        
        tk.Button(action_frame, text="➡️ Advance Workflow", 
                 command=self.advance_workflow,
                 font=('Arial', 10), bg='#e67e22', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=5)
        
        tk.Button(action_frame, text="📁 Open Folder", 
                 command=self.open_current_stage_folder,
                 font=('Arial', 10), bg='#3498db', fg='white',
                 relief='flat', padx=15, pady=5).pack(side='left', padx=5)
    
    def create_workflow_visualization(self, parent):
        """Create the workflow stages visualization"""
        # Create canvas for workflow visualization
        canvas_frame = tk.Frame(parent, bg='#34495e')
        canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Workflow stages will be displayed here
        self.workflow_canvas = tk.Canvas(canvas_frame, bg='white', height=400)
        self.workflow_canvas.pack(fill='both', expand=True)
        
        # Scrollbar for workflow canvas
        workflow_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.workflow_canvas.yview)
        self.workflow_canvas.configure(yscrollcommand=workflow_scrollbar.set)
        workflow_scrollbar.pack(side="right", fill="y")
        # Enable mouse wheel
        bind_mousewheel_to_canvas(self.workflow_canvas)
    
    def load_data(self):
        """Load initial data"""
        self.load_departments()
        self.refresh_active_reviews()
    
    def load_departments(self):
        """Load departments for filter"""
        try:
            departments = self.settings_manager.get_departments()
            dept_list = ['All'] + [dept[0] for dept in departments]
            self.dept_filter_combo['values'] = dept_list
            self.dept_filter_var.set('All')
        except Exception as e:
            print(f"Error loading departments: {e}")
    
    def refresh_active_reviews(self):
        """Refresh the active reviews list"""
        # Clear existing items
        for item in self.reviews_tree.get_children():
            self.reviews_tree.delete(item)
        
        try:
            # Get filter
            dept_filter = self.dept_filter_var.get()
            department = None if dept_filter == 'All' else dept_filter
            
            # Get pending reviews
            pending_reviews = self.workflow_engine.get_pending_reviews(department)
            
            for review in pending_reviews:
                self.reviews_tree.insert("", "end", values=(
                    review['job_number'],
                    review['customer_name'],
                    f"Stage {review['stage']}",
                    review['department'],
                    "In Progress"
                ))
            
            print(f"Loaded {len(pending_reviews)} active reviews")
            
        except Exception as e:
            print(f"Error refreshing active reviews: {e}")
    
    def on_dept_filter_changed(self, event):
        """Handle department filter change"""
        self.refresh_active_reviews()
    
    def on_review_selected(self, event):
        """Handle review selection"""
        selection = self.reviews_tree.selection()
        if not selection:
            return
        
        item = self.reviews_tree.item(selection[0])
        job_number = item['values'][0]
        
        self.load_workflow_details(job_number)

    def _on_reviews_tree_right_click(self, event):
        iid = self.reviews_tree.identify_row(event.y)
        if iid:
            self.reviews_tree.selection_set(iid)
            try:
                self.reviews_ctx.tk_popup(event.x_root, event.y_root)
            finally:
                self.reviews_ctx.grab_release()

    def add_note_for_selected_job(self):
        sel = self.reviews_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a job first.")
            return
        vals = self.reviews_tree.item(sel[0], 'values')
        job_number = vals[0]
        open_add_note_dialog(self.root, str(job_number))
    
    def load_workflow_details(self, job_number):
        """Load workflow details for selected job"""
        try:
            # Update title
            self.details_title.config(text=f"Workflow Details - Job {job_number}")
            
            # Get workflow summary
            summary = self.workflow_engine.get_workflow_summary(job_number)
            
            if not summary:
                self.clear_workflow_visualization()
                return
            
            # Store current job for actions
            self.current_job = job_number
            
            # Draw workflow visualization
            self.draw_workflow_visualization(summary)
            
        except Exception as e:
            print(f"Error loading workflow details: {e}")
    
    def draw_workflow_visualization(self, summary):
        """Draw the workflow stages visualization"""
        # Clear canvas
        self.workflow_canvas.delete("all")
        
        workflow_status = summary['workflow_status']
        current_stage = summary['review_info']['current_stage']
        
        # Draw stages
        stage_width = 150
        stage_height = 80
        spacing = 20
        start_x = 50
        start_y = 50
        
        for i, stage_info in enumerate(workflow_status):
            stage = stage_info['stage']
            status = stage_info['status']
            stage_name = stage_info['stage_name']
            reviewer = stage_info['reviewer'] or "Not Assigned"
            
            # Calculate position
            x = start_x + (i % 2) * (stage_width + spacing)
            y = start_y + (i // 2) * (stage_height + spacing)
            
            # Determine colors
            if status == 'completed':
                fill_color = '#27ae60'  # Green
                text_color = 'white'
            elif status == 'in_progress':
                fill_color = '#f39c12'  # Orange
                text_color = 'white'
            else:
                fill_color = '#bdc3c7'  # Gray
                text_color = 'black'
            
            # Draw stage rectangle
            self.workflow_canvas.create_rectangle(
                x, y, x + stage_width, y + stage_height,
                fill=fill_color, outline='black', width=2
            )
            
            # Draw stage number
            self.workflow_canvas.create_text(
                x + 10, y + 10, anchor='nw',
                text=f"Stage {stage}", font=('Arial', 10, 'bold'),
                fill=text_color
            )
            
            # Draw stage name
            self.workflow_canvas.create_text(
                x + 10, y + 30, anchor='nw',
                text=stage_name, font=('Arial', 8),
                fill=text_color, width=stage_width-20
            )
            
            # Draw reviewer
            self.workflow_canvas.create_text(
                x + 10, y + 60, anchor='nw',
                text=reviewer, font=('Arial', 8),
                fill=text_color
            )
            
            # Highlight current stage
            if stage == current_stage:
                self.workflow_canvas.create_rectangle(
                    x-2, y-2, x + stage_width+2, y + stage_height+2,
                    outline='#e74c3c', width=3
                )
        
        # Update scroll region
        self.workflow_canvas.configure(scrollregion=self.workflow_canvas.bbox("all"))
    
    def clear_workflow_visualization(self):
        """Clear the workflow visualization"""
        self.workflow_canvas.delete("all")
        self.details_title.config(text="Select a review to view details")
    
    def complete_current_stage(self):
        """Complete the current stage"""
        if not hasattr(self, 'current_job'):
            messagebox.showwarning("Warning", "Please select a review first")
            return
        
        # Get current user info
        current_user = self.settings_manager.current_user
        current_dept = self.settings_manager.current_department
        
        if not current_user:
            messagebox.showwarning("Warning", "Please set your user information in Settings first")
            return
        
        # Show completion dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Complete Stage")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Notes field
        tk.Label(dialog, text="Stage Completion Notes:", 
                font=('Arial', 10, 'bold')).pack(pady=10)
        
        notes_text = tk.Text(dialog, height=10, width=40)
        notes_text.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def complete_stage():
            notes = notes_text.get(1.0, tk.END).strip()
            
            # Get current stage
            summary = self.workflow_engine.get_workflow_summary(self.current_job)
            current_stage = summary['review_info']['current_stage']
            
            # Complete stage
            success = self.workflow_engine.complete_stage(
                self.current_job, current_stage, current_user, current_dept, notes
            )
            
            if success:
                messagebox.showinfo("Success", f"Stage {current_stage} completed successfully!")
                dialog.destroy()
                self.load_workflow_details(self.current_job)
            else:
                messagebox.showerror("Error", "Failed to complete stage")
        
        tk.Button(button_frame, text="Complete Stage", 
                 command=complete_stage, bg='#27ae60', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", 
                 command=dialog.destroy, bg='#95a5a6', fg='white').pack(side='left', padx=5)
    
    def advance_workflow(self):
        """Advance workflow to next stage"""
        if not hasattr(self, 'current_job'):
            messagebox.showwarning("Warning", "Please select a review first")
            return
        
        # Get current user info
        current_user = self.settings_manager.current_user
        current_dept = self.settings_manager.current_department
        
        if not current_user:
            messagebox.showwarning("Warning", "Please set your user information in Settings first")
            return
        
        # Get current stage
        summary = self.workflow_engine.get_workflow_summary(self.current_job)
        current_stage = summary['review_info']['current_stage']
        
        # Advance workflow
        success = self.workflow_engine.advance_to_next_stage(
            self.current_job, current_stage, current_user, current_dept
        )
        
        if success:
            messagebox.showinfo("Success", "Workflow advanced to next stage(s)!")
            self.load_workflow_details(self.current_job)
        else:
            messagebox.showerror("Error", "Failed to advance workflow")
    
    def open_current_stage_folder(self):
        """Open the current stage folder"""
        if not hasattr(self, 'current_job'):
            messagebox.showwarning("Warning", "Please select a review first")
            return
        
        try:
            # Get current stage files
            summary = self.workflow_engine.get_workflow_summary(self.current_job)
            current_stage = summary['review_info']['current_stage']
            
            files = self.workflow_engine.get_files_for_stage(self.current_job, current_stage)
            
            if files and files[0]['stage_path']:
                folder_path = os.path.dirname(files[0]['stage_path'])
                os.startfile(folder_path)
            else:
                messagebox.showinfo("Info", "No files found for current stage")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {str(e)}")

def main():
    """Main function to run workflow manager standalone"""
    app = WorkflowManagerApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()
