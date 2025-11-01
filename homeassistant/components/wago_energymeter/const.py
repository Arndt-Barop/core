"""Constants for the WAGO Energy Meter integration."""

from typing import Final

DOMAIN: Final = "wago_energymeter"

# Configuration constants
DEFAULT_PORT = 502
DEFAULT_MODBUS_TIMEOUT = 5
DEFAULT_BAUDRATE = 19200
DEFAULT_PARITY = "even"

# Polling intervals (device-specific)
# MID Meter: Energy metering with cumulative counters - slower updates sufficient
SCAN_INTERVAL_MID_METER = 15
# 2857-570: Real-time power measurement - faster updates for responsive monitoring
SCAN_INTERVAL_2857_570 = 5

# Modbus settings
CONF_DEVICE_TYPE = "device_type"
CONF_BAUDRATE = "baudrate"
CONF_PARITY = "parity"
CONF_MODBUS_TIMEOUT = "modbus_timeout"

# Device types
DEVICE_TYPE_MID_METER = "mid_meter"
DEVICE_TYPE_2857_570 = "2857_570"

DEVICE_TYPES = {
    DEVICE_TYPE_MID_METER: "MID Meter (879-3000 series)",
    DEVICE_TYPE_2857_570: "3-Phase Power Measurement (2857-570/024-001)",
}

# Baudrate options
BAUDRATE_OPTIONS = [9600, 19200, 38400, 57600, 115200]

# Parity options
PARITY_OPTIONS = {
    "none": "None",
    "even": "Even",
    "odd": "Odd",
}

# Options flow
CONF_ADDITIONAL_SENSORS = "additional_sensors"

# Available additional sensors for MID meter
AVAILABLE_MID_SENSORS = {
    # Phase-specific energy values
    "energy_consumed_l1": "Active energy consumed L1",
    "energy_consumed_l2": "Active energy consumed L2",
    "energy_consumed_l3": "Active energy consumed L3",
    "energy_delivered_l1": "Active energy delivered L1",
    "energy_delivered_l2": "Active energy delivered L2",
    "energy_delivered_l3": "Active energy delivered L3",
    # Reactive energy per phase
    "reactive_energy_consumed_l1": "Reactive energy consumed L1",
    "reactive_energy_consumed_l2": "Reactive energy consumed L2",
    "reactive_energy_consumed_l3": "Reactive energy consumed L3",
    "reactive_energy_delivered_l1": "Reactive energy delivered L1",
    "reactive_energy_delivered_l2": "Reactive energy delivered L2",
    "reactive_energy_delivered_l3": "Reactive energy delivered L3",
    # Total reactive energy
    "reactive_energy_total": "Reactive energy total",
    # Tariff-based energy (T1, T2)
    "energy_consumed_t1": "Active energy consumed tariff 1",
    "energy_consumed_t2": "Active energy consumed tariff 2",
    "energy_delivered_t1": "Active energy delivered tariff 1",
    "energy_delivered_t2": "Active energy delivered tariff 2",
    "reactive_energy_consumed_t1": "Reactive energy consumed tariff 1",
    "reactive_energy_consumed_t2": "Reactive energy consumed tariff 2",
    "reactive_energy_delivered_t1": "Reactive energy delivered tariff 1",
    "reactive_energy_delivered_t2": "Reactive energy delivered tariff 2",
    # Total power values (no apparent power - not available on MID meter)
    "power_total": "Total active power",
    "reactive_power_total": "Total reactive power",
}

# Available additional sensors for 2857-570
AVAILABLE_2857_SENSORS = {
    # Total power values (always available but optional)
    "power_total": "Total active power",
    "reactive_power_total": "Total reactive power",
    "apparent_power_total": "Total apparent power",
    "power_factor_total": "Total power factor",
}
