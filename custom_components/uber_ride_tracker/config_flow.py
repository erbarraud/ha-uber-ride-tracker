"""Config flow for Uber Ride Tracker integration."""
import logging
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

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

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate the credentials format
                client_id = user_input[CONF_CLIENT_ID].strip()
                client_secret = user_input[CONF_CLIENT_SECRET].strip()
                
                # Basic validation
                if len(client_id) < 10:
                    errors["base"] = "invalid_client_id"
                elif len(client_secret) < 10:
                    errors["base"] = "invalid_client_secret"
                else:
                    # Set unique ID to prevent duplicate entries
                    await self.async_set_unique_id(f"uber_{client_id}")
                    self._abort_if_unique_id_configured()
                    
                    # Create the config entry
                    return self.async_create_entry(
                        title=NAME,
                        data={
                            CONF_CLIENT_ID: client_id,
                            CONF_CLIENT_SECRET: client_secret,
                        },
                    )
            except Exception as err:
                _LOGGER.error("Unexpected error: %s", err)
                errors["base"] = "unknown"

        # Get the external URL for the redirect URI
        redirect_uri = "https://my.home-assistant.io/redirect/oauth"
        if self.hass.config.external_url:
            redirect_uri = f"{self.hass.config.external_url}/auth/external/callback"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "redirect_uri": redirect_uri,
                "dashboard_url": "https://developer.uber.com/dashboard",
                "signup_url": "https://developer.uber.com/signup",
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
        )