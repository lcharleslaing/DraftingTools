import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class DirectoryPicker(ttk.Frame):
    """A directory picker widget with a text field and browse button"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.button = ttk.Button(self, text="📁", command=self.open_directory_picker, width=3)
        self.button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def open_directory_picker(self):
        """Open the directory picker dialog"""
        initial_dir = self.var.get() if self.var.get() and os.path.exists(self.var.get()) else os.getcwd()
        
        directory = filedialog.askdirectory(
            title="Select Directory",
            initialdir=initial_dir
        )
        
        if directory:
            self.var.set(directory)
    
    def get(self):
        """Get the current value"""
        return self.var.get()
    
    def set(self, value):
        """Set the current value"""
        self.var.set(value)

class FilePicker(ttk.Frame):
    """A file picker widget with a text field and browse button"""
    def __init__(self, parent, filetypes=None, **kwargs):
        super().__init__(parent)
        
        self.filetypes = filetypes or [("All Files", "*.*")]
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.button = ttk.Button(self, text="📄", command=self.open_file_picker, width=3)
        self.button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def open_file_picker(self):
        """Open the file picker dialog"""
        initial_dir = os.path.dirname(self.var.get()) if self.var.get() and os.path.exists(self.var.get()) else os.getcwd()
        
        file_path = filedialog.askopenfilename(
            title="Select File",
            initialdir=initial_dir,
            filetypes=self.filetypes
        )
        
        if file_path:
            self.var.set(file_path)
    
    def get(self):
        """Get the current value"""
        return self.var.get()
    
    def set(self, value):
        """Set the current value"""
        self.var.set(value)
