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
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_PROCESS_IMAGE_SIZE,
    PROCESS_INPUT_START,
    PROCESS_OUTPUT_START,
)
from .module_detector import DetectedModule, detect_modules

_LOGGER = logging.getLogger(__name__)


class WAGOIOSystemCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data updates from WAGO I/O System."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=config_entry,
        )
        self.config_entry = config_entry
        self.client = ModbusClient(
            host=config_entry.data[CONF_HOST],
            port=config_entry.data[CONF_PORT],
            unit_id=1,  # WAGO controllers use unit ID 1
            timeout=DEFAULT_TIMEOUT,
            auto_open=False,
        )
        self._detected_modules: list[DetectedModule] | None = None
        self._process_image_size = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the WAGO controller."""

        def _read_all_data() -> dict[str, Any]:
            """Read configuration and process image data via Modbus."""
            try:
                if not self.client.open():
                    _LOGGER.error(
                        "Failed to connect to WAGO controller at %s:%s",
                        self.config_entry.data[CONF_HOST],
                        self.config_entry.data[CONF_PORT],
                    )
                    raise UpdateFailed("Failed to connect to WAGO controller")
            except OSError as err:
                _LOGGER.error(
                    "Network error connecting to WAGO controller at %s:%s: %s",
                    self.config_entry.data[CONF_HOST],
                    self.config_entry.data[CONF_PORT],
                    err,
                )
                raise UpdateFailed(f"Network error: {err}") from err

            try:
                # Read configuration registers
                # Start with a reasonable chunk size (32 modules) to avoid timeouts
                # Most WAGO systems have fewer than 32 modules
                # Register 0x2030: modules 0-64, read first 32 to check
                _LOGGER.debug(
                    "Reading first 32 configuration registers from 0x%04X",
                    CONFIG_REG_1_64,
                )
                config_1_64_partial = self.client.read_holding_registers(
                    CONFIG_REG_1_64, 32
                )
                if config_1_64_partial is None:
                    _LOGGER.error(
                        "Failed to read configuration registers at 0x%04X. "
                        "Check Modbus connection and unit ID",
                        CONFIG_REG_1_64,
                    )
                    raise UpdateFailed("Failed to read configuration registers")

                _LOGGER.debug(
                    "Successfully read %d configuration values",
                    len(config_1_64_partial),
                )

                # Check if we need to read more from first block
                # If last value is non-zero, read the rest
                if config_1_64_partial[-1] != 0:
                    _LOGGER.debug("Detected more modules, reading remaining registers")
                    config_1_64_rest = self.client.read_holding_registers(
                        CONFIG_REG_1_64 + 32, 33
                    )
                    if config_1_64_rest is None:
                        _LOGGER.warning(
                            "Failed to read extended configuration registers, "
                            "using first 32 modules only"
                        )
                        config_1_64 = config_1_64_partial
                    else:
                        config_1_64 = config_1_64_partial + config_1_64_rest
                        _LOGGER.debug(
                            "Read total of %d configuration values", len(config_1_64)
                        )
                else:
                    config_1_64 = config_1_64_partial

                # For other blocks, only read if needed (most systems won't need these)
                # We'll pad with zeros if not read
                config_65_128 = [0] * 65
                config_129_192 = [0] * 64
                config_193_255 = [0] * 63

                data = {
                    "config_1_64": config_1_64,
                    "config_65_128": config_65_128,
                    "config_129_192": config_129_192,
                    "config_193_255": config_193_255,
                }

                # Detect modules on first run or if not cached
                if self._detected_modules is None:
                    self._detected_modules = detect_modules(
                        data["config_1_64"],
                        data["config_65_128"],
                        data["config_129_192"],
                        data["config_193_255"],
                    )
                    # Calculate total process image size needed
                    self._process_image_size = sum(
                        module.spec.data_width_bits // 16
                        for module in self._detected_modules
                    )
                    _LOGGER.debug(
                        "Detected %d modules, process image size: %d registers",
                        len(self._detected_modules),
                        self._process_image_size,
                    )

                # Read process image data if modules detected
                if self._process_image_size > 0:
                    read_size = min(self._process_image_size, MAX_PROCESS_IMAGE_SIZE)

                    # Read input registers
                    input_data = self.client.read_holding_registers(
                        PROCESS_INPUT_START, read_size
                    )
                    if input_data is None:
                        _LOGGER.warning("Failed to read process input data")
                        data["process_inputs"] = []
                    else:
                        data["process_inputs"] = input_data

                    # Read output registers
                    output_data = self.client.read_holding_registers(
                        PROCESS_OUTPUT_START, read_size
                    )
                    if output_data is None:
                        _LOGGER.warning("Failed to read process output data")
                        data["process_outputs"] = []
                    else:
                        data["process_outputs"] = output_data
                else:
                    data["process_inputs"] = []
                    data["process_outputs"] = []

                return data
            finally:
                self.client.close()

        try:
            return await self.hass.async_add_executor_job(_read_all_data)
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with WAGO controller: {err}"
            ) from err
