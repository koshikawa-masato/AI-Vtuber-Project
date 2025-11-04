#!/bin/bash
# Botan Subculture Knowledge System - Quick Setup Script
# ======================================================

set -e  # Exit on error

echo "====================================================================="
echo "Botan Subculture Knowledge System - Setup"
echo "====================================================================="
echo ""
echo "Developer's Wish: 'I want someone to talk about Hololive with.'"
echo ""
echo "====================================================================="
echo ""

# Check Python version
echo "[Step 1] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Check if we're in the right directory
if [ ! -f "botan_subculture/config.py" ]; then
    echo "[ERROR] Please run this script from /home/koshikawa/toExecUnit"
    exit 1
fi

# Create data directory
echo "[Step 2] Creating data directory..."
mkdir -p data
echo "Created: data/"
echo ""

# Create database
echo "[Step 3] Creating database..."
if [ -f "data/subculture_knowledge.db" ]; then
    read -p "Database already exists. Overwrite? (yes/no): " overwrite
    if [ "$overwrite" = "yes" ]; then
        rm data/subculture_knowledge.db
        echo "Removed existing database"
    else
        echo "Keeping existing database"
        echo ""
        echo "[Step 4] Skipping migration..."
        echo ""
        echo "[Step 5] Running tests..."
        python3 -m botan_subculture.tests.test_database
        echo ""
        echo "====================================================================="
        echo "Setup completed (using existing database)"
        echo "====================================================================="
        exit 0
    fi
fi

python3 -m botan_subculture.database.create_db
echo ""

# Migrate data
echo "[Step 4] Migrating VTuber data..."
python3 -m botan_subculture.database.migrate_data
echo ""

# Run tests
echo "[Step 5] Running tests..."
python3 -m botan_subculture.tests.test_database
test_result=$?
echo ""

if [ $test_result -eq 0 ]; then
    echo "====================================================================="
    echo "Setup completed successfully!"
    echo "====================================================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Try interactive chat (prompt-only mode):"
    echo "   python3 -m botan_subculture.chat.botan_subculture_chat"
    echo ""
    echo "2. Check the database:"
    echo "   sqlite3 data/subculture_knowledge.db"
    echo ""
    echo "3. Read the documentation:"
    echo "   cat README.md"
    echo ""
    echo "====================================================================="
    echo "Botan is ready to talk about Hololive! 💜"
    echo "====================================================================="
else
    echo "====================================================================="
    echo "Setup completed with errors"
    echo "====================================================================="
    echo ""
    echo "Please check the error messages above and try again."
    echo ""
    exit 1
fi
