# Letterboxd Home Assistant Custom Component

A Home Assistant custom component that integrates Letterboxd RSS feeds to display your movie watching activity.
<img width="485" height="359" alt="image" src="https://github.com/user-attachments/assets/b9f0430c-b718-44c0-972c-ffadad904429" />
## Features

- 📽️ **Multiple Feed Support**: Add one or more Letterboxd RSS feeds
- 📚 **Persistent Movie History**: Each RSS scan merges new movies into a stored history per feed (kept across restarts)
- 📊 **Last X Movies**: Choose how many recent movies to show (1–50, default 5) for efficient, dynamic dashboards
- ⭐ **Latest Movie Sensor**: One per feed; plus a **Recent Movies** sensor with a `movies` list attribute for cards
- 🎬 **Optional Movie Devices**: Expose the last N movies as HA devices (N configurable), each with image (poster), title, rating, year, and date added entities; entity IDs are prefixed with `letterboxd_`
- 🔄 **Per-Feed Update Intervals**: Configure refresh interval per feed (1 hour to 1 week)
- 🔗 **Proper Separation**: Movies from different feeds are properly separated

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu (⋮) in the top right corner
4. Select "Custom repositories"
5. In the "Repository" field, enter: `https://github.com/jakcyl/home-assistant-letterboxd`
6. In the "Category" dropdown, select "Integration"
7. Click "Add"
8. Close the dialog and search for "Letterboxd" in HACS
9. Click on "Letterboxd" and then click "Download"
10. Restart Home Assistant
11. Go to Settings → Devices & Services → Add Integration and search for "Letterboxd"

### Manual Installation

1. Copy the `custom_components/letterboxd` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Letterboxd"

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Letterboxd**
4. Enter your Letterboxd RSS feed URL(s)

### Finding Your Letterboxd RSS Feed URL

Your Letterboxd RSS feed URL follows this format:
```
https://letterboxd.com/{username}/rss/
```

This is your **Activity** feed, which shows your movie watching activity (films you've watched and rated).

For example:
- `https://letterboxd.com/john/rss/`
- `https://letterboxd.com/movielover/rss/`

### Adding Multiple Feeds

During setup, you can add multiple feeds:
1. Enter the first feed URL, optional name, update interval (default: 6 hours), **number of recent movies to show** (1–50, default 5), **max movies to expose as devices** (1–50, used when exposing as devices), and optionally **Expose movies as devices**
2. Click "Submit"
3. Choose to add another feed
4. Repeat until all feeds are added
5. Finish setup

**Update Interval**: How often each feed is checked (minutes). Range: 60 (1 hour) to 10080 (1 week). Default: 360 (6 hours).

**Number of recent movies to show**: The last X movies from your stored history are used for the Recent Movies sensor and (if enabled) for movie devices. Default: 5.

**Expose movies as devices**: When enabled, each of the last N movies is created as a Home Assistant device with entities: poster image, title, rating, year, date added. **Max movies to expose as devices**: How many of your most recent movies get a device (1–50). Can be higher than "Number of recent movies to show" (e.g. show 5 in the list but create devices for the last 25). Older entries in your history are not exposed as devices.

## Entities

### Latest Movie Sensor (One Per Feed)

- **Entity ID**: `sensor.letterboxd_latest_movie_{feed_name}`
- **State**: Title of the most recent movie
- **Attributes**: `movie_title`, `year`, `rating`, `image_url`, `date_added`, `link`, `feed_name`

### Recent Movies Sensor (One Per Feed)

- **Entity ID**: `sensor.letterboxd_recent_movies_{feed_name}`
- **State**: Count of recent movies (the number you configured as "last X")
- **Attribute `movies`**: List of the last X movies (newest first). Each item has: `movie_title`, `year`, `rating`, `image_url`, `date_added`, `link`, `feed_name`. Use this in markdown or template cards to display the list dynamically without typing movie names.

### Movie Devices (Optional)

If **Expose movies as devices** is enabled for a feed, each of the last N movies (N = "Max movies to expose as devices") appears as a **device** in Home Assistant with these entities:

- **Image**: Poster (image entity) — entity IDs like `image.letterboxd_poster`, `image.letterboxd_poster_2`, …
- **Sensor (title)**: Movie title — `sensor.letterboxd_title`, `sensor.letterboxd_title_2`, …
- **Sensor (rating)**: Rating (number) — `sensor.letterboxd_rating`, …
- **Sensor (year)**: Release year — `sensor.letterboxd_year`, …
- **Sensor (date added)**: Date when the movie was added — `sensor.letterboxd_date_added`, …

All device entity IDs are prefixed with `letterboxd_` so they are easy to find and do not clash with generic names. Only the **most recently watched** N movies get a device; older history is not exposed as devices. Movies are separated by feed; the same movie in two feeds appears as two devices.

## Dashboard Examples

**Latest movie** (single movie, one feed):

```yaml
type: markdown
content: >
  {% set e = 'sensor.letterboxd_latest_movie_{feed_name}' %}
  ### {{ state_attr(e, 'movie_title') }} ({{ state_attr(e, 'year') }}) ⭐{{ state_attr(e, 'rating') }}
  <div style="text-align: center;"><a href="{{ state_attr(e, 'link') }}" target="_blank"><img src="{{ state_attr(e, 'image_url') }}" style="border-radius: 8px;"></a></div>
```

**Last X movies** (dynamic list from Recent Movies sensor; replace `fabri` with your feed name):

```yaml
type: markdown
content: >
  {% set movies = state_attr('sensor.letterboxd_recent_movies_{feed_name}', 'movies') or [] %}
  {% for m in movies %}
  - **{{ m.movie_title }}** ({{ m.year }}) ⭐{{ m.rating }}
  {% endfor %}
```

If you enabled **Expose movies as devices**, you can use the image and sensor entities of each movie device on your dashboard (e.g. picture-entity cards per device).

## Update Frequency

Each feed can have its own update interval, configured during setup:
- **Default**: 360 minutes (6 hours)
- **Range**: 60 minutes (1 hour) to 10080 minutes (1 week)
- **Per Feed**: Each feed updates independently according to its configured interval

## Notes

- **Re-adding the integration**: If you remove and re-add the Letterboxd integration, a new config entry is created. Stored movie history is tied to the previous entry, so you will start with a fresh history (only movies from the next RSS fetches will be stored). To keep history, reconfigure the existing integration instead of removing it.

## Troubleshooting

### Feed Not Updating

- Check that your RSS feed URL is correct and accessible
- Verify the feed URL works in a browser
- Check Home Assistant logs for errors

### No Movies Showing

- Ensure your Letterboxd account has activity
- Verify the RSS feed URL is correct
- Check that the feed format matches Letterboxd's RSS structure

### Rating Not Showing

Ratings are extracted from the movie title in the RSS feed. If ratings don't appear, the feed format may have changed.

## Support

For issues, feature requests, or contributions, please visit the [GitHub repository](https://github.com/jakcyl/home-assistant-letterboxd).

## License

This project is licensed under the MIT License.
