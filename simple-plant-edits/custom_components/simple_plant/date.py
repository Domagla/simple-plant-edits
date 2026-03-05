"""Date platform for simple_plant."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from homeassistant.components.date import (
    DateEntity,
    DateEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import as_local, as_utc, utcnow

from .const import DOMAIN
from .coordinator import SimplePlantCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


ENTITY_DESCRIPTIONS = (
    DateEntityDescription(
        key="last_watered",
        translation_key="last_watered",
        icon="mdi:calendar-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the date platform."""
    async_add_entities(
        SimplePlantDate(hass, entry, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SimplePlantDate(CoordinatorEntity[SimplePlantCoordinator], DateEntity):
    """simple_plant date class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: DateEntityDescription,
    ) -> None:
        """Initialize the date class."""
        coordinator: SimplePlantCoordinator = hass.data[DOMAIN][entry.entry_id]
        super().__init__(coordinator)
        self.entity_description = description

        device = self.coordinator.device

        fallback_raw = entry.data.get("last_watered")
        self._fallback_value = (
            self._parse_date_value(str(fallback_raw))
            if fallback_raw
            else as_local(utcnow()).date()
        )

        self.entity_id = f"date.{DOMAIN}_{description.key}_{device}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{device}"

        # Set up device info
        self._attr_device_info = self.coordinator.device_info

    @property
    def device(self) -> str | None:
        """Return the device name."""
        return self.coordinator.device

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        if not self.native_value:
            await self.async_set_value(self._fallback_value)

    async def async_set_value(self, value: date) -> None:
        """Change the date."""
        local_midnight = datetime.combine(
            value,
            datetime.min.time(),
            tzinfo=ZoneInfo(self.hass.config.time_zone),
        )
        new_val = as_utc(local_midnight)
        await self.coordinator.async_set_last_watered(new_val)

    @property
    def native_value(self) -> date | None:
        """Return the date value."""
        if not self.coordinator.data:
            return None

        date_str = self.coordinator.data.get("last_watered")
        if not date_str:
            return None

        return self._parse_date_value(date_str)

    @staticmethod
    def _parse_date_value(value: str) -> date:
        """Parse a stored date/datetime into a local date."""
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.date()
        return as_local(parsed).date()
