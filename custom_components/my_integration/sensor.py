"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Time between updating data from the API
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    # Get the stored entry data
    config = hass.data[DOMAIN][entry.entry_id]
    
    # Create coordinator
    coordinator = MyIntegrationDataUpdateCoordinator(hass, config)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Add entities
    async_add_entities(
        [
            MyIntegrationSensor(coordinator, entry, "temperature"),
            MyIntegrationSensor(coordinator, entry, "humidity"),
        ]
    )


class MyIntegrationDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize."""
        self.config = config
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # TODO: Replace with actual API call
            # Example: return await self.api.async_get_data()
            
            # Placeholder data
            return {
                "temperature": 23.5,
                "humidity": 45.2,
            }
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception


class MyIntegrationSensor(CoordinatorEntity, SensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        coordinator: MyIntegrationDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_name = f"{config_entry.data.get('name', 'My Device')} {sensor_type.title()}"

        # Set device class and state class based on sensor type
        if sensor_type == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = "°C"
        elif sensor_type == "humidity":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self._sensor_type)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": self._config_entry.data.get("name", "My Device"),
            "manufacturer": "My Integration",
            "model": "Custom Sensor",
            "sw_version": "1.0.0",
        }
