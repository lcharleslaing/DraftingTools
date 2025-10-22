# Update Log — 2025-10-22 — Help Windows per App/Pane

Time: 2025-10-22T02:30:00Z
Author: Codex CLI Assistant

## Summary
Added contextual Help buttons across apps and major panes. Each Help opens a modal window describing how to use the app section.

## Implementation
- `DraftingTools/help_utils.py` — `show_help()` and `add_help_button()` utilities.
- Integrated Help buttons:
  - Dashboard: general help in header.
  - Projects: Projects pane and Project Details pane.
  - Product Configurations: Projects pane and Configuration pane.
  - Print Package: Projects pane and Drawings pane.
  - Project Monitor: Projects pane and Files pane.
  - D365 Builder: Projects pane and Report tab header.
  - Drawing Reviews: Reviewed list pane.
  - Drafting Checklist: Projects pane and Master Items pane.
  - Coil Verification: Search Results pane.
  - App Order Manager: Apps list pane.
  - Assist Engineering: app help placeholder.

## Notes
- Help text can be revised/expanded as needed; content lives inline where `add_help_button()` is called.

