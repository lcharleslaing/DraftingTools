import sys

def _is_windows():
    return sys.platform.startswith('win')

def _is_darwin():
    return sys.platform == 'darwin'

def bind_mousewheel_to_treeview(tree):
    """Enable mouse wheel scrolling on a ttk.Treeview across platforms."""
    def _on_mousewheel(event):
        if _is_windows():
            delta = int(-1 * (event.delta / 120))
            tree.yview_scroll(delta, 'units')
        elif _is_darwin():
            delta = int(-1 * (event.delta))
            tree.yview_scroll(delta, 'units')
        else:
            # X11 sends Button-4/5; this binding may not fire
            pass
        return 'break'

    def _on_linux_scroll_up(event):
        tree.yview_scroll(-1, 'units')
        return 'break'

    def _on_linux_scroll_down(event):
        tree.yview_scroll(1, 'units')
        return 'break'

    tree.bind('<MouseWheel>', _on_mousewheel)
    tree.bind('<Button-4>', _on_linux_scroll_up)
    tree.bind('<Button-5>', _on_linux_scroll_down)

def bind_mousewheel_to_canvas(canvas):
    """Enable mouse wheel scrolling on a Canvas across platforms."""
    def _on_mousewheel(event):
        if _is_windows():
            delta = int(-1 * (event.delta / 120))
            canvas.yview_scroll(delta, 'units')
        elif _is_darwin():
            delta = int(-1 * (event.delta))
            canvas.yview_scroll(delta, 'units')
        return 'break'

    def _on_linux_scroll_up(event):
        canvas.yview_scroll(-1, 'units')
        return 'break'

    def _on_linux_scroll_down(event):
        canvas.yview_scroll(1, 'units')
        return 'break'

    canvas.bind('<MouseWheel>', _on_mousewheel)
    canvas.bind('<Button-4>', _on_linux_scroll_up)
    canvas.bind('<Button-5>', _on_linux_scroll_down)

