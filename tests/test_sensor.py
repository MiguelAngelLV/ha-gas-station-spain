"""Test the Gas Station Spain sensor platform."""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

import pytest
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
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
from custom_components.gas_station_spain.sensor import (
    async_setup_entry,
    GasStationCoordinator,
    GasStationSensor,
)


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry for sensor tests."""
    return MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Gasolina 95 E5, Repsol (Calle Ejemplo 123)",
        data={
            CONF_PROVINCE: "28",
            CONF_PRODUCT: "1",
            CONF_MUNICIPALITY: "79",
            CONF_STATION: "1234",
            CONF_FIXED_DISCOUNT: 0.05,
            CONF_PERCENTAGE_DISCOUNT: 5.0,
            CONF_SHOW_IN_MAP: True,
        },
        unique_id="1-1234",
    )


@pytest.fixture
def mock_coordinator(hass: HomeAssistant) -> GasStationCoordinator:
    """Create a mock coordinator."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )
    coordinator.data = {
        "price": 1.459,
        "address": "Calle Ejemplo 123",
        "latitude": 40.4168,
        "longitude": -3.7038,
    }
    return coordinator


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_gas_station,
    mock_get_price,
) -> None:
    """Test sensor platform setup."""
    mock_config_entry.add_to_hass(hass)

    async_add_entities = MagicMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert async_add_entities.called
    assert len(async_add_entities.call_args[0][0]) == 1


async def test_coordinator_init(hass: HomeAssistant) -> None:
    """Test coordinator initialization."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )

    assert coordinator._gas_station_id == 1234
    assert coordinator._product_id == 1
    assert coordinator._price is None
    assert coordinator._address is None


async def test_coordinator_first_refresh(
    hass: HomeAssistant,
    mock_get_gas_station,
    mock_get_price,
) -> None:
    """Test coordinator first refresh."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )

    await coordinator.async_config_entry_first_refresh()

    assert coordinator._address == "Calle Ejemplo 123"
    assert coordinator._latitude == 40.4168
    assert coordinator._longitude == -3.7038


async def test_coordinator_update_data(
    hass: HomeAssistant,
    mock_get_price,
) -> None:
    """Test coordinator update data."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )
    coordinator._address = "Calle Ejemplo 123"
    coordinator._latitude = 40.4168
    coordinator._longitude = -3.7038

    data = await coordinator._async_update_data()

    assert data["price"] == 1.459
    assert data["address"] == "Calle Ejemplo 123"
    assert data["latitude"] == 40.4168
    assert data["longitude"] == -3.7038


async def test_coordinator_update_data_exception(
    hass: HomeAssistant,
) -> None:
    """Test coordinator update data handles exceptions."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )
    coordinator._address = "Calle Ejemplo 123"
    coordinator._latitude = 40.4168
    coordinator._longitude = -3.7038

    with patch(
        "custom_components.gas_station_spain.sensor.gss.get_price",
        side_effect=Exception("Test error"),
    ):
        data = await coordinator._async_update_data()

        # Should return data even if price fetch fails
        assert data["address"] == "Calle Ejemplo 123"
        assert data["price"] is None


async def test_sensor_init(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor initialization."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=True,
        coordinator=mock_coordinator,
    )

    assert sensor._attr_name == "Test Sensor"
    assert sensor._attr_unique_id == "test-unique-id"
    assert sensor._fixed_discount == 0.05
    assert sensor._percentage_discount == 5.0
    assert sensor._show_in_map is True
    assert sensor.entity_description.icon == "mdi:gas-station"
    assert sensor.entity_description.native_unit_of_measurement == CURRENCY_EURO


async def test_sensor_state_calculation(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor state calculation with discounts."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=False,
        coordinator=mock_coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    # Original price: 1.459
    # After fixed discount: 1.459 - 0.05 = 1.409
    # After percentage discount: 1.409 * (1 - 5/100) = 1.409 * 0.95 = 1.33855
    expected_price = (1.459 - 0.05) * (1.0 - 5.0 / 100.0)

    assert sensor.native_value == expected_price
    assert sensor._attrs["Precio Original"] == 1.459
    assert sensor._attrs["Dirección"] == "Calle Ejemplo 123"


async def test_sensor_state_calculation_no_discounts(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor state calculation without discounts."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=mock_coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    assert sensor.native_value == 1.459
    assert sensor._attrs["Precio Original"] == 1.459


async def test_sensor_map_attributes(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor includes map attributes when show_in_map is True."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=True,
        coordinator=mock_coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    assert sensor._attrs["latitude"] == 40.4168
    assert sensor._attrs["longitude"] == -3.7038


async def test_sensor_no_map_attributes(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor excludes map attributes when show_in_map is False."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=mock_coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    assert "latitude" not in sensor._attrs
    assert "longitude" not in sensor._attrs


async def test_sensor_extra_state_attributes(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor extra state attributes."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=True,
        coordinator=mock_coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    attrs = sensor.extra_state_attributes
    assert attrs is not None
    assert "Precio Original" in attrs
    assert "Dirección" in attrs
    assert "latitude" in attrs
    assert "longitude" in attrs


async def test_sensor_display_precision(
    hass: HomeAssistant,
    mock_coordinator: GasStationCoordinator,
) -> None:
    """Test sensor display precision."""
    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=mock_coordinator,
    )

    assert sensor.suggested_display_precision == 4

