# Update Log — 2025-10-22 — Additional Notes

Time: 2025-10-22T01:15:00Z
Author: Codex CLI Assistant

## Summary
Housekeeping entry to note recent quality-of-life improvements and where user preferences are stored.

## Details
- Column width preferences are saved per user in `~/.drafting_tools/ui_prefs.json`.
  - Remove this file to reset saved widths to defaults.
- Mouse wheel scrolling is standardized across Treeviews/Canvas where present.
- Projects retains its own column width persistence; other apps use the shared utility.

## Affected Modules
- Utilities: `ui_prefs.py`, `scroll_utils.py`
- Apps updated to bind column persistence and/or wheel scrolling.

