"""Fixtures for WAGO I/O System tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.wago_io_system.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from tests.common import MockConfigEntry


def mock_modbus_data() -> list[int]:
    """Return mock Modbus configuration data for module detection."""
    # Simulate WAGO I/O system configuration:
    # Module 1: 750-362 Coupler (0x016A, 0 channels, offset 0)
    # Module 2: Digital Output 8-bit (0x8802, 8 channels, offset 0)
    # Module 3: Digital Input 8-bit (0x8801, 8 channels, offset 8)
    # Module 4: 750-451 4-Channel Analog Input 4-20mA (0x0451, 4 channels, offset 0)
    # Module 5: 750-455 2-Channel Analog Input ±10V (0x0455, 2 channels, offset 4)
    return [
        # Module 1: 750-362 Coupler
        0x016A,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        # Module 2: Digital Output 8-bit
        0x8802,
        8,
        0,
        0,
        0,
        0,
        0,
        0,
        # Module 3: Digital Input 8-bit
        0x8801,
        8,
        8,
        0,
        0,
        0,
        0,
        0,
        # Module 4: 750-451
        0x0451,
        4,
        0,
        0,
        0,
        0,
        0,
        0,
        # Module 5: 750-455
        0x0455,
        2,
        4,
        0,
        0,
        0,
        0,
        0,
    ]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.wago_io_system.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_modbus_client() -> Generator[MagicMock]:
    """Mock pyModbusTCP ModbusClient."""
    with (
        patch(
            "homeassistant.components.wago_io_system.config_flow.ModbusClient",
            autospec=True,
        ) as mock_client_config,
        patch(
            "homeassistant.components.wago_io_system.coordinator.ModbusClient",
            autospec=True,
        ) as mock_client_coord,
    ):
        # Setup config flow mock
        client = mock_client_config.return_value
        client.open.return_value = True
        client.is_open.return_value = True
        client.read_holding_registers.return_value = [0x001A, 0x2B3C, 0x4D5E]

        # Setup coordinator mock
        coord_client = mock_client_coord.return_value
        coord_client.open.return_value = True
        coord_client.is_open.return_value = True
        coord_client.read_holding_registers.return_value = mock_modbus_data()
        coord_client.read_discrete_inputs.return_value = [False] * 16
        coord_client.read_coils.return_value = [False] * 16
        coord_client.read_input_registers.return_value = [0] * 32
        coord_client.write_single_coil.return_value = True

        yield mock_client_config


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Test WAGO",
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
        unique_id="00:1a:2b:3c:4d:5e",
    )
