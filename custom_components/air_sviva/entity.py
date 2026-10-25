# Copyright 2024 Guy Khnyan
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

"""Air Sviva Entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
        entry_data: AirSvivaData = self.coordinator.hass.data[DOMAIN][entry_id]

        device_name = entry_data.station_name
        if entry_data.city:
            device_name = f"{entry_data.station_name}, {entry_data.city}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=device_name,
            manufacturer=entry_data.device_manufacturer
            or "Israeli Ministry of Environmental Protection",
            model=entry_data.device_model or "Air Quality Monitor",
            serial_number=str(station_id),
            suggested_area=entry_data.city,
        )
