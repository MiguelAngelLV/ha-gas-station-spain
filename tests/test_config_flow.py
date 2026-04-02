"""Test the Gas Station Spain config flow."""

# pylint: disable=unused-argument,too-many-arguments,too-many-positional-arguments

from unittest.mock import patch

from gas_station_spain_api.exceptions import GasStationServerUnavailableException
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

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


async def test_form_user_step(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_form_user_step_with_input(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
    mock_get_municipalities,
) -> None:
    """Test user step with input goes to municipality step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "municipality"


async def test_form_municipality_step(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
    mock_get_municipalities,
    mock_get_gas_stations,
) -> None:
    """Test municipality step goes to station step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
        },
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_MUNICIPALITY: "79",
        },
    )
    await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "station"


async def test_form_station_step(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
    mock_get_municipalities,
    mock_get_gas_stations,
) -> None:
    """Test station step goes to options step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
        },
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_MUNICIPALITY: "79",
        },
    )

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_STATION: "1234",
        },
    )
    await hass.async_block_till_done()

    assert result4["type"] == FlowResultType.FORM
    assert result4["step_id"] == "options"


async def test_full_flow_success(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
    mock_get_municipalities,
    mock_get_gas_stations,
    mock_get_gas_station,
    mock_setup_entry,
) -> None:
    """Test a successful complete configuration flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
        },
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_MUNICIPALITY: "79",
        },
    )

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_STATION: "1234",
        },
    )

    result5 = await hass.config_entries.flow.async_configure(
        result4["flow_id"],
        {
            CONF_FIXED_DISCOUNT: 0.05,
            CONF_PERCENTAGE_DISCOUNT: 5.0,
            CONF_SHOW_IN_MAP: True,
        },
    )
    await hass.async_block_till_done()

    assert result5["type"] == FlowResultType.CREATE_ENTRY
    assert result5["title"] == "Gasolina 95 E5, Repsol (Calle Ejemplo 123)"
    assert result5["data"] == {
        CONF_PRODUCT: "1",
        CONF_MUNICIPALITY: "79",
        CONF_STATION: "1234",
        CONF_FIXED_DISCOUNT: 0.05,
        CONF_PERCENTAGE_DISCOUNT: 5.0,
        CONF_SHOW_IN_MAP: True,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_server_unavailable_on_user_step(
    hass: HomeAssistant,
    mock_get_products,
) -> None:
    """Test server unavailable error on user step."""
    with patch(
        "custom_components.gas_station_spain.config_flow.gss.get_provinces",
        side_effect=GasStationServerUnavailableException("Server error"),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "server_unavailable"


async def test_server_unavailable_on_municipality_step(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
) -> None:
    """Test server unavailable error on municipality step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.gas_station_spain.config_flow.gss.get_municipalities",
        side_effect=GasStationServerUnavailableException("Server error"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROVINCE: "28",
                CONF_PRODUCT: "1",
            },
        )

        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "server_unavailable"


async def test_server_unavailable_on_station_step(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
    mock_get_municipalities,
) -> None:
    """Test server unavailable error on station step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
        },
    )

    with patch(
        "custom_components.gas_station_spain.config_flow.gss.get_gas_stations",
        side_effect=GasStationServerUnavailableException("Server error"),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_MUNICIPALITY: "79",
            },
        )

        assert result3["type"] == FlowResultType.ABORT
        assert result3["reason"] == "server_unavailable"


async def test_server_unavailable_on_options_step(
    hass: HomeAssistant,
    mock_get_provinces,
    mock_get_products,
    mock_get_municipalities,
    mock_get_gas_stations,
) -> None:
    """Test server unavailable error on options step."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
        },
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_MUNICIPALITY: "79",
        },
    )

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {
            CONF_STATION: "1234",
        },
    )

    with patch(
        "custom_components.gas_station_spain.config_flow.gss.get_gas_station",
        side_effect=GasStationServerUnavailableException("Server error"),
    ):
        result5 = await hass.config_entries.flow.async_configure(
            result4["flow_id"],
            {
                CONF_FIXED_DISCOUNT: 0.05,
                CONF_PERCENTAGE_DISCOUNT: 5.0,
                CONF_SHOW_IN_MAP: True,
            },
        )

        assert result5["type"] == FlowResultType.ABORT
        assert result5["reason"] == "server_unavailable"
