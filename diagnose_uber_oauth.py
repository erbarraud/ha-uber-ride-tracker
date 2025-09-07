#!/usr/bin/env python3
"""Diagnostic tool for Uber OAuth issues."""

import json
import sys
from urllib.parse import urlencode, quote

def main():
    print("\n" + "="*60)
    print("UBER OAUTH DIAGNOSTIC TOOL")
    print("="*60 + "\n")
    
    # Get client ID
    client_id = input("Enter your Uber Client ID: ").strip()
    if not client_id:
        print("Error: Client ID is required")
        sys.exit(1)
    
    print("\n" + "-"*40)
    print("IMPORTANT: Check your Uber Developer Dashboard")
    print("-"*40)
    print("\n1. Go to: https://developer.uber.com/dashboard")
    print("2. Select your application")
    print("3. Go to the 'Auth' tab")
    print("4. Check the following settings:\n")
    
    print("   REDIRECT URIs:")
    print("   - Make sure this EXACT URL is listed:")
    print("     https://home.erbarraud.com/local/uber_callback.html")
    print("   - URLs must match EXACTLY (including https:// and trailing slashes)\n")
    
    print("   SCOPES:")
    print("   - Check which scopes are SELECTED in the dashboard")
    print("   - If NO scopes are selected, that could cause invalid_scope")
    print("   - Try selecting ONLY 'profile' scope in the dashboard\n")
    
    print("   APP STATUS:")
    print("   - Is your app in 'Development' or 'Production' mode?")
    print("   - Development apps have limited scope access\n")
    
    input("Press Enter after checking your dashboard settings...")
    
    print("\n" + "-"*40)
    print("TESTING OAUTH URLs")
    print("-"*40 + "\n")
    
    redirect_uri = "https://home.erbarraud.com/local/uber_callback.html"
    
    # Test different configurations
    tests = [
        {
            "name": "No scope parameter at all",
            "params": {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "state": "test1"
            }
        },
        {
            "name": "Empty scope parameter", 
            "params": {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "state": "test2",
                "scope": ""
            }
        },
        {
            "name": "Only 'profile' scope",
            "params": {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "state": "test3",
                "scope": "profile"
            }
        },
        {
            "name": "Space-separated scopes",
            "params": {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "state": "test4",
                "scope": "profile history"
            }
        }
    ]
    
    print("Copy and test each URL in your browser:\n")
    
    for i, test in enumerate(tests, 1):
        url = f"https://auth.uber.com/oauth/v2/authorize?{urlencode(test['params'])}"
        print(f"{i}. {test['name']}:")
        print(f"   {url}")
        print()
    
    print("-"*40)
    print("WHAT TO LOOK FOR:")
    print("-"*40)
    print("\n1. If you get 'invalid_scope' for ALL URLs:")
    print("   → Issue is with your Uber app configuration")
    print("   → Check that scopes are selected in dashboard")
    print("   → Verify redirect URI matches exactly\n")
    
    print("2. If one URL works but others don't:")
    print("   → Note which configuration works")
    print("   → We'll update the code to use that format\n")
    
    print("3. If you get a different error (not invalid_scope):")
    print("   → Progress! The scope issue is fixed")
    print("   → Note the new error message\n")
    
    print("="*60)
    print("\nRECOMMENDED UBER APP SETTINGS:")
    print("="*60)
    print("\n1. Redirect URI (must match EXACTLY):")
    print("   https://home.erbarraud.com/local/uber_callback.html\n")
    
    print("2. Selected Scopes in Dashboard:")
    print("   ☑ profile")
    print("   ☐ request (leave unchecked - requires approval)")
    print("   ☐ all_trips (leave unchecked - requires approval)")
    print("   ☐ request.receipt (leave unchecked - requires approval)\n")
    
    print("3. OAuth 2.0 Settings:")
    print("   - Make sure OAuth 2.0 is enabled")
    print("   - Client ID and Secret should be active\n")

if __name__ == "__main__":
    main()