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
from .card_setup import ensure_card_installed, show_setup_instructions

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uber Ride Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Setup the card file and resources
    card_setup_success = await ensure_card_installed(hass)
    await show_setup_instructions(hass, card_setup_success)
    
    # Create API client
    from .api_client import UberAPIClient
    api_client = UberAPIClient(
        hass,
        entry.data[CONF_CLIENT_ID],
        entry.data[CONF_CLIENT_SECRET]
    )
    
    # Test connection
    connection_result = await api_client.test_connection()
    if connection_result.get("success"):
        _LOGGER.info("Uber API connection successful")
    else:
        _LOGGER.warning("Uber API connection failed: %s", connection_result.get("error"))
    
    # Store the configuration and API client
    hass.data[DOMAIN][entry.entry_id] = {
        "client_id": entry.data[CONF_CLIENT_ID],
        "client_secret": entry.data[CONF_CLIENT_SECRET],
        "entry": entry,
        "api_client": api_client,
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
    
    # Register diagnostic services
    async def handle_test_api_access(call: ServiceCall):
        """Test what API endpoints are accessible."""
        api_client = hass.data[DOMAIN][entry.entry_id].get("api_client")
        if not api_client:
            _LOGGER.error("No API client available")
            return
        
        result = await api_client.test_api_access()
        _LOGGER.info("API Access Test Result: %s", result)
        
        # Format message for notification
        message = f"## API Test Results\n\n"
        message += f"**Token Valid:** {'✅' if result['token_valid'] else '❌'}\n"
        message += f"**Time:** {result['timestamp']}\n\n"
        
        if result['errors']:
            message += "### ❌ Errors:\n"
            for error in result['errors']:
                message += f"- {error}\n"
            message += "\n"
        
        message += "### Endpoint Access:\n"
        for endpoint in result['accessible_endpoints']:
            status_emoji = "✅" if endpoint['accessible'] else "❌"
            message += f"\n{status_emoji} **{endpoint['description']}**\n"
            message += f"   Endpoint: `{endpoint['endpoint']}`\n"
            message += f"   Status: {endpoint['status']}\n"
            
            if endpoint.get('sample_data'):
                message += f"   Data: {endpoint['sample_data']}\n"
            if endpoint.get('error'):
                message += f"   Error: {endpoint['error']}\n"
        
        # Show notification
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "🔍 Uber API Diagnostic Results",
                "message": message,
                "notification_id": "uber_api_diagnostic",
            },
        )
    
    async def handle_get_ride_history(call: ServiceCall):
        """Get ride history from Uber."""
        api_client = hass.data[DOMAIN][entry.entry_id].get("api_client")
        if not api_client:
            _LOGGER.error("No API client available")
            return
        
        limit = call.data.get("limit", 5)
        result = await api_client.get_ride_history(limit)
        
        if result and result.get("success"):
            message = f"## Ride History\n\n"
            message += f"**Total Rides:** {result.get('count', 0)}\n\n"
            
            for i, ride in enumerate(result.get('rides', []), 1):
                message += f"### Ride {i}\n"
                message += f"- Status: {ride.get('status')}\n"
                message += f"- Time: {ride.get('start_time')}\n"
                message += f"- Distance: {ride.get('distance')} miles\n"
                message += f"- Duration: {ride.get('duration')} mins\n"
                message += f"- Fare: ${ride.get('total')}\n\n"
        else:
            message = f"## ❌ Failed to get ride history\n\n"
            message += f"Error: {result.get('error') if result else 'No response'}\n"
            if result and result.get('details'):
                message += f"Details: {result['details']}\n"
        
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "📜 Uber Ride History",
                "message": message,
                "notification_id": "uber_ride_history",
            },
        )
    
    async def handle_check_current_ride(call: ServiceCall):
        """Manually check for current ride."""
        api_client = hass.data[DOMAIN][entry.entry_id].get("api_client")
        if not api_client:
            _LOGGER.error("No API client available")
            return
        
        ride_data = await api_client.get_current_ride()
        
        if ride_data:
            if ride_data.get("has_ride"):
                message = f"## 🚗 Active Ride Found!\n\n"
                message += f"**Status:** {ride_data.get('status')}\n"
                message += f"**Driver:** {ride_data.get('driver_name', 'Unknown')}\n"
                message += f"**Vehicle:** {ride_data.get('vehicle_make', '')} {ride_data.get('vehicle_model', '')}\n"
                message += f"**License:** {ride_data.get('vehicle_license_plate', '')}\n"
                message += f"**ETA:** {ride_data.get('eta', '?')} minutes\n"
            else:
                message = "## No Active Ride\n\nNo ride is currently in progress."
        else:
            message = "## ❌ Failed to check ride\n\nCould not retrieve ride data from Uber API."
        
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "🔄 Current Ride Status",
                "message": message,
                "notification_id": "uber_current_ride",
            },
        )
    
    # Register all services
    hass.services.async_register(
        DOMAIN,
        "test_api_access",
        handle_test_api_access,
    )
    
    hass.services.async_register(
        DOMAIN,
        "get_ride_history", 
        handle_get_ride_history,
    )
    
    hass.services.async_register(
        DOMAIN,
        "check_current_ride",
        handle_check_current_ride,
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