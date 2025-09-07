"""Update coordinator for Uber Ride Tracker integration."""
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER, NAME

_LOGGER = logging.getLogger(__name__)

GITHUB_RELEASE_URL = "https://api.github.com/repos/yourusername/ha-uber-ride-tracker/releases/latest"
UPDATE_CHECK_INTERVAL = timedelta(hours=12)


class UberRideTrackerUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to check for updates."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{NAME} Update Checker",
            update_interval=UPDATE_CHECK_INTERVAL,
        )
        self.session = aiohttp.ClientSession()

    async def _async_update_data(self) -> Dict[str, Any]:
        """Check for updates from GitHub."""
        try:
            async with self.session.get(GITHUB_RELEASE_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "latest_version": data.get("tag_name", "").lstrip("v"),
                        "release_url": data.get("html_url", ""),
                        "release_notes": data.get("body", ""),
                        "published_at": data.get("published_at", ""),
                    }
                else:
                    raise UpdateFailed(f"GitHub API returned {response.status}")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching update data: {err}")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uber Ride Tracker update platform."""
    coordinator = UberRideTrackerUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities(
        [UberRideTrackerUpdate(coordinator, config_entry)],
        True,
    )


class UberRideTrackerUpdate(UpdateEntity):
    """Representation of an Uber Ride Tracker update entity."""

    _attr_has_entity_name = True
    _attr_name = "Update"
    _attr_supported_features = (
        UpdateEntityFeature.INSTALL
        | UpdateEntityFeature.RELEASE_NOTES
        | UpdateEntityFeature.PROGRESS
    )

    def __init__(
        self,
        coordinator: UberRideTrackerUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the update entity."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_update"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": NAME,
            "manufacturer": MANUFACTURER,
        }
        
        # Get current version from manifest
        self._current_version = self._get_current_version()
        self._attr_installed_version = self._current_version

    def _get_current_version(self) -> str:
        """Get the current installed version from manifest."""
        import json
        from pathlib import Path
        
        manifest_path = Path(__file__).parent / "manifest.json"
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
                return manifest.get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def latest_version(self) -> Optional[str]:
        """Return the latest version available."""
        if self.coordinator.data:
            return self.coordinator.data.get("latest_version", self._current_version)
        return self._current_version

    @property
    def release_url(self) -> Optional[str]:
        """Return the release URL."""
        if self.coordinator.data:
            return self.coordinator.data.get("release_url")
        return None

    @property
    def release_summary(self) -> Optional[str]:
        """Return the release summary."""
        if self.coordinator.data:
            notes = self.coordinator.data.get("release_notes", "")
            # Return first paragraph or first 200 chars
            if notes:
                first_paragraph = notes.split("\n\n")[0]
                if len(first_paragraph) > 200:
                    return first_paragraph[:197] + "..."
                return first_paragraph
        return None

    @property
    def title(self) -> Optional[str]:
        """Return the title of the update."""
        return f"{NAME} {self.latest_version}"

    async def async_install(
        self, version: Optional[str] = None, backup: bool = True, **kwargs: Any
    ) -> None:
        """Install an update."""
        # For HACS installations, this triggers HACS to handle the update
        # For manual installations, we'll show instructions
        _LOGGER.info(
            "Update installation requested for version %s. "
            "Please update via HACS or download from GitHub.",
            version or self.latest_version
        )
        
        # Fire an event that can trigger an automation
        self.hass.bus.async_fire(
            f"{DOMAIN}_update_requested",
            {
                "version": version or self.latest_version,
                "current_version": self._current_version,
                "release_url": self.release_url,
            }
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )