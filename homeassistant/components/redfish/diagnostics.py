"""Diagnostics support for Redfish."""

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_BASE_URL
from .coordinator import RedfishConfigEntry

TO_REDACT = {
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    "odata_id",
    "reset_target",
    "serial_number",
    "thermal_target",
    "uuid",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: RedfishConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a Redfish config entry."""
    systems = []
    for system in entry.runtime_data.data.systems.values():
        system_data = asdict(system)
        system_data["reset_types"] = sorted(system.reset_types)
        systems.append(system_data)

    return async_redact_data(
        {
            "config_entry": entry.data,
            "systems": systems,
            "chassis": [
                asdict(chassis) for chassis in entry.runtime_data.data.chassis.values()
            ],
            "temperatures": [
                asdict(temperature)
                for temperature in entry.runtime_data.data.temperatures.values()
            ],
        },
        TO_REDACT,
    )
