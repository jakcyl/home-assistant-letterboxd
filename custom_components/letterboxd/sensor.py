"""Sensor platform for Letterboxd integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DATE_ADDED,
    ATTR_FEED_NAME,
    ATTR_IMAGE_URL,
    ATTR_LINK,
    ATTR_MOVIE_TITLE,
    ATTR_RATING,
    CONF_FEED_NAME,
    DOMAIN,
    SENSOR_LATEST_MOVIE,
    SENSOR_MOVIE_PREFIX,
)
from .coordinator import LetterboxdDataUpdateCoordinator, LetterboxdFeedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Letterboxd sensor entities."""
    coordinator: LetterboxdDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Create entities for each feed
    for feed_name, feed_coordinator in coordinator.feed_coordinators.items():
        # Create latest movie sensor for this feed
        entities.append(
            LetterboxdLatestMovieSensor(
                coordinator=feed_coordinator,
                feed_name=feed_name,
            )
        )

        # Create individual movie sensors for this feed
        # Entities will be created based on current data and update via coordinator
        if feed_coordinator.data and feed_coordinator.data.get("movies"):
            for movie in feed_coordinator.data["movies"]:
                entities.append(
                    LetterboxdMovieSensor(
                        coordinator=feed_coordinator,
                        feed_name=feed_name,
                        movie_data=movie,
                    )
                )

    async_add_entities(entities)


class LetterboxdLatestMovieSensor(CoordinatorEntity, SensorEntity):
    """Representation of the latest movie sensor for a feed."""

    _attr_icon = "mdi:movie-open-star"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._attr_name = f"Letterboxd Latest Movie ({feed_name})"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{SENSOR_LATEST_MOVIE}"

    @property
    def native_value(self) -> str:
        """Return the title of the latest movie."""
        latest_movie = self.coordinator.data.get("latest_movie") if self.coordinator.data else None
        if latest_movie:
            return latest_movie.get(ATTR_MOVIE_TITLE, "Unknown")
        return "No movies"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        latest_movie = self.coordinator.data.get("latest_movie") if self.coordinator.data else None
        if not latest_movie:
            return {}

        return {
            ATTR_MOVIE_TITLE: latest_movie.get(ATTR_MOVIE_TITLE),
            ATTR_RATING: latest_movie.get(ATTR_RATING),
            ATTR_IMAGE_URL: latest_movie.get(ATTR_IMAGE_URL),
            ATTR_DATE_ADDED: latest_movie.get(ATTR_DATE_ADDED),
            ATTR_LINK: latest_movie.get(ATTR_LINK),
            ATTR_FEED_NAME: self._feed_name,
        }


class LetterboxdMovieSensor(CoordinatorEntity, SensorEntity):
    """Representation of an individual movie sensor."""

    _attr_icon = "mdi:movie"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
        movie_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._movie_data = movie_data
        self._movie_title = movie_data.get(ATTR_MOVIE_TITLE, "Unknown")
        self._movie_unique_id = movie_data.get("unique_id", f"{coordinator.entry_id}_{feed_name}_{self._movie_title}")
        self._attr_name = f"Letterboxd Movie ({feed_name}): {self._movie_title}"
        self._attr_unique_id = self._movie_unique_id

    @property
    def native_value(self) -> str:
        """Return the movie title."""
        # Get current movie data from coordinator (in case it was updated)
        movies = self.coordinator.data.get("movies", []) if self.coordinator.data else []
        current_movie = next(
            (m for m in movies if m.get("unique_id") == self._movie_unique_id),
            self._movie_data,
        )
        return current_movie.get(ATTR_MOVIE_TITLE, self._movie_title)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        # Get current movie data from coordinator (in case it was updated)
        movies = self.coordinator.data.get("movies", []) if self.coordinator.data else []
        current_movie = next(
            (m for m in movies if m.get("unique_id") == self._movie_unique_id),
            self._movie_data,
        )

        return {
            ATTR_MOVIE_TITLE: current_movie.get(ATTR_MOVIE_TITLE),
            ATTR_RATING: current_movie.get(ATTR_RATING),
            ATTR_IMAGE_URL: current_movie.get(ATTR_IMAGE_URL),
            ATTR_DATE_ADDED: current_movie.get(ATTR_DATE_ADDED),
            ATTR_LINK: current_movie.get(ATTR_LINK),
            ATTR_FEED_NAME: self._feed_name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Entity is available if the movie still exists in the feed
        if not self.coordinator.data:
            return False
        movies = self.coordinator.data.get("movies", [])
        return any(m.get("unique_id") == self._movie_unique_id for m in movies)
