#!/bin/bash
# Drafting Tools Suite Launcher
# This script activates the virtual environment, installs dependencies, and launches the dashboard

echo "========================================"
echo " Drafting Tools Suite Launcher"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -f ".venv/Scripts/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create it first with: python -m venv .venv"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[1/3] Activating virtual environment..."
source .venv/Scripts/activate

echo "[2/3] Installing/updating dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[3/3] Launching Dashboard..."
echo ""
python dashboard.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Dashboard failed to launch"
    read -p "Press Enter to exit..."
    exit 1
fi

