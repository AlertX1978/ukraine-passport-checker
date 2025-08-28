#!/usr/bin/env python3
"""
Ukraine Passport Checker API Server
Flask REST API that wraps the passport checking functionality
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
import random
from bs4 import BeautifulSoup
from logging.handlers import RotatingFileHandler

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app

# Global variables
driver = None
driver_lock = threading.Lock()
config = {}

def setup_logging():
    """Setup enhanced logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'passport_api.log', 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def load_config():
    """Load configuration from JSON file"""
    global config
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logging.info(f"✅ Configuration loaded from {config_path}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to load config: {e}")
        # Default config
        config = {
            "timeouts": {
                "search_input_wait": 10,
                "search_button_wait": 10,
                "result_wait": 15
            }
        }
        return False

def setup_driver():
    """Setup Chrome driver with enhanced stability"""
    global driver
    
    with driver_lock:
        if driver is not None:
            try:
                driver.quit()
            except:
                pass
        
        logging.info("🔧 Setting up Chrome driver...")
        
        options = uc.ChromeOptions()
        # Enhanced options for stability and Cloudflare bypass
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1280,800')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--lang=uk-UA,uk;q=0.9,en-US,en;q=0.8')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
          # Preferences to appear more human-like
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        # Remove problematic options that cause Chrome driver errors
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = uc.Chrome(options=options, version_main=None)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logging.info("✅ Chrome driver setup successful")
            return True
        except Exception as e:
            logging.error(f"❌ Failed to setup Chrome driver: {e}")
            driver = None
            return False

def wait_with_random_delay(min_seconds=2, max_seconds=5):
    """Wait with random delay"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def find_element_safely(driver, selectors, timeout=10, element_type="element"):
    """Safely find an element using multiple selectors"""
    logging.info(f"🔍 Looking for {element_type}...")
    
    for i, selector in enumerate(selectors):
        try:
            if selector.startswith('//'):
                # XPath selector
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            else:
                # CSS selector
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            
            logging.info(f"✅ Found {element_type} with selector #{i+1}")
            return element
            
        except TimeoutException:
            logging.warning(f"⚠️ Selector #{i+1} failed for {element_type}: {selector}")
            continue
        except Exception as e:
            logging.warning(f"⚠️ Unexpected error with selector #{i+1}: {e}")
            continue
    
    logging.error(f"❌ Could not find {element_type} with any selector")
    return None

def check_passport_status(passport_code):
    """Check passport status on the official website"""
    global driver
    
    if not driver:
        if not setup_driver():
            return {
                "status": "ERROR",
                "message": "Failed to initialize browser",
                "success": False
            }
    
    try:
        with driver_lock:
            logging.info(f"🔍 Checking passport: {passport_code}")
            
            # Navigate to the passport website
            url = "https://passport.mfa.gov.ua"
            logging.info(f"🌐 Navigating to {url}")
            driver.get(url)
            
            # Wait for page to load and handle Cloudflare if present
            wait_with_random_delay(3, 7)
            
            # Check if Cloudflare challenge is present
            try:
                cf_elements = driver.find_elements(By.CSS_SELECTOR, '[data-ray], .cf-browser-verification, .cf-checking-browser, #cf-challenge-stage')
                if cf_elements:
                    logging.info("🛡️ Cloudflare protection detected, waiting...")
                    time.sleep(10)  # Wait for Cloudflare to complete
            except:
                pass
            
            # Find input field for passport code
            input_selectors = [
                'input[type="text"]',
                'input[placeholder*="сесії"]',
                'input[placeholder*="session"]',
                'input[id*="search"]',
                'input[name*="search"]',
                '.form-control',
                '#sessionId',
                '[data-testid="passport-input"]'
            ]
            
            input_element = find_element_safely(
                driver, 
                input_selectors, 
                timeout=config.get('timeouts', {}).get('search_input_wait', 10),
                element_type="passport input field"
            )
            
            if not input_element:
                return {
                    "status": "ERROR",
                    "message": "Could not find passport input field on website",
                    "success": False
                }
            
            # Clear and enter passport code
            logging.info(f"📝 Entering passport code: {passport_code}")
            input_element.clear()
            wait_with_random_delay(0.5, 1.5)
            
            # Type with human-like delays
            for char in passport_code:
                input_element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            wait_with_random_delay(1, 2)
            
            # Find and click search button
            button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("пошук")',
                'button:contains("Пошук")',
                'button:contains("search")',
                '.btn-primary',
                '.search-btn',
                '[data-testid="search-button"]'
            ]
            
            search_button = find_element_safely(
                driver, 
                button_selectors, 
                timeout=config.get('timeouts', {}).get('search_button_wait', 10),
                element_type="search button"
            )
            
            if not search_button:
                return {
                    "status": "ERROR", 
                    "message": "Could not find search button on website",
                    "success": False
                }
            
            # Click search button
            logging.info("🔍 Clicking search button...")
            search_button.click()
            
            # Wait for results
            wait_with_random_delay(3, 6)
            
            # Extract results
            return extract_passport_status(driver)
            
    except Exception as e:
        logging.error(f"❌ Error checking passport {passport_code}: {e}")
        return {
            "status": "ERROR",
            "message": f"Unexpected error: {str(e)}",
            "success": False
        }

def extract_passport_status(driver):
    """Extract passport status from the page"""
    try:
        # Wait for result content to load
        result_timeout = config.get('timeouts', {}).get('result_wait', 15)
        time.sleep(3)  # Initial wait
        
        # Get page content
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Log page title for debugging
        title = soup.find('title')
        if title:
            logging.info(f"📄 Page title: {title.get_text().strip()}")
        
        # Look for error messages first
        error_indicators = [
            'помилка', 'error', 'невірний', 'incorrect', 'не знайдено', 'not found',
            'недійсний', 'invalid', 'відсутній', 'missing'
        ]
        
        page_text = soup.get_text().lower()
        for error_word in error_indicators:
            if error_word in page_text:
                logging.warning(f"⚠️ Possible error detected: {error_word}")
                return {
                    "status": "INVALID",
                    "message": "Passport code not found or invalid",
                    "success": True
                }
        
        # Look for status information
        status_keywords = [
            'статус', 'status', 'стан', 'state', 'готовий', 'ready',
            'видано', 'issued', 'оброблено', 'processed', 'заявку подано', 'submitted'
        ]
        
        # Find status-related content
        status_found = False
        status_message = ""
        
        # Check for specific status containers
        status_selectors = [
            '.status', '.result', '.passport-status', '.document-status',
            '[class*="status"]', '[class*="result"]', '[id*="status"]', '[id*="result"]'
        ]
        
        for selector in status_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 5:  # Ignore very short text
                    for keyword in status_keywords:
                        if keyword in text.lower():
                            status_found = True
                            status_message = text
                            break
                    if status_found:
                        break
            if status_found:
                break
        
        # If no specific status found, get general page content
        if not status_found:
            # Look for any meaningful content
            content_elements = soup.find_all(['p', 'div', 'span', 'td'], string=True)
            for element in content_elements:
                text = element.get_text().strip()
                if text and len(text) > 10:
                    for keyword in status_keywords:
                        if keyword in text.lower():
                            status_message = text
                            status_found = True
                            break
                    if status_found:
                        break
        
        if status_found and status_message:
            logging.info(f"✅ Status found: {status_message}")
            
            # Determine status type based on content
            status_message_lower = status_message.lower()
            if any(word in status_message_lower for word in ['готовий', 'ready', 'видано', 'issued']):
                status_type = "VALID"
            elif any(word in status_message_lower for word in ['оброблено', 'processed', 'персоналізація', 'personalization']):
                status_type = "PROCESSING"
            elif any(word in status_message_lower for word in ['подано', 'submitted', 'заявку', 'application']):
                status_type = "PROCESSING"
            else:
                status_type = "UNKNOWN"
            
            return {
                "status": status_type,
                "message": status_message,
                "success": True,
                "details": {
                    "checkTime": datetime.now().isoformat(),
                    "source": "passport.mfa.gov.ua"
                }
            }
        else:
            # No clear status found
            logging.warning("⚠️ No status information found on page")
            return {
                "status": "UNKNOWN",
                "message": "No status information found",
                "success": True
            }
            
    except Exception as e:
        logging.error(f"❌ Error extracting status: {e}")
        return {
            "status": "ERROR",
            "message": f"Error extracting status: {str(e)}",
            "success": False
        }

# API Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Ukraine Passport Checker API"
    }), 200

@app.route('/check-passport', methods=['POST'])
def check_single_passport():
    """Check single passport endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'passportCode' not in data:
            return jsonify({
                "success": False,
                "error": "Missing passport code",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        passport_code = data['passportCode'].strip()
        
        if not passport_code:
            return jsonify({
                "success": False,
                "error": "Empty passport code",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Check passport
        result = check_passport_status(passport_code)
        
        if result['success']:
            # Convert to mobile app format
            api_response = {
                "passportCode": passport_code,
                "status": result['status'],
                "statusText": result['message'],
                "details": result.get('details', {})
            }
            
            return jsonify({
                "success": True,
                "data": api_response,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result['message'],
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logging.error(f"API error in check_single_passport: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/check-multiple', methods=['POST'])
def check_multiple_passports():
    """Check multiple passports endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'passportCodes' not in data:
            return jsonify({
                "success": False,
                "error": "Missing passport codes",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        passport_codes = data['passportCodes']
        
        if not isinstance(passport_codes, list) or not passport_codes:
            return jsonify({
                "success": False,
                "error": "Invalid passport codes format",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        results = []
        
        for passport_code in passport_codes:
            if passport_code.strip():
                result = check_passport_status(passport_code.strip())
                
                api_response = {
                    "passportCode": passport_code.strip(),
                    "status": result['status'],
                    "statusText": result['message'],
                    "details": result.get('details', {})
                }
                results.append(api_response)
                
                # Add delay between requests to avoid rate limiting
                time.sleep(random.uniform(2, 5))
        
        return jsonify({
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"API error in check_multiple_passports: {e}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/status', methods=['GET'])
def api_status():
    """Get API status and statistics"""
    return jsonify({
        "service": "Ukraine Passport Checker API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "driver_status": "initialized" if driver else "not_initialized"
    }), 200

if __name__ == '__main__':
    # Setup logging
    logger = setup_logging()
    
    # Load configuration
    load_config()
    
    # Initialize driver
    setup_driver()
    
    print("Starting Ukraine Passport Checker API Server...")
    print("Mobile app can connect to: http://localhost:8000")
    print("Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /check-passport - Check single passport")
    print("   POST /check-multiple - Check multiple passports")
    print("   GET  /status - API status")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        # Run Flask development server
        app.run(
            host='0.0.0.0',  # Allow connections from mobile app
            port=8000,
            debug=False,  # Set to False for production
            threaded=True
        )
    except KeyboardInterrupt:
        print("Shutting down server...")
        if driver:
            try:
                driver.quit()
                print("Browser closed")
            except:
                pass
        print("Server stopped")
    except Exception as e:
        logging.error(f"❌ Server error: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
