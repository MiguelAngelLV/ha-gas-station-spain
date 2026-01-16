"""Gas Station Spain Config"""

from __future__ import annotations

import logging
from typing import Any, Self, override

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectOptionDict,
    SelectSelectorMode,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

import gas_station_spain_api as gss

from .const import (
    DOMAIN,
    CONF_FIXED_DISCOUNT,
    CONF_PERCENTAGE_DISCOUNT,
    CONF_SHOW_IN_MAP,
    CONF_STATION,
    CONF_PRODUCT,
    CONF_PROVINCE,
    CONF_MUNICIPALITY,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow."""

    VERSION = 2

    province_id: str
    product_id: str
    municipality_id: str
    station_id: str
    show_in_map: bool
    fixed_discount: float
    percentage_discount: float

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionFlowHandler()

    @override
    def is_matching(self, other_flow: Self) -> bool:
        return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self.product_id = user_input[CONF_PRODUCT]
            self.province_id = user_input[CONF_PROVINCE]
            return await self.async_step_municipality()

        provinces = await gss.get_provinces()
        products = gss.get_products()

        schema = vol.Schema(
            {
                vol.Required(CONF_PRODUCT): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(label=p.name, value=str(p.id))
                            for p in products
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_PROVINCE): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(label=p.name, value=str(p.id))
                            for p in provinces
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_municipality(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self.municipality_id = user_input[CONF_MUNICIPALITY]
            return await self.async_step_station()

        municipalities = await gss.get_municipalities(
            id_province=self.province_id
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_MUNICIPALITY): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(label=m.name, value=str(m.id))
                            for m in municipalities
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(step_id="municipality", data_schema=schema)

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self.station_id = user_input[CONF_STATION]
            return await self.async_step_options()

        stations = await gss.get_gas_stations(
            municipality_id=int(self.municipality_id),
            product_id=int(self.product_id),
            province_id=int(self.province_id),
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                label=f"{s.marquee} - {s.address}",
                                value=str(s.id),
                            )
                            for s in stations
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )

        return self.async_show_form(step_id="station", data_schema=schema)

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self.show_in_map = user_input[CONF_SHOW_IN_MAP]
            self.fixed_discount = user_input[CONF_FIXED_DISCOUNT]
            self.percentage_discount = user_input[CONF_PERCENTAGE_DISCOUNT]

            station = await gss.get_gas_station(self.station_id)
            product = next(
                p for p in gss.get_products() if str(p.id) == self.product_id
            )

            unique_id = f"{self.product_id}-{station.id}"
            name = f"{product.name}, {station.marquee} ({station.address})"

            await self.async_set_unique_id(unique_id)

            return self.async_create_entry(
                title=name,
                data={
                    CONF_PRODUCT: self.product_id,
                    CONF_MUNICIPALITY: self.municipality_id,
                    CONF_STATION: self.station_id,
                    CONF_FIXED_DISCOUNT: self.fixed_discount,
                    CONF_PERCENTAGE_DISCOUNT: self.percentage_discount,
                    CONF_SHOW_IN_MAP: self.show_in_map,
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
                    )
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
    """Options Flow."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Gasolineras de España",
                data=user_input,
            )

        fixed = self.config_entry.options.get(
            CONF_FIXED_DISCOUNT,
            self.config_entry.data.get(CONF_FIXED_DISCOUNT, 0.0),
        )
        percentage = self.config_entry.options.get(
            CONF_PERCENTAGE_DISCOUNT,
            self.config_entry.data.get(CONF_PERCENTAGE_DISCOUNT, 0.0),
        )
        show_in_map = self.config_entry.options.get(
            CONF_SHOW_IN_MAP,
            self.config_entry.data.get(CONF_SHOW_IN_MAP, False),
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
                    )
                ),
                vol.Required(
                    CONF_PERCENTAGE_DISCOUNT,
                    default=float(percentage),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=100,
                        step=0.01,
                        unit_of_measurement="%",
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_SHOW_IN_MAP,
                    default=bool(show_in_map),
                ): cv.boolean,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
