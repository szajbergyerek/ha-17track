"""Sensor platform for the 17TRACK integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import format_package_status
from .const import DOMAIN
from .coordinator import Track17Coordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """
    Set up 17TRACK package sensors from a config entry, adding new sensors as new packages appear.

    param hass: The Home Assistant instance.
    param entry: The config entry for this 17TRACK account.
    param async_add_entities: Callback used to register new entities with Home Assistant.

    :return: None
    """
    coordinator: Track17Coordinator = hass.data[DOMAIN][entry.entry_id]
    known_tracking_numbers: set[str] = set()

    def _add_new_package_sensors() -> None:
        """
        Create sensor entities for any tracking numbers not yet represented in Home Assistant.

        :return: None
        """
        new_entities = [
            PackageSensor(coordinator, tracking_number)
            for tracking_number in coordinator.data
            if tracking_number not in known_tracking_numbers
        ]
        if new_entities:
            known_tracking_numbers.update(entity.tracking_number for entity in new_entities)
            async_add_entities(new_entities)

    _add_new_package_sensors()
    coordinator.async_add_listener(_add_new_package_sensors)


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
        self._attr_unique_id = f"track17_{tracking_number}"

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

        :return: A dictionary with the tracking number, carrier, package status, and last event time.
        """
        package = self._package
        return {
            "tracking_number": self.tracking_number,
            "carrier": package.get("carrier"),
            "package_status": package.get("package_status"),
            "last_event_time": package.get("latest_event_time"),
        }
