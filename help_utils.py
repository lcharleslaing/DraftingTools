import tkinter as tk
from tkinter import ttk

def show_help(parent, title: str, text: str):
    win = tk.Toplevel(parent)
    win.title(f"Help — {title}")
    win.transient(parent)
    win.grab_set()
    win.geometry("680x480")

    frm = ttk.Frame(win, padding=10)
    frm.pack(fill='both', expand=True)

    lbl = ttk.Label(frm, text=title, font=('Segoe UI', 11, 'bold'))
    lbl.pack(anchor='w')

    txt = tk.Text(frm, wrap='word')
    txt.pack(fill='both', expand=True, pady=(6,6))
    txt.insert('1.0', text)
    txt.config(state='disabled')

    ttk.Button(frm, text='Close', command=win.destroy).pack(anchor='e')

def add_help_button(parent, title: str, text: str) -> ttk.Button:
    return ttk.Button(parent, text='Help', command=lambda: show_help(parent, title, text))

