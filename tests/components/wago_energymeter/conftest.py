"""Fixtures for WAGO Energy Meter integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.wago_energymeter.const import (
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_2857_570,
    DEVICE_TYPE_MID_METER,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture
def mock_modbus_client() -> Generator[MagicMock]:
    """Return a mocked ModbusClient."""
    with patch(
        "homeassistant.components.wago_energymeter.meter.ModbusClient", autospec=True
    ) as mock_client_class:
        # Mock successful connection
        mock_client = mock_client_class.return_value
        mock_client.open.return_value = True
        mock_client.close.return_value = None
        mock_client.is_open = True

        # Mock read methods to return empty/zero results
        mock_client.read_holding_registers.return_value = [0] * 100
        mock_client.read_input_registers.return_value = [0] * 100

        yield mock_client


@pytest.fixture
def mock_config_entry_mid() -> MockConfigEntry:
    """Return the default mocked config entry for MID meter."""
    return MockConfigEntry(
        title="WAGO MID Meter",
        domain=DOMAIN,
        data={
            CONF_NAME: "Test MID Meter",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
        },
        options={},
        unique_id="wago_mid_test_unique_id",
        entry_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    )


@pytest.fixture
def mock_config_entry_2857() -> MockConfigEntry:
    """Return the default mocked config entry for 2857-570."""
    return MockConfigEntry(
        title="WAGO 2857-570",
        domain=DOMAIN,
        data={
            CONF_NAME: "Test 2857-570",
            CONF_HOST: "192.168.1.101",
            CONF_PORT: 502,
            CONF_DEVICE_TYPE: DEVICE_TYPE_2857_570,
        },
        options={},
        unique_id="wago_2857_test_unique_id",
        entry_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
    )


@pytest.fixture
def mock_wago_meter_mid(mock_modbus_client) -> Generator[MagicMock]:
    """Return a mocked WagoMeter for MID device."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter", autospec=True
    ) as meter_mock:
        meter = meter_mock.return_value

        # Mock device info
        meter.device_name = "Test MID Meter"
        meter.device_type = DEVICE_TYPE_MID_METER
        meter.serial_number = "12345678"
        meter.firmware_version = "1.0.0"

        # Mock availability
        meter.is_available.return_value = True

        # Mock start and stop methods
        meter.start.return_value = None
        meter.stop.return_value = None

        # Mock MID meter sensor getters - voltage
        meter.get_voltage_l1.return_value = 230.0
        meter.get_voltage_l2.return_value = 230.5
        meter.get_voltage_l3.return_value = 229.8

        # Mock MID meter sensor getters - current
        meter.get_current_l1.return_value = 5.2
        meter.get_current_l2.return_value = 4.8
        meter.get_current_l3.return_value = 5.1

        # Mock MID meter sensor getters - power
        meter.get_power_l1.return_value = 1196.0
        meter.get_power_l2.return_value = 1104.0
        meter.get_power_l3.return_value = 1173.0
        meter.get_power_total.return_value = 3473.0

        # Mock MID meter sensor getters - reactive power
        meter.get_reactive_power_l1.return_value = 100.0
        meter.get_reactive_power_l2.return_value = 95.0
        meter.get_reactive_power_l3.return_value = 105.0
        meter.get_reactive_power_total.return_value = 300.0

        # Mock MID meter sensor getters - frequency
        meter.get_frequency.return_value = 50.0

        # Mock MID meter sensor getters - energy
        meter.get_energy_consumed.return_value = 3689.5
        meter.get_energy_delivered.return_value = 38.0
        meter.get_energy_consumed_l1.return_value = 1234.5
        meter.get_energy_consumed_l2.return_value = 1256.7
        meter.get_energy_consumed_l3.return_value = 1198.3
        meter.get_energy_delivered_l1.return_value = 12.3
        meter.get_energy_delivered_l2.return_value = 15.6
        meter.get_energy_delivered_l3.return_value = 10.1
        meter.get_reactive_energy_consumed.return_value = 150.0
        meter.get_reactive_energy_delivered.return_value = 15.0

        yield meter


@pytest.fixture
def mock_wago_meter_2857(mock_modbus_client) -> Generator[MagicMock]:
    """Return a mocked WagoMeter for 2857-570 device."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter", autospec=True
    ) as meter_mock:
        meter = meter_mock.return_value

        # Mock device info
        meter.device_name = "Test 2857-570"
        meter.device_type = DEVICE_TYPE_2857_570
        meter.serial_number = "87654321"
        meter.firmware_version = "2.0.0"

        # Mock availability
        meter.is_available.return_value = True

        # Mock start and stop methods
        meter.start.return_value = None
        meter.stop.return_value = None

        # Mock 2857-570 sensor getters - voltage
        meter.get_voltage_l1.return_value = 230.2
        meter.get_voltage_l2.return_value = 230.1
        meter.get_voltage_l3.return_value = 230.3

        # Mock 2857-570 sensor getters - current
        meter.get_current_l1.return_value = 10.5
        meter.get_current_l2.return_value = 10.2
        meter.get_current_l3.return_value = 10.8

        # Mock 2857-570 sensor getters - active power
        meter.get_power_l1.return_value = 2417.1
        meter.get_power_l2.return_value = 2347.0
        meter.get_power_l3.return_value = 2487.2
        meter.get_power_total.return_value = 7251.3

        # Mock 2857-570 sensor getters - reactive power
        meter.get_reactive_power_l1.return_value = 150.0
        meter.get_reactive_power_l2.return_value = 145.0
        meter.get_reactive_power_l3.return_value = 155.0
        meter.get_reactive_power_total.return_value = 450.0

        # Mock 2857-570 sensor getters - apparent power
        meter.get_apparent_power_l1.return_value = 2421.7
        meter.get_apparent_power_l2.return_value = 2351.5
        meter.get_apparent_power_l3.return_value = 2491.9
        meter.get_apparent_power_total.return_value = 7265.1

        # Mock 2857-570 sensor getters - power factor
        meter.get_power_factor_l1.return_value = 0.998
        meter.get_power_factor_l2.return_value = 0.998
        meter.get_power_factor_l3.return_value = 0.998
        meter.get_power_factor_total.return_value = 0.998

        # Mock 2857-570 sensor getters - frequency
        meter.get_frequency.return_value = 50.05

        yield meter


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.wago_energymeter.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
async def init_integration_mid(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> MockConfigEntry:
    """Set up the WAGO Energy Meter integration for testing with MID meter."""
    mock_config_entry_mid.add_to_hass(hass)

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry_mid


@pytest.fixture
async def init_integration_2857(
    hass: HomeAssistant,
    mock_config_entry_2857: MockConfigEntry,
    mock_wago_meter_2857: MagicMock,
) -> MockConfigEntry:
    """Set up the WAGO Energy Meter integration for testing with 2857-570."""
    mock_config_entry_2857.add_to_hass(hass)

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_2857,
    ):
        await hass.config_entries.async_setup(mock_config_entry_2857.entry_id)
        await hass.async_block_till_done()

    return mock_config_entry_2857
