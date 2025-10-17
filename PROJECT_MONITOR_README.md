# Project File Monitor

A comprehensive project monitoring and file tracking system for the Drafting Tools suite. This application scans, documents, and monitors project folder structures to help track file changes and maintain project integrity.

## Features

### 🔍 Project Structure Scanning
- **Complete Folder Documentation**: Scans entire project directories and stores folder structure in database
- **File Metadata Tracking**: Records file sizes, creation dates, modification dates, and file hashes
- **JSON Backup**: Creates JSON backups of all project data for portability

### 📊 File Change Monitoring
- **Real-time Change Detection**: Monitors files for modifications, additions, and deletions
- **Change History**: Maintains a complete history of all file changes
- **Status Tracking**: Tracks whether changes have been acknowledged by users

### 📋 User Interface
- **Project List Panel**: Displays all projects sorted by due date (left panel)
- **File Updates Panel**: Shows file changes with status indicators (right panel)
- **Resizable Layout**: Adjustable panel widths for optimal viewing
- **Scrollable Tables**: Horizontal and vertical scrolling for large datasets

### 🔧 File Extraction Capabilities
- **Excel Files**: Extracts all sheet data, formulas, formatting, and styling
- **Word Documents**: Extracts text, formatting, tables, and document structure
- **PDF Files**: Extracts text content and page information
- **Other Files**: Basic metadata extraction for all file types

### 🚀 Project Recreation
- **Structure Replication**: Recreate complete project folder structures on other machines
- **Excel Extraction Script**: Automatically includes `excel_extract_duplicate.py` for data extraction
- **Testing Support**: Perfect for setting up test environments

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Required Packages**:
   - `openpyxl>=3.1.0` - Excel file processing
   - `python-docx>=0.8.11` - Word document processing
   - `PyPDF2>=3.0.0` - PDF file processing
   - `tkinter` - GUI framework (included with Python)

## Usage

### Starting the Application

```bash
python launch_project_monitor.py
```

Or directly:
```bash
python project_monitor.py
```

### Main Interface

#### Left Panel - Projects List
- **Job Number**: Project identifier
- **Customer**: Customer name
- **Due Date**: Project due date (sorted by this field)
- **Refresh**: Reload projects from database
- **Scan All**: Scan all projects for changes
- **Recreate Structure**: Recreate selected project structure

#### Right Panel - File Updates
- **File Name**: Name of the file
- **File Path**: Relative path within project
- **Type**: File extension
- **Created**: File creation date
- **Modified**: Last modification date
- **Status**: Change status (New File, Updated, No Changes)
- **Action**: Open file button

### Key Functions

#### 1. Scanning Projects
- Click "Scan All" to scan all projects with defined directories
- Individual project scanning happens automatically when selected
- Background monitoring checks for changes every 30 seconds

#### 2. Viewing Changes
- Select a project from the left panel
- View all file changes in the right panel
- Green text indicates new or updated files
- Double-click any file to open it

#### 3. Managing Changes
- **Refresh Updates**: Reload file changes for current project
- **Mark All Read**: Mark all changes as acknowledged
- **Export Changes**: Export change history to JSON file

#### 4. Recreating Project Structure
- Select a project from the left panel
- Click "Recreate Structure"
- Choose destination directory
- Complete folder structure will be recreated
- `excel_extract_duplicate.py` script will be included

## Database Schema

### project_structure Table
Stores complete file and folder information:
- `job_number`: Project identifier
- `file_path`: Relative path within project
- `file_name`: File name
- `file_type`: File extension
- `file_size`: File size in bytes
- `created_date`: File creation timestamp
- `modified_date`: Last modification timestamp
- `file_hash`: MD5 hash for change detection
- `is_directory`: Boolean flag for directories
- `parent_path`: Parent directory path
- `scan_date`: When this record was created/updated

### file_changes Table
Tracks all file modifications:
- `job_number`: Project identifier
- `file_path`: Relative path within project
- `change_type`: 'new', 'updated', or 'deleted'
- `old_hash`: Previous file hash
- `new_hash`: New file hash
- `change_date`: When change was detected
- `acknowledged`: Whether user has seen this change

### project_scan_history Table
Records scan operations:
- `job_number`: Project identifier
- `scan_date`: When scan was performed
- `files_scanned`: Number of files processed
- `changes_detected`: Number of changes found
- `scan_duration`: Time taken for scan

## File Extraction Script

The `excel_extract_duplicate.py` script is automatically included when recreating project structures. It provides:

### Excel File Processing
- **Complete Data Extraction**: All cell values, formulas, and formatting
- **Style Information**: Fonts, colors, borders, alignment
- **Sheet Properties**: Dimensions, formatting settings
- **Formula Preservation**: Maintains original Excel formulas

### Word Document Processing
- **Text Extraction**: All paragraph text and formatting
- **Table Processing**: Complete table structure and content
- **Style Information**: Font properties, formatting details
- **Document Structure**: Paragraphs, runs, and styling

### PDF File Processing
- **Text Extraction**: All text content from pages
- **Page Information**: Page dimensions and metadata
- **Multi-page Support**: Processes all pages in document

### Usage
```bash
python excel_extract_duplicate.py [directory_path]
```

If no directory is specified, processes current directory.

## Configuration

### Database Connection
The application uses the existing `drafting_tools.db` database. Ensure the database is properly initialized with the `DatabaseManager` class.

### Project Directories
Projects must have a `job_directory` field set in the database for scanning to work. This should point to the root folder of the project.

### Background Monitoring
- Checks for changes every 30 seconds
- Only monitors currently selected project
- Automatically updates UI when changes are detected

## Troubleshooting

### Common Issues

1. **"No project directory found"**
   - Ensure project has `job_directory` set in database
   - Verify directory path exists on filesystem

2. **"Failed to load projects"**
   - Check database connection
   - Verify `projects` table exists and has data

3. **"Could not open file"**
   - File may have been moved or deleted
   - Check file permissions
   - Verify file path is correct

4. **Import errors for file processing**
   - Install missing packages: `pip install openpyxl python-docx PyPDF2`
   - Check Python version compatibility

### Performance Considerations

- Large projects may take time to scan initially
- Background monitoring uses minimal resources
- Database operations are optimized for performance
- File hashing is done efficiently with MD5

## Integration

This application integrates with the existing Drafting Tools suite:
- Uses same database (`drafting_tools.db`)
- Follows existing project structure
- Compatible with existing project management workflow
- Can be launched from main dashboard

## Future Enhancements

- Real-time file system watching (using `watchdog` library)
- Email notifications for critical changes
- Advanced filtering and search capabilities
- Change visualization and reporting
- Integration with version control systems
- Automated backup scheduling

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Check database connectivity
4. Review error messages in status bar
