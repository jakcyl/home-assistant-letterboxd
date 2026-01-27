"""Data update coordinator for Letterboxd."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import feedparser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_DATE_ADDED,
    ATTR_IMAGE_URL,
    ATTR_LINK,
    ATTR_MOVIE_TITLE,
    ATTR_RATING,
    CONF_FEED_NAME,
    CONF_FEED_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class LetterboxdFeedCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data for a single Letterboxd feed."""

    def __init__(
        self,
        hass: HomeAssistant,
        feed_config: dict[str, Any],
        entry_id: str,
    ) -> None:
        """Initialize."""
        self.feed_config = feed_config
        self.feed_url = feed_config[CONF_FEED_URL]
        self.feed_name = feed_config.get(CONF_FEED_NAME, self.feed_url)
        self.scan_interval = feed_config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.entry_id = entry_id

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.feed_name}",
            update_interval=timedelta(minutes=self.scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from a single Letterboxd feed."""
        movies: list[dict[str, Any]] = []
        latest_movie: dict[str, Any] | None = None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.feed_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        _LOGGER.warning(
                            "Failed to fetch feed %s: HTTP %s", self.feed_name, response.status
                        )
                        return {
                            "movies": [],
                            "latest_movie": None,
                            "error": f"HTTP {response.status}",
                        }

                    text = await response.text()
                    feed = feedparser.parse(text)

                    for entry in feed.entries:
                        # Extract movie information from Letterboxd RSS feed
                        title = entry.get("title", "").strip()
                        link = entry.get("link", "")
                        published = entry.get("published_parsed")

                        # Parse rating from title (format: "Movie Title ★★★★☆" or "Movie Title (2023) ★★★★☆")
                        rating = None
                        if "★" in title:
                            stars = title.count("★")
                            half_star = "½" in title
                            rating = stars + (0.5 if half_star else 0)
                            # Remove rating from title
                            title = title.split("★")[0].strip()
                            # Remove year if present: "Movie Title (2023)" -> "Movie Title"
                            if "(" in title and ")" in title:
                                title = title.rsplit("(", 1)[0].strip()

                        # Extract image URL from entry content or summary
                        image_url = None
                        if hasattr(entry, "content") and entry.content:
                            for content in entry.content:
                                if "img" in content.get("value", "").lower():
                                    import re
                                    img_match = re.search(
                                        r'<img[^>]+src=["\']([^"\']+)["\']',
                                        content.get("value", ""),
                                    )
                                    if img_match:
                                        image_url = img_match.group(1)
                        elif hasattr(entry, "summary"):
                            import re
                            img_match = re.search(
                                r'<img[^>]+src=["\']([^"\']+)["\']',
                                entry.summary,
                            )
                            if img_match:
                                image_url = img_match.group(1)

                        # Parse date
                        date_added = None
                        if published:
                            try:
                                date_added = datetime(*published[:6]).isoformat()
                            except (ValueError, TypeError):
                                pass

                        movie_data = {
                            ATTR_MOVIE_TITLE: title,
                            ATTR_RATING: rating,
                            ATTR_IMAGE_URL: image_url,
                            ATTR_DATE_ADDED: date_added or entry.get("published", ""),
                            ATTR_LINK: link,
                            "unique_id": self._generate_movie_unique_id(title, link, date_added),
                        }

                        movies.append(movie_data)

                    # Find latest movie (most recent date_added)
                    if movies:
                        sorted_movies = sorted(
                            movies,
                            key=lambda x: x.get(ATTR_DATE_ADDED, ""),
                            reverse=True,
                        )
                        latest_movie = sorted_movies[0]

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching feed %s: %s", self.feed_name, err)
            return {
                "movies": [],
                "latest_movie": None,
                "error": str(err),
            }
        except Exception as err:
            _LOGGER.exception("Unexpected error processing feed %s: %s", self.feed_name, err)
            return {
                "movies": [],
                "latest_movie": None,
                "error": str(err),
            }

        return {
            "movies": movies,
            "latest_movie": latest_movie,
            "feed_url": self.feed_url,
            "last_update": datetime.now().isoformat(),
        }

    def _generate_movie_unique_id(self, title: str, link: str, date_added: str | None) -> str:
        """Generate a unique ID for a movie within this feed."""
        # Use feed name + movie title + date to ensure uniqueness
        # Even if same movie appears in multiple feeds, they'll have different IDs
        base_id = f"{self.entry_id}_{self.feed_name}_{title}_{date_added or link}"
        # Clean up the ID to be valid for entity IDs
        import re
        base_id = re.sub(r"[^a-zA-Z0-9_]", "_", base_id)
        base_id = base_id.lower()
        return base_id[:255]  # Limit length


class LetterboxdDataUpdateCoordinator:
    """Main coordinator that manages multiple feed coordinators."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = config_entry
        self.feeds = config_entry.data.get("feeds", [])
        self.feed_coordinators: dict[str, LetterboxdFeedCoordinator] = {}

        # Create a coordinator for each feed
        for feed_config in self.feeds:
            feed_name = feed_config.get(CONF_FEED_NAME, feed_config.get(CONF_FEED_URL))
            coordinator = LetterboxdFeedCoordinator(
                hass, feed_config, config_entry.entry_id
            )
            self.feed_coordinators[feed_name] = coordinator

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh for all feed coordinators."""
        for coordinator in self.feed_coordinators.values():
            await coordinator.async_config_entry_first_refresh()

    @property
    def data(self) -> dict[str, Any]:
        """Return aggregated data from all feed coordinators."""
        return {
            feed_name: coordinator.data
            for feed_name, coordinator in self.feed_coordinators.items()
        }
