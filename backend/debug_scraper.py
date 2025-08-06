#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime, date
import re

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def debug_scrape():
    driver = setup_driver()
    try:
        url = "https://edmtrain.com/new-york-city-ny"
        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(5)
        
        # Scroll more to load content
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Look for today's date in various formats
        today = date.today()
        today_patterns = [
            today.strftime("%a, %b %-d"),   # Mon, Jul 28
            today.strftime("%A, %B %-d"),   # Monday, July 28
            today.strftime("%b %-d"),       # Jul 28
            today.strftime("%a, %b %d"),    # Mon, Jul 28
            today.strftime("%A, %B %d"),    # Monday, July 28
            today.strftime("%b %d"),        # Jul 28
            today.strftime("%-d"),          # 28
            "Mon",                          # Just the day
            "Monday"                        # Full day name
        ]
        
        print(f"\nLooking for today: {today} ({today.strftime('%A, %B %d, %Y')})")
        print(f"Patterns to search: {today_patterns}")
        
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        
        # Find all date-like patterns
        date_lines = []
        for i, line in enumerate(lines):
            if re.match(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', line):
                date_lines.append((i, line))
            # Also look for any of our today patterns
            for pattern in today_patterns:
                if pattern.lower() in line.lower():
                    print(f"FOUND POTENTIAL MATCH at line {i}: '{line}'")
        
        print(f"\nFound {len(date_lines)} date-like lines:")
        for i, (line_num, line) in enumerate(date_lines[:20]):  # Show first 20
            print(f"{line_num}: {line}")
            
        # Show some context around potential matches
        print(f"\nSearching for Monday events...")
        for i, line in enumerate(lines):
            if "mon" in line.lower() and i < len(lines) - 5:
                print(f"\nContext around line {i} ('{line}'):")
                for j in range(max(0, i-2), min(len(lines), i+5)):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j}: {lines[j]}")
                    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_scrape()