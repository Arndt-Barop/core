"""Fixtures for WAGO I/O System tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.wago_io_system.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT

from tests.common import MockConfigEntry


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
    with patch(
        "homeassistant.components.wago_io_system.config_flow.ModbusClient",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.open.return_value = True
        # Mock MAC address reading (3 registers = 6 bytes)
        client.read_holding_registers.return_value = [0x001A, 0x2B3C, 0x4D5E]
        yield mock_client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
        unique_id="00:1a:2b:3c:4d:5e",
    )
