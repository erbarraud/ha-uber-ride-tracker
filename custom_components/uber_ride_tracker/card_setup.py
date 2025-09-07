"""Card setup utilities for Uber Ride Tracker."""
import json
import logging
from pathlib import Path
from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.util import yaml

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "uber-ride-tracker-card.js"
CARD_URL = f"/local/{CARD_FILENAME}"


async def ensure_card_installed(hass: HomeAssistant) -> bool:
    """Ensure the card is installed and registered."""
    success = True
    
    # Step 1: Copy card file to www folder
    if not await copy_card_to_www(hass):
        success = False
    
    # Step 2: Register as lovelace resource
    if not await register_lovelace_resource(hass):
        _LOGGER.warning("Could not auto-register resource, manual registration needed")
        # Don't fail the whole setup for this
    
    # Step 3: Verify installation
    if await verify_card_installation(hass):
        _LOGGER.info("Card installation verified successfully")
    else:
        _LOGGER.warning("Card installation could not be verified")
    
    return success


async def copy_card_to_www(hass: HomeAssistant) -> bool:
    """Copy the card file to www folder."""
    try:
        # Get paths
        www_path = Path(hass.config.path("www"))
        card_dest = www_path / CARD_FILENAME
        
        # Path to the card in the integration
        integration_dir = Path(__file__).parent
        card_source = integration_dir / "www" / CARD_FILENAME
        
        # Verify source exists
        if not card_source.exists():
            _LOGGER.error("Card source file not found at %s", card_source)
            return False
        
        # Create www directory if it doesn't exist
        if not www_path.exists():
            _LOGGER.info("Creating www directory at %s", www_path)
            www_path.mkdir(mode=0o755, parents=True, exist_ok=True)
        
        # Copy the card file
        import shutil
        shutil.copy2(str(card_source), str(card_dest))
        _LOGGER.info("Card copied to %s", card_dest)
        
        # Set proper permissions
        card_dest.chmod(0o644)
        
        return True
        
    except Exception as e:
        _LOGGER.error("Failed to copy card file: %s", e)
        return False


async def register_lovelace_resource(hass: HomeAssistant) -> bool:
    """Register the card as a lovelace resource."""
    try:
        # Path to lovelace resources storage
        resources_path = Path(hass.config.path(".storage/lovelace_resources"))
        
        # Load existing resources or create new
        if resources_path.exists():
            with open(resources_path, "r") as f:
                data = json.load(f)
        else:
            data = {
                "version": 1,
                "minor_version": 1,
                "key": "lovelace_resources",
                "data": {
                    "resources": []
                }
            }
        
        # Check if already registered
        resources = data.get("data", {}).get("resources", [])
        for resource in resources:
            if resource.get("url") == CARD_URL:
                _LOGGER.debug("Card already registered as resource")
                return True
        
        # Add new resource
        new_resource = {
            "id": f"uber_ride_tracker_card_{len(resources)}",
            "url": CARD_URL,
            "type": "module"
        }
        resources.append(new_resource)
        
        # Save updated resources
        data["data"]["resources"] = resources
        
        # Write back to file
        resources_path.parent.mkdir(parents=True, exist_ok=True)
        with open(resources_path, "w") as f:
            json.dump(data, f, indent=2)
        
        _LOGGER.info("Card registered as lovelace resource")
        return True
        
    except Exception as e:
        _LOGGER.error("Failed to register lovelace resource: %s", e)
        return False


async def verify_card_installation(hass: HomeAssistant) -> bool:
    """Verify the card is properly installed."""
    try:
        # Check if file exists
        www_path = Path(hass.config.path("www"))
        card_path = www_path / CARD_FILENAME
        
        if not card_path.exists():
            _LOGGER.error("Card file not found at %s", card_path)
            return False
        
        # Check file size (should be around 13KB)
        size = card_path.stat().st_size
        if size < 1000:
            _LOGGER.error("Card file seems too small: %d bytes", size)
            return False
        
        # Check if it contains the custom element definition
        content = card_path.read_text()
        if "customElements.define('uber-ride-tracker-card'" not in content:
            _LOGGER.error("Card file doesn't contain proper element definition")
            return False
        
        _LOGGER.info("Card installation verified: %s (%d bytes)", card_path, size)
        return True
        
    except Exception as e:
        _LOGGER.error("Failed to verify card installation: %s", e)
        return False


async def show_setup_instructions(hass: HomeAssistant, success: bool) -> None:
    """Show setup instructions to the user."""
    if success:
        message = """
## ✅ Uber Ride Tracker Ready!

The integration and custom card have been installed successfully.

### To add the card to your dashboard:

1. **Clear browser cache** (Ctrl+F5 or Cmd+Shift+R)
2. **Edit any dashboard**
3. **Add Card** → Search for "**Uber**"
4. Or add manually:

```yaml
type: custom:uber-ride-tracker-card
entity: sensor.uber_ride_tracker_ride_status
```

### Troubleshooting:
- If card doesn't appear, try incognito/private mode
- Restart Home Assistant if needed
- Check browser console for errors (F12)
"""
    else:
        message = """
## ⚠️ Uber Ride Tracker - Manual Setup Needed

The integration is installed but the card needs manual setup:

### Manual card installation:

1. **Add as Lovelace Resource:**
   - Go to Settings → Dashboards → Resources
   - Add Resource: `/local/uber-ride-tracker-card.js`
   - Type: JavaScript Module

2. **Clear browser cache** (Ctrl+F5)

3. **Add the card:**
```yaml
type: custom:uber-ride-tracker-card
entity: sensor.uber_ride_tracker_ride_status
```
"""
    
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": "🚗 Uber Ride Tracker Setup",
            "message": message,
            "notification_id": "uber_ride_tracker_setup",
        },
        blocking=False
    )