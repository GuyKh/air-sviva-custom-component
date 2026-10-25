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

"""Sensor platform for Air Sviva."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass

from .const import DOMAIN
from .entity import AirSvivaEntity

if TYPE_CHECKING:
    from air_sviva_api.models.reading import StationIndexData
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import AirSvivaUpdateCoordinator
    from .data import AirSvivaData


@dataclass(slots=True)
class SensorInitData:
    """Data for sensor initialization."""

    station_id: int
    station_name: str
    pollutant_name: str
    channel_data: dict[str, Any]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Air Sviva sensors from a config entry."""
    entry_data: AirSvivaData = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data.coordinator
    data = coordinator.data

    if data is None or "channels" not in data:
        return

    station_id = entry_data.station_id

    # Create sensors for all channels from the data
    entities = [
        AirSvivaSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            init_data=SensorInitData(
                station_id=station_id,
                station_name=entry_data.station_name,
                pollutant_name=pollutant,
                channel_data=channel_data,
            ),
        )
        for pollutant, channel_data in data["channels"].items()
    ]

    # Also create sensors for pollutants that have sub-indices in the AQI data
    # but are not present in the channels list (fixes issue #26)
    aqi_data = data.get("aqi")
    if aqi_data is not None:
        idx: Any = aqi_data  # type: ignore[assignment]
        if hasattr(idx, "indexes") and idx.indexes:
            # Get the set of pollutant names already have sensors for
            existing_pollutants = {init_data.pollutant_name for init_data in [
                SensorInitData(
                    station_id=station_id,
                    station_name=entry_data.station_name,
                    pollutant_name=pollutant,
                    channel_data=channel_data,
                )
                for pollutant, channel_data in data["channels"].items()
            ]}

            for detail in idx.indexes:
                pollutant = detail.pollutant
                if pollutant and pollutant not in existing_pollutants:
                    entities.append(
                        AirSvivaSensor(
                            coordinator=coordinator,
                            entry_id=entry.entry_id,
                            init_data=SensorInitData(
                                station_id=station_id,
                                station_name=entry_data.station_name,
                                pollutant_name=pollutant,
                                channel_data={
                                    "id": 0,
                                    "name": pollutant,
                                    "alias": None,
                                    "value": detail.index,
                                    "status": 0,
                                    "valid": True,
                                    "units": "AQI",
                                    "pollutant_id": None,
                                    "datetime": None,
                                    "description": None,
                                },
                            ),
                        ),
                    )

    entities.append(
        AirSvivaAQISensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            station_id=station_id,
        ),
    )
    async_add_entities(entities)


class AirSvivaSensor(AirSvivaEntity, SensorEntity):
    """Air Sviva sensor for a single pollutant."""

    _pollutant_name: str
    _channel_data: dict[str, Any]
    _is_wind_direction: bool = False
    _last_value: float | None = None

    def __init__(
        self,
        coordinator: AirSvivaUpdateCoordinator,
        entry_id: str,
        init_data: SensorInitData,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, init_data.station_id)
        self._pollutant_name = init_data.pollutant_name
        self._channel_data = init_data.channel_data
        pollutant = init_data.pollutant_name
        normalized = (
            pollutant.lower().replace(".", "_").replace(" ", "_").replace("-", "_")
        )
        self._attr_unique_id = f"sviva_station_{init_data.station_id}_{normalized}"
        self.entity_id = f"sensor.sviva_station_{init_data.station_id}_{normalized}"

        # Set translation key for HA translation system
        # Use lowercase with underscores for translation key
        clean_name = pollutant.lower()
        clean_name = clean_name.replace(".", "_")
        clean_name = clean_name.replace(" ", "_")
        clean_name = clean_name.replace("-", "_")
        self._attr_translation_key = clean_name

        # Check if this is wind direction for circular sensor handling
        self._is_wind_direction = pollutant.upper() in ("WD", "WDD")

        units = init_data.channel_data.get("units") or "AQI"
        self._attr_native_unit_of_measurement = units

    @property
    def native_value(self) -> float | None:
        """Return the current pollutant index value."""
        data = self.coordinator.data
        if data is None:
            return None

        # First, try to get value from channels
        channel = data.get("channels", {}).get(self._pollutant_name)
        if channel is not None:
            value = channel.get("value")
            if value is not None:
                self._last_value = value
                return value

        # Fall back to AQI sub-index data (fixes issue #26)
        aqi_data = data.get("aqi")
        if aqi_data is not None:
            idx: Any = aqi_data  # type: ignore[assignment]
            if hasattr(idx, "indexes") and idx.indexes:
                for detail in idx.indexes:
                    pollutant_match = detail.pollutant == self._pollutant_name
                    index_valid = detail.index is not None
                    if pollutant_match and index_valid:
                        self._last_value = round(detail.index)
                        return self._last_value

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if data is None:
            return {}
        channel = data.get("channels", {}).get(self._pollutant_name, {})
        attrs: dict[str, Any] = {
            "channel_id": channel.get("id"),
            "pollutant_id": channel.get("pollutant_id"),
            "color": channel.get("color"),
            "description": channel.get("description"),
            "alias": channel.get("alias"),
            "datetime": channel.get("datetime"),
        }
        if self._is_wind_direction:
            attrs["is_circular"] = True
            attrs["max_value"] = 360
            attrs["min_value"] = 0
        return attrs


class AirSvivaAQISensor(AirSvivaEntity, SensorEntity):
    """
    Air Sviva AQI (Air Quality Index) sensor.

    Uses the API-computed station index from /stations/index/latest endpoint.
    """

    _attr_translation_key = "aqi"
    _attr_native_unit_of_measurement = "AQI"
    _attr_icon = "mdi:air-filter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    _last_value: int | None = None

    def __init__(
        self,
        coordinator: AirSvivaUpdateCoordinator,
        entry_id: str,
        station_id: int,
    ) -> None:
        """Initialize the AQI sensor."""
        super().__init__(coordinator, entry_id, station_id)
        self._attr_unique_id = f"sviva_station_{station_id}_aqi"
        self.entity_id = f"sensor.sviva_station_{station_id}_aqi"

    def _get_station_index(self) -> StationIndexData | None:
        data = self.coordinator.data
        if data is None:
            return None
        return data.get("aqi")

    @property
    def native_value(self) -> int | None:
        """Return the current AQI value."""
        idx = self._get_station_index()
        if idx is not None and idx.index is not None:
            self._last_value = round(idx.index)
            return round(idx.index)
        return self._last_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        idx = self._get_station_index()
        if idx is None:
            return {}
        attrs: dict[str, Any] = {
            "classification": idx.description,
            "worst_pollutant": idx.pollutant,
        }
        for detail in idx.indexes or []:
            if detail.pollutant and detail.index is not None:
                attrs[f"{detail.pollutant}_sub_index"] = round(detail.index)
        return attrs
