"""Data models for the Redfish integration."""

from dataclasses import dataclass
import math
from typing import Any

STANDARD_RESET_TYPES = frozenset(
    {
        "ForceOff",
        "ForceOn",
        "ForceRestart",
        "FullPowerCycle",
        "GracefulRestart",
        "GracefulShutdown",
        "Nmi",
        "On",
        "Pause",
        "PowerCycle",
        "PushPowerButton",
        "Resume",
        "Suspend",
    }
)


@dataclass(frozen=True, slots=True)
class RedfishSystem:
    """A Redfish ComputerSystem resource."""

    odata_id: str
    system_id: str
    name: str | None
    uuid: str | None
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    power_state: str | None
    reset_target: str | None
    reset_types: frozenset[str]


@dataclass(frozen=True, slots=True)
class RedfishChassis:
    """A Redfish Chassis resource."""

    chassis_id: str
    name: str | None
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    thermal_target: str | None


@dataclass(frozen=True, slots=True)
class RedfishTemperature:
    """A Redfish Temperature resource."""

    chassis_id: str
    member_id: str
    name: str
    reading_celsius: float


@dataclass(frozen=True, slots=True)
class RedfishData:
    """Data discovered from a Redfish service."""

    systems: dict[str, RedfishSystem]
    chassis: dict[str, RedfishChassis]
    temperatures: dict[tuple[str, str], RedfishTemperature]


def _non_empty_str(value: Any) -> str | None:
    """Return a non-empty string or None."""
    return value if isinstance(value, str) and value.strip() else None


def parse_system(payload: dict[str, Any]) -> RedfishSystem | None:
    """Parse a ComputerSystem resource, skipping unusable resources."""
    odata_id = _non_empty_str(payload.get("@odata.id"))
    system_id = _non_empty_str(payload.get("Id"))
    if odata_id is None or system_id is None:
        return None

    reset_target: str | None = None
    reset_types = frozenset[str]()
    actions = payload.get("Actions")
    if isinstance(actions, dict):
        reset = actions.get("#ComputerSystem.Reset")
        if isinstance(reset, dict) and (
            reset_target := _non_empty_str(reset.get("target"))
        ):
            allowable_values = reset.get("ResetType@Redfish.AllowableValues")
            if isinstance(allowable_values, list):
                reset_types = frozenset(
                    value
                    for value in allowable_values
                    if isinstance(value, str) and value in STANDARD_RESET_TYPES
                )

    return RedfishSystem(
        odata_id=odata_id,
        system_id=system_id,
        name=_non_empty_str(payload.get("Name")),
        uuid=_non_empty_str(payload.get("UUID")),
        manufacturer=_non_empty_str(payload.get("Manufacturer")),
        model=_non_empty_str(payload.get("Model")),
        serial_number=_non_empty_str(payload.get("SerialNumber")),
        power_state=_non_empty_str(payload.get("PowerState")),
        reset_target=reset_target,
        reset_types=reset_types,
    )


def parse_chassis(payload: dict[str, Any]) -> RedfishChassis | None:
    """Parse a Chassis resource, skipping unusable resources."""
    chassis_id = _non_empty_str(payload.get("Id"))
    if chassis_id is None:
        return None
    thermal = payload.get("Thermal")
    thermal_target = (
        _non_empty_str(thermal.get("@odata.id")) if isinstance(thermal, dict) else None
    )
    return RedfishChassis(
        chassis_id=chassis_id,
        name=_non_empty_str(payload.get("Name")),
        manufacturer=_non_empty_str(payload.get("Manufacturer")),
        model=_non_empty_str(payload.get("Model")),
        serial_number=_non_empty_str(payload.get("SerialNumber")),
        thermal_target=thermal_target,
    )


def parse_temperature(
    chassis_id: str, payload: dict[str, Any]
) -> RedfishTemperature | None:
    """Parse a Temperature resource, skipping unusable readings."""
    member_id = _non_empty_str(payload.get("MemberId"))
    name = _non_empty_str(payload.get("Name"))
    reading = payload.get("ReadingCelsius")
    if (
        member_id is None
        or name is None
        or isinstance(reading, bool)
        or not isinstance(reading, (int, float))
        or not math.isfinite(reading)
    ):
        return None
    return RedfishTemperature(
        chassis_id=chassis_id,
        member_id=member_id,
        name=name,
        reading_celsius=float(reading),
    )
