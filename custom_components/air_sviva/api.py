"""Small Air Sviva API client for this Home Assistant integration."""

from __future__ import annotations

import base64
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

from aiohttp import ClientError, ClientResponse, ClientSession

MAIN_URL = "https://air.sviva.gov.il/"
BASE_URL = "https://air-papi.sviva.gov.il/v1/envista/"
AUTH_GENERATION_URL = "https://air-papi.sviva.gov.il/v1/GenerateToken"
GUEST_API_URL = "https://air.sviva.gov.il/Account/GetApiToken"

PRIMARY_DOMAIN = "air-papi.sviva.gov.il"
SECONDARY_DOMAIN = "air-api.sviva.gov.il"
FALLBACK_DOMAINS = {
    PRIMARY_DOMAIN: SECONDARY_DOMAIN,
    SECONDARY_DOMAIN: PRIMARY_DOMAIN,
}
RETRYABLE_STATUS_CODES = {404, 406, 500, 502, 503, 504}
AUTH_TOKEN_MAX_AGE_SECONDS = 45 * 60

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en,he;q=0.9",
    "origin": MAIN_URL.rstrip("/"),
    "referer": MAIN_URL,
    "domainname": "sviva",
    "envi-data-source": "MANA",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


class SvivaAirError(Exception):
    """Raised when the Air Sviva API request fails."""


@dataclass
class Location:
    """Station location."""

    latitude: float | None = None
    longitude: float | None = None


@dataclass
class Station:
    """Air monitoring station."""

    station_id: int
    name: str
    short_name: str | None = None
    city: str | None = None
    address: str | None = None
    active: bool = False
    location: Location | None = None


@dataclass
class Region:
    """Air monitoring region."""

    region_id: int
    name: str
    stations: list[Station] | None = None


@dataclass
class ChannelReading:
    """Latest channel reading."""

    id: int | None = None
    name: str = ""
    alias: str | None = None
    value: float | None = None
    status: int | None = None
    valid: bool = False
    description: str | None = None
    units: str | None = None
    active: bool = False
    pollutant_id: int | None = None
    datetime: str | None = None


@dataclass
class RegionData:
    """Latest readings for a station."""

    datetime: str | None = None
    channels: list[ChannelReading] | None = None


@dataclass
class RegionStationData:
    """Latest station data response item."""

    station_id: int
    region_data: RegionData | None = None


@dataclass
class StationIndexData:
    """Latest official air quality index data for a station."""

    station_id: int
    datetime: str | None = None
    pollutant: str | None = None
    index_id: int | None = None
    index: float | None = None
    value: float | None = None
    color: str | None = None
    description: str | None = None
    pollutant_id: int | None = None
    pollutant_time_base: int | None = None
    indexes: list[dict[str, Any]] | None = None


def _fallback_url(url: str) -> str | None:
    parsed = urlparse(url)
    replacement = FALLBACK_DOMAINS.get(parsed.netloc)
    if replacement is None:
        return None
    return urlunparse(parsed._replace(netloc=replacement))


def _jwt_expired(
    token: str,
    generated_at: float,
    buffer_seconds: int = 60,
) -> bool:
    if time.time() - generated_at >= AUTH_TOKEN_MAX_AGE_SECONDS:
        return True

    parts = token.split(".")
    if len(parts) != 3:
        return False
    try:
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return False
    exp = decoded.get("exp")
    return exp is not None and int(time.time()) + buffer_seconds >= exp


async def _json_or_text(response: ClientResponse) -> Any:
    text = await response.text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _clean_token(token: Any) -> str:
    if isinstance(token, str):
        return token.strip().replace('"', "")
    return str(token)


def _station_from_dict(data: dict[str, Any]) -> Station:
    location = data.get("location") or {}
    return Station(
        station_id=data["stationId"],
        name=data.get("name") or "",
        short_name=data.get("shortName"),
        city=data.get("city"),
        address=data.get("address"),
        active=bool(data.get("active")),
        location=Location(
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
        )
        if location
        else None,
    )


def _channel_from_dict(data: dict[str, Any]) -> ChannelReading:
    return ChannelReading(
        id=data.get("id"),
        name=data.get("name") or "",
        alias=data.get("alias"),
        value=data.get("value"),
        status=data.get("status"),
        valid=bool(data.get("valid")),
        description=data.get("description"),
        units=data.get("units"),
        active=bool(data.get("active")),
        pollutant_id=data.get("pollutantId"),
        datetime=data.get("datetime"),
    )


def _station_index_from_dict(data: dict[str, Any]) -> StationIndexData:
    return StationIndexData(
        station_id=data["stationId"],
        datetime=data.get("datetime"),
        pollutant=data.get("pollutant"),
        index_id=data.get("indexId"),
        index=data.get("index"),
        value=data.get("value"),
        color=data.get("color"),
        description=data.get("description"),
        pollutant_id=data.get("pollutantId"),
        pollutant_time_base=data.get("PollutantTimeBase"),
        indexes=data.get("indexes"),
    )


class SvivaAirClient:
    """Async client for the public Air Sviva API."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the client."""
        self._session = session
        self._request_verification_token = str(uuid.uuid4())
        self._auth_token: str | None = None
        self._auth_token_generated_at = 0.0

    def _headers(self) -> dict[str, str]:
        headers = dict(HEADERS)
        headers["x-requestverificationtoken"] = self._request_verification_token
        if self._auth_token:
            headers["authorization"] = f"JwtToken {self._auth_token}"
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        urls = [url]
        fallback = _fallback_url(url)
        if fallback:
            urls.append(fallback)

        last_error: Exception | None = None
        for attempt_url in urls:
            try:
                async with self._session.request(
                    method,
                    attempt_url,
                    headers=headers,
                    json=json_data,
                    timeout=30,
                ) as response:
                    payload = await _json_or_text(response)
                    if response.status == 200:
                        return payload
                    if response.status in RETRYABLE_STATUS_CODES:
                        last_error = SvivaAirError(
                            f"API returned status {response.status}: {payload}"
                        )
                        continue
                    msg = f"API returned status {response.status}: {payload}"
                    raise SvivaAirError(msg)
            except (TimeoutError, ClientError) as exc:
                last_error = exc
                continue

        raise SvivaAirError(str(last_error))

    async def generate_token(self) -> str:
        """Generate and store an API auth token."""
        api_token_headers = self._headers()
        api_token_headers["content-type"] = "application/json; charset=UTF-8"
        api_token_headers["accept"] = "application/json, text/javascript, */*; q=0.01"
        api_token = await self._request(
            "POST",
            GUEST_API_URL,
            api_token_headers,
            {"userName": "Guest"},
        )

        token_headers = self._headers()
        token_headers["accept"] = "application/json"
        token_headers["authorization"] = f"ApiToken {_clean_token(api_token)}"
        self._auth_token = _clean_token(
            await self._request("POST", AUTH_GENERATION_URL, token_headers, {})
        )
        self._auth_token_generated_at = time.time()
        return self._auth_token

    async def _ensure_auth_headers(self) -> dict[str, str]:
        if self._auth_token is None or _jwt_expired(
            self._auth_token,
            self._auth_token_generated_at,
        ):
            await self.generate_token()
        return self._headers()

    async def _authorized_request(self, method: str, url: str) -> Any:
        try:
            return await self._request(
                method,
                url,
                await self._ensure_auth_headers(),
            )
        except SvivaAirError as exc:
            if "Unauthorized" not in str(exc):
                raise
            self._auth_token = None
            return await self._request(
                method,
                url,
                await self._ensure_auth_headers(),
            )

    async def get_regions(self) -> list[Region]:
        """Get all monitoring regions with stations."""
        response = await self._authorized_request(
            "GET",
            BASE_URL + "regions",
        )
        return [
            Region(
                region_id=region["regionId"],
                name=region.get("name") or "",
                stations=[
                    _station_from_dict(station)
                    for station in (region.get("stations") or [])
                ],
            )
            for region in response
        ]

    async def get_regions_latest_data(
        self,
        region_ids: list[int],
        hours_back: int = 4,
    ) -> list[RegionStationData]:
        """Get latest readings for the requested regions."""
        ids = ",".join(str(region_id) for region_id in region_ids)
        query = f"?unitConversion=true&regionsIds={ids}&hoursBack={hours_back}"
        response = await self._authorized_request(
            "GET",
            BASE_URL + "regions/data/latest" + query,
        )

        stations: list[RegionStationData] = []
        for item in response:
            region_data = item.get("regionData") or {}
            channels = [
                _channel_from_dict(channel)
                for channel in (region_data.get("channels") or [])
            ]
            stations.append(
                RegionStationData(
                    station_id=item["stationId"],
                    region_data=RegionData(
                        datetime=region_data.get("datetime"),
                        channels=channels,
                    ),
                )
            )
        return stations

    async def get_stations_latest_index(
        self,
        region_ids: list[int],
        hours_back: int = 24,
    ) -> list[StationIndexData]:
        """Get latest official index data for the requested regions."""
        ids = ",".join(str(region_id) for region_id in region_ids)
        query = f"?unitConversion=true&regionsIds={ids}&hoursBack={hours_back}"
        response = await self._authorized_request(
            "GET",
            BASE_URL + "stations/index/latest" + query,
        )
        if not isinstance(response, dict):
            return []
        return [
            _station_index_from_dict(item)
            for item in (response.get("data") or [])
            if item.get("stationId") is not None
        ]
