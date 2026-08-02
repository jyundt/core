"""Tests for Redfish reset buttons."""

from dataclasses import replace
from unittest.mock import AsyncMock

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.redfish.models import RedfishData
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry


async def test_advertised_reset_buttons_and_action(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_redfish_api: tuple[AsyncMock, AsyncMock],
    entity_registry: er.EntityRegistry,
) -> None:
    """Test only advertised non-primary reset buttons are created."""
    expected_unique_ids = {
        "uuid-1_force_off",
        "uuid-1_graceful_restart",
        "uuid-1_force_restart",
        "uuid-1_full_power_cycle",
    }
    actual_unique_ids = {
        entry.unique_id
        for entry in entity_registry.entities.values()
        if entry.platform == "redfish" and entry.domain == BUTTON_DOMAIN
    }
    assert actual_unique_ids == expected_unique_ids

    entity_id = entity_registry.async_get_entity_id(
        BUTTON_DOMAIN, "redfish", "uuid-1_force_off"
    )
    assert entity_id is not None
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    mock_redfish_api[1].assert_awaited_once_with(
        "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset", "ForceOff"
    )


async def test_reset_button_unavailable_when_no_longer_advertised(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test a reset button becomes unavailable if support is withdrawn."""
    entity_id = entity_registry.async_get_entity_id(
        BUTTON_DOMAIN, "redfish", "uuid-1_force_off"
    )
    assert entity_id is not None
    coordinator = init_integration.runtime_data
    system = coordinator.data.systems["1"]
    coordinator.async_set_updated_data(
        RedfishData(
            systems={
                **coordinator.data.systems,
                "1": replace(
                    system,
                    reset_types=system.reset_types - {"ForceOff"},
                ),
            }
        )
    )
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == "unavailable"
