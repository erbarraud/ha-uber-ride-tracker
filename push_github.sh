#!/bin/bash

echo "========================================"
echo "Push Uber Ride Tracker to GitHub"
echo "========================================"

# Get repository URL from command line or prompt
if [ $# -eq 0 ]; then
    echo "Usage: ./push_github.sh <repository-url>"
    echo "Example: ./push_github.sh https://github.com/yourusername/ha-uber-ride-tracker.git"
    echo ""
    echo "Please create a repository on GitHub first:"
    echo "1. Go to https://github.com/new"
    echo "2. Name it: ha-uber-ride-tracker"
    echo "3. Don't initialize with any files"
    echo "4. Copy the repository URL"
    exit 1
fi

REPO_URL=$1

# Check if remote already exists
if git remote | grep -q origin; then
    echo "Removing existing origin..."
    git remote remove origin
fi

echo "Adding remote: $REPO_URL"
git remote add origin "$REPO_URL"

echo "Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "Repository URL: $REPO_URL"
    echo ""
    echo "📋 Your Uber App Credentials:"
    echo "Client ID: gyUPRACf08NFEBoEcXTG3-Wa8U3FB-Bf"
    echo "Client Secret: wzo8V7ivmB1DRPbewGiFQtXtl27wDP9T9e3QVYWJ"
    echo ""
    echo "🏠 To install in Home Assistant:"
    echo "1. Open HACS"
    echo "2. Three dots menu → Custom repositories"
    echo "3. Add: $REPO_URL"
    echo "4. Category: Integration"
    echo "5. Install 'Uber Ride Tracker'"
    echo "6. Restart Home Assistant"
    echo "7. Add integration with the credentials above"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "1. Repository exists on GitHub"
    echo "2. You have push access"
    echo "3. URL is correct"
fi