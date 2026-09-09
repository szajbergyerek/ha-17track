"""Data update coordinator for the 17TRACK integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Track17Api, Track17ApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Track17Coordinator(DataUpdateCoordinator[dict]):
    """Coordinator that periodically polls 17TRACK for all registered packages."""

    def __init__(self, hass: HomeAssistant, api: Track17Api, update_interval_minutes: int) -> None:
        """
        Initialize the coordinator.

        param hass: The Home Assistant instance.
        param api: The 17TRACK API client used to fetch package data.
        param update_interval_minutes: How often to poll the 17TRACK API, in minutes.

        :return: None
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_minutes),
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        """
        Fetch the latest package list from 17TRACK and index it by tracking number.

        :return: A dictionary mapping tracking number to its raw package data.
        """
        try:
            packages = await self.hass.async_add_executor_job(self.api.get_all_packages)
        except Track17ApiError as error:
            raise UpdateFailed(f"Error communicating with 17TRACK API: {error}") from error
        except Exception as error:
            raise UpdateFailed(f"Error communicating with 17TRACK API: {error}") from error

        return {package["number"]: package for package in packages}

    async def async_delete_delivered_packages(self) -> int:
        """
        Delete every currently delivered package from 17TRACK and refresh the coordinator data.

        :return: The number of packages that were deleted.
        """
        delivered_packages = [
            package for package in self.data.values() if package["package_status"] == "Delivered"
        ]
        if delivered_packages:
            try:
                await self.hass.async_add_executor_job(self.api.delete_packages, delivered_packages)
            except Track17ApiError as error:
                raise UpdateFailed(f"Error communicating with 17TRACK API: {error}") from error

        await self.async_request_refresh()
        return len(delivered_packages)
