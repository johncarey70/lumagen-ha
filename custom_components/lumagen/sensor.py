"""Sensor platform for the Lumagen integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LumagenConfigEntry
from .coordinator import LumagenCoordinatorData
from .entity import LumagenEntity


@dataclass(frozen=True)
class LumagenSensorDescription:
    """Lumagen sensor description."""

    key: str
    name: str
    icon: str
    value_fn: Callable[[LumagenCoordinatorData], str | int | float | bool | None]
    unit: str | None = None
    entity_category: EntityCategory | None = None


def _source_name(data: LumagenCoordinatorData) -> str | None:
    """Return current source name."""
    input_number = data.input_number

    if input_number is None:
        return None

    labels = data.input_labels or {}
    label = labels.get(input_number)

    if label:
        return label

    return f"Input {input_number}"


def _status_value(
    data: LumagenCoordinatorData,
    key: str,
) -> str | int | float | bool | None:
    """Return a value from full status."""
    if data.status is None:
        return None

    return data.status.get(key)


def _format_combined_resolution(
    horizontal: str | int | float | bool | None,
    vertical: str | int | float | bool | None,
    mode: str | int | float | bool | None,
) -> str | None:
    """Return combined resolution like 4096x2160p."""
    if horizontal in (None, "") or vertical in (None, ""):
        return None

    mode_text = ""
    if isinstance(mode, str):
        if mode == "Progressive":
            mode_text = "p"
        elif mode == "Interlaced":
            mode_text = "i"
        elif mode in {"p", "P", "i", "I"}:
            mode_text = mode.lower()

    return f"{horizontal}x{vertical}{mode_text}"


def _input_combined_format(data: LumagenCoordinatorData) -> str | None:
    """Return combined input format."""
    return _format_combined_resolution(
        _status_value(data, "source_horizontal_resolution"),
        _status_value(data, "source_vertical_resolution"),
        _status_value(data, "source_mode"),
    )


def _output_combined_format(data: LumagenCoordinatorData) -> str | None:
    """Return combined output format."""
    return _format_combined_resolution(
        _status_value(data, "output_horizontal_resolution"),
        _status_value(data, "output_vertical_resolution"),
        _status_value(data, "output_mode"),
    )


SENSORS = [
    # Main sensors
    LumagenSensorDescription(
        key="current_input",
        name="Current Input",
        icon="mdi:video-input-hdmi",
        value_fn=lambda data: data.input_number,
    ),
    LumagenSensorDescription(
        key="current_source",
        name="Current Source",
        icon="mdi:video-switch",
        value_fn=_source_name,
    ),
    LumagenSensorDescription(
        key="input_status",
        name="Input Status",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "input_status"),
    ),
    LumagenSensorDescription(
        key="input_format",
        name="Input Format",
        icon="mdi:video-input-hdmi",
        value_fn=_input_combined_format,
    ),
    LumagenSensorDescription(
        key="current_source_content_aspect",
        name="Input Aspect",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "current_source_content_aspect"),
    ),
    LumagenSensorDescription(
        key="input_rate",
        name="Input Rate",
        icon="mdi:speedometer",
        value_fn=lambda data: _status_value(data, "source_vertical_rate"),
        unit="Hz",
    ),
    LumagenSensorDescription(
        key="source_dynamic_range",
        name="Input Dynamic Range",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "source_dynamic_range"),
    ),
    LumagenSensorDescription(
        key="source_mem",
        name="Input Memory",
        icon="mdi:eye",
        value_fn=lambda data: data.input_memory,
    ),
    LumagenSensorDescription(
        key="output_format",
        name="Output Format",
        icon="mdi:video-input-hdmi",
        value_fn=_output_combined_format,
    ),
    LumagenSensorDescription(
        key="output_rate",
        name="Output Rate",
        icon="mdi:speedometer",
        value_fn=lambda data: _status_value(data, "output_vertical_rate"),
        unit="Hz",
    ),
    LumagenSensorDescription(
        key="output_aspect",
        name="Output Aspect",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "output_aspect"),
    ),
    LumagenSensorDescription(
        key="output_on",
        name="Output On",
        icon="mdi:hdmi-port",
        value_fn=lambda data: _status_value(data, "output_on"),
    ),

    # Input diagnostics
    LumagenSensorDescription(
        key="input_mode",
        name="Input Mode",
        icon="mdi:video-input-hdmi",
        value_fn=lambda data: _status_value(data, "source_mode"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="source_horiz_resolution",
        name="Input Horizontal Resolution",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "source_horizontal_resolution"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="source_vertical_resolution",
        name="Input Vertical Resolution",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "source_vertical_resolution"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="source_raster_aspect",
        name="Input Raster Aspect",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "source_raster_aspect"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="source_3d_mode",
        name="Input 3D Mode",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "source_3d_mode"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="input_config_number",
        name="Input Config Number",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "input_config_number"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="virtual_input_selected",
        name="Input Virtual Selected",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "virtual_input_selected"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="physical_input_selected",
        name="Physical Input Selected",
        icon="mdi:hdmi-port",
        value_fn=lambda data: _status_value(data, "physical_input_selected"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # Output diagnostics
    LumagenSensorDescription(
        key="output_mode",
        name="Output Mode",
        icon="mdi:video-input-hdmi",
        value_fn=lambda data: _status_value(data, "output_mode"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="output_horizontal_resolution",
        name="Output Horizontal Resolution",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "output_horizontal_resolution"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="output_vertical_resolution",
        name="Output Vertical Resolution",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "output_vertical_resolution"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="output_color_space",
        name="Output Color Space",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "output_color_space"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="output_mode_3d",
        name="Output Mode 3D",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "output_mode_3d"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="active_output_cms",
        name="Active Output CMS",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "active_output_cms"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="active_output_style",
        name="Active Output Style",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "active_output_style"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    # Aspect / processing diagnostics
    LumagenSensorDescription(
        key="detected_source_aspect",
        name="Detected Source Aspect",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "detected_source_aspect"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="detected_source_raster_aspect",
        name="Detected Source Raster Aspect",
        icon="mdi:aspect-ratio",
        value_fn=lambda data: _status_value(data, "detected_source_raster_aspect"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    LumagenSensorDescription(
        key="nls_active",
        name="NLS Active",
        icon="mdi:eye",
        value_fn=lambda data: _status_value(data, "nls_active"),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: LumagenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lumagen sensor entities."""
    async_add_entities(
        [
            LumagenStatusSensor(entry.runtime_data, description)
            for description in SENSORS
        ]
    )


class LumagenStatusSensor(LumagenEntity, SensorEntity):
    """Lumagen status sensor."""

    def __init__(
        self,
        coordinator,
        description: LumagenSensorDescription,
    ) -> None:
        """Initialize the Lumagen status sensor."""
        super().__init__(coordinator, description.key)
        self._description = description
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_native_unit_of_measurement = description.unit
        self._attr_entity_category = description.entity_category

    @property
    def native_value(self) -> str | int | float | bool | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None

        return self._description.value_fn(self.coordinator.data)
