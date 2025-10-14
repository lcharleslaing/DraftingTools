# Project Backup Restoration Instructions

## Overview
This guide will help you restore your project backup from the work PC to your home PC. The backup contains all 8 projects with their complete directory structures and files.

## What's Included in the Backup
- **8 Complete Projects** with all files and folders
- **Alias Mapping File** (`ALIAS_MAPPING.txt`) for path translation
- **Same directory structure** as your F:/ drive at work
- **All project data** including drawings, documents, and subfolders

## Prerequisites
- Python installed on your home PC
- The `ProjectBackup` folder copied to your home PC
- The restoration script (`restore_projects.py`)

## Step-by-Step Restoration Process

### Step 1: Copy Files to Home PC
1. Copy the entire `ProjectBackup` folder from your work PC to your home PC
2. Copy the `restore_projects.py` script to your home PC
3. Place both in the same directory (e.g., `C:\DraftingTools\`)

### Step 2: Choose Your Base Path
Decide where you want to restore the projects on your home PC. Examples:
- `C:\Projects\` (recommended)
- `D:\Work\Projects\`
- `C:\Users\[YourName]\Documents\Projects\`

### Step 3: Run the Restoration Script
Open Command Prompt or PowerShell and navigate to the folder containing the backup:

```cmd
cd C:\DraftingTools
python restore_projects.py C:\Projects
```

**Replace `C:\Projects` with your chosen base path.**

### Step 4: Update Database Paths
After restoration, update the database to point to the new paths:

```cmd
python update_database_paths.py C:\Projects
```

**Replace `C:\Projects` with your chosen base path.**

### Step 5: Verify the Restoration
After running both scripts, you should see:
- A new directory structure under your chosen base path
- All 8 project folders with complete contents
- Database paths updated to new locations
- Drafting tools ready to use

## Expected Directory Structure After Restoration

```
C:\Projects\  (or your chosen path)
├── Whitewater Processing\West Harrison, IN\35042\
├── Geneva Rock\Logan, UT\35140\
├── Sunroc\St George, UT\35154\
├── Plymate Uniform\Shelbyville, IN\35256\
├── McCurdy's Laundry\Red Wing, MN\35332\
├── Pinty's Delicious Foods\Oakville, ON\35359\
├── Brakebush Brothers\Hartwell, GA\35371\
└── Ozinga Concrete Products, Inc\Plymouth, IN\35354\
```

## Updating Database Paths (If Needed)

If you plan to use the drafting tools applications at home, you may need to update the database paths:

### Option 1: Update Database Paths
1. Open the database file (`drafting_tools.db`)
2. Update the `job_directory` field for each project to reflect the new paths
3. Example: Change `F:/Ozinga Concrete Products, Inc/Plymouth, IN/35354` to `C:/Projects/Ozinga Concrete Products, Inc/Plymouth, IN/35354`

### Option 2: Use Path Mapping
The `ALIAS_MAPPING.txt` file contains the original and new paths for easy reference.

## Troubleshooting

### Common Issues and Solutions

#### 1. "Python not found" Error
- Install Python from [python.org](https://python.org)
- Make sure Python is added to your system PATH
- Try using `py` instead of `python` in the command

#### 2. Permission Denied Error
- Run Command Prompt as Administrator
- Check that you have write permissions to the target directory

#### 3. Path Too Long Error
- Use a shorter base path (e.g., `C:\P\` instead of `C:\Projects\`)
- Enable long path support in Windows 10/11

#### 4. Missing Files
- Verify the `ProjectBackup` folder was copied completely
- Check that all subfolders and files are present
- Re-copy if necessary

## File Structure Details

Each project contains the following standard folders:
- `1. Sales\` - Sales documents, proposals, orders
- `2. Accounting\` - Financial documents, invoices, PO's
- `3. Engineering\` - Design files, calculations, releases
- `4. Drafting\` - CAD files, drawings, packages
- `5. Purchasing\` - Purchase orders, vendor quotes
- `6. Manufacturing\` - Production documents, QA
- `7. Factory Acceptance Test\` - FAT documentation
- `8. Service\` - Service and startup records
- `9. Warranty Form\` - Warranty documentation
- `Status Reports\` - Project status reports

## Backup Information

- **Backup Created:** October 10, 2025, 4:45 PM
- **Total Projects:** 8
- **Total Size:** ~700 MB
- **Source Drive:** F:/ (Work PC)
- **Backup Location:** ./ProjectBackup

## Notes

- One file was skipped during backup due to being locked by Inventor: `894-01-392.iam.dwf`
- All other files were successfully backed up
- The restoration maintains the exact same folder structure as the original
- File permissions and timestamps are preserved where possible

## Support

If you encounter any issues during restoration:
1. Check the error message carefully
2. Verify all files were copied correctly
3. Ensure Python is properly installed
4. Try running as Administrator if permission issues occur

## Success Confirmation

After successful restoration, you should have:
- ✅ All 8 project directories
- ✅ Complete file structure preserved
- ✅ All documents and drawings accessible
- ✅ Ready to work on projects at home

The restoration is complete when you can navigate to any project folder and see all the expected subfolders and files.
---
---
---
Actually, it's not as big as it looks! Let me show you how simple it really is:

## **The Reality - It's Just 2 Commands:**

### **Step 1: Copy the folder**
```cmd
# Just copy the ProjectBackup folder to your home PC
# (This is just a regular Windows copy operation)
```

### **Step 2: Run one command**
```cmd
python restore_projects.py C:\Projects
```

**That's it!** The script does all the heavy lifting automatically.

## **What the Script Actually Does:**
- Reads the `ALIAS_MAPPING.txt` file
- Creates the directory structure
- Copies all files to the new location
- Updates paths automatically

## **The "Big Job" is Just Documentation:**
The markdown file I created is comprehensive because I wanted to cover:
- Troubleshooting (in case something goes wrong)
- What to expect (so you know it worked)
- Background info (so you understand what's happening)

## **Realistic Timeline:**
- **Copy files:** 5-10 minutes (depending on your connection)
- **Run script:** 30 seconds
- **Total time:** Under 15 minutes

The restoration script is designed to be **one-click simple** - you literally just run one command and it handles everything else automatically! 

Would you like me to create a simpler "Quick Start" version with just the essential steps?