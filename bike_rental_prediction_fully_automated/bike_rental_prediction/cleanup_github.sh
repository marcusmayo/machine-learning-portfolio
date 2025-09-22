#!/bin/bash

echo "🧹 Cleaning GitHub Repository..."

# Remove all backup files
git rm -f *_backup* *_original* *.bak 2>/dev/null

# Remove temporary fix scripts
git rm -f fix_*.sh fix_*.py 2>/dev/null
git rm -f test_fix.py check_*.py 2>/dev/null
git rm -f remote_deploy.sh force_trigger.sh 2>/dev/null
git rm -f apply_fix.sh complete_fix.sh 2>/dev/null
git rm -f setup_venv.sh run_*.sh verify*.* 2>/dev/null

# Remove old model directories
git rm -rf models_backup_aug6/ 2>/dev/null
git rm -rf training_runs/ 2>/dev/null

# Remove log files
git rm -f *.log 2>/dev/null

# Update .gitignore to prevent future issues
cat > .gitignore << 'GITIGNORE'
# Virtual environments
venv/
env/
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.pyc

# Models and runs
*.pt
*.pkl
*.pth
*.h5
training_runs/
mlruns/
runs/

# Logs
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Backups
*_backup*
*_original*
*.bak

# Temporary scripts
fix_*.sh
fix_*.py
test_*.sh
GITIGNORE

git add .gitignore
git commit -m "Clean: Remove temporary files and update .gitignore"
git push
