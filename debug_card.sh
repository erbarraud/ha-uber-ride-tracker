#!/bin/bash

echo "=== Uber Ride Tracker Card Debug Script ==="
echo ""

# Check where Home Assistant config is located
echo "1. Checking for Home Assistant config location..."
HA_CONFIG_PATHS=(
    "$HOME/homeassistant"
    "$HOME/.homeassistant"
    "/usr/share/hassio/homeassistant"
    "/config"
    "$HOME/config"
    "/home/homeassistant/.homeassistant"
)

HA_CONFIG=""
for path in "${HA_CONFIG_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "   ✓ Found HA config at: $path"
        HA_CONFIG="$path"
        break
    fi
done

if [ -z "$HA_CONFIG" ]; then
    echo "   ✗ Could not find Home Assistant config directory"
    echo "   Please set HA_CONFIG environment variable to your config path"
    exit 1
fi

echo ""
echo "2. Checking www folder..."
if [ -d "$HA_CONFIG/www" ]; then
    echo "   ✓ www folder exists"
    echo "   Contents:"
    ls -la "$HA_CONFIG/www/" | grep -E "\.js$"
else
    echo "   ✗ www folder does not exist"
    echo "   Creating it now..."
    mkdir -p "$HA_CONFIG/www"
    echo "   ✓ Created $HA_CONFIG/www"
fi

echo ""
echo "3. Checking for the card file..."
CARD_LOCATIONS=(
    "$HA_CONFIG/www/uber-ride-tracker-card.js"
    "$HA_CONFIG/www/community/uber_ride_tracker/uber-ride-tracker-card.js"
    "$HA_CONFIG/custom_components/uber_ride_tracker/www/uber-ride-tracker-card.js"
)

CARD_FOUND=""
for location in "${CARD_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        echo "   ✓ Found card at: $location"
        CARD_FOUND="$location"
        echo "   File size: $(ls -lh "$location" | awk '{print $5}')"
        echo "   Modified: $(ls -l "$location" | awk '{print $6, $7, $8}')"
    fi
done

if [ -z "$CARD_FOUND" ]; then
    echo "   ✗ Card file not found in any expected location"
fi

echo ""
echo "4. Checking HACS installation..."
if [ -d "$HA_CONFIG/custom_components/hacs" ]; then
    echo "   ✓ HACS is installed"
    if [ -d "$HA_CONFIG/www/community" ]; then
        echo "   ✓ HACS community folder exists"
        echo "   HACS cards:"
        ls -la "$HA_CONFIG/www/community/" 2>/dev/null | grep "^d" | awk '{print "     -", $9}'
    fi
else
    echo "   ℹ HACS not installed"
fi

echo ""
echo "5. Checking lovelace resources..."
if [ -f "$HA_CONFIG/.storage/lovelace_resources" ]; then
    echo "   ✓ Lovelace resources file exists"
    echo "   Registered resources:"
    grep -o '"url":"[^"]*"' "$HA_CONFIG/.storage/lovelace_resources" | sed 's/"url":"//g' | sed 's/"//g' | while read -r url; do
        echo "     - $url"
    done
else
    echo "   ℹ No lovelace resources file found"
fi

echo ""
echo "6. Copying card to www folder (if needed)..."
REPO_CARD="/Users/erik/ha-uber-ride-tracker/www/uber-ride-tracker-card.js"
if [ -f "$REPO_CARD" ]; then
    if [ ! -f "$HA_CONFIG/www/uber-ride-tracker-card.js" ]; then
        echo "   Copying card to $HA_CONFIG/www/"
        cp "$REPO_CARD" "$HA_CONFIG/www/"
        echo "   ✓ Card copied successfully"
    else
        echo "   ℹ Card already exists in www folder"
    fi
else
    echo "   ✗ Source card file not found at $REPO_CARD"
fi

echo ""
echo "7. Checking Home Assistant logs for errors..."
if [ -f "$HA_CONFIG/home-assistant.log" ]; then
    echo "   Recent errors related to uber or card:"
    grep -i -E "(uber|card|custom|lovelace)" "$HA_CONFIG/home-assistant.log" | tail -5
else
    echo "   ℹ Log file not found"
fi

echo ""
echo "=== Summary ==="
echo ""
if [ -f "$HA_CONFIG/www/uber-ride-tracker-card.js" ]; then
    echo "✅ Card is installed at: $HA_CONFIG/www/uber-ride-tracker-card.js"
    echo ""
    echo "Next steps:"
    echo "1. Go to Settings → Dashboards → Resources"
    echo "2. Add Resource with URL: /local/uber-ride-tracker-card.js"
    echo "3. Resource type: JavaScript Module"
    echo "4. Clear browser cache (Ctrl+F5)"
    echo "5. Add card with type: custom:uber-ride-tracker-card"
else
    echo "❌ Card needs to be installed"
    echo ""
    echo "Run this to install:"
    echo "cp /Users/erik/ha-uber-ride-tracker/www/uber-ride-tracker-card.js $HA_CONFIG/www/"
fi

echo ""
echo "=== Browser Console Check ==="
echo "Open browser DevTools (F12) and run:"
echo "customElements.get('uber-ride-tracker-card')"
echo "If it returns undefined, the card isn't loaded."