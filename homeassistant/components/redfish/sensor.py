"""Sensors for Redfish temperatures."""

from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RedfishConfigEntry, RedfishDataUpdateCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RedfishConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Redfish temperature sensors."""
    async_add_entities(
        RedfishTemperatureSensor(entry.runtime_data, temperature_key)
        for temperature_key in entry.runtime_data.data.temperatures
    )


class RedfishTemperatureSensor(
    CoordinatorEntity[RedfishDataUpdateCoordinator], SensorEntity
):
    """A Redfish chassis temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: RedfishDataUpdateCoordinator,
        temperature_key: tuple[str, str],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._temperature_key = temperature_key
        chassis_id, member_id = temperature_key
        temperature = coordinator.data.temperatures[temperature_key]
        chassis = coordinator.data.chassis[chassis_id]
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{chassis_id}_{member_id}"
        )
        self._attr_name = temperature.name
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.config_entry.entry_id}_chassis_{chassis_id}")
            },
            name=chassis.name or chassis.chassis_id,
            manufacturer=chassis.manufacturer,
            model=chassis.model,
            serial_number=chassis.serial_number,
        )

    @property
    @override
    def available(self) -> bool:
        """Return whether this reading is present in the latest update."""
        return (
            super().available
            and self._temperature_key in self.coordinator.data.temperatures
        )

    @property
    @override
    def native_value(self) -> float | None:
        """Return temperature in Celsius."""
        if temperature := self.coordinator.data.temperatures.get(self._temperature_key):
            return temperature.reading_celsius
        return None
