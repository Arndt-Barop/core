"""Binary sensor platform for WAGO I/O System."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WAGOIOSystemConfigEntry
from .coordinator import WAGOIOSystemCoordinator
from .entity import WAGOIOSystemEntity
from .module_detector import detect_modules
from .module_registry import ModuleType

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WAGOIOSystemConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
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

    entities = []
    for module in detected_modules:
        if module.spec.module_type == ModuleType.DIGITAL_INPUT:
            for channel in range(module.spec.channels):
                # For digital modules, process_image_offset is already the bit offset
                # Each channel is 1 bit
                bit_offset = module.process_image_offset + channel

                entities.append(
                    WAGOBinarySensor(
                        coordinator=coordinator,
                        module_position=module.position,
                        module_name=module.spec.name,
                        channel=channel,
                        device_class=module.spec.device_class,
                        bit_offset=bit_offset,
                    )
                )

    async_add_entities(entities)


class WAGOBinarySensor(WAGOIOSystemEntity, BinarySensorEntity):
    """Representation of a WAGO binary sensor."""

    def __init__(
        self,
        coordinator: WAGOIOSystemCoordinator,
        module_position: int,
        module_name: str,
        channel: int,
        device_class,
        bit_offset: int,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, module_position, module_name, channel)
        self._attr_device_class = device_class
        self._bit_offset = bit_offset

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data or "digital_inputs" not in self.coordinator.data:
            return None

        digital_inputs = self.coordinator.data["digital_inputs"]

        # Digital inputs are bit-addressed directly
        if self._bit_offset >= len(digital_inputs):
            return None

        return bool(digital_inputs[self._bit_offset])
