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
    
    # Create API client based on auth type
    from .api_client import UberAPIClient
    
    if entry.data.get("auth_type") == "personal_token":
        # Personal token mode - no client ID/secret needed
        api_client = UberAPIClient(
            hass,
            client_id=None,
            client_secret=None
        )
        api_client.access_token = entry.data["personal_access_token"]
        _LOGGER.info("Using personal access token for user: %s", 
                     entry.data.get("user_info", {}).get("email", "Unknown"))
    else:
        # OAuth mode
        api_client = UberAPIClient(
            hass,
            entry.data.get(CONF_CLIENT_ID),
            entry.data.get(CONF_CLIENT_SECRET)
        )
        
        # Set tokens if they were stored during setup
        if "access_token" in entry.data:
            api_client.access_token = entry.data["access_token"]
            _LOGGER.info("Using stored access token from setup")
        if "refresh_token" in entry.data:
            api_client.refresh_token = entry.data["refresh_token"]
            _LOGGER.info("Using stored refresh token from setup")
    
    # Test connection
    connection_result = await api_client.test_connection()
    if connection_result.get("success"):
        _LOGGER.info("Uber API connection successful")
    else:
        _LOGGER.warning("Uber API connection failed: %s", connection_result.get("error"))
    
    # Store the configuration and API client
    hass.data[DOMAIN][entry.entry_id] = {
        "client_id": entry.data.get(CONF_CLIENT_ID),
        "client_secret": entry.data.get(CONF_CLIENT_SECRET),
        "auth_type": entry.data.get("auth_type", "oauth"),
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
        if result.get('requires_oauth'):
            message = "## 🔐 OAuth Authorization Required\n\n"
            message += f"**Auth URL:** {result.get('auth_url')}\n\n"
            message += "### Instructions:\n"
            message += "1. Add this redirect URI to your Uber app:\n"
            message += "   `https://home.erbarraud.com/local/uber_callback.html`\n\n"
            message += "2. Visit the auth URL above\n"
            message += "3. Authorize the app with your Uber account\n"
            message += "4. You'll see a success page with your auth code\n"
            message += "5. Copy the code (there's a copy button)\n"
            message += "6. Use the `uber_ride_tracker.authorize` service with that code\n"
        else:
            message = f"## API Test Results\n\n"
            message += f"**Token Valid:** {'✅' if result['token_valid'] else '❌'}\n"
            message += f"**Time:** {result['timestamp']}\n\n"
        
        if result.get('errors'):
            message += "\n### ❌ Errors:\n"
            for error in result['errors']:
                message += f"- {error}\n"
            message += "\n"
        
        if result.get('accessible_endpoints'):
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
    
    async def handle_authorize(call: ServiceCall):
        """Handle OAuth authorization with auth code."""
        auth_code = call.data.get("auth_code")
        redirect_uri = call.data.get("redirect_uri")
        
        # If no auth code provided, check if we have a stored one
        if not auth_code:
            auth_code = hass.data[DOMAIN].get("last_auth_code")
            if not auth_code:
                _LOGGER.error("No auth code provided and no stored code found")
                return
            _LOGGER.info("Using stored auth code from callback")
        
        api_client = hass.data[DOMAIN][entry.entry_id].get("api_client")
        if not api_client:
            _LOGGER.error("No API client available")
            return
        
        result = await api_client.exchange_auth_code(auth_code, redirect_uri)
        
        if result.get("success"):
            message = "## ✅ Authorization Successful!\n\n"
            message += f"**Token obtained:** Yes\n"
            message += f"**Expires in:** {result.get('expires_in')} seconds\n"
            message += f"**Scope:** {result.get('scope')}\n\n"
            message += "You can now use the Uber Ride Tracker services!"
        else:
            message = "## ❌ Authorization Failed\n\n"
            message += f"**Error:** {result.get('error')}\n"
            if result.get('details'):
                message += f"**Details:** {result.get('details')}\n"
        
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "🔐 Uber OAuth Authorization",
                "message": message,
                "notification_id": "uber_auth_result",
            },
        )
    
    # Register all services
    hass.services.async_register(
        DOMAIN,
        "authorize",
        handle_authorize,
    )
    
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
    
    async def handle_setup_callback(call: ServiceCall):
        """Manually copy callback file to www folder."""
        from pathlib import Path
        import shutil
        
        try:
            # Get paths
            www_path = Path(hass.config.path("www"))
            integration_dir = Path(__file__).parent
            
            # Create www directory if it doesn't exist
            if not www_path.exists():
                www_path.mkdir(mode=0o755, parents=True, exist_ok=True)
                message = f"Created www directory at: {www_path}\n\n"
            else:
                message = f"www directory exists at: {www_path}\n\n"
            
            # Copy callback HTML
            callback_source = integration_dir / "www" / "uber_callback.html"
            callback_dest = www_path / "uber_callback.html"
            
            if callback_source.exists():
                shutil.copy2(str(callback_source), str(callback_dest))
                callback_dest.chmod(0o644)
                message += f"✅ Callback page copied to: {callback_dest}\n"
                message += f"Access it at: https://home.erbarraud.com/local/uber_callback.html\n\n"
            else:
                message += f"❌ Source file not found at: {callback_source}\n\n"
            
            # Also copy the card file
            card_source = integration_dir / "www" / "uber-ride-tracker-card.js"
            card_dest = www_path / "uber-ride-tracker-card.js"
            
            if card_source.exists():
                shutil.copy2(str(card_source), str(card_dest))
                card_dest.chmod(0o644)
                message += f"✅ Card file copied to: {card_dest}\n"
            else:
                message += f"⚠️ Card file not found at: {card_source}\n"
            
            # List www directory contents
            message += f"\n**Contents of {www_path}:**\n"
            for file in www_path.iterdir():
                message += f"- {file.name} ({file.stat().st_size} bytes)\n"
                
        except Exception as e:
            message = f"❌ Error: {e}"
        
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "🔧 Uber OAuth Callback Setup",
                "message": message,
                "notification_id": "uber_callback_setup",
            },
        )
    
    hass.services.async_register(
        DOMAIN,
        "setup_callback",
        handle_setup_callback,
    )
    
    _LOGGER.info(
        "Uber Ride Tracker integration setup completed. "
        "Note: OAuth authentication is required for API access. "
        "Use service 'uber_ride_tracker.test_api_access' to test API."
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