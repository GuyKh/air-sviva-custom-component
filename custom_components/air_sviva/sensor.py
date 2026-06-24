"""Sensor platform for Air Sviva."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .entity import AirSvivaEntity

INDEX_SENSOR_KEY = "air_quality_index"
NORMALIZED_INDEX_SCALE = "uv_like_0_11"

if TYPE_CHECKING:
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


def normalize_air_quality_index(index: Any) -> float | None:
    """Normalize the official Air Sviva index to a UV-like risk scale."""
    if index is None:
        return None

    try:
        official_index = float(index)
    except (TypeError, ValueError):
        return None

    if not isfinite(official_index):
        return None

    if official_index > 100:
        return 0.0
    if official_index >= 50:
        normalized = _scale_index_range(official_index, 100, 50, 0.0, 2.9)
    elif official_index >= -1:
        normalized = _scale_index_range(official_index, 50, -1, 3.0, 5.9)
    elif official_index >= -201:
        normalized = _scale_index_range(official_index, -1, -201, 6.0, 7.9)
    elif official_index >= -402:
        normalized = _scale_index_range(official_index, -201, -402, 8.0, 11.0)
    else:
        return 11.0

    return round(normalized, 1)


def _scale_index_range(
    value: float,
    official_high: float,
    official_low: float,
    normalized_low: float,
    normalized_high: float,
) -> float:
    ratio = (official_high - value) / (official_high - official_low)
    return normalized_low + ratio * (normalized_high - normalized_low)


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

    entities: list[SensorEntity] = [
        AirSvivaIndexSensor(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            station_id=station_id,
        )
    ]
    entities.extend(
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
    )
    async_add_entities(entities)


class AirSvivaSensor(AirSvivaEntity, SensorEntity):
    """Air Sviva sensor for a single pollutant."""

    _pollutant_name: str
    _channel_data: dict[str, Any]
    _is_wind_direction: bool = False

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
        channel = data.get("channels", {}).get(self._pollutant_name)
        if channel is None:
            return None
        return channel.get("value")

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


class AirSvivaIndexSensor(AirSvivaEntity, SensorEntity):
    """Air Sviva official air quality index sensor."""

    def __init__(
        self,
        coordinator: AirSvivaUpdateCoordinator,
        entry_id: str,
        station_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, station_id)
        self._attr_unique_id = f"sviva_station_{station_id}_{INDEX_SENSOR_KEY}"
        self.entity_id = f"sensor.sviva_station_{station_id}_{INDEX_SENSOR_KEY}"
        self._attr_translation_key = INDEX_SENSOR_KEY

    @property
    def native_value(self) -> float | None:
        """Return the current official air quality index value."""
        data = self.coordinator.data
        if data is None:
            return None
        station_index = data.get("station_index")
        if station_index is None:
            return None
        return station_index.get("index")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if data is None:
            return {}
        station_index = data.get("station_index")
        if station_index is None:
            return {}
        return {
            "pollutant": station_index.get("pollutant"),
            "pollutant_id": station_index.get("pollutant_id"),
            "value": station_index.get("value"),
            "description": station_index.get("description"),
            "color": station_index.get("color"),
            "datetime": station_index.get("datetime"),
            "normalized_index": normalize_air_quality_index(station_index.get("index")),
            "normalized_index_scale": NORMALIZED_INDEX_SCALE,
            "indexes": station_index.get("indexes", []),
        }
