#!/bin/bash

echo "=== FULL CARD DEBUG CHECK ==="
echo ""

HA_CONFIG="/Users/erik/homeassistant"

echo "1. Card file check:"
echo "-------------------"
if [ -f "$HA_CONFIG/www/uber-ride-tracker-card.js" ]; then
    echo "✓ Card exists at: $HA_CONFIG/www/uber-ride-tracker-card.js"
    echo "  Size: $(ls -lh "$HA_CONFIG/www/uber-ride-tracker-card.js" | awk '{print $5}')"
    echo "  First line: $(head -1 "$HA_CONFIG/www/uber-ride-tracker-card.js")"
    echo "  Last line: $(tail -1 "$HA_CONFIG/www/uber-ride-tracker-card.js")"
    echo "  MD5: $(md5 -q "$HA_CONFIG/www/uber-ride-tracker-card.js" 2>/dev/null || md5sum "$HA_CONFIG/www/uber-ride-tracker-card.js" | awk '{print $1}')"
else
    echo "✗ Card NOT found!"
fi

echo ""
echo "2. Resource registration check:"
echo "-------------------------------"
if [ -f "$HA_CONFIG/.storage/lovelace_resources" ]; then
    echo "Searching for uber-ride-tracker-card in resources:"
    grep -A2 -B2 "uber-ride-tracker" "$HA_CONFIG/.storage/lovelace_resources" | head -20
else
    echo "✗ No lovelace_resources file found"
fi

echo ""
echo "3. Integration check:"
echo "--------------------"
echo "Custom components:"
ls -la "$HA_CONFIG/custom_components/" | grep uber

echo ""
echo "Config entries:"
if [ -f "$HA_CONFIG/.storage/core.config_entries" ]; then
    grep -A5 "uber_ride_tracker" "$HA_CONFIG/.storage/core.config_entries" | head -20
fi

echo ""
echo "4. Entity check:"
echo "---------------"
if [ -f "$HA_CONFIG/.storage/core.entity_registry" ]; then
    echo "Uber entities found:"
    grep "uber_ride_tracker" "$HA_CONFIG/.storage/core.entity_registry" | head -10
else
    echo "No entity registry found"
fi

echo ""
echo "5. Check if card defines itself correctly:"
echo "------------------------------------------"
grep -E "(customElements\.define|class.*extends.*HTMLElement)" "$HA_CONFIG/www/uber-ride-tracker-card.js" | head -5

echo ""
echo "6. Check for JavaScript errors in HA log:"
echo "-----------------------------------------"
if [ -f "$HA_CONFIG/home-assistant.log" ]; then
    grep -i -E "(uber|card|custom:|lovelace|javascript|error.*resource)" "$HA_CONFIG/home-assistant.log" | tail -10
fi

echo ""
echo "7. Browser test commands:"
echo "-------------------------"
echo "Open browser console (F12) and run these:"
echo ""
echo "// Check if card class exists:"
echo "console.log('Card defined:', customElements.get('uber-ride-tracker-card'));"
echo ""
echo "// Check all custom cards:"
echo "console.log('Custom cards:', window.customCards);"
echo ""
echo "// Force reload the card:"
echo "import('/local/uber-ride-tracker-card.js').then(() => console.log('Card loaded'));"
echo ""
echo "// Check for load errors:"
echo "fetch('/local/uber-ride-tracker-card.js').then(r => r.text()).then(t => console.log('Card length:', t.length));"

echo ""
echo "8. Quick fix attempt:"
echo "--------------------"
echo "Copying fresh card file..."
cp /Users/erik/ha-uber-ride-tracker/www/uber-ride-tracker-card.js "$HA_CONFIG/www/uber-ride-tracker-card.js"
echo "✓ Fresh copy made"

echo ""
echo "9. File permissions check:"
echo "-------------------------"
ls -la "$HA_CONFIG/www/uber-ride-tracker-card.js"

echo ""
echo "=== SUMMARY ==="
echo "If card still doesn't show:"
echo "1. Restart Home Assistant"
echo "2. Clear ALL browser data for your HA URL"
echo "3. Try incognito/private mode"
echo "4. Try a different browser"
echo ""
echo "Share this output for further debugging!"