"""Test the Gas Station Spain integration init."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gas_station_spain import (
    async_setup_entry,
    async_unload_entry,
    async_migrate_entry,
)
from custom_components.gas_station_spain.const import (
    DOMAIN,
    CONF_PROVINCE,
    CONF_PRODUCT,
    CONF_MUNICIPALITY,
    CONF_STATION,
    CONF_FIXED_DISCOUNT,
    CONF_PERCENTAGE_DISCOUNT,
    CONF_SHOW_IN_MAP,
)


async def test_setup_entry(hass: HomeAssistant, mock_config_entry_data: dict) -> None:
    """Test setting up the integration."""
    entry = MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Test Station",
        data=mock_config_entry_data,
        unique_id="1-1234",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ):
        assert await async_setup_entry(hass, entry)


async def test_unload_entry(hass: HomeAssistant, mock_config_entry_data: dict) -> None:
    """Test unloading the integration."""
    entry = MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Test Station",
        data=mock_config_entry_data,
        unique_id="1-1234",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload:
        assert await async_unload_entry(hass, entry)
        assert len(mock_unload.mock_calls) == 1


async def test_migrate_entry_from_v1(hass: HomeAssistant) -> None:
    """Test migrating config entry from version 1 to version 2."""
    config_entry = MockConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Station",
        data={
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
            CONF_MUNICIPALITY: "79",
            CONF_STATION: "1234",
        },
        unique_id="1-1234",
    )
    config_entry.add_to_hass(hass)

    assert config_entry.version == 1
    assert await async_migrate_entry(hass, config_entry)
    assert config_entry.version == 2
    assert config_entry.data[CONF_FIXED_DISCOUNT] == 0.0
    assert config_entry.data[CONF_PERCENTAGE_DISCOUNT] == 0.0
    assert config_entry.data[CONF_SHOW_IN_MAP] is False


async def test_migrate_entry_already_v2(hass: HomeAssistant, mock_config_entry_data: dict) -> None:
    """Test migrating config entry that is already version 2."""
    entry = MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Test Station",
        data=mock_config_entry_data,
        unique_id="1-1234",
    )
    entry.add_to_hass(hass)

    assert entry.version == 2
    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
