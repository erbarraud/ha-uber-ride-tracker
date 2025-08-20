"""Device tracker platform for Uber Ride Tracker."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
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
    """Set up Uber Ride Tracker device trackers from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    trackers = [
        UberDriverTracker(coordinator, entry),
    ]

    async_add_entities(trackers, update_before_add=True)


class UberDriverTracker(CoordinatorEntity, TrackerEntity):
    """Device tracker for Uber driver location."""

    _attr_name = "Driver"
    _attr_has_entity_name = True
    _attr_icon = "mdi:car-connected"

    def __init__(
        self,
        coordinator: UberRideCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_driver_tracker"

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the tracker."""
        return SourceType.GPS

    @property
    def latitude(self) -> Optional[float]:
        """Return latitude value of the driver."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return None
        
        ride = self.coordinator.data.get("ride", {})
        location = ride.get("location", {})
        
        return location.get("latitude")

    @property
    def longitude(self) -> Optional[float]:
        """Return longitude value of the driver."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return None
        
        ride = self.coordinator.data.get("ride", {})
        location = ride.get("location", {})
        
        return location.get("longitude")

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the device."""
        # Uber typically provides accurate GPS data
        return 10  # meters

    @property
    def battery_level(self) -> Optional[int]:
        """Return the battery level of the device."""
        # Not applicable for driver tracking
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return {
                "status": "no_active_ride",
                "tracking": False,
            }
        
        ride = self.coordinator.data.get("ride", {})
        location = ride.get("location", {})
        driver = ride.get("driver", {})
        vehicle = ride.get("vehicle", {})
        status = ride.get("status")
        
        attributes = {
            "status": status,
            "tracking": status in ACTIVE_RIDE_STATUSES,
        }
        
        if location.get("bearing") is not None:
            attributes["bearing"] = location["bearing"]
        
        if driver.get("name"):
            attributes.update({
                "driver_name": driver.get("name"),
                "driver_rating": driver.get("rating"),
                "driver_phone": driver.get("phone_number"),
                "driver_photo_url": driver.get("picture_url"),
            })
        
        if vehicle.get("make"):
            attributes.update({
                "vehicle": f"{vehicle.get('make')} {vehicle.get('model')}",
                "vehicle_color": vehicle.get("color"),
                "vehicle_license_plate": vehicle.get("license_plate"),
                "vehicle_picture_url": vehicle.get("picture_url"),
            })
        
        # Add pickup and destination info
        pickup = ride.get("pickup", {})
        destination = ride.get("destination", {})
        
        if pickup.get("address"):
            attributes.update({
                "pickup_address": pickup.get("address"),
                "pickup_latitude": pickup.get("latitude"),
                "pickup_longitude": pickup.get("longitude"),
            })
        
        if destination.get("address"):
            attributes.update({
                "destination_address": destination.get("address"),
                "destination_latitude": destination.get("latitude"),
                "destination_longitude": destination.get("longitude"),
            })
        
        # Add trip progress
        attributes["trip_progress_percentage"] = ride.get("progress_percentage", 0)
        
        return attributes

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
        if not self.coordinator.last_update_success:
            return False
        
        # Entity is available even if there's no active ride
        return True

    @property
    def icon(self) -> str:
        """Return the icon based on tracking status."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return "mdi:car-off"
        
        ride = self.coordinator.data.get("ride", {})
        status = ride.get("status")
        
        if status == "arriving":
            return "mdi:car-clock"
        elif status == "in_progress":
            return "mdi:car-connected"
        else:
            return "mdi:car"