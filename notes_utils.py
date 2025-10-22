import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

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

def open_add_note_dialog(parent, job_number: str):
    """Open a modal to add a note for the given job number."""
    win = tk.Toplevel(parent)
    win.title(f"Add Note — Job {job_number}")
    win.transient(parent)
    win.grab_set()
    win.geometry("540x320")

    frame = ttk.Frame(win, padding=10)
    frame.pack(fill='both', expand=True)

    ttk.Label(frame, text=f"Job {job_number}", font=('Segoe UI', 10, 'bold')).pack(anchor='w')
    txt = tk.Text(frame, height=10, wrap='word')
    txt.pack(fill='both', expand=True, pady=(8,8))

    btns = ttk.Frame(frame)
    btns.pack(fill='x')

    def on_save():
        content = txt.get('1.0', tk.END).strip()
        if not content:
            messagebox.showwarning("Empty", "Please enter a note body before saving.", parent=win)
            return
        ok = append_job_note(job_number, content)
        if ok:
            messagebox.showinfo("Saved", "Note saved to job notes.", parent=win)
            win.destroy()
        else:
            messagebox.showerror("Error", "Failed to save note.", parent=win)

    ttk.Button(btns, text="Save", command=on_save).pack(side='right')
    ttk.Button(btns, text="Cancel", command=win.destroy).pack(side='right', padx=(0,6))

