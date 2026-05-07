"""Constants for the Lumagen integration."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.const import Platform

DOMAIN = "lumagen"

CONF_CONNECTION_TYPE = "connection_type"
CONF_SERIAL_DEVICE = "serial_device"
CONF_BAUDRATE = "baudrate"

CONF_MODEL = "model"
CONF_SW_VERSION = "sw_version"
CONF_SERIAL_NUMBER = "serial_number"

CONNECTION_TYPE_TCP = "tcp"
CONNECTION_TYPE_SERIAL = "serial"

DEFAULT_NAME = "Lumagen Radiance Pro"
DEFAULT_PORT = 4999
DEFAULT_BAUDRATE = 9600
DEFAULT_TIMEOUT = 5.0

PLATFORMS = [
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SENSOR,
    Platform.SWITCH,
]


class LumagenCommand(StrEnum):
    """Supported Lumagen remote commands."""

    MENU = "menu"
    EXIT = "exit"
    CLEAR = "clear"
    OK = "ok"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    POWER_ON = "power_on"
    STANDBY = "standby"


REMOTE_COMMANDS = {
    "alt": "alt",
    "auto_aspect_disable": "auto_aspect_disable",
    "auto_aspect_enable": "auto_aspect_enable",
    "clear": "clear",
    "down": "down",
    "exit": "exit",
    "help": "help",
    "left": "left",
    "mema": "mema",
    "memb": "memb",
    "memc": "memc",
    "memd": "memd",
    "menu": "menu",
    "nls": "toggle_nls",
    "ok": "ok",
    "right": "right",
    "show_aspect": "show_aspect",
    "source_aspect_16x9": "set_aspect_16_9",
    "source_aspect_1_85": "set_aspect_1_85",
    "source_aspect_1_90": "set_aspect_1_90",
    "source_aspect_2_00": "set_aspect_2_00",
    "source_aspect_2_20": "set_aspect_2_20",
    "source_aspect_2_35": "set_aspect_2_35",
    "source_aspect_2_40": "set_aspect_2_40",
    "source_aspect_4x3": "set_aspect_4_3",
    "source_aspect_lbox": "set_aspect_lbox",
    "up": "up",
}
