"""Base entity for the Lumagen integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, CONF_SERIAL_NUMBER, CONF_SW_VERSION, DOMAIN
from .coordinator import LumagenCoordinatorData, LumagenDataUpdateCoordinator


class LumagenEntity(CoordinatorEntity[LumagenDataUpdateCoordinator]):
    """Base Lumagen entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LumagenDataUpdateCoordinator,
        entity_suffix: str,
    ) -> None:
        """Initialize the Lumagen entity."""
        super().__init__(coordinator)

        entry_data = coordinator.config_entry.data
        serial_number = entry_data[CONF_SERIAL_NUMBER]

        self._attr_unique_id = f"{serial_number}_{entity_suffix}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None and self.coordinator.data.available

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        entry_data = self.coordinator.config_entry.data
        serial_number = entry_data[CONF_SERIAL_NUMBER]

        return DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            name=self.coordinator.config_entry.title,
            manufacturer="Lumagen",
            model=entry_data[CONF_MODEL],
            sw_version=(
                self.coordinator.data.sw_version
                if self.coordinator.data is not None
                else entry_data.get(CONF_SW_VERSION)
            ),
            suggested_area="Theater",
            serial_number=serial_number,
        )

    def _set_power_state(self, power_on: bool) -> None:
        """Optimistically update Lumagen power state."""
        data = self.coordinator.data

        self.coordinator.async_set_updated_data(
            LumagenCoordinatorData(
                power_on=power_on,
                available=True,
                input_number=data.input_number if data else None,
                input_memory=data.input_memory if data else None,
                input_labels=data.input_labels if data else None,
                status=data.status if data else None,
                sw_version=data.sw_version if data else None,
            )
        )
