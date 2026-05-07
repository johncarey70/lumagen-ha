"""The Lumagen integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS
from .coordinator import (
    LumagenCoordinatorData,
    LumagenDataUpdateCoordinator,
    create_lumagen_device,
)

type LumagenConfigEntry = ConfigEntry[LumagenDataUpdateCoordinator]

SET_INPUT_LABEL_SCHEMA = vol.Schema(
    {
        vol.Required("memory"): vol.In(["A", "B", "C", "D"]),
        vol.Required("input_number"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Required("label"): vol.All(cv.string, vol.Length(max=10)),
    }
)

SET_INPUT_LABELS_SCHEMA = vol.Schema(
    {
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
    }
)

DISPLAY_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("duration", default=5): vol.All(
            vol.Coerce(int),
            vol.Range(min=0, max=9),
        ),
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LumagenConfigEntry,
) -> bool:
    """Set up Lumagen from a config entry."""
    device = create_lumagen_device(entry)
    coordinator = LumagenDataUpdateCoordinator(hass, entry, device)

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

    entry.runtime_data = coordinator

    if not hass.services.has_service(DOMAIN, "set_input_label"):

        async def async_set_input_label_service(call) -> None:
            """Handle set input label service."""
            await entry.runtime_data.async_set_input_label(
                call.data["memory"],
                call.data["input_number"],
                call.data["label"],
            )

        hass.services.async_register(
            DOMAIN,
            "set_input_label",
            async_set_input_label_service,
            schema=SET_INPUT_LABEL_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, "set_input_labels"):

        async def async_set_input_labels_service(call) -> None:
            """Handle set input labels service."""
            await entry.runtime_data.async_set_input_labels(
                call.data["memory"],
                call.data["labels"],
            )

        hass.services.async_register(
            DOMAIN,
            "set_input_labels",
            async_set_input_labels_service,
            schema=SET_INPUT_LABELS_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, "display_message"):

        async def async_display_message_service(call) -> None:
            """Handle display message service."""
            await entry.runtime_data.async_display_message(
                call.data["message"],
                call.data["duration"],
            )

        hass.services.async_register(
            DOMAIN,
            "display_message",
            async_display_message_service,
            schema=DISPLAY_MESSAGE_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, "clear_message"):

        async def async_clear_message_service(_call) -> None:
            """Handle clear message service."""
            await entry.runtime_data.async_clear_message()

        hass.services.async_register(
            DOMAIN,
            "clear_message",
            async_clear_message_service,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: LumagenConfigEntry,
) -> bool:
    """Unload a Lumagen config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await entry.runtime_data.async_shutdown()

    return unload_ok
