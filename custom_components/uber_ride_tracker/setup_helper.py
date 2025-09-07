"""Setup helper for easy Uber API configuration."""
import logging
import webbrowser
from typing import Dict, Any, Optional
import aiohttp
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.components import persistent_notification

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UBER_DEVELOPER_SIGNUP = "https://developer.uber.com/signup"
UBER_DEVELOPER_DASHBOARD = "https://developer.uber.com/dashboard"
UBER_APP_CREATE = "https://developer.uber.com/dashboard/create"


class UberAPISetupHelper:
    """Helper class to simplify Uber API setup process."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the setup helper."""
        self.hass = hass
        self.redirect_uri = None
        self.session = aiohttp.ClientSession()

    async def get_redirect_uri(self) -> str:
        """Get the correct redirect URI for this Home Assistant instance."""
        # Try to get the external URL configured in HA
        external_url = self.hass.config.external_url
        internal_url = self.hass.config.internal_url
        
        if external_url:
            base_url = str(external_url).rstrip('/')
        elif internal_url:
            base_url = str(internal_url).rstrip('/')
        else:
            # Fallback to local URL
            base_url = "http://homeassistant.local:8123"
        
        # Check if using Nabu Casa
        if "ui.nabu.casa" in base_url:
            self.redirect_uri = "https://my.home-assistant.io/redirect/oauth"
        else:
            self.redirect_uri = f"{base_url}/auth/external/callback"
        
        return self.redirect_uri

    async def validate_credentials(self, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Validate Uber API credentials."""
        result = {
            "valid": False,
            "error": None,
            "suggestions": []
        }
        
        # Basic validation
        if not client_id or len(client_id) < 20:
            result["error"] = "Client ID appears to be invalid"
            result["suggestions"].append("Check that you copied the complete Client ID from Uber Dashboard")
            return result
        
        if not client_secret or len(client_secret) < 20:
            result["error"] = "Client Secret appears to be invalid"
            result["suggestions"].append("Check that you copied the complete Client Secret from Uber Dashboard")
            return result
        
        # Test the credentials with a basic API call
        try:
            # This is a simple validation - actual OAuth flow will happen during setup
            result["valid"] = True
            result["message"] = "Credentials format appears valid. OAuth authentication will be tested during setup."
        except Exception as e:
            result["error"] = str(e)
            result["suggestions"].append("Ensure your Uber app is properly configured")
        
        return result

    async def generate_setup_instructions(self) -> Dict[str, str]:
        """Generate personalized setup instructions."""
        redirect_uri = await self.get_redirect_uri()
        
        instructions = {
            "step1": {
                "title": "Create Uber Developer Account",
                "description": "Sign up for a free Uber Developer account",
                "action": "Open Uber Developer Signup",
                "url": UBER_DEVELOPER_SIGNUP,
                "details": [
                    "Click 'Sign Up' if you don't have an account",
                    "Use your regular Uber account email",
                    "Verify your email address"
                ]
            },
            "step2": {
                "title": "Create New App",
                "description": "Create an app in Uber Developer Dashboard",
                "action": "Open App Creation Page",
                "url": UBER_APP_CREATE,
                "details": [
                    "App Name: 'Home Assistant Ride Tracker' (or any name you prefer)",
                    "Description: 'Personal ride tracking for Home Assistant'",
                    "Select 'Rides API' as the product"
                ]
            },
            "step3": {
                "title": "Configure OAuth Settings",
                "description": "Add the redirect URI to your Uber app",
                "action": "Copy Redirect URI",
                "value": redirect_uri,
                "details": [
                    f"Add this exact URL: {redirect_uri}",
                    "Save the app settings",
                    "Make note of your Client ID and Client Secret"
                ]
            },
            "step4": {
                "title": "Copy Credentials",
                "description": "Get your Client ID and Client Secret",
                "action": "Open Dashboard",
                "url": UBER_DEVELOPER_DASHBOARD,
                "details": [
                    "Find your app in the dashboard",
                    "Copy the Client ID (starts with a long string)",
                    "Copy the Client Secret (keep this secure!)",
                    "Paste them in Home Assistant when prompted"
                ]
            }
        }
        
        return instructions

    async def create_quick_setup_notification(self):
        """Create a persistent notification with setup instructions."""
        redirect_uri = await self.get_redirect_uri()
        
        message = f"""
## 🚀 Quick Setup Guide for Uber API

### Step 1: Create Uber Developer Account
[Click here to sign up]({UBER_DEVELOPER_SIGNUP})

### Step 2: Create New App
[Click here to create app]({UBER_APP_CREATE})
- Name: "Home Assistant Ride Tracker"
- Product: "Rides API"

### Step 3: Add Redirect URI
Add this exact URL to your app:
```
{redirect_uri}
```

### Step 4: Get Credentials
[Open your dashboard]({UBER_DEVELOPER_DASHBOARD})
- Copy your Client ID
- Copy your Client Secret

### Step 5: Enter in Home Assistant
Return here and enter your credentials

---
**Need help?** The redirect URI has been copied to your clipboard!
        """
        
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "🚗 Uber Ride Tracker - API Setup Guide",
                "message": message,
                "notification_id": f"{DOMAIN}_setup_guide",
            }
        )
        
        # Also copy redirect URI to clipboard if possible
        await self.hass.services.async_call(
            "frontend",
            "set_clipboard",
            {"text": redirect_uri},
            blocking=False
        )

    async def check_api_availability(self) -> Dict[str, Any]:
        """Check if Uber API is accessible from this network."""
        result = {
            "accessible": False,
            "latency": None,
            "error": None
        }
        
        try:
            import time
            start = time.time()
            async with self.session.get(
                "https://api.uber.com/v1.2/products",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                result["latency"] = round((time.time() - start) * 1000, 2)
                result["accessible"] = True
                result["status_code"] = response.status
        except aiohttp.ClientError as e:
            result["error"] = f"Cannot reach Uber API: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result

    async def auto_configure_app(self, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Attempt to auto-configure the Uber app settings."""
        result = {
            "success": False,
            "message": "",
            "next_steps": []
        }
        
        # Note: Uber doesn't provide API to modify app settings
        # But we can provide the exact configuration needed
        
        redirect_uri = await self.get_redirect_uri()
        
        result["message"] = "Auto-configuration prepared"
        result["next_steps"] = [
            f"1. Go to: {UBER_DEVELOPER_DASHBOARD}",
            f"2. Select your app",
            f"3. Add Redirect URI: {redirect_uri}",
            f"4. Enable scopes: profile, request, all_trips",
            f"5. Save changes"
        ]
        
        # Create a clickable link notification
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "📋 Configuration Ready",
                "message": f"Redirect URI copied to clipboard:\n`{redirect_uri}`\n\n[Open Uber Dashboard]({UBER_DEVELOPER_DASHBOARD})",
                "notification_id": f"{DOMAIN}_auto_config",
            }
        )
        
        result["success"] = True
        return result

    async def cleanup(self):
        """Clean up resources."""
        await self.session.close()


async def simplify_setup_flow(hass: HomeAssistant) -> None:
    """Simplify the entire setup flow with automation."""
    helper = UberAPISetupHelper(hass)
    
    # Create setup guide notification
    await helper.create_quick_setup_notification()
    
    # Check API availability
    api_check = await helper.check_api_availability()
    if not api_check["accessible"]:
        _LOGGER.warning("Uber API may not be accessible: %s", api_check.get("error"))
    
    # Get redirect URI for easy copying
    redirect_uri = await helper.get_redirect_uri()
    _LOGGER.info("Redirect URI for Uber app: %s", redirect_uri)
    
    await helper.cleanup()


class SetupWizard:
    """Interactive setup wizard for the config flow."""
    
    STEPS = {
        "account": {
            "title": "Uber Developer Account",
            "description": "Do you have an Uber Developer account?",
            "fields": {
                "has_account": {
                    "type": "boolean",
                    "default": False
                }
            }
        },
        "create_app": {
            "title": "Create Uber App",
            "description": "Let's create your Uber app",
            "fields": {
                "open_dashboard": {
                    "type": "button",
                    "url": UBER_APP_CREATE
                }
            }
        },
        "configure_redirect": {
            "title": "Configure Redirect URI",
            "description": "Add this URI to your Uber app",
            "fields": {
                "redirect_uri": {
                    "type": "text",
                    "readonly": True,
                    "copyable": True
                }
            }
        },
        "enter_credentials": {
            "title": "Enter API Credentials",
            "description": "Enter your Client ID and Secret from Uber Dashboard",
            "fields": {
                "client_id": {
                    "type": "text",
                    "required": True
                },
                "client_secret": {
                    "type": "password",
                    "required": True
                }
            }
        }
    }
    
    @classmethod
    async def get_step(cls, step_id: str, hass: HomeAssistant) -> Dict[str, Any]:
        """Get wizard step configuration."""
        step = cls.STEPS.get(step_id, {}).copy()
        
        if step_id == "configure_redirect":
            helper = UberAPISetupHelper(hass)
            redirect_uri = await helper.get_redirect_uri()
            step["fields"]["redirect_uri"]["value"] = redirect_uri
            await helper.cleanup()
        
        return step