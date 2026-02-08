"""Image platform for Letterboxd integration (movie poster per device)."""
from __future__ import annotations

import collections
from datetime import datetime
from typing import Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_IMAGE_URL,
    CONF_EXPOSE_AS_DEVICES,
    DOMAIN,
)
from .coordinator import LetterboxdDataUpdateCoordinator, LetterboxdFeedCoordinator
from .helpers import feed_slug, movie_slug


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Letterboxd image entities (poster per movie device)."""
    coordinator: LetterboxdDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ImageEntity] = []

    for feed_name, feed_coordinator in coordinator.feed_coordinators.items():
        feed_config = feed_coordinator.feed_config
        if not feed_config.get(CONF_EXPOSE_AS_DEVICES, False):
            continue
        device_movies = (feed_coordinator.data or {}).get("movies_for_devices") or (feed_coordinator.data or {}).get("movies") or []
        if not device_movies:
            continue

        for movie in device_movies:
            movie_uid = movie.get("unique_id", "")
            device_info = DeviceInfo(
                identifiers={(DOMAIN, movie_uid)},
                name=_device_name(movie),
                entry_type=None,
            )
            entities.append(
                LetterboxdMoviePosterImage(
                    coordinator=feed_coordinator,
                    feed_name=feed_name,
                    movie=movie,
                    device_info=device_info,
                )
            )

    async_add_entities(entities)


def _device_name(movie: dict[str, Any]) -> str:
    title = movie.get("movie_title") or "Unknown"
    year = movie.get("year")
    if year:
        return f"{title} ({year})"
    return f"Letterboxd - {title}"


class LetterboxdMoviePosterImage(CoordinatorEntity, ImageEntity):
    """Poster image entity for a movie device."""

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
        movie: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(coordinator)
        # ImageEntity requires _client and access_tokens for state_attributes and async_image.
        # Set them explicitly so we never hit AttributeError if ImageEntity.__init__ order differs.
        hass = coordinator.hass
        self._client = get_async_client(hass, verify_ssl=False)
        self.access_tokens = collections.deque([], 2)
        self.async_update_token()
        try:
            ImageEntity.__init__(self, hass, verify_ssl=False)
        except Exception:
            pass
        self._feed_name = feed_name
        self._movie = movie
        self._movie_uid = movie.get("unique_id", "")
        self._attr_device_info = device_info
        self._attr_name = f"Letterboxd {feed_slug(feed_name)} Poster"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{self._movie_uid}_poster"
        self._attr_suggested_object_id = f"letterboxd_{feed_slug(feed_name)}_{movie_slug(self._movie)}_poster"
        self._attr_image_last_updated = datetime.now()

    @property
    def image_url(self) -> str | None:
        """Return the URL of the poster image, or a placeholder so the entity stays valid."""
        movies = self.coordinator.data.get("movies", []) if self.coordinator.data else []
        current = next(
            (m for m in movies if m.get("unique_id") == self._movie_uid),
            self._movie,
        )
        url = current.get(ATTR_IMAGE_URL)
        if url and isinstance(url, str) and url.strip():
            return url.strip()
        # Placeholder so the entity has a valid URL and does not show as unavailable
        return "https://placehold.co/300x450/png?text=No+poster"

    @property
    def available(self) -> bool:
        """Return True when coordinator has succeeded and we have movie data."""
        if not self.coordinator.last_update_success:
            return False
        return bool(self._movie and self._movie.get("unique_id"))

    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update: bump image_last_updated so frontend refetches."""
        self._attr_image_last_updated = datetime.now()
        super()._handle_coordinator_update()
