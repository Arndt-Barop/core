"""Test the WAGO Energy Meter diagnostics."""

from unittest.mock import MagicMock, patch

from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


async def test_diagnostics_mid_meter(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test diagnostics for MID meter."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry_mid
    )

    assert result == snapshot


async def test_diagnostics_2857_570(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_2857: MockConfigEntry,
    mock_wago_meter_2857: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test diagnostics for 2857-570."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_2857,
    ):
        mock_config_entry_2857.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_2857.entry_id)
        await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry_2857
    )

    assert result == snapshot


async def test_diagnostics_with_oserror(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test diagnostics when meter raises OSError."""
    # Make voltage reading raise OSError
    mock_wago_meter_mid.get_voltage_l1.side_effect = OSError("Connection failed")
    mock_wago_meter_mid.get_voltage_l2.side_effect = OSError("Connection failed")
    mock_wago_meter_mid.get_voltage_l3.side_effect = OSError("Connection failed")

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry_mid
    )

    # Should have unavailable for voltage readings
    assert result["current_readings"]["voltage_l1"] == "unavailable"
    assert result["current_readings"]["voltage_l2"] == "unavailable"
    assert result["current_readings"]["voltage_l3"] == "unavailable"
    # But other readings should still work
    assert result["current_readings"]["current_l1"] == 5.2
    assert result["current_readings"]["frequency"] == 50.0


async def test_diagnostics_with_attribute_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test diagnostics when meter raises AttributeError."""
    # Make current reading raise AttributeError
    mock_wago_meter_mid.get_current_l1.side_effect = AttributeError(
        "Method not available"
    )
    mock_wago_meter_mid.get_current_l2.side_effect = AttributeError(
        "Method not available"
    )
    mock_wago_meter_mid.get_current_l3.side_effect = AttributeError(
        "Method not available"
    )

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry_mid
    )

    # Should have unavailable for current readings
    assert result["current_readings"]["current_l1"] == "unavailable"
    assert result["current_readings"]["current_l2"] == "unavailable"
    assert result["current_readings"]["current_l3"] == "unavailable"
    # But other readings should still work
    assert result["current_readings"]["voltage_l1"] == 230.0


async def test_diagnostics_frequency_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test diagnostics when frequency reading fails."""
    # Make frequency reading raise OSError
    mock_wago_meter_mid.get_frequency.side_effect = OSError("Frequency read failed")

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    result = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry_mid
    )

    # Frequency should be unavailable
    assert result["current_readings"]["frequency"] == "unavailable"
    # But other readings should still work
    assert result["current_readings"]["voltage_l1"] == 230.0
