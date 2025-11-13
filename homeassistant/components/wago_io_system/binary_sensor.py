"""Binary sensor platform for WAGO I/O System."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up WAGO binary sensor entities."""
    coordinator = entry.runtime_data

    # Detect modules from coordinator data
    detected_modules = detect_modules(
        coordinator.data["config_1_64"],
        coordinator.data["config_65_128"],
        coordinator.data["config_129_192"],
        coordinator.data["config_193_255"],
    )

    entities = [
        WAGOBinarySensor(
            coordinator=coordinator,
            module_position=module.position,
            module_name=module.spec.name,
            channel=channel,
            device_class=module.spec.device_class,
        )
        for module in detected_modules
        if module.spec.module_type == ModuleType.DIGITAL_INPUT
        for channel in range(module.spec.channels)
    ]

    async_add_entities(entities)


class WAGOBinarySensor(BinarySensorEntity):
    """Representation of a WAGO binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WAGOIOSystemCoordinator,
        module_position: int,
        module_name: str,
        channel: int,
        device_class,
    ) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self._module_position = module_position
        self._module_name = module_name
        self._channel = channel
        self._attr_device_class = device_class

        # Generate unique ID
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_m{module_position}_ch{channel}"
        )

        # Set entity name
        self._attr_name = f"Module {module_position} Channel {channel}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        # TODO: Read actual process image data from coordinator
        # For now, return None (unknown state)
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
