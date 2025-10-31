"""The WAGO Energy Meter integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_BAUDRATE,
    CONF_DEVICE_TYPE,
    CONF_MODBUS_TIMEOUT,
    CONF_PARITY,
    DEFAULT_BAUDRATE,
    DEFAULT_MODBUS_TIMEOUT,
    DEFAULT_PARITY,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_MID_METER,
    DOMAIN,
)
from .meter import WagoMeter

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type WAGOEnergyMeterConfigEntry = ConfigEntry[WagoMeter]

__all__ = ["DOMAIN"]


async def async_setup_entry(
    hass: HomeAssistant, entry: WAGOEnergyMeterConfigEntry
) -> bool:
    """Set up WAGO Energy Meter from a config entry."""

    # Get configuration with defaults for backwards compatibility
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_MID_METER)
    modbus_timeout = entry.data.get(CONF_MODBUS_TIMEOUT, DEFAULT_MODBUS_TIMEOUT)
    baudrate = entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
    parity = entry.data.get(CONF_PARITY, DEFAULT_PARITY)

    _LOGGER.info(
        "Setting up WAGO Energy Meter: %s (Device Type: %s, Baudrate: %s, Parity: %s, Timeout: %s)",
        entry.data[CONF_HOST],
        device_type,
        baudrate,
        parity,
        modbus_timeout,
    )

    # Create meter instance in executor to avoid blocking
    def create_meter() -> WagoMeter:
        return WagoMeter(
            ip=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            interval=DEFAULT_SCAN_INTERVAL,
            timeout=modbus_timeout,
            device_type=device_type,
        )

    try:
        wago_meter = await hass.async_add_executor_job(create_meter)
        # Start the Modbus polling thread
        await hass.async_add_executor_job(wago_meter.start)
    except (OSError, ValueError) as err:
        _LOGGER.error("Failed to initialize WAGO Energy Meter: %s", err)
        raise ConfigEntryNotReady(
            f"Failed to connect to {entry.data[CONF_HOST]}"
        ) from err

    # Store meter instance in runtime_data
    entry.runtime_data = wago_meter

    # Forward entry setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: WAGOEnergyMeterConfigEntry
) -> bool:
    """Unload a config entry."""
    # Unload platforms first
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Stop the meter thread only if runtime_data exists
    if unload_ok and hasattr(entry, "runtime_data"):

        def stop_meter() -> None:
            entry.runtime_data.stop()

        await hass.async_add_executor_job(stop_meter)

    return unload_ok
