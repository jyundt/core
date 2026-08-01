"""Data coordinator for Redfish."""

from dataclasses import dataclass
import logging
from typing import Any, override

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_BASE_URL, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type RedfishConfigEntry = ConfigEntry[RedfishDataUpdateCoordinator]


class RedfishError(Exception):
    """Base error communicating with Redfish."""


class RedfishAuthError(RedfishError):
    """Authentication failed."""


@dataclass(slots=True)
class RedfishData:
    """Discovered Redfish data."""

    systems: list[dict[str, Any]]
    temperatures: list[dict[str, Any]]


class RedfishClient:
    """Minimal asynchronous Redfish client."""

    def __init__(
        self, hass: HomeAssistant, base_url: str, username: str, password: str
    ) -> None:
        """Initialize the client."""
        self._session = async_get_clientsession(hass)
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": aiohttp.encode_basic_auth(username, password)}

    async def _async_get(self, path: str) -> dict[str, Any]:
        """Get a Redfish resource."""
        try:
            async with self._session.get(
                f"{self._base_url}{path}", headers=self._headers
            ) as response:
                self._check_response(response)
                return await response.json()
        except RedfishAuthError:
            raise
        except (aiohttp.ClientError, ValueError) as err:
            raise RedfishError from err

    async def async_reset(self, target: str, reset_type: str) -> None:
        """Perform an advertised reset action."""
        try:
            async with self._session.post(
                f"{self._base_url}{target}",
                headers=self._headers,
                json={"ResetType": reset_type},
            ) as response:
                self._check_response(response)
        except RedfishAuthError:
            raise
        except aiohttp.ClientError as err:
            raise RedfishError from err

    async def async_discover(self) -> RedfishData:
        """Discover systems and standard chassis Thermal resources."""
        root = await self._async_get("/redfish/v1/")
        systems = await self._async_members(root.get("Systems"))
        temperatures: list[dict[str, Any]] = []
        for chassis in await self._async_members(root.get("Chassis")):
            thermal = chassis.get("Thermal")
            if not isinstance(thermal, dict) or not (
                thermal_path := thermal.get("@odata.id")
            ):
                continue
            thermal_data = await self._async_get(thermal_path)
            for temperature in thermal_data.get("Temperatures", []):
                if not isinstance(temperature, dict):
                    continue
                member_id = temperature.get("MemberId")
                name = temperature.get("Name")
                reading = temperature.get("ReadingCelsius")
                if (
                    not isinstance(member_id, str)
                    or not isinstance(name, str)
                    or not isinstance(reading, (int, float))
                ):
                    continue
                temperatures.append(
                    {"chassis_id": chassis.get("Id", "unknown"), **temperature}
                )
        return RedfishData(systems, temperatures)

    async def _async_members(self, link: Any) -> list[dict[str, Any]]:
        """Resolve a Redfish collection's member resources."""
        if not isinstance(link, dict) or not (path := link.get("@odata.id")):
            return []
        collection = await self._async_get(path)
        return [
            await self._async_get(member_path)
            for member in collection.get("Members", [])
            if isinstance(member, dict) and (member_path := member.get("@odata.id"))
        ]

    @staticmethod
    def _check_response(response: aiohttp.ClientResponse) -> None:
        """Validate a Redfish response."""
        if response.status in (401, 403):
            raise RedfishAuthError
        response.raise_for_status()


class RedfishDataUpdateCoordinator(DataUpdateCoordinator[RedfishData]):
    """Coordinate Redfish polling."""

    config_entry: RedfishConfigEntry

    def __init__(self, hass: HomeAssistant, entry: RedfishConfigEntry) -> None:
        """Initialize coordinator."""
        self.client = RedfishClient(
            hass,
            entry.data[CONF_BASE_URL],
            entry.data["username"],
            entry.data["password"],
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    @override
    async def _async_update_data(self) -> RedfishData:
        """Fetch Redfish data."""
        try:
            return await self.client.async_discover()
        except RedfishError as err:
            raise UpdateFailed from err
