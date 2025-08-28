"""
Enhanced stealth passport checker with advanced anti-detection techniques
"""
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

def setup_ultra_stealth_driver():
    """Setup Chrome driver with maximum stealth capabilities"""
    logging.info("🔧 Setting up ultra-stealth Chrome driver...")
    
    try:
        options = uc.ChromeOptions()
        
        # Minimal detection options - less is more
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1366,768')
        
        # Enable JavaScript and images for full functionality
        options.add_argument('--enable-javascript')
        
        # Ultra-stealth preferences
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Create driver with minimal options for maximum stealth
        driver = uc.Chrome(options=options, version_main=None)
        
        # Enhanced anti-detection script injection
        stealth_script = """
        // Remove webdriver traces
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'uk']
        });
        
        // Add chrome runtime
        window.navigator.chrome = {
            runtime: {},
            app: {
                isInstalled: false,
                InstallState: {
                    DISABLED: 'disabled',
                    INSTALLED: 'installed',
                    NOT_INSTALLED: 'not_installed'
                },
                RunningState: {
                    CANNOT_RUN: 'cannot_run',
                    READY_TO_RUN: 'ready_to_run',
                    RUNNING: 'running'
                }
            }
        };
        
        // Override permissions
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({state: 'granted'})
            })
        });
        
        // Mock connection info
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 100,
                downlink: 10
            })
        });
        
        // Override hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4
        });
        
        // Mock deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });
        """
        
        driver.execute_script(stealth_script)
        
        logging.info("✅ Ultra-stealth Chrome driver setup completed")
        return driver
        
    except Exception as e:
        logging.error(f"❌ Ultra-stealth driver setup failed: {str(e)}")
        raise

def ultra_human_navigation(driver, passport_code):
    """Ultra-realistic human navigation simulation"""
    logging.info("🎭 Starting ultra-realistic human simulation...")
    
    # Phase 1: Natural page arrival
    url = "https://passport.mfa.gov.ua"
    driver.get(url)
    
    # Simulate slow human reading of page title and initial scan
    time.sleep(random.uniform(3, 6))
    
    # Phase 2: Realistic mouse movement and scrolling
    driver.execute_script("""
        // Simulate natural mouse movements
        let moveCount = 0;
        const maxMoves = 8;
        
        function naturalMouseMove() {
            if (moveCount < maxMoves) {
                const x = Math.random() * window.innerWidth;
                const y = Math.random() * window.innerHeight;
                
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
                
                moveCount++;
                setTimeout(naturalMouseMove, Math.random() * 800 + 200);
            }
        }
        
        // Start natural mouse movement
        naturalMouseMove();
        
        // Simulate reading behavior with natural scrolling
        let scrollCount = 0;
        const scrollPattern = [0, 150, 300, 200, 100, 0];
        
        function naturalScroll() {
            if (scrollCount < scrollPattern.length) {
                window.scrollTo({
                    top: scrollPattern[scrollCount],
                    behavior: 'smooth'
                });
                scrollCount++;
                setTimeout(naturalScroll, Math.random() * 1500 + 1000);
            }
        }
        
        setTimeout(naturalScroll, 2000);
    """)
    
    # Wait for page to fully load with human-like patience
    time.sleep(random.uniform(8, 15))
    
    # Phase 3: Form interaction with realistic hesitation
    logging.info("🔍 Looking for passport input field...")
    
    # Find input with multiple attempts (like a human would)
    input_found = False
    attempts = 0
    max_attempts = 3
    
    while not input_found and attempts < max_attempts:
        try:
            # Try different ways a human might look for the input
            input_selectors = [
                'input[type="text"]',
                'input[placeholder*="номер"]',
                'input[placeholder*="passport"]',
                'input[name*="passport"]',
                'input[name*="number"]'
            ]
            
            for selector in input_selectors:
                try:
                    search_input = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    if search_input:
                        input_found = True
                        break
                except TimeoutException:
                    continue
            
            if not input_found:
                attempts += 1
                logging.info(f"🔍 Input not found, attempt {attempts}. Waiting and scrolling...")
                # Simulate human confusion and re-scanning the page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(random.uniform(2, 4))
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            attempts += 1
            logging.debug(f"Attempt {attempts} failed: {e}")
            time.sleep(random.uniform(1, 2))
    
    if not input_found:
        raise Exception("Could not find passport input field after human-like search")
    
    # Phase 4: Ultra-realistic typing simulation
    logging.info("⌨️ Starting ultra-realistic typing...")
    
    # Human-like focus behavior
    search_input.click()
    time.sleep(random.uniform(0.3, 0.8))
    
    # Clear field like a human (select all then type)
    search_input.clear()
    time.sleep(random.uniform(0.2, 0.5))
    
    # Type with realistic human rhythm
    for i, digit in enumerate(passport_code):
        # Simulate thinking pauses at certain points
        if i == 0:
            time.sleep(random.uniform(0.5, 1.2))  # Initial thinking
        elif i == 3:
            time.sleep(random.uniform(0.3, 0.7))  # Mid-sequence pause
        elif i == len(passport_code) - 1:
            time.sleep(random.uniform(0.2, 0.5))  # Final verification pause
        
        search_input.send_keys(digit)
        
        # Variable typing speed based on human patterns
        if i < 2:
            typing_delay = random.uniform(0.15, 0.35)  # Careful start
        elif i < 5:
            typing_delay = random.uniform(0.08, 0.20)  # Getting comfortable
        else:
            typing_delay = random.uniform(0.10, 0.25)  # Finishing up
            
        time.sleep(typing_delay)
    
    # Phase 5: Human verification and submission
    time.sleep(random.uniform(0.8, 2.0))  # Human verification pause
    
    # Look for submit button
    logging.info("🔍 Looking for submit button...")
    
    button_selectors = [
        'input[type="submit"]',
        'button[type="submit"]',
        'button:contains("Пошук")',
        'button:contains("Search")',
        '.btn-primary',
        '.submit-button'
    ]
    
    submit_button = None
    for selector in button_selectors:
        try:
            if 'contains' in selector:
                # XPath for text content
                xpath = f"//button[contains(text(), '{selector.split('\"')[1]}')]"
                submit_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
            else:
                submit_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
            
            if submit_button:
                break
        except TimeoutException:
            continue
    
    if not submit_button:
        raise Exception("Could not find submit button")
    
    # Human-like submission
    logging.info("🖱️ Submitting form with human-like behavior...")
    time.sleep(random.uniform(0.5, 1.5))  # Final hesitation
    
    submit_button.click()
    
    # Phase 6: Patient waiting for results
    logging.info("⏳ Waiting for results with human patience...")
    
    # Simulate human waiting behavior
    wait_time = random.uniform(10, 20)
    intervals = int(wait_time / 2)
    
    for i in range(intervals):
        time.sleep(2)
        # Occasional page interaction during wait
        if random.random() < 0.3:  # 30% chance
            driver.execute_script("""
                window.scrollTo(0, window.scrollY + Math.random() * 100 - 50);
            """)
    
    logging.info("✅ Ultra-realistic navigation completed")

def extract_status_ultra_careful(driver):
    """Ultra-careful status extraction with multiple strategies"""
    logging.info("📄 Starting ultra-careful status extraction...")
    
    # Wait a bit more for any dynamic content
    time.sleep(random.uniform(3, 6))
    
    # Strategy 1: Check for the status div directly
    try:
        status_element = driver.find_element(By.ID, "statusResultId")
        if status_element and status_element.is_displayed():
            content = status_element.text.strip()
            logging.info(f"✅ Found status content: {content[:100]}...")
            
            # Check if we got the temporary unavailable message vs real data
            if "тимчасово недоступні" in content or "temporarily unavailable" in content.lower():
                logging.warning("⚠️ Got 'temporarily unavailable' message - may need manual verification")
                
                # Try to wait a bit longer and check again
                logging.info("⏳ Waiting longer for content to load...")
                time.sleep(random.uniform(10, 15))
                
                # Refresh and try again
                driver.refresh()
                time.sleep(random.uniform(8, 12))
                
                status_element = driver.find_element(By.ID, "statusResultId")
                content = status_element.text.strip()
                
            return content
    except Exception as e:
        logging.debug(f"Direct status extraction failed: {e}")
    
    # Strategy 2: Look for any tables on the page
    try:
        tables = driver.find_elements(By.TAG_NAME, "table")
        for table in tables:
            if table.is_displayed():
                table_text = table.text.strip()
                if len(table_text) > 50 and ("Application" in table_text or "submitted" in table_text):
                    logging.info("✅ Found detailed status table")
                    return table_text
    except Exception as e:
        logging.debug(f"Table extraction failed: {e}")
    
    # Strategy 3: Page source analysis
    try:
        page_source = driver.page_source
        
        # Save page for debugging
        import os
        from datetime import datetime
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(script_dir, 'logs')
        debug_filename = os.path.join(logs_dir, f"ultra_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        with open(debug_filename, 'w', encoding='utf-8') as f:
            f.write(page_source)
        logging.info(f"💾 Saved ultra-debug page: {debug_filename}")
        
        # Extract any meaningful content
        if "statusResultId" in page_source:
            # Try to extract the content around statusResultId
            start_pos = page_source.find('id="statusResultId"')
            if start_pos != -1:
                # Extract content around this area
                context = page_source[start_pos:start_pos + 1000]
                return f"Page analysis result:\n{context}"
        
    except Exception as e:
        logging.debug(f"Page source analysis failed: {e}")
    
    return "Could not extract status with ultra-careful methods"

def test_ultra_stealth_check(passport_code="1320864"):
    """Test the ultra-stealth passport checking"""
    driver = None
    try:
        logging.info("🚀 Starting ultra-stealth passport check test...")
        
        driver = setup_ultra_stealth_driver()
        ultra_human_navigation(driver, passport_code)
        result = extract_status_ultra_careful(driver)
        
        logging.info("✅ Ultra-stealth test completed")
        return result
        
    except Exception as e:
        logging.error(f"❌ Ultra-stealth test failed: {e}")
        return f"Error: {str(e)}"
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    result = test_ultra_stealth_check()
    print(f"Result: {result}")
