"""Tests for Redfish diagnostics."""

import json

from homeassistant.components.redfish.diagnostics import (
    async_get_config_entry_diagnostics,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


async def test_diagnostics_redact_sensitive_data(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test diagnostics contain useful data without sensitive data."""
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)
    serialized = json.dumps(diagnostics)

    assert diagnostics["config_entry"]["base_url"] == "**REDACTED**"
    assert diagnostics["config_entry"]["username"] == "**REDACTED**"
    assert diagnostics["config_entry"]["password"] == "**REDACTED**"
    assert diagnostics["systems"][0]["name"] == "Server"
    assert diagnostics["systems"][0]["uuid"] == "**REDACTED**"
    assert diagnostics["systems"][0]["serial_number"] == "**REDACTED**"
    assert diagnostics["systems"][0]["odata_id"] == "**REDACTED**"
    assert diagnostics["systems"][0]["reset_target"] == "**REDACTED**"
    assert diagnostics["chassis"][0]["serial_number"] == "**REDACTED**"
    assert diagnostics["chassis"][0]["thermal_target"] == "**REDACTED**"
    assert '"username": "user"' not in serialized
    assert '"password": "password"' not in serialized
    assert "https://bmc.example" not in serialized
    assert "uuid-1" not in serialized
    assert '"serial"' not in serialized
    assert "chassis-serial" not in serialized
