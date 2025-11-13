"""Data update coordinator for WAGO I/O System."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from pyModbusTCP.client import ModbusClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONFIG_REG_1_64,
    CONFIG_REG_65_128,
    CONFIG_REG_129_192,
    CONFIG_REG_193_255,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class WAGOIOSystemCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data updates from WAGO I/O System."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=config_entry,
        )
        self.client = ModbusClient(
            host=config_entry.data[CONF_HOST],
            port=config_entry.data[CONF_PORT],
            timeout=DEFAULT_TIMEOUT,
            auto_open=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the WAGO controller."""

        def _read_config_registers() -> dict[str, Any]:
            """Read module configuration registers via Modbus."""
            if not self.client.open():
                raise UpdateFailed("Failed to connect to WAGO controller")

            try:
                config_1_64 = self.client.read_holding_registers(CONFIG_REG_1_64, 1)
                config_65_128 = self.client.read_holding_registers(CONFIG_REG_65_128, 1)
                config_129_192 = self.client.read_holding_registers(
                    CONFIG_REG_129_192, 1
                )
                config_193_255 = self.client.read_holding_registers(
                    CONFIG_REG_193_255, 1
                )

                if (
                    config_1_64 is None
                    or config_65_128 is None
                    or config_129_192 is None
                    or config_193_255 is None
                ):
                    raise UpdateFailed("Failed to read configuration registers")

                return {
                    "config_1_64": config_1_64[0],
                    "config_65_128": config_65_128[0],
                    "config_129_192": config_129_192[0],
                    "config_193_255": config_193_255[0],
                }
            finally:
                self.client.close()

        try:
            return await self.hass.async_add_executor_job(_read_config_registers)
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with WAGO controller: {err}") from err
