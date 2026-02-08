"""Sensor platform for Letterboxd integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DATE_ADDED,
    ATTR_FEED_NAME,
    ATTR_IMAGE_URL,
    ATTR_LINK,
    ATTR_MOVIE_TITLE,
    ATTR_MOVIES,
    ATTR_RATING,
    ATTR_YEAR,
    CONF_EXPOSE_AS_DEVICES,
    CONF_FEED_NAME,
    DOMAIN,
    SENSOR_LATEST_MOVIE,
    SENSOR_RECENT_MOVIES,
)
from .coordinator import LetterboxdDataUpdateCoordinator, LetterboxdFeedCoordinator
from .helpers import feed_slug, movie_slug


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Letterboxd sensor entities."""
    coordinator: LetterboxdDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for feed_name, feed_coordinator in coordinator.feed_coordinators.items():
        feed_config = feed_coordinator.feed_config
        expose_as_devices = feed_config.get(CONF_EXPOSE_AS_DEVICES, False)

        entities.append(
            LetterboxdLatestMovieSensor(
                coordinator=feed_coordinator,
                feed_name=feed_name,
            )
        )
        entities.append(
            LetterboxdRecentMoviesSensor(
                coordinator=feed_coordinator,
                feed_name=feed_name,
            )
        )

        device_movies = (feed_coordinator.data or {}).get("movies_for_devices") or (feed_coordinator.data or {}).get("movies") or []
        if expose_as_devices and device_movies:
            for movie in device_movies:
                movie_uid = movie.get("unique_id", "")
                device_info = DeviceInfo(
                    identifiers={(DOMAIN, movie_uid)},
                    name=_device_name(movie),
                    entry_type=None,
                )
                entities.append(
                    LetterboxdMovieTitleSensor(
                        coordinator=feed_coordinator,
                        feed_name=feed_name,
                        movie=movie,
                        device_info=device_info,
                    )
                )
                entities.append(
                    LetterboxdMovieRatingSensor(
                        coordinator=feed_coordinator,
                        feed_name=feed_name,
                        movie=movie,
                        device_info=device_info,
                    )
                )
                entities.append(
                    LetterboxdMovieYearSensor(
                        coordinator=feed_coordinator,
                        feed_name=feed_name,
                        movie=movie,
                        device_info=device_info,
                    )
                )
                entities.append(
                    LetterboxdMovieDateAddedSensor(
                        coordinator=feed_coordinator,
                        feed_name=feed_name,
                        movie=movie,
                        device_info=device_info,
                    )
                )

    async_add_entities(entities)


def _device_name(movie: dict[str, Any]) -> str:
    """Build device name from movie (title and year if present)."""
    title = movie.get("movie_title") or "Unknown"
    year = movie.get("year")
    if year:
        return f"{title} ({year})"
    return f"Letterboxd - {title}"


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
            ATTR_YEAR: latest_movie.get(ATTR_YEAR),
            ATTR_IMAGE_URL: latest_movie.get(ATTR_IMAGE_URL),
            ATTR_DATE_ADDED: latest_movie.get(ATTR_DATE_ADDED),
            ATTR_LINK: latest_movie.get(ATTR_LINK),
            ATTR_FEED_NAME: self._feed_name,
        }


class LetterboxdRecentMoviesSensor(CoordinatorEntity, SensorEntity):
    """Sensor with list of last X movies for dashboard/cards."""

    _attr_icon = "mdi:movie-multiple"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._attr_name = f"Letterboxd Recent Movies ({feed_name})"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{SENSOR_RECENT_MOVIES}"

    @property
    def native_value(self) -> int:
        """Return the count of recent movies."""
        movies = self.coordinator.data.get("movies", []) if self.coordinator.data else []
        return len(movies)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of recent movies for templates/cards."""
        movies = self.coordinator.data.get("movies", []) if self.coordinator.data else []
        list_attrs = []
        for m in movies:
            list_attrs.append({
                ATTR_MOVIE_TITLE: m.get(ATTR_MOVIE_TITLE),
                ATTR_YEAR: m.get(ATTR_YEAR),
                ATTR_RATING: m.get(ATTR_RATING),
                ATTR_IMAGE_URL: m.get(ATTR_IMAGE_URL),
                ATTR_DATE_ADDED: m.get(ATTR_DATE_ADDED),
                ATTR_LINK: m.get(ATTR_LINK),
                ATTR_FEED_NAME: self._feed_name,
            })
        return {ATTR_MOVIES: list_attrs}


def _current_movie(
    coordinator: LetterboxdFeedCoordinator,
    movie_unique_id: str,
    fallback: dict[str, Any],
) -> dict[str, Any]:
    """Get current movie data from coordinator or fallback."""
    if not coordinator.data:
        return fallback
    movies = coordinator.data.get("movies", [])
    return next(
        (m for m in movies if m.get("unique_id") == movie_unique_id),
        fallback,
    )


class LetterboxdMovieTitleSensor(CoordinatorEntity, SensorEntity):
    """Title sensor for a movie device."""

    _attr_icon = "mdi:movie"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
        movie: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._movie = movie
        self._movie_uid = movie.get("unique_id", "")
        self._attr_device_info = device_info
        self._attr_name = f"Letterboxd {feed_slug(feed_name)} Title"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{self._movie_uid}_title"
        self._attr_suggested_object_id = f"letterboxd_{feed_slug(feed_name)}_{movie_slug(movie)}_title"

    @property
    def native_value(self) -> str:
        m = _current_movie(self.coordinator, self._movie_uid, self._movie)
        return m.get(ATTR_MOVIE_TITLE) or "Unknown"


class LetterboxdMovieRatingSensor(CoordinatorEntity, SensorEntity):
    """Rating sensor for a movie device."""

    _attr_icon = "mdi:star"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
        movie: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._movie = movie
        self._movie_uid = movie.get("unique_id", "")
        self._attr_device_info = device_info
        self._attr_name = f"Letterboxd {feed_slug(feed_name)} Rating"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{self._movie_uid}_rating"
        self._attr_suggested_object_id = f"letterboxd_{feed_slug(feed_name)}_{movie_slug(movie)}_rating"

    @property
    def native_value(self) -> float | None:
        m = _current_movie(self.coordinator, self._movie_uid, self._movie)
        return m.get(ATTR_RATING)


class LetterboxdMovieYearSensor(CoordinatorEntity, SensorEntity):
    """Year sensor for a movie device."""

    _attr_icon = "mdi:calendar"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
        movie: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._movie = movie
        self._movie_uid = movie.get("unique_id", "")
        self._attr_device_info = device_info
        self._attr_name = f"Letterboxd {feed_slug(feed_name)} Year"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{self._movie_uid}_year"
        self._attr_suggested_object_id = f"letterboxd_{feed_slug(feed_name)}_{movie_slug(movie)}_year"

    @property
    def native_value(self) -> int | None:
        m = _current_movie(self.coordinator, self._movie_uid, self._movie)
        return m.get(ATTR_YEAR)


class LetterboxdMovieDateAddedSensor(CoordinatorEntity, SensorEntity):
    """Date added sensor for a movie device."""

    _attr_icon = "mdi:calendar-plus"

    def __init__(
        self,
        coordinator: LetterboxdFeedCoordinator,
        feed_name: str,
        movie: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._feed_name = feed_name
        self._movie = movie
        self._movie_uid = movie.get("unique_id", "")
        self._attr_device_info = device_info
        self._attr_name = f"Letterboxd {feed_slug(feed_name)} Date added"
        self._attr_unique_id = f"{coordinator.entry_id}_{feed_name}_{self._movie_uid}_date_added"
        self._attr_suggested_object_id = f"letterboxd_{feed_slug(feed_name)}_{movie_slug(movie)}_date_added"

    @property
    def native_value(self) -> str | None:
        m = _current_movie(self.coordinator, self._movie_uid, self._movie)
        return m.get(ATTR_DATE_ADDED)
