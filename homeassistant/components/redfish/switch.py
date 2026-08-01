"""Switches for Redfish systems."""

from typing import Any, override

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import RedfishConfigEntry
from .entity import RedfishEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RedfishConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Redfish switches."""
    async_add_entities(
        RedfishSystemSwitch(entry.runtime_data, system)
        for system in entry.runtime_data.data.systems
    )


class RedfishSystemSwitch(RedfishEntity, SwitchEntity):
    """A Redfish ComputerSystem power switch."""

    def __init__(self, coordinator: Any, system: dict[str, Any]) -> None:
        """Initialize switch."""
        super().__init__(coordinator, system)
        self._attr_unique_id = f"{self.identity}_power"

    @property
    @override
    def name(self) -> str:
        """Return name."""
        return self._system().get("Name", self.system["Id"])

    @property
    @override
    def is_on(self) -> bool:
        """Return true only for the Redfish On state."""
        return self._system().get("PowerState") == "On"

    async def _async_reset(self, reset_type: str) -> None:
        system = self._system()
        action = system.get("Actions", {}).get("#ComputerSystem.Reset", {})
        target = action.get("target")
        values = action.get("ResetType@Redfish.AllowableValues", [])
        if not target or reset_type not in values:
            raise HomeAssistantError(
                f"Redfish reset type {reset_type} is not supported"
            )
        await self.coordinator.client.async_reset(target, reset_type)
        await self.coordinator.async_request_refresh()

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on using only the advertised On action."""
        await self._async_reset("On")

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off using only the advertised GracefulShutdown action."""
        await self._async_reset("GracefulShutdown")
