"""Test the Gas Station Spain sensor platform."""

# pylint: disable=protected-access,redefined-outer-name,unused-argument

from unittest.mock import MagicMock, patch

from homeassistant.const import CURRENCY_EURO, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gas_station_spain.const import DOMAIN
from custom_components.gas_station_spain.sensor import (
    async_setup_entry,
    GasStationCoordinator,
    GasStationSensor,
)


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
    mock_get_gas_station,
    mock_get_price,
) -> None:
    """Test sensor platform setup."""
    entry = MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Gasolina 95 E5, Repsol (Calle Ejemplo 123)",
        data=mock_config_entry_data,
        unique_id="1-1234",
    )
    entry.add_to_hass(hass)

    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

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


async def test_sensor_init(hass: HomeAssistant) -> None:
    """Test sensor initialization."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=True,
        coordinator=coordinator,
    )

    assert sensor._attr_name == "Test Sensor"
    assert sensor._attr_unique_id == "test-unique-id"
    assert sensor._fixed_discount == 0.05
    assert sensor._percentage_discount == 5.0
    assert sensor._show_in_map is True
    assert sensor.entity_description.icon == "mdi:gas-station"
    assert sensor.entity_description.native_unit_of_measurement == CURRENCY_EURO


async def test_sensor_state_calculation(hass: HomeAssistant) -> None:
    """Test sensor state calculation with discounts."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=False,
        coordinator=coordinator,
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


async def test_sensor_state_calculation_no_discounts(hass: HomeAssistant) -> None:
    """Test sensor state calculation without discounts."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    assert sensor.native_value == 1.459
    assert sensor._attrs["Precio Original"] == 1.459


async def test_sensor_map_attributes(hass: HomeAssistant) -> None:
    """Test sensor includes map attributes when show_in_map is True."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=True,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    assert sensor._attrs["latitude"] == 40.4168
    assert sensor._attrs["longitude"] == -3.7038


async def test_sensor_no_map_attributes(hass: HomeAssistant) -> None:
    """Test sensor excludes map attributes when show_in_map is False."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    assert "latitude" not in sensor._attrs
    assert "longitude" not in sensor._attrs


async def test_sensor_extra_state_attributes(hass: HomeAssistant) -> None:
    """Test sensor extra state attributes."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=True,
        coordinator=coordinator,
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


async def test_sensor_display_precision(hass: HomeAssistant) -> None:
    """Test sensor display precision."""
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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    assert sensor.suggested_display_precision == 4


async def test_sensor_restore_state(hass: HomeAssistant) -> None:
    """Test sensor restores previous state."""

    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )
    coordinator.data = None  # No hay datos disponibles

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.05,
        percentage_discount=5.0,
        show_in_map=True,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"

    # Simular estado anterior
    with patch.object(
        sensor,
        "async_get_last_state",
        return_value=State(
            entity_id="sensor.test_sensor",
            state="1.350",
            attributes={
                "Precio Original": 1.500,
                "Dirección": "Calle Restaurada, 1",
                "latitude": 40.5,
                "longitude": -3.7,
            },
        ),
    ):
        await sensor.async_added_to_hass()

    # Debe restaurar el estado anterior
    assert sensor.native_value == 1.350
    assert sensor._attrs["Precio Original"] == 1.500
    assert sensor._attrs["Dirección"] == "Calle Restaurada, 1"
    assert sensor._attrs["latitude"] == 40.5
    assert sensor._attrs["longitude"] == -3.7


async def test_sensor_restore_state_invalid(hass: HomeAssistant) -> None:
    """Test sensor handles invalid restored state."""

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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"

    # Simular estado anterior con valor inválido
    with patch.object(
        sensor,
        "async_get_last_state",
        return_value=State(
            entity_id="sensor.test_sensor",
            state="invalid_number",
            attributes={},
        ),
    ):
        await sensor.async_added_to_hass()

    # Debe usar datos actuales en lugar del estado inválido
    assert sensor.native_value == 1.459


async def test_sensor_restore_state_unknown(hass: HomeAssistant) -> None:
    """Test sensor doesn't restore unknown state."""

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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"

    # Simular estado anterior como unknown
    with patch.object(
        sensor,
        "async_get_last_state",
        return_value=State(
            entity_id="sensor.test_sensor",
            state=STATE_UNKNOWN,
            attributes={},
        ),
    ):
        await sensor.async_added_to_hass()

    # Debe usar datos actuales
    assert sensor.native_value == 1.459


async def test_sensor_restore_state_unavailable(hass: HomeAssistant) -> None:
    """Test sensor doesn't restore unavailable state."""

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

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"

    # Simular estado anterior como unavailable
    with patch.object(
        sensor,
        "async_get_last_state",
        return_value=State(
            entity_id="sensor.test_sensor",
            state=STATE_UNAVAILABLE,
            attributes={},
        ),
    ):
        await sensor.async_added_to_hass()

    # Debe usar datos actuales
    assert sensor.native_value == 1.459


async def test_sensor_handle_coordinator_no_data(hass: HomeAssistant) -> None:
    """Test sensor handles coordinator with no data."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )
    coordinator.data = None

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=False,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"

    # No debe fallar con data=None
    sensor._handle_coordinator_update()

    # El estado debe permanecer None
    assert sensor.native_value is None


async def test_sensor_handle_partial_data(hass: HomeAssistant) -> None:
    """Test sensor handles partial coordinator data."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )
    coordinator.data = {
        "price": 1.459,
        "address": None,
        "latitude": None,
        "longitude": None,
    }

    sensor = GasStationSensor(
        name="Test Sensor",
        unique_id="test-unique-id",
        fixed_discount=0.0,
        percentage_discount=0.0,
        show_in_map=True,
        coordinator=coordinator,
    )

    sensor.hass = hass
    sensor.entity_id = "sensor.test_sensor"
    await sensor.async_added_to_hass()

    # Debe actualizar precio pero no otros campos
    assert sensor.native_value == 1.459
    assert sensor._attrs["Precio Original"] == 1.459
    assert "Dirección" not in sensor._attrs
    assert "latitude" not in sensor._attrs
    assert "longitude" not in sensor._attrs


async def test_coordinator_first_refresh_error(
    hass: HomeAssistant,
) -> None:
    """Test coordinator handles first refresh error."""
    coordinator = GasStationCoordinator(
        hass=hass,
        gas_station_id=1234,
        product_id=1,
    )

    # Simular error en get_gas_station
    with (
        patch(
            "custom_components.gas_station_spain.sensor.gss.get_gas_station",
            side_effect=Exception("API Error"),
        ),
        patch(
            "custom_components.gas_station_spain.sensor.gss.get_price",
            return_value=1.459,
        ),
    ):
        # No debe lanzar excepción
        await coordinator.async_config_entry_first_refresh()

    # Los datos de la gasolinera deben ser None
    assert coordinator._address is None
    assert coordinator._latitude is None
    assert coordinator._longitude is None


async def test_setup_entry_with_api_error(
    hass: HomeAssistant,
    mock_config_entry_data: dict,
) -> None:
    """Test setup entry handles API errors gracefully."""
    entry = MockConfigEntry(
        version=2,
        minor_version=0,
        domain=DOMAIN,
        title="Gasolina 95 E5, Repsol (Calle Ejemplo 123)",
        data=mock_config_entry_data,
        unique_id="1-1234",
    )
    entry.add_to_hass(hass)

    async_add_entities = MagicMock()

    # Simular que la API falla
    with (
        patch(
            "custom_components.gas_station_spain.sensor.gss.get_gas_station",
            side_effect=Exception("API Error"),
        ),
        patch(
            "custom_components.gas_station_spain.sensor.gss.get_price",
            side_effect=Exception("API Error"),
        ),
    ):
        # El setup debe completarse sin error
        await async_setup_entry(hass, entry, async_add_entities)

    # El sensor debe crearse aunque la API haya fallado
    assert async_add_entities.called
    assert len(async_add_entities.call_args[0][0]) == 1
