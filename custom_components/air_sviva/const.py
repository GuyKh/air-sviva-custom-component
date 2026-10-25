# Copyright 2024 Guy Khnyan
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Constants for air_sviva."""

from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.const import Platform

DOMAIN = "air_sviva"
LOGGER: Logger = getLogger(__package__)

ATTRIBUTION = "Data provided by the Israeli Ministry of Environmental Protection"

CONF_REGION_ID = "region_id"
CONF_REGION_NAME = "region_name"
CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_STATION_TARGET = "station_target"
CONF_CITY = "city"
CONF_OWNER = "owner"
CONF_ADDRESS = "address"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_HEIGHT = "height"

SCAN_INTERVAL = timedelta(minutes=10)
DEFAULT_HOURS_BACK = 4

PLATFORMS: list[Platform] = [Platform.SENSOR]

SHARED_CLIENT_KEY: str = f"{DOMAIN}_shared_client"
