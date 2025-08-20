"""Config flow for Uber Ride Tracker integration."""
import logging
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import UberAPI, UberAPIError
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    NAME,
)
from .oauth import UberOAuth2Implementation, UberOAuthManager

_LOGGER = logging.getLogger(__name__)


class UberRideTrackerConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN
):
    """Handle a config flow for Uber Ride Tracker."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data to include in the authorize URL."""
        return {"prompt": "consent"}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID]
            self._client_secret = user_input[CONF_CLIENT_SECRET]

            # Store OAuth implementation
            self.flow_impl = UberOAuth2Implementation(
                self.hass,
                self._client_id,
                self._client_secret,
            )

            # Continue with OAuth flow
            return await self.async_step_pick_implementation()

        data_schema = vol.Schema({
            vol.Required(CONF_CLIENT_ID): str,
            vol.Required(CONF_CLIENT_SECRET): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "docs_url": "https://developer.uber.com/docs/riders/guides/authentication/introduction",
            },
        )

    async def async_step_pick_implementation(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle implementation selection."""
        return await self.async_step_auth()

    async def async_step_auth(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the authorization step."""
        if user_input is not None:
            return await self.async_step_creation(user_input)

        # Generate authorization URL
        auth_url = await self.flow_impl.async_generate_authorize_url(self.flow_id)

        return self.async_external_step(
            step_id="auth",
            url=auth_url,
        )

    async def async_step_creation(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the creation step."""
        # Exchange authorization code for tokens
        token_data = await self.flow_impl.async_resolve_external_data(
            self.external_data
        )

        # Create OAuth manager
        oauth_manager = UberOAuthManager(
            self.hass,
            self._client_id,
            self._client_secret,
            token_data,
        )

        # Create API client
        api = UberAPI(self.hass, oauth_manager)

        # Test the connection and get user profile
        try:
            user_profile = await api.async_get_user_profile()
            user_id = user_profile.get("uuid", "unknown")
            user_email = user_profile.get("email", "unknown")
            
        except UberAPIError as err:
            _LOGGER.error("Failed to get user profile: %s", err)
            return self.async_abort(reason="cannot_connect")

        # Check if already configured
        await self.async_set_unique_id(user_id)
        self._abort_if_unique_id_configured()

        # Create the config entry
        return self.async_create_entry(
            title=f"{NAME} ({user_email})",
            data={
                CONF_CLIENT_ID: self._client_id,
                CONF_CLIENT_SECRET: self._client_secret,
                "token": token_data,
                "user_id": user_id,
                "user_email": user_email,
            },
        )

    async def async_oauth_create_entry(self, data: dict) -> FlowResult:
        """Create an entry for the flow."""
        # This is called by the OAuth2 flow handler
        return await self.async_step_creation(data)