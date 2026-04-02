"""Gas Station Spain"""

from __future__ import annotations


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_FIXED_DISCOUNT,
    CONF_PERCENTAGE_DISCOUNT,
    CONF_SHOW_IN_MAP,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup a config entry."""

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def _async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""

    hass.config_entries.async_update_entry(config_entry, data={**config_entry.data, **config_entry.options})
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry):
    """Migrate entry configuration."""

    version = config_entry.version

    if version == 1:
        data = {
            **config_entry.data,
            CONF_FIXED_DISCOUNT: 0.0,
            CONF_PERCENTAGE_DISCOUNT: 0.0,
            CONF_SHOW_IN_MAP: False,
        }

        hass.config_entries.async_update_entry(config_entry, data=data, version=2)

    return True
