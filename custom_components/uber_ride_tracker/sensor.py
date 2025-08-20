"""Sensor platform for Uber Ride Tracker."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up Uber Ride Tracker sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = [
        UberRideStatusSensor(coordinator, entry),
        UberRideProgressSensor(coordinator, entry),
        UberDriverLocationSensor(coordinator, entry),
    ]

    async_add_entities(sensors, update_before_add=True)


class UberRideTrackerSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Uber Ride Tracker sensors."""

    def __init__(
        self,
        coordinator: UberRideCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True

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


class UberRideStatusSensor(UberRideTrackerSensorBase):
    """Sensor for Uber ride status."""

    _attr_name = "Ride Status"
    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: UberRideCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ride_status"

    @property
    def state(self) -> Optional[str]:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return "no_active_ride"
        
        ride = self.coordinator.data.get("ride", {})
        return ride.get("status", "unknown")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return self.coordinator.get_ride_attributes()

    @property
    def icon(self) -> str:
        """Return the icon based on ride status."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return "mdi:car-off"
        
        ride = self.coordinator.data.get("ride", {})
        status = ride.get("status")
        
        if status == "processing":
            return "mdi:magnify"
        elif status == "accepted":
            return "mdi:check-circle"
        elif status == "arriving":
            return "mdi:car-clock"
        elif status == "in_progress":
            return "mdi:car-connected"
        elif status == "completed":
            return "mdi:check-all"
        elif status in ["driver_canceled", "rider_canceled"]:
            return "mdi:cancel"
        else:
            return "mdi:car"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class UberRideProgressSensor(UberRideTrackerSensorBase):
    """Sensor for Uber ride progress percentage."""

    _attr_name = "Ride Progress"
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UberRideCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ride_progress"

    @property
    def state(self) -> Optional[float]:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return 0
        
        ride = self.coordinator.data.get("ride", {})
        return ride.get("progress_percentage", 0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return {}
        
        ride = self.coordinator.data.get("ride", {})
        status = ride.get("status")
        
        attributes = {
            "status": status,
        }
        
        # Add ETA information if available
        if status in ACTIVE_RIDE_STATUSES:
            pickup = ride.get("pickup", {})
            destination = ride.get("destination", {})
            
            if pickup.get("eta"):
                attributes["pickup_eta"] = pickup["eta"]
            if destination.get("eta"):
                attributes["destination_eta"] = destination["eta"]
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class UberDriverLocationSensor(UberRideTrackerSensorBase):
    """Sensor for Uber driver location."""

    _attr_name = "Driver Location"
    _attr_icon = "mdi:map-marker-account"

    def __init__(
        self,
        coordinator: UberRideCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_driver_location"

    @property
    def state(self) -> Optional[str]:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return "unavailable"
        
        ride = self.coordinator.data.get("ride", {})
        location = ride.get("location", {})
        
        if location.get("latitude") and location.get("longitude"):
            return f"{location['latitude']}, {location['longitude']}"
        
        return "unavailable"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return {}
        
        ride = self.coordinator.data.get("ride", {})
        location = ride.get("location", {})
        driver = ride.get("driver", {})
        vehicle = ride.get("vehicle", {})
        
        attributes = {}
        
        if location.get("latitude"):
            attributes.update({
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "bearing": location.get("bearing"),
            })
        
        if driver.get("name"):
            attributes.update({
                "driver_name": driver.get("name"),
                "driver_rating": driver.get("rating"),
            })
        
        if vehicle.get("make"):
            attributes.update({
                "vehicle": f"{vehicle.get('make')} {vehicle.get('model')}",
                "vehicle_color": vehicle.get("color"),
                "license_plate": vehicle.get("license_plate"),
            })
        
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        
        if not self.coordinator.data or not self.coordinator.data.get("has_active_ride"):
            return True  # Available but no data
        
        ride = self.coordinator.data.get("ride", {})
        location = ride.get("location", {})
        return bool(location.get("latitude") and location.get("longitude"))