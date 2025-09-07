"""Sensor platform for Uber Ride Tracker - Simplified version."""
import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uber Ride Tracker sensors from a config entry."""
    
    sensors = [
        UberRideStatusSensor(entry),
        UberRideProgressSensor(entry),
    ]
    
    async_add_entities(sensors)


class UberRideStatusSensor(SensorEntity):
    """Sensor for Uber ride status."""

    _attr_icon = "mdi:car"
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ride_status"
        # This will create entity_id: sensor.uber_ride_tracker_ride_status
        self.entity_id = f"sensor.{DOMAIN}_ride_status"
        self._attr_name = "Ride Status"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        # Return a demo state for testing
        # In production, this would come from the Uber API
        return "no_active_ride"  # or "arriving", "in_progress", etc.

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        # Demo attributes for testing the card
        # In production, these would come from the Uber API
        return {
            "status": "no_active_ride",
            "message": "OAuth authentication needed for live data",
            "integration_status": "configured",
            # Demo data for card testing (uncomment to see card with data)
            # "driver_name": "John Smith",
            # "driver_rating": 4.95,
            # "driver_phone": "+1234567890",
            # "vehicle_make": "Toyota",
            # "vehicle_model": "Camry",
            # "vehicle_color": "Silver",
            # "vehicle_license_plate": "ABC 123",
            # "pickup_eta": 5,
            # "destination_eta": 15,
            # "pickup_address": "123 Main St",
            # "destination_address": "456 Oak Ave",
            # "trip_progress_percentage": 45,
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


class UberRideProgressSensor(SensorEntity):
    """Sensor for Uber ride progress percentage."""

    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ride_progress"
        # This will create entity_id: sensor.uber_ride_tracker_ride_progress
        self.entity_id = f"sensor.{DOMAIN}_ride_progress"
        self._attr_name = "Ride Progress"

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return 0

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