"""Tests for the WAGO I/O System config flow."""

from unittest.mock import MagicMock

import pytest

from homeassistant import config_entries
from homeassistant.components.wago_io_system.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_form_user_success(
    hass: HomeAssistant, mock_modbus_client: MagicMock, mock_setup_entry: MagicMock
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WAGO Controller (192.168.2.44)"
    assert result["data"] == {
        CONF_HOST: "192.168.2.44",
        CONF_PORT: 502,
        CONF_SCAN_INTERVAL: 1,
    }
    assert result["result"].unique_id == "00:1a:2b:3c:4d:5e"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(
    hass: HomeAssistant, mock_modbus_client: MagicMock
) -> None:
    """Test connection error."""
    mock_modbus_client.return_value.open.return_value = False

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_cannot_read_mac(
    hass: HomeAssistant, mock_modbus_client: MagicMock
) -> None:
    """Test MAC address reading error."""
    mock_modbus_client.return_value.read_holding_registers.return_value = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_already_configured(
    hass: HomeAssistant,
    mock_modbus_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test duplicate entry."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_form_exception(
    hass: HomeAssistant, mock_modbus_client: MagicMock
) -> None:
    """Test unexpected exception."""
    mock_modbus_client.return_value.open.side_effect = Exception("Test exception")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.2.44",
            CONF_PORT: 502,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown"}


@pytest.mark.parametrize(
    ("host", "port"),
    [
        ("10.0.0.1", 502),
        ("192.168.1.100", 5020),
        ("wago-controller.local", 502),
    ],
)
async def test_form_various_inputs(
    hass: HomeAssistant,
    mock_modbus_client: MagicMock,
    mock_setup_entry: MagicMock,
    host: str,
    port: int,
) -> None:
    """Test form with various valid inputs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: host,
            CONF_PORT: port,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == host
    assert result["data"][CONF_PORT] == port
