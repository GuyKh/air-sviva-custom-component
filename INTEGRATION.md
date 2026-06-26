# Air Sviva Integration for Home Assistant

A Home Assistant custom component for Israeli air quality monitoring using data from the Ministry of Environmental Protection (air.sviva.gov.il).

## Features

- Config flow with 2-step setup: Region → Station
- Auto-select closest station via Haversine distance from HA coordinates
- Dynamic sensors — one entity per pollutant (PM2.5, PM10, NO₂, SO₂, O₃, CO)
- Official station AQI sensor via the Air Sviva index endpoint
- Hebrew/English/Arabic translations
- 10-minute polling interval

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Search for "Air Sviva"
3. Click "Download"
4. Restart Home Assistant
5. Add integration via Settings → Devices & Services → Add Integration → Search "Air Sviva"

### Manual

Copy `custom_components/air_sviva` to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Air Sviva"
3. Select your region from the dropdown
4. Select your station (closest station to your HA location is pre-selected)
5. Submit

## Sensors

Each pollutant creates a separate sensor entity:
- AQI (official station air quality index)
- PM2.5 (µg/m³)
- PM10 (µg/m³)
- NO₂ (ppb)
- SO₂ (ppb)
- O₃ (ppb)
- CO (ppm)

Sensor names and units include Hebrew translations.

## Data Source

Data provided by the Israeli Ministry of Environmental Protection via air.sviva.gov.il

## Requirements

- Home Assistant 2023.0+
- Python 3.11+

## License

MIT
