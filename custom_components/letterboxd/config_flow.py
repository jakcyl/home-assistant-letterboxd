"""Config flow for Letterboxd integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import feedparser
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_EXPOSE_AS_DEVICES,
    CONF_FEEDS,
    CONF_FEED_NAME,
    CONF_FEED_URL,
    CONF_MAX_MOVIES,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_MOVIES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_feed(hass: HomeAssistant, feed_url: str) -> dict[str, Any]:
    """Validate that the feed URL is accessible and returns valid Letterboxd data."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise CannotConnect(f"HTTP {response.status}")
                text = await response.text()

        feed = feedparser.parse(text)
        if not feed.entries:
            raise InvalidFeed("Feed appears to be empty or invalid")

        # Check if it looks like a Letterboxd feed
        if not any("letterboxd.com" in entry.get("link", "") for entry in feed.entries[:3]):
            raise InvalidFeed("Feed does not appear to be a valid Letterboxd feed")

        return {"title": feed.feed.get("title", "Letterboxd Feed"), "valid": True}

    except aiohttp.ClientError as err:
        raise CannotConnect(f"Error connecting to feed: {err}") from err
    except Exception as err:
        raise InvalidFeed(f"Error parsing feed: {err}") from err


class LetterboxdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Letterboxd."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.feeds: list[dict[str, str]] = []
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            feed_url = user_input.get(CONF_FEED_URL, "").strip()
            feed_name = user_input.get(CONF_FEED_NAME, "").strip()

            if not feed_url:
                errors[CONF_FEED_URL] = "feed_url_required"
            elif feed_url in [feed.get(CONF_FEED_URL) for feed in self.feeds]:
                errors[CONF_FEED_URL] = "feed_already_added"
            else:
                try:
                    feed_info = await validate_feed(self.hass, feed_url)
                    if not feed_name:
                        # Use the feed title from validation or extract from URL
                        feed_name = feed_info.get("title", feed_url.split("/")[-2] if "/" in feed_url else "Letterboxd Feed")

                    scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    max_movies = user_input.get(CONF_MAX_MOVIES, DEFAULT_MAX_MOVIES)
                    expose_as_devices = user_input.get(CONF_EXPOSE_AS_DEVICES, False)
                    self.feeds.append({
                        CONF_FEED_URL: feed_url,
                        CONF_FEED_NAME: feed_name,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_MAX_MOVIES: max_movies,
                        CONF_EXPOSE_AS_DEVICES: expose_as_devices,
                    })
                    return await self.async_step_add_another()

                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidFeed:
                    errors["base"] = "invalid_feed"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FEED_URL): str,
                    vol.Optional(CONF_FEED_NAME): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): vol.All(vol.Coerce(int), vol.Range(min=60, max=10080)),  # 1 hour to 1 week
                    vol.Optional(
                        CONF_MAX_MOVIES,
                        default=DEFAULT_MAX_MOVIES,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                    vol.Optional(CONF_EXPOSE_AS_DEVICES, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_add_another(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask user if they want to add another feed."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_another",
                data_schema=vol.Schema(
                    {
                        vol.Required("add_another", default=False): bool,
                    }
                ),
            )

        if user_input.get("add_another"):
            return await self.async_step_user()

        # Finalize configuration
        self.data[CONF_FEEDS] = self.feeds

        return self.async_create_entry(
            title=f"Letterboxd ({len(self.feeds)} feed{'s' if len(self.feeds) > 1 else ''})",
            data=self.data,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidFeed(HomeAssistantError):
    """Error to indicate the feed is invalid."""
