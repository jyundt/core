"""Tests for Redfish temperature sensors."""

from homeassistant.components.redfish.models import RedfishData, RedfishTemperature
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry


async def test_temperature_sensor_and_device_metadata(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test temperature state, unique ID, and chassis device metadata."""
    entity_id = entity_registry.async_get_entity_id(
        SENSOR_DOMAIN, "redfish", "redfish-entry_1_CPU1"
    )
    assert entity_id is not None
    assert (state := hass.states.get(entity_id))
    assert state.state == "42.5"
    assert state.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS

    entity = entity_registry.async_get(entity_id)
    assert entity is not None
    assert entity.device_id is not None
    device = device_registry.async_get(entity.device_id)
    assert device is not None
    assert device.name == "Main chassis"
    assert device.manufacturer == "Acme"
    assert device.model == "Rack 1"
    assert device.serial_number == "chassis-serial"


async def test_temperature_is_unavailable_when_missing_from_update(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test a missing temperature reading becomes unavailable."""
    entity_id = entity_registry.async_get_entity_id(
        SENSOR_DOMAIN, "redfish", "redfish-entry_1_CPU1"
    )
    assert entity_id is not None
    coordinator = init_integration.runtime_data

    coordinator.async_set_updated_data(
        RedfishData(
            systems=coordinator.data.systems,
            chassis=coordinator.data.chassis,
            temperatures={},
        )
    )
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == "unavailable"


async def test_temperature_sensor_is_added_when_reading_becomes_usable(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test a newly usable temperature reading creates a sensor."""
    coordinator = init_integration.runtime_data
    coordinator.async_set_updated_data(
        RedfishData(
            systems=coordinator.data.systems,
            chassis=coordinator.data.chassis,
            temperatures={
                **coordinator.data.temperatures,
                ("1", "CPU2"): RedfishTemperature(
                    chassis_id="1",
                    member_id="CPU2",
                    name="CPU 2",
                    reading_celsius=43.5,
                ),
            },
        )
    )
    await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id(
        SENSOR_DOMAIN, "redfish", "redfish-entry_1_CPU2"
    )
    assert entity_id is not None
    assert (state := hass.states.get(entity_id))
    assert state.state == "43.5"
