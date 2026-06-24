# Air Sviva Custom Component

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

_Integration to integrate with [Israeli Ministry of Environmental Protection air quality API][air-sviva]._

**This integration will set up the following platforms.**

![Example Image][exampleimg]

Platform | Description
-- | --
`sensor` | Air quality sensors from the Israeli Ministry of Environmental Protection monitoring network.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Search for "Air Sviva"
3. Click "Download"
4. Restart Home Assistant

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `air_sviva`.
4. Download _all_ the files from the `custom_components/air_sviva/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant.
7. In the HA UI go to **Settings** → **Devices & Services** → **Add Integration** and search for "Air Sviva".

## Configuration is done in the UI

1. Select your region from the dropdown
2. Select your station (the closest station to your Home Assistant location is pre-selected)
3. Submit

Sensors will be created dynamically based on the pollutants available at the selected station.

## Sensors

Each monitored pollutant creates a separate sensor entity. Sensor names automatically adjust based on your Home Assistant language:

- **English:** Shows pollutant names in English (e.g., "SO₂", "Wind Speed", "Temperature")
- **Hebrew:** Shows non-scientific names in Hebrew (e.g., "מהירות רוח", "טמפרטורה"), scientific notation stays universal (e.g., "SO₂", "PM2.5", "NO₂")

Sensor name format: `sensor.sviva_station_{station_id}_{pollutant}`

## Logs

To view logs in debug add this to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.air_sviva: debug
    air_sviva_api: debug
```

<!---->

## Data Source

Data is sourced from the Israeli Ministry of Environmental Protection (המשרד להגנת הסביבה) air quality monitoring network via [air.sviva.gov.il][air-sviva].

<!---->

## Frequently Asked Questions

#### How often is the data fetched?

The component fetches data every 10 minutes.

#### Which pollutants are monitored?

It depends on the station. Common pollutants include PM2.5, PM10, NO₂, SO₂, O₃, CO, as well as meteorological data like wind speed, wind direction, temperature, humidity, barometric pressure, and more.

#### Why do some sensors show Hebrew names and others show English?

Sensor names follow your Home Assistant language setting. Scientific/metric terms (SO₂, PM2.5, etc.) remain universal regardless of language. Non-scientific names (Wind Direction, Temperature, etc.) are translated.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[air-sviva]: https://air.sviva.gov.il
[buymecoffee]: https://www.buymeacoffee.com/guykh
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/guykh/air-sviva-custom-component.svg?style=for-the-badge
[commits]: https://github.com/guykh/air-sviva-custom-component/commits/main
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/guykh/air-sviva-custom-component.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Guy%20Khmelnitsky%20%40GuyKh-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/guykh/air-sviva-custom-component.svg?style=for-the-badge
[releases]: https://github.com/guykh/air-sviva-custom-component/releases
