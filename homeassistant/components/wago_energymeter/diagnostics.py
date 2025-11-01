"""Diagnostics support for WAGO Energy Meter."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

from . import WAGOEnergyMeterConfigEntry

# Sensitive data to redact from diagnostics
TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: WAGOEnergyMeterConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    meter = entry.runtime_data

    # Collect diagnostic data
    diagnostics_data: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
        },
        "device_info": {
            "name": entry.data.get(CONF_NAME),
            "port": entry.data.get(CONF_PORT),
        },
    }

    # Try to get current meter readings if available
    try:
        meter_data = {}
        # Voltage readings
        for phase in range(1, 4):
            try:
                voltage_fun = getattr(meter, f"get_voltage_l{phase}")
                meter_data[f"voltage_l{phase}"] = voltage_fun()
            except (OSError, AttributeError):
                meter_data[f"voltage_l{phase}"] = "unavailable"

        # Current readings
        for phase in range(1, 4):
            try:
                current_fun = getattr(meter, f"get_current_l{phase}")
                meter_data[f"current_l{phase}"] = current_fun()
            except (OSError, AttributeError):
                meter_data[f"current_l{phase}"] = "unavailable"

        # Power readings
        for phase in range(1, 4):
            try:
                power_fun = getattr(meter, f"get_power_l{phase}")
                meter_data[f"power_l{phase}"] = power_fun()
            except (OSError, AttributeError):
                meter_data[f"power_l{phase}"] = "unavailable"

        # Frequency
        try:
            meter_data["frequency"] = meter.get_frequency()
        except (OSError, AttributeError):
            meter_data["frequency"] = "unavailable"

        diagnostics_data["current_readings"] = meter_data

    except (OSError, AttributeError, ValueError) as err:
        diagnostics_data["current_readings"] = {
            "error": f"Failed to retrieve meter data: {err}"
        }

    return diagnostics_data
