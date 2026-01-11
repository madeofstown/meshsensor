#!/bin/bash
# MeshSensor Setup Script
# Automates installation and initial configuration

set -e

echo "=========================================="
echo "MeshSensor Backend Setup"
echo "=========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if virtual environment should be created
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r new_requirements.txt

echo "✓ Dependencies installed"
echo ""

# Create database backup if it exists
if [ -f "sensorDB.json" ]; then
    echo "Backing up existing JSON database..."
    cp sensorDB.json "sensorDB.json.backup.$(date +%s)"
    echo "✓ Backup created"
fi

# Show next steps
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update config.json with your radio host and node IDs"
echo "2. Run: python main.py"
echo ""
echo "Dashboard will be available at: http://localhost:5000"
echo "API will be available at: http://localhost:5001"
echo ""
echo "For more information, see:"
echo "- BACKEND_REFACTOR.md - Overview of changes"
echo "- MIGRATION_GUIDE.md - Migration instructions"
echo "- API_DOCUMENTATION.md - API reference"
echo ""
