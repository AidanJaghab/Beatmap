#!/usr/bin/env python3
"""
EDMTrain NYC Event Scraper using Selenium
Scrapes today's EDM events from edmtrain.com for New York City
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
from datetime import datetime, date
import os
import re

def setup_driver():
    """Set up Chrome driver in headless mode"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    return webdriver.Chrome(options=chrome_options)

def parse_date_string(date_str):
    """Convert date strings like 'Wed, Jul 23' to datetime.date objects"""
    try:
        # Remove any extra whitespace
        date_str = date_str.strip()
        
        # Get current year
        current_year = datetime.now().year
        
        # Try to parse the date
        # Format: "Wed, Jul 23"
        date_obj = datetime.strptime(f"{date_str} {current_year}", "%a, %b %d %Y").date()
        
        return date_obj
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def scrape_edmtrain_nyc():
    """Scrape EDMTrain NYC events page"""
    driver = setup_driver()
    
    try:
        url = "https://edmtrain.com/new-york-city-ny"
        print(f"Loading {url}...")
        driver.get(url)
        
        # Wait for page to load and scroll to load more events
        time.sleep(5)
        
        # Scroll down to load more events
        print("Scrolling to load more events...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Get all text content from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Get today's date
        today = date.today()
        print(f"Looking for events on: {today.strftime('%a, %b %d')}")
        
        events = []
        
        # Parse the page text
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            
        # Find today's date in the text
        today_patterns = [
            today.strftime("%a, %b %-d"),  # Wed, Jul 23
            today.strftime("%A, %B %-d"),  # Wednesday, July 23
            today.strftime("%b %-d"),       # Jul 23
        ]
        
        # Also try with zero-padded day
        today_patterns.extend([
            today.strftime("%a, %b %d"),    # Wed, Jul 23
            today.strftime("%A, %B %d"),    # Wednesday, July 23
            today.strftime("%b %d"),        # Jul 23
        ])
            
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line contains today's date
            if any(pattern.lower() in line.lower() for pattern in today_patterns):
                print(f"\nFound today's date at line {i}: {line}")
                
                # Process events under this date until we hit the next date
                j = i + 1
                while j < len(lines):
                    current_line = lines[j].strip()
                    
                    # Stop if we hit another date
                    if re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', current_line):
                        if not any(pattern in current_line for pattern in today_patterns):
                            break
                    
                    # Skip empty lines and non-event content
                    if not current_line or len(current_line) < 3:
                        j += 1
                        continue
                    
                    if any(skip in current_line.lower() for skip in ['buy tickets', 'sold out', 'on sale', 'free rsvp', 'stubhub', 'tickets', 'venue directions', 'buy now', 'purchase']):
                        j += 1
                        continue
                    
                    # Skip lines that are clearly locations, not event names
                    if any(loc in current_line.lower() for loc in ['brooklyn, ny', 'manhattan, ny', 'queens, ny', 'bronx, ny']):
                        j += 1
                        continue
                    
                    # Check if this looks like an event name 
                    is_event_name = False
                    
                    # Check if it has commas (multiple artists) and is not a location
                    if ',' in current_line and not any(loc in current_line.lower() for loc in ['brooklyn', 'manhattan', 'queens', 'bronx']):
                        is_event_name = True
                    
                    # Check if next line looks like a venue (even for single artist events)
                    elif j + 1 < len(lines) and len(current_line) > 3:
                        next_line = lines[j + 1].strip()
                        # Look for venue indicators
                        venue_indicators = ['rooftop', 'club', 'hall', 'venue', 'bar', 'lounge', 'brooklyn', 'manhattan', 'queens', 'elsewhere', 'tba', 'earthly', 'signal']
                        
                        if any(indicator in next_line.lower() for indicator in venue_indicators) or \
                           (any(loc in next_line.lower() for loc in ['ny']) and ' - ' in next_line):
                            # Make sure current line doesn't look like ticket/promo text
                            if not any(skip in current_line.lower() for skip in ['free', 'rsvp', 'buy', 'sold', 'ticket', '$']):
                                is_event_name = True
                    
                    if is_event_name:
                        event = {
                            "name": current_line,
                            "venue": "TBA",
                            "location": "New York, NY",
                            "date": today.isoformat()
                        }
                        
                        # Look for venue in next line (always the line after artist)
                        if j + 1 < len(lines):
                            venue_line = lines[j + 1].strip()
                            
                            # Parse venue line: "Venue - City, State | Age" or "Venue - City, State Age"
                            if ' - ' in venue_line:
                                parts = venue_line.split(' - ')
                                event["venue"] = parts[0].strip()
                                if len(parts) > 1:
                                    location_part = parts[1].strip()
                                    # Extract location and age
                                    for age in ['21+', '18+', '16+']:
                                        if age in location_part:
                                            location_part = location_part.replace(age, '').strip()
                                            break
                                    event["location"] = location_part
                            else:
                                # No dash, just venue name (clean age restrictions)
                                venue_clean = venue_line
                                for age in ['21+', '18+', '16+']:
                                    if age in venue_clean:
                                        venue_clean = venue_clean.replace(age, '').strip()
                                event["venue"] = venue_clean
                            
                            j += 1  # Skip the venue line
                        
                        events.append(event)
                        print(f"Found event: {event['name']} @ {event['venue']}")
                    
                    j += 1
                
                break
            
            i += 1
        
        # Remove duplicates
        unique_events = []
        seen = set()
        for event in events:
            key = (event['name'], event['venue'])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
        
    finally:
        driver.quit()

def main():
    print("EDMTrain NYC Event Scraper")
    print("=" * 50)
    
    # Scrape events
    events = scrape_edmtrain_nyc()
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Save to JSON
    output_file = 'data/latest_events.json'
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)
    
    print(f"\nFound {len(events)} events for today")
    
    if events:
        print("\nTODAY'S EVENTS:")
        print("=" * 50)
        for i, event in enumerate(events, 1):
            print(f"\nEvent {i}:")
            print(f"  Name: {event['name']}")
            print(f"  Venue: {event['venue']}")
            print(f"  Location: {event['location']}")
            print(f"  Date: {event['date']}")
    else:
        print("\nNo events found for today")
    
    print(f"\nEvents saved to {output_file}")

if __name__ == "__main__":
    main()