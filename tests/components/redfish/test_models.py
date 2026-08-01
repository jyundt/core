"""Tests for Redfish data models."""

import math

import pytest

from homeassistant.components.redfish.models import (
    RedfishSystem,
    RedfishTemperature,
    parse_chassis,
    parse_system,
    parse_temperature,
)


@pytest.mark.parametrize("payload", [{}, {"Id": ""}, {"Id": 1}])
def test_skip_malformed_chassis(payload: dict[str, object]) -> None:
    """Test chassis without a stable standard identifier are skipped."""
    assert parse_chassis(payload) is None


def test_parse_system_metadata_and_actions() -> None:
    """Test parsing system metadata and only usable advertised reset types."""
    assert parse_system(
        {
            "@odata.id": "/redfish/v1/Systems/1",
            "Id": "1",
            "Name": "Server",
            "UUID": "uuid-1",
            "Manufacturer": "Acme",
            "Model": "Model 1",
            "SerialNumber": "serial",
            "PowerState": "On",
            "Actions": {
                "#ComputerSystem.Reset": {
                    "target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                    "ResetType@Redfish.AllowableValues": [
                        "On",
                        "ForceOff",
                        "FullPowerCycle",
                        "On",
                        "VendorReset",
                        1,
                    ],
                }
            },
        }
    ) == RedfishSystem(
        odata_id="/redfish/v1/Systems/1",
        system_id="1",
        name="Server",
        uuid="uuid-1",
        manufacturer="Acme",
        model="Model 1",
        serial_number="serial",
        power_state="On",
        reset_target="/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
        reset_types=frozenset({"On", "ForceOff", "FullPowerCycle"}),
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"Id": "1"},
        {"@odata.id": "/redfish/v1/Systems/1"},
        {"@odata.id": "", "Id": "1"},
        {"@odata.id": "/redfish/v1/Systems/1", "Id": ""},
    ],
)
def test_skip_malformed_systems(payload: dict[str, object]) -> None:
    """Test systems without stable standard identifiers are skipped."""
    assert parse_system(payload) is None


@pytest.mark.parametrize("reading", [True, math.nan, math.inf, "42", None])
def test_skip_malformed_temperature_readings(reading: object) -> None:
    """Test invalid temperature readings are skipped."""
    assert (
        parse_temperature(
            "chassis-1",
            {
                "MemberId": "CPU1",
                "Name": "CPU 1",
                "ReadingCelsius": reading,
            },
        )
        is None
    )


def test_parse_temperature() -> None:
    """Test usable standard temperature data is parsed."""
    assert parse_temperature(
        "chassis-1",
        {"MemberId": "CPU1", "Name": "CPU 1", "ReadingCelsius": 42},
    ) == RedfishTemperature(
        chassis_id="chassis-1",
        member_id="CPU1",
        name="CPU 1",
        reading_celsius=42.0,
    )


@pytest.mark.parametrize(
    ("member_id", "name"),
    [
        pytest.param("", "CPU 1", id="empty-member-id"),
        pytest.param(" ", "CPU 1", id="blank-member-id"),
        pytest.param("CPU1", "", id="empty-name"),
        pytest.param("CPU1", " ", id="blank-name"),
    ],
)
def test_skip_temperature_without_usable_identity(member_id: str, name: str) -> None:
    """Test readings without usable names and member IDs are skipped."""
    assert (
        parse_temperature(
            "chassis-1",
            {"MemberId": member_id, "Name": name, "ReadingCelsius": 42},
        )
        is None
    )
