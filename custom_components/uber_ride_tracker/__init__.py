"""The Uber Ride Tracker integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.components.lovelace import async_register_resource
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)
from .migrations import async_migrate_entry, CURRENT_CONFIG_VERSION

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.UPDATE]

LOVELACE_CARD_URL = "/hacsfiles/uber_ride_tracker/uber-ride-tracker-card.js"
LOVELACE_CARD_TYPE = "module"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uber Ride Tracker from a config entry."""
    # Handle migration if needed
    if entry.version < CURRENT_CONFIG_VERSION:
        if not await async_migrate_entry(hass, entry):
            _LOGGER.error("Migration failed for %s", entry.entry_id)
            return False
    
    hass.data.setdefault(DOMAIN, {})
    
    # Auto-register the Lovelace card resource
    await _register_lovelace_card(hass)
    
    # Store the basic configuration
    # OAuth will need to be implemented with a proper flow
    hass.data[DOMAIN][entry.entry_id] = {
        "client_id": entry.data[CONF_CLIENT_ID],
        "client_secret": entry.data[CONF_CLIENT_SECRET],
        "entry": entry,
        # Mock coordinator data for now
        "coordinator": None,
    }
    
    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Uber Technologies Inc.",
        model="Ride Tracker",
        name="Uber Ride Tracker",
        sw_version="1.0.0",
    )
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register test service
    async def handle_test_api(call: ServiceCall):
        """Handle the test API service call."""
        from .test_api_connection import test_uber_api_connection
        
        result = await test_uber_api_connection()
        _LOGGER.info("API Test Result: %s", result)
        
        # Fire event with results
        hass.bus.async_fire(f"{DOMAIN}_api_test_result", result)
        
        # Show notification
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Uber API Test Result",
                "message": f"Check logs for details. Auth URL: {result.get('auth_url', 'N/A')}",
                "notification_id": "uber_api_test",
            },
        )
    
    hass.services.async_register(
        DOMAIN,
        "test_api_connection",
        handle_test_api,
    )
    
    _LOGGER.info(
        "Uber Ride Tracker integration setup completed. "
        "Note: OAuth authentication is required for API access. "
        "Use service 'uber_ride_tracker.test_api_connection' to test API."
    )
    
    # Show card setup notification
    await _show_card_setup_notification(hass, entry.entry_id)
    
    return True


async def _register_lovelace_card(hass: HomeAssistant) -> None:
    """Register the custom Lovelace card resource."""
    # Check if already registered
    resources = hass.data.get("lovelace", {}).get("resources", None)
    if resources:
        for resource in resources.async_items():
            if LOVELACE_CARD_URL in resource.get("url", ""):
                _LOGGER.debug("Lovelace card already registered")
                return
    
    try:
        # Try to register the resource
        await async_register_resource(
            hass,
            url=LOVELACE_CARD_URL,
            resource_type=LOVELACE_CARD_TYPE
        )
        _LOGGER.info("Successfully registered Uber Ride Tracker card resource")
    except Exception as e:
        _LOGGER.debug("Could not auto-register card resource: %s", e)
        # Fall back to manual registration instructions


async def _show_card_setup_notification(hass: HomeAssistant, entry_id: str) -> None:
    """Show notification about how to add the card to dashboard."""
    message = """
## 🎉 Uber Ride Tracker is Ready!

### Quick Add to Dashboard:

1. **Edit any dashboard** (click pencil icon)
2. Click **"+ Add Card"**
3. Search for **"Uber Ride Tracker"**
4. Click to add!

### Manual Add (YAML):
```yaml
type: custom:uber-ride-tracker-card
entity: sensor.uber_ride_tracker_ride_status
```

### Features:
- 🎨 Apple Live Activity design
- 📍 Real-time ride tracking
- 👤 Driver info & photo
- 📊 Trip progress bar
- 📱 Mobile optimized

[View More Examples](https://github.com/yourusername/ha-uber-ride-tracker#dashboard-cards)
"""
    
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": "✅ Add Uber Tracker Card to Dashboard",
            "message": message,
            "notification_id": f"{DOMAIN}_card_setup_{entry_id}",
        },
        blocking=False
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok