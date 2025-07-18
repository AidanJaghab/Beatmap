#!/usr/bin/env python3
"""
EDM Train HTML Extractor
Opens https://edmtrain.com/ with WebDriver and extracts HTML
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_driver():
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def extract_edmtrain_html():
    """Extract HTML from EDM Train main page"""
    driver = None
    try:
        print("🌐 Opening EDM Train with WebDriver...")
        driver = setup_driver()
        logger.info("Chrome WebDriver initialized")
        
        # Navigate to EDM Train main page
        logger.info("Navigating to https://edmtrain.com/...")
        driver.get("https://edmtrain.com/")
        
        # Wait for page to load
        logger.info("Waiting for page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(5)
        
        # Scroll to load more content
        logger.info("Scrolling to load dynamic content...")
        for i in range(4):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4});")
            time.sleep(2)
        
        # Go back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Get page information
        current_url = driver.current_url
        page_title = driver.title
        page_source = driver.page_source
        
        # Get timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML to file
        html_filename = f"edmtrain_homepage_{timestamp}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- EDM Train Homepage HTML -->\n")
            f.write(f"<!-- Extracted on: {datetime.now().isoformat()} -->\n")
            f.write(f"<!-- URL: {current_url} -->\n")
            f.write(f"<!-- Title: {page_title} -->\n")
            f.write(f"<!-- User Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 -->\n")
            f.write("<!-- ======================================== -->\n\n")
            f.write(page_source)
        
        # Extract and save visible text
        text_filename = f"edmtrain_text_{timestamp}.txt"
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write("=== EDM TRAIN HOMEPAGE TEXT ===\n")
            f.write(f"Extracted: {datetime.now().isoformat()}\n")
            f.write(f"URL: {current_url}\n")
            f.write(f"Title: {page_title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(body_text)
        
        # Get some page statistics
        all_links = driver.find_elements(By.TAG_NAME, "a")
        all_images = driver.find_elements(By.TAG_NAME, "img")
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        
        logger.info("HTML extraction complete")
        
        print("✅ HTML extraction successful!")
        print(f"📁 HTML saved to: {html_filename}")
        print(f"📁 Text saved to: {text_filename}")
        print(f"\n📊 Page Statistics:")
        print(f"   • URL: {current_url}")
        print(f"   • Title: {page_title}")
        print(f"   • HTML size: {len(page_source):,} characters")
        print(f"   • Text size: {len(body_text):,} characters")
        print(f"   • Links found: {len(all_links)}")
        print(f"   • Images found: {len(all_images)}")
        print(f"   • Div elements: {len(all_divs)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error extracting HTML: {e}")
        print(f"❌ Error: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")


def main():
    print("🎵 EDM TRAIN HTML EXTRACTOR")
    print("🌐 Target: https://edmtrain.com/")
    print("📁 Saving to current folder")
    print("=" * 50)
    
    success = extract_edmtrain_html()
    
    if success:
        print("\n🎉 Extraction completed successfully!")
    else:
        print("\n❌ Extraction failed!")


if __name__ == '__main__':
    main()