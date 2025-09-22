#!/bin/bash

echo "🧹 Starting EC2 Cleanup..."

# Navigate to project directory
cd ~/neural-networks/bike_rental_prediction_fully_automated/bike_rental_prediction

# Remove all backup files
echo "Removing backup files..."
find . -name "*_backup*" -delete
find . -name "*_original*" -delete
find . -name "*.bak" -delete

# Remove test and fix scripts
echo "Removing temporary scripts..."
rm -f fix_*.sh fix_*.py
rm -f test_*.sh test_*.py  
rm -f check_*.py
rm -f remote_deploy.sh
rm -f force_trigger.sh
rm -f apply_fix.sh
rm -f complete_fix.sh
rm -f fix_integration_tests.sh
rm -f fix_root_endpoint.py
rm -f setup_venv.sh
rm -f run_local.sh
rm -f run_training.sh
rm -f run_training_simple.sh
rm -f verify*.sh verify*.py

# Remove Python cache
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Remove old training runs and logs
echo "Removing old runs and logs..."
rm -rf training_runs/
rm -rf mlruns/
rm -rf mlflow_artifacts/
rm -f *.log

# Remove model backups (keep only latest)
echo "Cleaning model directories..."
rm -rf models_backup_aug6/

# Remove empty directories
echo "Removing empty directories..."
find . -type d -empty -delete

# Keep only essential files
echo "✅ Keeping essential files:"
echo "  - src/ (source code)"
echo "  - app/ (API application)"
echo "  - data/ (dataset)"
echo "  - models/ (current models)"
echo "  - requirements.txt"
echo "  - Dockerfile"
echo "  - README.md"
echo "  - ci_test.py"
echo "  - .gitignore"

echo "✅ EC2 Cleanup complete!"
ls -la
