"""Test edge cases in config flow for WAGO Energy Meter integration."""

from unittest.mock import MagicMock, patch

from homeassistant import config_entries
from homeassistant.components.wago_energymeter.const import (
    CONF_ADDITIONAL_SENSORS,
    CONF_DEVICE_TYPE,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry


async def test_user_flow_unexpected_exception(
    hass: HomeAssistant,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test user flow with unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    # Mock validate_input to raise unexpected exception
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.validate_input",
        side_effect=RuntimeError("Unexpected error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Test Device",
                CONF_HOST: "10.42.0.57",
                CONF_PORT: 502,
                CONF_DEVICE_TYPE: "mid_meter",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_reauth_flow_unexpected_exception(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
) -> None:
    """Test reauth flow with unexpected exception."""
    mock_config_entry_mid.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry_mid.entry_id,
        },
    )

    # Mock validate_input to raise unexpected exception
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.validate_input",
        side_effect=ValueError("Unexpected error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "10.42.0.58",
                CONF_PORT: 503,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_reconfigure_flow_unexpected_exception(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
) -> None:
    """Test reconfigure flow with unexpected exception."""
    mock_config_entry_mid.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": mock_config_entry_mid.entry_id,
        },
    )

    # Mock validate_input to raise unexpected exception
    with patch(
        "homeassistant.components.wago_energymeter.config_flow.validate_input",
        side_effect=TypeError("Unexpected error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "10.42.0.59",
                CONF_PORT: 504,
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_options_flow_unsupported_device_type(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
) -> None:
    """Test options flow with unsupported device type."""
    # Create config entry with unsupported device type
    mock_config_entry_mid.add_to_hass(hass)

    # Temporarily change device type to unsupported value
    hass.config_entries.async_update_entry(
        mock_config_entry_mid,
        data={**mock_config_entry_mid.data, CONF_DEVICE_TYPE: "unsupported"},
    )

    result = await hass.config_entries.options.async_init(
        mock_config_entry_mid.entry_id
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_options_flow_remove_deselected_sensors(
    hass: HomeAssistant,
    mock_config_entry_2857: MockConfigEntry,
    mock_wago_meter_2857: MagicMock,
) -> None:
    """Test options flow removes entities for deselected sensors."""
    mock_config_entry_2857.add_to_hass(hass)

    # Set up with some sensors already selected
    hass.config_entries.async_update_entry(
        mock_config_entry_2857,
        options={CONF_ADDITIONAL_SENSORS: ["power_total", "reactive_power_total"]},
    )
    await hass.config_entries.async_setup(mock_config_entry_2857.entry_id)
    await hass.async_block_till_done()

    # Verify entities were created
    entity_registry = er.async_get(hass)
    power_entity_id = entity_registry.async_get_entity_id(
        "sensor",
        DOMAIN,
        f"{mock_config_entry_2857.entry_id}_power_total",
    )
    assert power_entity_id is not None

    # Start options flow
    result = await hass.config_entries.options.async_init(
        mock_config_entry_2857.entry_id
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Deselect all sensors (empty list)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ADDITIONAL_SENSORS: []},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Verify entities were removed
    power_entity_id_after = entity_registry.async_get_entity_id(
        "sensor",
        DOMAIN,
        f"{mock_config_entry_2857.entry_id}_power_total",
    )
    assert power_entity_id_after is None
