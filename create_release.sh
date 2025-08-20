#!/bin/bash

echo "Creating GitHub Release for Uber Ride Tracker"
echo "============================================="

VERSION="v1.0.0"

# Create a git tag
git tag -a $VERSION -m "Initial release - Uber Ride Tracker for Home Assistant

Features:
- OAuth authentication
- Real-time ride tracking
- Driver location tracking
- Smart polling intervals
- Multiple sensor entities
- HACS compatible"

# Push the tag
git push origin $VERSION

echo ""
echo "✅ Tag $VERSION created and pushed!"
echo ""
echo "Now create a release on GitHub:"
echo "1. Go to: https://github.com/erbarraud/ha-uber-ride-tracker/releases/new"
echo "2. Choose tag: $VERSION"
echo "3. Release title: Uber Ride Tracker v1.0.0"
echo "4. Description: Initial release"
echo "5. Click 'Publish release'"
echo ""
echo "Or use GitHub CLI:"
echo "gh release create $VERSION --title 'Uber Ride Tracker v1.0.0' --notes 'Initial release with full OAuth support and real-time tracking'"