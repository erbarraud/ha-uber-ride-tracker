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

    _attr_name = "Uber Ride Status"
    _attr_icon = "mdi:car"
    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ride_status"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return "waiting_for_oauth"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        return {
            "message": "OAuth authentication needed",
            "client_id": self._entry.data.get("client_id", "")[:10] + "...",
            "integration_status": "configured",
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

    _attr_name = "Uber Ride Progress"
    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"
    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ride_progress"

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