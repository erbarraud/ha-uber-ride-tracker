"""DataUpdateCoordinator for Uber Ride Tracker."""
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import UberAPI, UberAPIError, UberNoActiveRideError
from .const import (
    ACTIVE_RIDE_STATUSES,
    DOMAIN,
    UPDATE_INTERVAL_ACTIVE,
    UPDATE_INTERVAL_ERROR,
    UPDATE_INTERVAL_INACTIVE,
)

_LOGGER = logging.getLogger(__name__)


class UberRideCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Uber ride data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: UberAPI,
        entry_id: str,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.entry_id = entry_id
        self._last_status: Optional[str] = None
        self._error_count = 0
        self._max_error_count = 3

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=UPDATE_INTERVAL_INACTIVE,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Uber API."""
        try:
            # Reset error count on successful update
            self._error_count = 0

            # Get current ride data
            ride_data = await self.api.async_get_current_ride()

            if ride_data:
                # Parse the ride data
                parsed_data = self.api.parse_ride_data(ride_data)
                current_status = parsed_data.get("status")

                # Log status changes
                if current_status != self._last_status:
                    _LOGGER.info(
                        "Ride status changed from %s to %s",
                        self._last_status,
                        current_status,
                    )
                    self._last_status = current_status

                # Adjust update interval based on ride status
                if current_status in ACTIVE_RIDE_STATUSES:
                    self.update_interval = UPDATE_INTERVAL_ACTIVE
                    _LOGGER.debug("Active ride detected, using fast update interval")
                else:
                    self.update_interval = UPDATE_INTERVAL_INACTIVE
                    _LOGGER.debug("No active ride, using slow update interval")

                # Get additional details if ride is active
                if current_status in ACTIVE_RIDE_STATUSES:
                    request_id = parsed_data.get("request_id")
                    if request_id:
                        try:
                            # Get receipt/fare information
                            receipt_data = await self.api.async_get_ride_receipt(request_id)
                            parsed_data["receipt"] = receipt_data
                        except UberAPIError:
                            # Receipt might not be available for ongoing rides
                            _LOGGER.debug("Receipt not available for current ride")

                        try:
                            # Get map data
                            map_data = await self.api.async_get_ride_map(request_id)
                            parsed_data["map"] = map_data
                        except UberAPIError:
                            _LOGGER.debug("Map data not available for current ride")

                return {
                    "ride": parsed_data,
                    "has_active_ride": True,
                    "last_update": self.hass.helpers.template.now(),
                }

            else:
                # No active ride
                self._last_status = None
                self.update_interval = UPDATE_INTERVAL_INACTIVE
                
                return {
                    "ride": None,
                    "has_active_ride": False,
                    "last_update": self.hass.helpers.template.now(),
                }

        except UberNoActiveRideError:
            # This is expected when there's no active ride
            self._last_status = None
            self.update_interval = UPDATE_INTERVAL_INACTIVE
            
            return {
                "ride": None,
                "has_active_ride": False,
                "last_update": self.hass.helpers.template.now(),
            }

        except UberAPIError as err:
            self._error_count += 1
            _LOGGER.error("Error fetching Uber data: %s (error count: %s)", err, self._error_count)
            
            # Use error interval after multiple failures
            if self._error_count >= self._max_error_count:
                self.update_interval = UPDATE_INTERVAL_ERROR
                _LOGGER.warning("Multiple errors detected, using error update interval")
            
            raise UpdateFailed(f"Error communicating with Uber API: {err}")

        except Exception as err:
            self._error_count += 1
            _LOGGER.exception("Unexpected error fetching Uber data")
            
            if self._error_count >= self._max_error_count:
                self.update_interval = UPDATE_INTERVAL_ERROR
            
            raise UpdateFailed(f"Unexpected error: {err}")

    async def async_refresh_status(self) -> None:
        """Force refresh the ride status."""
        _LOGGER.info("Force refreshing ride status")
        await self.async_request_refresh()

    async def async_get_ride_history(self, limit: int = 10) -> list:
        """Get ride history."""
        try:
            return await self.api.async_get_trip_history(limit=limit)
        except UberAPIError as err:
            _LOGGER.error("Failed to get ride history: %s", err)
            raise UpdateFailed(f"Failed to get ride history: {err}")

    def get_ride_attributes(self) -> Dict[str, Any]:
        """Get formatted ride attributes for entities."""
        if not self.data or not self.data.get("has_active_ride"):
            return {}

        ride = self.data.get("ride", {})
        if not ride:
            return {}

        attributes = {
            "status": ride.get("status"),
            "trip_id": ride.get("request_id"),
            "product_id": ride.get("product_id"),
            "surge_multiplier": ride.get("surge_multiplier", 1.0),
            "shared": ride.get("shared", False),
            "last_update": self.data.get("last_update"),
        }

        # Driver information
        driver = ride.get("driver", {})
        if driver.get("name"):
            attributes.update({
                "driver_name": driver.get("name"),
                "driver_rating": driver.get("rating"),
                "driver_phone": driver.get("phone_number"),
                "driver_photo_url": driver.get("picture_url"),
            })

        # Vehicle information
        vehicle = ride.get("vehicle", {})
        if vehicle.get("make"):
            attributes.update({
                "vehicle_make": vehicle.get("make"),
                "vehicle_model": vehicle.get("model"),
                "vehicle_color": vehicle.get("color"),
                "vehicle_license_plate": vehicle.get("license_plate"),
                "vehicle_picture_url": vehicle.get("picture_url"),
            })

        # Location information
        pickup = ride.get("pickup", {})
        if pickup.get("address"):
            attributes.update({
                "pickup_address": pickup.get("address"),
                "pickup_eta": pickup.get("eta"),
                "pickup_latitude": pickup.get("latitude"),
                "pickup_longitude": pickup.get("longitude"),
            })

        destination = ride.get("destination", {})
        if destination.get("address"):
            attributes.update({
                "destination_address": destination.get("address"),
                "destination_eta": destination.get("eta"),
                "destination_latitude": destination.get("latitude"),
                "destination_longitude": destination.get("longitude"),
            })

        # Current location
        location = ride.get("location", {})
        if location.get("latitude"):
            attributes.update({
                "driver_latitude": location.get("latitude"),
                "driver_longitude": location.get("longitude"),
                "driver_bearing": location.get("bearing"),
            })

        # Fare information
        if ride.get("fare"):
            attributes["fare_estimate"] = ride.get("fare")

        # Progress
        attributes["trip_progress_percentage"] = ride.get("progress_percentage", 0)

        # Map URL (construct from ride ID)
        if ride.get("request_id"):
            attributes["map_url"] = f"https://riders.uber.com/trips/{ride['request_id']}"
            attributes["share_url"] = f"https://riders.uber.com/share/{ride['request_id']}"

        return attributes