"""Switch platform for WAGO I/O System."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WAGOIOSystemConfigEntry
from .coordinator import WAGOIOSystemCoordinator
from .entity import WAGOIOSystemEntity
from .module_detector import detect_modules
from .module_registry import ModuleType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WAGOIOSystemConfigEntry,
    async_add_entities: AddEntitiesCallback,
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
                # Calculate register and bit offset
                register_offset = module.process_image_offset
                bit_offset = channel

                entities.append(
                    WAGOSwitch(
                        coordinator=coordinator,
                        module_position=module.position,
                        module_name=module.spec.name,
                        channel=channel,
                        register_offset=register_offset,
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
        register_offset: int,
        bit_offset: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, module_position, module_name, channel)
        self._register_offset = register_offset
        self._bit_offset = bit_offset

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        if not self.coordinator.data or "process_outputs" not in self.coordinator.data:
            return None

        process_outputs = self.coordinator.data["process_outputs"]
        if self._register_offset >= len(process_outputs):
            return None

        register_value = process_outputs[self._register_offset]
        if register_value is None:
            return None

        return bool(register_value & (1 << self._bit_offset))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        # TODO: Implement Modbus write to set output high
        _LOGGER.debug(
            "Turn on switch: Module %d Channel %d", self._module_position, self._channel
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        # TODO: Implement Modbus write to set output low
        _LOGGER.debug(
            "Turn off switch: Module %d Channel %d",
            self._module_position,
            self._channel,
        )
