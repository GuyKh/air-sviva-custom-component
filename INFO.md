# Air Sviva

Home Assistant integration for Israeli air quality monitoring using Ministry of Environmental Protection data.

## Installation

This integration can be installed via [HACS](https://hacs.xyz/).

1. Open HACS in Home Assistant
2. Search for "Air Sviva"
3. Click "Download"
4. Restart Home Assistant

## Configuration

After installation, go to **Settings > Devices & Services > Add Integration** and search for "Air Sviva".

The integration will:
1. Fetch available regions and stations from the Ministry of Environmental Protection
2. Allow you to select a region and station, or auto-select the closest station to your Home Assistant location
3. Create sensors for each pollutant measured at the selected station

## Sensors

Sensors are created dynamically based on the pollutants available at the selected station. Each sensor includes:
- Current value
- Unit of measurement (Hebrew translations provided)
- Last updated timestamp (from station data, not fetch time)
- Device class where applicable

## Data Source

Data is sourced from the Israeli Ministry of Environmental Protection (המשרד להגנת הסביבה) air quality monitoring network.

## Links

- [GitHub Repository](https://github.com/GuyKh/air-sviva-custom-component)
- [Issues](https://github.com/GuyKh/air-sviva-custom-component/issues)