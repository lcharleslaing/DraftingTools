# Update Log — 2025-10-22 — Template-Driven Project Workflow

Time: 2025-10-22T09:10:00Z
Author: Codex CLI Assistant

## Summary
Introduced a versioned, template‑driven Project Workflow for the Projects app. A new "Workflow Settings" editor defines the Standard workflow (steps, order, departments, groups, titles, durations). New projects are seeded from the active template; existing projects are not auto‑updated.

## User‑Visible Changes
- Projects → Workflow toolbar: new button `⚙️ Workflow Settings`.
- Projects → Workflow: new section "Standard Workflow (Template)" listing steps with:
  - Start [ ] and Completed [ ] checkboxes with timestamps (timestamps are retained if unchecked later).
  - Transfer To and Received From person pickers (populated from Drafting/Engineering names plus Production: "Larry W."). Timestamps saved on first set.
  - Due date (back‑scheduled, Monday–Friday business days) and Duration (actual if completed, else planned).
- New projects automatically get the active Standard template steps.
- Existing projects are not updated to new templates (no auto‑migration).

## Implementation
- DB (database_setup.py):
  - `workflow_templates(id, name, version, is_active, created_date)`
  - `workflow_template_steps(id, template_id, order_index, department, group_name, title, planned_duration_days)`
  - `project_workflow_steps(id, project_id, template_id, template_step_id, order_index, department, group_name, title, start_flag, start_ts, completed_flag, completed_ts, transfer_to_name, transfer_to_ts, received_from_name, received_from_ts, planned_due_date, actual_completed_date, actual_duration_days)`
  - Seeds `workflow_templates` with Standard v1 (no steps) if empty.
- Projects (projects.py):
  - Toolbar updated to include `⚙️ Workflow Settings`.
  - New section renderer: `create_template_workflow_content(...)` and event handlers for start/complete/transfer/receive.
  - People list uses Designers + Engineers + "Larry W." (Production).
  - Seeding: on first save of a new project, copies active template steps into `project_workflow_steps`.
  - Scheduling: back‑scheduled due dates computed from project due date through durations (Mon–Fri), taking actual start timestamps into account when available.

## Behavior Notes
- Versioning: Editing the Standard workflow creates a new version and activates it; prior versions remain archived and are not applied to existing projects.
- Due dates: If the next step has an actual start timestamp, the current step’s due date is that actual start date; otherwise, planned dates are used. Back‑scheduling respects Monday–Friday business days.
- Timestamps: If a checkbox is unchecked after being set, the original timestamp is preserved (for auditability).

## Next Steps
- Optional: add admin‑only guard for the settings window.
- Optional: add a manual “Apply Latest Template” action for a selected existing project (currently deferred per requirements).

