"""Config flow for WAGO I/O System integration."""

from __future__ import annotations

import logging
from typing import Any

from pyModbusTCP.client import ModbusClient
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
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
        host=host,
        port=port,
        unit_id=1,  # WAGO controllers use unit ID 1
        timeout=DEFAULT_TIMEOUT,
        auto_open=False,
    )

    def _test_connection() -> tuple[bool, str | None]:
        """Test connection and try to get device MAC address in executor.

        Returns tuple of (success, mac_address).
        MAC address is attempted from Modbus registers 0x2010-0x2012 (3 words).
        Falls back to host:port if MAC not available (e.g., older controllers).
        """
        if not client.open():
            return False, None

        try:
            # Try to read MAC address from registers 0x2010-0x2012 (6 bytes = 3 registers)
            # This may not be available on all WAGO controllers
            mac_registers = client.read_holding_registers(0x2010, 3)
        except OSError:
            # Connection worked but register read failed - use host:port as identifier
            return True, f"{host}:{port}"
        else:
            if mac_registers and all(r is not None for r in mac_registers):
                # Convert registers to MAC address string
                mac_bytes: list[int] = []
                for reg in mac_registers:
                    if reg is not None:  # Type guard for mypy
                        mac_bytes.append((reg >> 8) & 0xFF)  # High byte
                        mac_bytes.append(reg & 0xFF)  # Low byte
                mac_address = ":".join(f"{b:02x}" for b in mac_bytes)
            else:
                # MAC not available - use host:port as unique identifier
                mac_address = f"{host}:{port}"

            return True, mac_address
        finally:
            client.close()

    success, mac_address = await hass.async_add_executor_job(_test_connection)

    if not success:
        raise CannotConnect

    if mac_address is None:
        raise CannotConnect

    return {"title": data[CONF_NAME], "mac": mac_address}


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
                # Set unique ID based on device MAC address
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
