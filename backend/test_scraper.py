#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime, date

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def test_scrape():
    driver = setup_driver()
    try:
        url = "https://edmtrain.com/new-york-city-ny"
        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(5)
        
        # Get page text
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Look for today's date
        today = date.today()
        today_str = today.strftime("%a, %b %-d")  # Mon, Jul 28
        print(f"\nLooking for: {today_str}")
        
        # Print first 50 lines to see what's on the page
        lines = page_text.split('\n')[:50]
        for i, line in enumerate(lines):
            if line.strip():
                print(f"{i}: {line.strip()}")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    test_scrape()