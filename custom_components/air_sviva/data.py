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
    station_id: int
    station_name: str
