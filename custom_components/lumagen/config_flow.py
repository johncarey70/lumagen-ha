"""Config flow for the Lumagen integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from lumagen_control import (
    LumagenDevice,
    LumagenProtocol,
    SerialTransport,
    TcpTransport,
)

from .const import (CONF_BAUDRATE, CONF_CONNECTION_TYPE, CONF_MODEL,
                    CONF_SERIAL_DEVICE, CONF_SERIAL_NUMBER, CONF_SW_VERSION,
                    CONNECTION_TYPE_SERIAL, CONNECTION_TYPE_TCP,
                    DEFAULT_BAUDRATE, DEFAULT_NAME, DEFAULT_PORT, DEFAULT_TIMEOUT, DOMAIN)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Unable to connect to the Lumagen."""


class InvalidConnectionType(HomeAssistantError):
    """Invalid connection type selected."""


async def validate_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    connection_type = user_input[CONF_CONNECTION_TYPE]

    if connection_type == CONNECTION_TYPE_TCP:
        transport = TcpTransport(
            host=user_input[CONF_HOST],
            port=user_input[CONF_PORT],
            timeout=DEFAULT_TIMEOUT,
        )
    elif connection_type == CONNECTION_TYPE_SERIAL:
        transport = SerialTransport(
            device=user_input[CONF_SERIAL_DEVICE],
            baudrate=user_input[CONF_BAUDRATE],
            timeout=DEFAULT_TIMEOUT,
        )
    else:
        raise InvalidConnectionType

    device = LumagenDevice(LumagenProtocol(transport))

    try:
        await device.connect()
        alive = await device.query_alive()
        identity = await device.query_id()
    except (TimeoutError, OSError, ValueError) as err:
        raise CannotConnect from err
    finally:
        await device.disconnect()

    if not alive:
        raise CannotConnect

    return {
        "title": f"{identity.model} {identity.serial_number}",
        CONF_MODEL: identity.model,
        CONF_SW_VERSION: identity.software,
        CONF_SERIAL_NUMBER: identity.serial_number,
    }


class LumagenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lumagen."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Lumagen config flow."""
        self._connection_type: str | None = None

    def is_matching(self, other_flow: config_entries.ConfigFlow) -> bool:
        """Return whether this flow matches another flow."""
        return False

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._connection_type = user_input[CONF_CONNECTION_TYPE]

            if self._connection_type == CONNECTION_TYPE_TCP:
                return await self.async_step_tcp()

            if self._connection_type == CONNECTION_TYPE_SERIAL:
                return await self.async_step_serial()

            errors["base"] = "invalid_connection_type"

        connection_options = {
            CONNECTION_TYPE_TCP: (
                "Network serial connection "
                "(serial-over-TCP adapter)"
            ),
            CONNECTION_TYPE_SERIAL: "Local Serial Port (/dev/tty*)",
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONNECTION_TYPE,
                        default=CONNECTION_TYPE_TCP,
                    ): vol.In(connection_options),
                }
            ),
            errors=errors,
        )

    async def async_step_tcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle TCP setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            full_input = {
                CONF_NAME: user_input[CONF_NAME],
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
            }

            try:
                info = await validate_input(full_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during Lumagen TCP setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info[CONF_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()

                full_input[CONF_MODEL] = info[CONF_MODEL]
                full_input[CONF_SW_VERSION] = info[CONF_SW_VERSION]
                full_input[CONF_SERIAL_NUMBER] = info[CONF_SERIAL_NUMBER]

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=full_input,
                )

        return self.async_show_form(
            step_id="tcp",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_serial(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle serial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            full_input = {
                CONF_NAME: user_input[CONF_NAME],
                CONF_CONNECTION_TYPE: CONNECTION_TYPE_SERIAL,
                CONF_SERIAL_DEVICE: user_input[CONF_SERIAL_DEVICE],
                CONF_BAUDRATE: user_input[CONF_BAUDRATE],
            }

            try:
                info = await validate_input(full_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during Lumagen serial setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info[CONF_SERIAL_NUMBER])
                self._abort_if_unique_id_configured()

                full_input[CONF_MODEL] = info[CONF_MODEL]
                full_input[CONF_SW_VERSION] = info[CONF_SW_VERSION]
                full_input[CONF_SERIAL_NUMBER] = info[CONF_SERIAL_NUMBER]

                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=full_input,
                )

        return self.async_show_form(
            step_id="serial",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_SERIAL_DEVICE, default="/dev/ttyS0"): str,
                    vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
                }
            ),
            errors=errors,
        )
