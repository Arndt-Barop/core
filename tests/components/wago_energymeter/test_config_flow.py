"""Test the WAGO Energy Meter config flow."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.wago_energymeter.const import (
    CONF_ADDITIONAL_SENSORS,
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_2857_570,
    DEVICE_TYPE_MID_METER,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


async def test_user_flow_mid_meter(hass: HomeAssistant, mock_wago_meter_mid) -> None:
    """Test user flow for MID meter configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Complete setup in one step
    with (
        patch(
            "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
        ) as mock_modbus,
        patch(
            "homeassistant.components.wago_energymeter.WagoMeter",
            return_value=mock_wago_meter_mid,
        ),
    ):
        # Mock successful Modbus connection
        mock_modbus.return_value.open.return_value = True
        mock_modbus.return_value.close.return_value = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test MID Meter",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test MID Meter"
    assert result["data"][CONF_NAME] == "Test MID Meter"
    assert result["data"][CONF_HOST] == "192.168.1.100"
    assert result["data"][CONF_PORT] == 502
    assert result["data"][CONF_DEVICE_TYPE] == DEVICE_TYPE_MID_METER


async def test_user_flow_2857_570(hass: HomeAssistant, mock_wago_meter_2857) -> None:
    """Test user flow for 2857-570 configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
        ) as mock_modbus,
        patch(
            "homeassistant.components.wago_energymeter.WagoMeter",
            return_value=mock_wago_meter_2857,
        ),
    ):
        mock_modbus.return_value.open.return_value = True
        mock_modbus.return_value.close.return_value = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test 2857-570",
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_2857_570,
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test 2857-570"
    assert result["data"][CONF_DEVICE_TYPE] == DEVICE_TYPE_2857_570


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """Test user flow with connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
    ) as mock_modbus:
        # Mock failed Modbus connection
        mock_modbus.return_value.open.return_value = False

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test Meter",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_exception(hass: HomeAssistant) -> None:
    """Test user flow with unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.wago_energymeter.config_flow.ModbusClient",
        side_effect=Exception("Unexpected error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test Meter",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
            },
        )

    # Exception during ModbusClient creation is caught and treated as connection error
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_entry(hass: HomeAssistant, mock_wago_meter_mid) -> None:
    """Test that duplicate entries are prevented."""
    # Create existing entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Existing Meter",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
        },
        unique_id=None,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
        ) as mock_modbus,
        patch(
            "homeassistant.components.wago_energymeter.WagoMeter",
            return_value=mock_wago_meter_mid,
        ),
    ):
        mock_modbus.return_value.open.return_value = True
        mock_modbus.return_value.close.return_value = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Duplicate Meter",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_flow(
    hass: HomeAssistant, mock_config_entry_mid: MockConfigEntry, mock_wago_meter_mid
) -> None:
    """Test reconfigure flow."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await mock_config_entry_mid.start_reconfigure_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with (
        patch(
            "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
        ) as mock_modbus,
        patch(
            "homeassistant.components.wago_energymeter.WagoMeter",
            return_value=mock_wago_meter_mid,
        ),
    ):
        mock_modbus.return_value.open.return_value = True
        mock_modbus.return_value.close.return_value = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.150",
                CONF_PORT: 503,
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry_mid.data[CONF_HOST] == "192.168.1.150"
    assert mock_config_entry_mid.data[CONF_PORT] == 503


async def test_reauth_flow(
    hass: HomeAssistant, mock_config_entry_mid: MockConfigEntry, mock_wago_meter_mid
) -> None:
    """Test reauth flow."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await mock_config_entry_mid.start_reauth_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with (
        patch(
            "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
        ) as mock_modbus,
        patch(
            "homeassistant.components.wago_energymeter.WagoMeter",
            return_value=mock_wago_meter_mid,
        ),
    ):
        mock_modbus.return_value.open.return_value = True
        mock_modbus.return_value.close.return_value = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"


async def test_options_flow_mid_meter(
    hass: HomeAssistant, mock_config_entry_mid: MockConfigEntry
) -> None:
    """Test options flow for MID meter."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        mock_config_entry_mid.entry_id
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Test selecting additional sensors
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDITIONAL_SENSORS: [
                "energy_consumed_l1",
                "energy_consumed_l2",
                "reactive_power_total",
            ]
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_ADDITIONAL_SENSORS: [
            "energy_consumed_l1",
            "energy_consumed_l2",
            "reactive_power_total",
        ]
    }


async def test_options_flow_2857_570_no_options(
    hass: HomeAssistant, mock_config_entry_2857: MockConfigEntry
) -> None:
    """Test that 2857-570 has no options flow."""
    mock_config_entry_2857.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        mock_config_entry_2857.entry_id
    )

    # 2857-570 should not have options flow (all sensors always enabled)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_no_sensor_selection(
    hass: HomeAssistant, mock_config_entry_mid: MockConfigEntry
) -> None:
    """Test options flow when no additional sensors are selected."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        mock_config_entry_mid.entry_id
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Configure with empty sensor list
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ADDITIONAL_SENSORS: []},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ADDITIONAL_SENSORS] == []


async def test_user_flow_modbus_timeout(
    hass: HomeAssistant, mock_wago_meter_mid: MagicMock
) -> None:
    """Test user flow with Modbus timeout error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Mock timeout exception in ModbusClient.open()
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
    ) as mock_client:
        mock_client.return_value.open.side_effect = asyncio.TimeoutError

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Test Device",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_modbus_error(
    hass: HomeAssistant, mock_wago_meter_mid: MagicMock
) -> None:
    """Test user flow with general Modbus error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Mock general exception in ModbusClient
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
    ) as mock_client:
        mock_client.return_value.open.side_effect = Exception("Connection failed")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_NAME: "Test Device",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_flow_connection_error(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test reauth flow with connection error."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await mock_config_entry_mid.start_reauth_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Mock connection error in ModbusClient
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
    ) as mock_client:
        mock_client.return_value.open.return_value = False

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 502,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_flow_connection_error(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test reconfigure flow with connection error."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await mock_config_entry_mid.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Mock timeout in ModbusClient
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.ModbusClient"
    ) as mock_client:
        mock_client.return_value.open.side_effect = OSError("Connection timeout")

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 502,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
