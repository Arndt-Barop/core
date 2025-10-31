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
