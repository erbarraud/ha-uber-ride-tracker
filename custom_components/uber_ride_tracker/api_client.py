"""Simple Uber API client for testing without OAuth."""
import logging
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://api.uber.com"


class UberAPIClient:
    """Uber API client for ride tracking."""
    
    def __init__(self, hass: HomeAssistant, client_id: str, client_secret: str):
        """Initialize the API client."""
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = async_get_clientsession(hass)
        self.access_token = None
        self.token_expires = None
        self.refresh_token = None
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test if we can connect to Uber API."""
        # Note: Uber requires OAuth2 authorization code flow for user data
        # Client credentials flow doesn't work for accessing ride data
        
        # Generate OAuth URL for user authorization
        from urllib.parse import urlencode
        
        # Use your actual Home Assistant domain  
        # This should be added to your Uber app's redirect URIs
        redirect_uri = "https://home.erbarraud.com/local/uber_callback.html"
        
        # Request specific scopes for ride tracking
        # Note: Some scopes like 'request' are privileged and need Full Access approval
        # Using scopes that should work in development
        auth_params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "profile history",  # Start with basic scopes
            "state": "ha_uber_tracker"
        }
        
        auth_url = f"https://login.uber.com/oauth/v2/authorize?{urlencode(auth_params)}"
        
        _LOGGER.warning(
            "Uber API requires OAuth user authorization. "
            "Please visit the authorization URL and grant access."
        )
        
        return {
            "success": False,
            "requires_oauth": True,
            "auth_url": auth_url,
            "message": "Visit the auth URL to authorize access to your Uber account",
            "redirect_uri": redirect_uri,
            "redirect_uri_info": f"Add this to your Uber app redirect URIs: {redirect_uri}"
        }
    
    async def exchange_auth_code(self, auth_code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        # Use the same redirect URI that was used for authorization
        if not redirect_uri:
            redirect_uri = "https://home.erbarraud.com/local/uber_callback.html"
            
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri
        }
        
        try:
            async with self.session.post(
                "https://login.uber.com/oauth/v2/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    expires_in = data.get("expires_in", 3600)
                    self.token_expires = datetime.now() + timedelta(seconds=expires_in)
                    
                    _LOGGER.info("Successfully obtained Uber access token")
                    return {
                        "success": True,
                        "token_obtained": True,
                        "expires_in": expires_in,
                        "scope": data.get("scope")
                    }
                else:
                    error_text = await response.text()
                    _LOGGER.error("Failed to exchange auth code: %s", error_text)
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "details": error_text
                    }
        except Exception as e:
            _LOGGER.error("Error exchanging auth code: %s", e)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_current_ride(self) -> Optional[Dict[str, Any]]:
        """Get current ride information."""
        if not self.access_token:
            _LOGGER.warning("No access token available")
            # Try to get a new token
            await self.test_connection()
            if not self.access_token:
                return None
        
        # Check if token expired
        if self.token_expires and datetime.now() > self.token_expires:
            _LOGGER.info("Token expired, refreshing...")
            await self.test_connection()
        
        if not self.access_token:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Try to get current ride
            async with self.session.get(
                f"{API_BASE_URL}/v1.2/requests/current",
                headers=headers
            ) as response:
                if response.status == 200:
                    ride_data = await response.json()
                    _LOGGER.info("Found active ride: %s", ride_data.get("status"))
                    return self._parse_ride_data(ride_data)
                elif response.status == 404:
                    _LOGGER.debug("No active ride")
                    return {
                        "status": "no_active_ride",
                        "has_ride": False
                    }
                elif response.status == 401:
                    _LOGGER.warning("Unauthorized - token may be invalid")
                    self.access_token = None
                    return None
                else:
                    error_text = await response.text()
                    _LOGGER.error("Error getting ride: HTTP %s - %s", response.status, error_text)
                    return None
                    
        except Exception as e:
            _LOGGER.error("Error fetching current ride: %s", e)
            return None
    
    def _parse_ride_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ride data from Uber API response."""
        if not data:
            return {"status": "no_active_ride", "has_ride": False}
        
        # Extract relevant information
        result = {
            "has_ride": True,
            "status": data.get("status", "unknown"),
            "request_id": data.get("request_id"),
            "product_id": data.get("product_id"),
            "eta": data.get("eta"),  # Arrival time in minutes
            "surge_multiplier": data.get("surge_multiplier", 1.0),
        }
        
        # Driver information
        if driver := data.get("driver"):
            result.update({
                "driver_name": driver.get("name"),
                "driver_phone": driver.get("phone_number"),
                "driver_rating": driver.get("rating"),
                "driver_picture_url": driver.get("picture_url"),
            })
        
        # Vehicle information
        if vehicle := data.get("vehicle"):
            result.update({
                "vehicle_make": vehicle.get("make"),
                "vehicle_model": vehicle.get("model"),
                "vehicle_license_plate": vehicle.get("license_plate"),
                "vehicle_color": vehicle.get("color"),
                "vehicle_picture_url": vehicle.get("picture_url"),
            })
        
        # Location information
        if location := data.get("location"):
            result.update({
                "driver_latitude": location.get("latitude"),
                "driver_longitude": location.get("longitude"),
                "driver_bearing": location.get("bearing"),
            })
        
        # Pickup and destination
        if pickup := data.get("pickup"):
            result.update({
                "pickup_address": pickup.get("alias") or pickup.get("name") or pickup.get("address"),
                "pickup_latitude": pickup.get("latitude"),
                "pickup_longitude": pickup.get("longitude"),
                "pickup_eta": pickup.get("eta"),
            })
        
        if destination := data.get("destination"):
            result.update({
                "destination_address": destination.get("alias") or destination.get("name") or destination.get("address"),
                "destination_latitude": destination.get("latitude"),
                "destination_longitude": destination.get("longitude"),
                "destination_eta": destination.get("eta"),
            })
        
        # Trip information
        if trip := data.get("trip"):
            result.update({
                "distance_estimate": trip.get("distance_estimate"),
                "duration_estimate": trip.get("duration_estimate"),
                "fare_estimate": trip.get("fare_estimate"),
            })
        
        # Calculate progress if in trip
        if result["status"] == "in_progress" and "duration_estimate" in result:
            # This is a rough estimate - would need more data for accurate progress
            result["trip_progress_percentage"] = 50  # Placeholder
        
        return result
    
    async def get_ride_receipt(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get receipt for a completed ride."""
        if not self.access_token or not request_id:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(
                f"{API_BASE_URL}/v1.2/requests/{request_id}/receipt",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception as e:
            _LOGGER.error("Error fetching receipt: %s", e)
            return None
    
    async def test_api_access(self) -> Dict[str, Any]:
        """Test what API endpoints we can access."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "token_valid": False,
            "accessible_endpoints": [],
            "errors": []
        }
        
        # Check if we have a token
        if not self.access_token:
            # Generate OAuth URL instead
            connection_result = await self.test_connection()
            results["requires_oauth"] = True
            results["auth_url"] = connection_result.get("auth_url")
            results["errors"].append(
                "OAuth authorization required. Visit the URL in notifications to authorize."
            )
            return results
        
        results["token_valid"] = True
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Test endpoints - v1.2 API endpoints
        # Note: Some endpoints require specific scopes
        endpoints_to_test = [
            ("/v1.2/me", "User Profile"),  # Requires 'profile' scope
            ("/v1.2/requests/current", "Current Ride"),  # Requires 'request' scope (privileged)
            ("/v1.2/history", "Ride History"),  # Requires 'history' scope
            ("/v1.2/payment-methods", "Payment Methods"),  # Requires 'request' scope
            ("/v1.2/places", "Saved Places"),  # Requires 'places' scope
            ("/v1/products", "Available Products"),  # Public endpoint, no auth needed
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                # Add latitude/longitude for products endpoint
                params = {}
                if "history" in endpoint:
                    params = {"limit": 1}
                elif "products" in endpoint:
                    # Use a default location (San Francisco) for testing
                    params = {"latitude": 37.7749, "longitude": -122.4194}
                
                async with self.session.get(
                    f"{API_BASE_URL}{endpoint}",
                    headers=headers if endpoint != "/v1/products" else {},  # Products doesn't need auth
                    params=params
                ) as response:
                    result = {
                        "endpoint": endpoint,
                        "description": description,
                        "status": response.status,
                        "accessible": response.status in [200, 404]  # 404 is ok for current ride
                    }
                    
                    if response.status == 200:
                        data = await response.json()
                        if endpoint == "/v1.2/me":
                            result["sample_data"] = {
                                "email": data.get("email"),
                                "name": f"{data.get('first_name', '')} {data.get('last_name', '')}",
                                "uuid": data.get("uuid", "")[:8] + "..."
                            }
                        elif endpoint == "/v1.2/history":
                            result["sample_data"] = {
                                "count": data.get("count", 0),
                                "has_rides": data.get("count", 0) > 0
                            }
                        elif endpoint == "/v1.2/requests/current":
                            result["sample_data"] = {"has_active_ride": True}
                    elif response.status == 404 and endpoint == "/v1.2/requests/current":
                        result["sample_data"] = {"has_active_ride": False}
                        result["accessible"] = True
                    elif response.status == 401:
                        result["error"] = "Unauthorized - scope may be missing"
                    else:
                        result["error"] = await response.text()
                    
                    results["accessible_endpoints"].append(result)
                    
            except Exception as e:
                results["accessible_endpoints"].append({
                    "endpoint": endpoint,
                    "description": description,
                    "error": str(e),
                    "accessible": False
                })
        
        return results
    
    async def get_ride_history(self, limit: int = 5) -> Optional[Dict[str, Any]]:
        """Get ride history."""
        if not self.access_token:
            await self.test_connection()
            if not self.access_token:
                return None
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(
                f"{API_BASE_URL}/v1.2/history",
                headers=headers,
                params={"limit": limit, "offset": 0}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "count": data.get("count", 0),
                        "rides": data.get("history", []),
                        "success": True
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "details": await response.text()
                    }
        except Exception as e:
            _LOGGER.error("Error fetching ride history: %s", e)
            return {
                "success": False,
                "error": str(e)
            }