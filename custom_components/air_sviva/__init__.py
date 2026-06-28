"""The Air Sviva integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from air_sviva_api.client import SvivaAirClient
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.translation import async_get_translations
from homeassistant.loader import async_get_loaded_integration

from .const import (
    CONF_ADDRESS,
    CONF_CITY,
    CONF_HEIGHT,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OWNER,
    CONF_REGION_ID,
    CONF_REGION_NAME,
    CONF_STATION_ID,
    CONF_STATION_NAME,
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

    translations = await async_get_translations(
        hass, hass.config.language, "entity", {DOMAIN}
    )
    label_station_type = translations.get(
        f"component.{DOMAIN}.entity.device_label.station_type.name"
    )
    label_owner = translations.get(f"component.{DOMAIN}.entity.device_label.owner.name")

    station_target = entry.data.get(CONF_STATION_TARGET)
    owner = entry.data.get(CONF_OWNER)
    device_model = f"{label_station_type}: {station_target}" if station_target else None
    device_manufacturer = f"{label_owner}: {owner}" if owner else None

    entry_data = AirSvivaData(
        client=shared_client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        region_id=entry.data[CONF_REGION_ID],
        region_name=entry.data.get(CONF_REGION_NAME),
        station_id=entry.data[CONF_STATION_ID],
        station_name=entry.data[CONF_STATION_NAME],
        station_target=station_target,
        city=entry.data.get(CONF_CITY),
        owner=owner,
        address=entry.data.get(CONF_ADDRESS),
        latitude=entry.data.get(CONF_LATITUDE),
        longitude=entry.data.get(CONF_LONGITUDE),
        height=entry.data.get(CONF_HEIGHT),
        device_model=device_model,
        device_manufacturer=device_manufacturer,
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
