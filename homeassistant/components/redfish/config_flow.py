"""Config flow for Redfish."""

from typing import Any, override

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import CONF_BASE_URL, DOMAIN
from .coordinator import RedfishAuthError, RedfishClient, RedfishError


class RedfishConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Redfish config flow."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            client = RedfishClient(
                self.hass,
                user_input[CONF_BASE_URL],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                data = await client.async_discover()
            except RedfishAuthError:
                errors["base"] = "invalid_auth"
            except RedfishError:
                errors["base"] = "cannot_connect"
            else:
                if not data.systems:
                    errors["base"] = "no_systems"
                else:
                    await self.async_set_unique_id(
                        user_input[CONF_BASE_URL].rstrip("/")
                    )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=data.systems[0].get("Name", user_input[CONF_BASE_URL]),
                        data=user_input,
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BASE_URL): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
