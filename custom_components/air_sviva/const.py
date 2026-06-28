"""Constants for air_sviva."""

from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.const import Platform

DOMAIN = "air_sviva"
LOGGER: Logger = getLogger(__package__)

ATTRIBUTION = "Data provided by the Israeli Ministry of Environmental Protection"

CONF_REGION_ID = "region_id"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_STATION_CITY = "station_city"
CONF_STATION_ADDRESS = "station_address"
CONF_STATION_OWNER = "station_owner"
CONF_STATION_TARGET = "station_target"
CONF_STATION_HEIGHT = "station_height"
CONF_STATION_LATITUDE = "station_latitude"
CONF_STATION_LONGITUDE = "station_longitude"
CONF_STATION_REGION_NAME = "station_region_name"

SCAN_INTERVAL = timedelta(minutes=10)
DEFAULT_HOURS_BACK = 4

PLATFORMS: list[Platform] = [Platform.SENSOR]

SHARED_CLIENT_KEY: str = f"{DOMAIN}_shared_client"
