"""The Uber Ride Tracker integration."""
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .api import UberAPI, UberAPIError, UberAuthenticationError
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    SERVICE_GET_RIDE_HISTORY,
    SERVICE_REFRESH_STATUS,
)
from .coordinator import UberRideCoordinator
from .oauth import UberOAuthManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uber Ride Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create OAuth manager
    oauth_manager = UberOAuthManager(
        hass,
        entry.data[CONF_CLIENT_ID],
        entry.data[CONF_CLIENT_SECRET],
        entry.data.get("token", {}),
    )

    # Create API client
    api = UberAPI(hass, oauth_manager)

    # Test the connection
    try:
        if not await api.async_test_connection():
            raise ConfigEntryNotReady("Unable to connect to Uber API")
    except UberAuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except UberAPIError as err:
        _LOGGER.error("Failed to connect to Uber API: %s", err)
        raise ConfigEntryNotReady(f"Error connecting to Uber API: {err}") from err

    # Create coordinator
    coordinator = UberRideCoordinator(hass, api, entry.entry_id)

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "oauth_manager": oauth_manager,
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

    # Register services
    await async_register_services(hass, coordinator)

    # Register update listener
    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Unregister services if no more entries
        if not hass.data[DOMAIN]:
            await async_unregister_services(hass)

    return unload_ok


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update a config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_register_services(
    hass: HomeAssistant, coordinator: UberRideCoordinator
) -> None:
    """Register services for the integration."""
    
    async def handle_refresh_status(call: Any) -> None:
        """Handle the refresh status service call."""
        await coordinator.async_refresh_status()

    async def handle_get_ride_history(call: Any) -> None:
        """Handle the get ride history service call."""
        limit = call.data.get("limit", 10)
        history = await coordinator.async_get_ride_history(limit)
        
        # Fire an event with the history data
        hass.bus.async_fire(
            f"{DOMAIN}_ride_history",
            {"history": history, "count": len(history)},
        )

    # Check if services are already registered
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_STATUS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_STATUS,
            handle_refresh_status,
            schema=None,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_GET_RIDE_HISTORY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_GET_RIDE_HISTORY,
            handle_get_ride_history,
            schema={"limit": int},
        )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister services for the integration."""
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_STATUS)
    hass.services.async_remove(DOMAIN, SERVICE_GET_RIDE_HISTORY)