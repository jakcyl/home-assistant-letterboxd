# Letterboxd Home Assistant Custom Component

A Home Assistant custom component that integrates Letterboxd RSS feeds to display your movie watching activity.

## Features

- 📽️ **Multiple Feed Support**: Add one or more Letterboxd RSS feeds
- 🎬 **Individual Movie Entities**: Each movie gets its own sensor entity with full details
- ⭐ **Latest Movie Sensor**: One per feed, automatically tracks the most recent movie
- 🔄 **Per-Feed Update Intervals**: Configure update frequency individually for each feed (1 hour to 1 week)
- 📊 **Dashboard Ready**: Latest movie sensors perfect for dashboard cards
- 🔗 **Proper Separation**: Movies from different feeds are properly separated even if they're the same movie

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
1. Enter the first feed URL, optional name, and update interval (default: 6 hours)
2. Click "Submit"
3. Choose to add another feed
4. Repeat until all feeds are added
5. Finish setup

**Update Interval**: Set how often each feed should be checked (in minutes). Range: 60 minutes (1 hour) to 10080 minutes (1 week). Default: 360 minutes (6 hours).

## Entities

### Latest Movie Sensors (One Per Feed)

For each feed, a latest movie sensor is created:
- **Entity ID**: `sensor.letterboxd_latest_movie_{feed_name}`
- **State**: Title of the most recent movie in that feed
- **Attributes**:
  - `movie_title`: Movie title
  - `rating`: Rating as a number (0-5, can include 0.5 for half stars)
  - `image_url`: Poster image URL
  - `date_added`: Date when the movie was added
  - `link`: Link to the Letterboxd page
  - `feed_name`: Name of the feed this movie came from

### Individual Movie Sensors

Each movie in each feed gets its own sensor entity:
- **Entity ID**: `sensor.letterboxd_movie_{feed_name}_{movie_title}`
- **State**: Movie title
- **Attributes**:
  - `movie_title`: Movie title
  - `rating`: Rating as a number (0-5, can include 0.5 for half stars)
  - `image_url`: Poster image URL
  - `date_added`: Date when the movie was added
  - `link`: Link to the Letterboxd page
  - `feed_name`: Name of the feed this movie came from

**Note**: Movies are properly separated by feed. Even if the same movie appears in multiple feeds, each will have its own entity with a unique ID based on the feed name.

## Dashboard Example

Add a latest movie sensor to your dashboard with a picture-entity card:

```yaml
type: picture-entity
entity: sensor.letterboxd_latest_movie_{feed_name}
image: '{{ state_attr("sensor.letterboxd_latest_movie_{feed_name}", "image_url") }}'
title: '{{ state_attr("sensor.letterboxd_latest_movie_{feed_name}", "movie_title") }}'
tap_action:
  action: url
  url_path: '{{ state_attr("sensor.letterboxd_latest_movie_{feed_name}", "link") }}'
```

Or use a custom card for more detailed information:

```yaml
type: markdown
content: |
  ## {{ state_attr('sensor.letterboxd_latest_movie_{feed_name}', 'movie_title') }}
  
  **Rating:** {{ state_attr('sensor.letterboxd_latest_movie_{feed_name}', 'rating') }} ⭐
  
  **Date Added:** {{ state_attr('sensor.letterboxd_latest_movie_{feed_name}', 'date_added') }}
  
  [View on Letterboxd]({{ state_attr('sensor.letterboxd_latest_movie_{feed_name}', 'link') }})
```

Replace `{feed_name}` with your actual feed name (e.g., `sensor.letterboxd_latest_movie_my_diary`).

You can also use individual movie sensors for more granular control or to display multiple movies.

## Update Frequency

Each feed can have its own update interval, configured during setup:
- **Default**: 360 minutes (6 hours)
- **Range**: 60 minutes (1 hour) to 10080 minutes (1 week)
- **Per Feed**: Each feed updates independently according to its configured interval

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
