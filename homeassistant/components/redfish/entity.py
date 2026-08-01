"""Shared entities for Redfish."""

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RedfishDataUpdateCoordinator


class RedfishEntity(CoordinatorEntity[RedfishDataUpdateCoordinator]):
    """Base Redfish entity."""

    def __init__(
        self, coordinator: RedfishDataUpdateCoordinator, system: dict[str, Any]
    ) -> None:
        """Initialize a system entity."""
        super().__init__(coordinator)
        self.system = system
        self.identity = (
            system.get("UUID") or f"{coordinator.config_entry.entry_id}_{system['Id']}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.identity)},
            name=system.get("Name"),
            manufacturer=system.get("Manufacturer"),
            model=system.get("Model"),
            serial_number=system.get("SerialNumber"),
        )

    def _system(self) -> dict[str, Any]:
        """Return current system data."""
        return next(
            item
            for item in self.coordinator.data.systems
            if item["Id"] == self.system["Id"]
        )
