"""The Air Sviva integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from air_sviva_api.client import SvivaAirClient
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

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
    PLATFORMS,
    SHARED_CLIENT_KEY,
)
from .coordinator import AirSvivaUpdateCoordinator
from .data import AirSvivaData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up the Air Sviva integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    shared_client: SvivaAirClient | None = hass.data[DOMAIN].get(SHARED_CLIENT_KEY)
    if shared_client is None:
        shared_client = SvivaAirClient(session=async_get_clientsession(hass))
        await shared_client.generate_token()
        hass.data[DOMAIN][SHARED_CLIENT_KEY] = shared_client

    coordinator = AirSvivaUpdateCoordinator(hass=hass, config_entry=entry)

    entry_data = AirSvivaData(
        client=shared_client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        region_id=entry.data[CONF_REGION_ID],
        station_id=entry.data[CONF_STATION_ID],
        station_name=entry.data[CONF_STATION_NAME],
        station_city=entry.data.get(CONF_STATION_CITY),
        station_address=entry.data.get(CONF_STATION_ADDRESS),
        station_owner=entry.data.get(CONF_STATION_OWNER),
        station_target=entry.data.get(CONF_STATION_TARGET),
        station_height=entry.data.get(CONF_STATION_HEIGHT),
        station_latitude=entry.data.get(CONF_STATION_LATITUDE),
        station_longitude=entry.data.get(CONF_STATION_LONGITUDE),
        station_region_name=entry.data.get(CONF_STATION_REGION_NAME),
    )

    hass.data[DOMAIN][entry.entry_id] = entry_data

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        entry_keys = [k for k in hass.data[DOMAIN] if k != SHARED_CLIENT_KEY]
        if not entry_keys:
            hass.data[DOMAIN].pop(SHARED_CLIENT_KEY, None)
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
