"""The Lumagen integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, PLATFORMS
from .coordinator import (
    LumagenCoordinatorData,
    LumagenDataUpdateCoordinator,
    LumagenOsdMessage,
    create_lumagen_device,
)

type LumagenConfigEntry = ConfigEntry[LumagenDataUpdateCoordinator]

SERVICE_CLEAR_MESSAGE = "clear_message"
SERVICE_DISPLAY_MESSAGE = "display_message"
SERVICE_SET_INPUT_LABEL = "set_input_label"
SERVICE_SET_INPUT_LABELS = "set_input_labels"

SERVICES: tuple[str, ...] = (
    SERVICE_CLEAR_MESSAGE,
    SERVICE_DISPLAY_MESSAGE,
    SERVICE_SET_INPUT_LABEL,
    SERVICE_SET_INPUT_LABELS,
)

ENTITY_SCHEMA = {
    vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
}

SET_INPUT_LABEL_SCHEMA = vol.Schema(
    {
        **ENTITY_SCHEMA,
        vol.Required("memory"): vol.In(["A", "B", "C", "D"]),
        vol.Required("input_number"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("label"): vol.All(cv.string, vol.Length(max=10)),
    },
    extra=vol.PREVENT_EXTRA,
)

SET_INPUT_LABELS_SCHEMA = vol.Schema(
    {
        **ENTITY_SCHEMA,
        vol.Required("memory"): vol.In(["A", "B", "C", "D"]),
        vol.Required("labels"): vol.All(
            [
                {
                    vol.Required("input_number"): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=8),
                    ),
                    vol.Required("label"): vol.All(
                        cv.string,
                        vol.Length(max=10),
                    ),
                }
            ],
            vol.Length(min=1),
        ),
    },
    extra=vol.PREVENT_EXTRA,
)

DISPLAY_MESSAGE_SCHEMA = vol.Schema(
    {
        **ENTITY_SCHEMA,
        vol.Optional("message"): cv.string,
        vol.Optional("line1"): cv.string,
        vol.Optional("line2"): cv.string,
        vol.Optional("duration", default=5): vol.All(
            vol.Coerce(int),
            vol.Range(min=0, max=9),
        ),
        vol.Optional("message_placement", default="auto"): vol.In(
            ["auto", "line1", "line2"]
        ),
        vol.Optional("center"): vol.In(["line1", "line2", "both"]),
        vol.Optional("block_char"): vol.All(
            cv.string,
            vol.Length(min=1, max=1),
        ),
    },
    extra=vol.PREVENT_EXTRA,
)

CLEAR_MESSAGE_SCHEMA = vol.Schema(
    {
        **ENTITY_SCHEMA,
    },
    extra=vol.PREVENT_EXTRA,
)


def _get_coordinator(
    hass: HomeAssistant,
    entity_id: str | None,
) -> LumagenDataUpdateCoordinator:
    """Return the selected or only active Lumagen coordinator."""
    coordinators: dict[str, LumagenDataUpdateCoordinator] = hass.data.get(DOMAIN, {})

    if entity_id is not None:
        registry = er.async_get(hass)
        entity_entry = registry.async_get(entity_id)

        if entity_entry is None:
            raise HomeAssistantError(f"Unknown Lumagen entity: {entity_id}")

        config_entry_id = entity_entry.config_entry_id

        if config_entry_id is None or config_entry_id not in coordinators:
            raise HomeAssistantError(
                f"Entity is not a loaded Lumagen device: {entity_id}"
            )

        return coordinators[config_entry_id]

    if len(coordinators) == 1:
        return next(iter(coordinators.values()))

    if not coordinators:
        raise HomeAssistantError("No Lumagen config entries are loaded")

    raise HomeAssistantError(
        "entity_id is required when multiple Lumagen devices are loaded"
    )


def _register_services(hass: HomeAssistant) -> None:
    """Register Lumagen services once."""

    if not hass.services.has_service(DOMAIN, SERVICE_SET_INPUT_LABEL):

        async def async_set_input_label_service(call) -> None:
            """Handle set input label service."""
            coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTITY_ID))

            await coordinator.async_set_input_label(
                call.data["memory"],
                call.data["input_number"],
                call.data["label"],
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_INPUT_LABEL,
            async_set_input_label_service,
            schema=SET_INPUT_LABEL_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SET_INPUT_LABELS):

        async def async_set_input_labels_service(call) -> None:
            """Handle set input labels service."""
            coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTITY_ID))

            await coordinator.async_set_input_labels(
                call.data["memory"],
                call.data["labels"],
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_INPUT_LABELS,
            async_set_input_labels_service,
            schema=SET_INPUT_LABELS_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DISPLAY_MESSAGE):

        async def async_display_message_service(call) -> None:
            """Handle display message service."""
            if not any(
                call.data.get(key) is not None for key in ("message", "line1", "line2")
            ):
                raise HomeAssistantError("message, line1, or line2 is required")

            coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTITY_ID))

            center = call.data.get("center")

            await coordinator.async_display_message(
                LumagenOsdMessage(
                    message=call.data.get("message"),
                    duration=call.data["duration"],
                    message_placement=call.data["message_placement"],
                    block_char=call.data.get("block_char"),
                    line1=call.data.get("line1"),
                    line2=call.data.get("line2"),
                    center_line1=center in {"line1", "both"},
                    center_line2=center in {"line2", "both"},
                )
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_DISPLAY_MESSAGE,
            async_display_message_service,
            schema=DISPLAY_MESSAGE_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_MESSAGE):

        async def async_clear_message_service(call) -> None:
            """Handle clear message service."""
            coordinator = _get_coordinator(hass, call.data.get(ATTR_ENTITY_ID))

            await coordinator.async_clear_message()

        hass.services.async_register(
            DOMAIN,
            SERVICE_CLEAR_MESSAGE,
            async_clear_message_service,
            schema=CLEAR_MESSAGE_SCHEMA,
        )


def _remove_services(hass: HomeAssistant) -> None:
    """Remove Lumagen services."""
    for service in SERVICES:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LumagenConfigEntry,
) -> bool:
    """Set up Lumagen from a config entry."""
    device = create_lumagen_device(entry)
    coordinator = LumagenDataUpdateCoordinator(hass, entry, device)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        coordinator.async_set_updated_data(
            LumagenCoordinatorData(
                power_on=False,
                input_number=None,
                input_memory=None,
                input_labels=None,
                status=None,
            )
        )

        await coordinator.async_config_entry_first_refresh()

        _register_services(hass)

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

        await coordinator.async_shutdown()
        raise

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: LumagenConfigEntry,
) -> bool:
    """Unload a Lumagen config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            _remove_services(hass)

    return unload_ok
