"""Tests for Lumagen setup retry and reconnect behavior."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from lumagen_control.models import LumagenId, LumagenInput, LumagenPowerStatus
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lumagen.const import (
    CONF_CONNECTION_TYPE,
    CONF_MODEL,
    CONF_SERIAL_NUMBER,
    CONF_SW_VERSION,
    CONNECTION_TYPE_TCP,
    DOMAIN,
)
from custom_components.lumagen.coordinator import LumagenDataUpdateCoordinator

type EventCallback = Callable[[str], Awaitable[None]] | None


class FakeLumagenDevice:
    """In-memory Lumagen device used by reconnect tests."""

    def __init__(self, *, reachable: bool = True, power_on: bool = False) -> None:
        """Initialize the fake device."""
        self.reachable = reachable
        self.power_on = power_on
        self._connected = False
        self.connect_calls = 0
        self.disconnect_calls = 0
        self._event_callback: EventCallback = None

    @property
    def is_connected(self) -> bool:
        """Return whether the fake transport is connected."""
        return self._connected

    async def connect(self) -> None:
        """Connect, or raise if the device should be unreachable."""
        self.connect_calls += 1
        if not self.reachable:
            raise OSError("Connection refused")
        self._connected = True

    async def disconnect(self) -> None:
        """Disconnect the fake transport."""
        self.disconnect_calls += 1
        self._connected = False

    def set_event_callback(self, callback: EventCallback) -> None:
        """Store the coordinator event callback."""
        self._event_callback = callback

    def drop_connection(self) -> None:
        """Simulate a mid-session transport drop."""
        self._connected = False

    async def query_power(self) -> LumagenPowerStatus:
        """Return a standby or on power status."""
        flag = "1" if self.power_on else "0"
        status = LumagenPowerStatus.from_response(f"!S02,{flag}")
        assert status is not None
        return status

    async def query_input(self) -> LumagenInput:
        """Return a selected input."""
        return LumagenInput(input_number=1, memory="A", physical_input=1)

    async def query_full_status(self) -> None:
        """Return no full status so startup stays simple."""
        return None

    async def query_id(self) -> LumagenId:
        """Return a stable identity payload."""
        return LumagenId(
            model="Radiance Pro",
            software="030326",
            model_number="5244",
            serial_number="TESTSERIAL",
        )

    async def query_output_info(self) -> None:
        """Return no output info."""
        return None

    async def query_input_labels(self, memory: str) -> dict[int, str]:
        """Return an empty label map."""
        return {}


def _mock_entry() -> MockConfigEntry:
    """Return a Lumagen config entry for tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Lumagen Radiance Pro",
        unique_id="TESTSERIAL",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP,
            CONF_HOST: "192.0.2.10",
            CONF_PORT: 4999,
            CONF_MODEL: "Radiance Pro 5244",
            CONF_SERIAL_NUMBER: "TESTSERIAL",
            CONF_SW_VERSION: "030326",
        },
    )


async def _wait_until(
    predicate: Callable[[], bool],
    *,
    timeout: float = 2.0,
) -> None:
    """Wait until a condition is true."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("Condition was not met in time")


async def _setup_with_device(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    device: FakeLumagenDevice,
) -> bool:
    """Set up the config entry with a patched Lumagen device."""
    entry.add_to_hass(hass)
    with patch(
        "custom_components.lumagen.create_lumagen_device",
        return_value=device,
    ):
        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return result


def _coordinator(
    hass: HomeAssistant, entry: MockConfigEntry
) -> LumagenDataUpdateCoordinator:
    """Return the loaded Lumagen coordinator."""
    return hass.data[DOMAIN][entry.entry_id]


async def test_setup_retries_when_unreachable(hass: HomeAssistant) -> None:
    """Setup leaves the entry in retry when the Lumagen cannot be reached."""
    entry = _mock_entry()
    device = FakeLumagenDevice(reachable=False)

    assert await _setup_with_device(hass, entry, device) is False
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert DOMAIN not in hass.data


async def test_setup_succeeds_when_lumagen_is_in_standby(
    hass: HomeAssistant,
) -> None:
    """A reachable Lumagen in standby still sets up."""
    entry = _mock_entry()
    device = FakeLumagenDevice(reachable=True, power_on=False)

    assert await _setup_with_device(hass, entry, device) is True
    assert entry.state is ConfigEntryState.LOADED

    coordinator = _coordinator(hass, entry)
    assert coordinator.data is not None
    assert coordinator.data.available is True
    assert coordinator.data.power_on is False


async def test_dropped_connection_retries_and_recovers(
    hass: HomeAssistant,
) -> None:
    """A live drop is marked unavailable, retried, and recovered."""
    entry = _mock_entry()
    device = FakeLumagenDevice(reachable=True, power_on=True)

    assert await _setup_with_device(hass, entry, device) is True
    coordinator = _coordinator(hass, entry)
    assert coordinator.data is not None
    assert coordinator.data.available is True
    assert coordinator.data.power_on is True

    device.reachable = False
    device.drop_connection()

    await _wait_until(
        lambda: coordinator.data is not None and not coordinator.data.available
    )
    assert coordinator.data.power_on is True
    delay_after_drop = coordinator._reconnect_delay

    device.reachable = True
    await _wait_until(
        lambda: coordinator.data is not None and coordinator.data.available
    )
    assert coordinator.data.power_on is True
    assert coordinator._connected is True
    assert device.is_connected is True
    assert coordinator._reconnect_delay == 0.05
    assert delay_after_drop >= 0.05


async def test_reconnect_delay_backs_off_while_unreachable(
    hass: HomeAssistant,
) -> None:
    """Reconnect delay increases while the Lumagen stays unreachable."""
    entry = _mock_entry()
    device = FakeLumagenDevice(reachable=True, power_on=False)

    assert await _setup_with_device(hass, entry, device) is True
    coordinator = _coordinator(hass, entry)

    device.reachable = False
    device.drop_connection()

    await _wait_until(lambda: coordinator._reconnect_delay > 0.05)
    assert coordinator.data is not None
    assert coordinator.data.available is False
    assert coordinator._reconnect_delay <= 0.2
