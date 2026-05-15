"""Switch platform for the Lumagen integration."""

# pylint: disable=duplicate-code

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LumagenConfigEntry
from .const import DOMAIN
from .coordinator import LumagenCoordinatorData, LumagenDataUpdateCoordinator
from .entity import LumagenEntity


@dataclass(frozen=True)
class LumagenSwitchDescription:  # pylint: disable=too-many-instance-attributes
    """Lumagen switch description."""

    key: str
    name: str
    icon: str
    is_on_fn: Callable[[LumagenCoordinatorData], bool | None]
    turn_on_fn: Callable[[LumagenSwitch], Awaitable[None]]
    turn_off_fn: Callable[[LumagenSwitch], Awaitable[None]]
    available_fn: Callable[[LumagenCoordinatorData], bool] | None = None
    entity_category: EntityCategory | None = None


def _status_value(
    data: LumagenCoordinatorData,
    key: str,
) -> str | int | float | bool | None:
    """Return a value from full status."""
    if data.status is None:
        return None

    return data.status.get(key)


def _status_available(data: LumagenCoordinatorData, key: str) -> bool:
    """Return true if a status value exists."""
    return data.available and _status_value(data, key) is not None


def _auto_aspect_is_on(data: LumagenCoordinatorData) -> bool | None:
    """Return true if auto aspect is enabled."""
    value = _status_value(data, "auto_aspect_status")

    if value is None:
        return None

    return value == "On"


async def _turn_auto_aspect_on(entity: LumagenSwitch) -> None:
    """Turn auto aspect on."""
    await entity.coordinator.async_set_auto_aspect(True)


async def _turn_auto_aspect_off(entity: LumagenSwitch) -> None:
    """Turn auto aspect off."""
    await entity.coordinator.async_set_auto_aspect(False)


def _nls_is_on(data: LumagenCoordinatorData) -> bool | None:
    """Return true if NLS is enabled."""
    value = _status_value(data, "nls_active")

    if value is None:
        return None

    return value == "On"


async def _turn_nls_on(entity: LumagenSwitch) -> None:
    """Turn NLS on."""
    await entity.coordinator.async_set_nls(True)


async def _turn_nls_off(entity: LumagenSwitch) -> None:
    """Turn NLS off."""
    await entity.coordinator.async_set_nls(False)


SWITCHES = [
    LumagenSwitchDescription(
        key="auto_aspect",
        name="Auto Aspect",
        icon="mdi:aspect-ratio",
        is_on_fn=_auto_aspect_is_on,
        turn_on_fn=_turn_auto_aspect_on,
        turn_off_fn=_turn_auto_aspect_off,
        available_fn=lambda data: _status_available(data, "auto_aspect_status"),
    ),
    LumagenSwitchDescription(
        key="nls",
        name="NLS",
        icon="mdi:stretch-to-page",
        is_on_fn=_nls_is_on,
        turn_on_fn=_turn_nls_on,
        turn_off_fn=_turn_nls_off,
        available_fn=lambda data: _status_available(data, "nls_active"),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LumagenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lumagen switch entities."""
    coordinator: LumagenDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [LumagenSwitch(coordinator, description) for description in SWITCHES]
    )


class LumagenSwitch(LumagenEntity, SwitchEntity):
    """Lumagen switch entity."""

    def __init__(
        self,
        coordinator: LumagenDataUpdateCoordinator,
        description: LumagenSwitchDescription,
    ) -> None:
        """Initialize the Lumagen switch."""
        super().__init__(coordinator, description.key)
        self._description = description
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category

    @property
    def available(self) -> bool:
        """Return if the switch is available."""
        data = self.coordinator.data

        if data is None:
            return False

        if self._description.available_fn is not None:
            return self._description.available_fn(data)

        return data.available

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        data = self.coordinator.data

        if data is None:
            return None

        return self._description.is_on_fn(data)

    def turn_on(self, **_kwargs) -> None:
        """Turn the switch on."""
        raise NotImplementedError

    def turn_off(self, **_kwargs) -> None:
        """Turn the switch off."""
        raise NotImplementedError

    async def async_turn_on(self, **_kwargs) -> None:
        """Turn the switch on."""
        await self._description.turn_on_fn(self)

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn the switch off."""
        await self._description.turn_off_fn(self)
