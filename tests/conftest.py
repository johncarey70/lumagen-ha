"""Fixtures for the Lumagen integration tests."""

from collections.abc import Generator
from unittest.mock import patch

import pytest

from custom_components.lumagen import coordinator as coordinator_module


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load custom_components in every test."""


@pytest.fixture(autouse=True)
def short_reconnect_delays() -> Generator[None]:
    """Keep connection-watch and reconnect delays short for tests."""
    with (
        patch.object(coordinator_module, "RECONNECT_INITIAL_DELAY_SECONDS", 0.05),
        patch.object(coordinator_module, "RECONNECT_MAX_DELAY_SECONDS", 0.2),
        patch.object(coordinator_module, "CONNECTION_WATCH_INTERVAL_SECONDS", 0.05),
    ):
        yield
