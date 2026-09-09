"""Config flow for the 17TRACK integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import Track17Api, Track17ApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


async def _validate_api_key(hass: HomeAssistant, api_key: str) -> None:
    """
    Validate the given API key by attempting to fetch the package list from 17TRACK.

    param hass: The Home Assistant instance.
    param api_key: The 17TRACK API key to validate.

    :return: None
    """
    api = Track17Api(api_key)
    try:
        await hass.async_add_executor_job(api.get_all_packages)
    except Track17ApiError as error:
        raise InvalidAuth from error
    except Exception as error:
        raise CannotConnect from error


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 17TRACK."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """
        Handle the step where the user enters their 17TRACK API key.

        param user_input: The form data submitted by the user, or None on first display.

        :return: The next flow step result.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_API_KEY])
            self._abort_if_unique_id_configured()

            try:
                await _validate_api_key(self.hass, user_input[CONF_API_KEY])
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title="17TRACK", data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the 17TRACK API."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate the given 17TRACK API key is invalid."""
