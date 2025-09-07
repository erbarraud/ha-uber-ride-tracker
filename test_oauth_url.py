#!/usr/bin/env python3
"""Test OAuth URL generation to debug invalid_scope error."""

import sys
from urllib.parse import urlencode

def test_oauth_urls():
    """Generate different OAuth URL variations to test."""
    
    # Get client ID from command line or use placeholder
    client_id = sys.argv[1] if len(sys.argv) > 1 else "YOUR_CLIENT_ID"
    redirect_uri = "https://home.erbarraud.com/local/uber_callback.html"
    
    print("Testing different OAuth URL configurations:\n")
    print("=" * 60)
    
    # Test 1: No scope at all
    params1 = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": "test"
    }
    url1 = f"https://auth.uber.com/oauth/v2/authorize?{urlencode(params1)}"
    print("1. WITHOUT scope parameter:")
    print(f"   {url1}\n")
    
    # Test 2: Empty scope
    params2 = {
        "client_id": client_id,
        "response_type": "code", 
        "redirect_uri": redirect_uri,
        "state": "test",
        "scope": ""
    }
    url2 = f"https://auth.uber.com/oauth/v2/authorize?{urlencode(params2)}"
    print("2. WITH empty scope:")
    print(f"   {url2}\n")
    
    # Test 3: Profile scope only
    params3 = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": "test",
        "scope": "profile"
    }
    url3 = f"https://auth.uber.com/oauth/v2/authorize?{urlencode(params3)}"
    print("3. WITH 'profile' scope:")
    print(f"   {url3}\n")
    
    print("=" * 60)
    print("\nInstructions:")
    print("1. Replace YOUR_CLIENT_ID with your actual Uber app client ID")
    print("2. Try each URL in your browser")
    print("3. See which one doesn't give invalid_scope error")
    print("4. Check your Uber app settings at https://developer.uber.com")
    print("   - Ensure your app is properly configured")
    print("   - Check which scopes are available for your app")
    print("   - Verify the redirect URI matches exactly")

if __name__ == "__main__":
    test_oauth_urls()