# EDM Backend - NYC Event Scraper

A web scraper that extracts today's EDM events from EDMTrain for New York City venues.

## Folder Structure

```
your-project/
├── backend/
│   ├── server.js           ← ✅ Backend API server
│   ├── scraper.py          ← ✅ Python scraper
│   ├── package.json        ← ✅ Node.js dependencies
│   ├── requirements.txt    ← ✅ Python dependencies
│   └── data/
│       └── latest_events.json  ← ✅ Scraped events data
├── frontend/               ← Optional React app
│   ├── App.jsx
│   └── package.json
├── .github/
│   └── workflows/
│       └── daily-scraper.yml   ← ✅ Automated daily scraping
├── .gitignore
└── README.md
```

## Features

- Scrapes EDMTrain NYC page for today's events
- Extracts: Artist, Venue, Event Name, Location, Date, Time, Age restrictions
- REST API endpoints with `/api/` prefix
- Automated daily scraping via GitHub Actions

## Successfully Extracted Events

- **Mamba Mondays: Bruce Wayne** at Good Room (21+)
- **Kiss Kiss: CMD+JAZMINE** at Montauk Yacht Club

## Setup Steps

### Backend Setup (in terminal, inside `/backend` folder):

```bash
cd backend
npm init -y
npm install express cors
node server.js
```

Then visit: 👉 **http://localhost:5000/api/events**

You should see your scraped JSON.

### Install Python Dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Run the Scraper:

```bash
cd backend
python scraper.py
```

## API Endpoints

- `GET /api/events` - Returns today's scraped events
- `POST /api/scrape` - Triggers a new scrape
- `GET /api/health` - Health check

### Example API Response

```json
{
  "success": true,
  "data": [
    {
      "artist": "Bruce Wayne",
      "venue": "Good Room",
      "event_name": "Mamba Mondays",
      "location": "New York, NY",
      "date": "Mon Jul 21, 2025",
      "time": "Check venue",
      "age": "21+",
      "url": "",
      "scraped_at": "2025-07-21T19:21:31.308287",
      "day_of_week": "Monday"
    }
  ],
  "source": "scraped",
  "last_updated": "2025-07-21T19:21:31.308287"
}
```

## Frontend (Optional)

The `/frontend` folder contains a basic React app that displays the events. To use it:

```bash
cd frontend
npm install
npm run dev
```

## Automated Daily Scraping

The GitHub Action runs daily at 6 AM EST to automatically scrape and update the events data.

## Quick Start

1. Clone the repository
2. `cd backend`
3. `npm install`
4. `pip install -r requirements.txt`
5. `python scraper.py` (to get initial data)
6. `node server.js`
7. Visit `http://localhost:5000/api/events`

✅ You should see the scraped events JSON!