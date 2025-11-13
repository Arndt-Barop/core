"""Module detection for WAGO I/O System."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .module_registry import WAGOModuleSpec, get_module_spec

_LOGGER = logging.getLogger(__name__)


@dataclass
class DetectedModule:
    """Represents a detected WAGO module with position information."""

    position: int
    spec: WAGOModuleSpec
    process_image_offset: int  # For analog: register offset; for digital: bit offset


def detect_modules(
    config_1_64: list[int],
    config_65_128: list[int],
    config_129_192: list[int],
    config_193_255: list[int],
) -> list[DetectedModule]:
    """Detect WAGO modules from configuration registers.

    Each register contains the module ID directly. For digital modules,
    bit 15 is set and bits 8-14 contain the module size.

    Args:
        config_1_64: Configuration registers for modules 0-64 (0x2030)
        config_65_128: Configuration registers for modules 65-128 (0x2031)
        config_129_192: Configuration registers for modules 129-192 (0x2032)
        config_193_255: Configuration registers for modules 193-255 (0x2033)

    Returns:
        List of detected modules with position and specification

    """
    detected: list[DetectedModule] = []
    digital_bit_offset = 0  # Offset in bits for digital I/O (Coils)
    analog_register_offset = 0  # Offset in 16-bit words for analog I/O (Registers)

    # Combine all config register arrays
    all_configs = config_1_64 + config_65_128 + config_129_192 + config_193_255

    for position, module_value in enumerate(all_configs):
        if module_value == 0:
            continue  # No module at this position

        # Check if this is a digital module (bit 15 set)
        is_digital = bool(module_value & 0x8000)

        if is_digital:
            # Digital module: bits 8-14 contain size, bits 0-1 contain type
            module_size = (module_value >> 8) & 0x7F  # Bits 8-14
            is_input = bool(module_value & 0x01)  # Bit 0
            is_output = bool(module_value & 0x02)  # Bit 1

            _LOGGER.debug(
                "Digital module at position %d: size=%d bits, input=%s, output=%s",
                position,
                module_size,
                is_input,
                is_output,
            )

            # For digital modules, we create a synthetic module ID
            # This is handled by the module registry
            module_id = module_value
        else:
            # Analog/complex module: value is the order number (without 750- prefix)
            module_id = module_value

        spec = get_module_spec(module_id)
        if spec is not None:
            # Use appropriate offset based on module type
            if spec.is_digital():
                current_offset = digital_bit_offset
            else:
                current_offset = analog_register_offset

            detected.append(
                DetectedModule(
                    position=position,
                    spec=spec,
                    process_image_offset=current_offset,
                )
            )

            # Update offset for next module
            if spec.is_digital():
                # Digital modules: offset is in bits
                digital_bit_offset += spec.data_width_bits
                _LOGGER.info(
                    "Detected module %s (%s) at position %d, digital bit offset %d",
                    spec.name,
                    hex(module_id),
                    position,
                    current_offset,
                )
            else:
                # Analog modules: offset is in 16-bit registers
                analog_register_offset += spec.data_width_bits // 16
                _LOGGER.info(
                    "Detected module %s (%s) at position %d, analog register offset %d",
                    spec.name,
                    hex(module_id),
                    position,
                    current_offset,
                )
        else:
            _LOGGER.warning(
                "Unknown module ID 0x%04X at position %d",
                module_id,
                position,
            )

    return detected
