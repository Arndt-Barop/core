"""Test the WAGO Energy Meter integration init."""

from unittest.mock import MagicMock, patch

from homeassistant.components.wago_energymeter.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test setting up config entry."""
    mock_config_entry_mid.add_to_hass(hass)

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry_mid.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.config.components


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test unloading config entry."""
    mock_config_entry_mid.add_to_hass(hass)

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        assert await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mock_config_entry_mid.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry_mid.state is ConfigEntryState.NOT_LOADED
    mock_wago_meter_mid.stop.assert_called_once()
