# Drafting Tools - Project Management System

A comprehensive Tkinter-based project management system for drafting tools, built with SQLite database integration and JSON export/import capabilities.

## Features

### Core Applications

1. **Dashboard** (`dashboard.py`) - Main entry point for all applications
2. **Project Management** (`projects.py`) - Manage drafting projects and track progress
3. **App Order Manager** (`app_order.py`) - Configure the display order of dashboard apps

### Database Features

- **SQLite Database** - Local database storage with automatic backup/restore
- **JSON Export/Import** - Data portability and sharing between users
- **Master Database** - Centralized backup location for team collaboration
- **Automatic Backup** - Database and JSON backup on application exit

### Project Management Features

- **Job Number Tracking** - Primary identifier for all projects
- **Assignment Management** - Track who projects are assigned to
- **Date Tracking** - Start date, completion date, and calculated duration
- **Progress Tracking** - Redline updates, OPS review, and release management
- **Status Monitoring** - Visual status indicators and progress tracking

## Installation

1. Clone or download the project files
2. Ensure Python 3.6+ is installed
3. No external dependencies required (uses only Python standard library)

## Usage

### Starting the System

1. Run the database setup (first time only):
   ```bash
   python database_setup.py
   ```

2. Launch the dashboard:
   ```bash
   python dashboard.py
   ```

### Individual Applications

- **Projects**: `python projects.py`
- **App Order Manager**: `python app_order.py`
- **Dashboard**: `python dashboard.py`

## Database Schema

### Core Tables

- **projects** - Main project information
- **designers** - Project team members
- **engineers** - Engineering team members
- **redline_updates** - Project review updates
- **ops_review** - Operations review tracking
- **peter_weck_review** - Quality control review
- **release_to_dee** - Final release tracking
- **app_order** - Dashboard app configuration

### Key Relationships

- Projects are linked to designers via `assigned_to_id`
- Redline updates are linked to both projects and engineers
- All project-related tables reference the main projects table via `project_id`

## Data Management

### Backup System

- **Automatic Backup**: Database and JSON files are backed up on application exit
- **Master Location**: All backups are stored in the `backup/` directory
- **Team Collaboration**: Import/export functionality allows data sharing between team members

### JSON Export/Import

- **Export**: All database tables are exported to `backup/master_data.json`
- **Import**: Data can be imported from the master JSON file
- **Synchronization**: Use import/export to sync data between different installations

## Project Workflow

1. **Project Creation** - Create new project with job number
2. **Assignment** - Assign to designer and set assignment date
3. **Initial Review** - Track initial redline and engineering review
4. **Updates** - Manage redline updates and engineering feedback
5. **OPS Review** - Track operations review process
6. **Quality Control** - Peter Weck review and error fixing
7. **Release** - Final release to Dee with completion tracking

## Configuration

### App Order Management

Use the App Order Manager to:
- Add new applications to the dashboard
- Reorder applications by priority
- Enable/disable applications
- Configure display settings

### Default Data

The system comes pre-configured with:
- **Designers**: Lee L., Pete W., Mike K., Rich T.
- **Engineers**: B. Pender, T. Stevenson, A. Rzonca
- **Default Apps**: projects, dashboard

## File Structure

```
DraftingTools/
├── dashboard.py          # Main dashboard application
├── projects.py           # Project management application
├── app_order.py          # App order management
├── database_setup.py     # Database initialization
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── backup/              # Backup directory
│   ├── master_drafting_tools.db
│   └── master_data.json
└── drafting_tools.db    # Local SQLite database
```

## Troubleshooting

### Common Issues

1. **Database Not Found**: Run `python database_setup.py` to initialize
2. **Import/Export Errors**: Check file permissions in the backup directory
3. **App Launch Errors**: Ensure all Python files are in the same directory

### Data Recovery

If the local database is corrupted:
1. Delete `drafting_tools.db`
2. Run `python database_setup.py` to recreate
3. Use the Import JSON function to restore data from backup

## Future Enhancements

- Additional project tracking features
- Reporting and analytics
- Integration with external systems
- Advanced search and filtering
- Custom field support

## Support

For issues or questions, check the application logs and ensure all files are properly installed.
# DraftingTools
