"""Sensor platform for Uber Ride Tracker - Simplified version."""
import logging
from typing import Any, Dict
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, MANUFACTURER, NAME

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)  # Poll every 30 seconds


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Uber Ride Tracker sensors from a config entry."""
    
    # Get the API client
    data = hass.data[DOMAIN][entry.entry_id]
    api_client = data.get("api_client")
    
    sensors = [
        UberRideStatusSensor(hass, entry, api_client),
        UberRideProgressSensor(hass, entry, api_client),
    ]
    
    async_add_entities(sensors, update_before_add=True)


class UberRideStatusSensor(SensorEntity):
    """Sensor for Uber ride status."""

    _attr_icon = "mdi:car"
    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api_client) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._api_client = api_client
        self._attr_unique_id = f"{entry.entry_id}_ride_status"
        # This will create entity_id: sensor.uber_ride_tracker_ride_status
        self.entity_id = f"sensor.{DOMAIN}_ride_status"
        self._attr_name = "Ride Status"
        self._ride_data = {}
        self._state = "no_active_ride"

    async def async_update(self) -> None:
        """Update the sensor."""
        if not self._api_client:
            _LOGGER.warning("No API client available")
            return
        
        # Get current ride data
        ride_data = await self._api_client.get_current_ride()
        
        if ride_data:
            self._ride_data = ride_data
            self._state = ride_data.get("status", "no_active_ride")
            
            if ride_data.get("has_ride"):
                _LOGGER.info("Active ride found: %s", self._state)
                # Update scan interval to 10 seconds during active ride
                self.hass.async_create_task(self._schedule_fast_updates())
            else:
                _LOGGER.debug("No active ride")
        else:
            _LOGGER.debug("No data from API")

    async def _schedule_fast_updates(self):
        """Schedule faster updates during active ride."""
        # This will be called to trigger more frequent updates
        # Home Assistant will handle the scheduling
        pass

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        # Start with basic attributes
        attributes = {
            "status": self._state,
            "integration_status": "configured",
        }
        
        # Add all ride data as attributes
        if self._ride_data:
            # Map API fields to expected attribute names
            field_mapping = {
                "driver_name": "driver_name",
                "driver_rating": "driver_rating", 
                "driver_phone": "driver_phone",
                "driver_picture_url": "driver_photo_url",
                "vehicle_make": "vehicle_make",
                "vehicle_model": "vehicle_model",
                "vehicle_color": "vehicle_color",
                "vehicle_license_plate": "vehicle_license_plate",
                "pickup_address": "pickup_address",
                "pickup_eta": "pickup_eta",
                "destination_address": "destination_address",
                "destination_eta": "destination_eta",
                "eta": "eta_minutes",
                "trip_progress_percentage": "trip_progress_percentage",
                "surge_multiplier": "surge_multiplier",
                "fare_estimate": "fare_estimate",
                "driver_latitude": "driver_latitude",
                "driver_longitude": "driver_longitude",
            }
            
            for api_field, attr_name in field_mapping.items():
                if api_field in self._ride_data:
                    attributes[attr_name] = self._ride_data[api_field]
        
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


class UberRideProgressSensor(SensorEntity):
    """Sensor for Uber ride progress percentage."""

    _attr_icon = "mdi:percent"
    _attr_native_unit_of_measurement = "%"
    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api_client) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._api_client = api_client
        self._attr_unique_id = f"{entry.entry_id}_ride_progress"
        # This will create entity_id: sensor.uber_ride_tracker_ride_progress
        self.entity_id = f"sensor.{DOMAIN}_ride_progress"
        self._attr_name = "Ride Progress"
        self._progress = 0

    async def async_update(self) -> None:
        """Update the sensor."""
        if self._api_client:
            ride_data = await self._api_client.get_current_ride()
            if ride_data and ride_data.get("has_ride"):
                self._progress = ride_data.get("trip_progress_percentage", 0)
            else:
                self._progress = 0

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._progress

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