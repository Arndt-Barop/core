"""Switch platform for WAGO I/O System."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WAGOIOSystemConfigEntry
from .coordinator import WAGOIOSystemCoordinator
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

    entities = [
        WAGOSwitch(
            coordinator=coordinator,
            module_position=module.position,
            module_name=module.spec.name,
            channel=channel,
        )
        for module in detected_modules
        if module.spec.module_type == ModuleType.DIGITAL_OUTPUT
        for channel in range(module.spec.channels)
    ]

    async_add_entities(entities)


class WAGOSwitch(SwitchEntity):
    """Representation of a WAGO switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WAGOIOSystemCoordinator,
        module_position: int,
        module_name: str,
        channel: int,
    ) -> None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._module_position = module_position
        self._module_name = module_name
        self._channel = channel

        # Generate unique ID
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_m{module_position}_ch{channel}"
        )

        # Set entity name
        self._attr_name = f"Module {module_position} Channel {channel}"

    @property
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        # TODO: Read actual process image data from coordinator
        # For now, return None (unknown state)
        return None

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

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
