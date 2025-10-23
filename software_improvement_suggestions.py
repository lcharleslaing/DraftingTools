#!/usr/bin/env python3
"""
Software Improvement Suggestions App

Fullscreen Tkinter app with full CRUD for improvement suggestions.
Fields: app name, description (with clipboard screenshot paste), suggested by
(current Settings user), timestamps, action taken, approval states, and closure.
Filters (Open/Completed/Closed) and newest-first sorting by created date.
"""

import os
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import ImageGrab, Image, ImageTk
except Exception:
    ImageGrab = None
    Image = None
    ImageTk = None

from database_setup import DatabaseManager
from settings import SettingsManager

SCREENSHOT_DIR = os.path.join('updates', 'screenshots')


class SuggestionsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Software Improvement Suggestions')
        # Fullscreen/maximized like other apps
        try:
            self.root.state('zoomed')
        except Exception:
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                pass
        self.root.minsize(1100, 700)

        # Ensure DB and dirs
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.dbm = DatabaseManager()
        self.db_path = self.dbm.db_path
        self.sm = SettingsManager(self.db_path)

        self.current_id = None
        self.preview_image = None

        self._build_ui()
        self._load_rows()

    # UI
    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.BOTH, expand=True)

        # Toolbar with filter
        toolbar = ttk.Frame(top)
        toolbar.pack(fill=tk.X)
        ttk.Label(toolbar, text='Filter:').pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value='Open')
        for name in ('Open', 'Completed', 'Closed'):
            ttk.Radiobutton(toolbar, text=name, value=name, variable=self.filter_var, command=self._load_rows).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(toolbar, text='New', command=self._new).pack(side=tk.LEFT, padx=(12,0))
        ttk.Button(toolbar, text='Save', command=self._save).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(toolbar, text='Delete', command=self._delete).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(toolbar, text='Paste Screenshot', command=self._paste_screenshot).pack(side=tk.LEFT, padx=(12,0))

        pw = ttk.PanedWindow(top, orient=tk.HORIZONTAL)
        pw.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(pw)
        right = ttk.Frame(pw)
        pw.add(left, weight=2)
        pw.add(right, weight=3)

        # Left: list
        cols = ('id', 'created', 'app', 'status')
        self.tree = ttk.Treeview(left, columns=cols, show='headings', height=22)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('created', width=160)
        self.tree.column('app', width=220)
        self.tree.column('status', width=140)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # Right: form
        form = ttk.Frame(right, padding=8)
        form.pack(fill=tk.BOTH, expand=True)
        r = 0
        ttk.Label(form, text='App Name:').grid(row=r, column=0, sticky='w'); self.app_var = tk.StringVar();
        ttk.Entry(form, textvariable=self.app_var, width=40).grid(row=r, column=1, sticky='w'); r += 1

        ttk.Label(form, text='Suggested By:').grid(row=r, column=0, sticky='w');
        self.suggested_by_var = tk.StringVar(value=self.sm.current_user or '')
        ttk.Entry(form, textvariable=self.suggested_by_var, width=30, state='readonly').grid(row=r, column=1, sticky='w'); r += 1

        ttk.Label(form, text='Description:').grid(row=r, column=0, sticky='nw');
        self.desc = tk.Text(form, width=70, height=10, wrap='word')
        self.desc.grid(row=r, column=1, sticky='nsew'); r += 1
        form.columnconfigure(1, weight=1); form.rowconfigure(r-1, weight=1)

        ttk.Label(form, text='Action Taken:').grid(row=r, column=0, sticky='nw');
        self.action = tk.Text(form, width=70, height=5, wrap='word')
        self.action.grid(row=r, column=1, sticky='nsew'); r += 1

        # Flags row
        flags = ttk.Frame(form); flags.grid(row=r, column=1, sticky='w'); r += 1
        self.completed_var = tk.BooleanVar(); ttk.Checkbutton(flags, text='Completed', variable=self.completed_var).pack(side=tk.LEFT)
        self.not_approved_var = tk.BooleanVar(); ttk.Checkbutton(flags, text='Not Approved', variable=self.not_approved_var).pack(side=tk.LEFT, padx=(12,0))
        self.closed_var = tk.BooleanVar(); ttk.Checkbutton(flags, text='Closed', variable=self.closed_var).pack(side=tk.LEFT, padx=(12,0))

        ttk.Label(form, text='Not Approved Reason:').grid(row=r, column=0, sticky='nw');
        self.not_approved_reason = tk.Text(form, width=70, height=3, wrap='word')
        self.not_approved_reason.grid(row=r, column=1, sticky='nsew'); r += 1

        # Screenshot preview
        ttk.Label(form, text='Screenshot:').grid(row=r, column=0, sticky='nw')
        self.preview_lbl = ttk.Label(form)
        self.preview_lbl.grid(row=r, column=1, sticky='w'); r += 1

        # Bind paste (Ctrl+V) in description to image paste if available
        self.desc.bind('<Control-v>', self._on_ctrl_v)

    # Data
    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _status_from_row(self, row):
        completed = row[8] or 0
        closed = row[14] or 0
        not_appr = row[11] or 0
        if closed or not_appr:
            return 'Closed'
        if completed:
            return 'Completed'
        return 'Open'

    def _load_rows(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        filt = self.filter_var.get()
        where = ''
        params = ()
        if filt == 'Open':
            where = 'WHERE COALESCE(closed_flag,0)=0 AND COALESCE(completed_flag,0)=0 AND COALESCE(not_approved_flag,0)=0'
        elif filt == 'Completed':
            where = 'WHERE COALESCE(completed_flag,0)=1'
        elif filt == 'Closed':
            where = 'WHERE COALESCE(closed_flag,0)=1 OR COALESCE(not_approved_flag,0)=1'
        sql = f"""
            SELECT id, created_ts, app_name, description, screenshot_path, suggested_by,
                   updated_ts, action_taken, completed_flag, completed_ts,
                   not_approved_reason, not_approved_flag, not_approved_ts,
                   closed_flag, closed_ts
            FROM software_improvement_suggestions
            {where}
            ORDER BY datetime(COALESCE(created_ts, '1970-01-01')) DESC
        """
        try:
            conn = self._conn(); cur = conn.cursor(); cur.execute(sql, params)
            rows = cur.fetchall(); conn.close()
            for r in rows:
                status = self._status_from_row(r)
                self.tree.insert('', 'end', values=(r[0], r[1] or '', r[2] or '', status))
        except Exception as e:
            print(f"ERROR[_load_rows]: {e}")

    def _on_select(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        sid = self.tree.set(sel[0], 'id')
        try:
            conn = self._conn(); cur = conn.cursor()
            cur.execute(
                """
                SELECT id, app_name, description, screenshot_path, suggested_by,
                       created_ts, updated_ts, completed_flag, completed_ts,
                       action_taken, not_approved_flag, not_approved_ts,
                       not_approved_reason, closed_flag, closed_ts
                FROM software_improvement_suggestions WHERE id = ?
                """,
                (sid,)
            )
            r = cur.fetchone(); conn.close()
            if not r:
                return
            self.current_id = r[0]
            self.app_var.set(r[1] or '')
            self._set_text(self.desc, r[2] or '')
            self._load_preview(r[3] or '')
            self.suggested_by_var.set(r[4] or (self.sm.current_user or ''))
            self._set_text(self.action, r[9] or '')
            self.completed_var.set(bool(r[7]))
            self.not_approved_var.set(bool(r[10]))
            self.closed_var.set(bool(r[13]))
            self._set_text(self.not_approved_reason, r[12] or '')
        except Exception as e:
            print(f"ERROR[_on_select]: {e}")

    def _set_text(self, widget: tk.Text, value: str):
        widget.delete('1.0', tk.END)
        widget.insert('1.0', value or '')

    def _new(self):
        self.current_id = None
        self.app_var.set('')
        self._set_text(self.desc, '')
        self._set_text(self.action, '')
        self._set_text(self.not_approved_reason, '')
        self.suggested_by_var.set(self.sm.current_user or '')
        self.completed_var.set(False)
        self.not_approved_var.set(False)
        self.closed_var.set(False)
        self._load_preview('')

    def _save(self):
        app = (self.app_var.get() or '').strip()
        if not app:
            messagebox.showerror('Error', 'App Name is required'); return
        desc = self.desc.get('1.0', tk.END).strip()
        action = self.action.get('1.0', tk.END).strip()
        reason = self.not_approved_reason.get('1.0', tk.END).strip()
        suggested_by = self.suggested_by_var.get() or (self.sm.current_user or '')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        completed = 1 if self.completed_var.get() else 0
        not_appr = 1 if self.not_approved_var.get() else 0
        closed = 1 if self.closed_var.get() else 0
        # Completed/flags timestamps
        conn = self._conn(); cur = conn.cursor()
        try:
            if self.current_id is None:
                cur.execute(
                    """
                    INSERT INTO software_improvement_suggestions
                    (app_name, description, screenshot_path, suggested_by, created_ts, updated_ts,
                     completed_flag, completed_ts, action_taken,
                     not_approved_flag, not_approved_ts, not_approved_reason,
                     closed_flag, closed_ts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (app, desc, getattr(self, 'current_screenshot', None), suggested_by, now, now,
                     completed, (now if completed else None), action,
                     not_appr, (now if not_appr else None), reason,
                     closed, (now if closed else None))
                )
                self.current_id = cur.lastrowid
            else:
                # Preserve previous timestamps if already set
                cur.execute("SELECT completed_flag, completed_ts, not_approved_flag, not_approved_ts, closed_flag, closed_ts FROM software_improvement_suggestions WHERE id = ?", (self.current_id,))
                prev = cur.fetchone() or (0, None, 0, None, 0, None)
                comp_ts = prev[1] or (now if completed and not prev[0] else None)
                nap_ts = prev[3] or (now if not_appr and not prev[2] else None)
                clo_ts = prev[5] or (now if closed and not prev[4] else None)
                cur.execute(
                    """
                    UPDATE software_improvement_suggestions
                    SET app_name=?, description=?, screenshot_path=?, suggested_by=?, updated_ts=?,
                        completed_flag=?, completed_ts=COALESCE(completed_ts, ?),
                        action_taken=?, not_approved_flag=?, not_approved_ts=COALESCE(not_approved_ts, ?),
                        not_approved_reason=?, closed_flag=?, closed_ts=COALESCE(closed_ts, ?)
                    WHERE id = ?
                    """,
                    (app, desc, getattr(self, 'current_screenshot', None), suggested_by, now,
                     completed, comp_ts, action, not_appr, nap_ts, reason, closed, clo_ts, self.current_id)
                )
            conn.commit()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save: {e}')
        finally:
            conn.close()
        self._load_rows()

    def _delete(self):
        if not self.current_id:
            return
        if not messagebox.askyesno('Delete', 'Delete this suggestion?'):
            return
        try:
            conn = self._conn(); cur = conn.cursor(); cur.execute('DELETE FROM software_improvement_suggestions WHERE id = ?', (self.current_id,)); conn.commit(); conn.close()
            self._new(); self._load_rows()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to delete: {e}')

    # Screenshot handling
    def _on_ctrl_v(self, event=None):
        # Attempt image paste; if not image or not available, fall back to normal paste
        if ImageGrab is None:
            return None  # allow default
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._save_and_set_screenshot(img)
                return 'break'
        except Exception:
            pass
        return None

    def _paste_screenshot(self):
        if ImageGrab is None:
            messagebox.showinfo('Paste Screenshot', 'Pillow is not installed. Paste screenshot requires Pillow (PIL).')
            return
        try:
            img = ImageGrab.grabclipboard()
            if not isinstance(img, Image.Image):
                messagebox.showinfo('Paste Screenshot', 'No image found on clipboard.')
                return
            self._save_and_set_screenshot(img)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to paste screenshot: {e}')

    def _save_and_set_screenshot(self, img):
        # Save under updates/screenshots
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        sid = self.current_id or 'new'
        fname = f'suggestion_{sid}_{ts}.png'
        path = os.path.join(SCREENSHOT_DIR, fname)
        try:
            img.save(path, format='PNG')
            self.current_screenshot = path
            self._load_preview(path)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save screenshot: {e}')

    def _load_preview(self, path: str):
        if not path or not os.path.exists(path) or Image is None or ImageTk is None:
            self.preview_image = None
            self.preview_lbl.configure(image='', text='(No screenshot)')
            return
        try:
            im = Image.open(path)
            im.thumbnail((480, 320))
            self.preview_image = ImageTk.PhotoImage(im)
            self.preview_lbl.configure(image=self.preview_image, text='')
        except Exception:
            self.preview_image = None
            self.preview_lbl.configure(image='', text='(Failed to load image)')


def main():
    app = SuggestionsApp()
    app.root.mainloop()


if __name__ == '__main__':
    main()

