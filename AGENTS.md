# Repository Guidelines

## Project Structure & Module Organization
- Entry points (root): `dashboard.py` (launcher), `projects.py`, `product_configurations.py`, `print_package.py`, `app_order.py`, `project_monitor.py`.
- Database and setup: `database_setup.py`, `db_utils.py`, primary `drafting_tools.db` in repo root; snapshots/exports in `backup/`.
- Support and UI helpers: `nav_utils.py`, `help_utils.py`, `ui_prefs.py`, `scroll_utils.py`.
- Assets/logs: `checklist_images/`, `logs/`, `updates/`.
- Scripts: `launch.bat`, `launch.sh`, and app-specific `*.bat`/`*.py` launchers.
- Docs: `README.md`, `CODEBASE_OVERVIEW.md`, app-specific `*.md` guides.

## Build, Test, and Development Commands
- Create venv (Windows): `python -m venv .venv && .\.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt` (psutil, pywin32, reportlab, openpyxl, PyPDF2, etc.).
- Initialize DB (first run/schema changes): `python database_setup.py`.
- Run dashboard: `python dashboard.py` (recommended entry).
- Run individual apps: e.g., `python projects.py`, `python print_package.py`.
- Ad-hoc UI/process test: `python test_exit_functionality.py`.

## Coding Style & Naming Conventions
- Python 3.8+, PEP 8, 4-space indents, trailing commas where helpful.
- Names: modules/functions/vars `snake_case`; classes `CamelCase`; constants `UPPER_SNAKE_CASE`.
- Keep Tkinter patterns consistent: prefer `ttk`, split views into `create_*` helpers, use `grid` with explicit `sticky`.
- Docstrings: triple-quoted, imperative summary first line.
- No enforced formatter; if used locally, prefer `black` (88) and `ruff` but do not reformat unrelated code.

## Testing Guidelines
- Current tests are manual/ad-hoc. Use `test_exit_functionality.py` for process cleanup behavior.
- For DB changes, re-run `python database_setup.py` and validate key flows in `projects.py` and `print_package.py`.
- Add small, script-level checks near the affected module (e.g., `python -m module_name`), and keep them deterministic.

## Commit & Pull Request Guidelines
- Commits: imperative, present tense, concise scope prefix (e.g., "DashboardApp:", "ProjectsApp:"), <= 72-char subject.
  - Example: `Refactor DashboardApp tile creation for better click targets`.
- PRs: include summary, rationale, test steps, and screenshots for UI changes. Note any schema changes/backup impacts.
- Link issues and reference affected entry points.

## Security & Configuration Tips
- Do not commit sensitive data. Treat `drafting_tools.db` as development data; snapshots live in `backup/`.
- Windows integrations (printing, pywin32) require local permissions; avoid admin-only APIs.
- Paths in settings and job directories must exist; prefer defensive checks and error dialogs.

