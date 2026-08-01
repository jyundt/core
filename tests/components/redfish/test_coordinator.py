"""Tests for the Redfish coordinator."""

from collections.abc import Callable
from typing import Any

from aiohttp import web
from aiohttp.test_utils import TestServer
import pytest

from homeassistant.components.redfish.coordinator import RedfishClient
from homeassistant.core import HomeAssistant


@pytest.fixture
def redfish_app() -> web.Application:
    """Return a representative Redfish service."""
    app = web.Application()
    app["requests"] = []

    async def response(request: web.Request) -> web.Response:
        app["requests"].append(
            (request.path, await request.json() if request.method == "POST" else None)
        )
        if request.method == "POST":
            return web.Response(status=204)
        resources: dict[str, dict[str, Any]] = {
            "/redfish/v1/": {
                "Systems": {"@odata.id": "/redfish/v1/Systems"},
                "Chassis": {"@odata.id": "/redfish/v1/Chassis"},
            },
            "/redfish/v1/Systems": {
                "Members": [{"@odata.id": "/redfish/v1/Systems/1"}]
            },
            "/redfish/v1/Systems/1": {
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
                            "GracefulShutdown",
                            "ForceOff",
                            "GracefulRestart",
                        ],
                    }
                },
            },
            "/redfish/v1/Chassis": {
                "Members": [{"@odata.id": "/redfish/v1/Chassis/1"}]
            },
            "/redfish/v1/Chassis/1": {
                "Id": "1",
                "Thermal": {"@odata.id": "/redfish/v1/Chassis/1/Thermal"},
            },
            "/redfish/v1/Chassis/1/Thermal": {
                "Temperatures": [
                    {"MemberId": "CPU1", "Name": "CPU 1", "ReadingCelsius": 42.5},
                    {"MemberId": "bad", "Name": "Bad"},
                    {"MemberId": "empty", "ReadingCelsius": 10},
                ]
            },
        }
        if request.path not in resources:
            return web.Response(status=404)
        return web.json_response(resources[request.path])

    app.router.add_route("*", "/{path:.*}", response)
    return app


@pytest.fixture
def aiohttp_server(
    aiohttp_server: Callable[[], TestServer], socket_enabled: None
) -> Callable[[], TestServer]:
    """Return aiohttp_server and allow opening sockets."""
    return aiohttp_server


async def test_discover_systems_and_temperatures(
    hass: HomeAssistant,
    aiohttp_server: Callable[[], TestServer],
    redfish_app: web.Application,
) -> None:
    """Test standard service-root discovery and malformed temperature filtering."""
    server = await aiohttp_server(redfish_app)
    client = RedfishClient(hass, str(server.make_url("")), "user", "password")

    data = await client.async_discover()

    assert data.systems == [
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
                        "GracefulShutdown",
                        "ForceOff",
                        "GracefulRestart",
                    ],
                }
            },
        }
    ]
    assert data.temperatures == [
        {"chassis_id": "1", "MemberId": "CPU1", "Name": "CPU 1", "ReadingCelsius": 42.5}
    ]


async def test_post_reset_uses_advertised_target_and_type(
    hass: HomeAssistant,
    aiohttp_server: Callable[[], TestServer],
    redfish_app: web.Application,
) -> None:
    """Test reset commands use the advertised action URL and payload."""
    server = await aiohttp_server(redfish_app)
    client = RedfishClient(hass, str(server.make_url("")), "user", "password")

    await client.async_reset(
        "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset", "ForceOff"
    )

    assert redfish_app["requests"] == [
        (
            "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
            {"ResetType": "ForceOff"},
        )
    ]
