"""Uber API client."""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ENDPOINT_CURRENT_REQUEST,
    ENDPOINT_REQUEST_DETAILS,
    ENDPOINT_REQUEST_MAP,
    ENDPOINT_REQUEST_RECEIPT,
    ENDPOINT_TRIP_HISTORY,
    ENDPOINT_USER_PROFILE,
    ERROR_API_ERROR,
    ERROR_INVALID_RESPONSE,
    ERROR_NO_ACTIVE_RIDE,
    ERROR_RATE_LIMITED,
    RATE_LIMIT_CALLS,
    RATE_LIMIT_WINDOW,
)
from .oauth import UberOAuthManager

_LOGGER = logging.getLogger(__name__)


class UberAPIError(Exception):
    """Base exception for Uber API errors."""

    pass


class UberRateLimitError(UberAPIError):
    """Exception for rate limit errors."""

    pass


class UberAuthenticationError(UberAPIError):
    """Exception for authentication errors."""

    pass


class UberNoActiveRideError(UberAPIError):
    """Exception for no active ride."""

    pass


class UberAPI:
    """Uber API client."""

    def __init__(
        self,
        hass: HomeAssistant,
        oauth_manager: UberOAuthManager,
    ) -> None:
        """Initialize the Uber API client."""
        self.hass = hass
        self._oauth_manager = oauth_manager
        self._session = async_get_clientsession(hass)
        self._rate_limit_remaining = RATE_LIMIT_CALLS
        self._rate_limit_reset = datetime.now().timestamp() + RATE_LIMIT_WINDOW

    async def _async_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Uber API."""
        # Check rate limiting
        if self._rate_limit_remaining <= 0:
            if datetime.now().timestamp() < self._rate_limit_reset:
                wait_time = self._rate_limit_reset - datetime.now().timestamp()
                _LOGGER.warning(
                    "Rate limited. Waiting %s seconds before retry", wait_time
                )
                raise UberRateLimitError(f"Rate limited for {wait_time} seconds")
            else:
                # Reset rate limit
                self._rate_limit_remaining = RATE_LIMIT_CALLS
                self._rate_limit_reset = datetime.now().timestamp() + RATE_LIMIT_WINDOW

        # Ensure valid token
        await self._oauth_manager.async_ensure_valid_token()

        url = f"{API_BASE_URL}{endpoint}"
        headers = self._oauth_manager.get_authorization_header()
        headers["Content-Type"] = "application/json"
        headers["Accept-Language"] = "en_US"

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                # Update rate limit info from headers
                if "X-Rate-Limit-Remaining" in response.headers:
                    self._rate_limit_remaining = int(
                        response.headers["X-Rate-Limit-Remaining"]
                    )
                if "X-Rate-Limit-Reset" in response.headers:
                    self._rate_limit_reset = int(response.headers["X-Rate-Limit-Reset"])

                if response.status == 401:
                    raise UberAuthenticationError("Authentication failed")
                elif response.status == 429:
                    raise UberRateLimitError("Rate limited")
                elif response.status == 404:
                    if endpoint == ENDPOINT_CURRENT_REQUEST:
                        raise UberNoActiveRideError("No active ride found")
                    raise UberAPIError(f"Resource not found: {endpoint}")
                elif response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get("message", f"HTTP {response.status}")
                    raise UberAPIError(f"API error: {error_msg}")

                return await response.json()

        except asyncio.TimeoutError:
            _LOGGER.error("Request timeout for %s", endpoint)
            raise UberAPIError("Request timeout")
        except aiohttp.ClientError as err:
            _LOGGER.error("Request failed for %s: %s", endpoint, err)
            raise UberAPIError(f"Request failed: {err}")

    async def async_get_current_ride(self) -> Optional[Dict[str, Any]]:
        """Get the current active ride."""
        try:
            return await self._async_request("GET", ENDPOINT_CURRENT_REQUEST)
        except UberNoActiveRideError:
            _LOGGER.debug("No active ride found")
            return None
        except UberAPIError as err:
            _LOGGER.error("Failed to get current ride: %s", err)
            raise

    async def async_get_ride_details(self, request_id: str) -> Dict[str, Any]:
        """Get details for a specific ride."""
        endpoint = ENDPOINT_REQUEST_DETAILS.format(request_id=request_id)
        return await self._async_request("GET", endpoint)

    async def async_get_ride_receipt(self, request_id: str) -> Dict[str, Any]:
        """Get receipt for a completed ride."""
        endpoint = ENDPOINT_REQUEST_RECEIPT.format(request_id=request_id)
        return await self._async_request("GET", endpoint)

    async def async_get_ride_map(self, request_id: str) -> Dict[str, Any]:
        """Get map data for a ride."""
        endpoint = ENDPOINT_REQUEST_MAP.format(request_id=request_id)
        return await self._async_request("GET", endpoint)

    async def async_get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        return await self._async_request("GET", ENDPOINT_USER_PROFILE)

    async def async_get_trip_history(
        self, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get trip history."""
        params = {"limit": limit, "offset": offset}
        response = await self._async_request("GET", ENDPOINT_TRIP_HISTORY, params=params)
        return response.get("history", [])

    def parse_ride_data(self, ride_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ride data into a structured format."""
        if not ride_data:
            return {}

        # Extract driver information
        driver = ride_data.get("driver", {})
        driver_info = {
            "name": driver.get("name"),
            "phone_number": driver.get("phone_number"),
            "sms_number": driver.get("sms_number"),
            "rating": driver.get("rating"),
            "picture_url": driver.get("picture_url"),
        }

        # Extract vehicle information
        vehicle = ride_data.get("vehicle", {})
        vehicle_info = {
            "make": vehicle.get("make"),
            "model": vehicle.get("model"),
            "license_plate": vehicle.get("license_plate"),
            "picture_url": vehicle.get("picture_url"),
            "color": vehicle.get("color"),
        }

        # Extract location information
        location = ride_data.get("location", {})
        pickup = ride_data.get("pickup", {})
        destination = ride_data.get("destination", {})

        # Calculate progress
        status = ride_data.get("status")
        progress = 0
        if status == "completed":
            progress = 100
        elif status == "in_progress" and location:
            # This is a simplified calculation
            # In reality, you'd need to calculate based on route distance
            progress = 50

        # Parse the response
        parsed_data = {
            "request_id": ride_data.get("request_id"),
            "product_id": ride_data.get("product_id"),
            "status": status,
            "driver": driver_info,
            "vehicle": vehicle_info,
            "pickup": {
                "latitude": pickup.get("latitude"),
                "longitude": pickup.get("longitude"),
                "address": pickup.get("address"),
                "eta": pickup.get("eta"),
            },
            "destination": {
                "latitude": destination.get("latitude"),
                "longitude": destination.get("longitude"),
                "address": destination.get("address"),
                "eta": destination.get("eta"),
            },
            "location": {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "bearing": location.get("bearing"),
            },
            "surge_multiplier": ride_data.get("surge_multiplier", 1.0),
            "fare": ride_data.get("fare"),
            "shared": ride_data.get("shared", False),
            "progress_percentage": progress,
        }

        return parsed_data

    async def async_test_connection(self) -> bool:
        """Test the API connection."""
        try:
            await self.async_get_user_profile()
            return True
        except UberAPIError:
            return False