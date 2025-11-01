"""Test sensor entity configuration for WAGO Energy Meter integration."""

from unittest.mock import MagicMock, patch

from homeassistant.const import (
    STATE_UNAVAILABLE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry


async def test_mid_meter_sensor_configuration(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test MID meter sensors are correctly configured."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    # Check voltage L1 sensor exists with correct configuration
    state = hass.states.get("sensor.test_mid_meter_voltage_l1")
    assert state is not None
    assert state.attributes["unit_of_measurement"] == UnitOfElectricPotential.VOLT
    assert state.attributes["device_class"] == "voltage"
    assert state.attributes["state_class"] == "measurement"

    # Check all three voltage sensors exist
    for phase in ["l1", "l2", "l3"]:
        state = hass.states.get(f"sensor.test_mid_meter_voltage_{phase}")
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfElectricPotential.VOLT

    # Check all three current sensors exist
    for phase in ["l1", "l2", "l3"]:
        state = hass.states.get(f"sensor.test_mid_meter_current_{phase}")
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfElectricCurrent.AMPERE
        assert state.attributes["device_class"] == "current"

    # Check all three power sensors exist
    for phase in ["l1", "l2", "l3"]:
        state = hass.states.get(f"sensor.test_mid_meter_power_{phase}")
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfPower.WATT
        assert state.attributes["device_class"] == "power"

    # Check frequency sensor exists
    state = hass.states.get("sensor.test_mid_meter_frequency")
    assert state is not None
    assert state.attributes["unit_of_measurement"] == UnitOfFrequency.HERTZ
    assert state.attributes["device_class"] == "frequency"

    # Check energy sensors exist
    state = hass.states.get("sensor.test_mid_meter_active_energy_consumed")
    assert state is not None
    assert state.attributes["unit_of_measurement"] == UnitOfEnergy.KILO_WATT_HOUR
    assert state.attributes["device_class"] == "energy"
    assert state.attributes["state_class"] == "total_increasing"

    state = hass.states.get("sensor.test_mid_meter_active_energy_delivered")
    assert state is not None
    assert state.attributes["state_class"] == "total_increasing"

    # Check reactive energy sensors exist
    state = hass.states.get("sensor.test_mid_meter_reactive_energy_consumed")
    assert state is not None
    assert state.attributes["unit_of_measurement"] == "kvarh"
    assert state.attributes["state_class"] == "total_increasing"

    state = hass.states.get("sensor.test_mid_meter_reactive_energy_delivered")
    assert state is not None
    assert state.attributes["unit_of_measurement"] == "kvarh"


async def test_2857_570_sensor_configuration(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry_2857: MockConfigEntry,
    mock_wago_meter_2857: MagicMock,
) -> None:
    """Test 2857-570 sensors are correctly configured."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_2857,
    ):
        mock_config_entry_2857.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_2857.entry_id)
        await hass.async_block_till_done()

    # Check basic sensors for all three phases
    for phase in ["l1", "l2", "l3"]:
        # Voltage
        state = hass.states.get(f"sensor.test_2857_570_voltage_{phase}")
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfElectricPotential.VOLT
        assert state.attributes["device_class"] == "voltage"

        # Current
        state = hass.states.get(f"sensor.test_2857_570_current_{phase}")
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfElectricCurrent.AMPERE
        assert state.attributes["device_class"] == "current"

        # Active power
        state = hass.states.get(f"sensor.test_2857_570_power_{phase}")
        assert state is not None
        assert state.attributes["unit_of_measurement"] == UnitOfPower.WATT
        assert state.attributes["device_class"] == "power"

        # Reactive power
        state = hass.states.get(f"sensor.test_2857_570_reactive_power_{phase}")
        assert state is not None
        assert (
            state.attributes["unit_of_measurement"]
            == UnitOfReactivePower.VOLT_AMPERE_REACTIVE
        )
        assert state.attributes["device_class"] == "reactive_power"

        # Apparent power
        state = hass.states.get(f"sensor.test_2857_570_apparent_power_{phase}")
        assert state is not None
        assert (
            state.attributes["unit_of_measurement"] == UnitOfApparentPower.VOLT_AMPERE
        )
        assert state.attributes["device_class"] == "apparent_power"

        # Power factor
        state = hass.states.get(f"sensor.test_2857_570_power_factor_{phase}")
        assert state is not None
        assert state.attributes["device_class"] == "power_factor"
        # Power factor has no unit
        assert "unit_of_measurement" not in state.attributes

    # Check frequency sensor
    state = hass.states.get("sensor.test_2857_570_frequency")
    assert state is not None
    assert state.attributes["unit_of_measurement"] == UnitOfFrequency.HERTZ
    assert state.attributes["device_class"] == "frequency"


async def test_sensor_availability_when_meter_unavailable(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test sensor becomes unavailable when meter is not available."""
    # Set meter to unavailable
    mock_wago_meter_mid.is_available.return_value = False

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    # All sensors should be unavailable
    state = hass.states.get("sensor.test_mid_meter_voltage_l1")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_sensor_entity_registry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test sensor entities are correctly registered."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    # Check voltage L1 entity is registered
    entity = entity_registry.async_get("sensor.test_mid_meter_voltage_l1")
    assert entity is not None
    assert entity.unique_id == f"{mock_config_entry_mid.entry_id}_voltage_l1"
    assert entity.original_device_class == "voltage"

    # Check energy entity is registered with correct state class
    entity = entity_registry.async_get("sensor.test_mid_meter_active_energy_consumed")
    assert entity is not None
    assert entity.unique_id == f"{mock_config_entry_mid.entry_id}_energy_consumed"
    assert entity.original_device_class == "energy"
