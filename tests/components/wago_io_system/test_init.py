"""Test the WAGO I/O System init."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture
def mock_modbus_client():
    """Return a mocked ModbusClient."""
    with patch(
        "homeassistant.components.wago_io_system.coordinator.ModbusClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.open.return_value = True
        mock_client.is_open = True

        # Mock successful configuration register read
        mock_client.read_holding_registers.return_value = [
            0x016A,  # 750-362 coupler
            0x8802,  # Digital Output 8-bit
            0x8801,  # Digital Input 8-bit
            0x01C3,  # 750-451 analog input
            0x01C7,  # 750-455 analog input
        ] + [0] * 27  # Rest of registers

        # Mock process image reads
        mock_client.read_discrete_inputs.return_value = [False] * 8
        mock_client.read_coils.return_value = [False] * 8
        mock_client.read_input_registers.return_value = [0] * 6

        yield mock_client


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_modbus_client: MagicMock,
) -> None:
    """Test successful setup from config entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_modbus_client.open.called


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setup fails when connection fails."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.wago_io_system.coordinator.ModbusClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.open.return_value = False

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_modbus_client: MagicMock,
) -> None:
    """Test successful unload of a config entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_entry_timeout(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setup fails on timeout."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.wago_io_system.coordinator.ModbusClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.open.return_value = True
        mock_client.read_holding_registers.side_effect = OSError("Connection timeout")

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
