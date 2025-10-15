# Drafting Tools Suite – Comprehensive Guide

This is a production-focused, Tkinter-based desktop suite for Engineering/Drafting operations. It centralizes project tracking, product configuration, and drawing print-package workflows with a shared SQLite database, JSON import/export, and a launcher dashboard.

The documentation below describes everything the suite does, including small UX details, data fields, and background behaviors.

---

## 1) Applications Overview

- **Dashboard** (`dashboard.py`)
  - Full‑screen, maximized launcher showing tiles for each app with counters pulled live from the database (active projects, total configurations, existing print packages).
  - Tracks spawned child processes and can close all related windows on exit.
  - Control buttons: About, Show Running Apps, Exit Application.

- **Projects Management** (`projects.py`)
  - End‑to‑end job tracking by job number with customer info, dates, durations, workflow sections, document helpers, and autosave.
  - Sections include Initial Redline, Redline Updates (multi‑cycle), OPS Review, D365 BOM Entry, Peter Weck Review, and Release to Dee. Each section stores completion states and dates.

- **Product Configurations** (`product_configurations.py`)
  - Manages heater/tank/pump configuration data tied to an existing job number; tracks status and provides parameter, fittings, and drawing number entry UIs.

- **Print Package Management** (`print_package.py`)
  - Curate, search, open, and print drawings for a job. Supports printer selection, paper size detection/selection, conversion to PDF for DWG/IDW, and multi‑file print queues.

- **App Order Manager** (`app_order.py`)
  - Admin tool to add/reorder/activate dashboard apps; exports/imports JSON; triggers backup on close.

---

## 2) Installing & Running

Requirements: Windows, Python 3.8+ recommended.

1) Initialize the database (first run only):
```bash
python database_setup.py
```

2) Start the Dashboard (recommended):
```bash
python dashboard.py
```

Run apps directly if needed:
- Projects: `python projects.py`
- Product Configurations: `python product_configurations.py`
- Print Package Management: `python print_package.py`
- App Order Manager: `python app_order.py`

---

## 3) Database Model (SQLite)

Created/managed in `database_setup.py` and shared by all apps: `drafting_tools.db`

- `designers(id, name UNIQUE)` – default values inserted (Lee L., Pete W., Mike K., Rich T.)
- `engineers(id, name UNIQUE)` – default values (B. Pender, T. Stevenson, A. Rzonca)
- `projects`
  - `job_number UNIQUE`, `job_directory`, customer name/location (+ directory variants), designer assignment (`assigned_to_id`), dates: assignment/start/completion/due, last cover sheet date, totals (duration), `released_to_dee` string, and optional `project_engineer_id`.
- `initial_redline(project_id, engineer_id, redline_date, is_completed)`
- `redline_updates(project_id, engineer_id, update_date, update_cycle, is_completed)` – supports multiple update cycles.
- `ops_review(project_id, review_date, is_completed)`
- `d365_bom_entry(project_id, entry_date, is_completed)`
- `peter_weck_review(project_id, fixed_errors_date, is_completed)`
- `release_to_dee(project_id, release_date, missing_prints_date, d365_updates_date, other_notes, other_date, is_completed, due_date)`
- `app_order(app_name UNIQUE, display_order, is_active)` – controls dashboard layout and visibility.
- `drawings(id, job_number, drawing_path, drawing_name, drawing_type, file_extension, added_date, added_by)` – for print packages.
- `print_packages(id, job_number, package_name, created_date)`

Backups and exports:
- `backup/master_drafting_tools.db` – master DB snapshot
- `backup/master_data.json` – full JSON export of every table

---

## 4) Dashboard (UX and Behavior)

- Opens maximized; minimum window 1200×800; centered on screen.
- Tiles (Projects, Product Configurations, Print Package, Additional Tools, Database Management) show counters derived by live SQL queries.
- Hovering a tile subtly changes background/border to indicate focus.
- Clicking a tile spawns a Python process for that app and tracks it in `child_processes` for cleanup.
- “Show Running Apps” lists currently detected Python processes that launched these tools (by script name or window title on Windows). Useful for closing strays.
- “Exit Application” prompts to close all detected related processes and then quits.

---

## 5) Projects Management – Detailed Features

Primary UI areas (names reflect functions in `projects.py`):

- Project List Panel
  - Load, filter, and sort projects (by job number, customer, due date). Search box filters as you type.
  - Columns include job number, customer, due date, assignment/completion status.

- Project Details Panel
  - Job info: job number (validated), job directory, customer name/location (+ quick open buttons for each directory), due date, assignment/start/completion dates; duration auto‑calculated.
  - Designer/Engineer selectors populated from DB; dropdowns load via `load_dropdown_data`.
  - Cover Sheet button appears when prerequisites satisfied; last cover sheet date shown; reacts to recent update checks.

- Specifications Area
  - Intelligent parsing of heater design spreadsheets to auto‑populate specific specs (e.g., can size via `read_excel_can_size`, spray nozzle part number from multiple files).
  - Manual spec override inputs with context menu: Edit/Delete, plus direct file open for the design source when available.
  - Spec sections are grouped (heater specs etc.).

- Workflow Panel (scrollable, with toolbar)
  - Stages: Initial Redline, Redline Update cycles (N), OPS Review, D365 BOM Entry, Peter Weck Review, Release to Dee.
  - Each stage provides: date pickers, engineer dropdowns (where applicable), completion toggles, notes/flags, and autosave wiring.
  - A “Quick Access” strip lists common actions/documents for the current job.

- Quick Access & Document Helpers
  - Open job/customer folders (by either name or location), and search/open by approximate folder names.
  - Locate and open specific document types: KOM/OC forms, proposals, other docs, and engineering/drafting docs; utilities scan common subfolders and link them.
  - D365 helpers to create import files and transmittal notices in target `fabs_dir`.

- Persistence, Autosave, Integrity
  - Form changes trigger `auto_save` into the projects + workflow tables.
  - New/Save/Delete project flows include confirmations and validation (job number format, uniqueness, etc.).
  - Import/Export buttons serialize all tables to/from JSON (team sync, restore).

- Window/Navigation
  - Fullscreen toggle; “Open Dashboard” returns to launcher; graceful exit with backup/export on close.

---

## 6) Product Configurations – Detailed Features

- Project list, filter/search, selection loads existing job configuration status.
- Tabs for product types with a primary Heater tab in code:
  - Parameter sections: operating parameters, fittings, drawing numbers.
  - Rich form with dropdowns populated by `populate_dropdown_data` and `load_dropdown_data` (initial DB bootstrap in `init_database` and `create_dropdown_tables`).
  - Autosave wires to inputs and ensures partial data persists without explicit save.
- CRUD flows: New, Save (silent save and explicit save), Delete.
- Status update integrates back to the `projects` table to reflect whether a configuration exists for the job.
- Exports configuration payload, with optional import in future.
- Fullscreen controls and Dashboard return path.

---

## 7) Print Package Management – Detailed Features

- Panels
  - Project List: filter/search; selecting a job loads its current drawing set.
  - Drawings Panel: two lists – Current Job’s drawings and Global Search results.

- Drawing Management
  - Add from file browser or from Global Search results (including cross‑job reuse).
  - Double‑click to open; context menus provide open/print/delete per file.
  - Stores path, name, type, extension, added date/by; persisted in `drawings`.

- Printing
  - “Choose Printer” dialog stores per‑paper‑size printer preferences (and detailed orientation/paper type when using the detailed config).
  - Quantity chooser for batch printing.
  - File‑type aware printing:
    - DWG/IDW → optional conversion to PDF with AutoCAD/Inventor helpers, then print.
    - Generic files can be printed via Windows Shell verbs when supported.
  - Paper size helpers: detect from drawing metadata or select from standard sizes; maps sizes to configured printers.

- Package Operations
  - Save package snapshot; import a package and add to current job; print entire package.
  - Clear current list and re‑build quickly from stored package data.

- Utilities
  - Enumerate available printers; test prints; create synthetic PDFs for printer diagnostics.
  - Fullscreen toggle; Dashboard return.

---

## 8) App Order Manager – Detailed Features

- Grid view of configured apps (`app_order`): App Name, Display Order, Active.
- Add new app with explicit order; Update (order and Active), Delete, Move Up/Down (swap logic in SQL).
- Refresh, Export JSON, Import JSON.
- On close: triggers DB backup and JSON export.

---

## 9) Backup, Restore, and Data Portability

- Automatic backups and JSON export occur on application close in management utilities.
- Manual controls available via App Order Manager’s Export/Import.
- Master backup targets:
  - DB: `backup/master_drafting_tools.db`
  - JSON: `backup/master_data.json`
- Restore helpers exist in `database_setup.py` (copy back from master).

---

## 10) Operational Notes & Small but Important Details

- All windows are sized sensibly for 1080p and support full‑screen toggles.
- The dashboard keeps a list of spawned child processes and cleans up periodically; exit attempts to terminate any lingering app windows and, if needed, aggressively kills detected Python processes matching these tools.
- File/directory “Open” actions rely on Windows shell; ensure paths exist and permissions allow access.
- Many inputs are wired to autosave—typing or changing selection persists without explicit Save.
- Project duration is computed from start to completion date and updates automatically when either changes.
- Cover Sheet button visibility depends on project readiness checks (recent updates and required fields).

---

## 11) File Map

```
DraftingTools/
├── dashboard.py                # Full-screen launcher, process tracking, counters
├── projects.py                 # Project CRUD, workflow stages, specs parsing, docs helpers
├── product_configurations.py   # Heater/Tank/Pump configuration UI + autosave
├── print_package.py            # Drawing sets, search, PDF conversion, printing
├── app_order.py                # Dashboard tiles ordering/activation + export/import
├── database_setup.py           # Schema creation, defaults, backup/restore, JSON import/export
├── backup/
│   ├── master_drafting_tools.db
│   └── master_data.json
├── drafting_tools.db           # Local SQLite database (generated)
└── README.md                   # This guide
```

---

## 12) Quick Start

```bash
python database_setup.py   # one-time init
python dashboard.py        # launch hub
```

Troubleshooting:
- If tables are missing or DB is corrupted, delete `drafting_tools.db` and re-run `database_setup.py`, then Import JSON if you have a backup.
- Printing requires access to installed printers and, for DWG/IDW conversion, AutoCAD/Inventor where applicable.

---

## 13) Change Control / Future Ideas

- Extend configuration types beyond heaters; unify parameter dictionaries across products.
- Add report exports (CSV/PDF) for project/print‑package summaries.
- Centralize printer profiles per user and per site; cloud‑sync JSON.
- Add authentication and role‑based controls for admin tools.

---

## 14) Support

For internal use. If something fails:
1) Re-run `database_setup.py`.
2) Check the `backup/` directory and permissions.
3) Verify printers and CAD software availability for conversions.

If you need exact field or workflow logic, search the function names cited above inside each module.
