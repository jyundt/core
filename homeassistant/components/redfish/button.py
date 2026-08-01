"""Buttons for non-primary Redfish reset actions."""

from dataclasses import dataclass
from typing import override

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import RedfishConfigEntry, RedfishDataUpdateCoordinator
from .entity import RedfishSystemEntity

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class RedfishResetButtonEntityDescription(ButtonEntityDescription):
    """Describe a Redfish reset button."""

    reset_type: str


RESET_BUTTONS = (
    RedfishResetButtonEntityDescription(
        key="force_off", translation_key="force_off", reset_type="ForceOff"
    ),
    RedfishResetButtonEntityDescription(
        key="graceful_restart",
        translation_key="graceful_restart",
        reset_type="GracefulRestart",
    ),
    RedfishResetButtonEntityDescription(
        key="force_restart",
        translation_key="force_restart",
        reset_type="ForceRestart",
    ),
    RedfishResetButtonEntityDescription(
        key="full_power_cycle",
        translation_key="full_power_cycle",
        reset_type="FullPowerCycle",
    ),
    RedfishResetButtonEntityDescription(
        key="nmi", translation_key="nmi", reset_type="Nmi"
    ),
    RedfishResetButtonEntityDescription(
        key="force_on", translation_key="force_on", reset_type="ForceOn"
    ),
    RedfishResetButtonEntityDescription(
        key="push_power_button",
        translation_key="push_power_button",
        reset_type="PushPowerButton",
    ),
    RedfishResetButtonEntityDescription(
        key="power_cycle", translation_key="power_cycle", reset_type="PowerCycle"
    ),
    RedfishResetButtonEntityDescription(
        key="suspend", translation_key="suspend", reset_type="Suspend"
    ),
    RedfishResetButtonEntityDescription(
        key="pause", translation_key="pause", reset_type="Pause"
    ),
    RedfishResetButtonEntityDescription(
        key="resume", translation_key="resume", reset_type="Resume"
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RedfishConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up buttons for advertised non-primary reset actions."""
    coordinator = entry.runtime_data
    async_add_entities(
        RedfishResetButton(coordinator, system_id, description)
        for system_id, system in coordinator.data.systems.items()
        for description in RESET_BUTTONS
        if description.reset_type in system.reset_types
    )


class RedfishResetButton(RedfishSystemEntity, ButtonEntity):
    """An advertised non-primary Redfish reset action."""

    entity_description: RedfishResetButtonEntityDescription

    def __init__(
        self,
        coordinator: RedfishDataUpdateCoordinator,
        system_id: str,
        description: RedfishResetButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, system_id)
        self.entity_description = description
        self._attr_unique_id = f"{self._system_identity}_{description.key}"

    @property
    @override
    def available(self) -> bool:
        """Return whether this reset type is currently advertised."""
        return (
            super().available
            and self.system is not None
            and self.system.reset_target is not None
            and self.entity_description.reset_type in self.system.reset_types
        )

    @override
    async def async_press(self) -> None:
        """Invoke this advertised reset action."""
        await self._async_reset(self.entity_description.reset_type)
