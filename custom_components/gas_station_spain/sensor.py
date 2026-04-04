"""Gas Station sensor platform."""

import logging
from datetime import timedelta
from typing import Mapping, Any

from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.const import (
    CURRENCY_EURO,
)

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

import gas_station_spain_api as gss

from .const import (
    CONF_STATION,
    CONF_PRODUCT,
    UPDATE_INTERVAL,
    CONF_FIXED_DISCOUNT,
    CONF_PERCENTAGE_DISCOUNT,
    CONF_SHOW_IN_MAP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Gas Station Spain sensor setup."""
    show_in_map = entry.data[CONF_SHOW_IN_MAP]
    product_id = int(entry.data[CONF_PRODUCT])
    gas_station_id = int(entry.data[CONF_STATION])
    fixed_discount = entry.data[CONF_FIXED_DISCOUNT]
    percentage_discount = entry.data[CONF_PERCENTAGE_DISCOUNT]

    _LOGGER.info("Creating Gas Station Spain sensor with station=%s and product=%s", gas_station_id, product_id)

    coordinator = GasStationCoordinator(hass=hass, gas_station_id=gas_station_id, product_id=product_id)

    # Intentar la primera actualización pero no fallar si hay error
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # pylint: disable=W0718
        _LOGGER.warning("Could not fetch initial data for station=%s: %s. Will use restored state if available.", gas_station_id, err)

    sensor = GasStationSensor(
        entry.title,
        entry.unique_id,
        fixed_discount,
        percentage_discount,
        show_in_map,
        coordinator,
    )
    async_add_entities([sensor])


class GasStationCoordinator(DataUpdateCoordinator):
    """API access coordinator."""

    def __init__(self, hass: HomeAssistant, gas_station_id, product_id):
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Gas Station",
            update_interval=timedelta(hours=UPDATE_INTERVAL),
        )
        self._price = None
        self._address = None
        self._latitude = None
        self._longitude = None
        self._gas_station_id = gas_station_id
        self._product_id = product_id

    async def async_config_entry_first_refresh(self) -> None:
        try:
            gas_station = await gss.get_gas_station(self._gas_station_id)
            self._address = gas_station.address
            self._latitude = gas_station.latitude
            self._longitude = gas_station.longitude
        except Exception as err:  # pylint: disable=W0718
            _LOGGER.warning("Could not fetch gas station data for station=%s: %s", self._gas_station_id, err)

        await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        try:
            self._price = await gss.get_price(station_id=self._gas_station_id, product_id=self._product_id)
            _LOGGER.debug("Updated station=%s and product=%s with original price=%s", self._gas_station_id, self._product_id, self._price)
        except Exception:  # pylint: disable=W0718
            _LOGGER.exception("Updated station=%s and product=%s", self._gas_station_id, self._product_id)

        return {
            "price": self._price,
            "address": self._address,
            "latitude": self._latitude,
            "longitude": self._longitude,
        }


# pylint: disable=R0913,R0902,R0917
class GasStationSensor(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Gas Station Sensor."""

    def __init__(
        self,
        name: str,
        unique_id: str,
        fixed_discount: float,
        percentage_discount: float,
        show_in_map: bool,
        coordinator: GasStationCoordinator,
    ):
        super().__init__(coordinator=coordinator)
        self._state = None
        self._original_price = None
        self._fixed_discount = fixed_discount
        self._percentage_discount = percentage_discount
        self._attrs: dict[str, Any] = {}
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._show_in_map = show_in_map
        self.entity_description = SensorEntityDescription(
            key=name,
            icon="mdi:gas-station",
            native_unit_of_measurement=CURRENCY_EURO,
            state_class=SensorStateClass.MEASUREMENT,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Restaurar el último estado conocido si está disponible
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._state = float(last_state.state)
                if last_state.attributes:
                    self._attrs = dict(last_state.attributes)
                _LOGGER.debug("Restored previous state: %s with attributes: %s", self._state, self._attrs)
            except (ValueError, TypeError) as err:
                _LOGGER.warning("Could not restore previous state: %s", err)

        # Actualizar con datos actuales del coordinador si están disponibles
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is None:
            _LOGGER.debug("No data available from coordinator yet")
            return

        data = self.coordinator.data

        # Solo actualizar si tenemos un precio válido
        if data.get("price") is not None:
            self._state = (data["price"] - self._fixed_discount) * (1.0 - self._percentage_discount / 100.0)
            self._attrs["Precio Original"] = data["price"]

        # Actualizar dirección si está disponible
        if data.get("address") is not None:
            self._attrs["Dirección"] = data["address"]

        # Actualizar coordenadas si están disponibles y se debe mostrar en el mapa
        if self._show_in_map:
            if data.get("latitude") is not None:
                self._attrs["latitude"] = data["latitude"]
            if data.get("longitude") is not None:
                self._attrs["longitude"] = data["longitude"]

        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        return self._state

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self._attrs

    @property
    def suggested_display_precision(self) -> int | None:
        return 4
