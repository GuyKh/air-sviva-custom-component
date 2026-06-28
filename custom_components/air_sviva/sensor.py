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
        channel = data.get("channels", {}).get(self._pollutant_name)
        if channel is None:
            return None
        value = channel.get("value")
        if value is not None:
            self._last_value = value
            return value
        return self._last_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if data is None:
            return {}
        channel = data.get("channels", {}).get(self._pollutant_name, {})
        attrs: dict[str, Any] = dict(super().extra_state_attributes or {})
        attrs.update(
            {
                "channel_id": channel.get("id"),
                "pollutant_id": channel.get("pollutant_id"),
                "color": channel.get("color"),
                "description": channel.get("description"),
                "alias": channel.get("alias"),
                "datetime": channel.get("datetime"),
            }
        )
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
        attrs: dict[str, Any] = dict(super().extra_state_attributes or {})
        if idx is None:
            return attrs
        attrs.update(
            {
                "classification": idx.description,
                "worst_pollutant": idx.pollutant,
            }
        )
        for detail in idx.indexes or []:
            if detail.pollutant and detail.index is not None:
                attrs[f"{detail.pollutant}_sub_index"] = round(detail.index)
        return attrs
