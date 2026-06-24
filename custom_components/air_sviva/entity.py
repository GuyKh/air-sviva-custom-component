"""Air Sviva Entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import AirSvivaUpdateCoordinator


class AirSvivaEntity(CoordinatorEntity[AirSvivaUpdateCoordinator]):
    """Base entity for Air Sviva sensors."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AirSvivaUpdateCoordinator,
        entry_id: str,
        station_id: int,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"Air Sviva Station {station_id}",
            manufacturer="Israeli Ministry of Environmental Protection",
            model="Air Quality Monitor",
            serial_number=str(station_id),
        )
