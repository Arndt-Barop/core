"""Config flow for WAGO I/O System integration."""

from __future__ import annotations

import logging
from typing import Any

from pyModbusTCP.client import ModbusClient
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]
    port = data[CONF_PORT]

    # Test connection to Modbus device
    client = ModbusClient(
        host=host, port=port, timeout=DEFAULT_TIMEOUT, auto_open=False
    )

    def _test_connection() -> bool:
        """Test connection in executor."""
        if not client.open():
            return False
        # Try to read a register to verify connection
        result = client.read_holding_registers(0, 1)
        client.close()
        return result is not None

    if not await hass.async_add_executor_job(_test_connection):
        raise CannotConnect

    return {"title": f"WAGO Controller ({host})"}


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class WAGOIOSystemConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WAGO I/O System."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Unique ID will be set in future commit based on device info
                # Duplicate entry checking will be added in future commit
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
