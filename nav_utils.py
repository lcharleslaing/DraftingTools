import sys
import subprocess
import time
import psutil

APP_MAP = {
    'dashboard': {'script': 'dashboard.py', 'title': 'Drafting Tools Dashboard'},
    # Title must match the actual window title set in the app
    'projects': {'script': 'projects.py', 'title': 'Project Management - Drafting Tools'},
    'product_configurations': {'script': 'product_configurations.py', 'title': 'Product Configurations - Heater, Tank & Pump'},
    'print_package': {'script': 'print_package.py', 'title': 'Print Package Management - Drafting Tools'},
    'd365_builder': {'script': 'd365_import_formatter.py', 'title': 'D365 Builder'},
    'project_monitor': {'script': 'project_monitor.py', 'title': 'Project File Monitor - Drafting Tools'},
    'drawing_reviews': {'script': 'drawing_reviews.py', 'title': 'Drawing Reviews - Digital Markup System'},
    'drafting_checklist': {'script': 'drafting_items_to_look_for.py', 'title': 'Drafting Drawing Checklist - Drafting Tools'},
    'workflow_manager': {'script': 'workflow_manager.py', 'title': 'Print Package Workflow Manager'},
    'project_workflow': {'script': 'project_workflow.py', 'title': 'Project Workflow'},
    'coil_verification': {'script': 'coil_verification_tool.py', 'title': 'Coil Verification Tool - Drafting Tools'},
    'app_order': {'script': 'app_order.py', 'title': 'App Order Manager - Drafting Tools'},
    'assist_engineering': {'script': 'assist_engineering.py', 'title': 'Assist Engineering'},
}

CACHED_PIDS = {}


def _find_process_for_script(script_name: str):
    # Fast path: cached PID
    pid = CACHED_PIDS.get(script_name)
    if pid and psutil.pid_exists(pid):
        try:
            return psutil.Process(pid)
        except Exception:
            CACHED_PIDS.pop(script_name, None)
    # Time‑budgeted scan to avoid slow downs
    deadline = time.perf_counter() + 0.3  # 300ms budget
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            if any(script_name in part for part in cmdline):
                CACHED_PIDS[script_name] = proc.pid
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if time.perf_counter() > deadline:
            break
    return None


def _focus_window_by_title(title: str) -> bool:
    try:
        import win32gui
        import win32con
        import win32api

        hwnds = []

        def enum_handler(hwnd, _param):
            if win32gui.IsWindowVisible(hwnd):
                text = win32gui.GetWindowText(hwnd)
                if text and title in text:
                    hwnds.append(hwnd)

        win32gui.EnumWindows(enum_handler, None)
        if not hwnds:
            return False
        hwnd = hwnds[0]
        # Restore if minimized
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def _focus_window_by_pid(pid: int) -> bool:
    """Attempt to focus any top-level window owned by the given PID (Windows)."""
    try:
        import win32gui
        import win32con
        import win32process

        target = []

        def enum_handler(hwnd, _param):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _tid, wp = win32process.GetWindowThreadProcessId(hwnd)
                    if wp == pid:
                        target.append(hwnd)
                except Exception:
                    pass

        win32gui.EnumWindows(enum_handler, None)
        if not target:
            return False
        hwnd = target[0]
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def open_or_focus(app_key: str):
    cfg = APP_MAP.get(app_key)
    if not cfg:
        return
    script = cfg['script']
    title = cfg['title']

    # If process exists, focus its window instead of spawning another
    proc = _find_process_for_script(script)
    if proc:
        # Try focus by title; if that fails, try by owning PID
        if _focus_window_by_title(title) or _focus_window_by_pid(proc.pid):
            return
        # As a fallback (e.g., pywin32 missing), attempt to launch to ensure user sees a window
        # May result in a second instance in rare cases, but improves UX when focus is not possible.
        try:
            p = subprocess.Popen([sys.executable, script], start_new_session=True)
            CACHED_PIDS[script] = p.pid
        except Exception:
            pass
        return

    # Launch new process
    try:
        p = subprocess.Popen([sys.executable, script], start_new_session=True)
        CACHED_PIDS[script] = p.pid
    except Exception:
        pass
