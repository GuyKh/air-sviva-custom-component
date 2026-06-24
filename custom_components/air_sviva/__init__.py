"""The Air Sviva integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import SvivaAirClient
from .const import (
    CONF_REGION_ID,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
    PLATFORMS,
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
    client = SvivaAirClient(session=async_get_clientsession(hass))
    await client.generate_token()

    coordinator = AirSvivaUpdateCoordinator(hass=hass, config_entry=entry)

    entry_data = AirSvivaData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        region_id=entry.data[CONF_REGION_ID],
        station_id=entry.data[CONF_STATION_ID],
        station_name=entry.data[CONF_STATION_NAME],
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry_data

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
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
