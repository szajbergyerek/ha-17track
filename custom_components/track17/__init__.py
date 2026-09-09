"""The 17TRACK integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant

from .api import Track17Api
from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN
from .coordinator import Track17Coordinator

PLATFORMS = [Platform.SENSOR]


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
    return unload_ok
