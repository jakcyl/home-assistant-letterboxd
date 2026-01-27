"""Constants for the Letterboxd integration."""
from __future__ import annotations

DOMAIN = "letterboxd"

# Default update interval in minutes
DEFAULT_SCAN_INTERVAL = 360  # 6 hours

# Configuration keys
CONF_FEEDS = "feeds"
CONF_FEED_URL = "feed_url"
CONF_FEED_NAME = "feed_name"
CONF_SCAN_INTERVAL = "scan_interval"

# Sensor attributes
ATTR_MOVIE_TITLE = "movie_title"
ATTR_RATING = "rating"
ATTR_IMAGE_URL = "image_url"
ATTR_DATE_ADDED = "date_added"
ATTR_LINK = "link"
ATTR_FEED_NAME = "feed_name"
ATTR_MOVIES = "movies"

# Sensor names
SENSOR_LATEST_MOVIE = "latest_movie"
SENSOR_MOVIE_PREFIX = "movie"
