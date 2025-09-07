#!/usr/bin/env python3
"""
Manual setup for Uber integration using a token you obtain manually.

Since your Uber app doesn't show the personal token section, you have a few options:

1. Contact Uber support to enable token generation for your app
2. Use the OAuth flow (requires scope approval from Uber)
3. Try creating a new app in the Uber dashboard

For now, if you can obtain a token through any means (API testing tools, 
Postman, etc.), you can use this script to test it.
"""

import asyncio
import aiohttp
import json
import sys

async def test_uber_token(token):
    """Test an Uber access token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "="*60)
    print("TESTING UBER ACCESS TOKEN")
    print("="*60 + "\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: User Profile
        print("1. Testing user profile endpoint...")
        try:
            async with session.get(
                "https://api.uber.com/v1.2/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ SUCCESS - User: {data.get('first_name')} {data.get('last_name')}")
                    print(f"   Email: {data.get('email')}")
                    print(f"   UUID: {data.get('uuid')}")
                elif response.status == 401:
                    print("   ❌ UNAUTHORIZED - Token is invalid or expired")
                    return False
                else:
                    print(f"   ❌ ERROR - HTTP {response.status}")
                    print(f"   Response: {await response.text()}")
                    return False
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            return False
        
        # Test 2: Ride History
        print("\n2. Testing ride history endpoint...")
        try:
            async with session.get(
                "https://api.uber.com/v1.2/history?limit=5",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    count = data.get("count", 0)
                    print(f"   ✅ SUCCESS - Found {count} rides in history")
                    if count > 0 and "history" in data:
                        latest = data["history"][0]
                        print(f"   Latest ride: {latest.get('start_city', {}).get('display_name', 'Unknown')}")
                elif response.status == 401:
                    print("   ⚠️  UNAUTHORIZED - May need 'history' scope")
                elif response.status == 403:
                    print("   ⚠️  FORBIDDEN - 'history' scope not available")
                else:
                    print(f"   ❌ ERROR - HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        # Test 3: Current Ride
        print("\n3. Testing current ride endpoint...")
        try:
            async with session.get(
                "https://api.uber.com/v1.2/requests/current",
                headers=headers
            ) as response:
                if response.status == 200:
                    print("   ✅ Active ride found!")
                elif response.status == 404:
                    print("   ✅ No active ride (expected)")
                elif response.status == 401:
                    print("   ⚠️  UNAUTHORIZED - May need 'request' scope")
                elif response.status == 403:
                    print("   ⚠️  FORBIDDEN - 'request' scope not available")
                else:
                    print(f"   ❌ ERROR - HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
    
    print("\n" + "="*60)
    print("TOKEN TEST COMPLETE")
    print("="*60 + "\n")
    
    return True

def generate_ha_config(token):
    """Generate Home Assistant configuration."""
    print("\nTo use this token in Home Assistant, add to your configuration.yaml:\n")
    print("```yaml")
    print("# Manual Uber configuration")
    print("uber_ride_tracker:")
    print(f'  personal_access_token: "{token}"')
    print("```")
    print("\nOr save the token in secrets.yaml:")
    print("```yaml")
    print("# secrets.yaml")
    print(f'uber_token: "{token}"')
    print("\n# configuration.yaml")
    print("uber_ride_tracker:")
    print("  personal_access_token: !secret uber_token")
    print("```")

async def main():
    """Main function."""
    print("\n" + "="*60)
    print("UBER MANUAL TOKEN SETUP")
    print("="*60)
    
    print("\nSince your Uber app doesn't show the personal token section,")
    print("you'll need to obtain a token through other means:")
    print("\n1. Contact Uber support to enable token generation")
    print("2. Use OAuth flow (requires scope approval)")
    print("3. Try creating a new test app in Uber dashboard")
    print("4. Use Uber's API testing tools if available\n")
    
    token = input("If you have a token, paste it here (or press Enter to skip): ").strip()
    
    if token:
        success = await test_uber_token(token)
        if success:
            generate_ha_config(token)
    else:
        print("\nNo token provided. Please obtain one from Uber first.")
        print("\nAlternative: Send the email we drafted to Uber support")
        print("requesting OAuth scope access for your application.")

if __name__ == "__main__":
    asyncio.run(main())