"""Migration handlers for configuration updates."""
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ACCESS_TOKEN, CONF_CLIENT_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Migration version tracking
CURRENT_CONFIG_VERSION = 2


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entries to new version."""
    _LOGGER.info(
        "Migrating %s configuration from version %s to %s",
        DOMAIN,
        config_entry.version,
        CURRENT_CONFIG_VERSION,
    )

    if config_entry.version == 1:
        # Example migration from v1 to v2
        new_data = {**config_entry.data}
        new_options = {**config_entry.options}
        
        # Migrate old field names to new ones
        if "uber_client_id" in new_data:
            new_data[CONF_CLIENT_ID] = new_data.pop("uber_client_id")
        
        # Add new required fields with defaults
        if "polling_interval" not in new_options:
            new_options["polling_interval"] = 60
        
        # Update the config entry
        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            options=new_options,
            version=2,
        )
        
        _LOGGER.info("Migration to version %s successful", 2)

    return True


def migrate_device_identifiers(
    hass: HomeAssistant, entry_id: str, old_identifier: tuple, new_identifier: tuple
) -> None:
    """Migrate device identifiers when structure changes."""
    device_registry = hass.helpers.device_registry.async_get(hass)
    device = device_registry.async_get_device(identifiers={old_identifier})
    
    if device:
        device_registry.async_update_device(
            device.id,
            new_identifiers={new_identifier},
        )
        _LOGGER.info(
            "Migrated device identifier from %s to %s",
            old_identifier,
            new_identifier,
        )


def cleanup_orphaned_entities(hass: HomeAssistant, entry_id: str) -> None:
    """Remove entities that are no longer needed after an update."""
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    
    # List of old entity IDs that should be removed
    deprecated_entities = [
        f"{DOMAIN}.old_sensor_name",
        f"{DOMAIN}.deprecated_entity",
    ]
    
    for entity_id in deprecated_entities:
        if entity := entity_registry.async_get(entity_id):
            if entity.config_entry_id == entry_id:
                entity_registry.async_remove(entity_id)
                _LOGGER.info("Removed deprecated entity: %s", entity_id)


async def async_handle_breaking_changes(
    hass: HomeAssistant, config_entry: ConfigEntry, old_version: str, new_version: str
) -> Dict[str, Any]:
    """Handle breaking changes between versions."""
    breaking_changes = {}
    
    # Check for breaking changes between specific versions
    if old_version.startswith("0.") and new_version.startswith("1."):
        breaking_changes["oauth_required"] = True
        breaking_changes["message"] = (
            "Version 1.0.0 requires OAuth authentication. "
            "Please reconfigure the integration with your Uber API credentials."
        )
        
        # Show persistent notification
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"{DOMAIN.title()} Breaking Changes",
                "message": breaking_changes["message"],
                "notification_id": f"{DOMAIN}_breaking_changes",
            },
        )
    
    return breaking_changes


async def async_check_config_compatibility(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Check if the current config is compatible with the new version."""
    required_fields = [CONF_CLIENT_ID, "client_secret"]
    
    for field in required_fields:
        if field not in config_entry.data:
            _LOGGER.error(
                "Configuration is missing required field: %s. "
                "Please reconfigure the integration.",
                field
            )
            return False
    
    return True


async def async_create_backup_before_update(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> Dict[str, Any]:
    """Create a backup of the current configuration before updating."""
    backup = {
        "version": config_entry.version,
        "data": dict(config_entry.data),
        "options": dict(config_entry.options),
        "unique_id": config_entry.unique_id,
    }
    
    # Store backup in hass.data for potential rollback
    hass.data.setdefault(f"{DOMAIN}_backups", {})[config_entry.entry_id] = backup
    
    _LOGGER.info("Created configuration backup for %s", config_entry.entry_id)
    return backup


async def async_rollback_migration(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Rollback to previous configuration if migration fails."""
    backup_key = f"{DOMAIN}_backups"
    
    if backup_key in hass.data and config_entry.entry_id in hass.data[backup_key]:
        backup = hass.data[backup_key][config_entry.entry_id]
        
        hass.config_entries.async_update_entry(
            config_entry,
            data=backup["data"],
            options=backup["options"],
            version=backup["version"],
        )
        
        _LOGGER.warning(
            "Rolled back configuration to version %s due to migration failure",
            backup["version"],
        )
        return True
    
    return False