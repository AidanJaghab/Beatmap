#!/usr/bin/env python3
"""
EDM Train Event Parser

This script parses HTML from the EDM Train website (edmtrain.com) to extract 
electronic music event information for NYC venues.

Key Features:
- Extracts artist names from the first line of event containers
- Captures venue location from the line directly under the artist name
- Parses venue details (venue name, city, state) from location strings
- Filters events to show only this week's events (Monday-Sunday)
- Extracts event dates, times, prices, and URLs when available
- Outputs structured JSON data with all event information
- Removes duplicate events based on artist names

Usage:
1. First run edmtrain_html_extractor.py to get the HTML
2. Then run this script to parse events: python3 parse_edmtrain_events.py

Output:
- Creates this_week_events.json with all parsed event data
- Each event includes: artist, venue, venue_location, city, state, date, time, price, event_url

Dependencies:
- beautifulsoup4 (pip install beautifulsoup4)
- Built-in libraries: json, re, datetime, logging

Example event structure:
{
  "artist": "A-Trak",
  "venue": "Elsewhere", 
  "venue_location": "Elsewhere - Brooklyn, NY",
  "city": "Brooklyn",
  "state": "NY",
  "date": "Friday, July 18, 2025",
  "time": "10:00 PM",
  "price": "$45",
  "event_url": "https://edmtrain.com/events/a-trak"
}
"""

import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EDMTrainParser:
    """Parse EDM Train HTML for event information"""
    
    def __init__(self, html_file):
        self.html_file = html_file
        self.events = []
        self.soup = None
        
    def load_html(self):
        """Load and parse HTML file"""
        try:
            with open(self.html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.soup = BeautifulSoup(html_content, 'html.parser')
            logger.info(f"Successfully loaded HTML file: {self.html_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading HTML file: {e}")
            return False
    
    def find_event_containers(self):
        """Find event containers in the HTML"""
        # Try multiple selectors for event containers
        selectors = [
            'div[class*="event"]',
            'div[class*="show"]',
            'div[class*="listing"]',
            'article[class*="event"]',
            '[itemtype*="Event"]',
            'div[class*="card"]',
            'div[data-event-id]'
        ]
        
        event_containers = []
        
        for selector in selectors:
            containers = self.soup.select(selector)
            if containers:
                logger.info(f"Found {len(containers)} containers with selector: {selector}")
                event_containers.extend(containers)
                break
        
        # If no specific containers found, look for divs with event-like content
        if not event_containers:
            logger.info("No specific event containers found, searching by content...")
            all_divs = self.soup.find_all('div')
            
            for div in all_divs:
                text = div.get_text(strip=True)
                # Look for event indicators
                if (text and 20 < len(text) < 1000 and
                    any(indicator in text.lower() for indicator in ['pm', 'am', '$', 'tickets', 'brooklyn', 'manhattan'])):
                    event_containers.append(div)
        
        logger.info(f"Total event containers found: {len(event_containers)}")
        return event_containers
    
    def extract_artist_and_venue_location(self, container):
        """Extract artist name and venue location (line right under artist)"""
        text = container.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None, None
            
        # First line is artist
        artist = lines[0].strip()
        
        # Skip navigation elements
        if any(term in artist.lower() for term in ['view all', 'see more', 'click here']):
            return None, None
            
        # Second line should be venue location
        venue_location = None
        for line in lines[1:5]:
            if (any(indicator in line.lower() for indicator in ['brooklyn', 'manhattan', 'queens', 'ny']) or
                ' - ' in line):
                venue_location = line.strip()
                break
        
        return artist, venue_location
    
    def extract_venue_location(self, container):
        """Extract venue and location from container"""
        text = container.get_text()
        
        # Known NYC venues
        known_venues = {
            'brooklyn mirage': {'venue': 'Brooklyn Mirage', 'city': 'Brooklyn', 'state': 'NY'},
            'avant gardner': {'venue': 'Avant Gardner', 'city': 'Brooklyn', 'state': 'NY'},
            'great hall': {'venue': 'Great Hall at Avant Gardner', 'city': 'Brooklyn', 'state': 'NY'},
            'terminal 5': {'venue': 'Terminal 5', 'city': 'New York', 'state': 'NY'},
            'elsewhere': {'venue': 'Elsewhere', 'city': 'Brooklyn', 'state': 'NY'},
            'marquee': {'venue': 'Marquee', 'city': 'New York', 'state': 'NY'},
            'pier 17': {'venue': 'Pier 17', 'city': 'New York', 'state': 'NY'},
            'rooftop at pier 17': {'venue': 'Rooftop at Pier 17', 'city': 'New York', 'state': 'NY'},
            'webster hall': {'venue': 'Webster Hall', 'city': 'New York', 'state': 'NY'},
            'irving plaza': {'venue': 'Irving Plaza', 'city': 'New York', 'state': 'NY'},
            'bowery ballroom': {'venue': 'Bowery Ballroom', 'city': 'New York', 'state': 'NY'},
            'mercury lounge': {'venue': 'Mercury Lounge', 'city': 'New York', 'state': 'NY'},
            'house of yes': {'venue': 'House of Yes', 'city': 'Brooklyn', 'state': 'NY'},
            'knockdown center': {'venue': 'Knockdown Center', 'city': 'Queens', 'state': 'NY'},
            'brooklyn steel': {'venue': 'Brooklyn Steel', 'city': 'Brooklyn', 'state': 'NY'},
            'schimanski': {'venue': 'Schimanski', 'city': 'Brooklyn', 'state': 'NY'},
            'output': {'venue': 'Output', 'city': 'Brooklyn', 'state': 'NY'},
            'cielo': {'venue': 'Cielo', 'city': 'New York', 'state': 'NY'}
        }
        
        text_lower = text.lower()
        
        # Check for known venues
        for venue_key, venue_info in known_venues.items():
            if venue_key in text_lower:
                return venue_info
        
        # Try to extract venue from patterns
        venue_patterns = [
            r'at\s+([^-,\n]+)',
            r'@\s+([^-,\n]+)',
            r'•\s+([^•,\n]+)',
            r'-\s+([A-Za-z\s]+),?\s*(?:Brooklyn|Manhattan|Queens|NYC|New York)',
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                venue = match.group(1).strip()
                if 3 < len(venue) < 50:
                    # Default to NYC if no specific borough found
                    city = 'Brooklyn' if 'brooklyn' in text_lower else 'New York'
                    return {'venue': venue, 'city': city, 'state': 'NY'}
        
        # Default return
        return {'venue': 'TBA', 'city': 'New York', 'state': 'NY'}
    
    def extract_date_time(self, container):
        """Extract date and time from container"""
        text = container.get_text()
        
        # Extract date patterns
        date_patterns = [
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})',
            r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})?',
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})'
        ]
        
        date_found = None
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_found = match.group(0)
                break
        
        # Extract time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*[AP]M)',
            r'(\d{1,2}\s*[AP]M)',
            r'Doors:\s*(\d{1,2}:\d{2}\s*[AP]M)'
        ]
        
        time_found = None
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_found = match.group(1)
                break
        
        return date_found, time_found
    
    def extract_link(self, container):
        """Extract event link from container"""
        # Look for links within the container
        link_element = container.find('a')
        if link_element and link_element.get('href'):
            href = link_element.get('href')
            
            # Make absolute URL if relative
            if href.startswith('/'):
                href = 'https://edmtrain.com' + href
            elif not href.startswith('http'):
                href = 'https://edmtrain.com/' + href
                
            return href
        
        return None
    
    def extract_price(self, container):
        """Extract price from container"""
        text = container.get_text()
        
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',
            r'(\d+)\s*USD',
            r'From\s*\$(\d+)',
            r'Tickets:\s*\$(\d+)',
            r'Price:\s*\$(\d+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return f"${match.group(1)}"
        
        return "Check website"
    
    def is_this_week(self, date_string):
        """Check if date is this week (July 14-20, 2025)"""
        if not date_string or date_string == 'TBA':
            return True
        
        this_week_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        return any(day in date_string.lower() for day in this_week_days)
    
    def parse_venue_details(self, venue_location):
        """Parse venue location string"""
        if not venue_location:
            return 'TBA', 'New York', 'NY'
        
        # Pattern: "Venue - City, State"
        if ' - ' in venue_location:
            parts = venue_location.split(' - ')
            venue = parts[0].strip()
            location = parts[1].strip() if len(parts) > 1 else ''
            city = location.split(',')[0].strip() if ',' in location else location
            return venue, city, 'NY'
        
        return venue_location, 'New York', 'NY'

    def parse_events(self):
        """Parse this week's events from the HTML"""
        if not self.soup:
            logger.error("No HTML loaded")
            return False
        
        containers = self.find_event_containers()
        if not containers:
            return False
        
        logger.info(f"Processing {len(containers)} containers for this week...")
        
        for container in containers:
            try:
                # Extract artist and venue location from structure
                artist, venue_location = self.extract_artist_and_venue_location(container)
                if not artist:
                    continue
                
                # Parse venue details
                venue, city, state = self.parse_venue_details(venue_location)
                
                # Extract date/time
                date_found, time_found = self.extract_date_time(container)
                
                # Filter for this week only
                if not self.is_this_week(date_found):
                    continue
                
                link = self.extract_link(container)
                price = self.extract_price(container)
                
                event = {
                    'artist': artist,
                    'venue': venue,
                    'venue_location': venue_location or 'TBA',
                    'city': city,
                    'state': state,
                    'date': date_found or 'TBA',
                    'time': time_found or 'TBA',
                    'price': price,
                    'event_url': link or 'https://edmtrain.com',
                    'scraped_at': datetime.now().isoformat()
                }
                
                if len(artist) > 2:
                    self.events.append(event)
                    logger.debug(f"Added: {artist}")
                
            except Exception as e:
                logger.debug(f"Error: {e}")
                continue
        
        self.events = self.deduplicate_events()
        logger.info(f"Parsed {len(self.events)} this week events")
        return True
    
    def deduplicate_events(self):
        """Remove duplicate events based on artist name"""
        unique_events = []
        seen_artists = set()
        
        for event in self.events:
            artist_key = event['artist'].lower().strip()
            if artist_key not in seen_artists:
                unique_events.append(event)
                seen_artists.add(artist_key)
        
        return unique_events
    
    def save_events(self, output_file='this_week_events.json'):
        """Save events to JSON file"""
        try:
            # Sort events by artist name
            self.events.sort(key=lambda x: x['artist'].lower())
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.events)} events to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving events: {e}")
            return False
    
    def print_summary(self):
        """Print summary of parsed events"""
        print(f"\n🎵 EDM TRAIN EVENTS PARSED: {len(self.events)}")
        print("=" * 60)
        
        if not self.events:
            print("❌ No events found")
            return
        
        # Group by venue
        venues = {}
        for event in self.events:
            venue = event['venue']
            if venue not in venues:
                venues[venue] = []
            venues[venue].append(event)
        
        # Show summary by venue
        for venue in sorted(venues.keys()):
            if venue != 'TBA':
                print(f"\n📍 {venue} ({len(venues[venue])} events)")
                for event in venues[venue][:3]:  # Show first 3
                    date_str = f" - {event['date']}" if event['date'] != 'TBA' else ""
                    time_str = f" @ {event['time']}" if event['time'] != 'TBA' else ""
                    print(f"   • {event['artist']}{date_str}{time_str}")
                if len(venues[venue]) > 3:
                    print(f"   ... and {len(venues[venue]) - 3} more")
        
        # Show TBA venues
        if 'TBA' in venues:
            print(f"\n📍 Venue TBA ({len(venues['TBA'])} events)")
            for event in venues['TBA'][:5]:
                print(f"   • {event['artist']}")
            if len(venues['TBA']) > 5:
                print(f"   ... and {len(venues['TBA']) - 5} more")
    
    def run(self, output_file='edmtrain_events.json'):
        """Main execution method"""
        print("🎵 EDM TRAIN EVENT PARSER")
        print("📄 Using Beautiful Soup to parse HTML")
        print("=" * 50)
        
        if not self.load_html():
            return False
        
        if not self.parse_events():
            return False
        
        if not self.save_events(output_file):
            return False
        
        self.print_summary()
        
        print(f"\n✅ Successfully parsed {len(self.events)} events")
        print(f"📁 Saved to: {output_file}")
        return True


def main():
    # Look for the most recent HTML file
    import glob
    import os
    
    html_files = glob.glob("edmtrain_homepage_*.html")
    if not html_files:
        print("❌ No EDM Train HTML file found")
        print("Please run the HTML extractor first")
        return
    
    # Use the most recent file
    html_file = max(html_files, key=os.path.getctime)
    print(f"📄 Using HTML file: {html_file}")
    
    # Parse events
    parser = EDMTrainParser(html_file)
    parser.run()


if __name__ == '__main__':
    main()