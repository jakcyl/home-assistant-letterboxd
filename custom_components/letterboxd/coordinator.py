"""Data update coordinator for Letterboxd."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any

import aiohttp
import feedparser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_DATE_ADDED,
    ATTR_IMAGE_URL,
    ATTR_LINK,
    ATTR_MOVIE_TITLE,
    ATTR_RATING,
    ATTR_YEAR,
    CONF_FEED_NAME,
    CONF_FEED_URL,
    CONF_MAX_DEVICES,
    CONF_MAX_MOVIES,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_MOVIES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_STORED_MOVIES,
)

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1
STORE_KEY_PREFIX = "letterboxd"


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
        self.max_movies = feed_config.get(CONF_MAX_MOVIES, DEFAULT_MAX_MOVIES)
        self.max_devices = feed_config.get(
            CONF_MAX_DEVICES, feed_config.get(CONF_MAX_MOVIES, DEFAULT_MAX_MOVIES)
        )
        self.entry_id = entry_id
        self._store = Store(
            hass,
            STORE_VERSION,
            f"{STORE_KEY_PREFIX}_{entry_id}_{self.feed_name}.json",
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.feed_name}",
            update_interval=timedelta(minutes=self.scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from a single Letterboxd feed, merge into stored history, return last X."""
        rss_movies: list[dict[str, Any]] = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.feed_url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        _LOGGER.warning(
                            "Failed to fetch feed %s: HTTP %s", self.feed_name, response.status
                        )
                        stored = await self._load_stored()
                        movies = stored[: self.max_movies]
                        movies_for_devices = stored[: self.max_devices]
                        return {
                            "movies": movies,
                            "movies_for_devices": movies_for_devices,
                            "latest_movie": movies[0] if movies else None,
                            "feed_url": self.feed_url,
                            "last_update": datetime.now().isoformat(),
                            "error": f"HTTP {response.status}",
                        }

                    text = await response.text()
                    feed = feedparser.parse(text)

                    for entry in feed.entries:
                        title = entry.get("title", "").strip()
                        link = entry.get("link", "")
                        published = entry.get("published_parsed")

                        rating = None
                        if "★" in title:
                            stars = title.count("★")
                            half_star = "½" in title
                            rating = stars + (0.5 if half_star else 0)
                            title = title.split("★")[0].strip()

                        year = None
                        year_match = re.search(r',\s*(\d{4})\s*-?\s*$', title)
                        if year_match:
                            year = int(year_match.group(1))
                            title = re.sub(r',\s*\d{4}\s*-?\s*$', '', title)
                        elif "(" in title and ")" in title:
                            year_match = re.search(r'\((\d{4})\)', title)
                            if year_match:
                                year = int(year_match.group(1))
                            title = title.rsplit("(", 1)[0].strip()
                        title = title.strip()

                        image_url = None
                        if hasattr(entry, "content") and entry.content:
                            for content in entry.content:
                                if "img" in content.get("value", "").lower():
                                    img_match = re.search(
                                        r'<img[^>]+src=["\']([^"\']+)["\']',
                                        content.get("value", ""),
                                    )
                                    if img_match:
                                        image_url = img_match.group(1)
                        elif hasattr(entry, "summary"):
                            img_match = re.search(
                                r'<img[^>]+src=["\']([^"\']+)["\']',
                                entry.summary,
                            )
                            if img_match:
                                image_url = img_match.group(1)

                        date_added = None
                        if published:
                            try:
                                date_added = datetime(*published[:6]).isoformat()
                            except (ValueError, TypeError):
                                pass
                        date_added = date_added or entry.get("published", "")

                        movie_data = {
                            ATTR_MOVIE_TITLE: title,
                            ATTR_RATING: rating,
                            ATTR_YEAR: year,
                            ATTR_IMAGE_URL: image_url,
                            ATTR_DATE_ADDED: date_added,
                            ATTR_LINK: link,
                            "unique_id": self._generate_movie_unique_id(title, link, date_added),
                        }
                        rss_movies.append(movie_data)

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching feed %s: %s", self.feed_name, err)
            stored = await self._load_stored()
            movies = stored[: self.max_movies]
            movies_for_devices = stored[: self.max_devices]
            return {
                "movies": movies,
                "movies_for_devices": movies_for_devices,
                "latest_movie": movies[0] if movies else None,
                "feed_url": self.feed_url,
                "last_update": datetime.now().isoformat(),
                "error": str(err),
            }
        except Exception as err:
            _LOGGER.exception("Unexpected error processing feed %s: %s", self.feed_name, err)
            stored = await self._load_stored()
            movies = stored[: self.max_movies]
            movies_for_devices = stored[: self.max_devices]
            return {
                "movies": movies,
                "movies_for_devices": movies_for_devices,
                "latest_movie": movies[0] if movies else None,
                "feed_url": self.feed_url,
                "last_update": datetime.now().isoformat(),
                "error": str(err),
            }

        # Merge RSS into stored history
        stored_list = await self._load_stored()
        seen_links = {m.get(ATTR_LINK) for m in stored_list}
        seen_unique_ids = {m.get("unique_id") for m in stored_list}

        for movie in rss_movies:
            link = movie.get(ATTR_LINK)
            uid = movie.get("unique_id")
            if link not in seen_links and uid not in seen_unique_ids:
                stored_list.append(movie)
                seen_links.add(link)
                seen_unique_ids.add(uid)

        stored_list.sort(key=lambda x: x.get(ATTR_DATE_ADDED, ""), reverse=True)
        stored_list = stored_list[:MAX_STORED_MOVIES]
        await self._save_stored(stored_list)

        movies = stored_list[: self.max_movies]
        movies_for_devices = stored_list[: self.max_devices]
        latest_movie = movies[0] if movies else None

        return {
            "movies": movies,
            "movies_for_devices": movies_for_devices,
            "latest_movie": latest_movie,
            "feed_url": self.feed_url,
            "last_update": datetime.now().isoformat(),
        }

    async def _load_stored(self) -> list[dict[str, Any]]:
        """Load stored movie history for this feed."""
        data = await self._store.async_load()
        if data and isinstance(data.get("movies"), list):
            return data["movies"]
        return []

    async def _save_stored(self, movies: list[dict[str, Any]]) -> None:
        """Save movie history to store."""
        await self._store.async_save({"movies": movies})

    def _generate_movie_unique_id(self, title: str, link: str, date_added: str | None) -> str:
        """Generate a unique ID for a movie within this feed."""
        # Use feed name + movie title + date to ensure uniqueness
        # Even if same movie appears in multiple feeds, they'll have different IDs
        base_id = f"{self.entry_id}_{self.feed_name}_{title}_{date_added or link}"
        # Clean up the ID to be valid for entity IDs
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
