"""Media player platform for the Lumagen integration."""

from __future__ import annotations

from homeassistant.components.media_player import (MediaPlayerEntity,
                                                   MediaPlayerEntityFeature,
                                                   MediaPlayerState)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LumagenConfigEntry
from .entity import LumagenEntity

SOURCE_MAP = {f"Input {input_number}": input_number for input_number in range(1, 19)}


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: LumagenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lumagen media player entity."""
    async_add_entities([LumagenMediaPlayer(entry.runtime_data)])


class LumagenMediaPlayer(
    LumagenEntity,
    MediaPlayerEntity,
):  # pylint: disable=abstract-method
    """Lumagen media player entity."""

    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = list(SOURCE_MAP)

    def __init__(self, coordinator) -> None:
        """Initialize the Lumagen media player."""
        super().__init__(coordinator, "media_player")

    @property
    def state(self) -> MediaPlayerState:
        """Return the media player state."""
        data = self.coordinator.data

        if data is not None and data.power_on:
            return MediaPlayerState.ON

        return MediaPlayerState.OFF

    @property
    def source_list(self) -> list[str]:
        """Return available input sources."""
        data = self.coordinator.data
        labels = data.input_labels if data and data.input_labels else {}

        return [
            self._source_name(input_number, labels.get(input_number))
            for input_number in range(1, 11)
        ]

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        data = self.coordinator.data

        if data is None or data.input_number is None:
            return None

        labels = data.input_labels or {}
        return self._source_name(data.input_number, labels.get(data.input_number))

    async def async_select_source(self, source: str) -> None:
        """Select a Lumagen input source."""
        input_number = self._input_number_from_source(source)
        await self.coordinator.async_select_input(input_number)

    @staticmethod
    def _source_name(input_number: int, label: str | None) -> str:
        """Return display name for an input."""
        if label:
            return label

        return f"Input {input_number}"

    def _input_number_from_source(self, source: str) -> int:
        """Return input number for a source name."""
        labels = self.coordinator.data.input_labels or {}

        for input_number in range(1, 19):
            if source == self._source_name(input_number, labels.get(input_number)):
                return input_number

        raise ValueError(f"Unknown Lumagen source: {source}")

    async def async_turn_on(self) -> None:
        """Turn the Lumagen on."""
        await self.coordinator.async_power_on()

    async def async_turn_off(self) -> None:
        """Put the Lumagen in standby."""
        await self.coordinator.async_standby()
