#!/bin/bash
# Backup Policy Coach Pro project

BACKUP_NAME="policy-coach-backup-$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup: $BACKUP_NAME"

cd ~
tar -czf "${BACKUP_NAME}.tar.gz" prompt-ops-policy-coach/
echo "✅ Backup created: ${BACKUP_NAME}.tar.gz"
ls -lh "${BACKUP_NAME}.tar.gz"
