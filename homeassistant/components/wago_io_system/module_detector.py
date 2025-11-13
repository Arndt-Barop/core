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
    process_image_offset: int


def detect_modules(
    config_1_64: int,
    config_65_128: int,
    config_129_192: int,
    config_193_255: int,
) -> list[DetectedModule]:
    """Detect WAGO modules from configuration registers.

    Args:
        config_1_64: Configuration register for modules 1-64 (0x2030)
        config_65_128: Configuration register for modules 65-128 (0x2031)
        config_129_192: Configuration register for modules 129-192 (0x2032)
        config_193_255: Configuration register for modules 193-255 (0x2033)

    Returns:
        List of detected modules with position and specification

    """
    detected: list[DetectedModule] = []
    process_image_offset = 0

    config_registers = [config_1_64, config_65_128, config_129_192, config_193_255]

    for register_idx, config_value in enumerate(config_registers):
        base_position = register_idx * 64 + 1

        for bit_position in range(16):
            if config_value & (1 << bit_position):
                module_position = base_position + bit_position
                module_id = _read_module_id(module_position, config_value, bit_position)

                if module_id is not None:
                    spec = get_module_spec(module_id)
                    if spec is not None:
                        detected.append(
                            DetectedModule(
                                position=module_position,
                                spec=spec,
                                process_image_offset=process_image_offset,
                            )
                        )
                        process_image_offset += spec.data_width_bits // 16
                        _LOGGER.debug(
                            "Detected module %s (%s) at position %d, offset %d",
                            spec.name,
                            hex(module_id),
                            module_position,
                            process_image_offset,
                        )
                    else:
                        _LOGGER.warning(
                            "Unknown module ID %s at position %d",
                            hex(module_id) if module_id else "None",
                            module_position,
                        )

    return detected


def _read_module_id(position: int, config_value: int, bit_position: int) -> int | None:
    """Read module ID from configuration register.

    The module ID is encoded in the configuration register bits.
    For digital modules, bit 15 is set to 1.

    Args:
        position: Module position (1-255)
        config_value: Configuration register value
        bit_position: Bit position in register (0-15)

    Returns:
        Module ID or None if not detected

    """
    # Extract module ID from configuration bits
    # In WAGO systems, the module ID is typically encoded in the register value
    # For this implementation, we assume the register bit indicates presence
    # and the actual module ID needs to be read from a separate register or
    # is encoded in the configuration value itself

    # For now, return the configuration value as module ID
    # This is a simplified implementation and may need adjustment
    # based on actual WAGO protocol documentation
    return config_value if config_value != 0 else None
