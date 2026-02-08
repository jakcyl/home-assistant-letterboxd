"""Constants for the Letterboxd integration."""
from __future__ import annotations

DOMAIN = "letterboxd"

# Default update interval in minutes
DEFAULT_SCAN_INTERVAL = 360  # 6 hours

# Configuration keys
CONF_FEEDS = "feeds"
CONF_FEED_URL = "Feed url"
CONF_FEED_NAME = "Feed name"
CONF_SCAN_INTERVAL = "Scan interval"
CONF_MAX_MOVIES = "max last movies"
CONF_EXPOSE_AS_DEVICES = "movies as devices"

# Defaults
DEFAULT_MAX_MOVIES = 5
MAX_STORED_MOVIES = 500

# Sensor attributes
ATTR_MOVIE_TITLE = "movie_title"
ATTR_RATING = "rating"
ATTR_IMAGE_URL = "image_url"
ATTR_DATE_ADDED = "date_added"
ATTR_LINK = "link"
ATTR_FEED_NAME = "feed_name"
ATTR_MOVIES = "movies"
ATTR_YEAR = "year"

# Sensor names
SENSOR_LATEST_MOVIE = "latest_movie"
SENSOR_RECENT_MOVIES = "recent_movies"
SENSOR_MOVIE_PREFIX = "movie"
