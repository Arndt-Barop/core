"""Module registry for WAGO I/O modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass


class ModuleType(IntEnum):
    """Module type enumeration."""

    DIGITAL_INPUT = 1
    DIGITAL_OUTPUT = 2
    ANALOG_INPUT = 3
    ANALOG_OUTPUT = 4


@dataclass(frozen=True)
class WAGOModuleSpec:
    """Specification for a WAGO I/O module."""

    module_id: int
    name: str
    module_type: ModuleType
    channels: int
    data_width_bits: int
    device_class: SensorDeviceClass | BinarySensorDeviceClass | None = None
    native_unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None


WAGO_MODULE_REGISTRY: dict[int, WAGOModuleSpec] = {
    # Coupler/Controller (position 0)
    0x016A: WAGOModuleSpec(
        module_id=0x016A,
        name="750-362",
        module_type=ModuleType.DIGITAL_INPUT,  # Coupler has no I/O
        channels=0,
        data_width_bits=0,
    ),
    # Digital Input Modules
    0x0192: WAGOModuleSpec(
        module_id=0x0192,
        name="750-402",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=2,
        data_width_bits=2,
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    0x0194: WAGOModuleSpec(
        module_id=0x0194,
        name="750-404",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=4,
        data_width_bits=4,
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    0x01F6: WAGOModuleSpec(
        module_id=0x01F6,
        name="750-430",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=8,
        data_width_bits=8,
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    0x01F8: WAGOModuleSpec(
        module_id=0x01F8,
        name="750-432",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=16,
        data_width_bits=16,
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    # Digital Output Modules
    0x01F4: WAGOModuleSpec(
        module_id=0x01F4,
        name="750-504",
        module_type=ModuleType.DIGITAL_OUTPUT,
        channels=4,
        data_width_bits=4,
    ),
    0x01F5: WAGOModuleSpec(
        module_id=0x01F5,
        name="750-508",
        module_type=ModuleType.DIGITAL_OUTPUT,
        channels=8,
        data_width_bits=8,
    ),
    0x01F9: WAGOModuleSpec(
        module_id=0x01F9,
        name="750-530",
        module_type=ModuleType.DIGITAL_OUTPUT,
        channels=16,
        data_width_bits=16,
    ),
    # Analog Input Modules (Voltage)
    0x01C3: WAGOModuleSpec(
        module_id=0x01C3,
        name="750-451",
        module_type=ModuleType.ANALOG_INPUT,
        channels=4,
        data_width_bits=64,  # 4 channels × 16 bits
        device_class=SensorDeviceClass.CURRENT,
        native_unit="mA",
        min_value=4.0,
        max_value=20.0,
    ),
    0x01C7: WAGOModuleSpec(
        module_id=0x01C7,
        name="750-455",
        module_type=ModuleType.ANALOG_INPUT,
        channels=2,
        data_width_bits=32,  # 2 channels × 16 bits
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit="V",
        min_value=-10.0,
        max_value=10.0,
    ),
    0x0228: WAGOModuleSpec(
        module_id=0x0228,
        name="750-469",
        module_type=ModuleType.ANALOG_INPUT,
        channels=4,
        data_width_bits=64,
        device_class=SensorDeviceClass.CURRENT,
        native_unit="mA",
        min_value=4.0,
        max_value=20.0,
    ),
    0x022A: WAGOModuleSpec(
        module_id=0x022A,
        name="750-471",
        module_type=ModuleType.ANALOG_INPUT,
        channels=4,
        data_width_bits=64,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit="V",
        min_value=0.0,
        max_value=10.0,
    ),
    0x022C: WAGOModuleSpec(
        module_id=0x022C,
        name="750-473",
        module_type=ModuleType.ANALOG_INPUT,
        channels=4,
        data_width_bits=64,
        device_class=SensorDeviceClass.CURRENT,
        native_unit="mA",
        min_value=0.0,
        max_value=20.0,
    ),
    # Analog Output Modules
    0x0258: WAGOModuleSpec(
        module_id=0x0258,
        name="750-550",
        module_type=ModuleType.ANALOG_OUTPUT,
        channels=4,
        data_width_bits=64,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit="V",
        min_value=0.0,
        max_value=10.0,
    ),
    0x0259: WAGOModuleSpec(
        module_id=0x0259,
        name="750-552",
        module_type=ModuleType.ANALOG_OUTPUT,
        channels=4,
        data_width_bits=64,
        device_class=SensorDeviceClass.CURRENT,
        native_unit="mA",
        min_value=4.0,
        max_value=20.0,
    ),
}


def get_module_spec(module_id: int) -> WAGOModuleSpec | None:
    """Get module specification by module ID.

    For digital modules (bit 15 set), create a dynamic spec based on size.
    For analog modules, look up in registry.
    """
    # Check if this is a digital module (bit 15 set)
    if module_id & 0x8000:
        # Digital module: decode size and type from bits
        module_size = (module_id >> 8) & 0x7F  # Bits 8-14
        is_input = bool(module_id & 0x01)  # Bit 0
        is_output = bool(module_id & 0x02)  # Bit 1

        # Determine module type
        if is_input and not is_output:
            module_type = ModuleType.DIGITAL_INPUT
        elif is_output and not is_input:
            module_type = ModuleType.DIGITAL_OUTPUT
        else:
            # Both input and output (bidirectional)
            module_type = ModuleType.DIGITAL_INPUT  # Default to input

        return WAGOModuleSpec(
            module_id=module_id,
            name=f"Digital {'I/O' if (is_input and is_output) else 'Input' if is_input else 'Output'} ({module_size} bit)",
            module_type=module_type,
            channels=module_size,
            data_width_bits=module_size,
            device_class=BinarySensorDeviceClass.OPENING if is_input else None,
        )

    # Analog/complex module: look up in registry
    return WAGO_MODULE_REGISTRY.get(module_id)
