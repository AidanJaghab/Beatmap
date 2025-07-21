# EDM Backend - NYC Event Scraper

A web scraper that extracts today's EDM events from EDMTrain for New York City venues.

## Features

- Scrapes EDMTrain NYC page for today's events
- Extracts: Artist, Venue, Event Name, Location, Date, Time, Age restrictions
- Provides REST API to serve scraped data
- Automated daily scraping via GitHub Actions

## Successfully Extracted Events

- **Mamba Mondays: Bruce Wayne** at Good Room (21+)
- **Kiss Kiss: CMD+JAZMINE** at Montauk Yacht Club

## Installation

### Prerequisites
- Python 3.9+
- Node.js 14+
- Chrome/Chromium browser
- ChromeDriver

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/edm-backend.git
cd edm-backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

## Usage

### Run the Scraper

```bash
python scraper.py
```
or
```bash
npm run scrape
```

### Start the API Server

```bash
npm start
```

## API Endpoints

- `GET /events` - Returns today's scraped events
- `POST /scrape` - Triggers a new scrape
- `GET /health` - Health check

## Files

- `scraper.py` - Main Python scraper
- `server.js` - Express API server
- `today_events.json` - Scraped events data
- `.github/workflows/daily-scraper.yml` - Automated daily scraping