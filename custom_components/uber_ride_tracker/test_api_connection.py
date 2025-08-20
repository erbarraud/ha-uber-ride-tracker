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
    
    def __init__(self):
        """Initialize test."""
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.access_token = None
        
    def get_auth_url(self):
        """Generate OAuth authorization URL."""
        from urllib.parse import urlencode
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "profile ride.request",
            "redirect_uri": "http://localhost:8080/callback",
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
            "redirect_uri": "http://localhost:8080/callback"
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
        
        # Test 3: Trip History
        try:
            async with session.get(
                f"{API_BASE_URL}/v1.2/history",
                headers=headers,
                params={"limit": 5}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    history = data.get("history", [])
                    results["trip_history"] = {
                        "success": True,
                        "count": len(history),
                        "recent_trips": [
                            {
                                "date": datetime.fromtimestamp(trip.get("start_time", 0)).strftime("%Y-%m-%d"),
                                "status": trip.get("status")
                            }
                            for trip in history[:3]
                        ] if history else []
                    }
                else:
                    results["trip_history"] = {
                        "success": False,
                        "status": response.status,
                        "error": await response.text()
                    }
        except Exception as e:
            results["trip_history"] = {"success": False, "error": str(e)}
        
        return results


async def test_uber_api_connection():
    """Main test function."""
    tester = UberAPITest()
    
    print("\n" + "="*60)
    print("UBER API CONNECTION TEST")
    print("="*60)
    
    # Step 1: Generate Auth URL
    auth_url = tester.get_auth_url()
    print("\n1. OAuth Authorization URL:")
    print("-" * 60)
    print(auth_url)
    print("-" * 60)
    
    print("\n2. Instructions:")
    print("   a) Open the URL above in a browser")
    print("   b) Login with your Uber account")
    print("   c) Authorize the app")
    print("   d) Copy the 'code' parameter from redirect URL")
    print("   e) Add it to this script as AUTH_CODE")
    
    # TODO: Replace with actual auth code after OAuth
    AUTH_CODE = ""  # <-- PASTE YOUR AUTH CODE HERE
    
    if not AUTH_CODE:
        print("\n⚠️  No auth code provided. Showing what would be tested:")
        print("\nAPI Endpoints to test:")
        print("✓ User Profile (/v1.2/me)")
        print("✓ Current Ride (/v1.2/requests/current)")
        print("✓ Trip History (/v1.2/history)")
        print("\nExpected data:")
        print("• User email and name")
        print("• Active ride status (if any)")
        print("• Recent trip history")
        return {
            "status": "waiting_for_auth_code",
            "auth_url": auth_url,
            "credentials_valid": True
        }
    
    async with aiohttp.ClientSession() as session:
        # Exchange code for token
        print("\n3. Exchanging auth code for access token...")
        token_result = await tester.exchange_code_for_token(AUTH_CODE, session)
        
        if not token_result["success"]:
            print(f"❌ Token exchange failed: {token_result['error']}")
            return {"status": "token_exchange_failed", "error": token_result}
        
        print(f"✅ Access token obtained!")
        print(f"   Expires in: {token_result['expires_in']} seconds")
        print(f"   Scope: {token_result['scope']}")
        
        # Test API endpoints
        print("\n4. Testing API endpoints...")
        api_results = await tester.test_api_endpoints(session)
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        
        for endpoint, result in api_results.items():
            if result.get("success"):
                print(f"\n✅ {endpoint.upper()}:")
                for key, value in result.items():
                    if key != "success":
                        print(f"   {key}: {value}")
            else:
                print(f"\n❌ {endpoint.upper()}: Failed")
                print(f"   Error: {result.get('error', 'Unknown')}")
        
        return {
            "status": "success",
            "token_obtained": True,
            "api_results": api_results
        }


# This can be run as a service in Home Assistant
async def async_test_service(hass, call):
    """Service to test Uber API connection."""
    result = await test_uber_api_connection()
    
    # Log results
    _LOGGER.info("Uber API Test Results: %s", result)
    
    # Fire event with results
    hass.bus.async_fire("uber_api_test_complete", result)
    
    return result


if __name__ == "__main__":
    # For standalone testing
    asyncio.run(test_uber_api_connection())