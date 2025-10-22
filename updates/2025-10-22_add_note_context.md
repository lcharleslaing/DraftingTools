# Update Log — 2025-10-22 — Add Note via Right-Click

Time: 2025-10-22T01:40:00Z
Author: Codex CLI Assistant

## Summary
Users can right‑click on a job entry (typically in the left pane) in multiple apps to quickly add a new note. A modal opens with a text area; saving appends the note to the job’s consolidated notes in the central database.

## Implementation
- New shared helper: `DraftingTools/notes_utils.py`
  - `open_add_note_dialog(parent, job_number)` shows the modal.
  - `append_job_note(job_number, text)` appends notes into `job_notes` table with timestamp and (if available) current user/department from Settings.
- Apps updated with context menus:
  - Print Package: `print_package.py` — Project tree.
  - Product Configurations: `product_configurations.py` — Project tree.
  - Projects: `projects.py` — Existing job context menu now includes “Add New Note…”.
  - Project Monitor: `project_monitor.py` — Projects list.
  - D365 Import Builder: `d365_import_formatter.py` — Projects list.
  - Drafting Checklist: `drafting_items_to_look_for.py` — Projects tree.
  - Workflow Manager: `workflow_manager.py` — Reviews tree.

## Notes
- Notes are stored in `job_notes(job_number TEXT PRIMARY KEY, notes TEXT)` in `drafting_tools.db`.
- New notes are prepended with a header: `=== YYYY-MM-DD HH:MM by USER (DEPT) ===`.
- The Projects app already displays and prints job notes; these additions provide quick, cross‑app note capture.

