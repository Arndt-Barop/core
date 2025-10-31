"""Config flow for WAGO Energy Meter integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from pyModbusTCP.client import ModbusClient
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, selector

from . import WAGOEnergyMeterConfigEntry
from .const import (
    AVAILABLE_2857_SENSORS,
    AVAILABLE_MID_SENSORS,
    BAUDRATE_OPTIONS,
    CONF_ADDITIONAL_SENSORS,
    CONF_BAUDRATE,
    CONF_DEVICE_TYPE,
    CONF_MODBUS_TIMEOUT,
    CONF_PARITY,
    DEFAULT_BAUDRATE,
    DEFAULT_MODBUS_TIMEOUT,
    DEFAULT_PARITY,
    DEFAULT_PORT,
    DEVICE_TYPE_2857_570,
    DEVICE_TYPE_MID_METER,
    DEVICE_TYPES,
    DOMAIN,
    PARITY_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    def test_connection() -> bool:
        """Test if we can establish a Modbus TCP connection to the WAGO device.

        Note: We only test if the Modbus TCP connection can be established.
        Reading actual meter data is optional - the device might be online but
        no MID meter module is connected yet. The entities will become available
        automatically once a meter module is connected and provides data.
        """
        try:
            _LOGGER.info(
                "Testing Modbus TCP connection to WAGO device at %s:%s",
                data[CONF_HOST],
                data[CONF_PORT],
            )
            client = ModbusClient(
                host=data[CONF_HOST],
                port=data[CONF_PORT],
                unit_id=1,
                auto_open=False,
                timeout=10,
            )

            # Try to open the Modbus TCP connection
            if not client.open():
                _LOGGER.error(
                    "Failed to establish Modbus TCP connection to %s:%s",
                    data[CONF_HOST],
                    data[CONF_PORT],
                )
                return False

            _LOGGER.info(
                "Successfully established Modbus TCP connection to WAGO device at %s:%s",
                data[CONF_HOST],
                data[CONF_PORT],
            )

            # Close the connection
            client.close()

        except (OSError, ValueError) as err:
            _LOGGER.error(
                "Error connecting to WAGO device at %s:%s - %s",
                data[CONF_HOST],
                data[CONF_PORT],
                err,
            )
            return False
        except Exception:
            _LOGGER.exception("Unexpected error connecting to WAGO device")
            return False
        else:
            return True

    # Test the connection in executor to avoid blocking
    if not await hass.async_add_executor_job(test_connection):
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": data[CONF_NAME]}


class WAGOEnergyMeterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WAGO Energy Meter."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: WAGOEnergyMeterConfigEntry,
    ) -> WagoEnergyMeterOptionsFlow:
        """Get the options flow for this handler."""
        return WagoEnergyMeterOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Convert baudrate from string to int if needed
            if isinstance(user_input.get(CONF_BAUDRATE), str):
                user_input[CONF_BAUDRATE] = int(user_input[CONF_BAUDRATE])

            # Check if device is already configured
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            )

            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        # Schema for the configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(
                        CONF_DEVICE_TYPE, default=DEVICE_TYPE_MID_METER
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=k, label=v)
                                for k, v in DEVICE_TYPES.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=str(baudrate), label=str(baudrate)
                                )
                                for baudrate in BAUDRATE_OPTIONS
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_PARITY, default=DEFAULT_PARITY
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=k, label=v)
                                for k, v in PARITY_OPTIONS.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_MODBUS_TIMEOUT, default=DEFAULT_MODBUS_TIMEOUT
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=30,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth flow when connection fails."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            # Test connection with new config
            test_data = {
                CONF_NAME: reauth_entry.data[CONF_NAME],
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
            }

            try:
                await validate_input(self.hass, test_data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=reauth_entry.data[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=reauth_entry.data[CONF_PORT]): int,
                }
            ),
            errors=errors,
            description_placeholders={"name": reauth_entry.data[CONF_NAME]},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            # Convert baudrate from string to int if needed
            if isinstance(user_input.get(CONF_BAUDRATE), str):
                user_input[CONF_BAUDRATE] = int(user_input[CONF_BAUDRATE])

            # Test connection with new configuration
            test_data = {
                CONF_NAME: reconfigure_entry.data[CONF_NAME],
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
            }

            try:
                await validate_input(self.hass, test_data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_DEVICE_TYPE: user_input[CONF_DEVICE_TYPE],
                        CONF_BAUDRATE: user_input[CONF_BAUDRATE],
                        CONF_PARITY: user_input[CONF_PARITY],
                        CONF_MODBUS_TIMEOUT: user_input[CONF_MODBUS_TIMEOUT],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=reconfigure_entry.data[CONF_HOST]
                    ): str,
                    vol.Required(
                        CONF_PORT, default=reconfigure_entry.data[CONF_PORT]
                    ): int,
                    vol.Required(
                        CONF_DEVICE_TYPE,
                        default=reconfigure_entry.data.get(
                            CONF_DEVICE_TYPE, DEVICE_TYPE_MID_METER
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=k, label=v)
                                for k, v in DEVICE_TYPES.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_BAUDRATE,
                        default=str(
                            reconfigure_entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=str(baudrate), label=str(baudrate)
                                )
                                for baudrate in BAUDRATE_OPTIONS
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_PARITY,
                        default=reconfigure_entry.data.get(CONF_PARITY, DEFAULT_PARITY),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=k, label=v)
                                for k, v in PARITY_OPTIONS.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_MODBUS_TIMEOUT,
                        default=reconfigure_entry.data.get(
                            CONF_MODBUS_TIMEOUT, DEFAULT_MODBUS_TIMEOUT
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=30,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"name": reconfigure_entry.data[CONF_NAME]},
        )


class WagoEnergyMeterOptionsFlow(OptionsFlow):
    """Handle options flow for WAGO Energy Meter."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        device_type = self.config_entry.data.get(CONF_DEVICE_TYPE)

        # Determine which sensors are available based on device type
        if device_type == DEVICE_TYPE_MID_METER:
            available_sensors = AVAILABLE_MID_SENSORS
        elif device_type == DEVICE_TYPE_2857_570:
            available_sensors = AVAILABLE_2857_SENSORS
        else:
            return self.async_abort(reason="not_supported")

        if user_input is not None:
            # Get previously selected sensors
            previous_sensors = set(
                self.config_entry.options.get(CONF_ADDITIONAL_SENSORS, [])
            )
            new_sensors = set(user_input.get(CONF_ADDITIONAL_SENSORS, []))

            # Remove entities for sensors that were deselected
            removed_sensors = previous_sensors - new_sensors
            if removed_sensors:
                entity_registry = er.async_get(self.hass)
                for sensor_id in removed_sensors:
                    # Construct unique_id: {entry_id}_{sensor_id}
                    unique_id = f"{self.config_entry.entry_id}_{sensor_id}"
                    entity_id = entity_registry.async_get_entity_id(
                        Platform.SENSOR, DOMAIN, unique_id
                    )
                    if entity_id:
                        entity_registry.async_remove(entity_id)

            return self.async_create_entry(title="", data=user_input)

        # Get currently selected additional sensors
        current_sensors = self.config_entry.options.get(CONF_ADDITIONAL_SENSORS, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ADDITIONAL_SENSORS,
                        default=current_sensors,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=key,
                                    label=label,
                                )
                                for key, label in available_sensors.items()
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                }
            ),
            description_placeholders={
                "name": self.config_entry.data[CONF_NAME],
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
