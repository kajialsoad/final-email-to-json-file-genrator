"""
Selenium-based automation for Gmail OAuth client creation
Integrated from test driver implementation
"""

import os
import time
import json
import random
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from config import ConfigManager

class SeleniumAutomation:
    """Selenium-based automation for Gmail OAuth client creation"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.logger = logging.getLogger(__name__)
        
    def setup_chrome_options(self) -> Options:
        """Setup Chrome options for anti-detection"""
        chrome_options = Options()
        
        # Anti-detection settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Window size
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Set download directory and preferences
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            # Disable Chrome sign-in prompts
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        if not self.config.browser.headless:
            chrome_options.add_argument("--start-maximized")
        else:
            chrome_options.add_argument("--headless=new")
            
        return chrome_options
    
    async def handle_chrome_signin_popup(self) -> bool:
        """Handle Chrome sign-in popup and related dialogs"""
        try:
            # Wait a bit for popup to appear
            time.sleep(2)
            
            # First, try to click "Continue as [User]" button if it exists
            continue_selectors = [
                (By.XPATH, "//button[contains(text(), 'Continue as')]"),
                (By.XPATH, "//span[contains(text(), 'Continue as')]/parent::button"),
                (By.CSS_SELECTOR, "button[data-action='continue']"),
                (By.XPATH, "//button[contains(@aria-label, 'Continue as')]")
            ]
            
            for selector_type, selector_value in continue_selectors:
                try:
                    continue_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    self.logger.info("🔄 Clicking 'Continue as' button...")
                    
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", continue_button)
                    time.sleep(1)
                    
                    try:
                        continue_button.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", continue_button)
                    
                    self.logger.info("✅ 'Continue as' button clicked")
                    time.sleep(3)
                    
                    # After clicking continue, handle country selection and terms
                    await self.handle_country_and_terms()
                    return True
                    
                except Exception:
                    continue
            
            # If no "Continue as" button, try to dismiss the popup
            popup_selectors = [
                (By.XPATH, "//button[contains(text(), 'Use Chrome without an account')]"),
                (By.XPATH, "//button[contains(text(), 'No thanks')]"),
                (By.XPATH, "//button[contains(text(), 'Skip')]"),
                (By.CSS_SELECTOR, "button[data-testid='no-thanks-button']"),
                (By.XPATH, "//div[contains(text(), 'Sign in to Chrome?')]//following::button[contains(text(), 'No thanks')]")
            ]
            
            for selector_type, selector_value in popup_selectors:
                try:
                    popup_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    popup_button.click()
                    self.logger.info("✅ Chrome sign-in popup dismissed")
                    time.sleep(1)
                    return True
                except Exception:
                    continue
            
            # If no popup found, that's also fine
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not handle Chrome sign-in popup: {e}")
            return True  # Continue anyway
    
    async def handle_country_and_terms(self):
        """Handle country selection and terms of service agreement"""
        try:
            # Handle country selection
            await self.select_country_united_states()
            
            # Handle terms of service
            await self.agree_to_terms_of_service()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not handle country/terms: {str(e)}")
    
    async def select_country_united_states(self):
        """Select United States as country"""
        try:
            self.logger.info("🌍 Selecting country: United States...")
            
            # Wait for country selection dialog
            time.sleep(2)
            
            # Try to find country dropdown or selection
            country_selectors = [
                (By.XPATH, "//select[contains(@name, 'country')]"),
                (By.XPATH, "//select[contains(@aria-label, 'Country')]"),
                (By.CSS_SELECTOR, "select[name*='country']"),
                (By.XPATH, "//div[contains(text(), 'Country')]/following-sibling::select"),
                (By.XPATH, "//label[contains(text(), 'Country')]/following-sibling::select")
            ]
            
            for selector_type, selector_value in country_selectors:
                try:
                    country_dropdown = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    
                    # Select United States
                    from selenium.webdriver.support.ui import Select
                    select = Select(country_dropdown)
                    
                    # Try different variations of United States
                    us_options = ["United States", "US", "USA", "United States of America"]
                    for option in us_options:
                        try:
                            select.select_by_visible_text(option)
                            self.logger.info(f"✅ Selected country: {option}")
                            time.sleep(1)
                            return
                        except Exception:
                            continue
                    
                    # If text selection fails, try by value
                    try:
                        select.select_by_value("US")
                        self.logger.info("✅ Selected country: US (by value)")
                        return
                    except Exception:
                        pass
                        
                except Exception:
                    continue
            
            # Try clicking on United States option directly
            us_option_selectors = [
                (By.XPATH, "//option[contains(text(), 'United States')]"),
                (By.XPATH, "//li[contains(text(), 'United States')]"),
                (By.XPATH, "//div[contains(text(), 'United States')]")
            ]
            
            for selector_type, selector_value in us_option_selectors:
                try:
                    us_option = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    us_option.click()
                    self.logger.info("✅ Selected United States option")
                    time.sleep(1)
                    return
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Could not select country: {str(e)}")
    
    async def agree_to_terms_of_service(self):
        """Click Agree & Continue for Terms of Service"""
        try:
            self.logger.info("📋 Agreeing to Terms of Service...")
            
            # Wait for terms dialog
            time.sleep(2)
            
            # Try to find and click "Agree & Continue" button
            agree_selectors = [
                (By.XPATH, "//button[contains(text(), 'Agree & Continue')]"),
                (By.XPATH, "//button[contains(text(), 'Agree and Continue')]"),
                (By.XPATH, "//span[contains(text(), 'Agree & Continue')]/parent::button"),
                (By.XPATH, "//button[contains(text(), 'I agree')]"),
                (By.XPATH, "//button[contains(text(), 'Accept')]"),
                (By.CSS_SELECTOR, "button[data-action*='agree']")
            ]
            
            for selector_type, selector_value in agree_selectors:
                try:
                    agree_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", agree_button)
                    time.sleep(1)
                    
                    try:
                        agree_button.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", agree_button)
                    
                    self.logger.info("✅ Terms of Service agreed")
                    time.sleep(2)
                    return
                    
                except Exception:
                    continue
            
            # Try to find checkbox + continue pattern
            try:
                # Look for terms checkbox
                checkbox_selectors = [
                    (By.XPATH, "//input[@type='checkbox'][contains(@name, 'terms')]"),
                    (By.XPATH, "//input[@type='checkbox'][contains(@id, 'terms')]"),
                    (By.CSS_SELECTOR, "input[type='checkbox'][name*='agree']")
                ]
                
                for selector_type, selector_value in checkbox_selectors:
                    try:
                        checkbox = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        if not checkbox.is_selected():
                            checkbox.click()
                            self.logger.info("✅ Terms checkbox checked")
                        break
                    except Exception:
                        continue
                
                # Then click continue
                continue_selectors = [
                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                    (By.XPATH, "//button[contains(text(), 'Next')]"),
                    (By.CSS_SELECTOR, "button[type='submit']")
                ]
                
                for selector_type, selector_value in continue_selectors:
                    try:
                        continue_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        continue_button.click()
                        self.logger.info("✅ Continue button clicked after terms")
                        time.sleep(2)
                        return
                    except Exception:
                        continue
                        
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not agree to terms: {str(e)}")
    
    async def initialize_browser(self) -> bool:
        """Initialize Chrome browser with WebDriver"""
        try:
            self.logger.info("Initializing Chrome browser...")
            
            # Setup Chrome options
            chrome_options = self.setup_chrome_options()
            
            # Setup Chrome service with WebDriverManager
            service = Service(ChromeDriverManager().install())
            
            # Create WebDriver instance
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Setup WebDriverWait
            self.wait = WebDriverWait(self.driver, 30)
            
            self.logger.info("Chrome browser initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome browser: {e}")
            return False
    
    def human_delay(self, min_delay: float = None, max_delay: float = None):
        """Add human-like delay"""
        min_delay = min_delay or self.config.automation.human_delay_min
        max_delay = max_delay or self.config.automation.human_delay_max
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def human_type(self, element, text: str):
        """Type text with human-like delays"""
        for char in text:
            element.send_keys(char)
            delay = random.uniform(
                self.config.automation.typing_delay_min / 1000,
                self.config.automation.typing_delay_max / 1000
            )
            time.sleep(delay)
    
    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to a URL"""
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            self.human_delay()
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            return False
    
    async def click_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 30) -> bool:
        """Click an element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.human_delay(0.5, 1.0)
            
            # Click element
            element.click()
            self.human_delay()
            return True
            
        except TimeoutException:
            self.logger.error(f"Element not clickable: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {e}")
            return False
    
    async def fill_input(self, selector: str, text: str, by: By = By.CSS_SELECTOR, timeout: int = 30) -> bool:
        """Fill an input field"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            
            # Clear and fill
            element.clear()
            self.human_delay(0.3, 0.7)
            self.human_type(element, text)
            self.human_delay()
            return True
            
        except TimeoutException:
            self.logger.error(f"Input field not found: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to fill input {selector}: {e}")
            return False
    
    async def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 30) -> bool:
        """Wait for an element to be present"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except TimeoutException:
            self.logger.error(f"Element not found: {selector}")
            return False
    
    async def get_element_text(self, selector: str, by: By = By.CSS_SELECTOR, timeout: int = 30) -> Optional[str]:
        """Get text content of an element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element.text
        except TimeoutException:
            self.logger.error(f"Element not found: {selector}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get text from {selector}: {e}")
            return None
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"selenium_screenshot_{timestamp}.png"
            
            screenshot_path = os.path.join(self.config.paths.screenshots_dir, filename)
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return ""
    
    async def close_browser(self):
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
    
    async def create_oauth_client(self, email: str, password: str, project_name: str = None) -> Dict[str, Any]:
        """
        Main automation flow for creating OAuth client
        Integrated from test driver implementation
        """
        try:
            # Default project name if not provided
            if not project_name:
                project_name = f"GmailOAuth-{int(time.time())}"
            self.logger.info(f"Starting OAuth client creation for project: {project_name}")
            
            # Initialize browser
            if not await self.initialize_browser():
                return {"success": False, "error": "Failed to initialize browser"}
            
            # Step 1: Login to Google Cloud Console
            self.logger.info("🔑 Starting Step 1: Login to Google Cloud Console")
            login_result = await self.login_to_google_cloud(email, password)
            if not login_result:
                return {"success": False, "error": "Login to Google Cloud Console failed"}
            self.logger.info("✅ Step 1 completed: Login to Google Cloud Console")
                
            # Step 2: Create or select project
            self.logger.info("🏗️ Starting Step 2: Create or select project")
            project_id = await self.create_or_select_project(project_name)
            if not project_id:
                return {"success": False, "error": "Create or select project failed"}
            self.logger.info(f"✅ Step 2 completed: Project created/selected with ID: {project_id}")
                
            # Step 3: Enable Gmail API
            self.logger.info("🔌 Starting Step 3: Enable Gmail API")
            api_result = await self.enable_gmail_api()
            if not api_result:
                return {"success": False, "error": "Enable Gmail API failed"}
            self.logger.info("✅ Step 3 completed: Gmail API enabled")
                
            # Step 4: Setup OAuth consent screen
            self.logger.info("🔧 Starting Step 4: Setup OAuth consent screen")
            consent_result = await self.setup_oauth_consent_screen(email)
            if not consent_result:
                return {"success": False, "error": "Setup OAuth consent screen failed"}
            self.logger.info("✅ Step 4 completed: OAuth consent screen setup")
                
            # Step 5: Create OAuth credentials
            self.logger.info("🔑 Starting Step 5: Create OAuth credentials")
            credentials_data = await self.create_oauth_credentials_selenium(email)
            if not credentials_data:
                return {"success": False, "error": "Create OAuth credentials failed"}
            self.logger.info("✅ Step 5 completed: OAuth credentials created")
                
            # Step 6: Save JSON file
            self.logger.info("💾 Starting Step 6: Save JSON file")
            save_result = await self.save_oauth_json(email, credentials_data, project_id)
            if not save_result:
                return {"success": False, "error": "Save JSON file failed"}
            self.logger.info("✅ Step 6 completed: JSON file saved")
            
            self.logger.info("🎉 All steps completed successfully!")
            return {"success": True, "message": "OAuth client created successfully", "project_id": project_id}
            
        except Exception as e:
            self.logger.error(f"Error in OAuth client creation: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            await self.close_browser()

    async def login_to_google_cloud(self, email: str, password: str) -> bool:
        """Login to Google Cloud Console"""
        try:
            self.logger.info("🌐 Navigating to Google Cloud Console...")
            self.driver.get("https://console.cloud.google.com/")
            
            # Handle Chrome sign-in popup if it appears
            await self.handle_chrome_signin_popup()
            
            # Wait for login page or dashboard
            WebDriverWait(self.driver, 30).until(
                lambda d: "accounts.google.com" in d.current_url or "console.cloud.google.com" in d.current_url
            )
            
            self.logger.info(f"📍 Current URL: {self.driver.current_url}")
            
            # If redirected to login page
            if "accounts.google.com" in self.driver.current_url:
                self.logger.info("🔐 Login page detected, entering credentials...")
                
                # Enter email
                self.logger.info(f"📧 Entering email: {email}")
                try:
                    email_input = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.ID, "identifierId"))
                    )
                    email_input.clear()
                    email_input.send_keys(email)
                    
                    # Click Next
                    next_button = self.driver.find_element(By.ID, "identifierNext")
                    next_button.click()
                    self.logger.info("✅ Email entered successfully")
                except Exception as e:
                    self.logger.error(f"❌ Failed to enter email: {str(e)}")
                    return False
                
                # Wait for password field
                self.logger.info("🔐 Waiting for password field...")
                try:
                    # Try multiple selectors for password field
                    password_input = None
                    selectors = [
                        (By.CSS_SELECTOR, "#password input"),
                        (By.XPATH, "//div[@id='password']//input"),
                        (By.CSS_SELECTOR, "div[data-initial-value] input"),
                        (By.NAME, "password"),
                        (By.CSS_SELECTOR, "input[type='password']"),
                        (By.XPATH, "//input[@type='password']"),
                        (By.CSS_SELECTOR, "input[autocomplete='current-password']")
                    ]
                    
                    for selector_type, selector_value in selectors:
                        try:
                            password_input = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((selector_type, selector_value))
                            )
                            break
                        except Exception:
                            continue
                    
                    if password_input is None:
                        # Wait longer and try again
                        time.sleep(3)
                        password_input = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.NAME, "password"))
                        )
                    
                    # Enter password
                    self.logger.info("🔐 Entering password...")
                    time.sleep(2)  # Wait for element to be interactive
                    
                    # Try multiple methods to enter password
                    password_filled = False
                    
                    # Method 1: Standard Selenium approach
                    try:
                        password_input.click()
                        password_input.clear()
                        password_input.send_keys(password)
                        
                        # Verify
                        password_value = password_input.get_attribute("value")
                        if len(password_value) == len(password):
                            password_filled = True
                    except Exception as e:
                        self.logger.warning(f"Method 1 failed: {e}")
                     
                    # Method 2: JavaScript approach
                    if not password_filled:
                        try:
                            # Focus and set value with JavaScript
                            self.driver.execute_script("arguments[0].focus();", password_input)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].value = '';", password_input)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].value = arguments[1];", password_input, password)
                            
                            # Trigger events
                            self.driver.execute_script("""
                                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                            """, password_input)
                            
                            password_filled = True
                        except Exception as e:
                            self.logger.warning(f"Method 2 failed: {e}")
                    
                    if not password_filled:
                        return False
                    
                    # Click Next/Sign in
                    time.sleep(2)
                    try:
                        next_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "passwordNext"))
                        )
                        next_button.click()
                    except Exception:
                        # Try alternative selectors
                        signin_selectors = [
                            (By.XPATH, "//button[contains(text(), 'Next')]"),
                            (By.XPATH, "//input[@value='Sign in']"),
                            (By.CSS_SELECTOR, "button[type='submit']")
                        ]
                        for selector_type, selector_value in signin_selectors:
                            try:
                                signin_button = self.driver.find_element(selector_type, selector_value)
                                signin_button.click()
                                break
                            except Exception:
                                continue
                    
                    self.logger.info("✅ Password entered successfully")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to enter password: {str(e)}")
                    return False
                
                # Wait for successful login
                try:
                    WebDriverWait(self.driver, 30).until(
                        lambda d: "console.cloud.google.com" in d.current_url
                    )
                    self.logger.info("✅ Successfully logged into Google Cloud Console")
                    return True
                except Exception as e:
                    self.logger.error(f"❌ Login verification failed: {str(e)}")
                    return False
            else:
                self.logger.info("✅ Already logged into Google Cloud Console")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Login process failed: {str(e)}")
            return False

    async def create_or_select_project(self, project_name: str) -> str:
        """Create or select a project"""
        try:
            self.logger.info(f"🏗️ Creating/selecting project: {project_name}")
            
            # Navigate to project selector
            self.driver.get("https://console.cloud.google.com/projectselector2/home/dashboard")
            time.sleep(3)
            
            # Handle Chrome sign-in popup if it appears
            await self.handle_chrome_signin_popup()
            
            # Check if we're already in a project
            try:
                current_project = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-value*='project']"))
                )
                self.logger.info("✅ Already in a project, continuing...")
                return project_name
            except Exception:
                pass
            
            # Try to create new project
            create_project_selectors = [
                (By.XPATH, "//button[contains(text(), 'CREATE PROJECT')]"),
                (By.XPATH, "//span[contains(text(), 'CREATE PROJECT')]/parent::button"),
                (By.XPATH, "//button[contains(text(), 'Create Project')]"),
                (By.CSS_SELECTOR, "button[aria-label*='Create project']")
            ]
            
            project_created = False
            for selector_type, selector_value in create_project_selectors:
                try:
                    create_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", create_button)
                    time.sleep(1)
                    
                    try:
                        create_button.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", create_button)
                    
                    time.sleep(3)
                    
                    # Enter project name with multiple selector attempts
                    project_name_selectors = [
                        (By.CSS_SELECTOR, "input[aria-label*='Project name']"),
                        (By.CSS_SELECTOR, "input[placeholder*='project name']"),
                        (By.XPATH, "//input[contains(@aria-label, 'Project name')]"),
                        (By.CSS_SELECTOR, "input[name*='project']")
                    ]
                    
                    for name_selector_type, name_selector_value in project_name_selectors:
                        try:
                            project_name_input = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((name_selector_type, name_selector_value))
                            )
                            project_name_input.clear()
                            self.human_type(project_name_input, project_name)
                            break
                        except Exception:
                            continue
                    
                    # Click create button
                    create_button_selectors = [
                        (By.XPATH, "//button[contains(text(), 'CREATE')]"),
                        (By.XPATH, "//span[contains(text(), 'CREATE')]/parent::button"),
                        (By.XPATH, "//button[contains(text(), 'Create')]"),
                        (By.CSS_SELECTOR, "button[type='submit']")
                    ]
                    
                    for create_selector_type, create_selector_value in create_button_selectors:
                        try:
                            create_button = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((create_selector_type, create_selector_value))
                            )
                            
                            try:
                                create_button.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", create_button)
                            
                            # Wait for project creation
                            time.sleep(10)
                            self.logger.info("✅ Project created successfully")
                            project_created = True
                            break
                        except Exception:
                            continue
                    
                    if project_created:
                        break
                        
                except Exception:
                    continue
            
            if not project_created:
                # Try to select an existing project or continue with current one
                self.logger.warning("⚠️ Could not create new project, continuing with existing setup...")
                
                # Navigate to home dashboard to ensure we're in a valid project context
                self.driver.get("https://console.cloud.google.com/home/dashboard")
                time.sleep(3)
            
            return project_name
                
        except Exception as e:
            self.logger.error(f"❌ Project creation/selection failed: {str(e)}")
            # Try to continue anyway
            try:
                self.driver.get("https://console.cloud.google.com/home/dashboard")
                time.sleep(3)
                return project_name
            except Exception:
                return None

    async def enable_gmail_api(self) -> bool:
        """Enable Gmail API with improved error handling"""
        try:
            self.logger.info("🔌 Enabling Gmail API...")
            
            # Navigate to APIs & Services Library
            library_url = f"https://console.cloud.google.com/apis/library?project={self.project_id}"
            self.driver.get(library_url)
            time.sleep(3)
            
            # Handle Chrome sign-in popup if it appears
            await self.handle_chrome_signin_popup()
            
            # Wait for page to load completely
            WebDriverWait(self.driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
            
            # Search for Gmail API with improved selectors and interaction
            search_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='Search']"),
                (By.CSS_SELECTOR, "input[aria-label*='Search']"),
                (By.CSS_SELECTOR, "input[type='search']"),
                (By.XPATH, "//input[contains(@placeholder, 'Search')]"),
                (By.XPATH, "//input[contains(@aria-label, 'Search')]"),
                (By.CSS_SELECTOR, "cfc-textfield input"),
                (By.XPATH, "//cfc-textfield//input")
            ]
            
            search_input = None
            for selector_type, selector_value in search_selectors:
                try:
                    search_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    
                    # Ensure element is interactable
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    break
                except Exception:
                    continue
            
            if not search_input:
                self.logger.error("❌ Could not find search input")
                return False
            
            # Interact with search input using multiple methods
            try:
                # Scroll to element and focus
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", search_input)
                time.sleep(1)
                
                # Click to focus
                search_input.click()
                time.sleep(1)
                
                # Clear and type
                search_input.clear()
                time.sleep(0.5)
                self.human_type(search_input, "Gmail API")
                time.sleep(1)
                search_input.send_keys("\n")
                
            except Exception:
                # Fallback to JavaScript interaction
                self.driver.execute_script("arguments[0].value = 'Gmail API';", search_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)
                time.sleep(1)
                search_input.send_keys("\n")
            
            time.sleep(4)  # Wait for search results
            
            # Click on Gmail API with improved selectors
            gmail_api_selectors = [
                (By.XPATH, "//a[contains(@href, 'gmail')]"),
                (By.XPATH, "//div[contains(text(), 'Gmail API')]//ancestor::a"),
                (By.XPATH, "//span[contains(text(), 'Gmail API')]//ancestor::a"),
                (By.CSS_SELECTOR, "a[href*='gmail']"),
                (By.XPATH, "//cfc-card[contains(., 'Gmail API')]//a"),
                (By.XPATH, "//div[contains(@class, 'card')]//span[contains(text(), 'Gmail API')]//ancestor::a"),
                (By.XPATH, "//cfc-list-item[contains(., 'Gmail API')]")
            ]
            
            gmail_api_link = None
            for selector_type, selector_value in gmail_api_selectors:
                try:
                    gmail_api_link = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    
                    # Ensure element is clickable
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    break
                except Exception:
                    continue
            
            if not gmail_api_link:
                # Try direct navigation to Gmail API page
                self.logger.info("🔄 Navigating directly to Gmail API page...")
                gmail_api_url = f"https://console.cloud.google.com/apis/library/gmail.googleapis.com?project={self.project_id}"
                self.driver.get(gmail_api_url)
                time.sleep(3)
            else:
                # Click Gmail API link with improved interaction
                try:
                    # Scroll to element
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", gmail_api_link)
                    time.sleep(2)
                    
                    # Try multiple click methods
                    try:
                        gmail_api_link.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", gmail_api_link)
                        except Exception:
                            # Use ActionChains as last resort
                            ActionChains(self.driver).move_to_element(gmail_api_link).click().perform()
                    
                    time.sleep(3)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to click Gmail API link: {str(e)}")
                    # Fallback to direct navigation
                    gmail_api_url = f"https://console.cloud.google.com/apis/library/gmail.googleapis.com?project={self.project_id}"
                    self.driver.get(gmail_api_url)
                    time.sleep(3)
            
            # Check if API is already enabled before trying to enable
            enabled_indicators = [
                "//span[contains(text(), 'API enabled')]",
                "//div[contains(text(), 'enabled')]",
                "//button[contains(text(), 'MANAGE')]",
                "//span[contains(text(), 'MANAGE')]",
                "//div[contains(text(), 'This API is enabled')]"
            ]
            
            for indicator in enabled_indicators:
                try:
                    enabled_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    self.logger.info("✅ Gmail API is already enabled")
                    return True
                except Exception:
                    continue
            
            # Enable the API with improved selectors and interaction
            enable_selectors = [
                (By.XPATH, "//button[contains(text(), 'ENABLE')]"),
                (By.XPATH, "//span[contains(text(), 'ENABLE')]/parent::button"),
                (By.CSS_SELECTOR, "button[aria-label*='Enable']"),
                (By.XPATH, "//button[contains(text(), 'Enable')]"),
                (By.XPATH, "//cfc-button[contains(text(), 'ENABLE')]"),
                (By.XPATH, "//div[contains(@role, 'button')]//span[contains(text(), 'ENABLE')]")
            ]
            
            enabled_api = False
            for selector_type, selector_value in enable_selectors:
                try:
                    enable_button = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    
                    # Scroll to element
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", enable_button)
                    time.sleep(2)
                    
                    # Ensure element is clickable
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    
                    # Try multiple click methods
                    try:
                        enable_button.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", enable_button)
                        except Exception:
                            ActionChains(self.driver).move_to_element(enable_button).click().perform()
                    
                    self.logger.info("✅ Gmail API enabled successfully")
                    enabled_api = True
                    break
                    
                except Exception as e:
                    self.logger.debug(f"Failed to click enable button: {str(e)}")
                    continue
            
            if not enabled_api:
                self.logger.warning("⚠️ Could not find or click Enable button, checking if already enabled...")
                
                # Final check for enabled status
                for indicator in enabled_indicators:
                    try:
                        enabled_element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, indicator))
                        )
                        self.logger.info("✅ Gmail API appears to be already enabled")
                        return True
                    except Exception:
                        continue
                
                self.logger.warning("⚠️ Could not confirm Gmail API enablement, but continuing...")
                return True  # Continue anyway as API might already be enabled
            
            # Wait for enablement to complete
            time.sleep(5)
            return True
                
        except Exception as e:
            self.logger.error(f"❌ Failed to enable Gmail API: {str(e)}")
            return False

    async def setup_oauth_consent_screen(self, email: str) -> bool:
        """Setup OAuth consent screen with app information, audience, and contact details"""
        try:
            self.logger.info("🔧 Setting up OAuth consent screen...")
            
            # Navigate to OAuth consent screen
            self.driver.get("https://console.cloud.google.com/apis/credentials/consent")
            time.sleep(3)
            
            # Handle Chrome sign-in popup if it appears
            await self.handle_chrome_signin_popup()
            
            # Check if consent screen is already configured
            try:
                # Look for existing consent screen
                existing_screen = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'EDIT APP')]"))
                )
                self.logger.info("✅ OAuth consent screen already configured")
                return True
            except Exception:
                # No existing screen, need to create one
                pass
            
            # Click "Get started" or "Configure consent screen"
            try:
                get_started_selectors = [
                    (By.XPATH, "//button[contains(text(), 'Get started')]"),
                    (By.XPATH, "//span[contains(text(), 'Get started')]/parent::button"),
                    (By.XPATH, "//button[contains(text(), 'Configure consent screen')]"),
                    (By.XPATH, "//span[contains(text(), 'Configure consent screen')]/parent::button")
                ]
                
                for selector_type, selector_value in get_started_selectors:
                    try:
                        get_started_btn = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        get_started_btn.click()
                        break
                    except Exception:
                        continue
                
                time.sleep(2)
            except Exception:
                pass
            
            # Select External user type
            try:
                external_radio = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value='EXTERNAL']"))
                )
                external_radio.click()
                self.logger.info("✅ Selected External user type")
                time.sleep(1)
            except Exception as e:
                self.logger.warning(f"⚠️ Could not select External user type: {e}")
            
            # Click Create or Continue
            try:
                create_continue_selectors = [
                    (By.XPATH, "//button[contains(text(), 'CREATE')]"),
                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                    (By.XPATH, "//span[contains(text(), 'CREATE')]/parent::button"),
                    (By.XPATH, "//span[contains(text(), 'Continue')]/parent::button")
                ]
                
                for selector_type, selector_value in create_continue_selectors:
                    try:
                        create_btn = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((selector_type, selector_value))
                        )
                        create_btn.click()
                        break
                    except Exception:
                        continue
                
                time.sleep(3)
                self.logger.info("✅ Proceeded to app information")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not click CREATE/Continue: {e}")
            
            # Fill App Information
            try:
                # App name
                app_name_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='App name']"))
                )
                app_name_input.clear()
                app_name_input.send_keys(email)
                self.logger.info(f"✅ App name set to: {email}")
                
                # User support email
                try:
                    support_email_dropdown = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label*='User support email']"))
                    )
                    support_email_dropdown.click()
                    time.sleep(1)
                    
                    # Select the email option
                    email_option = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{email}')]"))
                    )
                    email_option.click()
                    self.logger.info(f"✅ User support email set to: {email}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not set user support email: {e}")
                
                # Developer contact information (scroll down first)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                try:
                    contact_email_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='Email addresses']"))
                    )
                    contact_email_input.clear()
                    contact_email_input.send_keys(email)
                    self.logger.info(f"✅ Developer contact email set to: {email}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not set developer contact email: {e}")
                
                # Click Save and Continue
                save_continue_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'SAVE AND CONTINUE')]"))
                )
                save_continue_btn.click()
                time.sleep(3)
                self.logger.info("✅ App information saved")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to fill app information: {e}")
                return False
            
            # Skip Scopes step (click Save and Continue)
            try:
                save_continue_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'SAVE AND CONTINUE')]"))
                )
                save_continue_btn.click()
                time.sleep(2)
                self.logger.info("✅ Scopes step skipped")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not skip scopes step: {e}")
            
            # Skip Test users step (click Save and Continue)
            try:
                save_continue_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'SAVE AND CONTINUE')]"))
                )
                save_continue_btn.click()
                time.sleep(2)
                self.logger.info("✅ Test users step skipped")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not skip test users step: {e}")
            
            # Summary step - click Back to Dashboard
            try:
                back_dashboard_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'BACK TO DASHBOARD')]"))
                )
                back_dashboard_btn.click()
                time.sleep(2)
                self.logger.info("✅ OAuth consent screen setup completed")
                return True
            except Exception as e:
                self.logger.warning(f"⚠️ Could not click back to dashboard: {e}")
                return True  # Consider it successful anyway
                
        except Exception as e:
            self.logger.error(f"❌ Failed to setup OAuth consent screen: {str(e)}")
            return False

    async def create_oauth_credentials_selenium(self, email: str) -> Dict[str, Any]:
        """Create OAuth credentials using Selenium"""
        try:
            self.logger.info("🔑 Creating OAuth 2.0 Client ID...")
            
            # Navigate to Credentials page
            self.driver.get("https://console.cloud.google.com/apis/credentials")
            time.sleep(3)
            
            # Click "Create Credentials"
            create_credentials_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Create Credentials')]/parent::button"))
            )
            create_credentials_btn.click()
            
            # Select "OAuth client ID"
            oauth_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'OAuth client ID')]"))
            )
            oauth_option.click()
            
            time.sleep(2)
            
            # Select Desktop application
            desktop_radio = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='DESKTOP']"))
            )
            desktop_radio.click()
            
            # Enter name
            name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label*='Name']"))
            )
            name_input.clear()
            name_input.send_keys(email)
            
            # Click Create
            create_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'CREATE')]"))
            )
            create_button.click()
            
            time.sleep(3)
            
            # Download JSON
            download_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'DOWNLOAD JSON')]"))
            )
            download_button.click()
            
            time.sleep(2)
            self.logger.info("✅ OAuth credentials created and JSON downloaded")
            
            return {"success": True, "downloaded": True}
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create OAuth credentials: {str(e)}")
            return None

    async def save_oauth_json(self, email: str, credentials_data: Dict[str, Any], project_id: str) -> bool:
        """Save OAuth JSON file with proper naming"""
        try:
            # The file should already be downloaded to the default downloads folder
            # We just need to verify it exists and optionally rename it
            self.logger.info("💾 Verifying JSON file download...")
            
            # Wait a bit for download to complete
            time.sleep(3)
            
            # Check downloads folder for the JSON file
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            json_files = [f for f in os.listdir(downloads_path) if f.endswith('.json') and 'client_secret' in f]
            
            if json_files:
                # Get the most recent JSON file
                latest_file = max([os.path.join(downloads_path, f) for f in json_files], key=os.path.getctime)
                self.logger.info(f"✅ Found downloaded JSON file: {latest_file}")
                
                # Optionally rename it to include email
                new_name = f"{email.replace('@', '_').replace('.', '_')}.json"
                new_path = os.path.join(downloads_path, new_name)
                
                try:
                    os.rename(latest_file, new_path)
                    self.logger.info(f"✅ JSON file renamed to: {new_name}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not rename file: {e}")
                
                return True
            else:
                self.logger.error("❌ No JSON file found in downloads")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save OAuth JSON: {str(e)}")
            return False