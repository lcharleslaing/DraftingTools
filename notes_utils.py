import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime
import re

try:
    from db_utils import get_connection
except Exception:
    get_connection = None

def _conn():
    if get_connection:
        return get_connection('drafting_tools.db')
    return sqlite3.connect('drafting_tools.db')

def _ensure_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS job_notes (
            job_number TEXT PRIMARY KEY,
            notes TEXT
        )
        """
    )

def _ensure_projects_table(cur):
    # Minimal declaration; real schema is richer. IF NOT EXISTS prevents conflicts.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_number TEXT UNIQUE NOT NULL,
            job_directory TEXT
        )
        """
    )

def _is_valid_job_number(job: str) -> bool:
    if not job:
        return False
    s = str(job).strip()
    return bool(re.match(r"^\d{5}$", s) or re.match(r"^\d{5} \(\d+\)$", s))

def _ensure_project_exists(job_number: str, job_dir: str = None):
    conn = _conn(); cur = conn.cursor()
    _ensure_projects_table(cur)
    cur.execute("SELECT 1 FROM projects WHERE job_number = ?", (str(job_number),))
    exists = cur.fetchone() is not None
    if exists:
        # Optionally update directory if provided
        if job_dir:
            try:
                cur.execute("UPDATE projects SET job_directory = COALESCE(?, job_directory) WHERE job_number = ?", (job_dir, str(job_number)))
                conn.commit()
            except Exception:
                pass
        conn.close(); return True
    try:
        cur.execute("INSERT INTO projects (job_number, job_directory) VALUES (?, ?)", (str(job_number), job_dir))
        conn.commit(); conn.close(); return True
    except Exception:
        conn.close(); return False

def append_job_note(job_number: str, note_text: str) -> bool:
    """Append a note to the job's notes blob with timestamp and (optionally) current user."""
    if not note_text.strip():
        return False
    try:
        user = None
        dept = None
        try:
            from settings import SettingsManager
            sm = SettingsManager()
            user = sm.current_user
            dept = sm.current_department
        except Exception:
            pass

        conn = _conn()
        cur = conn.cursor()
        _ensure_table(cur)
        cur.execute("SELECT notes FROM job_notes WHERE job_number = ?", (str(job_number),))
        row = cur.fetchone()
        existing = row[0] if row and row[0] else ""

        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        header = f"=== {ts}"
        if user:
            if dept:
                header += f" by {user} ({dept})"
            else:
                header += f" by {user}"
        header += " ===\n"

        new_blob = f"{header}{note_text.strip()}\n\n" + (existing or "")
        cur.execute("INSERT OR REPLACE INTO job_notes (job_number, notes) VALUES (?, ?)", (str(job_number), new_blob))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def open_add_note_dialog(parent, job_number: str = None, on_saved=None):
    """Open a modal to add a note. If job_number is None, prompt to create a Documentation Only job on save.

    on_saved: optional callback(job_number_str) invoked after a successful save.
    """
    title_job = job_number if job_number else "No Job Selected"
    win = tk.Toplevel(parent)
    win.title(f"Add Note — {title_job}")
    win.transient(parent)
    win.grab_set()
    win.geometry("540x320")

    frame = ttk.Frame(win, padding=10)
    frame.pack(fill='both', expand=True)

    job_label_text = f"Job {job_number}" if job_number else "No job selected"
    ttk.Label(frame, text=job_label_text, font=('Segoe UI', 10, 'bold')).pack(anchor='w')
    txt = tk.Text(frame, height=10, wrap='word')
    txt.pack(fill='both', expand=True, pady=(8,8))

    btns = ttk.Frame(frame)
    btns.pack(fill='x')

    def on_save():
        content = txt.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("Empty", "Please enter a note body before saving.", parent=win)
            return
        target_job = job_number
        # If no job is provided, offer to create a Documentation Only job
        if not target_job:
            if not messagebox.askyesno(
                "No Job Selected",
                "No job is selected. Create a Documentation Only job to save this note?",
                parent=win,
            ):
                return
            # Ask for job number
            while True:
                jn = simpledialog.askstring("Job Number", "Enter 5-digit Job Number (or 12345 (1)):", parent=win)
                if jn is None:
                    return
                if _is_valid_job_number(jn):
                    target_job = jn.strip()
                    break
                messagebox.showwarning("Invalid", "Please enter a valid job number format.", parent=win)
            # Ask for job directory
            jd = filedialog.askdirectory(title="Select Job Folder", parent=win)
            if not jd:
                messagebox.showwarning("Required", "Job path is required to create the job.", parent=win)
                return
            if not _ensure_project_exists(target_job, jd):
                messagebox.showerror("Error", "Failed to create Documentation Only job.", parent=win)
                return
        ok = append_job_note(target_job, content)
        if ok:
            messagebox.showinfo("Saved", f"Note saved to job {target_job}.", parent=win)
            try:
                if callable(on_saved):
                    on_saved(str(target_job))
            finally:
                win.destroy()
        else:
            messagebox.showerror("Error", "Failed to save note.", parent=win)

    ttk.Button(btns, text="Save", command=on_save).pack(side='right')
    ttk.Button(btns, text="Cancel", command=win.destroy).pack(side='right', padx=(0,6))
