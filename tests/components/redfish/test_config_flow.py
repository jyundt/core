"""Tests for the Redfish config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.components.redfish.const import CONF_BASE_URL, DOMAIN
from homeassistant.components.redfish.coordinator import (
    RedfishAuthError,
    RedfishData,
    RedfishError,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_config_flow_success(hass: HomeAssistant) -> None:
    """Test successful setup flow."""
    with patch(
        "homeassistant.components.redfish.config_flow.RedfishClient.async_discover",
        return_value=RedfishData([{"Id": "1", "Name": "Server"}], []),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_BASE_URL: "https://bmc.example",
                CONF_USERNAME: "user",
                CONF_PASSWORD: "password",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Server"


async def test_config_flow_errors(hass: HomeAssistant) -> None:
    """Test authentication, connection, and no-system errors."""
    data = {
        CONF_BASE_URL: "https://bmc.example",
        CONF_USERNAME: "user",
        CONF_PASSWORD: "password",
    }
    for result_data, error in (
        (RedfishAuthError(), "invalid_auth"),
        (RedfishError(), "cannot_connect"),
        (RedfishData([], []), "no_systems"),
    ):
        with patch(
            "homeassistant.components.redfish.config_flow.RedfishClient.async_discover",
            side_effect=result_data if isinstance(result_data, Exception) else None,
            return_value=result_data
            if not isinstance(result_data, Exception)
            else None,
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
            )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": error}


async def test_setup_and_unload(hass: HomeAssistant) -> None:
    """Test config-entry setup and platform unload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_BASE_URL: "https://bmc.example",
            CONF_USERNAME: "user",
            CONF_PASSWORD: "password",
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.redfish.coordinator.RedfishDataUpdateCoordinator.async_config_entry_first_refresh",
        new=AsyncMock(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
