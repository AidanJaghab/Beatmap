#!/usr/bin/env python3
"""
Daily Events Scraper for GitHub Actions
Scrapes EDM Train for current day's events and saves to day-specific JSON files
"""

import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

# Force webdriver-manager to ignore system PATH
os.environ['WDM_LOCAL'] = '1'
# Ensure webdriver-manager doesn't use system chromedriver
os.environ['WDM_SKIP_CHROME_DRIVER_PATH_CHECK'] = '1'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DailyEventsScraper:
    """Scrape events for the current day"""
    
    def __init__(self):
        self.events = []
        self.driver = None
        self.current_day = os.getenv('CURRENT_DAY', datetime.now().strftime('%A').lower())
        self.current_date = os.getenv('CURRENT_DATE', datetime.now().strftime('%Y-%m-%d'))
        self.display_date = os.getenv('DISPLAY_DATE', datetime.now().strftime('%A, %B %d, %Y'))
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome driver for GitHub Actions"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Force webdriver-manager to download correct version and ignore PATH
            logger.info("Downloading ChromeDriver using webdriver-manager...")
            
            # Clear any cached driver paths
            from webdriver_manager.core.utils import ChromeType
            driver_path = ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()
            
            logger.info(f"ChromeDriver downloaded to: {driver_path}")
            
            # Create service with explicit executable path
            service = Service(executable_path=driver_path)
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def extract_html(self):
        """Extract HTML from EDM Train"""
        try:
            logger.info("Navigating to EDM Train...")
            self.driver.get("https://edmtrain.com/")
            time.sleep(5)
            
            # Scroll to load content
            for i in range(3):
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3});")
                time.sleep(2)
            
            page_source = self.driver.page_source
            logger.info(f"Extracted HTML ({len(page_source)} characters)")
            return page_source
            
        except Exception as e:
            logger.error(f"Error extracting HTML: {e}")
            return None
    
    def parse_events_for_day(self, html_content):
        """Parse events for the current day"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find event containers
        containers = soup.select('div[class*="event"]')
        logger.info(f"Found {len(containers)} event containers")
        
        day_events = []
        
        for container in containers:
            try:
                event = self.parse_event_container(container)
                if event and self.is_current_day_event(event):
                    day_events.append(event)
                    
            except Exception as e:
                logger.debug(f"Error parsing container: {e}")
                continue
        
        # Remove duplicates
        unique_events = self.deduplicate_events(day_events)
        
        logger.info(f"Found {len(unique_events)} events for {self.current_day}")
        return unique_events
    
    def parse_event_container(self, container):
        """Parse individual event container"""
        try:
            text = container.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None
            
            # Extract artist (first line)
            artist = lines[0].strip()
            
            # Skip navigation elements
            skip_terms = ['view all', 'see more', 'click here', 'loading', 'menu']
            if any(term in artist.lower() for term in skip_terms):
                return None
            
            # Extract venue location (second line)
            venue_location = None
            for line in lines[1:5]:
                if (any(indicator in line.lower() for indicator in ['brooklyn', 'manhattan', 'queens', 'ny']) or
                    ' - ' in line):
                    venue_location = line.strip()
                    break
            
            # Parse venue details
            venue, city, state = self.parse_venue_details(venue_location)
            
            # Extract date and time
            date_found, time_found = self.extract_date_time(text)
            
            # Extract price
            price = self.extract_price(text)
            
            # Extract link
            event_url = self.extract_link(container)
            
            return {
                'artist': artist,
                'venue': venue,
                'venue_location': venue_location or 'TBA',
                'city': city,
                'state': state,
                'date': date_found or self.display_date,
                'time': time_found or 'TBA',
                'price': price,
                'event_url': event_url,
                'scraped_at': datetime.now().isoformat(),
                'day_of_week': self.current_day.title()
            }
            
        except Exception as e:
            logger.debug(f"Error parsing event: {e}")
            return None
    
    def parse_venue_details(self, venue_location):
        """Parse venue location string"""
        if not venue_location:
            return 'TBA', 'New York', 'NY'
        
        if ' - ' in venue_location:
            parts = venue_location.split(' - ')
            venue = parts[0].strip()
            location = parts[1].strip() if len(parts) > 1 else ''
            city = location.split(',')[0].strip() if ',' in location else location
            return venue, city, 'NY'
        
        return venue_location, 'New York', 'NY'
    
    def extract_date_time(self, text):
        """Extract date and time from text"""
        # Look for current day patterns
        day_patterns = {
            'monday': ['monday', 'mon'],
            'tuesday': ['tuesday', 'tue', 'tues'],
            'wednesday': ['wednesday', 'wed'],
            'thursday': ['thursday', 'thurs', 'thu'],
            'friday': ['friday', 'fri'],
            'saturday': ['saturday', 'sat'],
            'sunday': ['sunday', 'sun']
        }
        
        date_found = None
        text_lower = text.lower()
        
        # Check if text contains current day
        current_day_patterns = day_patterns.get(self.current_day, [])
        if any(pattern in text_lower for pattern in current_day_patterns):
            date_found = self.display_date
        
        # Extract time
        time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)', text, re.IGNORECASE)
        time_found = time_match.group(1) if time_match else None
        
        return date_found, time_found
    
    def extract_price(self, text):
        """Extract price from text"""
        price_patterns = [r'\$(\d+)', r'(\d+)\s*USD', r'From\s*\$(\d+)']
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return f"${match.group(1)}"
        
        return "Check website"
    
    def extract_link(self, container):
        """Extract event link"""
        link_element = container.find('a')
        if link_element and link_element.get('href'):
            href = link_element.get('href')
            if href.startswith('/'):
                href = 'https://edmtrain.com' + href
            elif not href.startswith('http'):
                href = 'https://edmtrain.com/' + href
            return href
        
        return 'https://edmtrain.com'
    
    def is_current_day_event(self, event):
        """Check if event is for current day"""
        if not event:
            return False
        
        # Check if event date matches current day
        event_date = event.get('date', '').lower()
        artist = event.get('artist', '').lower()
        
        # Include if date contains current day or if no specific date
        return (self.current_day in event_date or 
                event_date == 'tba' or 
                len(artist) > 2)
    
    def deduplicate_events(self, events):
        """Remove duplicate events"""
        unique = []
        seen = set()
        
        for event in events:
            key = f"{event['artist'].lower()}_{event['venue'].lower()}"
            if key not in seen:
                unique.append(event)
                seen.add(key)
        
        return unique
    
    def save_events(self, events):
        """Save events to JSON files"""
        # Save day-specific file
        day_file = f"data/{self.current_day}_events.json"
        with open(day_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        # Save latest events file
        latest_file = "data/latest_events.json"
        latest_data = {
            'date': self.current_date,
            'day': self.current_day.title(),
            'display_date': self.display_date,
            'event_count': len(events),
            'updated_at': datetime.now().isoformat(),
            'events': events
        }
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(latest_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(events)} events to {day_file} and {latest_file}")
        
        return day_file, latest_file
    
    def cleanup(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
    
    def run(self):
        """Main execution"""
        try:
            print(f"🎵 DAILY EDM EVENTS SCRAPER")
            print(f"📅 Scraping events for: {self.display_date}")
            print(f"🤖 Running in GitHub Actions mode")
            print("=" * 50)
            
            if not self.setup_driver():
                return False
            
            html_content = self.extract_html()
            if not html_content:
                return False
            
            events = self.parse_events_for_day(html_content)
            
            if events:
                day_file, latest_file = self.save_events(events)
                print(f"✅ Successfully scraped {len(events)} events for {self.current_day}")
                print(f"📁 Files: {day_file}, {latest_file}")
            else:
                print(f"⚠️  No events found for {self.current_day}")
                # Still save empty file to track the attempt
                self.save_events([])
            
            return True
            
        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            print(f"❌ Scraper failed: {e}")
            return False
        finally:
            self.cleanup()


def main():
    scraper = DailyEventsScraper()
    success = scraper.run()
    
    if not success:
        exit(1)  # Exit with error code for GitHub Actions


if __name__ == '__main__':
    main()