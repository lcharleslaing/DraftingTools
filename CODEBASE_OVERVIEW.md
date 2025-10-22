# Drafting Tools Suite – Codebase Overview

This document provides a concise, code-grounded overview of the Drafting Tools suite: what it does, how the modules fit together, the data model, and the key strengths and weaknesses. File paths reference the workspace root.

## What It Is

- Windows-first, Tkinter-based desktop suite for engineering/drafting operations centered on a shared SQLite database.
- Major apps: Dashboard launcher, Project Management, Product Configurations, Print Package Management, D365 Import Builder, Workflow Manager, and a Project File Monitor.
- Database schema initialization/migrations and backup/restore utilities included.

## Core Apps

### Dashboard and Settings
- `DraftingTools/dashboard.py`
  - Full-screen dashboard launcher. Shows live counters pulled from the DB (active projects, configurations, print packages).
  - Spawns child processes for apps and can clean them up on exit.
  - Provides Settings popup and displays current user/department.
- `DraftingTools/settings.py`
  - Settings storage and UI: users, departments, app_settings, and admin session tracking.
  - Admin password stored as SHA-256 hash; admin sessions last 8 hours.

### Projects Management
- `DraftingTools/projects.py`
  - End-to-end job tracking with sections for Initial Redline, multi-cycle Redline Updates, OPS Review, D365 BOM Entry, Peter Weck Review, and Release to Dee.
  - Project list with search/sort, details panel, workflow panel, and quick-access actions to open folders/documents.
  - Excel-assisted spec extraction for heater designs with override/edit/delete via context menus.
  - Autosave to DB; per-user UI preferences persisted to `~/.drafting_tools/ui_prefs.json`.
  - Exports formatted Job Notes to Excel (using `openpyxl`).

### Product Configurations
- `DraftingTools/product_configurations.py`
  - Manages configuration data for Heater/Tank/Pump tied to projects; many dropdown table sources and autosave.
  - Filters projects, optionally hides completed; anchors to `projects` table.

### Print Package Management
- `DraftingTools/print_package.py`
  - Curate and manage drawings per job; global search across drawings table.
  - Toggles printed state; prints using Windows Shell/`pywin32` (`win32api.ShellExecute`) and falls back to `cmd /c print`.
  - Opens DWG in AutoCAD and IDW in Inventor for manual printing.
  - Basic printer configuration table plus package export/import (JSON).

### Print Package Workflow
- `DraftingTools/print_package_workflow.py`
  - Workflow engine with 8 stages. Tracks status, reviewer/department, timestamps; handles copying files from one stage folder to the next under `…/PP-Print Packages/` within a job folder.
- `DraftingTools/workflow_manager.py`
  - UI to visualize workflow stages, complete stages with notes, advance to next stage(s), open current stage folder, and filter active reviews by department.

### D365 Import Builder
- `DraftingTools/d365_import_formatter.py`
  - Tkinter app to generate D365 BOM import rows for heaters/tanks/pumps.
  - Lists active projects from `drafting_tools.db` and stores its own data in `d365_builder.db`.
  - Optionally seeds defaults from `DraftingTools/D365 IMPORT.json`.

### Project File Monitor
- `DraftingTools/project_monitor.py`
  - Scans project directories, tracks file changes (new/updated/deleted), logs to `DraftingTools/logs/`, and shows unread change counts.
  - Background monitoring thread; utilities to scan selected/all, clean duplicates, clear false positives, and mark projects complete.

## Data Model (SQLite)

- Initialized and evolved in `DraftingTools/database_setup.py` using `CREATE TABLE IF NOT EXISTS` plus guarded `ALTER TABLE` adds.
- Tables (high level):
  - Core: `designers`, `engineers`, `projects` (many columns for directories, dates, people, due dates, etc.), `app_order`.
  - Workflow: `initial_redline`, `redline_updates` (multi-cycle), `ops_review`, `d365_bom_entry`, `peter_weck_review`, `release_to_dee`.
  - Print packages: `drawings`, `print_packages`, `print_package_reviews`, `print_package_files` (per-stage paths), `print_package_workflow`.
  - D365: `d365_import_configs`, `d365_part_numbers`, `d365_import_params`.
  - Settings (created by `settings.py`): `users`, `departments`, `app_settings`, `admin_sessions`.
- Backup/restore/export:
  - DB copy to `DraftingTools/backup/master_drafting_tools.db`.
  - Full JSON export/import at `DraftingTools/backup/master_data.json`.

## Cross-Cutting Behaviors

- Processes: Dashboard launches child Python scripts and can terminate/kill them on exit.
- Windows-first: uses `os.startfile`, `win32api.ShellExecute`, `.bat` launchers; print flows assume Windows.
- Requirements in `DraftingTools/requirements.txt`: `psutil`, `pywin32`, `reportlab`, `python-docx`, `openpyxl`, `PyPDF2`.

## Strong Points

- Cohesive suite backed by a single database; consistent counters and shared state across apps.
- Practical coverage of drafting operations: project lifecycle, print packages, staged workflows, configurations, and D365 item generation.
- Sensible UX: full-screen/resizable UIs, search/sort filters, quick file access, notes export, per-user UI prefs.
- Operational utilities: DB/JSON backup and restore; Project Monitor with logs and cleanup tools.
- Settings and roles: users/departments with admin session gating sensitive actions in the UI.

## Weak Points

- Platform coupling: heavy reliance on Windows APIs; poor portability to macOS/Linux without guards and alternate backends.
- Maintainability: very large modules mix UI, DB, and business logic; limited unit-testability; many broad `except` blocks mask errors.
- Data modeling/performance: few explicit indexes; wide `print_package_files` table with `stage_0_path…stage_7_path` columns; potential scale issues as rows grow.
- Concurrency: background scanning plus frequent SQLite access without explicit WAL/locking strategy; risk of occasional locks.
- Security: admin password uses unsalted SHA-256 in `app_settings`; no per-user desktop auth.
- Logging/error handling: reliance on `print` and silent failure in places; inconsistent feedback to the user.
- Professional polish: a few leftover placeholders/comments (e.g., commented “SHIT BRICKS SIDEWAYS”) reduce professionalism.

## Recommended Improvements

- Architecture: extract shared DB helpers (context-managed connections, indexes, error handling) and shared UI widgets; split monolith scripts into modules.
- Reliability: add structured logging, replace generic `except:` blocks with targeted exceptions; improve user-visible error messages.
- Performance: add indexes for frequent filters/joins (`job_number`, `project_id`, `review_id`, `stage`); consider enabling WAL.
- Data design: normalize workflow file storage (map of file-to-stage) instead of many `stage_X_path` columns; simplifies queries and supports >8 stages.
- Platform handling: wrap Windows-only behaviors behind adapters; provide no-op or alternative flows on non-Windows.
- Security: switch to salted password hashing (e.g., `bcrypt`) for admin; consider per-user authentication and roles if needed.

## File-by-File Highlights

- `DraftingTools/dashboard.py` — Launcher with live counters and child-process management; opens Settings.
- `DraftingTools/settings.py` — Settings storage (users, departments, app_settings, admin sessions) and full settings UI.
- `DraftingTools/database_setup.py` — Creates/migrates schema; backups and JSON export/import helpers.
- `DraftingTools/projects.py` — Projects CRUD; workflow panels; spec extraction from Excel; quick-access actions; notes to Excel.
- `DraftingTools/product_configurations.py` — Heater/Tank/Pump configuration UI and tables; synced with projects.
- `DraftingTools/print_package.py` — Drawing management and printing; global search; package import/export; printer config.
- `DraftingTools/print_package_workflow.py` — Workflow engine for 8-stage review; file propagation across stage folders.
- `DraftingTools/workflow_manager.py` — Workflow UI visualization; complete/advance stages; open stage folder; filter by department.
- `DraftingTools/d365_import_formatter.py` — D365 item generator and UI; reads active projects; stores to `d365_builder.db`; optional seed from JSON.
- `DraftingTools/project_monitor.py` — Project file scanning/monitoring; unread change counts; logs; cleanup utilities.
- Utilities and scripts:
  - `DraftingTools/date_picker.py`, `DraftingTools/directory_picker.py` — UI helpers.
  - `DraftingTools/backup_*.py`, `DraftingTools/restore_projects.py`, `DraftingTools/retry_failed_backup.py` — backup/restore and reliability tools.
  - `DraftingTools/print_package_workflow.py` — workflow engine used by the Workflow Manager.
  - Launchers: `DraftingTools/launch*.bat` and `.py` convenience scripts.

## Environment & Setup

- Python 3.8+ on Windows recommended.
- Initialize the DB once: `python DraftingTools/database_setup.py`
- Launch dashboard: `python DraftingTools/dashboard.py`
- Install dependencies: `pip install -r DraftingTools/requirements.txt`

---

If you’d like, this document can be extended with architectural diagrams, DB ERD, or per-table field definitions derived directly from `database_setup.py`.

