"""Switch platform for WAGO I/O System."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WAGOIOSystemConfigEntry
from .coordinator import WAGOIOSystemCoordinator
from .entity import WAGOIOSystemEntity
from .module_detector import detect_modules
from .module_registry import ModuleType

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1  # Serialize to prevent conflicting writes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WAGOIOSystemConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WAGO switch entities."""
    coordinator = entry.runtime_data

    # Detect modules from coordinator data
    detected_modules = detect_modules(
        coordinator.data["config_1_64"],
        coordinator.data["config_65_128"],
        coordinator.data["config_129_192"],
        coordinator.data["config_193_255"],
    )

    entities = []
    for module in detected_modules:
        if module.spec.module_type == ModuleType.DIGITAL_OUTPUT:
            for channel in range(module.spec.channels):
                # Calculate bit offset (digital outputs use bit addressing)
                bit_offset = module.process_image_offset + channel

                entities.append(
                    WAGOSwitch(
                        coordinator=coordinator,
                        module_position=module.position,
                        module_name=module.spec.name,
                        channel=channel,
                        bit_offset=bit_offset,
                    )
                )

    async_add_entities(entities)


class WAGOSwitch(WAGOIOSystemEntity, SwitchEntity):
    """Representation of a WAGO switch."""

    def __init__(
        self,
        coordinator: WAGOIOSystemCoordinator,
        module_position: int,
        module_name: str,
        channel: int,
        bit_offset: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, module_position, module_name, channel)
        self._bit_offset = bit_offset

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if not self.coordinator.data or "digital_outputs" not in self.coordinator.data:
            return None

        digital_outputs = self.coordinator.data["digital_outputs"]
        if self._bit_offset >= len(digital_outputs):
            return None

        return digital_outputs[self._bit_offset]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._write_output(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._write_output(False)

    async def _write_output(self, state: bool) -> None:
        """Write output state to Modbus coil."""

        def _write_coil() -> bool:
            """Write to Modbus output coil."""
            if not self.coordinator.client.open():
                _LOGGER.error("Failed to connect to WAGO controller for write")
                return False

            try:
                # Write directly to coil (no read-modify-write needed for coils)
                # WAGO uses 0x0200 as start address for process outputs
                success = self.coordinator.client.write_single_coil(
                    0x0200 + self._bit_offset, state
                )
                if not success:
                    _LOGGER.error("Failed to write output coil %d", self._bit_offset)
                    return False

                return True
            finally:
                self.coordinator.client.close()

        success = await self.hass.async_add_executor_job(_write_coil)
        if success:
            # Request coordinator refresh to update state
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning(
                "Failed to %s switch: Module %d Channel %d",
                "turn on" if state else "turn off",
                self._module_position,
                self._channel,
            )
