"""Config flow for Uber Ride Tracker integration."""
import logging
from typing import Any, Dict, Optional
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.components import persistent_notification

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    NAME,
)
from .setup_helper import UberAPISetupHelper, SetupWizard, simplify_setup_flow

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("setup_mode"): vol.In({
        "guided": "🎯 Guided Setup (Recommended) - I'll help you step by step",
        "manual": "⚡ Quick Setup - I already have my API credentials"
    })
})

STEP_CREDENTIALS_SCHEMA = vol.Schema({
    vol.Required(CONF_CLIENT_ID): str,
    vol.Required(CONF_CLIENT_SECRET): str,
})


class UberRideTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Uber Ride Tracker."""

    VERSION = 2
    
    def __init__(self):
        """Initialize the config flow."""
        self.setup_helper = None
        self.redirect_uri = None
        self.client_id = None
        self.client_secret = None

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step - choose setup mode."""
        if user_input is not None:
            if user_input["setup_mode"].startswith("🎯"):
                # Guided setup
                return await self.async_step_guided_start()
            else:
                # Manual setup
                return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={
                "intro": "Let's get your Uber Ride Tracker set up!"
            },
        )

    async def async_step_guided_start(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Start guided setup process."""
        if user_input is not None:
            return await self.async_step_guided_account()

        # Initialize setup helper
        self.setup_helper = UberAPISetupHelper(self.hass)
        self.redirect_uri = await self.setup_helper.get_redirect_uri()
        
        # Create helpful notification
        await self.setup_helper.create_quick_setup_notification()

        return self.async_show_form(
            step_id="guided_start",
            data_schema=vol.Schema({}),
            description_placeholders={
                "message": f"""
# 🚗 Welcome to Uber Ride Tracker Setup!

I'll guide you through getting your Uber API credentials in just 4 easy steps:

1. **Create a free Uber Developer account** (2 minutes)
2. **Create an app** in your dashboard (1 minute)  
3. **Add your redirect URI** (I'll provide it)
4. **Copy your credentials** to Home Assistant

## 📋 Important: Your Redirect URI

I've detected your Home Assistant's redirect URI:
```
{self.redirect_uri}
```

This has been copied to your clipboard and you'll need it in Step 3.

**Ready to start?** Click Continue below!
                """
            },
        )

    async def async_step_guided_account(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Guide through account creation."""
        if user_input is not None:
            if user_input.get("has_account"):
                return await self.async_step_guided_app()
            else:
                return await self.async_step_guided_create_account()

        return self.async_show_form(
            step_id="guided_account",
            data_schema=vol.Schema({
                vol.Required("has_account", default=False): bool,
            }),
            description_placeholders={
                "message": """
# Step 1: Uber Developer Account

Do you already have an Uber Developer account?

- **Yes** → Let's create your app
- **No** → I'll help you sign up (it's free!)
                """
            },
        )

    async def async_step_guided_create_account(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Guide through account creation."""
        if user_input is not None:
            return await self.async_step_guided_app()

        return self.async_show_form(
            step_id="guided_create_account",
            data_schema=vol.Schema({
                vol.Optional("understood", default=True): bool,
            }),
            description_placeholders={
                "message": """
# Creating Your Uber Developer Account

1. **[Click here to open Uber Developer Signup](https://developer.uber.com/signup)** 
2. Click "**Sign Up**" button
3. Use your regular Uber account email (or create new)
4. Verify your email address
5. Come back here and click Continue

⏱️ **This takes about 2 minutes**

The signup page has been opened in a new tab. Once you've created your account and verified your email, click Continue below.
                """,
                "signup_url": "https://developer.uber.com/signup"
            },
        )

    async def async_step_guided_app(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Guide through app creation."""
        if user_input is not None:
            return await self.async_step_guided_redirect()

        return self.async_show_form(
            step_id="guided_app",
            data_schema=vol.Schema({
                vol.Optional("app_created", default=False): bool,
            }),
            description_placeholders={
                "message": f"""
# Step 2: Create Your Uber App

1. **[Click here to open the App Creation page](https://developer.uber.com/dashboard/create)**
2. Fill in these details:
   - **App Name**: `Home Assistant Ride Tracker` (or any name you like)
   - **Description**: `Personal ride tracking for Home Assistant`
   - **Use Case**: Select "Personal Use" or "Rides"
3. Click "**Create App**"
4. Your app will be created instantly

⏱️ **This takes about 1 minute**

Once your app is created, click Continue below.
                """,
                "create_url": "https://developer.uber.com/dashboard/create"
            },
        )

    async def async_step_guided_redirect(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Guide through redirect URI setup."""
        if user_input is not None:
            return await self.async_step_guided_credentials()

        return self.async_show_form(
            step_id="guided_redirect",
            data_schema=vol.Schema({
                vol.Optional("redirect_added", default=False): bool,
            }),
            description_placeholders={
                "message": f"""
# Step 3: Add Your Redirect URI

1. **[Open your Uber App Dashboard](https://developer.uber.com/dashboard)**
2. Click on your app name
3. Go to the "**Auth**" or "**OAuth**" section
4. Find "**Redirect URIs**" field
5. Add this exact URL:

```
{self.redirect_uri}
```

6. Click "**Save**" or "**Update**"

⚠️ **Important**: Copy and paste the URL exactly as shown above. It has been copied to your clipboard!

Once you've added the redirect URI and saved, click Continue below.
                """,
                "redirect_uri": self.redirect_uri,
                "dashboard_url": "https://developer.uber.com/dashboard"
            },
        )

    async def async_step_guided_credentials(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Get credentials from user."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate credentials
            helper = UberAPISetupHelper(self.hass)
            validation = await helper.validate_credentials(
                user_input[CONF_CLIENT_ID],
                user_input[CONF_CLIENT_SECRET]
            )
            await helper.cleanup()

            if validation["valid"]:
                # Set unique ID to prevent duplicate entries
                await self.async_set_unique_id(f"uber_{user_input[CONF_CLIENT_ID]}")
                self._abort_if_unique_id_configured()
                
                # Clear setup notification
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": f"{DOMAIN}_setup_guide"},
                    blocking=False
                )
                
                # Create success notification
                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "✅ Uber Ride Tracker Setup Complete!",
                        "message": "Your integration is ready to use. OAuth authentication will be initiated when needed.",
                        "notification_id": f"{DOMAIN}_setup_complete",
                    },
                    blocking=False
                )
                
                return self.async_create_entry(
                    title=NAME,
                    data={
                        CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                        CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                    },
                )
            else:
                errors["base"] = "invalid_auth"
                if validation.get("suggestions"):
                    errors["base"] = validation["suggestions"][0]

        return self.async_show_form(
            step_id="guided_credentials",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "message": """
# Step 4: Enter Your API Credentials

1. **[Open your Uber Dashboard](https://developer.uber.com/dashboard)**
2. Click on your app
3. Find and copy these two values:

## Client ID
- Looks like: `RkJB3tFGd9fDlJN5GlQzTg`
- Usually 22-32 characters long

## Client Secret  
- Looks like: `7FJ9ggMZCtqyxH4n2Mn1NzLf3Uv2wXYZ5KJbqAdF`
- Keep this secret! Never share it.

Paste them below:
                """,
                "dashboard_url": "https://developer.uber.com/dashboard"
            },
        )

    async def async_step_manual(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle manual setup with credentials."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate credentials format
                helper = UberAPISetupHelper(self.hass)
                validation = await helper.validate_credentials(
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET]
                )
                await helper.cleanup()

                if validation["valid"]:
                    # Set unique ID
                    await self.async_set_unique_id(f"uber_{user_input[CONF_CLIENT_ID]}")
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=NAME,
                        data={
                            CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                            CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET],
                        },
                    )
                else:
                    errors["base"] = "invalid_auth"
                    
            except Exception as err:
                _LOGGER.error("Unexpected error: %s", err)
                errors["base"] = "unknown"

        # Get redirect URI for display
        helper = UberAPISetupHelper(self.hass)
        redirect_uri = await helper.get_redirect_uri()
        await helper.cleanup()

        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_CREDENTIALS_SCHEMA,
            errors=errors,
            description_placeholders={
                "redirect_uri": redirect_uri,
                "dashboard_url": "https://developer.uber.com/dashboard",
                "docs_url": "https://developer.uber.com/docs/riders/guides/authentication/introduction",
            },
        )

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
            description_placeholders={
                "current_interval": self.config_entry.options.get("update_interval", 60)
            },
        )