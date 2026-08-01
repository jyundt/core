"""Sensors for Redfish temperatures."""

from typing import Any, override

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RedfishConfigEntry, RedfishDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RedfishConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Redfish temperature sensors."""
    async_add_entities(
        RedfishTemperatureSensor(entry.runtime_data, temperature)
        for temperature in entry.runtime_data.data.temperatures
    )


class RedfishTemperatureSensor(
    CoordinatorEntity[RedfishDataUpdateCoordinator], SensorEntity
):
    """A Redfish chassis temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self, coordinator: RedfishDataUpdateCoordinator, temperature: dict[str, Any]
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._chassis_id = temperature["chassis_id"]
        self._member_id = temperature["MemberId"]
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{self._chassis_id}_{self._member_id}"
        )
        self._attr_name = temperature["Name"]
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.config_entry.entry_id}_{self._chassis_id}")
            }
        )

    @property
    @override
    def native_value(self) -> float:
        """Return temperature in Celsius."""
        return next(
            item
            for item in self.coordinator.data.temperatures
            if item["chassis_id"] == self._chassis_id
            and item["MemberId"] == self._member_id
        )["ReadingCelsius"]
