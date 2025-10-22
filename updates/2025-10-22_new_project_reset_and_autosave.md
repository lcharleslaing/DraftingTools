# Update Log — 2025-10-22 — New Project Reset + Autosave

Time: 2025-10-22T07:45:00Z
Author: Codex CLI Assistant

## Summary
Improved the New Project flow in Projects by fully clearing selection and form state when clicking "New Project", and aligning autosave behavior to avoid saving during reset while ensuring edits continue to autosave once a valid job number is entered.

## User‑Visible Changes
- Clicking "New Project" now:
  - Unselects any selected project row in the list and removes row highlight.
  - Clears all Project Details fields (job number, directories, customer name/location, assigned designer, project engineer, assignment/start/completion/due dates, released to Dee, duration).
  - Clears all Project Workflow fields (all checkboxes unchecked; all engineer dropdowns cleared; all workflow dates cleared, including Release to Dee due date and its display).
  - Clears Job Notes (text area) and resets notes context (no job selected).
  - Refreshes Quick Access and Specifications panels to show "No project selected" until a job is specified.
  - Resets the cover sheet button to the default state (no current project).

- Autosave continues to work as you fill in fields once a valid 5‑digit job number is entered. Changes are silently saved on update.

## Implementation
- File: `projects.py`
  - Function: `ProjectsApp.new_project`
    - Temporarily disables autosave by setting `self._loading_project = True` during the reset.
    - Unselects `ttk.Treeview` selection, clears item tags, and resets focus.
    - Sets `self.current_project = None` to reflect the unselected state across the UI.
    - Clears Project Details fields: `job_number_var`, directory pickers, customer name/location (and their path pickers), `assigned_to_var`, `project_engineer_var`, all date fields (assignment/start/completion/due/released), and `duration_var`.
    - Clears Project Workflow fields: unchecks all related `BooleanVar`s; clears all engineer `StringVar`s and all associated `DateEntry` widgets; clears Release to Dee due date and display label.
    - Clears notes: sets `self.current_job_notes = ""` and empties `notes_text`.
    - Clears quick-access document lists and KOM path.
    - Refreshes Quick Access (`update_quick_access`) and Specifications (`update_specifications`) panels.
    - Updates the cover sheet button via `update_cover_sheet_button`.
    - Re-enables autosave by resetting `self._loading_project = False` at the end.

## Rationale
- Prevent stale selection or data from carrying over when starting a new project.
- Ensure a truly blank slate: no checkboxes selected, no dropdowns populated, and no leftover dates/notes.
- Avoid accidental autosave of the cleared state while resetting the form.

## Testing / Validation Steps
1. Launch Projects: `python projects.py`.
2. Select any project from the list and verify fields populate.
3. Click "New Project":
   - The tree selection is cleared; no row is highlighted.
   - All Project Details fields are empty; all dropdowns show no value.
   - All Workflow checkboxes are unchecked; all dates and engineer values are empty; Release to Dee due date and display are empty.
   - Notes area is blank and no job is set as current.
   - Quick Access and Specifications panels indicate no project selected.
   - Cover sheet button shows the default state.
4. Enter a valid 5‑digit job number (e.g., `12345`) and begin filling fields. Confirm changes autosave without prompts.

## Backward Compatibility / Notes
- No database schema changes.
- Autosave behavior remains the same (requires a valid 5‑digit job number), but is suppressed during the reset to avoid saving cleared values.
- Assignment Date now starts blank on "New Project" (previously defaulted to today); this matches the requirement to start with empty values. If desired, we can reintroduce a default date.

## Affected Areas
- UI: Projects → New Project button behavior, selection state, form reset, workflow panels, notes, quick access/specifications, cover sheet button state.
- Persistence: Autosave continues once a valid job number is provided.

