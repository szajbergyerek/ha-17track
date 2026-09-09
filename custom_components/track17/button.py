"""Button platform for the 17TRACK integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import Track17Coordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """
    Set up the delete-delivered-packages button from a config entry.

    param hass: The Home Assistant instance.
    param entry: The config entry for this 17TRACK account.
    param async_add_entities: Callback used to register new entities with Home Assistant.

    :return: None
    """
    coordinator: Track17Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DeleteDeliveredPackagesButton(coordinator, entry.entry_id)])


class DeleteDeliveredPackagesButton(CoordinatorEntity[Track17Coordinator], ButtonEntity):
    """Button that deletes every delivered package from 17TRACK when pressed."""

    _attr_has_entity_name = True
    _attr_name = "Delete delivered packages"
    _attr_icon = "mdi:package-variant-closed-remove"

    def __init__(self, coordinator: Track17Coordinator, entry_id: str) -> None:
        """
        Initialize the button.

        param coordinator: The coordinator managing this 17TRACK account's packages.
        param entry_id: The config entry id this button belongs to, used to build a unique id.

        :return: None
        """
        super().__init__(coordinator)
        self._attr_unique_id = f"track17_{entry_id}_delete_delivered_packages"

    async def async_press(self) -> None:
        """
        Delete every currently delivered package from 17TRACK.

        :return: None
        """
        await self.coordinator.async_delete_delivered_packages()
