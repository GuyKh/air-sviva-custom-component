"""Config flow for Air Sviva integration."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import voluptuous as vol
from air_sviva_api.client import SvivaAirClient
from air_sviva_api.models.exceptions import SvivaAirError
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    CONF_REGION_ID,
    CONF_STATION_ADDRESS,
    CONF_STATION_CITY,
    CONF_STATION_HEIGHT,
    CONF_STATION_ID,
    CONF_STATION_LATITUDE,
    CONF_STATION_LONGITUDE,
    CONF_STATION_NAME,
    CONF_STATION_OWNER,
    CONF_STATION_REGION_NAME,
    CONF_STATION_TARGET,
    DOMAIN,
    LOGGER,
)

if TYPE_CHECKING:
    from air_sviva_api.models.region import Region, Station


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in km."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sin_dlat = math.sin(dlat / 2)
    sin_dlon = math.sin(dlon / 2)
    a = sin_dlat**2 + math.cos(lat1) * math.cos(lat2) * sin_dlon**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371.0 * c


def _find_closest_station(
    stations: list[Station], ha_lat: float, ha_lon: float
) -> Station | None:
    """Find the closest station to Home Assistant coordinates."""
    closest_station = None
    closest_distance = float("inf")

    for station in stations:
        if hasattr(station, "location") and station.location:
            lat = station.location.latitude
            lon = station.location.longitude
            if lat is not None and lon is not None:
                dist = _haversine_distance(ha_lat, ha_lon, lat, lon)
                if dist < closest_distance:
                    closest_distance = dist
                    closest_station = station

    if closest_distance > 10:
        LOGGER.debug(
            "Closest station is too far away: %s > 10km, selecting first station",
            closest_distance,
        )
        return stations[0] if stations else None

    LOGGER.debug(
        "Closest station: %s - %s km",
        closest_station.name if closest_station else "None",
        round(closest_distance, 2),
    )
    return closest_station


def _get_station_pollutants(station: Station) -> str:
    """Get comma-separated list of pollutants for a station."""
    if hasattr(station, "pollutants") and station.pollutants:
        return ", ".join(station.pollutants)
    return ""


class AirSvivaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Config flow for Air Sviva."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        super().__init__()
        self._regions: list[Region] | None = None
        self._stations_by_region: dict[int, list[Station]] = {}
        self._selected_region_id: int | None = None

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial configuration step - select region."""
        errors: dict[str, str] = {}

        await self._fetch_regions(errors)

        if user_input is not None:
            self._selected_region_id = user_input[CONF_REGION_ID]
            return await self.async_step_select_station()

        # Auto-select region of closest station
        default_region_id = self._get_default_region_by_proximity()

        region_options = {r.region_id: r.name for r in self._regions or []}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REGION_ID,
                        default=default_region_id,
                    ): vol.In(region_options),
                },
            ),
            errors=errors,
        )

    async def async_step_select_station(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the station selection step."""
        errors: dict[str, str] = {}

        if self._selected_region_id is None:
            LOGGER.error("Station selection step reached but no region selected")
            return self.async_abort(reason="unknown")

        active_stations = self._stations_by_region.get(self._selected_region_id, [])

        if not active_stations:
            LOGGER.warning(
                "No active stations in region %s",
                self._selected_region_id,
            )
            return self.async_abort(reason="no_stations")

        if user_input is not None and CONF_STATION_ID in user_input:
            station_id = user_input[CONF_STATION_ID]
            selected_station = next(
                (s for s in active_stations if s.station_id == station_id), None
            )
            if selected_station:
                LOGGER.debug("Selected station: %s", selected_station.name)

                region_name = next(
                    (
                        r.name
                        for r in self._regions or []
                        if r.region_id == self._selected_region_id
                    ),
                    None,
                )

                station_lat = None
                station_lon = None
                if selected_station.location:
                    station_lat = selected_station.location.latitude
                    station_lon = selected_station.location.longitude

                return self.async_create_entry(
                    title=f"Air Sviva - {selected_station.name}",
                    data={
                        CONF_REGION_ID: self._selected_region_id,
                        CONF_STATION_ID: station_id,
                        CONF_STATION_NAME: selected_station.name,
                        CONF_STATION_CITY: selected_station.city,
                        CONF_STATION_ADDRESS: selected_station.address,
                        CONF_STATION_OWNER: selected_station.owner,
                        CONF_STATION_TARGET: selected_station.station_target,
                        CONF_STATION_HEIGHT: selected_station.height,
                        CONF_STATION_LATITUDE: station_lat,
                        CONF_STATION_LONGITUDE: station_lon,
                        CONF_STATION_REGION_NAME: region_name,
                    },
                )
            LOGGER.error(
                "Selected station_id %s not found in stations list (available: %s)",
                station_id,
                [s.station_id for s in active_stations],
            )
            errors["base"] = "invalid_station"

        # Auto-select closest station
        ha_lat = self.hass.config.latitude
        ha_lon = self.hass.config.longitude
        closest = _find_closest_station(active_stations, ha_lat, ha_lon)

        # Build station options with pollutants info
        station_options = {}
        for station in active_stations:
            pollutants = _get_station_pollutants(station)
            label = f"{station.name}, {station.city}" if station.city else station.name
            if pollutants:
                label = f"{label} - {pollutants}"
            station_options[station.station_id] = label

        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATION_ID,
                        default=closest.station_id if closest else None,
                    ): vol.In(station_options),
                },
            ),
            errors=errors,
        )

    async def _fetch_regions(self, errors: dict[str, str]) -> None:
        """Fetch regions and stations from API."""
        if self._regions is not None:
            return
        try:
            client = SvivaAirClient(
                session=async_create_clientsession(self.hass),
            )
            await client.generate_token()
            self._regions = await client.get_regions()
            LOGGER.debug("Fetched %d regions", len(self._regions or []))
            self._build_stations_by_region()
        except SvivaAirError as exc:
            LOGGER.error("Failed to fetch regions from Air Sviva API: %s", exc)
            errors["base"] = "cannot_connect"
        except OSError as exc:
            LOGGER.exception("Unexpected error fetching regions: %s", exc)
            errors["base"] = "unknown"

    def _build_stations_by_region(self) -> None:
        """Build stations by region dictionary."""
        for region in self._regions or []:
            if region.stations:
                active = [s for s in region.stations if getattr(s, "active", False)]
                if active:
                    self._stations_by_region[region.region_id] = active

    def _get_default_region_by_proximity(self) -> int | None:
        """Get default region ID based on closest station to HA coordinates."""
        ha_lat = self.hass.config.latitude
        ha_lon = self.hass.config.longitude

        closest_station = None
        closest_distance = float("inf")
        closest_region_id = None

        for region_id, stations in self._stations_by_region.items():
            for station in stations:
                if hasattr(station, "location") and station.location:
                    lat = station.location.latitude
                    lon = station.location.longitude
                    if lat is not None and lon is not None:
                        dist = _haversine_distance(ha_lat, ha_lon, lat, lon)
                        if dist < closest_distance:
                            closest_distance = dist
                            closest_station = station
                            closest_region_id = region_id

        if closest_region_id:
            LOGGER.debug(
                "Auto-selected region %s (closest station: %s - %s km)",
                closest_region_id,
                closest_station.name if closest_station else "None",
                round(closest_distance, 2),
            )
        return closest_region_id
