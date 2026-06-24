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

SCAN_INTERVAL = timedelta(minutes=10)
DEFAULT_HOURS_BACK = 4

PLATFORMS: list[Platform] = [Platform.SENSOR]

SERVICE_DEBUG_GET_COORDINATOR_DATA = "debug_get_coordinator_data"
