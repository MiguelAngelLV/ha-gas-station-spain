"""Common fixtures for Gas Station Spain tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from custom_components.gas_station_spain.const import (
    CONF_PROVINCE,
    CONF_PRODUCT,
    CONF_MUNICIPALITY,
    CONF_STATION,
    CONF_FIXED_DISCOUNT,
    CONF_PERCENTAGE_DISCOUNT,
    CONF_SHOW_IN_MAP,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry_data():
    """Return common config entry data."""
    return {
        CONF_PROVINCE: "28",
        CONF_PRODUCT: "1",
        CONF_MUNICIPALITY: "79",
        CONF_STATION: "1234",
        CONF_FIXED_DISCOUNT: 0.05,
        CONF_PERCENTAGE_DISCOUNT: 5.0,
        CONF_SHOW_IN_MAP: True,
    }


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.gas_station_spain.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_province():
    """Mock province object."""
    province = MagicMock()
    province.id = 28
    province.name = "Madrid"
    return province


@pytest.fixture
def mock_municipality():
    """Mock municipality object."""
    municipality = MagicMock()
    municipality.id = 79
    municipality.name = "Madrid"
    return municipality


@pytest.fixture
def mock_product():
    """Mock product object."""
    product = MagicMock()
    product.id = 1
    product.name = "Gasolina 95 E5"
    return product


@pytest.fixture
def mock_gas_station():
    """Mock gas station object."""
    station = MagicMock()
    station.id = 1234
    station.name = "Repsol"
    station.marquee = "Repsol"
    station.address = "Calle Ejemplo 123"
    station.latitude = 40.4168
    station.longitude = -3.7038
    return station


@pytest.fixture
def mock_get_provinces(mock_province):
    """Mock get_provinces API call."""
    with patch("custom_components.gas_station_spain.config_flow.gss.get_provinces") as mock:

        async def async_return():
            return [mock_province]

        mock.side_effect = async_return
        yield mock


@pytest.fixture
def mock_get_products(mock_product):
    """Mock get_products API call."""
    with patch("custom_components.gas_station_spain.config_flow.gss.get_products") as mock:
        mock.return_value = [mock_product]
        yield mock


@pytest.fixture
def mock_get_municipalities(mock_municipality):
    """Mock get_municipalities API call."""
    with patch("custom_components.gas_station_spain.config_flow.gss.get_municipalities") as mock:

        async def async_return(*args, **kwargs):
            return [mock_municipality]

        mock.side_effect = async_return
        yield mock


@pytest.fixture
def mock_get_gas_stations(mock_gas_station):
    """Mock get_gas_stations API call."""
    with patch("custom_components.gas_station_spain.config_flow.gss.get_gas_stations") as mock:

        async def async_return(*args, **kwargs):
            return [mock_gas_station]

        mock.side_effect = async_return
        yield mock


@pytest.fixture
def mock_get_gas_station(mock_gas_station):
    """Mock get_gas_station API call."""
    with patch("custom_components.gas_station_spain.config_flow.gss.get_gas_station") as mock:

        async def async_return(*args, **kwargs):
            return mock_gas_station

        mock.side_effect = async_return
        yield mock


@pytest.fixture
def mock_get_price():
    """Mock get_price API call."""
    with patch("custom_components.gas_station_spain.sensor.gss.get_price") as mock:

        async def async_return(*args, **kwargs):
            return 1.459

        mock.side_effect = async_return
        yield mock
