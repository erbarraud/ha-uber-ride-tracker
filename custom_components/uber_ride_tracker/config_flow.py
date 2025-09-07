"""Simplified config flow for Uber Ride Tracker integration."""
import logging
from typing import Any, Dict, Optional
import voluptuous as vol
import aiohttp
from urllib.parse import urlencode, parse_qs, urlparse

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components import persistent_notification

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    NAME,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_CLIENT_ID): str,
    vol.Required(CONF_CLIENT_SECRET): str,
})

class UberRideTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Uber Ride Tracker."""

    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.refresh_token = None
        self.auth_code = None
        self.redirect_uri = None
        self.test_results = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - get credentials and start OAuth."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            _LOGGER.info("Starting Uber integration setup with provided credentials")
            
            # Store credentials
            self.client_id = user_input[CONF_CLIENT_ID].strip()
            self.client_secret = user_input[CONF_CLIENT_SECRET].strip()
            
            # Basic validation
            _LOGGER.debug("Validating credentials format")
            if len(self.client_id) < 20:
                _LOGGER.error("Client ID too short: %d chars", len(self.client_id))
                errors["base"] = "invalid_client_id"
            elif len(self.client_secret) < 20:
                _LOGGER.error("Client secret too short: %d chars", len(self.client_secret))
                errors["base"] = "invalid_client_secret"
            else:
                # Set unique ID to prevent duplicates
                await self.async_set_unique_id(f"uber_{self.client_id}")
                self._abort_if_unique_id_configured()
                
                # Move to OAuth step
                return await self.async_step_oauth()

        # Show initial form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "dashboard_url": "https://developer.uber.com/dashboard",
            },
        )

    async def async_step_oauth(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle OAuth authorization."""
        _LOGGER.info("Starting OAuth authorization step")
        
        # Generate redirect URI based on HA instance
        if self.hass.config.external_url:
            base_url = str(self.hass.config.external_url).rstrip('/')
            self.redirect_uri = f"{base_url}/local/uber_callback.html"
        else:
            # Fallback
            self.redirect_uri = "https://home.erbarraud.com/local/uber_callback.html"
        
        _LOGGER.info("Using redirect URI: %s", self.redirect_uri)
        
        if user_input is not None:
            # User provided auth code
            self.auth_code = user_input.get("auth_code", "").strip()
            _LOGGER.info("Received auth code, attempting token exchange")
            
            # Exchange code for token
            success = await self._exchange_auth_code()
            if success:
                _LOGGER.info("Token exchange successful, moving to testing step")
                return await self.async_step_test()
            else:
                _LOGGER.error("Token exchange failed")
                return self.async_show_form(
                    step_id="oauth",
                    data_schema=vol.Schema({
                        vol.Required("auth_code"): str,
                    }),
                    errors={"base": "auth_failed"},
                    description_placeholders={
                        "auth_url": self._generate_auth_url(),
                        "redirect_uri": self.redirect_uri,
                    },
                )
        
        # Show OAuth form with auth URL
        auth_url = self._generate_auth_url()
        _LOGGER.info("Showing OAuth form with auth URL")
        
        # Also create a notification with clickable link
        await self._create_auth_notification(auth_url)
        
        return self.async_show_form(
            step_id="oauth",
            data_schema=vol.Schema({
                vol.Required("auth_code"): str,
            }),
            description_placeholders={
                "auth_url": auth_url,
                "redirect_uri": self.redirect_uri,
            },
        )

    async def async_step_test(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Test API access and show results."""
        _LOGGER.info("Starting API test step")
        
        # Run comprehensive tests
        self.test_results = await self._test_api_access()
        
        # Log test results
        _LOGGER.info("API Test Results:")
        for test_name, result in self.test_results.items():
            _LOGGER.info("  %s: %s", test_name, "✅ PASS" if result["success"] else f"❌ FAIL - {result.get('error', 'Unknown error')}")
        
        # Check if all critical tests passed
        critical_tests = ["token_valid", "profile_access", "history_access"]
        all_passed = all(
            self.test_results.get(test, {}).get("success", False)
            for test in critical_tests
        )
        
        if all_passed:
            _LOGGER.info("All critical tests passed, moving to completion")
            # Tests passed, complete setup
            return await self.async_step_complete()
        else:
            _LOGGER.warning("Some tests failed, showing results to user")
            # Show test results and allow retry
            return self.async_show_form(
                step_id="test",
                data_schema=vol.Schema({}),
                errors={"base": "tests_failed"},
                description_placeholders={
                    "test_results": self._format_test_results(),
                },
            )

    async def async_step_complete(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Complete setup and install card."""
        _LOGGER.info("Completing setup")
        
        if user_input is not None:
            # User clicked complete
            _LOGGER.info("Creating config entry")
            
            # Store tokens in data
            data = {
                CONF_CLIENT_ID: self.client_id,
                CONF_CLIENT_SECRET: self.client_secret,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
            }
            
            # Setup card
            await self._setup_card()
            
            return self.async_create_entry(
                title=NAME,
                data=data,
            )
        
        # Show completion form with card setup button
        return self.async_show_form(
            step_id="complete",
            data_schema=vol.Schema({}),
            description_placeholders={
                "test_results": self._format_test_results(),
                "card_info": "Click 'Submit' to complete setup and install the Lovelace card.",
            },
        )

    def _generate_auth_url(self) -> str:
        """Generate OAuth authorization URL."""
        # Don't specify scope - let Uber use default scopes
        # The invalid_scope error suggests Uber doesn't accept the scopes we're requesting
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": "ha_setup"
        }
        _LOGGER.info("Generating auth URL without explicit scopes to avoid invalid_scope error")
        return f"https://login.uber.com/oauth/v2/authorize?{urlencode(params)}"

    async def _exchange_auth_code(self) -> bool:
        """Exchange authorization code for access token."""
        _LOGGER.info("Exchanging auth code for access token")
        
        session = async_get_clientsession(self.hass)
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        try:
            async with session.post(
                "https://login.uber.com/oauth/v2/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get("access_token")
                    self.refresh_token = token_data.get("refresh_token")
                    _LOGGER.info("Successfully obtained access token")
                    _LOGGER.debug("Token scope: %s", token_data.get("scope"))
                    return True
                else:
                    error_text = await response.text()
                    _LOGGER.error("Token exchange failed: HTTP %d - %s", response.status, error_text)
                    return False
        except Exception as e:
            _LOGGER.error("Exception during token exchange: %s", e)
            return False

    async def _test_api_access(self) -> Dict[str, Any]:
        """Test various API endpoints."""
        _LOGGER.info("Testing API access with obtained token")
        
        results = {}
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Validate token
        results["token_valid"] = {
            "name": "Token Validation",
            "success": self.access_token is not None,
            "error": None if self.access_token else "No access token"
        }
        
        # Test 2: Profile access
        try:
            _LOGGER.debug("Testing profile endpoint")
            async with session.get(
                "https://api.uber.com/v1.2/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results["profile_access"] = {
                        "name": "Profile Access",
                        "success": True,
                        "data": {
                            "name": f"{data.get('first_name', '')} {data.get('last_name', '')}",
                            "email": data.get("email", "N/A")
                        }
                    }
                    _LOGGER.info("Profile access successful: %s", data.get("email"))
                else:
                    error = await response.text()
                    results["profile_access"] = {
                        "name": "Profile Access",
                        "success": False,
                        "error": f"HTTP {response.status}: {error[:100]}"
                    }
                    _LOGGER.error("Profile access failed: %s", error)
        except Exception as e:
            results["profile_access"] = {
                "name": "Profile Access",
                "success": False,
                "error": str(e)
            }
            _LOGGER.error("Profile test exception: %s", e)
        
        # Test 3: History access
        try:
            _LOGGER.debug("Testing history endpoint")
            async with session.get(
                "https://api.uber.com/v1.2/history",
                headers=headers,
                params={"limit": 1}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results["history_access"] = {
                        "name": "History Access",
                        "success": True,
                        "data": {"ride_count": data.get("count", 0)}
                    }
                    _LOGGER.info("History access successful: %d rides", data.get("count", 0))
                else:
                    error = await response.text()
                    results["history_access"] = {
                        "name": "History Access",
                        "success": False,
                        "error": f"HTTP {response.status}: {error[:100]}"
                    }
                    _LOGGER.error("History access failed: %s", error)
        except Exception as e:
            results["history_access"] = {
                "name": "History Access",
                "success": False,
                "error": str(e)
            }
            _LOGGER.error("History test exception: %s", e)
        
        # Test 4: Current ride (optional, might fail)
        try:
            _LOGGER.debug("Testing current ride endpoint")
            async with session.get(
                "https://api.uber.com/v1.2/requests/current",
                headers=headers
            ) as response:
                if response.status in [200, 404]:
                    results["current_ride"] = {
                        "name": "Current Ride Access",
                        "success": True,
                        "data": {"has_active": response.status == 200}
                    }
                    _LOGGER.info("Current ride access successful: %s", 
                                "active ride" if response.status == 200 else "no active ride")
                else:
                    error = await response.text()
                    results["current_ride"] = {
                        "name": "Current Ride Access",
                        "success": False,
                        "error": f"Requires 'request' scope (privileged)"
                    }
                    _LOGGER.warning("Current ride access requires privileged scope")
        except Exception as e:
            results["current_ride"] = {
                "name": "Current Ride Access",
                "success": False,
                "error": str(e)
            }
            _LOGGER.error("Current ride test exception: %s", e)
        
        return results

    def _format_test_results(self) -> str:
        """Format test results for display."""
        if not self.test_results:
            return "No tests run yet"
        
        lines = []
        for key, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            name = result.get("name", key)
            lines.append(f"{status} {name}")
            if result.get("data"):
                for k, v in result["data"].items():
                    lines.append(f"   • {k}: {v}")
            if result.get("error"):
                lines.append(f"   ⚠️ {result['error']}")
        
        return "\n".join(lines)

    async def _create_auth_notification(self, auth_url: str):
        """Create a persistent notification with auth URL."""
        _LOGGER.info("Creating auth notification")
        
        message = f"""
## 🔐 Uber Authorization Required

Please authorize the Uber integration:

1. **[Click here to authorize with Uber]({auth_url})**
2. Log in with your Uber account
3. Authorize the app
4. Copy the authorization code from the callback page
5. Paste it in the form below

**Redirect URI configured:** `{self.redirect_uri}`

Make sure this URI is added to your Uber app settings.
        """
        
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Uber Integration Setup",
                "message": message,
                "notification_id": "uber_setup_auth",
            },
        )

    async def _setup_card(self):
        """Setup the Lovelace card."""
        _LOGGER.info("Setting up Lovelace card")
        
        try:
            from pathlib import Path
            import shutil
            
            # Get paths
            www_path = Path(self.hass.config.path("www"))
            integration_dir = Path(__file__).parent
            
            # Create www directory if it doesn't exist
            if not www_path.exists():
                www_path.mkdir(mode=0o755, parents=True, exist_ok=True)
                _LOGGER.info("Created www directory at: %s", www_path)
            
            # Copy card file
            card_source = integration_dir / "www" / "uber-ride-tracker-card.js"
            card_dest = www_path / "uber-ride-tracker-card.js"
            
            if card_source.exists():
                shutil.copy2(str(card_source), str(card_dest))
                card_dest.chmod(0o644)
                _LOGGER.info("Card file copied to: %s", card_dest)
            else:
                _LOGGER.error("Card source file not found: %s", card_source)
            
            # Copy callback HTML
            callback_source = integration_dir / "www" / "uber_callback.html"
            callback_dest = www_path / "uber_callback.html"
            
            if callback_source.exists():
                shutil.copy2(str(callback_source), str(callback_dest))
                callback_dest.chmod(0o644)
                _LOGGER.info("Callback page copied to: %s", callback_dest)
            else:
                _LOGGER.error("Callback source file not found: %s", callback_source)
                
        except Exception as e:
            _LOGGER.error("Error setting up card: %s", e)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return UberRideTrackerOptionsFlow(config_entry)


class UberRideTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Uber Ride Tracker."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "update_interval",
                    default=self.config_entry.options.get("update_interval", 60)
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                vol.Optional(
                    "show_inactive",
                    default=self.config_entry.options.get("show_inactive", False)
                ): bool,
            }),
        )