import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import calendar

class DatePicker:
    def __init__(self, parent, initial_date=None):
        self.parent = parent
        self.result = None
        self.initial_date = initial_date or datetime.now()
        
        # Create popup window
        self.window = tk.Toplevel(parent)
        self.window.title("Select Date")
        self.window.geometry("300x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        self.update_calendar()
    
    def create_widgets(self):
        """Create the date picker widgets"""
        # Header frame
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Month/Year navigation
        nav_frame = ttk.Frame(header_frame)
        nav_frame.pack(fill=tk.X)
        
        self.prev_button = ttk.Button(nav_frame, text="◀", command=self.prev_month, width=3)
        self.prev_button.pack(side=tk.LEFT)
        
        self.month_year_var = tk.StringVar()
        self.month_year_label = ttk.Label(nav_frame, textvariable=self.month_year_var, font=('Arial', 12, 'bold'))
        self.month_year_label.pack(side=tk.LEFT, expand=True)
        
        self.next_button = ttk.Button(nav_frame, text="▶", command=self.next_month, width=3)
        self.next_button.pack(side=tk.RIGHT)
        
        # Calendar frame
        self.calendar_frame = ttk.Frame(self.window)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Day labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            label = ttk.Label(self.calendar_frame, text=day, font=('Arial', 9, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1)
        
        # Buttons frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Today", command=self.set_today).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self.clear_date).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
    
    def update_calendar(self):
        """Update the calendar display"""
        # Clear existing day buttons
        for widget in self.calendar_frame.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.destroy()
        
        # Update month/year label
        month_name = calendar.month_name[self.initial_date.month]
        self.month_year_var.set(f"{month_name} {self.initial_date.year}")
        
        # Get calendar data
        cal = calendar.monthcalendar(self.initial_date.year, self.initial_date.month)
        
        # Create day buttons
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day != 0:  # Only show days that exist in the month
                    button = ttk.Button(
                        self.calendar_frame, 
                        text=str(day), 
                        command=lambda d=day: self.select_date(d),
                        width=3
                    )
                    button.grid(row=week_num + 1, column=day_num, padx=1, pady=1, sticky='nsew')
                    
                    # Highlight today
                    today = datetime.now()
                    if (self.initial_date.year == today.year and 
                        self.initial_date.month == today.month and 
                        day == today.day):
                        button.configure(style='Accent.TButton')
        
        # Configure grid weights
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
        for i in range(6):
            self.calendar_frame.rowconfigure(i + 1, weight=1)
    
    def prev_month(self):
        """Go to previous month"""
        if self.initial_date.month == 1:
            self.initial_date = self.initial_date.replace(year=self.initial_date.year - 1, month=12)
        else:
            self.initial_date = self.initial_date.replace(month=self.initial_date.month - 1)
        self.update_calendar()
    
    def next_month(self):
        """Go to next month"""
        if self.initial_date.month == 12:
            self.initial_date = self.initial_date.replace(year=self.initial_date.year + 1, month=1)
        else:
            self.initial_date = self.initial_date.replace(month=self.initial_date.month + 1)
        self.update_calendar()
    
    def select_date(self, day):
        """Select a specific date"""
        self.selected_date = self.initial_date.replace(day=day)
        self.ok()
    
    def set_today(self):
        """Set to today's date"""
        self.selected_date = datetime.now()
        self.ok()
    
    def clear_date(self):
        """Clear the selected date"""
        self.selected_date = None
        self.ok()
    
    def ok(self):
        """Confirm selection"""
        if hasattr(self, 'selected_date'):
            self.result = self.selected_date.strftime("%Y-%m-%d")
        else:
            self.result = None
        self.window.destroy()
    
    def cancel(self):
        """Cancel selection"""
        self.result = None
        self.window.destroy()

class DateEntry(ttk.Frame):
    """A date entry widget with a date picker button"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.button = ttk.Button(self, text="📅", command=self.open_date_picker, width=3)
        self.button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def open_date_picker(self):
        """Open the date picker"""
        initial_date = None
        if self.var.get():
            try:
                initial_date = datetime.strptime(self.var.get(), "%Y-%m-%d")
            except ValueError:
                initial_date = datetime.now()
        else:
            initial_date = datetime.now()
        
        picker = DatePicker(self, initial_date)
        self.wait_window(picker.window)
        
        if picker.result is not None:
            self.var.set(picker.result)
    
    def get(self):
        """Get the current value"""
        return self.var.get()
    
    def set(self, value):
        """Set the current value"""
        self.var.set(value)
