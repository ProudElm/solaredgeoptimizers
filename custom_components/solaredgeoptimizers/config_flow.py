"""Config flow for SolarEdge Optimizers Data integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

from solaredgeoptimizers import solaredgeoptimizers

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("siteid"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class SolarEdgeWebAuth:
    """boe"""

    def __init__(self, siteid: str) -> None:
        """Initialize."""
        self.siteid = siteid

    async def authenticate(
        self, hass: HomeAssistant, username: str, password: str
    ) -> bool:
        """Test to check if siteid, username and password are correct."""
        api = solaredgeoptimizers(
            siteid=self.siteid, username=username, password=password
        )
        # http_result_code = api.check_login()
        http_result_code = await hass.async_add_executor_job(api.check_login)
        if http_result_code == 200:
            return True
        else:
            return False


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    hub = SolarEdgeWebAuth(data["siteid"])

    if not await hub.authenticate(hass, data["username"], data["password"]):
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "SolarEdge Site {}".format(data["siteid"])}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolarEdge Optimizers Data."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        # print("config_flow.py -> async_step_user")

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
