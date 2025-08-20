"""Binary sensor platform for Uber Ride Tracker."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ACTIVE_RIDE_STATUSES,
    DOMAIN,
    MANUFACTURER,
    NAME,
)
from .coordinator import UberRideCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uber Ride Tracker binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = [
        UberRideActiveBinarySensor(coordinator, entry),
    ]

    async_add_entities(sensors, update_before_add=True)


class UberRideActiveBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for active Uber ride."""

    _attr_name = "Ride Active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UberRideCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ride_active"

    @property
    def is_on(self) -> bool:
        """Return true if a ride is active."""
        if not self.coordinator.data:
            return False
        
        if not self.coordinator.data.get("has_active_ride"):
            return False
        
        ride = self.coordinator.data.get("ride", {})
        status = ride.get("status")
        
        return status in ACTIVE_RIDE_STATUSES

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return {
                "status": "no_active_ride",
                "last_check": self.coordinator.data.get("last_update") if self.coordinator.data else None,
            }
        
        ride = self.coordinator.data.get("ride", {})
        
        return {
            "status": ride.get("status"),
            "trip_id": ride.get("request_id"),
            "pickup_address": ride.get("pickup", {}).get("address"),
            "destination_address": ride.get("destination", {}).get("address"),
            "last_update": self.coordinator.data.get("last_update"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            model="Ride Tracker",
            sw_version="1.0.0",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success