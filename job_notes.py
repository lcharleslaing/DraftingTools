import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import sys

from database_setup import DatabaseManager
from nav_utils import open_or_focus
from app_nav import add_app_bar
from notes_utils import append_job_note, open_add_note_dialog


class JobNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Notes - Drafting Tools")
        try:
            self.root.state('zoomed')
        except Exception:
            pass
        self.root.minsize(1000, 700)

        try:
            add_app_bar(self.root, current_app='job_notes')
        except Exception:
            pass

        self.db = DatabaseManager()
        self.current_job = None

        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(0, weight=1)

        # Left: Jobs list
        left = ttk.Frame(container, padding=8)
        left.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Jobs", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        cols = ("Job Number", "Customer", "Due Date")
        self.tree = ttk.Treeview(left, columns=cols, show='headings', height=24)
        for c, w in [("Job Number", 110), ("Customer", 200), ("Due Date", 100)]:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, minwidth=80)
        ysb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ysb.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.tree.bind('<<TreeviewSelect>>', self.on_job_select)

        # Right: Notes editor
        right = ttk.Frame(container, padding=8)
        right.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)
        ttk.Label(right, text="Notes", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        self.txt = tk.Text(right, wrap='word', font=('Arial', 10))
        y2 = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.txt.yview)
        self.txt.configure(yscrollcommand=y2.set)
        self.txt.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        y2.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # Actions
        actions = ttk.Frame(right)
        actions.grid(row=2, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Button(actions, text="Save Notes", command=self.save_notes).pack(side=tk.LEFT)
        ttk.Button(actions, text="New Note…", command=self.append_note_dialog).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Delete Notes", command=self.delete_notes).pack(side=tk.LEFT, padx=(8, 0))

        self.load_jobs()

    def _conn(self):
        return sqlite3.connect(self.db.db_path)

    def load_jobs(self):
        try:
            conn = self._conn(); cur = conn.cursor()
            cur.execute(
                """
                SELECT job_number, COALESCE(customer_name, ''), COALESCE(due_date, '')
                FROM projects
                ORDER BY job_number DESC
                """
            )
            rows = cur.fetchall(); conn.close()
            for i in self.tree.get_children():
                self.tree.delete(i)
            for job, cust, due in rows:
                self.tree.insert('', 'end', values=(job, cust, due))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load jobs: {e}")

    def on_job_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], 'values')
        if not vals:
            return
        job = str(vals[0])
        self.current_job = job
        self.load_notes(job)

    def load_notes(self, job_number: str):
        try:
            conn = self._conn(); cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS job_notes (
                    job_number TEXT PRIMARY KEY,
                    notes TEXT
                )
                """
            )
            cur.execute("SELECT notes FROM job_notes WHERE job_number = ?", (str(job_number),))
            row = cur.fetchone(); conn.close()
            blob = row[0] if row and row[0] else ""
            self.txt.delete('1.0', tk.END)
            self.txt.insert('1.0', blob)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load notes: {e}")

    def save_notes(self):
        if not self.current_job:
            messagebox.showwarning("No Job", "Please select a job first.")
            return
        try:
            content = self.txt.get('1.0', tk.END).strip()
            conn = self._conn(); cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS job_notes (
                    job_number TEXT PRIMARY KEY,
                    notes TEXT
                )
                """
            )
            cur.execute(
                "INSERT OR REPLACE INTO job_notes (job_number, notes) VALUES (?, ?)",
                (str(self.current_job), content)
            )
            conn.commit(); conn.close()
            messagebox.showinfo("Saved", "Notes saved.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def append_note_dialog(self):
        def _after_save(saved_job):
            try:
                self.load_jobs()
                # Focus/select saved job and load its notes
                self.current_job = saved_job
                for iid in self.tree.get_children():
                    vals = self.tree.item(iid, 'values')
                    if vals and str(vals[0]) == str(saved_job):
                        self.tree.selection_set(iid)
                        self.tree.focus(iid)
                        self.tree.see(iid)
                        break
                self.load_notes(saved_job)
            except Exception:
                pass
        try:
            open_add_note_dialog(self.root, self.current_job, on_saved=_after_save)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open dialog: {e}")

    def delete_notes(self):
        if not self.current_job:
            messagebox.showwarning("No Job", "Please select a job first.")
            return
        if not messagebox.askyesno("Delete Notes", f"Delete all notes for job {self.current_job}?"):
            return
        try:
            conn = self._conn(); cur = conn.cursor()
            cur.execute("DELETE FROM job_notes WHERE job_number = ?", (str(self.current_job),))
            conn.commit(); conn.close()
            self.txt.delete('1.0', tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Job Notes Application')
    parser.add_argument('--job', type=str, help='Job number to preload')
    args = parser.parse_args()

    root = tk.Tk()
    app = JobNotesApp(root)
    if args.job:
        # Preselect the job in the list
        try:
            for iid in app.tree.get_children():
                vals = app.tree.item(iid, 'values')
                if vals and str(vals[0]) == str(args.job):
                    app.tree.selection_set(iid)
                    app.tree.focus(iid)
                    app.tree.see(iid)
                    app.on_job_select()
                    break
        except Exception:
            pass
    root.mainloop()


if __name__ == '__main__':
    main()
