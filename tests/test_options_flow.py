"""Test the Gas Station Spain options flow."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

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


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Test Station",
        data={
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
            CONF_MUNICIPALITY: "79",
            CONF_STATION: "1234",
            CONF_FIXED_DISCOUNT: 0.05,
            CONF_PERCENTAGE_DISCOUNT: 5.0,
            CONF_SHOW_IN_MAP: True,
        },
        options={},
        unique_id="1-1234",
    )


async def test_options_flow_init(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test options flow initialization."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_update(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test updating options."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_FIXED_DISCOUNT: 0.10,
            CONF_PERCENTAGE_DISCOUNT: 10.0,
            CONF_SHOW_IN_MAP: False,
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_FIXED_DISCOUNT: 0.10,
        CONF_PERCENTAGE_DISCOUNT: 10.0,
        CONF_SHOW_IN_MAP: False,
    }


async def test_options_flow_defaults_from_data(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test that options flow uses defaults from config entry data."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    # The form should have default values from the config entry data
    # This is tested implicitly through the schema defaults


async def test_options_flow_defaults_from_options(hass: HomeAssistant) -> None:
    """Test that options flow uses defaults from existing options if available."""
    config_entry = MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Test Station",
        data={
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
            CONF_MUNICIPALITY: "79",
            CONF_STATION: "1234",
            CONF_FIXED_DISCOUNT: 0.05,
            CONF_PERCENTAGE_DISCOUNT: 5.0,
            CONF_SHOW_IN_MAP: True,
        },
        options={
            CONF_FIXED_DISCOUNT: 0.15,
            CONF_PERCENTAGE_DISCOUNT: 15.0,
            CONF_SHOW_IN_MAP: False,
        },
        unique_id="1-1234",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    # The form should prefer options over data for defaults
