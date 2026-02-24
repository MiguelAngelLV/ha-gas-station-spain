"""Config flow for Gas Station Spain."""

from __future__ import annotations

import logging
from typing import Any, Self, override

import gas_station_spain_api as gss
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_FIXED_DISCOUNT,
    CONF_MUNICIPALITY,
    CONF_PERCENTAGE_DISCOUNT,
    CONF_PRODUCT,
    CONF_PROVINCE,
    CONF_SHOW_IN_MAP,
    CONF_STATION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gas Station Spain."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the flow."""
        self.province_id: str = ""
        self.product_id: str = ""
        self.municipality_id: str = ""
        self.station_id: str = ""

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionFlowHandler:
        """Get the options flow for this handler."""
        return OptionFlowHandler(config_entry)

    @override
    def is_matching(self, other_flow: Self) -> bool:
        """Return False to allow multiple instances if needed."""
        return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self.product_id = user_input[CONF_PRODUCT]
            self.province_id = user_input[CONF_PROVINCE]
            return await self.async_step_municipality()

        provinces = await gss.get_provinces()
        options_provinces = [
            SelectOptionDict(label=p.name, value=str(p.id)) for p in provinces
        ]

        products = gss.get_products()
        options_products = [
            SelectOptionDict(label=p.name, value=str(p.id)) for p in products
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_PRODUCT): SelectSelector(
                    SelectSelectorConfig(
                        options=options_products,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_PROVINCE): SelectSelector(
                    SelectSelectorConfig(
                        options=options_provinces,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, last_step=False)

    async def async_step_municipality(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Municipality selection."""
        if user_input is not None:
            self.municipality_id = user_input[CONF_MUNICIPALITY]
            return await self.async_step_station()

        municipalities = await gss.get_municipalities(id_province=self.province_id)
        options = [
            SelectOptionDict(label=m.name, value=str(m.id)) for m in municipalities
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_MUNICIPALITY): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="municipality", data_schema=schema)

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gas Station selection."""
        if user_input is not None:
            self.station_id = user_input[CONF_STATION]
            return await self.async_step_options()

        stations = await gss.get_gas_stations(
            municipality_id=int(self.municipality_id),
            product_id=int(self.product_id),
            province_id=int(self.province_id),
        )
        options = [
            SelectOptionDict(label=f"{s.marquee} - {s.address}", value=str(s.id))
            for s in stations
        ]

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="station", data_schema=schema)

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Final configuration step."""
        if user_input is not None:
            station = await gss.get_gas_station(self.station_id)
            product = next(
                p for p in gss.get_products() if p.id == int(self.product_id)
            )

            unique_id = f"{self.product_id}-{station.id}"
            name = f"{product.name}, {station.marquee} ({station.address})"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=name,
                data={
                    CONF_PRODUCT: self.product_id,
                    CONF_MUNICIPALITY: self.municipality_id,
                    CONF_STATION: self.station_id,
                    CONF_FIXED_DISCOUNT: user_input[CONF_FIXED_DISCOUNT],
                    CONF_PERCENTAGE_DISCOUNT: user_input[CONF_PERCENTAGE_DISCOUNT],
                    CONF_SHOW_IN_MAP: user_input[CONF_SHOW_IN_MAP],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_FIXED_DISCOUNT, default=0.0): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=1,
                        step=0.01,
                        unit_of_measurement="€",
                        mode=NumberSelectorMode.SLIDER,
                    ),
                ),
                vol.Required(CONF_PERCENTAGE_DISCOUNT, default=0.0): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=100,
                        step=0.01,
                        unit_of_measurement="%",
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(CONF_SHOW_IN_MAP, default=False): cv.boolean,
            }
        )
        return self.async_show_form(step_id="options", data_schema=schema)


class OptionFlowHandler(config_entries.OptionsFlow):
    """Handle options for the integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Usar .get() tanto en options como en data para asegurar que siempre haya un valor
        fixed = self.config_entry.options.get(
            CONF_FIXED_DISCOUNT, self.config_entry.data.get(CONF_FIXED_DISCOUNT, 0.0)
        )
        percentage = self.config_entry.options.get(
            CONF_PERCENTAGE_DISCOUNT,
            self.config_entry.data.get(CONF_PERCENTAGE_DISCOUNT, 0.0),
        )
        show_in_map = self.config_entry.options.get(
            CONF_SHOW_IN_MAP, self.config_entry.data.get(CONF_SHOW_IN_MAP, False)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_FIXED_DISCOUNT, default=float(fixed)): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=1,
                        step=0.01,
                        unit_of_measurement="€",
                        mode=NumberSelectorMode.SLIDER,
                    ),
                ),
                vol.Required(
                    CONF_PERCENTAGE_DISCOUNT, default=float(percentage)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=100,
                        step=0.01,
                        unit_of_measurement="%",
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(CONF_SHOW_IN_MAP, default=show_in_map): cv.boolean,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
