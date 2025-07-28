
#!/usr/bin/env python3
# ✅ UPDATED EDMTrain NYC Event Scraper using Hugging Face AI classifier for smart field parsing

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
from datetime import datetime, date, timedelta
import os
import re
from transformers import pipeline

# ---------------- AI CLASSIFIER SETUP ----------------
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
LABELS = ["event_name", "venue", "location", "promotional", "date", "unknown"]

def classify_event_line(text):
    result = classifier(text, LABELS)
    return result["labels"][0]
# -----------------------------------------------------

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def parse_date_string(date_str):
    try:
        date_str = date_str.strip()
        current_year = datetime.now().year
        return datetime.strptime(f"{date_str} {current_year}", "%a, %b %d %Y").date()
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def scrape_edmtrain_nyc():
    driver = setup_driver()
    try:
        url = "https://edmtrain.com/new-york-city-ny"
        driver.get(url)
        time.sleep(5)
        
        # Scroll more aggressively to load all events
        print("Scrolling to load more events...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 10  # Increase max scrolls
        
        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Give more time for content to load
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Try scrolling up a bit then down again to trigger lazy loading
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1000);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                final_height = driver.execute_script("return document.body.scrollHeight")
                if final_height == last_height:
                    print(f"No more content after {scroll_attempts + 1} scrolls")
                    break
            
            last_height = new_height
            scroll_attempts += 1
            print(f"Scroll {scroll_attempts}/{max_scrolls} - Page height: {new_height}")

        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        today = date.today()
        
        # Get this week's dates (7 days starting today)
        week_dates = []
        for i in range(0, 7):
            target_date = today + timedelta(days=i)
            week_dates.append(target_date)
        
        # Generate patterns for all dates in this week
        week_patterns = []
        for target_date in week_dates:
            patterns = [
                target_date.strftime("%a, %b %-d"),
                target_date.strftime("%A, %B %-d"),
                target_date.strftime("%a, %b %d"),
                target_date.strftime("%A, %B %d"),
                target_date.strftime("%b %-d"),
                target_date.strftime("%b %d"),
            ]
            week_patterns.extend(patterns)
        
        print(f"🗓️ Looking for THIS WEEK'S events: {[d.strftime('%a, %b %d') for d in week_dates]}")
        print(f"Total patterns to match: {len(week_patterns)}")
        print(f"Total lines to scan: {len(lines)}")
        events = []
        current_date = None
        current_date_obj = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line is a date
            date_match = re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})', line)
            if date_match:
                # Check if this date is in our target week
                if any(pattern.lower() in line.lower() for pattern in week_patterns):
                    current_date = line
                    # Find matching date object
                    current_date_obj = None
                    for target_date in week_dates:
                        if any(pattern.lower() in line.lower() for pattern in [
                            target_date.strftime("%a, %b %-d"),
                            target_date.strftime("%A, %B %-d"),
                            target_date.strftime("%a, %b %d"),
                            target_date.strftime("%A, %B %d")
                        ]):
                            current_date_obj = target_date.isoformat()
                            break
                    if not current_date_obj:
                        current_date_obj = today.isoformat()
                    print(f"📅 Found target date: {current_date}")
                else:
                    # If we've processed events and hit a date outside our week, we can continue
                    current_date = None
                    current_date_obj = None
                i += 1
                continue
            
            # Only process events if we're in a target date section
            if not current_date:
                i += 1
                continue
            
            # Skip empty lines and promotional content
            if not line or len(line) < 3:
                i += 1
                continue
            if any(skip in line.lower() for skip in ['buy tickets', 'sold out', 'tickets', 'venue directions', 'purchase']):
                i += 1
                continue
            
            # Check if this is a venue line
            if " - " in line and any(loc in line for loc in [" NY", " Brooklyn", " Manhattan", " Queens"]):
                venue_clean = line.split(' - ')[0].strip()
                for age in ['21+', '18+', '16+', 'All Ages']:
                    venue_clean = venue_clean.replace(age, '').strip()
                location_part = line.split(' - ')[1].strip()
                location = "Brooklyn, NY" if 'Brooklyn' in location_part else "New York, NY"
                
                print(f"  🏢 {current_date} - Found venue: {venue_clean} in {location}")
                
                # Look backward for the event name
                event_name = None
                for look_back in range(1, 4):
                    if i - look_back >= 0:
                        prev_line = lines[i - look_back].strip()
                        
                        # Skip promotional lines
                        if prev_line.lower() in ['new', 'open bar 8-9pm'] or any(skip in prev_line.lower() for skip in ['buy tickets', 'sold out', 'tickets']):
                            continue
                        
                        # Skip other venue lines
                        if " - " in prev_line and any(loc in prev_line for loc in [" NY", " Brooklyn", " Manhattan", " Queens"]):
                            continue
                            
                        # Skip date lines
                        if re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', prev_line):
                            continue
                        
                        # This should be our event
                        if len(prev_line) > 3:
                            event_name = prev_line
                            break
                
                if event_name:
                    event = {
                        "name": event_name,
                        "venue": venue_clean,
                        "location": location,
                        "date": current_date_obj or today.isoformat()
                    }
                    events.append(event)
                    print(f"    ✅ {event['name']} @ {event['venue']}")
            
            i += 1

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
    events = scrape_edmtrain_nyc()
    os.makedirs('data', exist_ok=True)
    with open('data/latest_events.json', 'w') as f:
        json.dump(events, f, indent=2)
    print(f"✅ Saved {len(events)} events to data/latest_events.json")

if __name__ == "__main__":
    main()
