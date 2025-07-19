# Beatmap - EDM Events Scraper

Automated web scraper for electronic music events in New York City from EDM Train.

## 🎵 Features

- **Daily Automated Scraping**: GitHub Action runs daily at 6 AM EST
- **Day-Specific Data**: Creates separate JSON files for each day (monday_events.json, tuesday_events.json, etc.)
- **Real Event Data**: Extracts artist names, venues, dates, times, and prices
- **No Generated Data**: Only real events from EDM Train website
- **Comprehensive Event Info**: Venue locations, cities, pricing, and event URLs

## 📁 File Structure

```
data/
├── monday_events.json      # Monday's events
├── tuesday_events.json     # Tuesday's events  
├── wednesday_events.json   # Wednesday's events
├── thursday_events.json    # Thursday's events
├── friday_events.json      # Friday's events
├── saturday_events.json    # Saturday's events
├── sunday_events.json      # Sunday's events
└── latest_events.json      # Most recent day's events with metadata
```

## 🤖 Automated Daily Updates

The GitHub Action automatically:
1. Runs every day at 6 AM UTC (2 AM EST)
2. Scrapes EDM Train for the current day's events
3. Saves data to day-specific JSON files
4. Commits and pushes updates to the repository

## 🚀 Manual Usage

### Extract HTML
```bash
python3 edmtrain_html_extractor.py
```

### Parse Events (This Week)
```bash
python3 parse_edmtrain_events.py
```

### Daily Events (Current Day Only)
```bash
python3 daily_events_scraper.py
```

## 📊 Event Data Format

Each event includes:
```json
{
  "artist": "Artist Name",
  "venue": "Venue Name",
  "venue_location": "Venue - City, State",
  "city": "Brooklyn",
  "state": "NY",
  "date": "Friday, July 18, 2025",
  "time": "10:00 PM",
  "price": "$45",
  "event_url": "https://edmtrain.com/events/artist-name",
  "scraped_at": "2025-07-18T15:20:22.542Z",
  "day_of_week": "Friday"
}
```

## 🛠️ Dependencies

- Python 3.11+
- selenium
- beautifulsoup4
- lxml

## 📅 GitHub Action Schedule

- **Frequency**: Daily
- **Time**: 6:00 AM EST
- **Trigger**: Automatic via cron schedule
- **Manual**: Can be triggered manually from GitHub Actions tab

## 🏙️ NYC Venues Covered

Major venues include:
- Brooklyn Mirage
- Avant Gardner  
- Terminal 5
- Elsewhere
- Webster Hall
- House of Yes
- Knockdown Center
- And many more...

## 📈 Data Updates

Check the `data/` folder for the latest event information. Files are updated daily with fresh event data from EDM Train.
