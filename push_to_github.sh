#!/bin/bash

echo "========================================"
echo "Push Uber Ride Tracker to GitHub"
echo "========================================"

# Check if remote is already added
if git remote | grep -q origin; then
    echo "Remote 'origin' already exists"
else
    echo "Add your GitHub repository as remote:"
    echo "Example: https://github.com/yourusername/ha-uber-ride-tracker.git"
    read -p "Enter your GitHub repository URL: " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "No repository URL provided. Exiting."
        exit 1
    fi
    
    git remote add origin "$REPO_URL"
    echo "✅ Remote added: $REPO_URL"
fi

echo ""
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Repository pushed successfully!"
echo ""
echo "Next steps:"
echo "1. Go to your GitHub repository"
echo "2. Check that all files are uploaded"
echo "3. Share the repository URL for Home Assistant testing"
echo ""
echo "To install in Home Assistant via HACS:"
echo "1. Add your repository URL as a custom repository"
echo "2. Install 'Uber Ride Tracker'"
echo "3. Restart Home Assistant"
echo "4. Add integration with credentials:"
echo "   Client ID: gyUPRACf08NFEBoEcXTG3-Wa8U3FB-Bf"
echo "   Client Secret: wzo8V7ivmB1DRPbewGiFQtXtl27wDP9T9e3QVYWJ"