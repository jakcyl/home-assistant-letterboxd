"""Helpers for the Letterboxd integration."""
from __future__ import annotations

import re
from typing import Any


def movie_slug(movie: dict[str, Any], max_length: int = 40) -> str:
    """Build a short slug from a movie for use in entity object_id (e.g. hamnet_2025)."""
    title = (movie.get("movie_title") or "unknown").strip().lower()
    title = re.sub(r"[^a-z0-9]+", "_", title).strip("_") or "movie"
    year = movie.get("year")
    if year is not None:
        slug = f"{title}_{year}"
    else:
        slug = title
    return (slug[:max_length] or "movie").lower()


def feed_slug(feed_name: str) -> str:
    """Sanitize feed name for use in entity object_id."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(feed_name).strip()).strip("_") or "feed"
    return slug.lower()[:32]
