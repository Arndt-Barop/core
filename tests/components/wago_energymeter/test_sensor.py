"""Test the WAGO Energy Meter sensor platform."""

from unittest.mock import MagicMock, patch

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry, snapshot_platform


@pytest.fixture
def platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return [Platform.SENSOR]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_mid_meter_sensors(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry_mid: MockConfigEntry,
    mock_wago_meter_mid: MagicMock,
) -> None:
    """Test MID meter sensor entities."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        mock_config_entry_mid.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_mid.entry_id)
        await hass.async_block_till_done()

    await snapshot_platform(
        hass, entity_registry, snapshot, mock_config_entry_mid.entry_id
    )

    # Verify device is created
    device_entry = device_registry.async_get_device(
        identifiers={("wago_energymeter", mock_config_entry_mid.entry_id)}
    )
    assert device_entry
    assert device_entry.name == "Test MID Meter"
    assert device_entry.manufacturer == "WAGO"
    assert device_entry.model == "MID Meter (879-3000 series)"

    # Verify entities are linked to device
    entity_entries = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry_mid.entry_id
    )
    for entity_entry in entity_entries:
        assert entity_entry.device_id == device_entry.id


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_2857_570_sensors(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry_2857: MockConfigEntry,
    mock_wago_meter_2857: MagicMock,
) -> None:
    """Test 2857-570 sensor entities."""
    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_2857,
    ):
        mock_config_entry_2857.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry_2857.entry_id)
        await hass.async_block_till_done()

    await snapshot_platform(
        hass, entity_registry, snapshot, mock_config_entry_2857.entry_id
    )

    # Verify device is created
    device_entry = device_registry.async_get_device(
        identifiers={("wago_energymeter", mock_config_entry_2857.entry_id)}
    )
    assert device_entry
    assert device_entry.name == "Test 2857-570"
    assert device_entry.manufacturer == "WAGO"
    assert device_entry.model == "3-Phase Power Measurement (2857-570/024-001)"
