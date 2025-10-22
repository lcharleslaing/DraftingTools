import tkinter as tk
from tkinter import ttk
from nav_utils import open_or_focus


def add_app_bar(root, current_app: str = None) -> tk.Frame:
    """Add a top app bar with navigation buttons to all apps.

    current_app: optional key from nav_utils.APP_MAP to disable its button.
    """
    bar = ttk.Frame(root)
    bar.pack(fill='x')

    apps = [
        ('Dashboard', 'dashboard'),
        ('Projects', 'projects'),
        ('Configurations', 'product_configurations'),
        ('Print Package', 'print_package'),
        ('D365 Builder', 'd365_builder'),
        ('Project Monitor', 'project_monitor'),
        ('Drawing Reviews', 'drawing_reviews'),
        ('Checklist', 'drafting_checklist'),
        ('Proj Workflow', 'project_workflow'),
        ('Workflow', 'workflow_manager'),
        ('Coil Verify', 'coil_verification'),
    ]

    for label, key in apps:
        state = 'disabled' if current_app and key == current_app else 'normal'
        btn = ttk.Button(bar, text=label, state=state, command=lambda k=key: open_or_focus(k))
        btn.pack(side='left', padx=(4, 0), pady=2)

    # Spacer expands to push items to left neatly
    spacer = ttk.Frame(bar)
    spacer.pack(side='left', expand=True, fill='x')

    return bar

