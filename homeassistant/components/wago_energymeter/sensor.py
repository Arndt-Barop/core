"""Platform for sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_NAME,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WAGOEnergyMeterConfigEntry
from .const import (
    CONF_ADDITIONAL_SENSORS,
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_2857_570,
    DEVICE_TYPE_MID_METER,
    DEVICE_TYPES,
    DOMAIN,
)
from .meter import WagoMeter

_LOGGER = logging.getLogger(__name__)

# Limit parallel updates to avoid overwhelming the device
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WAGOEnergyMeterConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WAGO Energy Meter sensors from a config entry."""
    meter_instance: WagoMeter = entry.runtime_data
    device_name = entry.data[CONF_NAME]
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_MID_METER)

    # Get device model based on device type
    model = DEVICE_TYPES.get(device_type, "Unknown WAGO Device")

    # Create device info for this meter
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=device_name,
        manufacturer="WAGO",
        model=model,
    )

    entities = []
    # Adding 3 phases sensors (common to all devices)
    for phase in range(1, 4):
        entities.extend(
            [
                WAGO_MID_Voltage(meter_instance, phase, entry.entry_id, device_info),
                WAGO_MID_Current(meter_instance, phase, entry.entry_id, device_info),
                WAGO_MID_Power(meter_instance, phase, entry.entry_id, device_info),
            ]
        )
    entities.append(WAGO_MID_Freq(meter_instance, entry.entry_id, device_info))

    # Add MID meter energy sensors (consumption/delivery)
    if device_type == DEVICE_TYPE_MID_METER:
        entities.extend(
            [
                # Total energy consumption/delivery (always enabled)
                WAGO_MID_Energy_Consumed(
                    meter_instance, entry.entry_id, device_info, enabled=True
                ),
                WAGO_MID_Energy_Delivered(
                    meter_instance, entry.entry_id, device_info, enabled=True
                ),
                # Reactive energy consumption/delivery (always enabled)
                WAGO_MID_ReactiveEnergy_Consumed(
                    meter_instance, entry.entry_id, device_info, enabled=True
                ),
                WAGO_MID_ReactiveEnergy_Delivered(
                    meter_instance, entry.entry_id, device_info, enabled=True
                ),
            ]
        )

        # Add optional sensors based on user selection in options
        selected_sensors = entry.options.get(CONF_ADDITIONAL_SENSORS, [])
        if selected_sensors:
            _LOGGER.debug(
                "Creating %d additional sensors: %s",
                len(selected_sensors),
                selected_sensors,
            )
            # Mapping of sensor IDs to configuration tuples
            # Format: (translation_key, getter_method, unit)
            energy_sensor_configs = {
                # Phase-specific active energy
                "energy_consumed_l1": (
                    "energy_consumed_l1",
                    "get_energy_consumed_l1",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_consumed_l2": (
                    "energy_consumed_l2",
                    "get_energy_consumed_l2",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_consumed_l3": (
                    "energy_consumed_l3",
                    "get_energy_consumed_l3",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_delivered_l1": (
                    "energy_delivered_l1",
                    "get_energy_delivered_l1",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_delivered_l2": (
                    "energy_delivered_l2",
                    "get_energy_delivered_l2",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_delivered_l3": (
                    "energy_delivered_l3",
                    "get_energy_delivered_l3",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                # Phase-specific reactive energy
                "reactive_energy_consumed_l1": (
                    "reactive_energy_consumed_l1",
                    "get_reactive_energy_consumed_l1",
                    "kvarh",
                ),
                "reactive_energy_consumed_l2": (
                    "reactive_energy_consumed_l2",
                    "get_reactive_energy_consumed_l2",
                    "kvarh",
                ),
                "reactive_energy_consumed_l3": (
                    "reactive_energy_consumed_l3",
                    "get_reactive_energy_consumed_l3",
                    "kvarh",
                ),
                "reactive_energy_delivered_l1": (
                    "reactive_energy_delivered_l1",
                    "get_reactive_energy_delivered_l1",
                    "kvarh",
                ),
                "reactive_energy_delivered_l2": (
                    "reactive_energy_delivered_l2",
                    "get_reactive_energy_delivered_l2",
                    "kvarh",
                ),
                "reactive_energy_delivered_l3": (
                    "reactive_energy_delivered_l3",
                    "get_reactive_energy_delivered_l3",
                    "kvarh",
                ),
                # Tariff-based active energy
                "energy_consumed_t1": (
                    "energy_consumed_t1",
                    "get_energy_consumed_t1",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_consumed_t2": (
                    "energy_consumed_t2",
                    "get_energy_consumed_t2",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_delivered_t1": (
                    "energy_delivered_t1",
                    "get_energy_delivered_t1",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                "energy_delivered_t2": (
                    "energy_delivered_t2",
                    "get_energy_delivered_t2",
                    UnitOfEnergy.KILO_WATT_HOUR,
                ),
                # Tariff-based reactive energy
                "reactive_energy_consumed_t1": (
                    "reactive_energy_consumed_t1",
                    "get_reactive_energy_consumed_t1",
                    "kvarh",
                ),
                "reactive_energy_consumed_t2": (
                    "reactive_energy_consumed_t2",
                    "get_reactive_energy_consumed_t2",
                    "kvarh",
                ),
                "reactive_energy_delivered_t1": (
                    "reactive_energy_delivered_t1",
                    "get_reactive_energy_delivered_t1",
                    "kvarh",
                ),
                "reactive_energy_delivered_t2": (
                    "reactive_energy_delivered_t2",
                    "get_reactive_energy_delivered_t2",
                    "kvarh",
                ),
                # Total reactive energy
                "reactive_energy_total": (
                    "reactive_energy_total",
                    "get_reactive_energy_total",
                    "kvarh",
                ),
            }

            # Mapping for power sensors (use existing classes, no apparent power for MID)
            power_sensor_mapping = {
                "power_total": WAGO_Generic_Power_Total,
                "reactive_power_total": WAGO_Generic_Reactive_Power_Total,
            }

            for sensor_id in selected_sensors:
                # Check if it's an energy sensor
                if sensor_id in energy_sensor_configs:
                    translation_key, getter_method, unit = energy_sensor_configs[
                        sensor_id
                    ]
                    entities.append(
                        WAGO_MID_Generic_Energy(
                            meter_instance,
                            entry.entry_id,
                            device_info,
                            sensor_id,
                            translation_key,
                            getter_method,
                            unit,
                        )
                    )
                # Check if it's a power sensor
                elif sensor_id in power_sensor_mapping:
                    sensor_class = power_sensor_mapping[sensor_id]
                    entities.append(
                        sensor_class(meter_instance, entry.entry_id, device_info)
                    )
                else:
                    _LOGGER.warning(
                        "Sensor '%s' not yet implemented, skipping", sensor_id
                    )

    # Add device-specific sensors for 2857-570
    if device_type == DEVICE_TYPE_2857_570:
        # Add optional sensors based on user selection in options
        selected_sensors = entry.options.get(CONF_ADDITIONAL_SENSORS, [])
        if selected_sensors:
            _LOGGER.debug(
                "Creating %d additional sensors for 2857-570: %s",
                len(selected_sensors),
                selected_sensors,
            )
            # Mapping of sensor IDs to sensor classes for 2857-570
            sensor_mapping: dict[str, type[SensorEntity]] = {
                "power_total": WAGO_Generic_Power_Total,
                "reactive_power_total": WAGO_Generic_Reactive_Power_Total,
                "apparent_power_total": WAGO_Generic_Apparent_Power_Total,
                "power_factor_total": WAGO_Generic_Power_Factor_Total,
            }

            for sensor_id in selected_sensors:
                sensor_class = sensor_mapping.get(sensor_id)  # type: ignore[assignment]
                if sensor_class is not None:
                    entities.append(
                        sensor_class(meter_instance, entry.entry_id, device_info)
                    )
                else:
                    _LOGGER.warning(
                        "Sensor '%s' not yet implemented for 2857-570, skipping",
                        sensor_id,
                    )

        # Add phase-specific sensors for 2857-570
        for phase in range(1, 4):
            entities.extend(
                [
                    WAGO_2857_ReactivePower(
                        meter_instance, phase, entry.entry_id, device_info
                    ),
                    WAGO_2857_ApparentPower(
                        meter_instance, phase, entry.entry_id, device_info
                    ),
                    WAGO_2857_PowerFactor(
                        meter_instance, phase, entry.entry_id, device_info
                    ),
                ]
            )

    async_add_entities(entities)


class WAGO_MID_Voltage(SensorEntity):
    """Representation of a WAGO EnergyMeter."""

    _attr_has_entity_name = True
    _attr_translation_key = "voltage"
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, meter, number: int, entry_id: str, device_info: DeviceInfo
    ) -> None:
        """Initialize an WAGO MID."""
        self._number = number
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_voltage_l{number}"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_translation_placeholders = {"phase": str(number)}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter voltage L%s is unavailable: Unable to read Modbus registers",
                    self._number,
                )
                self._attr_available = False
            return

        try:
            voltage_fun = getattr(self._meter, f"getUL{self._number}")
            x = voltage_fun()
            _LOGGER.debug("Get Value: %s", round(x, 4))
            self._attr_native_value = x
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO Energy Meter voltage L%s is back online", self._number
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter voltage L%s is unavailable: %s",
                    self._number,
                    err,
                )
                self._attr_available = False


class WAGO_MID_Current(SensorEntity):
    """WAGO EnergyMeter Current."""

    _attr_has_entity_name = True
    _attr_translation_key = "current"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, meter, number: int, entry_id: str, device_info: DeviceInfo
    ) -> None:
        """Initialize an WAGO MID current sensor."""
        self._number = number
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_current_l{number}"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_translation_placeholders = {"phase": str(number)}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter current L%s is unavailable: Unable to read Modbus registers",
                    self._number,
                )
                self._attr_available = False
            return

        try:
            current_fun = getattr(self._meter, f"getIL{self._number}")
            x = current_fun()
            _LOGGER.debug("Get Value: %s", round(x, 4))
            self._attr_native_value = x
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO Energy Meter current L%s is back online", self._number
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter current L%s is unavailable: %s",
                    self._number,
                    err,
                )
                self._attr_available = False


class WAGO_MID_Power(SensorEntity):
    """WAGO EnergyMeter Power."""

    _attr_has_entity_name = True
    _attr_translation_key = "power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, meter, number: int, entry_id: str, device_info: DeviceInfo
    ) -> None:
        """Initialize an WAGO MID power sensor."""
        self._number = number
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_power_l{number}"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_translation_placeholders = {"phase": str(number)}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter power L%s is unavailable: Unable to read Modbus registers",
                    self._number,
                )
                self._attr_available = False
            return

        try:
            power_fun = getattr(self._meter, f"getPL{self._number}")
            x = power_fun()
            _LOGGER.debug("Get Value: %s", round(x, 4))
            self._attr_native_value = x
            if not self._attr_available:
                _LOGGER.info("WAGO Energy Meter power L%s is back online", self._number)
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter power L%s is unavailable: %s", self._number, err
                )
                self._attr_available = False


class WAGO_MID_Freq(SensorEntity):
    """WAGO EnergyMeter Frequency."""

    _attr_has_entity_name = True
    _attr_translation_key = "frequency"
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, meter, entry_id: str, device_info: DeviceInfo) -> None:
        """Initialize an WAGO MID frequency sensor."""
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_frequency"
        self._attr_available = False
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter frequency is unavailable: Unable to read Modbus registers"
                )
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_frequency()
            if not self._attr_available:
                _LOGGER.info("WAGO Energy Meter frequency is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning("WAGO Energy Meter frequency is unavailable: %s", err)
                self._attr_available = False


class WAGO_MID_Energy_Consumed(SensorEntity):
    """WAGO MID Energy Meter Total Active Energy Consumed (Bezug)."""

    _attr_has_entity_name = True
    _attr_translation_key = "energy_consumed"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, meter, entry_id: str, device_info: DeviceInfo, enabled: bool = True
    ) -> None:
        """Initialize a WAGO MID energy consumed sensor."""
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_energy_consumed"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_entity_registry_enabled_default = enabled

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter energy consumed is unavailable: Unable to read Modbus registers"
                )
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_energy_consumed()
            if not self._attr_available:
                _LOGGER.info("WAGO Energy Meter energy consumed is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter energy consumed is unavailable: %s", err
                )
                self._attr_available = False


class WAGO_MID_Energy_Delivered(SensorEntity):
    """WAGO MID Energy Meter Total Active Energy Delivered (Lieferung)."""

    _attr_has_entity_name = True
    _attr_translation_key = "energy_delivered"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, meter, entry_id: str, device_info: DeviceInfo, enabled: bool = True
    ) -> None:
        """Initialize a WAGO MID energy delivered sensor."""
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_energy_delivered"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_entity_registry_enabled_default = enabled

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter energy delivered is unavailable: Unable to read Modbus registers"
                )
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_energy_delivered()
            if not self._attr_available:
                _LOGGER.info("WAGO Energy Meter energy delivered is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter energy delivered is unavailable: %s", err
                )
                self._attr_available = False


class WAGO_MID_ReactiveEnergy_Consumed(SensorEntity):
    """WAGO MID Energy Meter Total Reactive Energy Consumed (Bezug Blindenergie)."""

    _attr_has_entity_name = True
    _attr_translation_key = "reactive_energy_consumed"
    _attr_native_unit_of_measurement = "kvarh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, meter, entry_id: str, device_info: DeviceInfo, enabled: bool = True
    ) -> None:
        """Initialize a WAGO MID reactive energy consumed sensor."""
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_reactive_energy_consumed"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_entity_registry_enabled_default = enabled

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter reactive energy consumed is unavailable: Unable to read Modbus registers"
                )
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_reactive_energy_consumed()
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO Energy Meter reactive energy consumed is back online"
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter reactive energy consumed is unavailable: %s", err
                )
                self._attr_available = False


class WAGO_MID_ReactiveEnergy_Delivered(SensorEntity):
    """WAGO MID Energy Meter Total Reactive Energy Delivered (Lieferung Blindenergie)."""

    _attr_has_entity_name = True
    _attr_translation_key = "reactive_energy_delivered"
    _attr_native_unit_of_measurement = "kvarh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self, meter, entry_id: str, device_info: DeviceInfo, enabled: bool = True
    ) -> None:
        """Initialize a WAGO MID reactive energy delivered sensor."""
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_reactive_energy_delivered"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_entity_registry_enabled_default = enabled

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter reactive energy delivered is unavailable: Unable to read Modbus registers"
                )
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_reactive_energy_delivered()
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO Energy Meter reactive energy delivered is back online"
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO Energy Meter reactive energy delivered is unavailable: %s",
                    err,
                )
                self._attr_available = False


class WAGO_2857_ReactivePower(SensorEntity):
    """WAGO 2857-570 Reactive Power."""

    _attr_has_entity_name = True
    _attr_translation_key = "reactive_power"
    _attr_native_unit_of_measurement = UnitOfReactivePower.VOLT_AMPERE_REACTIVE
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, meter, number: int, entry_id: str, device_info: DeviceInfo
    ) -> None:
        """Initialize a WAGO 2857-570 reactive power sensor."""
        self._number = number
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_reactive_power_l{number}"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_translation_placeholders = {"phase": str(number)}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO 2857-570 reactive power L%s is unavailable: Unable to read Modbus registers",
                    self._number,
                )
                self._attr_available = False
            return

        try:
            reactive_power_fun = getattr(
                self._meter, f"get_reactive_power_l{self._number}"
            )
            x = reactive_power_fun()
            _LOGGER.debug("Get Reactive Power L%s: %s", self._number, round(x, 4))
            self._attr_native_value = x
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO 2857-570 reactive power L%s is back online", self._number
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO 2857-570 reactive power L%s is unavailable: %s",
                    self._number,
                    err,
                )
                self._attr_available = False


class WAGO_2857_ApparentPower(SensorEntity):
    """WAGO 2857-570 Apparent Power."""

    _attr_has_entity_name = True
    _attr_translation_key = "apparent_power"
    _attr_native_unit_of_measurement = UnitOfApparentPower.VOLT_AMPERE
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, meter, number: int, entry_id: str, device_info: DeviceInfo
    ) -> None:
        """Initialize a WAGO 2857-570 apparent power sensor."""
        self._number = number
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_apparent_power_l{number}"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_translation_placeholders = {"phase": str(number)}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO 2857-570 apparent power L%s is unavailable: Unable to read Modbus registers",
                    self._number,
                )
                self._attr_available = False
            return

        try:
            apparent_power_fun = getattr(
                self._meter, f"get_apparent_power_l{self._number}"
            )
            x = apparent_power_fun()
            _LOGGER.debug("Get Apparent Power L%s: %s", self._number, round(x, 4))
            self._attr_native_value = x
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO 2857-570 apparent power L%s is back online", self._number
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO 2857-570 apparent power L%s is unavailable: %s",
                    self._number,
                    err,
                )
                self._attr_available = False


class WAGO_2857_PowerFactor(SensorEntity):
    """WAGO 2857-570 Power Factor."""

    _attr_has_entity_name = True
    _attr_translation_key = "power_factor"
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, meter, number: int, entry_id: str, device_info: DeviceInfo
    ) -> None:
        """Initialize a WAGO 2857-570 power factor sensor."""
        self._number = number
        self._meter = meter
        self._attr_unique_id = f"{entry_id}_power_factor_l{number}"
        self._attr_available = False
        self._attr_device_info = device_info
        self._attr_translation_placeholders = {"phase": str(number)}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._attr_available

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        # Check if meter is available first
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO 2857-570 power factor L%s is unavailable: Unable to read Modbus registers",
                    self._number,
                )
                self._attr_available = False
            return

        try:
            power_factor_fun = getattr(self._meter, f"get_power_factor_l{self._number}")
            x = power_factor_fun()
            _LOGGER.debug("Get Power Factor L%s: %s", self._number, round(x, 4))
            self._attr_native_value = x
            if not self._attr_available:
                _LOGGER.info(
                    "WAGO 2857-570 power factor L%s is back online", self._number
                )
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "WAGO 2857-570 power factor L%s is unavailable: %s",
                    self._number,
                    err,
                )
                self._attr_available = False


class WAGO_Generic_Power_Total(SensorEntity):
    """Generic total active power sensor for both device types."""

    _attr_has_entity_name = True
    _attr_translation_key = "power_total"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(
        self,
        meter: WagoMeter,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        self._meter = meter
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry_id}_power_total"
        self._attr_available = True

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning("Power total is unavailable")
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_power_total()
            if not self._attr_available:
                _LOGGER.info("Power total is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning("Power total is unavailable: %s", err)
                self._attr_available = False


class WAGO_Generic_Reactive_Power_Total(SensorEntity):
    """Generic total reactive power sensor for both device types."""

    _attr_has_entity_name = True
    _attr_translation_key = "reactive_power_total"
    _attr_device_class = SensorDeviceClass.REACTIVE_POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfReactivePower.VOLT_AMPERE_REACTIVE

    def __init__(
        self,
        meter: WagoMeter,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        self._meter = meter
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry_id}_reactive_power_total"
        self._attr_available = True

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning("Reactive power total is unavailable")
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_reactive_power_total()
            if not self._attr_available:
                _LOGGER.info("Reactive power total is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning("Reactive power total is unavailable: %s", err)
                self._attr_available = False


class WAGO_Generic_Apparent_Power_Total(SensorEntity):
    """Generic total apparent power sensor (2857-570 only)."""

    _attr_has_entity_name = True
    _attr_translation_key = "apparent_power_total"
    _attr_device_class = SensorDeviceClass.APPARENT_POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfApparentPower.VOLT_AMPERE

    def __init__(
        self,
        meter: WagoMeter,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        self._meter = meter
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry_id}_apparent_power_total"
        self._attr_available = True

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning("Apparent power total is unavailable")
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_apparent_power_total()
            if not self._attr_available:
                _LOGGER.info("Apparent power total is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning("Apparent power total is unavailable: %s", err)
                self._attr_available = False


class WAGO_Generic_Power_Factor_Total(SensorEntity):
    """Generic total power factor sensor (2857-570 only)."""

    _attr_has_entity_name = True
    _attr_translation_key = "power_factor_total"
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        meter: WagoMeter,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        self._meter = meter
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry_id}_power_factor_total"
        self._attr_available = True

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning("Power factor total is unavailable")
                self._attr_available = False
            return

        try:
            self._attr_native_value = self._meter.get_power_factor_total()
            if not self._attr_available:
                _LOGGER.info("Power factor total is back online")
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning("Power factor total is unavailable: %s", err)
                self._attr_available = False


class WAGO_MID_Generic_Energy(SensorEntity):
    """Generic energy sensor for MID meter with flexible configuration."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        meter: WagoMeter,
        entry_id: str,
        device_info: DeviceInfo,
        sensor_id: str,
        translation_key: str,
        getter_method: str,
        unit: str = UnitOfEnergy.KILO_WATT_HOUR,
    ) -> None:
        """Initialize the sensor."""
        self._meter = meter
        self._attr_device_info = device_info
        self._attr_unique_id = f"{entry_id}_{sensor_id}"
        self._attr_translation_key = translation_key
        self._attr_native_unit_of_measurement = unit
        self._getter_method = getter_method
        self._attr_available = True

    def update(self) -> None:
        """Fetch new state data for the sensor."""
        if not self._meter.is_available():
            if self._attr_available:
                _LOGGER.warning("%s is unavailable", self._attr_translation_key)
                self._attr_available = False
            return

        try:
            getter = getattr(self._meter, self._getter_method)
            self._attr_native_value = getter()
            if not self._attr_available:
                _LOGGER.info("%s is back online", self._attr_translation_key)
                self._attr_available = True
        except (OSError, AttributeError) as err:
            if self._attr_available:
                _LOGGER.warning(
                    "%s is unavailable: %s", self._attr_translation_key, err
                )
                self._attr_available = False
