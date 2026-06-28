"""Air Sviva Entity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import AirSvivaUpdateCoordinator

if TYPE_CHECKING:
    from .data import AirSvivaData


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
        self._station_id = station_id

        entry_data: AirSvivaData = coordinator.hass.data[DOMAIN][entry_id]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=entry_data.station_name or f"Air Sviva Station {station_id}",
            manufacturer="Israeli Ministry of Environmental Protection",
            model="Air Quality Monitor",
            serial_number=str(station_id),
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes with station metadata."""
        entry_data: AirSvivaData = self.coordinator.hass.data[DOMAIN][self._entry_id]
        attrs: dict[str, Any] = {}

        if entry_data.station_city:
            attrs["city"] = entry_data.station_city
        if entry_data.station_address:
            attrs["address"] = entry_data.station_address
        if entry_data.station_owner:
            attrs["owner"] = entry_data.station_owner
        if entry_data.station_target:
            attrs["station_type"] = entry_data.station_target
        if entry_data.station_region_name:
            attrs["region"] = entry_data.station_region_name
        if entry_data.station_height:
            attrs["altitude"] = entry_data.station_height
        if entry_data.station_latitude is not None:
            attrs["latitude"] = entry_data.station_latitude
        if entry_data.station_longitude is not None:
            attrs["longitude"] = entry_data.station_longitude

        return attrs
