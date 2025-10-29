# Fix Git Permission Errors with OneDrive

## Problem
The `.git/FETCH_HEAD` permission denied error is caused by OneDrive trying to sync the `.git` folder, which creates file locks that conflict with Git operations.

## Solution: Exclude .git from OneDrive Sync

### Method 1: OneDrive Settings (Recommended)
1. Right-click the OneDrive icon in your system tray
2. Click "Settings"
3. Go to "Sync and backup" → "Advanced settings"
4. Click "Choose folders" under "Files On-Demand"
5. In your repo folder (DraftingTools), uncheck the `.git` folder
6. Click "OK"

### Method 2: Use .onedriveignore file
Create a `.onedriveignore` file in your repo root with:
```
.git/
.git/**
```

### Method 3: Move .git folder temporarily (if sync persists)
This is a workaround - not recommended for long-term:
```powershell
# Backup .git folder location
# Then pause OneDrive temporarily
```

## Alternative: Disable Cursor's Auto-Fetch
1. Open Cursor Settings (Ctrl+,)
2. Search for "git.fetch"
3. Disable "Git: Auto Fetch"
4. Restart Cursor

## Note
Git repositories in OneDrive can cause sync conflicts. Consider:
- Moving repo outside OneDrive
- Using a cloud Git service (GitHub, GitLab) instead of OneDrive for version control
- Using OneDrive only for non-Git projects

