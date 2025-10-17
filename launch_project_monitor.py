#!/usr/bin/env python3
"""
Project File Monitor Launcher
Launches the Project File Monitor application
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from project_monitor import main
    
    if __name__ == "__main__":
        print("Starting Project File Monitor...")
        main()
        
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install openpyxl python-docx PyPDF2")
    sys.exit(1)
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)
