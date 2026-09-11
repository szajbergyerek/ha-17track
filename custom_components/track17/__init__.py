"""The 17TRACK integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import Track17Api, Track17ApiError
from .const import (
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    SERVICE_DELETE_DELIVERED_PACKAGES,
    SERVICE_DELETE_PACKAGE,
    SERVICE_REGISTER_PACKAGE,
)
from .coordinator import Track17Coordinator

ATTR_TRACKING_NUMBER = "tracking_number"
ATTR_TAG = "tag"
ATTR_IDENTIFIER = "identifier"
SERVICE_REGISTER_PACKAGE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TRACKING_NUMBER): cv.string,
        vol.Optional(ATTR_TAG): cv.string,
    },
    extra=vol.REMOVE_EXTRA,
)
SERVICE_DELETE_PACKAGE_SCHEMA = vol.Schema({vol.Required(ATTR_IDENTIFIER): cv.string}, extra=vol.REMOVE_EXTRA)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up the 17TRACK integration from a config entry.

    param hass: The Home Assistant instance.
    param entry: The config entry containing the 17TRACK API key.

    :return: True if setup succeeded.
    """
    api = Track17Api(entry.data[CONF_API_KEY])
    coordinator = Track17Coordinator(hass, api, DEFAULT_SCAN_INTERVAL_MINUTES)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a 17TRACK config entry.

    param hass: The Home Assistant instance.
    param entry: The config entry to unload.

    :return: True if unloading succeeded.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_DELIVERED_PACKAGES)
            hass.services.async_remove(DOMAIN, SERVICE_REGISTER_PACKAGE)
            hass.services.async_remove(DOMAIN, SERVICE_DELETE_PACKAGE)
    return unload_ok


def _async_register_services(hass: HomeAssistant) -> None:
    """
    Register the delete_delivered_packages and register_package services, if not already registered.

    param hass: The Home Assistant instance.

    :return: None
    """
    if not hass.services.has_service(DOMAIN, SERVICE_DELETE_DELIVERED_PACKAGES):

        async def _handle_delete_delivered_packages(call: ServiceCall) -> None:
            """
            Delete every delivered package across all configured 17TRACK accounts.

            param call: The service call that triggered this handler.

            :return: None
            """
            try:
                for coordinator in hass.data[DOMAIN].values():
                    await coordinator.async_delete_delivered_packages()
            except Track17ApiError as error:
                raise HomeAssistantError(str(error)) from error

        hass.services.async_register(DOMAIN, SERVICE_DELETE_DELIVERED_PACKAGES, _handle_delete_delivered_packages)

    if not hass.services.has_service(DOMAIN, SERVICE_REGISTER_PACKAGE):

        async def _handle_register_package(call: ServiceCall) -> None:
            """
            Register a new tracking number across all configured 17TRACK accounts.

            param call: The service call containing the tracking number and optional tag to register.

            :return: None
            """
            tracking_number = call.data[ATTR_TRACKING_NUMBER]
            tag = call.data.get(ATTR_TAG)
            try:
                for coordinator in hass.data[DOMAIN].values():
                    await coordinator.async_register_package(tracking_number, tag)
            except Track17ApiError as error:
                raise HomeAssistantError(str(error)) from error

        hass.services.async_register(
            DOMAIN, SERVICE_REGISTER_PACKAGE, _handle_register_package, schema=SERVICE_REGISTER_PACKAGE_SCHEMA
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DELETE_PACKAGE):

        async def _handle_delete_package(call: ServiceCall) -> None:
            """
            Delete a single package, identified by its tag or tracking number, from whichever configured
            17TRACK account currently tracks it.

            param call: The service call containing the tag or tracking number identifying the package.

            :return: None
            """
            identifier = call.data[ATTR_IDENTIFIER]
            last_error: Track17ApiError | None = None
            for coordinator in hass.data[DOMAIN].values():
                try:
                    await coordinator.async_delete_package(identifier)
                except Track17ApiError as error:
                    last_error = error
                else:
                    last_error = None
                    break

            if last_error is not None:
                raise HomeAssistantError(str(last_error))

        hass.services.async_register(
            DOMAIN, SERVICE_DELETE_PACKAGE, _handle_delete_package, schema=SERVICE_DELETE_PACKAGE_SCHEMA
        )
