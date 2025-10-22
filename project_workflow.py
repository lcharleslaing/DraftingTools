#!/usr/bin/env python3
"""
Project Workflow App

Standalone app to manage the Standard (versioned) workflow template and
per‑project workflow state. This isolates the workflow logic from the Projects
UI and ensures project‑specific state is saved and viewed independently.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import os

from database_setup import DatabaseManager
from db_utils import get_connection
try:
    from app_nav import add_app_bar
except Exception:  # optional
    add_app_bar = None


class ProjectWorkflowApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Project Workflow")
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                pass
        self.root.minsize(1100, 700)

        # Initialize DB (ensure schema exists + migrations)
        self.dbm = DatabaseManager()
        self.conn = get_connection(self.dbm.db_path)

        if add_app_bar:
            try:
                add_app_bar(self.root, current_app='project_workflow')
            except Exception:
                pass

        self.current_job = None
        self.current_project_id = None
        self._build_ui()
        self._load_projects()

    # --------------------------- UI Layout ----------------------------
    def _build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(container)
        nb.pack(fill=tk.BOTH, expand=True)

        # Per‑project tab
        self.tab_project = ttk.Frame(nb)
        nb.add(self.tab_project, text="Projects")

        left = ttk.Frame(self.tab_project)
        right = ttk.Frame(self.tab_project)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left: projects list
        lf = ttk.LabelFrame(left, text="Projects", padding=6)
        lf.pack(fill=tk.BOTH, expand=True)
        sf = ttk.Frame(lf)
        sf.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(sf, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *_: self._filter_projects())
        ttk.Entry(sf, textvariable=self.search_var, width=18).pack(side=tk.LEFT, padx=(4, 0))
        self.projects_tree = ttk.Treeview(lf, columns=("Job", "Customer", "Due"), show='headings', height=18)
        for c in ("Job", "Customer", "Due"):
            self.projects_tree.heading(c, text=c)
        self.projects_tree.column("Job", width=90)
        self.projects_tree.column("Customer", width=160)
        self.projects_tree.column("Due", width=90)
        self.projects_tree.pack(fill=tk.BOTH, expand=True)
        self.projects_tree.bind('<<TreeviewSelect>>', self._on_project_select)

        # Right: project workflow
        toolbar = ttk.Frame(right)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="Apply Standard to Project", command=self._apply_template_to_current).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Sync Template Tasks", command=self._sync_template_tasks_to_current).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(toolbar, text="Recompute Due Dates", command=self._recompute_due_dates_for_current).pack(side=tk.LEFT, padx=(6, 0))
        self.current_lbl = ttk.Label(toolbar, text="No project selected", font=('Arial', 10, 'italic'))
        self.current_lbl.pack(side=tk.LEFT, padx=(12, 0))

        self.project_canvas = tk.Canvas(right, bg='white', highlightthickness=0)
        self.project_scroll = ttk.Scrollbar(right, orient='vertical', command=self.project_canvas.yview)
        self.project_canvas.configure(yscrollcommand=self.project_scroll.set)
        self.project_frame = ttk.Frame(self.project_canvas)
        self.project_canvas.create_window((0, 0), window=self.project_frame, anchor='nw')
        self.project_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.project_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.project_frame.bind('<Configure>', lambda e: self.project_canvas.configure(scrollregion=self.project_canvas.bbox('all')))

        # Template tab
        self.tab_template = ttk.Frame(nb)
        nb.add(self.tab_template, text="Standard Template")
        self._build_template_tab(self.tab_template)

    def _build_template_tab(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        ttk.Label(top, text="Standard Workflow (Active)", font=('Arial', 12, 'bold')).pack(anchor='w')

        # Split: left = steps, right = tasks for selected step
        pw = ttk.PanedWindow(top, orient=tk.HORIZONTAL)
        pw.pack(fill=tk.BOTH, expand=True, pady=(6, 6))
        left = ttk.Frame(pw)
        right = ttk.Frame(pw)
        pw.add(left, weight=3)
        pw.add(right, weight=2)

        # Steps tree
        cols = ("Order", "Department", "Group", "Title", "Duration (days)")
        self.template_tree = ttk.Treeview(left, columns=cols, show='headings', height=18)
        for c in cols:
            self.template_tree.heading(c, text=c)
        self.template_tree.column("Order", width=60, anchor='center')
        self.template_tree.pack(fill=tk.BOTH, expand=True)

        cbar = ttk.Frame(left)
        cbar.pack(fill=tk.X, pady=(6,0))
        ttk.Button(cbar, text="Add Before", command=lambda: self._tpl_add(before=True)).pack(side=tk.LEFT)
        ttk.Button(cbar, text="Add After", command=lambda: self._tpl_add(before=False)).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(cbar, text="Delete", command=self._tpl_delete).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(cbar, text="Up", command=lambda: self._tpl_move(-1)).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Button(cbar, text="Down", command=lambda: self._tpl_move(+1)).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(cbar, text="Save As New Version (Activate)", command=self._tpl_save_new_version).pack(side=tk.LEFT, padx=(12, 0))

        # Tasks panel
        self.tpl_task_header = ttk.Label(right, text="Tasks: (select a step)", font=('Arial', 10, 'bold'))
        self.tpl_task_header.pack(anchor='w')
        self.tpl_tasks_tree = ttk.Treeview(right, columns=("Order", "Title"), show='headings', height=14)
        self.tpl_tasks_tree.heading("Order", text="Order")
        self.tpl_tasks_tree.heading("Title", text="Title")
        self.tpl_tasks_tree.column("Order", width=60, anchor='center')
        self.tpl_tasks_tree.pack(fill=tk.BOTH, expand=True, pady=(6, 6))

        tbar = ttk.Frame(right)
        tbar.pack(fill=tk.X)
        ttk.Button(tbar, text="Add", command=lambda: self._tpl_tasks_add(self.tpl_tasks_tree)).pack(side=tk.LEFT)
        ttk.Button(tbar, text="Delete", command=lambda: self._tpl_tasks_delete(self.tpl_tasks_tree)).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(tbar, text="Up", command=lambda: self._tpl_tasks_move(self.tpl_tasks_tree, -1)).pack(side=tk.LEFT, padx=(12,0))
        ttk.Button(tbar, text="Down", command=lambda: self._tpl_tasks_move(self.tpl_tasks_tree, +1)).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(tbar, text="Apply Tasks", command=self._tpl_tasks_apply_current).pack(side=tk.LEFT, padx=(12,0))

        self._load_template_into_tree()
        self.template_tree.bind('<Double-1>', self._tpl_edit_cell)
        self.template_tree.bind('<<TreeviewSelect>>', self._tpl_on_select_update_tasks)

    # --------------------------- Projects -----------------------------
    def _load_projects(self):
        self.projects = []
        c = self.conn.cursor()
        c.execute(
            """
            SELECT job_number, COALESCE(customer_name, ''), COALESCE(due_date, '')
            FROM projects
            ORDER BY job_number
            """
        )
        self.projects = c.fetchall()
        self._render_projects()

    def _render_projects(self):
        for iid in self.projects_tree.get_children():
            self.projects_tree.delete(iid)
        term = (self.search_var.get() or '').lower()
        for job, cust, due in self.projects:
            if term and (term not in str(job).lower() and term not in cust.lower()):
                continue
            self.projects_tree.insert('', 'end', values=(job, cust, due))

    def _filter_projects(self):
        self._render_projects()

    def _on_project_select(self, _event=None):
        sel = self.projects_tree.selection()
        if not sel:
            return
        job = self.projects_tree.item(sel[0], 'values')[0]
        self.current_job = str(job)
        self.current_lbl.config(text=f"Current: {self.current_job}")
        # Lookup project id
        c = self.conn.cursor()
        c.execute("SELECT id FROM projects WHERE job_number = ?", (self.current_job,))
        r = c.fetchone()
        self.current_project_id = r[0] if r else None
        self._render_project_steps()

    # --------------------- Project Steps Rendering --------------------
    def _get_people_list(self):
        names = set()
        try:
            c = self.conn.cursor()
            c.execute("SELECT name FROM designers")
            for r in c.fetchall():
                if r and r[0]:
                    names.add(r[0])
            c.execute("SELECT name FROM engineers")
            for r in c.fetchall():
                if r and r[0]:
                    names.add(r[0])
        except Exception:
            pass
        names.add('Larry W.')
        return sorted(names)

    def _render_project_steps(self):
        # Clear previous
        for w in list(self.project_frame.children.values()):
            w.destroy()
        if not self.current_project_id:
            ttk.Label(self.project_frame, text="Select a project", foreground='gray').grid(row=0, column=0, sticky='w', padx=4, pady=6)
            return
        c = self.conn.cursor()
        try:
            c.execute(
                """
                SELECT id, order_index, department, COALESCE(group_name,''), title,
                       COALESCE(start_flag,0), COALESCE(start_ts,''),
                       COALESCE(completed_flag,0), COALESCE(completed_ts,''),
                       COALESCE(transfer_to_name,''), COALESCE(received_from_name,''),
                       COALESCE(planned_due_date,''), COALESCE(actual_duration_days, NULL)
                FROM project_workflow_steps
                WHERE project_id = ?
                ORDER BY order_index
                """,
                (self.current_project_id,),
            )
            steps = c.fetchall()
        except Exception as e:
            ttk.Label(self.project_frame, text=f"Error loading steps: {e}", foreground='red').grid(row=0, column=0, sticky='w')
            return

        if not steps:
            ttk.Label(self.project_frame, text="No steps. Click 'Apply Standard to Project' to seed steps.", foreground='gray').grid(row=0, column=0, sticky='w', padx=4, pady=6)
            return

        people = self._get_people_list()
        # Grid settings: 6 columns, unlimited rows, vertical scroll
        columns = getattr(self, 'project_columns', 6)
        for col_i in range(columns):
            self.project_frame.columnconfigure(col_i, weight=1, uniform='stepcol')

        for idx, (sid, order_i, dept, group, title, sflag, sts, cflag, cts, to_name, from_name, due, adur) in enumerate(steps):
            grid_row = idx // columns
            grid_col = idx % columns
            box = ttk.LabelFrame(self.project_frame, text=f"{order_i}. {dept}")
            box.grid(row=grid_row, column=grid_col, sticky='nsew', padx=6, pady=6)
            # Let each step card expand within its cell
            for ci in range(2):
                box.columnconfigure(ci, weight=1)

            ttk.Label(box, text=f"Group: {group}").grid(row=0, column=0, columnspan=2, sticky='w')
            ttk.Label(box, text=f"Title: {title}", font=('Arial', 10, 'bold')).grid(row=1, column=0, columnspan=2, sticky='w')

            # Start
            sv = tk.BooleanVar(value=bool(sflag))
            ttk.Label(box, text="Start:").grid(row=2, column=0, sticky='w')
            ttk.Checkbutton(box, variable=sv, command=lambda _sid=sid, _v=sv: self._on_step_start(_sid, _v)).grid(row=2, column=1, sticky='w')
            ttk.Label(box, text=f"Started At: {sts}").grid(row=3, column=0, columnspan=2, sticky='w')

            # Completed
            cv = tk.BooleanVar(value=bool(cflag))
            ttk.Label(box, text="Completed:").grid(row=4, column=0, sticky='w')
            ttk.Checkbutton(box, variable=cv, command=lambda _sid=sid, _v=cv: self._on_step_completed(_sid, _v)).grid(row=4, column=1, sticky='w')
            ttk.Label(box, text=f"Completed At: {cts}").grid(row=5, column=0, columnspan=2, sticky='w')

            # Transfer / Received
            to_var = tk.StringVar(value=to_name)
            ttk.Label(box, text="Transfer To:").grid(row=6, column=0, sticky='w')
            to_cb = ttk.Combobox(box, textvariable=to_var, values=people, width=18, state='readonly')
            to_cb.grid(row=6, column=1, sticky='w')
            to_cb.bind('<<ComboboxSelected>>', lambda _e, _sid=sid, _v=to_var: self._on_step_transfer(_sid, _v))

            from_var = tk.StringVar(value=from_name)
            ttk.Label(box, text="Received From:").grid(row=7, column=0, sticky='w')
            from_cb = ttk.Combobox(box, textvariable=from_var, values=people, width=18, state='readonly')
            from_cb.grid(row=7, column=1, sticky='w')
            from_cb.bind('<<ComboboxSelected>>', lambda _e, _sid=sid, _v=from_var: self._on_step_received(_sid, _v))

            ttk.Label(box, text=f"Due: {due}").grid(row=8, column=0, columnspan=2, sticky='w')
            ttk.Label(box, text=f"Duration (days): {adur if adur is not None else ''}").grid(row=9, column=0, columnspan=2, sticky='w')

            # Tasks (per-project checklist for this step)
            tasks = self._load_step_tasks(sid)
            r = 10
            if tasks:
                ttk.Label(box, text="Tasks:").grid(row=r, column=0, sticky='w'); r += 1
            for tid, ttitle, is_checked in tasks:
                tv = tk.BooleanVar(value=bool(is_checked))
                ttk.Checkbutton(box, text=ttitle, variable=tv, command=lambda _tid=tid, _v=tv: self._on_task_toggle(_tid, _v)).grid(row=r, column=0, columnspan=2, sticky='w')
                r += 1
            # Add Task button
            ttk.Button(box, text="Add Task", command=lambda _sid=sid: self._on_add_task(_sid)).grid(row=r, column=0, sticky='w', pady=(4,0))


    # -------------------------- Step Updates --------------------------
    def _on_step_start(self, step_id, var):
        try:
            c = self.conn.cursor()
            # Verify belongs to current project
            c.execute("SELECT project_id FROM project_workflow_steps WHERE id = ?", (step_id,))
            row = c.fetchone()
            if not row or row[0] != self.current_project_id:
                print(f"DEBUG[_on_step_start]: step {step_id} not in current project")
                return
            if var.get():
                c.execute(
                    "UPDATE project_workflow_steps SET start_flag = 1, start_ts = COALESCE(start_ts, ?) WHERE id = ? AND project_id = ?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), step_id, self.current_project_id),
                )
            else:
                c.execute("UPDATE project_workflow_steps SET start_flag = 0 WHERE id = ? AND project_id = ?", (step_id, self.current_project_id))
            self.conn.commit()
            print(f"DEBUG[_on_step_start]: updated step_id={step_id} proj_id={self.current_project_id} value={int(var.get())}")
        except Exception as e:
            print(f"ERROR[_on_step_start]: {e}")
        self._recompute_due_dates_for_current()
        self._render_project_steps()

    def _on_step_completed(self, step_id, var):
        try:
            c = self.conn.cursor()
            c.execute("SELECT project_id, start_ts FROM project_workflow_steps WHERE id = ?", (step_id,))
            row = c.fetchone()
            if not row or row[0] != self.current_project_id:
                print(f"DEBUG[_on_step_completed]: step {step_id} not in current project")
                return
            start_ts = row[1]
            if var.get():
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                actual_dur = None
                try:
                    if start_ts:
                        sdt = datetime.strptime(start_ts, "%Y-%m-%d %H:%M:%S")
                        actual_dur = (datetime.now() - sdt).days
                except Exception:
                    actual_dur = None
                c.execute(
                    """
                    UPDATE project_workflow_steps
                    SET completed_flag = 1,
                        completed_ts = COALESCE(completed_ts, ?),
                        actual_completed_date = COALESCE(actual_completed_date, DATE(?)),
                        actual_duration_days = COALESCE(actual_duration_days, ?)
                    WHERE id = ? AND project_id = ?
                    """,
                    (now, now, actual_dur, step_id, self.current_project_id),
                )
            else:
                c.execute("UPDATE project_workflow_steps SET completed_flag = 0 WHERE id = ? AND project_id = ?", (step_id, self.current_project_id))
            self.conn.commit()
            print(f"DEBUG[_on_step_completed]: updated step_id={step_id} proj_id={self.current_project_id} value={int(var.get())}")
        except Exception as e:
            print(f"ERROR[_on_step_completed]: {e}")
        self._render_project_steps()

    def _on_step_transfer(self, step_id, var):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE project_workflow_steps SET transfer_to_name = ?, transfer_to_ts = COALESCE(transfer_to_ts, ?) WHERE id = ? AND project_id = ?",
                      (var.get(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), step_id, self.current_project_id))
            self.conn.commit()
            print(f"DEBUG[_on_step_transfer]: step_id={step_id} proj_id={self.current_project_id} name='{var.get()}'")
        except Exception as e:
            print(f"ERROR[_on_step_transfer]: {e}")
        self._render_project_steps()

    def _on_step_received(self, step_id, var):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE project_workflow_steps SET received_from_name = ?, received_from_ts = COALESCE(received_from_ts, ?) WHERE id = ? AND project_id = ?",
                      (var.get(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), step_id, self.current_project_id))
            self.conn.commit()
            print(f"DEBUG[_on_step_received]: step_id={step_id} proj_id={self.current_project_id} name='{var.get()}'")
        except Exception as e:
            print(f"ERROR[_on_step_received]: {e}")
        self._render_project_steps()

    # --------------------------- Step Tasks ---------------------------
    def _load_step_tasks(self, project_step_id):
        c = self.conn.cursor()
        c.execute(
            "SELECT id, title, COALESCE(is_checked,0) FROM project_step_tasks WHERE project_step_id = ? ORDER BY order_index",
            (project_step_id,),
        )
        return c.fetchall()

    def _on_task_toggle(self, task_id, var):
        try:
            c = self.conn.cursor()
            if var.get():
                c.execute(
                    "UPDATE project_step_tasks SET is_checked = 1, checked_ts = COALESCE(checked_ts, ?) WHERE id = ?",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id),
                )
            else:
                c.execute("UPDATE project_step_tasks SET is_checked = 0 WHERE id = ?", (task_id,))
            self.conn.commit()
            print(f"DEBUG[_on_task_toggle]: task_id={task_id} value={int(var.get())}")
        except Exception as e:
            print(f"ERROR[_on_task_toggle]: {e}")

    def _on_add_task(self, project_step_id):
        try:
            from tkinter import simpledialog
            title = simpledialog.askstring("Add Task", "Task title:", parent=self.root)
            if not title:
                return
            c = self.conn.cursor()
            c.execute("SELECT COALESCE(MAX(order_index),0) + 1 FROM project_step_tasks WHERE project_step_id = ?", (project_step_id,))
            next_ord = c.fetchone()[0] or 1
            c.execute(
                "INSERT INTO project_step_tasks (project_step_id, order_index, title, is_checked) VALUES (?, ?, ?, 0)",
                (project_step_id, next_ord, title),
            )
            self.conn.commit()
            print(f"DEBUG[_on_add_task]: step_id={project_step_id} title='{title}' order={next_ord}")
        except Exception as e:
            print(f"ERROR[_on_add_task]: {e}")
        self._render_project_steps()

    # ---------------------- Due Date Recalculation --------------------
    def _recompute_due_dates_for_current(self):
        if not self.current_project_id:
            return
        try:
            c = self.conn.cursor()
            c.execute("SELECT due_date FROM projects WHERE id = ?", (self.current_project_id,))
            row = c.fetchone(); proj_due = row[0] if row else None
            if not proj_due:
                return
            c.execute(
                """
                SELECT id, order_index, start_ts,
                       (SELECT planned_duration_days FROM workflow_template_steps w WHERE w.id = pws.template_step_id)
                FROM project_workflow_steps pws
                WHERE project_id = ?
                ORDER BY order_index
                """,
                (self.current_project_id,),
            )
            steps = c.fetchall()
            if not steps:
                return

            def subtract_business_days(date_obj, days):
                d = date_obj
                remaining = int(days or 0)
                while remaining > 0:
                    d = d - timedelta(days=1)
                    if d.weekday() < 5:
                        remaining -= 1
                return d

            next_start = datetime.strptime(proj_due, "%Y-%m-%d").date()
            updates = []
            for sid, order_i, start_ts, dur in reversed(steps):
                planned_due = next_start
                planned_start = subtract_business_days(planned_due, dur or 0)
                if start_ts:
                    try:
                        next_start = datetime.strptime(start_ts, "%Y-%m-%d %H:%M:%S").date()
                    except Exception:
                        next_start = planned_start
                else:
                    next_start = planned_start
                updates.append((planned_due.strftime("%Y-%m-%d"), sid))
            for due, sid in updates:
                c.execute("UPDATE project_workflow_steps SET planned_due_date = ? WHERE id = ? AND project_id = ?", (due, sid, self.current_project_id))
            self.conn.commit()
        except Exception as e:
            print(f"ERROR[_recompute_due_dates_for_current]: {e}")

    # ------------------------- Template Logic ------------------------
    def _active_template(self):
        c = self.conn.cursor()
        c.execute("SELECT id, version FROM workflow_templates WHERE name = 'Standard' AND is_active = 1 ORDER BY version DESC LIMIT 1")
        return c.fetchone()

    def _load_template_into_tree(self):
        for iid in self.template_tree.get_children():
            self.template_tree.delete(iid)
        t = self._active_template()
        if not t:
            return
        tid = t[0]
        c = self.conn.cursor()
        c.execute("SELECT order_index, department, COALESCE(group_name,''), title, COALESCE(planned_duration_days,1) FROM workflow_template_steps WHERE template_id = ? ORDER BY order_index", (tid,))
        rows = c.fetchall()
        for i, (order_i, dept, group, title, dur) in enumerate(rows, start=1):
            self.template_tree.insert('', 'end', values=(order_i, dept, group, title, dur))

    def _tpl_add(self, before=True):
        sel = self.template_tree.selection()
        insert_at = 0
        if sel:
            idx = self.template_tree.index(sel[0])
            insert_at = idx if before else idx + 1
        self.template_tree.insert('', insert_at, values=(insert_at + 1, 'Drafting', '', 'New Step', 1))
        # Renumber
        for i, iid in enumerate(self.template_tree.get_children(), start=1):
            v = list(self.template_tree.item(iid, 'values')); v[0] = i; self.template_tree.item(iid, values=v)

    def _tpl_delete(self):
        sel = self.template_tree.selection()
        if not sel:
            return
        self.template_tree.delete(sel[0])
        for i, iid in enumerate(self.template_tree.get_children(), start=1):
            v = list(self.template_tree.item(iid, 'values')); v[0] = i; self.template_tree.item(iid, values=v)

    def _tpl_move(self, delta):
        sel = self.template_tree.selection()
        if not sel:
            return
        iid = sel[0]
        idx = self.template_tree.index(iid)
        new_idx = idx + delta
        kids = self.template_tree.get_children()
        if new_idx < 0 or new_idx >= len(kids):
            return
        self.template_tree.move(iid, '', new_idx)
        for i, ci in enumerate(self.template_tree.get_children(), start=1):
            v = list(self.template_tree.item(ci, 'values')); v[0] = i; self.template_tree.item(ci, values=v)

    def _tpl_edit_cell(self, event):
        item = self.template_tree.identify_row(event.y)
        col = self.template_tree.identify_column(event.x)
        if not item or col not in ('#2', '#3', '#4', '#5'):
            return
        x, y, w, h = self.template_tree.bbox(item, col)
        value = self.template_tree.set(item, col)
        entry = ttk.Entry(self.template_tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, value)
        entry.focus_set()
        def commit(_evt=None):
            new_val = entry.get(); entry.destroy(); self.template_tree.set(item, col, new_val)
        entry.bind('<Return>', commit)
        entry.bind('<FocusOut>', lambda _e: entry.destroy())

    def _tpl_save_new_version(self):
        try:
            c = self.conn.cursor()
            # Capture old active template id to copy tasks
            active = self._active_template()
            old_tid = active[0] if active else None
            c.execute("SELECT COALESCE(MAX(version),0) FROM workflow_templates WHERE name = 'Standard'")
            next_ver = (c.fetchone()[0] or 0) + 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO workflow_templates (name, version, is_active, created_date) VALUES ('Standard', ?, 1, ?)", (next_ver, now))
            new_tid = c.lastrowid
            c.execute("UPDATE workflow_templates SET is_active = 0 WHERE name = 'Standard' AND id != ?", (new_tid,))
            # Insert steps for new template
            for i, iid in enumerate(self.template_tree.get_children(), start=1):
                v = self.template_tree.item(iid, 'values')
                order_i = int(v[0]); dept = str(v[1]); group = str(v[2]); title = str(v[3]); dur = int(v[4]) if str(v[4]).isdigit() else 1
                c.execute(
                    """
                    INSERT INTO workflow_template_steps (template_id, order_index, department, group_name, title, planned_duration_days)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (new_tid, order_i, dept, group, title, dur),
                )
            # Copy tasks by matching order_index between old and new templates
            if old_tid:
                # Build map: order_index -> new step id
                c.execute("SELECT id, order_index FROM workflow_template_steps WHERE template_id = ?", (new_tid,))
                new_map = {oi: sid for sid, oi in c.fetchall()}
                c.execute("SELECT id, order_index FROM workflow_template_steps WHERE template_id = ?", (old_tid,))
                old_map = {oi: sid for sid, oi in c.fetchall()}
                for oi, old_sid in old_map.items():
                    new_sid = new_map.get(oi)
                    if not new_sid:
                        continue
                    c.execute("SELECT order_index, title, COALESCE(default_checked,0) FROM workflow_step_tasks WHERE template_step_id = ? ORDER BY order_index", (old_sid,))
                    for tord, ttitle, dflt in c.fetchall():
                        c.execute(
                            "INSERT INTO workflow_step_tasks (template_step_id, order_index, title, default_checked) VALUES (?, ?, ?, ?)",
                            (new_sid, tord, ttitle, dflt),
                        )
            self.conn.commit()
            messagebox.showinfo("Saved", f"Activated Standard v{next_ver}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {e}")
        self._load_template_into_tree()

    # --- inline tasks editor helpers ---
    def _tpl_on_select_update_tasks(self, _event=None):
        self._load_tasks_for_selected_step()

    def _tpl_current_template_step_id(self):
        sel = self.template_tree.selection()
        if not sel:
            return None
        try:
            order_i = int(self.template_tree.item(sel[0], 'values')[0])
        except Exception:
            return None
        t = self._active_template()
        if not t:
            return None
        tid = t[0]
        c = self.conn.cursor()
        c.execute("SELECT id, title FROM workflow_template_steps WHERE template_id = ? AND order_index = ?", (tid, order_i))
        row = c.fetchone()
        return row[0] if row else None

    def _load_tasks_for_selected_step(self):
        # Clear
        for iid in self.tpl_tasks_tree.get_children():
            self.tpl_tasks_tree.delete(iid)
        step_id = self._tpl_current_template_step_id()
        if not step_id:
            self.tpl_task_header.config(text="Tasks: (select a step)")
            return
        # Update header
        self.tpl_task_header.config(text=f"Tasks for Step ID {step_id}")
        c = self.conn.cursor()
        c.execute("SELECT order_index, title FROM workflow_step_tasks WHERE template_step_id = ? ORDER BY order_index", (step_id,))
        for order_i, title in c.fetchall():
            self.tpl_tasks_tree.insert('', 'end', values=(order_i, title))

    def _tpl_tasks_apply_current(self):
        step_id = self._tpl_current_template_step_id()
        if not step_id:
            messagebox.showinfo("Select Step", "Select a template step to apply tasks.")
            return
        try:
            c = self.conn.cursor()
            c.execute("DELETE FROM workflow_step_tasks WHERE template_step_id = ?", (step_id,))
            for i, iid in enumerate(self.tpl_tasks_tree.get_children(), start=1):
                _ord, title = self.tpl_tasks_tree.item(iid, 'values')
                c.execute(
                    "INSERT INTO workflow_step_tasks (template_step_id, order_index, title, default_checked) VALUES (?, ?, ?, 0)",
                    (step_id, int(i), str(title)),
                )
            self.conn.commit()
            print(f"DEBUG[_tpl_tasks_apply_current]: step_id={step_id} tasks={len(self.tpl_tasks_tree.get_children())}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply tasks: {e}")

    # ------------------ Apply Template to Project ---------------------
    def _apply_template_to_current(self):
        if not self.current_project_id:
            messagebox.showwarning("No Project", "Select a project first.")
            return
        t = self._active_template()
        if not t:
            messagebox.showwarning("No Template", "Define and activate a Standard workflow first.")
            return
        tid, ver = t
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM project_workflow_steps WHERE project_id = ?", (self.current_project_id,))
        count = c.fetchone()[0]
        if count > 0:
            if not messagebox.askyesno("Replace?", f"Project already has {count} step(s). Replace with Standard v{ver}?"):
                return
            c.execute("DELETE FROM project_workflow_steps WHERE project_id = ?", (self.current_project_id,))
        # Insert steps and capture mapping: template_step_id -> project_step_id
        c.execute("SELECT id, order_index, department, COALESCE(group_name,''), title FROM workflow_template_steps WHERE template_id = ? ORDER BY order_index", (tid,))
        tsteps = c.fetchall()
        for sid, order_i, dept, group, title in tsteps:
            c.execute(
                """
                INSERT INTO project_workflow_steps
                (project_id, template_id, template_step_id, order_index, department, group_name, title)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.current_project_id, tid, sid, order_i, dept, group, title),
            )
        self.conn.commit()

        # Map newly inserted project steps by template_step_id
        c.execute("SELECT id, template_step_id FROM project_workflow_steps WHERE project_id = ?", (self.current_project_id,))
        map_rows = c.fetchall()
        sid_to_pws = {tpl_id: pws_id for pws_id, tpl_id in map_rows}

        # Copy template tasks into project_step_tasks
        for sid, order_i, dept, group, title in tsteps:
            c.execute("SELECT id, order_index, title, COALESCE(default_checked,0) FROM workflow_step_tasks WHERE template_step_id = ? ORDER BY order_index", (sid,))
            t_tasks = c.fetchall()
            pws_id = sid_to_pws.get(sid)
            if not pws_id:
                continue
            for ttask_id, torder, ttitle, dflt in t_tasks:
                c.execute(
                    """
                    INSERT INTO project_step_tasks (project_step_id, template_task_id, order_index, title, is_checked)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (pws_id, ttask_id, torder, ttitle, int(dflt)),
                )
        self.conn.commit()
        self._recompute_due_dates_for_current()
        self._render_project_steps()

    # ---------------------- Template Tasks Editor ---------------------
    def _tpl_open_tasks_editor(self):
        sel = self.template_tree.selection()
        if not sel:
            messagebox.showinfo("Select Step", "Select a template step to edit its tasks.")
            return
        # Resolve selected step order and fetch its row
        order_i = int(self.template_tree.item(sel[0], 'values')[0])
        t = self._active_template()
        if not t:
            return
        tid = t[0]
        c = self.conn.cursor()
        c.execute("SELECT id FROM workflow_template_steps WHERE template_id = ? AND order_index = ?", (tid, order_i))
        row = c.fetchone()
        if not row:
            return
        template_step_id = row[0]

        win = tk.Toplevel(self.root)
        win.title("Edit Step Tasks")
        win.geometry("500x400")
        frame = ttk.Frame(win, padding=8)
        frame.pack(fill=tk.BOTH, expand=True)
        cols = ("Order", "Title")
        tree = ttk.Treeview(frame, columns=cols, show='headings', height=14)
        for ccol in cols:
            tree.heading(ccol, text=ccol)
        tree.column("Order", width=60, anchor='center')
        tree.pack(fill=tk.BOTH, expand=True)

        # Load existing tasks
        c.execute("SELECT order_index, title FROM workflow_step_tasks WHERE template_step_id = ? ORDER BY order_index", (template_step_id,))
        for order_j, ttitle in c.fetchall():
            tree.insert('', 'end', values=(order_j, ttitle))

        ctr = ttk.Frame(frame)
        ctr.pack(fill=tk.X, pady=(6,0))
        ttk.Button(ctr, text="Add", command=lambda: self._tpl_tasks_add(tree)).pack(side=tk.LEFT)
        ttk.Button(ctr, text="Delete", command=lambda: self._tpl_tasks_delete(tree)).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(ctr, text="Up", command=lambda: self._tpl_tasks_move(tree, -1)).pack(side=tk.LEFT, padx=(12,0))
        ttk.Button(ctr, text="Down", command=lambda: self._tpl_tasks_move(tree, +1)).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(ctr, text="Apply", command=lambda: self._tpl_tasks_apply(tree, template_step_id)).pack(side=tk.RIGHT)
        ttk.Button(ctr, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=(6,0))

        tree.bind('<Double-1>', lambda e: self._tpl_tasks_edit_cell(tree, e))

    def _tpl_tasks_add(self, tree):
        from tkinter import simpledialog
        title = simpledialog.askstring("New Task", "Task title:", parent=self.root)
        if not title:
            return
        tree.insert('', 'end', values=(len(tree.get_children())+1, title))

    def _tpl_tasks_delete(self, tree):
        sel = tree.selection()
        if not sel:
            return
        tree.delete(sel[0])
        for i, iid in enumerate(tree.get_children(), start=1):
            v = list(tree.item(iid, 'values')); v[0] = i; tree.item(iid, values=v)

    def _tpl_tasks_move(self, tree, delta):
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        idx = tree.index(iid)
        kids = tree.get_children()
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(kids):
            return
        tree.move(iid, '', new_idx)
        for i, ci in enumerate(tree.get_children(), start=1):
            v = list(tree.item(ci, 'values')); v[0] = i; tree.item(ci, values=v)

    def _tpl_tasks_edit_cell(self, tree, event):
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not item or col != '#2':
            return
        x, y, w, h = tree.bbox(item, col)
        value = tree.set(item, col)
        entry = ttk.Entry(tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, value)
        entry.focus_set()
        def commit(_e=None):
            nv = entry.get(); entry.destroy(); tree.set(item, col, nv)
        entry.bind('<Return>', commit)
        entry.bind('<FocusOut>', lambda _e: entry.destroy())

    def _tpl_tasks_apply(self, tree, template_step_id):
        try:
            c = self.conn.cursor()
            # Replace tasks for this template step with current tree content
            c.execute("DELETE FROM workflow_step_tasks WHERE template_step_id = ?", (template_step_id,))
            for i, iid in enumerate(tree.get_children(), start=1):
                _order_i, title = tree.item(iid, 'values')
                c.execute(
                    "INSERT INTO workflow_step_tasks (template_step_id, order_index, title, default_checked) VALUES (?, ?, ?, 0)",
                    (template_step_id, int(i), str(title)),
                )
            self.conn.commit()
            print(f"DEBUG[_tpl_tasks_apply]: template_step_id={template_step_id} tasks={len(tree.get_children())}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tasks: {e}")

    def _sync_template_tasks_to_current(self):
        """For the current project, add any missing tasks from the Standard template without removing existing project tasks."""
        if not self.current_project_id:
            messagebox.showinfo("Select Project", "Select a project first.")
            return
        t = self._active_template()
        if not t:
            messagebox.showinfo("No Template", "No active Standard template found.")
            return
        tid, _ = t
        try:
            c = self.conn.cursor()
            # Map project_step_id -> template_step_id
            c.execute("SELECT id, template_step_id FROM project_workflow_steps WHERE project_id = ?", (self.current_project_id,))
            pmap = c.fetchall()
            for pws_id, tpl_sid in pmap:
                if not tpl_sid:
                    continue
                # For each template task, ensure a project task exists
                c.execute("SELECT id, order_index, title, COALESCE(default_checked,0) FROM workflow_step_tasks WHERE template_step_id = ? ORDER BY order_index", (tpl_sid,))
                t_tasks = c.fetchall()
                for ttask_id, order_i, title, dflt in t_tasks:
                    c.execute("SELECT COUNT(*) FROM project_step_tasks WHERE project_step_id = ? AND template_task_id = ?", (pws_id, ttask_id))
                    exists = c.fetchone()[0]
                    if not exists:
                        c.execute(
                            "INSERT INTO project_step_tasks (project_step_id, template_task_id, order_index, title, is_checked) VALUES (?, ?, ?, ?, ?)",
                            (pws_id, ttask_id, order_i, title, int(dflt)),
                        )
            self.conn.commit()
            self._render_project_steps()
            messagebox.showinfo("Synced", "Template tasks synced to current project (missing tasks added).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sync tasks: {e}")


def main():
    app = ProjectWorkflowApp()
    app.root.mainloop()


if __name__ == '__main__':
    main()
