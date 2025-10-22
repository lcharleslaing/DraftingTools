# Update Log — 2025-10-22 — Global App Bar Navigation

Time: 2025-10-22T02:05:00Z
Author: Codex CLI Assistant

## Summary
Added a global app bar to all apps providing one-click navigation to other apps. Prevents multiple instances by focusing an already-running app window when available; otherwise launches a single new instance.

## Implementation
- `DraftingTools/app_nav.py` — `add_app_bar(root, current_app)` renders the top navigation bar with buttons.
- `DraftingTools/nav_utils.py` — app process/window management:
  - Detect existing app processes via `psutil`.
  - On Windows, bring app window to foreground via `pywin32` (title matching). If running but cannot focus, avoid launching duplicates.
  - Otherwise spawn a new process for the selected app.
- Integrated app bar into:
  - Projects (`projects.py`)
  - Product Configurations (`product_configurations.py`)
  - Print Package (`print_package.py`)
  - D365 Builder (`d365_import_formatter.py`)
  - Project Monitor (`project_monitor.py`)
  - Drawing Reviews (`drawing_reviews.py`)
  - Drafting Checklist (`drafting_items_to_look_for.py`)
  - Workflow Manager (`workflow_manager.py`)
  - Coil Verification (`coil_verification_tool.py`)
  - App Order Manager (`app_order.py`)
  - Assist Engineering (`assist_engineering.py`)

## Notes
- Window focusing uses the app window title; ensure titles remain stable.
- On non-Windows, focusing may be limited; duplicate prevention still avoids launching a second instance if a matching process is found.

