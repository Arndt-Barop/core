"""Base entity for WAGO I/O System."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WAGOIOSystemCoordinator


class WAGOIOSystemEntity(CoordinatorEntity[WAGOIOSystemCoordinator]):
    """Base entity for WAGO I/O System."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WAGOIOSystemCoordinator,
        module_position: int,
        module_name: str,
        channel: int,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._module_position = module_position
        self._module_name = module_name
        self._channel = channel

        # Generate unique ID
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_m{module_position}_ch{channel}"
        )

        # Set entity name
        self._attr_name = f"Module {module_position} Channel {channel}"

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"WAGO Controller ({coordinator.config_entry.data['host']})",
            manufacturer="WAGO",
            model="750-362",
        )
