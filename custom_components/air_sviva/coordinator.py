"""Air Sviva Coordinator."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from air_sviva_api.models.exceptions import SvivaAirError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL

if TYPE_CHECKING:
    from air_sviva_api.client import SvivaAirClient
    from air_sviva_api.models.reading import RegionStationData
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

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


class AirSvivaUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch station data from Air Sviva API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self._station_id = config_entry.data["station_id"]
        self._region_id = config_entry.data["region_id"]

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL.total_seconds() / 60),
        )
        self.config_entry = config_entry

    async def _async_update_data(self) -> dict[str, Any]:
        entry_data: AirSvivaData = self.hass.data[DOMAIN][self.config_entry.entry_id]
        client: SvivaAirClient = entry_data.client

        try:
            # Fetch latest data for all regions (station could be in any region)
            # Using hours_back=4 to get recent data
            all_regions = [r.region_id for r in (await client.get_regions())]
            response: list[RegionStationData] = await client.get_regions_latest_data(
                region_ids=all_regions,
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

        data: dict[str, Any] = {"station_id": self._station_id, "channels": {}}

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

        # Get the datetime from the first channel
        if station_data.region_data and station_data.region_data.channels:
            first_channel = station_data.region_data.channels[0]
            data["datetime"] = first_channel.datetime

        return data
