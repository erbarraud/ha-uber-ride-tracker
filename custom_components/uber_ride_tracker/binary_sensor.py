"""Binary sensor platform for Uber Ride Tracker - Simplified."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up Uber Ride Tracker binary sensors from a config entry."""
    
    sensors = [
        UberRideActiveBinarySensor(entry),
    ]
    
    async_add_entities(sensors)


class UberRideActiveBinarySensor(BinarySensorEntity):
    """Binary sensor for active Uber ride."""

    _attr_icon = "mdi:car-connected"
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ride_active"
        # This will create entity_id: binary_sensor.uber_ride_tracker_ride_active
        self.entity_id = f"binary_sensor.{DOMAIN}_ride_active"
        self._attr_name = "Ride Active"

    @property
    def is_on(self) -> bool:
        """Return true if a ride is active."""
        return False  # No active ride until OAuth is implemented

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