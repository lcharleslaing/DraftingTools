# Disable Cursor's Auto-Fetch to Fix Git Permission Errors

## Steps to Disable Auto-Fetch in Cursor:

1. **Open Cursor Settings:**
   - Press `Ctrl+,` (or `Cmd+,` on Mac)
   - Or go to: File → Preferences → Settings

2. **Search for Git Auto-Fetch:**
   - In the search bar at the top, type: `git.fetch`

3. **Disable Auto-Fetch:**
   - Find "Git: Auto Fetch" setting
   - Uncheck/Disable it
   - This will stop Cursor from automatically fetching in the background

4. **Restart Cursor:**
   - Close and reopen Cursor for changes to take effect

## Alternative: Access OneDrive Settings via Windows Settings

1. Press `Windows Key + I` to open Settings
2. Go to **Accounts** → **Microsoft Account** (or **OneDrive**)
3. Look for OneDrive sync settings
4. Or go to: **Windows Settings** → **System** → **Storage** → **OneDrive**

## Note
The `.onedriveignore` file I created should help, but OneDrive may need to restart or resync to recognize it.

If the error persists after disabling auto-fetch, it's safe to ignore - it won't affect your Git operations.

