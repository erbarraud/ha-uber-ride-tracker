"""OAuth implementation for Uber API."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import aiohttp
import jwt
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    OAUTH2_AUTHORIZE_URL,
    OAUTH2_TOKEN_URL,
    OAUTH2_SCOPES,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES,
    ERROR_AUTH_FAILED,
    ERROR_TOKEN_EXPIRED,
)

_LOGGER = logging.getLogger(__name__)


class UberOAuth2Implementation(config_entry_oauth2_flow.AbstractOAuth2Implementation):
    """Uber OAuth2 implementation."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
    ) -> None:
        """Initialize Uber OAuth2 implementation."""
        self.hass = hass
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return "Uber"

    @property
    def domain(self) -> str:
        """Domain of the implementation."""
        return "uber_ride_tracker"

    async def async_resolve_external_data(self, external_data: Any) -> dict:
        """Resolve external data to tokens."""
        return await self._async_token_request(
            {
                "grant_type": "authorization_code",
                "code": external_data,
            }
        )

    async def async_refresh_token(self, token: dict) -> dict:
        """Refresh a token."""
        return await self._async_token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": token[CONF_REFRESH_TOKEN],
            }
        )

    async def _async_token_request(self, data: dict) -> dict:
        """Make a token request."""
        session = async_get_clientsession(self.hass)
        
        data.update({
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        })

        try:
            async with session.post(
                OAUTH2_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                resp.raise_for_status()
                token_data = await resp.json()
                
                # Calculate token expiration
                expires_in = token_data.get("expires_in", 3600)
                token_data[CONF_TOKEN_EXPIRES] = (
                    datetime.now() + timedelta(seconds=expires_in)
                ).isoformat()
                
                return token_data
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Error requesting token: %s", err)
            raise

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data to include in authorization URL."""
        return {
            # Don't include scope to avoid invalid_scope error
            # Uber will use default scopes from app configuration
            "response_type": "code",
        }

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """Generate the authorize URL."""
        redirect_uri = self._generate_redirect_uri()
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            # Don't include scope - let Uber use app defaults
            "state": flow_id,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{OAUTH2_AUTHORIZE_URL}?{query_string}"

    def _generate_redirect_uri(self) -> str:
        """Generate redirect URI."""
        # This should be configured based on your Home Assistant instance
        return "https://my.home-assistant.io/redirect/oauth"


class UberOAuthManager:
    """Manager for Uber OAuth tokens."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        token_data: Dict[str, Any],
    ) -> None:
        """Initialize the OAuth manager."""
        self.hass = hass
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_data = token_data
        self._session = async_get_clientsession(hass)

    @property
    def access_token(self) -> str:
        """Get the current access token."""
        return self._token_data.get(CONF_ACCESS_TOKEN, "")

    @property
    def refresh_token(self) -> str:
        """Get the refresh token."""
        return self._token_data.get(CONF_REFRESH_TOKEN, "")

    def is_token_expired(self) -> bool:
        """Check if the token is expired."""
        expires_str = self._token_data.get(CONF_TOKEN_EXPIRES)
        if not expires_str:
            return True
            
        try:
            expires = datetime.fromisoformat(expires_str)
            # Consider token expired 5 minutes before actual expiration
            return datetime.now() >= expires - timedelta(minutes=5)
        except (ValueError, TypeError):
            return True

    async def async_ensure_valid_token(self) -> str:
        """Ensure we have a valid token, refreshing if necessary."""
        if self.is_token_expired():
            await self.async_refresh_access_token()
        return self.access_token

    async def async_refresh_access_token(self) -> None:
        """Refresh the access token."""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        try:
            async with self._session.post(
                OAUTH2_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                resp.raise_for_status()
                token_data = await resp.json()
                
                # Update token data
                self._token_data[CONF_ACCESS_TOKEN] = token_data.get("access_token")
                if "refresh_token" in token_data:
                    self._token_data[CONF_REFRESH_TOKEN] = token_data["refresh_token"]
                    
                expires_in = token_data.get("expires_in", 3600)
                self._token_data[CONF_TOKEN_EXPIRES] = (
                    datetime.now() + timedelta(seconds=expires_in)
                ).isoformat()
                
                _LOGGER.debug("Successfully refreshed access token")
                
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to refresh token: %s", err)
            raise

    def get_authorization_header(self) -> Dict[str, str]:
        """Get authorization header for API requests."""
        return {"Authorization": f"Bearer {self.access_token}"}

    async def async_revoke_token(self) -> None:
        """Revoke the current token."""
        # Uber API doesn't have a revoke endpoint, so we just clear local data
        self._token_data.clear()
        _LOGGER.info("Token data cleared")