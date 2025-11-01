"""Test the WAGO Energy Meter additional sensor configuration."""

from unittest.mock import patch

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.wago_energymeter.const import (
    CONF_ADDITIONAL_SENSORS,
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_2857_570,
    DEVICE_TYPE_MID_METER,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry, snapshot_platform


@pytest.fixture
def platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return [Platform.SENSOR]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_mid_meter_with_additional_sensors(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_wago_meter_mid,
) -> None:
    """Test MID meter with all additional sensors enabled."""
    # Create config entry with all additional sensors enabled
    config_entry = MockConfigEntry(
        title="WAGO MID Meter with Additional Sensors",
        domain=DOMAIN,
        data={
            CONF_NAME: "Test MID with Additional Sensors",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 502,
            CONF_DEVICE_TYPE: DEVICE_TYPE_MID_METER,
        },
        options={
            CONF_ADDITIONAL_SENSORS: [
                "energy_consumed_l1",
                "energy_consumed_l2",
                "energy_consumed_l3",
                "energy_delivered_l1",
                "energy_delivered_l2",
                "energy_delivered_l3",
                "reactive_energy_consumed_l1",
                "reactive_energy_consumed_l2",
                "reactive_energy_consumed_l3",
                "reactive_energy_delivered_l1",
                "reactive_energy_delivered_l2",
                "reactive_energy_delivered_l3",
            ]
        },
        unique_id="wago_mid_test_additional_sensors",
        entry_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
    )

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_mid,
    ):
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_2857_with_additional_sensors(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_wago_meter_2857,
) -> None:
    """Test 2857-570 with power total sensors enabled."""
    # Create config entry with power total sensors enabled
    config_entry = MockConfigEntry(
        title="WAGO 2857 with Additional Sensors",
        domain=DOMAIN,
        data={
            CONF_NAME: "Test 2857 with Additional Sensors",
            CONF_HOST: "192.168.1.101",
            CONF_PORT: 502,
            CONF_DEVICE_TYPE: DEVICE_TYPE_2857_570,
        },
        options={
            CONF_ADDITIONAL_SENSORS: [
                "power_total",
                "reactive_power_total",
                "apparent_power_total",
                "power_factor_total",
            ]
        },
        unique_id="wago_2857_test_additional_sensors",
        entry_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
    )

    with patch(
        "homeassistant.components.wago_energymeter.WagoMeter",
        return_value=mock_wago_meter_2857,
    ):
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)
