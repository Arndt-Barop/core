"""Integration for WAGO I/O System."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import WAGOIOSystemCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

__all__ = ["DOMAIN"]

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
        "Setting up WAGO I/O System integration for %s", entry.data[CONF_HOST]
    )

    coordinator = WAGOIOSystemCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: WAGOIOSystemConfigEntry
) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading WAGO I/O System integration for %s", entry.data[CONF_HOST])

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
