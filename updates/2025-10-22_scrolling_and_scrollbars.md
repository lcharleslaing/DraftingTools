# Update Log — 2025-10-22 — Scrolling and Scrollbars

Time: 2025-10-22T00:30:00Z
Author: Codex CLI Assistant

## Summary
Standardized mouse wheel scrolling across apps and fixed missing/unused scrollbars in key views. Added a reusable utility to bind mouse wheel events consistently on Windows/macOS/Linux.

## Changes

### New Utility
- `DraftingTools/scroll_utils.py`
  - `bind_mousewheel_to_treeview(tree)` and `bind_mousewheel_to_canvas(canvas)` for cross-platform wheel scrolling.

### Workflow Manager
- `DraftingTools/workflow_manager.py:18` — import scroll utils.
- `DraftingTools/workflow_manager.py:85` — bind mouse wheel to the workflow canvas.

### Print Package
- `DraftingTools/print_package.py:14` — import scroll utils.
- `DraftingTools/print_package.py:102` — bind wheel to current drawings Treeview.
- `DraftingTools/print_package.py:135` — bind wheel to global drawings Treeview.

### Product Configurations
- `DraftingTools/product_configurations.py:15` — import scroll utils.
- `DraftingTools/product_configurations.py:72` — bind wheel to projects Treeview.

### Projects
- `DraftingTools/projects.py:15` — import scroll utils.
- `DraftingTools/projects.py:229` — bind wheel to main projects Treeview.

### Project Monitor (bug fix + wheels)
- `DraftingTools/project_monitor.py:374` — add and pack vertical scrollbar for projects list and bind wheel.
- `DraftingTools/project_monitor.py:429` — pack vertical and horizontal scrollbars for files Treeview (previously created but not displayed) and bind wheel.

## Rationale
- Improves usability and consistency: users can scroll lists/canvases with the mouse wheel regardless of platform and without needing focus quirks.
- Fixes a UI defect where scrollbars were configured but not visible.

## Notes
- For very wide Treeviews, consider adding horizontal scroll bindings similarly where missing.
- The utility is non-invasive; it only binds wheel events to the target widget.

