import json
import os
from typing import Dict


def _prefs_path() -> str:
    base = os.path.join(os.path.expanduser('~'), '.drafting_tools')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, 'ui_prefs.json')


def _load_prefs() -> Dict:
    path = _prefs_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_prefs(data: Dict) -> None:
    path = _prefs_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def apply_tree_columns(tree, key: str) -> None:
    """Apply saved column widths to a ttk.Treeview given a unique key."""
    data = _load_prefs()
    widths = data.get('tree_columns', {}).get(key)
    if not widths:
        return
    try:
        for col, w in widths.items():
            if col in tree['columns']:
                tree.column(col, width=int(w))
    except Exception:
        pass


def bind_tree_column_persistence(tree, key: str, root=None, debounce_ms: int = 300) -> None:
    """Bind events to persist column widths for a ttk.Treeview.

    - key should be unique per view (e.g., 'print_package.project_tree').
    - root is used for debouncing; if None, uses the tree itself.
    """
    widget_for_after = root or tree
    save_after_id = {'id': None}

    def save_columns():
        data = _load_prefs()
        all_cols = {}
        try:
            for col in tree['columns']:
                try:
                    all_cols[col] = int(tree.column(col, option='width'))
                except Exception:
                    continue
        except Exception:
            return
        data.setdefault('tree_columns', {})[key] = all_cols
        _save_prefs(data)

    def debounce_save(_event=None):
        if save_after_id['id'] is not None:
            try:
                widget_for_after.after_cancel(save_after_id['id'])
            except Exception:
                pass
        save_after_id['id'] = widget_for_after.after(debounce_ms, save_columns)

    try:
        # Apply on init
        apply_tree_columns(tree, key)
        # Save when mouse released or dragged
        tree.bind('<ButtonRelease-1>', debounce_save)
        tree.bind('<B1-Motion>', debounce_save)
    except Exception:
        pass

