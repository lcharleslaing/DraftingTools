#!/usr/bin/env python3
"""
Launch script for Drawing Reviews Application
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from drawing_reviews import main
    main()
except Exception as e:
    print(f"Error launching Drawing Reviews: {e}")
    input("Press Enter to exit...")
