# Letterboxd Home Assistant Component Structure

## Folder Structure

```
letterboxd/
├── custom_components/
│   └── letterboxd/
│       ├── __init__.py          # Component initialization
│       ├── manifest.json         # Component metadata and requirements
│       ├── config_flow.py        # Configuration flow for adding feeds
│       ├── const.py              # Constants and configuration keys
│       ├── coordinator.py        # Data fetching and update coordinator
│       ├── sensor.py             # Sensor entities (feeds and latest movie)
│       └── strings.json          # Translation strings for UI
├── README.md                     # User documentation
├── hacs.json                     # HACS integration metadata
├── .gitignore                    # Git ignore rules
└── STRUCTURE.md                  # This file
```

## Component Files

### `__init__.py`
- Sets up the integration entry point
- Initializes the coordinator
- Registers sensor platform

### `manifest.json`
- Defines component metadata
- Lists dependencies (feedparser, aiohttp)
- Sets integration type and IoT class

### `config_flow.py`
- Handles user input during integration setup
- Validates feed URLs
- Supports adding multiple feeds
- Uses translation strings for UI

### `const.py`
- Defines all constants used across the component
- Configuration keys
- Attribute names
- Default values

### `coordinator.py`
- Fetches data from Letterboxd RSS feeds
- Parses movie information (title, rating, image, date)
- Manages update intervals (default: 6 hours)
- Aggregates data from multiple feeds
- Finds latest movie across all feeds

### `sensor.py`
- Creates sensor entities for each feed
- Creates "latest movie" sensor
- Exposes movie data as sensor attributes
- Handles entity registration

### `strings.json`
- Translation strings for config flow UI
- Error messages
- Form labels

## Key Features

1. **Multiple Feed Support**: Users can add multiple Letterboxd RSS feeds
2. **Auto-Updates**: Feeds update automatically every 6 hours (configurable)
3. **Latest Movie Tracking**: Special sensor that shows the most recent movie
4. **Rich Data**: Each movie includes title, rating, image URL, date, and link
5. **Dashboard Ready**: Latest movie sensor perfect for picture-entity cards

## Data Flow

1. User adds integration → `config_flow.py` validates feeds
2. Integration loads → `__init__.py` creates coordinator
3. Coordinator fetches → `coordinator.py` parses RSS feeds
4. Sensors update → `sensor.py` exposes data as entities
5. Dashboard displays → Latest movie sensor shows current movie

## Update Mechanism

- Uses Home Assistant's `DataUpdateCoordinator`
- Default update interval: 6 hours (360 minutes)
- Configurable per integration instance
- Handles errors gracefully (continues with other feeds if one fails)
