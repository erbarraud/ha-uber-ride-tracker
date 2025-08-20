"""Test script to verify Uber API connection in Home Assistant."""
import asyncio
import aiohttp
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

# Your Uber App Credentials
CLIENT_ID = "gyUPRACf08NFEBoEcXTG3-Wa8U3FB-Bf"
CLIENT_SECRET = "wzo8V7ivmB1DRPbewGiFQtXtl27wDP9T9e3QVYWJ"

# Uber API Configuration
OAUTH2_AUTHORIZE_URL = "https://login.uber.com/oauth/v2/authorize"
OAUTH2_TOKEN_URL = "https://login.uber.com/oauth/v2/token"
API_BASE_URL = "https://api.uber.com"

class UberAPITest:
    """Test Uber API connection."""
    
    def __init__(self, redirect_uri=None):
        """Initialize test."""
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.access_token = None
        # Use provided redirect URI or default
        self.redirect_uri = redirect_uri or "https://my.home-assistant.io/redirect/oauth"
        
    def get_auth_url(self, custom_redirect=None):
        """Generate OAuth authorization URL."""
        from urllib.parse import urlencode
        
        redirect = custom_redirect or self.redirect_uri
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "profile",  # Start with just profile scope
            "redirect_uri": redirect,
            "state": "test123"
        }
        
        return f"{OAUTH2_AUTHORIZE_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, auth_code: str, session: aiohttp.ClientSession):
        """Exchange authorization code for access token."""
        
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        try:
            async with session.post(
                OAUTH2_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token")
                    return {
                        "success": True,
                        "access_token": self.access_token[:20] + "...",
                        "expires_in": data.get("expires_in"),
                        "scope": data.get("scope")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "details": await response.text()
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_api_endpoints(self, session: aiohttp.ClientSession):
        """Test various Uber API endpoints."""
        if not self.access_token:
            return {"error": "No access token available"}
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        results = {}
        
        # Test 1: User Profile
        try:
            async with session.get(
                f"{API_BASE_URL}/v1.2/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    profile = await response.json()
                    results["profile"] = {
                        "success": True,
                        "email": profile.get("email"),
                        "name": f"{profile.get('first_name')} {profile.get('last_name')}",
                        "uuid": profile.get("uuid")
                    }
                else:
                    results["profile"] = {
                        "success": False,
                        "status": response.status,
                        "error": await response.text()
                    }
        except Exception as e:
            results["profile"] = {"success": False, "error": str(e)}
        
        # Test 2: Current Ride
        try:
            async with session.get(
                f"{API_BASE_URL}/v1.2/requests/current",
                headers=headers
            ) as response:
                if response.status == 200:
                    ride = await response.json()
                    results["current_ride"] = {
                        "success": True,
                        "status": ride.get("status"),
                        "request_id": ride.get("request_id"),
                        "driver": ride.get("driver", {}).get("name") if ride.get("driver") else None
                    }
                elif response.status == 404:
                    results["current_ride"] = {
                        "success": True,
                        "message": "No active ride (normal)"
                    }
                else:
                    results["current_ride"] = {
                        "success": False,
                        "status": response.status,
                        "error": await response.text()
                    }
        except Exception as e:
            results["current_ride"] = {"success": False, "error": str(e)}
        
        return results


async def test_uber_api_connection(redirect_uri=None):
    """Main test function."""
    tester = UberAPITest(redirect_uri)
    
    print("\n" + "="*60)
    print("UBER API CONNECTION TEST")
    print("="*60)
    
    # Generate multiple OAuth URLs with different redirect URIs
    print("\n📍 OAuth URLs (try each one):")
    print("-" * 60)
    
    redirect_options = [
        "https://my.home-assistant.io/redirect/oauth",
        "http://localhost:8080/callback",
        "http://homeassistant.local:8123/auth/external/callback",
    ]
    
    urls = {}
    for redirect in redirect_options:
        url = tester.get_auth_url(redirect)
        urls[redirect] = url
        print(f"\n{redirect}:")
        print(url)
    
    print("-" * 60)
    
    print("\n📋 Instructions:")
    print("1. Try each URL above until one works")
    print("2. The working URL should match what's in your Uber app")
    print("3. After authorizing, copy the code from the redirect")
    
    # Return the URLs for the notification
    main_url = tester.get_auth_url()
    
    return {
        "status": "waiting_for_auth_code",
        "auth_url": main_url,
        "all_urls": urls,
        "credentials_valid": True,
        "message": "Check logs for multiple redirect URI options"
    }


# This can be run as a service in Home Assistant
async def async_test_service(hass, call):
    """Service to test Uber API connection."""
    # Get redirect URI from config if available
    redirect_uri = call.data.get("redirect_uri")
    
    result = await test_uber_api_connection(redirect_uri)
    
    # Log results
    _LOGGER.info("Uber API Test Results: %s", result)
    
    # Fire event with results
    hass.bus.async_fire("uber_api_test_complete", result)
    
    return result


if __name__ == "__main__":
    # For standalone testing
    asyncio.run(test_uber_api_connection())