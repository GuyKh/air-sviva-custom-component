"""Data definitions for Air Sviva."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from air_sviva_api.client import SvivaAirClient
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
    from homeassistant.loader import Integration


@dataclass
class AirSvivaData:
    """Air Sviva runtime data stored in hass.data."""

    client: SvivaAirClient
    integration: Integration
    coordinator: DataUpdateCoordinator[dict[str, Any]]
    region_id: int
    region_name: str | None
    station_id: int
    station_name: str
    station_target: str | None
    city: str | None
    owner: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    height: str | None
    device_model: str | None
    device_manufacturer: str | None
