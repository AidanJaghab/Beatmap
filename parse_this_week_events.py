#!/usr/bin/env python3
"""
EDM Train This Week Parser
Extracts venue location right under artist name and filters for this week only
"""

import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ThisWeekEDMParser:
    """Parse EDM Train HTML for this week's events only"""
    
    def __init__(self, html_file):
        self.html_file = html_file
        self.events = []
        self.soup = None
        self.this_week_start = self.get_week_start()
        self.this_week_end = self.this_week_start + timedelta(days=6)
        
    def get_week_start(self):
        """Get the start of this week (Monday)"""
        today = datetime.now()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
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
            'div[class*="card"]'
        ]
        
        event_containers = []
        
        for selector in selectors:
            containers = self.soup.select(selector)
            if containers:
                logger.info(f"Found {len(containers)} containers with selector: {selector}")
                event_containers = containers  # Use the first successful selector
                break
        
        logger.info(f"Total event containers found: {len(event_containers)}")
        return event_containers
    
    def extract_artist_and_venue(self, container):
        """Extract artist name and venue location from container structure"""
        try:
            # Get all text lines from the container
            text = container.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None, None
            
            # First line should be artist name
            artist = lines[0].strip()
            
            # Skip if this looks like navigation or non-event text
            skip_terms = ['view all', 'see more', 'click here', 'loading', 'menu', 'filter', 'search']
            if any(term in artist.lower() for term in skip_terms):
                return None, None
            
            # Second line should be venue location
            venue_location = None
            for line in lines[1:5]:  # Check next few lines for venue
                # Look for venue patterns
                if (any(indicator in line.lower() for indicator in ['brooklyn', 'manhattan', 'queens', 'ny', 'new york']) or
                    any(venue in line.lower() for venue in ['mirage', 'avant', 'terminal', 'elsewhere', 'marquee', 'pier'])):
                    venue_location = line.strip()
                    break
                # Also check for venue-like patterns (contains dash and location)
                elif ' - ' in line and any(borough in line.lower() for borough in ['brooklyn', 'manhattan', 'queens']):
                    venue_location = line.strip()
                    break
            
            # Clean up artist name (remove extra info)
            artist = re.sub(r'\s*\([^)]*\)', '', artist)  # Remove parentheses
            artist = artist.strip()
            
            return artist, venue_location
            
        except Exception as e:
            logger.debug(f"Error extracting artist/venue: {e}")
            return None, None
    
    def parse_venue_location(self, venue_location):
        """Parse venue location string into venue, city, state"""
        if not venue_location:
            return 'TBA', 'New York', 'NY'
        
        # Pattern: "Venue Name - City, State Age+"
        venue_pattern = r'^([^-]+?)\s*-\s*([^,]+),?\s*(NY|New York)?\s*(\d+\+)?'
        match = re.match(venue_pattern, venue_location, re.IGNORECASE)
        
        if match:
            venue = match.group(1).strip()
            city = match.group(2).strip()
            state = 'NY'
            return venue, city, state
        
        # If no pattern match, try to extract what we can
        if ' - ' in venue_location:
            parts = venue_location.split(' - ')
            venue = parts[0].strip()
            location_part = parts[1].strip() if len(parts) > 1 else ''
            
            # Extract city from location part
            if ',' in location_part:
                city = location_part.split(',')[0].strip()
            else:
                city = location_part.strip()
            
            return venue, city, 'NY'
        
        # Default if we can't parse
        return venue_location, 'New York', 'NY'
    
    def extract_date_time(self, container):
        """Extract date and time from container"""
        text = container.get_text()
        
        # Look for this week's days
        current_date = datetime.now()
        week_days = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        # Check for day names in text
        text_lower = text.lower()
        found_day = None
        
        for day_name, day_num in week_days.items():
            if day_name in text_lower:
                # Calculate the date for this day in current week
                days_ahead = day_num - current_date.weekday()
                if days_ahead < 0:  # If day already passed this week, next week
                    days_ahead += 7
                event_date = current_date + timedelta(days=days_ahead)
                found_day = event_date.strftime('%A, %B %d, %Y')
                break
        
        # Look for specific date patterns
        if not found_day:
            date_patterns = [
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})?',
                r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
                r'(\d{1,2})-(\d{1,2})-(\d{2,4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    found_day = match.group(0)
                    break
        
        # Extract time
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
        
        return found_day, time_found
    
    def is_this_week(self, date_string):
        """Check if the date is within this week"""
        if not date_string or date_string == 'TBA':
            return True  # Include events without dates for now
        
        # Check for day names that indicate this week
        this_week_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if any(day in date_string.lower() for day in this_week_days):
            return True
        
        # Try to parse actual dates
        try:
            # Handle various date formats
            date_formats = [
                '%A, %B %d, %Y',  # Monday, July 18, 2025
                '%B %d, %Y',      # July 18, 2025
                '%m/%d/%Y',       # 07/18/2025
                '%m-%d-%Y'        # 07-18-2025
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string, fmt)
                    return self.this_week_start <= parsed_date <= self.this_week_end
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error parsing date {date_string}: {e}")
        
        return False  # Default to exclude if we can't parse
    
    def extract_link(self, container):
        """Extract event link from container"""
        link_element = container.find('a')
        if link_element and link_element.get('href'):
            href = link_element.get('href')
            
            # Make absolute URL if relative
            if href.startswith('/'):
                href = 'https://edmtrain.com' + href
            elif not href.startswith('http'):
                href = 'https://edmtrain.com/' + href
                
            return href
        
        return 'https://edmtrain.com'
    
    def extract_price(self, container):
        """Extract price from container"""
        text = container.get_text()
        
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',
            r'(\d+)\s*USD',
            r'From\s*\$(\d+)',
            r'Tickets:\s*\$(\d+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return f"${match.group(1)}"
        
        return "Check website"
    
    def parse_events(self):
        """Parse this week's events from the HTML"""
        if not self.soup:
            logger.error("No HTML loaded")
            return False
        
        containers = self.find_event_containers()
        
        if not containers:
            logger.warning("No event containers found")
            return False
        
        logger.info(f"Processing {len(containers)} event containers for this week...")
        logger.info(f"This week: {self.this_week_start.strftime('%A, %B %d')} - {self.this_week_end.strftime('%A, %B %d, %Y')}")
        
        for container in containers:
            try:
                # Extract artist and venue location
                artist, venue_location = self.extract_artist_and_venue(container)
                
                if not artist:
                    continue
                
                # Parse venue location
                venue, city, state = self.parse_venue_location(venue_location)
                
                # Extract date and time
                date_found, time_found = self.extract_date_time(container)
                
                # Check if this is a this week event
                if not self.is_this_week(date_found):
                    continue
                
                # Extract other details
                link = self.extract_link(container)
                price = self.extract_price(container)
                
                # Create event object
                event = {
                    'artist': artist,
                    'venue': venue,
                    'venue_location': venue_location or 'TBA',
                    'city': city,
                    'state': state,
                    'date': date_found or 'TBA',
                    'time': time_found or 'TBA',
                    'price': price,
                    'event_url': link,
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Validation
                if (len(artist) > 2 and 
                    not any(skip in artist.lower() for skip in ['click', 'more', 'view all', 'see all'])):
                    self.events.append(event)
                    logger.debug(f"Added this week event: {artist} at {venue}")
                
            except Exception as e:
                logger.debug(f"Error processing container: {e}")
                continue
        
        # Remove duplicates
        self.events = self.deduplicate_events()
        
        logger.info(f"Successfully parsed {len(self.events)} unique events for this week")
        return True
    
    def deduplicate_events(self):
        """Remove duplicate events"""
        unique_events = []
        seen_events = set()
        
        for event in self.events:
            # Create a key based on artist and venue
            key = f"{event['artist'].lower().strip()}_{event['venue'].lower().strip()}"
            if key not in seen_events:
                unique_events.append(event)
                seen_events.add(key)
        
        return unique_events
    
    def save_events(self, output_file='this_week_events.json'):
        """Save events to JSON file"""
        try:
            # Sort events by date then artist
            self.events.sort(key=lambda x: (x['date'] if x['date'] != 'TBA' else 'ZZZ', x['artist'].lower()))
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.events)} events to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving events: {e}")
            return False
    
    def print_summary(self):
        """Print summary of this week's events"""
        print(f"\n🎵 THIS WEEK'S EDM EVENTS: {len(self.events)}")
        print(f"📅 Week of {self.this_week_start.strftime('%B %d')} - {self.this_week_end.strftime('%B %d, %Y')}")
        print("=" * 60)
        
        if not self.events:
            print("❌ No events found for this week")
            return
        
        # Group by day
        days = {}
        for event in self.events:
            date = event['date']
            if date not in days:
                days[date] = []
            days[date].append(event)
        
        # Show events by day
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_name in day_order:
            day_events = []
            for date, events in days.items():
                if day_name.lower() in date.lower():
                    day_events.extend(events)
            
            if day_events:
                print(f"\n📅 {day_name} ({len(day_events)} events)")
                print("-" * 40)
                for event in day_events[:10]:  # Show first 10 per day
                    venue_str = f" @ {event['venue']}" if event['venue'] != 'TBA' else ""
                    time_str = f" - {event['time']}" if event['time'] != 'TBA' else ""
                    print(f"   • {event['artist']}{venue_str}{time_str}")
                if len(day_events) > 10:
                    print(f"   ... and {len(day_events) - 10} more")
        
        # Show TBA date events
        tba_events = days.get('TBA', [])
        if tba_events:
            print(f"\n📅 Date TBA ({len(tba_events)} events)")
            print("-" * 40)
            for event in tba_events[:5]:
                print(f"   • {event['artist']} @ {event['venue']}")
            if len(tba_events) > 5:
                print(f"   ... and {len(tba_events) - 5} more")
    
    def run(self, output_file='this_week_events.json'):
        """Main execution method"""
        print("🎵 EDM TRAIN THIS WEEK PARSER")
        print("📅 Extracting venue locations and filtering for this week")
        print("=" * 50)
        
        if not self.load_html():
            return False
        
        if not self.parse_events():
            return False
        
        if not self.save_events(output_file):
            return False
        
        self.print_summary()
        
        print(f"\n✅ Successfully parsed {len(self.events)} events for this week")
        print(f"📁 Saved to: {output_file}")
        return True


def main():
    import glob
    import os
    
    # Look for the most recent HTML file
    html_files = glob.glob("edmtrain_homepage_*.html")
    if not html_files:
        print("❌ No EDM Train HTML file found")
        print("Please run the HTML extractor first")
        return
    
    # Use the most recent file
    html_file = max(html_files, key=os.path.getctime)
    print(f"📄 Using HTML file: {html_file}")
    
    # Parse this week's events
    parser = ThisWeekEDMParser(html_file)
    parser.run()


if __name__ == '__main__':
    main()