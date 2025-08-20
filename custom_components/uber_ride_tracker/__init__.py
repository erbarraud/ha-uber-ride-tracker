"""The Uber Ride Tracker integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uber Ride Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
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
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok