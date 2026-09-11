"""Sensor platform for the 17TRACK integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import format_package_status, get_package_description
from .const import DOMAIN
from .coordinator import Track17Coordinator

CONVERSATION_ASSISTANT = "conversation"

_LOGGER = logging.getLogger(__name__)


def _unique_id_for(tracking_number: str) -> str:
    """
    Build the unique id used for a package sensor entity.

    param tracking_number: The tracking number the sensor represents.

    :return: The unique id for this tracking number's sensor entity.
    """
    return f"track17_{tracking_number}"


def _tracking_number_from_unique_id(unique_id: str) -> str:
    """
    Recover the tracking number from a package sensor's unique id.

    param unique_id: The unique id of a package sensor entity, as built by _unique_id_for.

    :return: The tracking number encoded in the unique id.
    """
    return unique_id.removeprefix("track17_")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """
    Set up 17TRACK package sensors from a config entry, keeping entities in sync with coordinator data.

    param hass: The Home Assistant instance.
    param entry: The config entry for this 17TRACK account.
    param async_add_entities: Callback used to register new entities with Home Assistant.

    :return: None
    """
    coordinator: Track17Coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_registry = er.async_get(hass)
    known_tracking_numbers: set[str] = set()

    # Entity registry entries survive a restart, but the entities themselves don't - every package
    # in coordinator.data still needs a fresh PackageSensor instance below, regardless of whether it
    # already has a registry entry from before. This loop only clears out registry entries for
    # packages that are no longer tracked at all.
    for registry_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if registry_entry.domain != SENSOR_DOMAIN:
            continue

        tracking_number = _tracking_number_from_unique_id(registry_entry.unique_id)
        if tracking_number not in coordinator.data:
            entity_registry.async_remove(registry_entry.entity_id)

    def _sync_package_sensors() -> None:
        """
        Add sensor entities for newly tracked packages and remove them for packages no longer tracked.

        :return: None
        """
        current_tracking_numbers = set(coordinator.data)

        new_tracking_numbers = current_tracking_numbers - known_tracking_numbers
        if new_tracking_numbers:
            async_add_entities([PackageSensor(coordinator, tracking_number) for tracking_number in new_tracking_numbers])
            hass.async_create_task(_expose_new_packages(new_tracking_numbers))

        removed_tracking_numbers = known_tracking_numbers - current_tracking_numbers
        for tracking_number in removed_tracking_numbers:
            entity_id = entity_registry.async_get_entity_id(
                SENSOR_DOMAIN, DOMAIN, _unique_id_for(tracking_number)
            )
            if entity_id is not None:
                entity_registry.async_remove(entity_id)

        known_tracking_numbers.clear()
        known_tracking_numbers.update(current_tracking_numbers)

    async def _expose_new_packages(tracking_numbers: set[str]) -> None:
        """
        Expose newly added package sensors to conversation agents (e.g. voice assistants) by default,
        so a freshly registered package doesn't need to be exposed manually before it can be asked about.

        param tracking_numbers: The tracking numbers whose sensors were just added.

        :return: None
        """
        for tracking_number in tracking_numbers:
            entity_id = None
            for _ in range(50):
                entity_id = entity_registry.async_get_entity_id(
                    SENSOR_DOMAIN, DOMAIN, _unique_id_for(tracking_number)
                )
                if entity_id is not None:
                    break
                await asyncio.sleep(0.2)

            if entity_id is None:
                _LOGGER.warning(
                    "Could not find entity id for tracking number %s, not exposing it to conversation",
                    tracking_number,
                )
                continue

            try:
                async_expose_entity(hass, CONVERSATION_ASSISTANT, entity_id, True)
            except Exception:
                _LOGGER.exception("Failed to expose %s to conversation", entity_id)

    _sync_package_sensors()
    coordinator.async_add_listener(_sync_package_sensors)


class PackageSensor(CoordinatorEntity[Track17Coordinator], SensorEntity):
    """Representation of a single package tracked via 17TRACK."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, coordinator: Track17Coordinator, tracking_number: str) -> None:
        """
        Initialize the sensor for one tracked package.

        param coordinator: The coordinator providing package data for all tracking numbers.
        param tracking_number: The tracking number this sensor represents.

        :return: None
        """
        super().__init__(coordinator)
        self.tracking_number = tracking_number
        self._attr_unique_id = _unique_id_for(tracking_number)

    @property
    def _package(self) -> dict:
        """
        Look up the raw package data for this sensor's tracking number.

        :return: The package dictionary from the coordinator, or an empty dict if no longer present.
        """
        return self.coordinator.data.get(self.tracking_number, {})

    @property
    def available(self) -> bool:
        """
        Report whether this package is still present in the latest 17TRACK data.

        :return: True if the tracking number is still returned by 17TRACK, False otherwise.
        """
        return self.tracking_number in self.coordinator.data

    @property
    def name(self) -> str:
        """
        Return the display name of this sensor, using the package's tag if one was set on 17TRACK.

        :return: The package tag, or the tracking number if no tag was set.
        """
        return self._package.get("tag") or self.tracking_number

    @property
    def native_value(self) -> str | None:
        """
        Return the current package status as the sensor's state.

        :return: A sentence describing the latest event and when it happened, or None if unavailable.
        """
        package = self._package
        return format_package_status(package) if package else None

    @property
    def extra_state_attributes(self) -> dict:
        """
        Return additional package details as sensor attributes for use on dashboards.

        :return: A dictionary with the tracking number, carrier, package status, description, and last event time.
        """
        package = self._package
        return {
            "tracking_number": self.tracking_number,
            "carrier": package.get("carrier"),
            "package_status": package.get("package_status"),
            "description": get_package_description(package) if package else None,
            "last_event_time": package.get("latest_event_time"),
        }
