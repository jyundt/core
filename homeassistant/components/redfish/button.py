"""Buttons for non-primary Redfish reset actions."""

from typing import Any, override

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import RedfishConfigEntry
from .entity import RedfishEntity

PRIMARY_RESET_TYPES = {"On", "GracefulShutdown"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RedfishConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up reset buttons for advertised non-primary actions."""
    entities = [
        RedfishResetButton(entry.runtime_data, system, reset_type)
        for system in entry.runtime_data.data.systems
        for reset_type in system.get("Actions", {})
        .get("#ComputerSystem.Reset", {})
        .get("ResetType@Redfish.AllowableValues", [])
        if reset_type not in PRIMARY_RESET_TYPES
    ]
    async_add_entities(entities)


class RedfishResetButton(RedfishEntity, ButtonEntity):
    """An advertised non-primary Redfish reset action."""

    def __init__(
        self, coordinator: Any, system: dict[str, Any], reset_type: str
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, system)
        self._reset_type = reset_type
        self._attr_name = reset_type
        self._attr_unique_id = (
            f"{system.get('UUID') or system['Id']}_{reset_type.lower()}"
        )

    @override
    async def async_press(self) -> None:
        """Invoke this advertised reset action."""
        system = self._system()
        action = system.get("Actions", {}).get("#ComputerSystem.Reset", {})
        target = action.get("target")
        values = action.get("ResetType@Redfish.AllowableValues", [])
        if not target or self._reset_type not in values:
            raise HomeAssistantError(
                f"Redfish reset type {self._reset_type} is not supported"
            )
        await self.coordinator.client.async_reset(target, self._reset_type)
        await self.coordinator.async_request_refresh()
