"""Sensor platform for Air Sviva."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .entity import AirSvivaEntity

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


class AirSvivaAQISensor(AirSvivaEntity, SensorEntity):
    """Air Sviva sensor for the official station AQI."""

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
        self._attr_translation_key = "aqi"
        self._attr_native_unit_of_measurement = "AQI"

    @property
    def native_value(self) -> float | None:
        """Return the current official station AQI value."""
        data = self.coordinator.data
        if data is None:
            return None
        aqi = data.get("aqi") or {}
        return aqi.get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        data = self.coordinator.data
        if data is None:
            return {}
        aqi = data.get("aqi") or {}
        return {
            "dominant_pollutant": aqi.get("pollutant"),
            "dominant_pollutant_value": aqi.get("pollutant_value"),
            "pollutant_id": aqi.get("pollutant_id"),
            "color": aqi.get("color"),
            "description": aqi.get("description"),
            "datetime": aqi.get("datetime"),
            "index_id": aqi.get("index_id"),
            "pollutant_time_base": aqi.get("pollutant_time_base"),
        }
