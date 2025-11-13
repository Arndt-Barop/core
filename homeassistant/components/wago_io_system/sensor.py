"""Sensor platform for WAGO I/O System."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up WAGO sensor entities."""
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
        if module.spec.module_type == ModuleType.ANALOG_INPUT:
            for channel in range(module.spec.channels):
                # Calculate register offset (analog inputs use multiple registers per channel)
                registers_per_channel = module.spec.data_width_bits // (
                    16 * module.spec.channels
                )
                register_offset = module.process_image_offset + (
                    channel * registers_per_channel
                )

                entities.append(
                    WAGOSensor(
                        coordinator=coordinator,
                        module_position=module.position,
                        module_name=module.spec.name,
                        channel=channel,
                        device_class=module.spec.device_class,
                        native_unit=module.spec.native_unit,
                        min_value=module.spec.min_value,
                        max_value=module.spec.max_value,
                        register_offset=register_offset,
                    )
                )

    async_add_entities(entities)


class WAGOSensor(WAGOIOSystemEntity, SensorEntity):
    """Representation of a WAGO sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: WAGOIOSystemCoordinator,
        module_position: int,
        module_name: str,
        channel: int,
        device_class,
        native_unit: str | None,
        min_value: float | None,
        max_value: float | None,
        register_offset: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, module_position, module_name, channel)
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = native_unit
        self._min_value = min_value
        self._max_value = max_value
        self._register_offset = register_offset

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or "process_inputs" not in self.coordinator.data:
            return None

        process_inputs = self.coordinator.data["process_inputs"]
        if self._register_offset >= len(process_inputs):
            return None

        register_value = process_inputs[self._register_offset]
        if register_value is None:
            return None

        # Convert raw register value to physical value
        # For WAGO analog modules, the raw value needs scaling
        if self._min_value is not None and self._max_value is not None:
            # Assume 16-bit signed value (-32768 to 32767)
            # Scale to physical range
            raw_min = -32768
            raw_max = 32767
            normalized = (register_value - raw_min) / (raw_max - raw_min)
            return self._min_value + normalized * (self._max_value - self._min_value)

        return float(register_value)
