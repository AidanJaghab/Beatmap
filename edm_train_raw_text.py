#!/usr/bin/env python3
"""
EDM Train Raw Text Extractor
Outputs the raw text content of the EDM Train website to a file
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def extract_raw_text():
    """Extract raw text from EDM Train NYC page"""
    driver = None
    try:
        driver = setup_driver()
        logger.info("Chrome driver initialized")
        
        # Navigate to EDM Train NYC
        logger.info("Navigating to EDM Train NYC...")
        driver.get("https://edmtrain.com/new-york-ny")
        
        # Wait for page to load
        logger.info("Waiting for page to load...")
        time.sleep(5)
        
        # Scroll to load more content
        logger.info("Scrolling to load content...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
        
        # Get all text from the page
        logger.info("Extracting text...")
        
        # Method 1: Get body text
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Method 2: Get HTML source
        page_source = driver.page_source
        
        # Method 3: Get all visible text elements
        all_elements = driver.find_elements(By.XPATH, "//*[not(self::script or self::style)]/text()[normalize-space()]/..")
        visible_texts = []
        for element in all_elements[:1000]:  # Limit to first 1000 elements
            try:
                text = element.text.strip()
                if text:
                    visible_texts.append(text)
            except:
                continue
        
        # Save raw text to file
        with open('edm_train_raw_text.txt', 'w', encoding='utf-8') as f:
            f.write("=== EDM TRAIN NYC RAW TEXT ===\n")
            f.write(f"URL: {driver.current_url}\n")
            f.write(f"Title: {driver.title}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("=== BODY TEXT ===\n")
            f.write(body_text)
            f.write("\n\n" + "=" * 50 + "\n\n")
            
            f.write("=== VISIBLE TEXT ELEMENTS ===\n")
            for i, text in enumerate(visible_texts, 1):
                f.write(f"[{i}] {text}\n")
                f.write("-" * 30 + "\n")
        
        # Save HTML source to separate file
        with open('edm_train_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        
        logger.info("Text extraction complete")
        print("✅ Raw text saved to: edm_train_raw_text.txt")
        print("✅ HTML source saved to: edm_train_page_source.html")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"   • Body text length: {len(body_text)} characters")
        print(f"   • Visible elements found: {len(visible_texts)}")
        print(f"   • Current URL: {driver.current_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")


def main():
    print("🌐 EDM TRAIN RAW TEXT EXTRACTOR")
    print("📍 Target: New York City page")
    print("=" * 50)
    
    extract_raw_text()


if __name__ == '__main__':
    main()