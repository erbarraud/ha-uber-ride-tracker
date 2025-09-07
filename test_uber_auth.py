#!/usr/bin/env python3
"""Test Uber API authentication and endpoints."""

import asyncio
import aiohttp
import sys
from urllib.parse import urlencode

# Configuration - Update these with your values
CLIENT_ID = "g7UPHAGKIBhPE8dEcXTQ3-Wa8UPl1b-elf"  # Your App ID from Uber
CLIENT_SECRET = ""  # Add your secret here
REDIRECT_URI = "https://home.erbarraud.com/local/uber_callback.html"

# Uber API endpoints - Use auth.uber.com (not login.uber.com)
AUTH_URL = "https://auth.uber.com/oauth/v2/authorize"
TOKEN_URL = "https://auth.uber.com/oauth/v2/token"
API_BASE = "https://api.uber.com"


async def generate_auth_url():
    """Generate OAuth authorization URL."""
    # Don't specify scope to avoid invalid_scope error
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "test_auth"
        # No scope parameter - let Uber use defaults
    }
    
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    print("\n" + "="*60)
    print("UBER OAUTH AUTHORIZATION")
    print("="*60)
    print("\n1. Visit this URL in your browser:")
    print(f"\n   {auth_url}\n")
    print("2. Log in with your Uber account")
    print("3. Authorize the app")
    print("4. Copy the authorization code from the callback page")
    print("5. Run this script again with the code:\n")
    print(f"   python test_uber_auth.py <AUTH_CODE>\n")
    print("="*60)


async def exchange_code(auth_code):
    """Exchange authorization code for access token."""
    if not CLIENT_SECRET:
        print("\n❌ ERROR: Please add your CLIENT_SECRET to the script")
        return None
    
    print(f"\n🔄 Exchanging authorization code for access token...")
    
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(TOKEN_URL, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    print("✅ Successfully obtained access token!")
                    print(f"\nToken details:")
                    print(f"  - Access Token: {token_data.get('access_token')[:20]}...")
                    print(f"  - Expires in: {token_data.get('expires_in')} seconds")
                    print(f"  - Scope: {token_data.get('scope')}")
                    print(f"  - Token Type: {token_data.get('token_type')}")
                    if token_data.get('refresh_token'):
                        print(f"  - Refresh Token: {token_data.get('refresh_token')[:20]}...")
                    return token_data.get('access_token')
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to exchange code: HTTP {response.status}")
                    print(f"   Error: {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


async def test_endpoints(access_token):
    """Test various API endpoints."""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("/v1.2/me", "User Profile", {}),
        ("/v1.2/history", "Ride History", {"limit": 1}),
        ("/v1.2/requests/current", "Current Ride", {}),
        ("/v1/products", "Available Products", {"latitude": 37.7749, "longitude": -122.4194}),
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, description, params in endpoints:
            print(f"\n📍 Testing: {description}")
            print(f"   Endpoint: {API_BASE}{endpoint}")
            
            # Products endpoint doesn't need auth
            endpoint_headers = {} if "products" in endpoint else headers
            
            try:
                async with session.get(
                    f"{API_BASE}{endpoint}",
                    headers=endpoint_headers,
                    params=params
                ) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ Success!")
                        
                        # Show sample data
                        if endpoint == "/v1.2/me":
                            print(f"   User: {data.get('first_name', '')} {data.get('last_name', '')}")
                            print(f"   Email: {data.get('email', 'N/A')}")
                        elif endpoint == "/v1.2/history":
                            count = data.get('count', 0)
                            print(f"   Total rides: {count}")
                            if count > 0 and data.get('history'):
                                ride = data['history'][0]
                                print(f"   Last ride: {ride.get('status')} - ${ride.get('total', 0)}")
                        elif endpoint == "/v1/products":
                            products = data.get('products', [])
                            print(f"   Available products: {len(products)}")
                            if products:
                                print(f"   Example: {products[0].get('display_name')}")
                    
                    elif response.status == 404:
                        if endpoint == "/v1.2/requests/current":
                            print(f"   ✅ No active ride (expected)")
                        else:
                            print(f"   ⚠️ Not found")
                    
                    elif response.status == 401:
                        error_text = await response.text()
                        print(f"   ❌ Unauthorized - may need different scope")
                        print(f"   Error: {error_text[:200]}")
                    
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Error: {error_text[:200]}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")


async def main():
    """Main function."""
    if len(sys.argv) > 1:
        auth_code = sys.argv[1]
        access_token = await exchange_code(auth_code)
        if access_token:
            await test_endpoints(access_token)
            print("\n" + "="*60)
            print("✅ Testing complete!")
            print("\nNext steps:")
            print("1. Use the 'uber_ride_tracker.authorize' service in Home Assistant")
            print("2. Provide the auth code to complete setup")
            print("="*60)
    else:
        await generate_auth_url()


if __name__ == "__main__":
    asyncio.run(main())