import time
import undetected_chromedriver as uc
import os
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
import random
import logging
from bs4 import BeautifulSoup  # Add this import
import json
import requests  # Add at top for Google Translate API
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import hashlib

# Setup enhanced logging with rotation
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Setup enhanced logging with rotation and better formatting"""
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
    
    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler with detailed format and rotation
    file_handler = RotatingFileHandler(
        'passport_checker.log', 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize logging
logger = setup_logging()

class ConfigMonitor:
    """Monitor configuration file for changes and reload settings automatically"""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self.last_modified = 0
        self.last_hash = ""
        self.current_config = {}
        self.config_lock = threading.Lock()
        self.load_config()
        
    def get_file_hash(self):
        """Get MD5 hash of config file content"""
        try:
            with open(self.config_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logging.debug(f"Error getting file hash: {e}")
            return ""
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with self.config_lock:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    new_config = json.load(f)
                
                # Update tracking variables
                self.last_modified = os.path.getmtime(self.config_path)
                self.last_hash = self.get_file_hash()
                self.current_config = new_config
                
                logging.debug("📋 Configuration loaded successfully")
                return True
                
        except Exception as e:
            logging.error(f"❌ Failed to load config: {str(e)}")
            return False
    
    def check_for_changes(self):
        """Check if config file has changed and reload if necessary"""
        try:
            if not os.path.exists(self.config_path):
                logging.warning("⚠️ Config file not found")
                return False
            
            current_modified = os.path.getmtime(self.config_path)
            current_hash = self.get_file_hash()
            
            # Check if file has been modified
            if (current_modified != self.last_modified or 
                current_hash != self.last_hash):
                
                logging.info("🔄 Config file changed, reloading settings...")
                print("🔄 Configuration file updated - applying new settings...")
                
                old_config = self.current_config.copy()
                
                if self.load_config():
                    # Log what changed
                    self.log_config_changes(old_config, self.current_config)
                    return True
                else:
                    logging.error("❌ Failed to reload config, keeping previous settings")
                    return False
            
            return False  # No changes detected
            
        except Exception as e:
            logging.error(f"❌ Error checking config changes: {str(e)}")
            return False
    
    def log_config_changes(self, old_config, new_config):
        """Log what configuration values have changed"""
        changes = []
        
        # Check main settings
        for key in ['passport_code', 'check_interval_seconds']:
            if key in old_config and key in new_config:
                if old_config[key] != new_config[key]:
                    changes.append(f"  • {key}: {old_config[key]} → {new_config[key]}")
        
        # Check timeout settings
        old_timeouts = old_config.get('timeouts', {})
        new_timeouts = new_config.get('timeouts', {})
        for key in ['search_input_wait', 'search_button_wait', 'result_wait']:
            if old_timeouts.get(key) != new_timeouts.get(key):
                changes.append(f"  • timeouts.{key}: {old_timeouts.get(key)} → {new_timeouts.get(key)}")
        
        # Check email settings
        old_email = old_config.get('email', {})
        new_email = new_config.get('email', {})
        for key in ['recipient', 'smtp_server', 'smtp_port']:
            if old_email.get(key) != new_email.get(key):
                changes.append(f"  • email.{key}: {old_email.get(key)} → {new_email.get(key)}")
        
        if changes:
            logging.info("Configuration changes detected:")
            for change in changes:
                logging.info(change)
                print(change)
        else:
            logging.info("Config file updated (minor changes or formatting)")
            print("Config file updated (minor changes)")
    
    def get_config(self):
        """Get current configuration (thread-safe)"""
        with self.config_lock:
            return self.current_config.copy()

def start_config_monitor(config_path):
    """Start configuration monitoring in a separate thread"""
    config_monitor = ConfigMonitor(config_path)
    
    def monitor_loop():
        while True:
            time.sleep(120)  # Check every 2 minutes
            config_monitor.check_for_changes()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    
    return config_monitor

def setup_driver(config: dict | None = None):
    """Setup Chrome driver with minimized fingerprint and stability."""
    logging.info("Setting up Chrome driver...")

    try:
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--lang=uk-UA')
        
        # Add stealth options from the original _inject_stealth helper
        # to make this single attempt more robust.
        early_script = """
        // 1) navigator.webdriver -> undefined
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // 2) window.chrome stub
        if (!window.chrome) {
          window.chrome = { runtime: {} };
        } else if (!window.chrome.runtime) {
          window.chrome.runtime = {};
        }

        // 3) Permissions: reflect Notification state instead of always granted
        const _origPerm = navigator.permissions && navigator.permissions.query;
        if (_origPerm) {
          navigator.permissions.query = (parameters) => {
            if (parameters && parameters.name === 'notifications') {
              return Promise.resolve({ state: Notification.permission });
            }
            return _origPerm(parameters);
          };
        }
        """
        
        driver = uc.Chrome(options=options)
        
        # Apply stealth settings
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': early_script})
        
        preferred_language = 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7'
        try:
            ua = driver.execute_script("return navigator.userAgent")
        except Exception:
            ua = None
        try:
            driver.execute_cdp_cmd('Network.enable', {})
            if ua:
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    'userAgent': ua.replace('HeadlessChrome', 'Chrome'), # Make it look less like a bot
                    'acceptLanguage': preferred_language,
                    'platform': 'Windows'
                })
        except Exception:
            pass

        logging.info("Chrome driver setup successful.")
        return driver
    except Exception as e:
        logging.error(f"Chrome driver setup failed: {e}")
        raise RuntimeError(f"Chrome driver setup failed: {e}")


def wait_with_random_delay(min_seconds=2.0, max_seconds=5.0):
    """Wait with random delay and progress indicator for longer waits"""
    delay = random.uniform(min_seconds, max_seconds)
    if delay > 5:
        print(f"Waiting {delay:.1f} seconds...")
        for i in range(int(delay)):
            time.sleep(1)
            if i % 5 == 0 and i > 0:
                print(f"{int(delay) - i} seconds remaining...")
        time.sleep(delay - int(delay))  # Handle fractional part
    else:
        time.sleep(delay)

def find_element_safely(driver, selectors, timeout=10, element_type="element"):
    """Safely find an element using multiple selectors with enhanced logging"""
    logging.info(f"Looking for {element_type}...")
    
    for i, selector in enumerate(selectors):
        try:
            logging.debug(f"Trying selector {i+1}/{len(selectors)}: {selector}")
            
            if selector.startswith('//'):
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            else:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            
            if element and element.is_displayed():
                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                wait_with_random_delay(0.5, 1)
                logging.info(f"Found {element_type} with selector: {selector}")
                return element
                
        except TimeoutException:
            logging.debug(f"Selector {i+1} timed out: {selector}")
            continue
        except Exception as e:
            logging.debug(f"Error with selector {i+1}: {str(e)}")
            continue
    
    logging.error(f"Could not find {element_type} with any selector")
    return None

def translate_ukrainian_status(text):
    """Translate Ukrainian text to English using Google Translate API with fallback"""
    if not text.strip():
        return text
        
    try:
        logging.info("Translating status using Google Translate...")
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'uk',
            'tl': 'en',
            'dt': 't',
            'q': text
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            # Google returns a nested list of translations
            translated = ''.join([part[0] for part in result[0] if part[0]])
            logging.info("Translation successful")
            return translated
        else:
            logging.warning(f"Google Translate API error: {response.status_code}")
            return text
            
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return text

def wait_for_cloudflare(driver, wait, max_retries=3):
    """Handle Cloudflare protection with enhanced detection and retries"""
    logging.info("Checking for Cloudflare protection...")
    
    for attempt in range(max_retries):
        try:
            # Check if driver is still valid
            if not driver.current_url:
                logging.warning("Driver session lost, cannot check Cloudflare")
                return False
                
            page_source = driver.page_source
            page_title = driver.title.lower()
            
            # Enhanced Cloudflare detection
            cloudflare_indicators = [
                "Just a moment",
                "Please Wait", 
                "Checking your browser",
                "DDoS protection by Cloudflare",
                "Cloudflare Ray ID",
                "cf-browser-verification",
                "Challenge running"
            ]
            
            is_cloudflare = any(indicator in page_source for indicator in cloudflare_indicators)
            is_cloudflare = is_cloudflare or "cloudflare" in page_title
            
            if is_cloudflare:
                logging.warning(f"Cloudflare protection detected, attempt {attempt + 1}/{max_retries}")
                print(f"Waiting for Cloudflare protection to pass...")
                
                # Longer wait for Cloudflare with progress indicator
                for i in range(20):
                    time.sleep(1)
                    if i % 5 == 0:
                        print(f"Waiting... {20-i} seconds remaining")
                
                logging.info("Refreshing page after Cloudflare wait")
                driver.refresh()
                wait_with_random_delay(3, 5)
            else:
                logging.info("No Cloudflare protection detected")
                return True
                
        except Exception as e:
            logging.error(f"Error during Cloudflare check (attempt {attempt + 1}): {str(e)}")
            if "no such window" in str(e).lower() or "target window already closed" in str(e).lower():
                logging.error("Browser window closed unexpectedly")
                return False
            if attempt == max_retries - 1:
                logging.error("Max retries reached for Cloudflare check")
                return False
            wait_with_random_delay(2, 4)
    
    logging.warning("Could not verify Cloudflare status after max retries")
    return False

def fetch_status_via_ajax(driver, session_id: str) -> str | None:
    """Call the site's AJAX endpoint directly using the browser's cookies.
    Returns extracted text if successful, else None.
    """
    try:
        base_url = "https://passport.mfa.gov.ua"
        endpoint = f"{base_url}/Home/CurrentSessionStatus?sessionId={session_id}"

        # Ensure we have cookies by having visited the base page
        try:
            if not driver.current_url or base_url not in driver.current_url:
                driver.get(base_url)
                wait_with_random_delay(2, 4)
        except Exception:
            pass

        # Collect cookies from Selenium
        cookies = {}
        try:
            for c in driver.get_cookies():
                cookies[c.get('name')] = c.get('value')
        except Exception:
            pass

        # Mirror browser headers
        try:
            ua = driver.execute_script("return navigator.userAgent")
        except Exception:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari/537.36"

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': f'{base_url}/',
            'User-Agent': ua,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': base_url,
            'Connection': 'keep-alive',
        }

        sess = requests.Session()
        sess.headers.update(headers)
        if cookies:
            sess.cookies.update(cookies)

        resp = sess.get(endpoint, timeout=20, allow_redirects=True)
        if resp.status_code != 200:
            logging.warning(f"AJAX endpoint returned HTTP {resp.status_code}")
            return None

        html = resp.text or ""

        # Persist for debugging
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logs_dir = os.path.join(script_dir, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            debug_filename = os.path.join(logs_dir, f"ajax_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logging.info(f"Saved AJAX response to: {debug_filename}")
        except Exception:
            pass

        # Parse and extract meaningful table/text
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Prefer statusResultId content
            container = soup.find(id='statusResultId') or soup
            table = container.find('table') if container else None
            if table:
                rows = table.find_all('tr')
                formatted = []
                for row in rows:
                    cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
                    if len(cols) >= 2 and any(cols):
                        formatted.append('\t'.join(cols[:2]))
                if formatted:
                    return 'Status\tDate\n' + '\n'.join(formatted)
                # Fallback to raw table text
                text = table.get_text('\n', strip=True)
                if text:
                    return text
            # Fallback: any substantial text
            text = container.get_text('\n', strip=True) if container else soup.get_text('\n', strip=True)
            if text and len(text) > 80:
                return text
        except Exception as parse_err:
            logging.debug(f"AJAX parse error: {parse_err}")

        return None
    except Exception as e:
        logging.warning(f"AJAX fallback failed: {e}")
        return None

def send_email(log_text, config_path, has_changed=False):
    """Send email notification with enhanced error handling"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        email_cfg = config["email"]
        
        msg = MIMEMultipart()
        msg['From'] = email_cfg['sender']
        msg['To'] = email_cfg['recipient']
        
        # Add "CHANGE" to subject if status has changed
        subject = "Alexander Passport Update"
        if has_changed:
            subject = "CHANGE - Alexander Passport Update"
        msg['Subject'] = subject
        
        msg.attach(MIMEText(log_text, 'plain', 'utf-8'))
        
        logging.info(f"Sending email with subject: {subject}")
        server = smtplib.SMTP(email_cfg['smtp_server'], email_cfg['smtp_port'])
        server.starttls()
        server.login(email_cfg['username'], email_cfg['password'])
        server.sendmail(email_cfg['sender'], email_cfg['recipient'], msg.as_string())
        server.quit()
        
        logging.info("Email sent successfully")
        print("Email sent successfully")
        
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        print(f"Failed to send email: {str(e)}")

def compare_with_last_log(translated_log, script_dir):
    """Compare current log with last saved log and return True if changed"""
    last_log_file = os.path.join(script_dir, 'last.log')
    
    # Read previous log if exists
    last_log = ""
    if os.path.exists(last_log_file):
        try:
            with open(last_log_file, 'r', encoding='utf-8') as f:
                last_log = f.read().strip()
        except Exception as e:
            print(f"Error reading last.log: {e}")
    
    # Compare logs (normalize whitespace)
    current_log_normalized = ' '.join(translated_log.split())
    last_log_normalized = ' '.join(last_log.split())
    
    has_changed = current_log_normalized != last_log_normalized
    
    # Save current log as last log
    try:
        with open(last_log_file, 'w', encoding='utf-8') as f:
            f.write(translated_log)
        print(f"Saved current log to: {last_log_file}")
    except Exception as e:
        print(f"Error saving to last.log: {e}")
    
    return has_changed

def check_passport():
    """Main passport checking function with enhanced anti-detection and error handling"""
    # Create logs directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    logging.info(f"📁 Script directory: {script_dir}")
    logging.info(f"📁 Logs directory: {logs_dir}")

    config_path = os.path.join(script_dir, 'config.json')
    
    # Start configuration monitor
    config_monitor = start_config_monitor(config_path)
    logging.info("🔍 Configuration monitoring started (checks every 2 minutes)")
    print("🔍 Configuration monitoring active - file changes will be detected automatically")
    
    if not config_monitor.current_config:
        logging.error("❌ Failed to load initial configuration")
        return

    check_count = 0
    while True:
        check_count += 1
        
        # Get current configuration (thread-safe)
        config = config_monitor.get_config()
        passport_code = config.get('passport_code', '1320864')
        check_interval = config.get('check_interval_seconds', 3600)

        # Get timeout settings from config
        timeouts = config.get('timeouts', {})
        search_input_wait = timeouts.get('search_input_wait', 5)
        search_button_wait = timeouts.get('search_button_wait', 5)
        result_wait = timeouts.get('result_wait', 5)

        logging.info(f"Starting passport check #{check_count}")
        print(f"\nStarting passport check #{check_count} at {datetime.now().strftime('%H:%M:%S')}")
        logging.info(f"Using config: passport={passport_code}, interval={check_interval}s, timeouts=({search_input_wait},{search_button_wait},{result_wait})")
        
        driver = None
        try:
            driver = setup_driver(config)
            
            # Enhanced stealth navigation with random delays
            url = "https://passport.mfa.gov.ua"
            logging.info(f"Accessing URL: {url}")
            print(f"Loading website with anti-detection measures...")
            
            # Random delay before accessing site
            wait_with_random_delay(2, 5)
            
            driver.get(url)

            # Wait for the main body of the page to be loaded.
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logging.info("Page body loaded.")
            except TimeoutException:
                raise RuntimeError("Page did not load within 30 seconds.")
            
            # Simulate human-like behavior
            logging.info("Simulating human behavior...")
            print("Simulating human browsing behavior...")
            
            # Random mouse movements and page interactions
            driver.execute_script("""
                // Simulate mouse movements
                var event = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.dispatchEvent(event);
                
                // Simulate scroll
                window.scrollTo(0, Math.random() * 200);
            """)
            
            # Enhanced Cloudflare handling with better error recovery
            if not wait_for_cloudflare(driver, None):
                raise RuntimeError("Could not bypass Cloudflare or anti-bot protection")

            # Additional human simulation before form interaction - more realistic
            logging.info("Simulating detailed human browsing behavior...")
            print("Applying advanced stealth techniques...")
            
            # Simulate reading the page more thoroughly
            wait_with_random_delay(8, 15)
            
            # Multiple scroll patterns like a human reading
            driver.execute_script("""
                // Simulate realistic human scrolling patterns
                function humanScroll() {
                    window.scrollTo(0, 150);
                    setTimeout(() => window.scrollTo(0, 300), 800);
                    setTimeout(() => window.scrollTo(0, 100), 1600);
                    setTimeout(() => window.scrollTo(0, 0), 2400);
                }
                humanScroll();
                
                // Simulate mouse hover on different elements
                var elements = document.querySelectorAll('input, button, a');
                if (elements.length > 0) {
                    var randomElement = elements[Math.floor(Math.random() * elements.length)];
                    var event = new MouseEvent('mouseover', {bubbles: true});
                    randomElement.dispatchEvent(event);
                }
            """)
            
            wait_with_random_delay(4, 8)

            # Find search input with enhanced selectors
            logging.info("Looking for search input...")
            print("Finding search input...")
            
            input_selectors = [
                'input[type="text"]',
                'input[name="passport"]',
                'input[name="number"]',
                'input[placeholder*="passport"]',
                'input[placeholder*="номер"]',
                'input[class*="search"]',
                '//input[@type="text"]',
                '//input[contains(@class, "search")]',
                '//input[contains(@placeholder, "passport")]',
                '//input[not(@type="hidden")]',
                'input'
            ]
            
            search_input = find_element_safely(driver, input_selectors, search_input_wait, "search input")
            if not search_input:
                raise NoSuchElementException("Could not find search input")

            # Enhanced human-like typing with random delays
            logging.info(f"Typing passport code: {passport_code}")
            print("Entering passport code with human-like typing...")
            
            # Focus on input like a human would
            search_input.click()
            wait_with_random_delay(0.5, 1.2)
            
            search_input.clear()
            wait_with_random_delay(0.3, 0.8)
            
            # Type with human-like rhythm
            for i, digit in enumerate(passport_code):
                search_input.send_keys(digit)
                # Variable typing speed - slower at start, faster as typing continues
                if i < 3:
                    wait_with_random_delay(0.15, 0.4)  # Slower start
                else:
                    wait_with_random_delay(0.08, 0.25)  # Faster typing

            # Small pause before submitting (human behavior)
            wait_with_random_delay(1, 2.5)

            # Find and click search button
            logging.info("Looking for search button...")
            print("Finding search button...")
            
            button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:not([type])',
                '.search-button',
                '//button[@type="submit"]',
                '//input[@type="submit"]',
                '//button[contains(text(), "Search")]',
                '//button[contains(text(), "Пошук")]',
                'button'
            ]
            
            search_button = find_element_safely(driver, button_selectors, search_button_wait, "search button")
            if not search_button:
                raise NoSuchElementException("Could not find search button")

            logging.info("Clicking search button...")
            print("Submitting search with human-like click...")
            
            # Human-like click with small movement
            driver.execute_script("arguments[0].focus();", search_button)
            wait_with_random_delay(0.2, 0.5)
            search_button.click()

            # Wait for results with extended time for dynamic loading
            print("Waiting for results (extended wait for dynamic content)...")
            wait_with_random_delay(10, 18)  # Much longer wait for dynamic content

            # Additional wait and page interaction to trigger any lazy loading
            logging.info("Ensuring all dynamic content is loaded...")
            print("Checking for dynamic content loading...")
            
            # Scroll to trigger any lazy loading
            driver.execute_script("""
                window.scrollTo(0, document.body.scrollHeight);
                setTimeout(() => window.scrollTo(0, 0), 1000);
            """)
            
            wait_with_random_delay(5, 8)
            
            # Check if page is still loading
            page_state = driver.execute_script("return document.readyState")
            logging.info(f"Page state: {page_state}")
            
            if page_state != "complete":
                logging.info("Page still loading, waiting longer...")
                wait_with_random_delay(5, 10)

            # Enhanced result extraction
            log_text = extract_passport_status(driver, result_wait)

            # If the page indicates anti-bot gating, try AJAX fallback
            unavailable_signals = [
                'temporarily unavailable',
                'тимчасово недоступні',
                'тимчасово недоступна',
                'Could not extract detailed passport status'
            ]
            if any(sig.lower() in (log_text or '').lower() for sig in unavailable_signals):
                logging.info("Trying AJAX fallback via cookie-authenticated request...")
                ajax_text = fetch_status_via_ajax(driver, passport_code)
                if ajax_text:
                    log_text = ajax_text
            
            if not log_text:
                # Try alternative extraction method if blocked
                logging.warning("Standard extraction failed, trying alternative methods...")
                print("Standard method blocked, trying alternative extraction...")
                
                # Try direct HTML parsing
                page_source = driver.page_source
                if "passport" in page_source.lower() or "паспорт" in page_source.lower():
                    # Save full page source for manual review
                    debug_filename = os.path.join(logs_dir, f"debug_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                    with open(debug_filename, 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    logging.info(f"Saved debug page source to: {debug_filename}")
                    print(f"Saved page source for analysis: {debug_filename}")
                    
                    log_text = "Website access successful but result extraction was blocked by anti-bot protection. Manual review required."
                else:
                    raise Exception("Could not extract passport status - possible anti-bot blocking")

            # Translate and process results
            translated_log = translate_ukrainian_status(log_text)
            logging.info(f"Status extracted successfully: {len(translated_log)} characters")
            print(f"\nPassport Status (English):\n{translated_log}\n")
            
            # Compare with last log to check for changes
            has_changed = compare_with_last_log(translated_log, script_dir)
            
            if has_changed:
                logging.warning("STATUS HAS CHANGED!")
                print("*** STATUS HAS CHANGED ***")
            else:
                logging.info("Status unchanged from last check")
                print("Status unchanged from last check")
            
            # Save log file
            log_filename = os.path.join(logs_dir, f"passport_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write(translated_log)
            logging.info(f"Saved log to: {log_filename}")
            
            # Send email notification
            send_email(translated_log, config_path, has_changed)
            
            logging.info(f"Check #{check_count} completed successfully")
            print(f"Check #{check_count} completed successfully")
                
        except Exception as e:
            logging.error(f"Error in check #{check_count}: {str(e)}")
            print(f"Error in check #{check_count}: {str(e)}")
            
            # Enhanced error handling for anti-bot detection
            if "anti-bot" in str(e).lower() or "blocked" in str(e).lower():
                print("Anti-bot protection detected. Consider:")
                print("   • Using a VPN or different IP address")
                print("   • Increasing check intervals (reduce frequency)")
                print("   • Manual verification might be required")
            
        finally:
            # Enhanced cleanup with error suppression
            if driver:
                try:
                    driver.quit()
                    logging.debug("Driver cleanup completed")
                except Exception as cleanup_error:
                    logging.debug(f"Driver cleanup error (suppressed): {cleanup_error}")
            
        # Wait before next check with progress indicator
        if check_interval > 60:
            next_check_time = datetime.now().timestamp() + check_interval
            next_check_str = datetime.fromtimestamp(next_check_time).strftime('%H:%M:%S')
            logging.info(f"⏰ Next check at {next_check_str} (waiting {check_interval}s)")
            print(f"⏰ Next check at {next_check_str}")
            
            # Show progress every 5 minutes for long waits
            for i in range(0, check_interval, 300):  # Every 5 minutes
                remaining = check_interval - i
                if remaining > 300:
                    time.sleep(300)
                    remaining_mins = remaining // 60
                    logging.info(f"⏳ {remaining_mins} minutes until next check...")
                    print(f"⏳ {remaining_mins} minutes until next check...")
                else:
                    time.sleep(remaining)
                    break
        else:
            time.sleep(check_interval)

def extract_passport_status(driver, result_wait):
    """Extract passport status from page with enhanced table detection"""
    logging.info("📄 Extracting passport status...")
    
    # Wait longer for dynamic content to load
    wait_with_random_delay(3, 6)
    
    # Method 1: Try to find status table specifically
    try:
        logging.debug("Looking for status table...")
        # Check for the specific table structure you mentioned
        table_selectors = [
            'table',
            '.table',
            '#statusResultId table',
            '.status-table',
            '[id*="status"] table',
            '[class*="status"] table'
        ]
        
        for selector in table_selectors:
            try:
                tables = driver.find_elements(By.CSS_SELECTOR, selector)
                logging.debug(f"Found {len(tables)} tables with selector: {selector}")
                
                for table in tables:
                    if table.is_displayed():
                        # Get table text and check if it contains status information
                        table_text = table.text.strip()
                        logging.debug(f"Table content preview: {table_text[:100]}...")
                        
                        # Check if table contains status information keywords
                        status_keywords = [
                            'Application submitted', 'Data sent for verification', 
                            'Data sent for personalization', 'document was produced',
                            'document arrived', 'Document issued', 'Status', 'Date',
                            'submitted', 'verification', 'personalization', 'produced', 'issued'
                        ]
                        
                        if any(keyword.lower() in table_text.lower() for keyword in status_keywords):
                            logging.info(f"✅ Found status table with content: {len(table_text)} characters")
                            # Format the table data properly
                            rows = table.find_elements(By.TAG_NAME, 'tr')
                            formatted_data = []
                            
                            for row in rows:
                                cells = row.find_elements(By.TAG_NAME, 'td')
                                if not cells:  # Try th for headers
                                    cells = row.find_elements(By.TAG_NAME, 'th')
                                
                                if cells and len(cells) >= 2:
                                    status = cells[0].text.strip()
                                    date = cells[1].text.strip()
                                    if status and date:
                                        formatted_data.append(f"{status}\t{date}")
                            
                            if formatted_data:
                                result = "Status\tDate\n" + "\n".join(formatted_data)
                                logging.info("✅ Successfully extracted formatted table data")
                                return result
                            else:
                                # Return raw table text if formatting fails
                                return table_text
                                
            except Exception as e:
                logging.debug(f"Error with table selector {selector}: {e}")
                continue
                
    except Exception as e:
        logging.debug(f"Table extraction method failed: {e}")

    # Method 2: Try to find result container and look for any structured data
    result_selectors = [
        '#statusResultId', '.result', '.log', '.alert', '.status', 
        '.card-body', '.passport-status', '.application-status', 
        '.document-status', '[id*="result"]', '[class*="result"]'
    ]
    
    try:
        logging.debug("Trying result container extraction...")
        for selector in result_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        element_text = element.text.strip()
                        logging.debug(f"Element content preview: {element_text[:100]}...")
                        
                        # Check if this contains actual status data vs generic message
                        if ('Application submitted' in element_text or 
                            'Data sent' in element_text or 
                            'Document' in element_text or
                            len(element_text) > 100):  # Longer text likely contains real data
                            
                            logging.info(f"✅ Found detailed status in element: {selector}")
                            return element_text
                            
            except Exception as e:
                logging.debug(f"Error with selector {selector}: {e}")
                continue
                
    except Exception as e:
        logging.debug(f"Result container extraction failed: {e}")

    # Method 3: Enhanced iframe detection
    try:
        logging.debug("Trying enhanced iframe extraction...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        logging.info(f"Found {len(iframes)} iframes to check")
        
        for idx, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                logging.debug(f"Checking iframe {idx}")
                
                # Look for tables first in iframe
                iframe_tables = driver.find_elements(By.TAG_NAME, 'table')
                for table in iframe_tables:
                    if table.is_displayed():
                        table_text = table.text.strip()
                        if 'Application submitted' in table_text or 'Status' in table_text:
                            logging.info(f"✅ Found status table in iframe {idx}")
                            result = table_text
                            driver.switch_to.default_content()
                            return result
                
                # Then look for other result containers
                for selector in result_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                element_text = element.text.strip()
                                if element_text and len(element_text) > 50:
                                    logging.info(f"✅ Found content in iframe {idx} with selector: {selector}")
                                    result = element_text
                                    driver.switch_to.default_content()
                                    return result
                    except Exception:
                        continue
                        
            except Exception as iframe_e:
                logging.debug(f"Error with iframe {idx}: {iframe_e}")
            finally:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass

    except Exception as e:
        logging.debug(f"Iframe extraction failed: {e}")

    # Method 4: Full page source analysis as last resort
    try:
        logging.debug("Analyzing full page source...")
        page_source = driver.page_source
        
        # Save full page for debugging
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(script_dir, 'logs')
        debug_filename = os.path.join(logs_dir, f"debug_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        try:
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            logging.info(f"💾 Saved full page source for analysis: {debug_filename}")
        except Exception:
            pass
            
        # Use BeautifulSoup for detailed analysis
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for status table in HTML
        status_div = soup.find('div', id='statusResultId')
        if status_div:
            table = status_div.find('table')
            if table and hasattr(table, 'find_all'):
                rows = table.find_all('tr')
                table_data = []
                for row in rows:
                    cols = [col.get_text(strip=True) for col in row.find_all(['td', 'th'])]
                    if len(cols) >= 2 and any(cols):  # Has at least 2 columns with content
                        table_data.append('\t'.join(cols))
                        
                if table_data:
                    result = '\n'.join(table_data)
                    logging.info("✅ Extracted table from HTML using BeautifulSoup")
                    return result
        
        # Look for any text containing status keywords
        status_keywords = ['Application submitted', 'Data sent for verification', 'Document issued']
        for keyword in status_keywords:
            if keyword in page_source:
                # Try to extract surrounding context
                start_pos = page_source.find(keyword)
                if start_pos != -1:
                    # Extract a reasonable chunk around the keyword
                    context_start = max(0, start_pos - 500)
                    context_end = min(len(page_source), start_pos + 1500)
                    context = page_source[context_start:context_end]
                    
                    # Clean up HTML and extract text
                    context_soup = BeautifulSoup(context, 'html.parser')
                    clean_text = context_soup.get_text(separator='\n', strip=True)
                    
                    if len(clean_text) > 100:
                        logging.info(f"✅ Found status context containing '{keyword}'")
                        return clean_text
        
    except Exception as e:
        logging.debug(f"Page source analysis failed: {e}")
    
    logging.error("❌ Could not extract passport status with any method")
    
    # Return a more informative message
    return "Could not extract detailed passport status. The website may be using advanced anti-bot protection or the page structure has changed."

def main():
    check_passport()

if __name__ == "__main__":
    main()
