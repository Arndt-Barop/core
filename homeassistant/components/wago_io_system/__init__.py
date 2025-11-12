"""The WAGO I/O System integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN as DOMAIN

if TYPE_CHECKING:
    from .coordinator import WAGOIOSystemCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

type WAGOIOSystemConfigEntry = ConfigEntry[WAGOIOSystemCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: WAGOIOSystemConfigEntry
) -> bool:
    """Set up WAGO I/O System from a config entry."""
    _LOGGER.debug(
        "Setting up WAGO I/O System integration for %s:%s",
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
    )

    # Coordinator and module detection will be implemented in next commits
    # coordinator = WAGOIOSystemCoordinator(hass, entry)
    # await coordinator.async_config_entry_first_refresh()
    # entry.runtime_data = coordinator

    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: WAGOIOSystemConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
