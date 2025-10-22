# Update Log — 2025-10-22 — Column Width Persistence

Time: 2025-10-22T01:00:00Z
Author: Codex CLI Assistant

## Summary
Add per-user persistence of Treeview column widths across the suite. When users resize columns, the widths are saved and restored on next launch for that specific app/view.

## Implementation

### Shared Utility
- `DraftingTools/ui_prefs.py`
  - Stores preferences at `~/.drafting_tools/ui_prefs.json`.
  - `apply_tree_columns(tree, key)` to restore widths.
  - `bind_tree_column_persistence(tree, key, root)` to debounce and save widths on resize.

### Apps Updated
- Print Package: `print_package.py`
  - Keys: `print_package.project_tree`, `print_package.current_drawings`, `print_package.global_drawings`.
- Product Configurations: `product_configurations.py`
  - Key: `product_configurations.project_tree`.
- Project Monitor: `project_monitor.py`
  - Keys: `project_monitor.projects_tree`, `project_monitor.files_tree`.
- Workflow Manager: `workflow_manager.py`
  - Key: `workflow_manager.reviews_tree`.
- Settings: `settings.py`
  - Keys: `settings.users_tree`, `settings.dept_tree`.
- D365 Import Builder: `d365_import_formatter.py`
  - Keys: `d365.projects_tree`, `d365.report_tree`, `d365.settings_tree`.
- Drawing Reviews: `drawing_reviews.py`
  - Keys: `drawing_reviews.drawings_tree`, `drawing_reviews.reviewed_tree`.
- Drafting Checklist: `drafting_items_to_look_for.py`
  - Keys: `drafting_checklist.project_tree`, `drafting_checklist.master_tree`.
- App Order Manager: `app_order.py`
  - Key: `app_order.tree`.

### Notes
- Projects (`projects.py`) already had its own per-user persistence logic and remains unchanged for now.
- Keys are unique per view to prevent collisions.
- Persistence triggers on mouse release/drag events; saved widths are applied during widget creation.

## Rationale
- Improves usability by remembering each user’s preferred column sizing across sessions and per view.

