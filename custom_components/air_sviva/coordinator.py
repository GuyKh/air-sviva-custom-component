"""Air Sviva Coordinator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SvivaAirError
from .const import CONF_REGION_ID, CONF_STATION_ID, DOMAIN, LOGGER, SCAN_INTERVAL

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .api import RegionStationData, StationIndexData, SvivaAirClient
    from .data import AirSvivaData


def _parse_station_channels(station_data: RegionStationData) -> dict[str, Any]:
    """Parse station channels from RegionStationData into channel dict."""
    channels: dict[str, Any] = {}

    if not station_data.region_data or not station_data.region_data.channels:
        return channels

    for channel in station_data.region_data.channels:
        if not channel.active or channel.value is None:
            continue

        # Use alias (Hebrew name) as description if available
        description = channel.alias or channel.description

        channels[channel.name] = {
            "id": channel.id,
            "name": channel.name,
            "alias": channel.alias,
            "value": channel.value,
            "status": channel.status,
            "valid": channel.valid,
            "units": channel.units,
            "pollutant_id": channel.pollutant_id,
            "datetime": channel.datetime,
            "description": description,
        }

    return channels


def _parse_station_index(
    station_index: StationIndexData | None,
) -> dict[str, Any] | None:
    """Parse station index data into a dict for sensors."""
    if station_index is None:
        return None

    return {
        "datetime": station_index.datetime,
        "pollutant": station_index.pollutant,
        "index_id": station_index.index_id,
        "index": station_index.index,
        "value": station_index.value,
        "color": station_index.color,
        "description": station_index.description,
        "pollutant_id": station_index.pollutant_id,
        "pollutant_time_base": station_index.pollutant_time_base,
        "indexes": station_index.indexes or [],
    }


class AirSvivaUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch station data from Air Sviva API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._station_id = config_entry.data[CONF_STATION_ID]
        self._region_id = config_entry.data[CONF_REGION_ID]

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.config_entry = config_entry

    async def _async_update_data(self) -> dict[str, Any]:
        entry_data: AirSvivaData = self.hass.data[DOMAIN][self.config_entry.entry_id]
        client: SvivaAirClient = entry_data.client

        try:
            # Fetch latest data for the configured station's region
            response: list[RegionStationData] = await client.get_regions_latest_data(
                region_ids=[self._region_id],
                hours_back=4,
            )
        except SvivaAirError as exc:
            LOGGER.error(
                "Failed to fetch station data for %s: %s",
                self._station_id,
                exc,
            )
            msg = f"Failed to fetch data: {exc}"
            raise UpdateFailed(msg) from exc
        except Exception as exc:
            LOGGER.exception(
                "Unexpected error fetching station data for %s",
                self._station_id,
            )
            msg = f"Unexpected error: {exc}"
            raise UpdateFailed(msg) from exc

        index_response: list[StationIndexData] = []
        try:
            index_response = await client.get_stations_latest_index(
                region_ids=all_regions,
                hours_back=24,
            )
        except SvivaAirError as exc:
            LOGGER.warning(
                "Failed to fetch official station index for %s: %s",
                self._station_id,
                exc,
            )

        data: dict[str, Any] = {
            "station_id": self._station_id,
            "channels": {},
            "station_index": None,
        }

        # Find the selected station in the response
        station_data = next(
            (s for s in response if s.station_id == self._station_id), None
        )

        if not station_data:
            LOGGER.debug("Station %s not found in response", self._station_id)
            return data

        data["station_id"] = station_data.station_id

        # Parse all channels for this station
        data["channels"] = _parse_station_channels(station_data)

        station_index = next(
            (s for s in index_response if s.station_id == self._station_id),
            None,
        )
        data["station_index"] = _parse_station_index(station_index)

        # Get the datetime from the first channel
        if station_data.region_data and station_data.region_data.channels:
            first_channel = station_data.region_data.channels[0]
            data["datetime"] = first_channel.datetime

        return data
