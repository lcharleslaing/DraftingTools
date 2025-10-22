# Update Log — 2025-10-22 — Default Maximized Windows

Time: 2025-10-22T01:25:00Z
Author: Codex CLI Assistant

## Summary
Ensure all primary application windows start maximized (Windows "zoomed"), while still allowing users to restore/resize via standard window controls.

## Changes
- Workflow Manager (`workflow_manager.py`): maximize on startup when launched standalone.
- Coil Verification Tool (`coil_verification_tool.py`): maximize on startup.
- App Order Manager (`app_order.py`): maximize on startup.
- Other apps already started maximized (Dashboard, Projects, Product Configurations, Print Package, Drafting Checklist, Drawing Reviews, Project Monitor, D365 Import Builder, Assist Engineering).

## Rationale
Provides a consistent, full-screen initial experience with normal Windows behavior to restore/resize using titlebar controls or dragging.

