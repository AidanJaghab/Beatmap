
#!/usr/bin/env python3
# ✅ UPDATED EDMTrain NYC Event Scraper using Hugging Face AI classifier for smart field parsing

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json
from datetime import datetime, date
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
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        page_text = driver.find_element(By.TAG_NAME, "body").text
        today = date.today()

        today_patterns = [
            today.strftime("%a, %b %-d"),
            today.strftime("%A, %B %-d"),
            today.strftime("%b %-d"),
            today.strftime("%a, %b %d"),
            today.strftime("%A, %B %d"),
            today.strftime("%b %d"),
        ]

        lines = [line.strip() for line in page_text.split('\n')]

') if line.strip()]
        events = []

        i = 0
        while i < len(lines):
            line = lines[i]
            if any(p.lower() in line.lower() for p in today_patterns):
                j = i + 1
                while j < len(lines):
                    current_line = lines[j].strip()
                    if re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', current_line):
                        if not any(p in current_line for p in today_patterns):
                            break
                    if not current_line or len(current_line) < 3:
                        j += 1
                        continue
                    if any(skip in current_line.lower() for skip in ['buy tickets', 'sold out', 'on sale', 'free rsvp', 'stubhub', 'tickets', 'venue directions', 'buy now', 'purchase']):
                        j += 1
                        continue
                    event_lines = [current_line]
                    for k in range(j + 1, min(j + 4, len(lines))):
                        if lines[k] and not any(x in lines[k].lower() for x in ['buy tickets', 'tickets', 'sold out']):
                            event_lines.append(lines[k])
                    parsed_event = {"event_name": "", "venue": "TBA", "location": "New York, NY", "promotional": [], "date": today.isoformat()}
                    for line in event_lines:
                        label = classify_event_line(line)
                        if label == "event_name" and not parsed_event["event_name"]:
                            parsed_event["event_name"] = line
                        elif label == "venue" and parsed_event["venue"] == "TBA":
                            venue_clean = line
                            for age in ['21+', '18+', '16+']:
                                venue_clean = venue_clean.replace(age, '').strip()
                            if ' - ' in venue_clean:
                                venue_clean = venue_clean.split(' - ')[0].strip()
                            parsed_event["venue"] = venue_clean
                        elif label == "location":
                            location = line
                            for age in ['21+', '18+', '16+']:
                                location = location.replace(age, '').strip()
                            if ' - ' in location:
                                location = location.split(' - ')[-1].strip()
                            parsed_event["location"] = location
                        elif label == "promotional":
                            parsed_event["promotional"].append(line)
                    if parsed_event["event_name"]:
                        event = {
                            "name": parsed_event["event_name"],
                            "venue": parsed_event["venue"],
                            "location": parsed_event["location"],
                            "date": parsed_event["date"]
                        }
                        events.append(event)
                        print(f"✅ {event['name']} @ {event['venue']}")
                    j += len(event_lines)
                break
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
