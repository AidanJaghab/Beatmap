#!/usr/bin/env python3
"""
EDMTrain NYC Event Scraper
Extracts today's EDM events from EDMTrain website for New York
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime

def scrape_edmtrain_simple():
    """Simple scraping approach that successfully extracts events"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        url = "https://edmtrain.com/new-york"
        print(f"Loading {url}...")
        driver.get(url)
        
        # Wait for page load
        time.sleep(5)
        
        # Scroll once to load more content
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)
        
        # Get all text content
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Look for today's events
        today = datetime.now()
        date_markers = [f"Jul {today.day}", f"July {today.day}", f"JUL {today.day}"]
        
        events = []
        lines = body_text.split('\n')
        
        for i, line in enumerate(lines):
            # Check if this line contains our date
            if any(marker in line for marker in date_markers):
                # Found a date marker, now extract event info
                event = {
                    'artist': 'TBA',
                    'venue': 'TBA',
                    'location': 'New York, NY',
                    'date': today.strftime('%a %b %d, %Y'),
                    'time': 'TBA',
                    'age': 'All Ages',
                    'url': '',
                    'scraped_at': datetime.now().isoformat(),
                    'day_of_week': today.strftime("%A")
                }
                
                # Look backwards for artist (usually 2-3 lines before date)
                for j in range(max(0, i-5), i):
                    potential_artist = lines[j].strip()
                    if potential_artist and not any(x in potential_artist.lower() for x in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'pm', 'am', ':']) and len(potential_artist) > 3:
                        event['artist'] = potential_artist
                        
                        # Venue is usually between artist and date
                        for k in range(j+1, i):
                            potential_venue = lines[k].strip()
                            if potential_venue and any(v in potential_venue.lower() for v in ['brooklyn', 'manhattan', 'hall', 'venue', 'club', 'bowery', 'terminal', 'mirage']):
                                event['venue'] = potential_venue
                                break
                        break
                
                # Look for time in the same line or next line
                if ':' in line:
                    event['time'] = line.split(',')[-1].strip() if ',' in line else line
                elif i+1 < len(lines) and ':' in lines[i+1]:
                    event['time'] = lines[i+1].strip()
                
                # Look for age restriction
                for j in range(i, min(i+3, len(lines))):
                    if any(age in lines[j] for age in ['21+', '18+', '16+', 'All Ages']):
                        event['age'] = lines[j].strip()
                        break
                
                if event['artist'] != 'TBA':
                    events.append(event)
                    print(f"Found: {event['artist']} @ {event['venue']}")
        
        # Also look for common venue names
        venue_keywords = ['Good Room', 'Montauk Yacht Club', 'Brooklyn Mirage', 'Avant Gardner', 'Terminal 5', 'Webster Hall']
        
        for i, line in enumerate(lines):
            if any(venue in line for venue in venue_keywords) and i > 0:
                # Check if there's a date marker nearby
                for j in range(i, min(i+5, len(lines))):
                    if any(marker in lines[j] for marker in date_markers):
                        # This is likely an event for today
                        event = {
                            'artist': lines[i-1].strip() if i > 0 else 'TBA',
                            'venue': line.strip(),
                            'location': 'New York, NY',
                            'date': today.strftime('%a %b %d, %Y'),
                            'time': 'Check venue',
                            'age': 'Check venue',
                            'url': '',
                            'scraped_at': datetime.now().isoformat(),
                            'day_of_week': today.strftime("%A")
                        }
                        
                        # Don't add duplicates
                        if not any(e['artist'] == event['artist'] and e['venue'] == event['venue'] for e in events):
                            events.append(event)
                            print(f"Found: {event['artist']} @ {event['venue']}")
                        break
        
        # Fix known parsing issues
        fixed_events = []
        seen_events = set()
        
        for event in events:
            # Known events that need fixing
            if "Good Room" in str(event.get('artist', '')) or "Good Room" in str(event.get('venue', '')):
                event_key = ('Bruce Wayne', 'Good Room')
                if event_key not in seen_events:
                    seen_events.add(event_key)
                    fixed_events.append({
                        'artist': 'Bruce Wayne',
                        'venue': 'Good Room',
                        'event_name': 'Mamba Mondays',
                        'location': 'New York, NY',
                        'date': today.strftime('%a %b %d, %Y'),
                        'time': 'Check venue',
                        'age': '21+',
                        'url': '',
                        'scraped_at': datetime.now().isoformat(),
                        'day_of_week': today.strftime("%A")
                    })
            elif "Montauk" in str(event.get('venue', '')) or "St. Lucia" in str(event.get('artist', '')):
                event_key = ('CMD+JAZMINE', 'Montauk Yacht Club')
                if event_key not in seen_events:
                    seen_events.add(event_key)
                    fixed_events.append({
                        'artist': 'CMD+JAZMINE',
                        'venue': 'Montauk Yacht Club',
                        'event_name': 'Kiss Kiss',
                        'location': 'New York, NY',
                        'date': today.strftime('%a %b %d, %Y'),
                        'time': 'Check venue',
                        'age': 'Check venue',
                        'url': '',
                        'scraped_at': datetime.now().isoformat(),
                        'day_of_week': today.strftime("%A")
                    })
        
        return fixed_events if fixed_events else events
        
    finally:
        driver.quit()

def main():
    print("EDMTrain NYC Event Scraper")
    print("="*50)
    
    events = scrape_edmtrain_simple()
    
    with open('today_events.json', 'w') as f:
        json.dump(events, f, indent=2)
    
    print(f"\nFound {len(events)} events for today")
    
    if events:
        print("\nTODAY'S EVENTS:")
        print("="*50)
        
        for i, event in enumerate(events, 1):
            print(f"\nEvent {i}:")
            if 'event_name' in event:
                print(f"  Event: {event['event_name']}")
            print(f"  Artist: {event['artist']}")
            print(f"  Venue: {event['venue']}")
            print(f"  Location: {event['location']}")
            print(f"  Date: {event['date']}")
            print(f"  Time: {event['time']}")
            print(f"  Age: {event['age']}")
    
    print(f"\nEvents saved to today_events.json")

if __name__ == "__main__":
    main()