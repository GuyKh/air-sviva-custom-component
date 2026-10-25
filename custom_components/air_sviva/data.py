# Copyright 2024 Guy Khmelnitsky
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
