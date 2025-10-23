# Drafting Tools Suite — Comprehensive Codebase Overview

This document maps the entire suite: what each app does, how they communicate, data model, and operational flows. Paths are relative to the repository root.

## 1) Big Picture

- Windows‑first, Tkinter desktop suite backed by a shared SQLite database `drafting_tools.db`.
- Unified navigation via a top app bar and the Dashboard launcher; right‑click job menus provide cross‑app deep links.
- Cross‑cutting features: per‑user UI prefs, job notes, standardized job number handling, and versioned project workflow templates.

Key apps
- Dashboard (`dashboard.py`) — launcher, live counters, process management, and Settings access.
- Projects (`projects.py`) — job tracking, details, dates, people, Standard workflow per project, quick access, duplication.
- Job Notes (`job_notes.py`) — dedicated notes browser/editor with full CRUD for all jobs.
- Product Configurations (`product_configurations.py`) — Heater/Tank/Pump configuration linked to jobs.
- Print Package (`print_package.py`) — manage drawings and printing; integrate with print‑package workflow.
- Workflow Manager (`workflow_manager.py`) — visualize and operate Print Package Review stages.
- Project Workflow (`project_workflow.py`) — standalone editor for Standard (versioned) workflow + per‑project states.
- D365 Builder (`d365_import_formatter.py`) — generate D365 BOM import rows, with its own DB and tie‑ins to projects.
- Project Monitor (`project_monitor.py`) — scan/track file changes per job with unread counts.
- Drafting Checklist (`drafting_items_to_look_for.py`) — QC checklist and project linking.
- Drawing Reviews (`drawing_reviews.py`) — digital markups workflow (standalone module).
- Utilities/Tools — App Order Manager (`app_order.py`), Assist Engineering (`assist_engineering.py`), suggestions, backup tools.

Shared modules
- Navigation: `app_nav.py` (UI app bar), `nav_utils.py` (open/focus windows, `APP_MAP`).
- Notes: `notes_utils.py` (append + dialog), integrated across apps.
- UI/UX helpers: `help_utils.py`, `ui_prefs.py`, `scroll_utils.py`, `duration_utils.py`, `date_picker.py`, `directory_picker.py`.
- Database: `database_setup.py` (schema + safeguards), `db_utils.py` (connections), `backup/*` assets.

## 2) Inter‑App Linking and UX Patterns

Global app bar
- All major apps call `add_app_bar(root, current_app=...)` to render top navigation.
- `nav_utils.APP_MAP` defines script names and window titles for focus/launch.

Right‑click job context
- Projects left table adds: Open in other apps, Duplicate, Add New Note…, Open in Job Notes.
- Print Package, Product Configurations, Drafting Checklist, Project Monitor, D365 Builder, Workflow Manager all include job right‑click menus with “Add New Note…” and “Open in Job Notes”.

Job preloading
- Many apps accept `--job <job_number>` to focus a specific job at startup: `projects.py`, `product_configurations.py`, `print_package.py`, `d365_import_formatter.py`, `coil_verification_tool.py`, `job_notes.py`.

Per‑user UI preferences
- Column widths and some UI state are persisted to `~/.drafting_tools/ui_prefs.json` (see `ui_prefs.py`).

Fullscreen & window behavior
- Most apps start maximized. `F11` toggles fullscreen where implemented.

## 3) Job Notes System

Table
- `job_notes(job_number TEXT PRIMARY KEY, notes TEXT)` stores the notes blob per job.

APIs
- `notes_utils.append_job_note(job, text)`: prepends a timestamped note, including current user/department from `settings.py` when available.
- `notes_utils.open_add_note_dialog(parent, job=None, on_saved=None)`: modal editor for adding notes.
  - If a job is provided, saves to that job.
  - If no job is selected: prompts to create a Documentation Only job, asks for Job Number and Job Path, creates the job (in `projects`), then saves the note.

Job Notes app (`job_notes.py`)
- Left: jobs (Job #, Customer, Due). Right: live notes editor.
- Buttons: Save Notes, New Note… (supports no‑selection doc‑only flow), Delete Notes.
- Integrated across apps via “Open in Job Notes”.

## 4) Projects App (Projects Management)

File: `projects.py`

Features
- Project list with search/sort, Show/Hide Completed, and right‑click deep links.
- Details: job directory, customer name/location (+ pickers), assigned designer, project engineer, assignment/start/due/completion dates, Release to Dee.
- Standard Workflow (Template) per project: start/complete/transfer/receive step events; planned due date chain recalculated.
- Quick Access panels and Excel‑assisted spec extraction for Heater Design (supports Can Size and Nozzle details from sheets, with helpers).
- Autosave all fields; Save button for explicit feedback.
- Duplicate project: creates a unique “12345 (n)” copy; clones `project_workflow_steps` and `project_step_tasks` with states cleared; recomputes planned due dates; appends a stamped note.

Data integrity
- Job numbers are normalized on save to “12345” or “12345 (n)”.
- ON CONFLICT(job_number) upsert prevents duplicate rows.
- DB initializer enforces `UNIQUE(projects.job_number)` and singleton‑table unique indexes.

Template‑driven workflow
- Global template tables: `workflow_templates(id,name,version,is_active,created_date)`, `workflow_template_steps(template_id, order_index, department, group_name, title, planned_duration_minutes)`.
- Per‑project tables: `project_workflow_steps(project_id, template_id, template_step_id, order_index, …, planned_due_date, actual_duration_minutes)`; `project_step_tasks(project_step_id, template_task_id, order_index, title, is_checked, checked_ts)`.
- Projects seeds steps from the active “Standard” template for new jobs; planned due dates compute backwards from project due date using business‑day math (see `duration_utils.py`).

Notes in Projects
- Inline text area under the projects table shows/edit notes for the selected job.
- Context menu includes “Add New Note…” and “Open in Job Notes”.

## 5) Product Configurations

File: `product_configurations.py`

Features
- Heater/Tank/Pump configuration fields with autosave; dropdowns sourced from tables.
- Left projects pane with search and “Show Completed” toggle (based on release/completion presence).
- Right‑click: Add New Note…, Open in Job Notes; supports `--job`.

## 6) Print Package Management

File: `print_package.py`

Features
- Left: Projects (with drawing counts and completed toggle); right: Drawings management for current job.
- Global drawing search; add drawing to current job; toggle Printed; double‑click/open in external apps.
- Printing via Windows Shell (`win32api.ShellExecute`) with fallbacks.
- Right‑click: Add New Note…, Open in Job Notes; supports `--job`.

Data
- `drawings(job_number, drawing_path, drawing_name, drawing_type, file_extension, printed, added_by, added_date)`.
- Auxiliary: printer setup tables; package import/export (JSON) helpers.

## 7) Print Package Workflow

Files: `print_package_workflow.py`, `workflow_manager.py`

Engine (`print_package_workflow.py`)
- 8‑stage review flow; per‑job review record and per‑stage status.
- Moves/copies files across stage folders under `…/PP-Print Packages/` in a job directory.

UI (`workflow_manager.py`)
- Left: Active reviews (filter by department, right‑click Add Note… / Open in Job Notes).
- Right: Details pane with visualization; actions to complete stage, advance, open folder.

Tables (high‑level)
- `print_package_reviews(job_number, created_date, …)`
- `print_package_workflow(review_id, job_number, stage, department, status, reviewer, …)`
- `print_package_files(review_id, job_number, path, stage, …)`

## 8) Project Workflow (Standalone)

File: `project_workflow.py`

- Tab 1: Projects — per‑project Standard workflow state (apply template, recompute dues, sync tasks).
- Tab 2: Standard Template — edit steps and per‑step default tasks; `Save As New Version (Activate)` versioning.
- Uses the same tables as Projects’ embedded workflow section.

## 9) D365 Builder

File: `d365_import_formatter.py`

- Generates D365 BOM import rows for heaters/tanks/pumps; stores to `d365_builder.db`.
- Lists active projects from `drafting_tools.db` to provide context.
- Right‑click projects: Add New Note…, Open in Job Notes; supports `--job`.

## 10) Project Monitor

File: `project_monitor.py`

- Scans project folders, tracks file additions/modifications/deletions; displays unread counts.
- Sorting: unread files and file counts with due‑date tie breaks.
- Right‑click: Add New Note…, Open in Job Notes.
- Utilities: mark as read, remove duplicates, ignore certain files, mark project complete.

## 11) Drafting Checklist and Drawing Reviews

Drafting Checklist (`drafting_items_to_look_for.py`)
- Master checklist management and per‑project checklist views.
- Right‑click projects: Add New Note…, Open in Job Notes; supports `--job`.

Drawing Reviews (`drawing_reviews.py`)
- Digital markup and review tool. App bar integration; notes dialog available from context menus where exposed.

## 12) Navigation, Process, and Settings

App bar & launch/focus (`app_nav.py`, `nav_utils.py`)
- `APP_MAP` maps logical names to `script` and `title` used to find/focus running windows via `pywin32`.
- `open_or_focus(key)` prefers focusing an existing window; otherwise launches a new process.

Dashboard (`dashboard.py`)
- Maximized launcher. Tiles for all apps (including Job Notes). Tracks child processes and provides a kill/cleanup on exit.
- Live counters: pulls from `drafting_tools.db` for active projects, configurations, print package jobs, and more.
- Settings button opens `settings.py`.

Settings (`settings.py`)
- Users, departments, and app settings. Stores admin session (8‑hour window). Current user/department used by notes stamping.

## 13) Database Schema and Safeguards

Initializer (`database_setup.py`)
- Creates all tables using idempotent `CREATE TABLE IF NOT EXISTS`.
- Adds new columns via guarded `ALTER TABLE … ADD COLUMN`.
- Populates starter data for designers/engineers/app order.
- Creates indexes for common lookups (templates, steps, workflow, drawings, print package tables, D365 tables, etc.).
- Deduplication & uniqueness safeguards:
  - De‑duplicate singleton tables by `project_id` (keep latest) for: `initial_redline`, `ops_review`, `d365_bom_entry`, `peter_weck_review`, `release_to_dee`.
  - Enforce `UNIQUE(projects.job_number)` with automatic cleanup if needed.
  - Enforce `UNIQUE(project_id)` on the singleton tables above.
- Backup and export:
  - `DatabaseManager.backup_database()` copies DB to `backup/master_drafting_tools.db`.
  - `DatabaseManager.export_to_json()` dumps all tables to `backup/master_data.json`.

Core tables (selected)
- People: `designers(id,name,department_id)`, `engineers(id,name,department_id)`.
- Projects: `projects(id, job_number UNIQUE, job_directory, customer_name, customer_location, …, assigned_to_id, project_engineer_id, assignment_date, start_date, completion_date, total_duration_days, released_to_dee, due_date, last_cover_sheet_date)`.
- Legacy workflow sections: `initial_redline`, `redline_updates(project_id, update_cycle, …)`, `ops_review`, `d365_bom_entry`, `peter_weck_review`, `release_to_dee(project_id UNIQUE, release_date, is_completed, …)`.
- Template workflow: `workflow_templates`, `workflow_template_steps`, `workflow_step_tasks`.
- Per‑project workflow: `project_workflow_steps`, `project_step_tasks`.
- Notes: `job_notes(job_number PRIMARY KEY, notes)`.
- Print packages: `drawings`, `print_packages`, `print_package_reviews`, `print_package_workflow`, `print_package_files`.
- D365: `d365_import_configs`, `d365_part_numbers`, `d365_import_params` (plus app‑local `d365_builder.db`).

## 14) Printing & External Integrations

- Uses Windows Shell/`pywin32` for printing; opens DWG/IDW via external apps when needed.
- OS file opens via `os.startfile`.

## 15) CLI and Launching

- Most apps support `--job <job_number>` to preload a job (Projects, Product Configs, Print Package, D365 Builder, Coil Verify, Job Notes).
- The Dashboard records/tracks child PIDs and can terminate them cleanly.

## 16) Conventions & Coding Style

- Python 3.8+, PEP 8, 4‑space indents; Tkinter `ttk` preferred; grid layout with explicit sticky.
- Names: functions/vars/modules `snake_case`; classes `CamelCase`; constants `UPPER_SNAKE_CASE`.
- Docstrings: imperative first line. Light use of trailing commas where helpful.

## 17) Known Behaviors & Guardrails

- Job number normalization everywhere prevents accidental duplicates. Duplicate copies must be explicit: `12345 (1)`, `12345 (2)`, …
- Projects autosave is disabled while loading a selection to avoid race conditions.
- Release/Completed status queries avoid multi‑row joins that duplicate projects.
- Column widths and certain layout prefs persist per user in `~/.drafting_tools`.

## 18) Setup & Running

- Create venv (Windows): `python -m venv .venv && .\.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
- Initialize DB: `python database_setup.py`
- Run Dashboard (recommended): `python dashboard.py`
- Run individual apps: e.g., `python projects.py`, `python print_package.py`, `python job_notes.py`

## 19) Opportunities (Future Work)

- Improve modularity: separate DB/data services from UI logic; move repeated queries to a shared layer.
- Add structured logging and telemetry for reliability.
- Harden schema migrations with explicit versioning and migration scripts.
- Expand tests (at least smoke tests for major save/load flows and basic DB integrity checks).

---

This overview stays in sync with the code. For deeper details, see inline docstrings and the `updates/` logs for recent changes (e.g., template workflow, scrolling, and print package scanning).

