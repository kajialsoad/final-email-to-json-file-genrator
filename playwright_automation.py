#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Automation Engine
Core automation engine with stealth mode and anti-detection features
"""

import asyncio
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
import time
import logging
import traceback
import os
import re

# Optional imports with fallbacks
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError
from config import get_config
from error_handler import error_handler, ErrorType, retry_async, log_error

class PlaywrightAutomationEngine:
    """Core Playwright automation engine with advanced features"""
    
    def __init__(self):
        self.config = get_config()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.session_id = str(uuid.uuid4())[:8]
        
        # Create directories
        self.screenshots_dir = Path(self.config.paths.screenshots_dir)
        self.downloads_dir = Path(self.config.paths.downloads_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = error_handler.logger
        
    @retry_async(context="browser_initialization")
    async def initialize_browser(self) -> bool:
        """Initialize Playwright browser with stealth and anti-detection"""
        try:
            self.logger.info("Initializing Playwright browser...")
            
            self.playwright = await async_playwright().start()
            
            # Get browser configuration
            browser_args = self.config.get_browser_args()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(**browser_args)
            
            # Create context with stealth settings and UI stability
            context_options = {
                'viewport': {
                    'width': self.config.browser.viewport_width,
                    'height': self.config.browser.viewport_height
                },
                'user_agent': self.config.browser.user_agent,
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': ['geolocation'],
                'device_scale_factor': self.config.browser.force_device_scale_factor,
                'is_mobile': False,
                'has_touch': False,
                'color_scheme': 'light',
                'reduced_motion': 'reduce' if self.config.browser.disable_animations else 'no-preference',
                'forced_colors': 'none',
                'extra_http_headers': {
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            }
            
            # Add download path
            if not self.config.browser.headless:
                context_options['accept_downloads'] = True
            
            self.context = await self.browser.new_context(**context_options)
            
            # Apply stealth mode
            if self.config.browser.stealth_mode and HAS_STEALTH:
                await stealth_async(self.context)
            elif self.config.browser.stealth_mode and not HAS_STEALTH:
                self.logger.warning("Stealth mode requested but playwright-stealth not installed")
            
            # Create page
            self.page = await self.context.new_page()
            
            # Configure page timeouts
            page_options = self.config.get_page_options()
            self.page.set_default_timeout(page_options['default_timeout'])
            self.page.set_default_navigation_timeout(page_options['default_navigation_timeout'])
            
            # Apply UI stability settings
            await self._apply_ui_stability_settings()
            
            # Add additional stealth measures
            await self._apply_stealth_measures()
            
            self.logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            log_error(e, "browser_initialization")
            raise
    
    async def _apply_ui_stability_settings(self):
        """Apply UI stability settings to prevent jumping and displacement"""
        try:
            # Disable smooth scrolling and animations
            await self.page.add_init_script("""
                // Disable smooth scrolling
                document.documentElement.style.scrollBehavior = 'auto';
                
                // Disable CSS animations and transitions
                const style = document.createElement('style');
                style.textContent = `
                    *, *::before, *::after {
                        animation-duration: 0s !important;
                        animation-delay: 0s !important;
                        transition-duration: 0s !important;
                        transition-delay: 0s !important;
                        scroll-behavior: auto !important;
                    }
                    
                    /* Prevent layout shifts */
                    body {
                        overflow-x: hidden !important;
                        position: relative !important;
                    }
                    
                    /* Stabilize viewport */
                    html {
                        overflow-x: hidden !important;
                        scroll-behavior: auto !important;
                    }
                    
                    /* Disable transform animations */
                    * {
                        transform: none !important;
                        will-change: auto !important;
                    }
                `;
                document.head.appendChild(style);
                
                // Prevent window resizing
                window.resizeTo = function() {};
                window.resizeBy = function() {};
                
                // Stabilize scroll position
                let lastScrollTop = 0;
                window.addEventListener('scroll', function(e) {
                    if (Math.abs(window.scrollY - lastScrollTop) > 100) {
                        window.scrollTo(0, lastScrollTop);
                    } else {
                        lastScrollTop = window.scrollY;
                    }
                }, { passive: false });
                
                // Prevent unwanted focus changes that can cause jumps
                document.addEventListener('focusin', function(e) {
                    e.target.scrollIntoView = function() {};
                });
            """)
            
            self.logger.info("✅ UI stability settings applied")
            
        except Exception as e:
            self.logger.warning(f"Failed to apply UI stability settings: {e}")

    async def _apply_stealth_measures(self):
        """Apply additional stealth and anti-detection measures"""
        try:
            # Override webdriver property
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Override plugins
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # Override languages
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            # Override permissions
            await self.page.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to apply some stealth measures: {str(e)}")
    
    async def human_delay(self, min_delay: float = None, max_delay: float = None):
        """Add human-like delay"""
        min_delay = min_delay or self.config.automation.human_delay_min
        max_delay = max_delay or self.config.automation.human_delay_max
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def human_type(self, selector: str, text: str, clear_first: bool = True) -> bool:
        """Type text with human-like timing"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=10000)
            
            if clear_first:
                await element.click()
                await self.page.keyboard.press('Control+a')
                await asyncio.sleep(0.1)
            
            # Type with random delays
            for char in text:
                await element.type(char)
                delay = random.randint(
                    self.config.automation.typing_delay_min,
                    self.config.automation.typing_delay_max
                )
                await asyncio.sleep(delay / 1000)
            
            return True
            
        except Exception as e:
            log_error(e, f"human_type: {selector}")
            return False
    
    async def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """Safely click an element with multiple attempts"""
        selectors = [selector] if isinstance(selector, str) else selector
        
        for sel in selectors:
            try:
                # Wait for element
                element = await self.page.wait_for_selector(sel, timeout=timeout)
                
                # Scroll into view
                await element.scroll_into_view_if_needed()
                await self.human_delay(0.2, 0.5)
                
                # Click
                await element.click()
                await self.human_delay(0.5, 1.0)
                
                return True
                
            except Exception as e:
                self.logger.debug(f"Click attempt failed for {sel}: {str(e)}")
                continue
        
        return False
    
    async def wait_for_navigation(self, timeout: int = 30000) -> bool:
        """Wait for page navigation to complete"""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout)
            await self.human_delay(1, 2)
            return True
        except Exception as e:
            log_error(e, "wait_for_navigation")
            return False
    
    async def take_screenshot(self, name: str = None, full_page: bool = False) -> str:
        """Take screenshot for debugging"""
        try:
            # Check if page is initialized
            if self.page is None:
                self.logger.warning("⚠️ Cannot take screenshot - page is None (browser not initialized)")
                return ""
            
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"screenshot_{self.session_id}_{timestamp}"
            
            # Ensure .png extension
            if not name.endswith('.png'):
                name += '.png'
            
            screenshot_path = self.screenshots_dir / name
            
            await self.page.screenshot(
                path=str(screenshot_path),
                full_page=full_page
            )
            
            self.logger.debug(f"📸 Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            log_error(e, "take_screenshot")
            return ""
    
    async def execute_with_retry(self, func, *args, max_retries: int = None, **kwargs) -> Any:
        """Execute function with retry logic"""
        max_retries = max_retries or self.config.automation.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = self.config.automation.retry_delay * (2 ** attempt)
                    self.logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    log_error(e, f"execute_with_retry: {func.__name__}")
        
        raise last_error
    
    async def check_for_challenges(self) -> Dict[str, bool]:
        """Enhanced challenge detection with improved CAPTCHA and reCAPTCHA detection"""
        challenges = {
            'captcha': False,
            'two_factor': False,
            'email_verification': False,
            'account_blocked': False,
            'unusual_activity': False,
            'recaptcha': False,
            'speedbump_verification': False
        }
        
        try:
            page_content = await self.page.content()
            page_text = page_content.lower()
            current_url = await self.get_current_url()
            
            # PRIORITY 1: Enhanced CAPTCHA/reCAPTCHA Detection (check first as it's most common)
            await self._detect_captcha_challenges(challenges, page_text, current_url)
            
            # If CAPTCHA is detected, return immediately to handle it
            if challenges['captcha'] or challenges['recaptcha']:
                return challenges
            
            # PRIORITY 2: Check for 2FA (after CAPTCHA to avoid conflicts)
            await self._detect_two_factor_challenges(challenges, page_text, current_url)
            
            # If two-factor is detected, return immediately to avoid false positives
            if challenges['two_factor']:
                return challenges
            
            # PRIORITY 3: Check for email verification
            await self._detect_email_verification_challenges(challenges, page_text)
            
            # PRIORITY 4: Check for blocked account
            await self._detect_account_blocked_challenges(challenges, page_text)
            
            # PRIORITY 5: Check for unusual activity
            await self._detect_unusual_activity_challenges(challenges, page_text)
            
            # PRIORITY 6: Check for speedbump verification (Google's "আমি বুঝি" popup)
            await self._detect_speedbump_verification(challenges, page_text, current_url)
            
        except Exception as e:
            log_error(e, "check_for_challenges")
        
        return challenges
    
    async def _detect_captcha_challenges(self, challenges: Dict[str, bool], page_text: str, current_url: str):
        """Enhanced CAPTCHA and reCAPTCHA detection with strict validation"""
        try:
            # Normal password page URLs that should NOT be considered CAPTCHA
            normal_password_urls = [
                'accounts.google.com/v3/signin/identifier',
                'accounts.google.com/signin/identifier',
                'accounts.google.com/v3/signin/password',
                'accounts.google.com/signin/password',
                'accounts.google.com/signin/v2/identifier',
                'accounts.google.com/signin/v2/password',
                'accounts.google.com/v3/signin/challenge/pwd',  # Normal password challenge page
                'accounts.google.com/signin/challenge/pwd'      # Normal password challenge page
            ]
            
            # Check if this is a normal password page
            is_normal_password_page = any(url_pattern in current_url for url_pattern in normal_password_urls)
            
            # Text-based CAPTCHA indicators (more specific)
            captcha_text_indicators = [
                'i\'m not a robot', 'im not a robot',
                'verify you\'re human', 'verify youre human',
                'confirm you\'re not a robot', 'confirm youre not a robot',
                'prove you\'re human', 'prove youre human'
            ]
            
            # Strong CAPTCHA text indicators (these alone can trigger detection)
            strong_captcha_indicators = [
                'recaptcha', 'captcha'
            ]
            
            # URL-based CAPTCHA indicators (specific challenge URLs only)
            captcha_url_patterns = [
                'accounts.google.com/v3/signin/challenge/recaptcha',
                'accounts.google.com/signin/challenge/recaptcha',
                'accounts.google.com/v3/signin/challenge/captcha',
                'accounts.google.com/signin/challenge/captcha'
            ]
            
            # Check different types of indicators
            text_captcha_detected = any(indicator in page_text.lower() for indicator in captcha_text_indicators)
            strong_text_detected = any(indicator in page_text.lower() for indicator in strong_captcha_indicators)
            url_captcha_detected = any(pattern in current_url for pattern in captcha_url_patterns)
            
            # Element-based detection for reCAPTCHA
            element_captcha_detected = await self._detect_captcha_elements()
            
            # Detailed logging for debugging
            self.logger.info(f"🔍 CAPTCHA Detection Analysis:")
            self.logger.info(f"   Current URL: {current_url}")
            self.logger.info(f"   Is normal password page: {is_normal_password_page}")
            self.logger.info(f"   Text indicators found: {text_captcha_detected}")
            self.logger.info(f"   Strong text indicators found: {strong_text_detected}")
            self.logger.info(f"   URL patterns found: {url_captcha_detected}")
            self.logger.info(f"   Element detection: {element_captcha_detected}")
            
            # STRICT DETECTION LOGIC:
            # 1. If it's a normal password page, don't detect CAPTCHA unless very strong evidence
            # 2. Require multiple indicators OR strong single indicator
            if is_normal_password_page:
                # For normal password pages, require very strong evidence
                captcha_detected = (element_captcha_detected and (strong_text_detected or url_captcha_detected))
                self.logger.info(f"   Normal password page - strict check: {captcha_detected}")
            else:
                # For other pages, require at least 2 indicators OR 1 strong indicator
                indicator_count = sum([text_captcha_detected, url_captcha_detected, element_captcha_detected])
                captcha_detected = (indicator_count >= 2) or strong_text_detected or url_captcha_detected
                self.logger.info(f"   Other page - indicator count: {indicator_count}, detected: {captcha_detected}")
            
            # Set challenge flags
            challenges['captcha'] = captcha_detected
            challenges['recaptcha'] = captcha_detected and (element_captcha_detected or 'recaptcha' in page_text.lower())
            
            if challenges['captcha'] or challenges['recaptcha']:
                self.logger.warning(f"🤖 CAPTCHA/reCAPTCHA CONFIRMED - Text: {text_captcha_detected}, Strong: {strong_text_detected}, URL: {url_captcha_detected}, Element: {element_captcha_detected}")
            else:
                self.logger.info(f"✅ No CAPTCHA detected - continuing with normal flow")
                
        except Exception as e:
            log_error(e, "_detect_captcha_challenges")
    
    async def _detect_captcha_elements(self) -> bool:
        """Detect CAPTCHA elements on the page with enhanced selectors"""
        try:
            # Enhanced reCAPTCHA element selectors
            recaptcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[title*="recaptcha"]',
                'iframe[title*="reCAPTCHA"]',
                'iframe[name*="recaptcha"]',
                '.g-recaptcha',
                '#g-recaptcha',
                '[data-sitekey]',
                'div[class*="recaptcha"]',
                'div[id*="recaptcha"]',
                'div[data-recaptcha]',
                'script[src*="recaptcha"]',
                'div.recaptcha-checkbox-border',
                'div.recaptcha-checkbox-checkmark',
                'div[role="presentation"][style*="recaptcha"]'
            ]
            
            # Enhanced "I'm not a robot" checkbox selectors
            robot_checkbox_selectors = [
                'input[type="checkbox"][aria-label*="not a robot"]',
                'input[type="checkbox"][aria-label*="not robot"]',
                'input[type="checkbox"][title*="not a robot"]',
                'input[type="checkbox"][title*="not robot"]',
                'span:has-text("I\'m not a robot")',
                'span:has-text("Im not a robot")',
                'span:has-text("I am not a robot")',
                'label:has-text("I\'m not a robot")',
                'label:has-text("Im not a robot")',
                'label:has-text("I am not a robot")',
                'div:has-text("I\'m not a robot")',
                'div:has-text("Im not a robot")',
                '.recaptcha-checkbox',
                '#recaptcha-checkbox',
                '.recaptcha-checkbox-border',
                '.recaptcha-checkbox-checkmark',
                'div[role="checkbox"][aria-label*="not a robot"]',
                'div[role="checkbox"][aria-label*="not robot"]'
            ]
            
            # Enhanced CAPTCHA image selectors
            captcha_image_selectors = [
                'img[src*="captcha"]',
                'img[alt*="captcha"]',
                'img[alt*="CAPTCHA"]',
                'img[title*="captcha"]',
                'img[title*="CAPTCHA"]',
                'canvas[id*="captcha"]',
                'canvas[class*="captcha"]',
                'div[class*="captcha-image"]',
                'div[id*="captcha-image"]',
                'div[class*="captcha-container"]',
                'div[id*="captcha-container"]',
                'img[src*="challenge"]',
                'img[alt*="challenge"]',
                'div[class*="challenge-image"]'
            ]
            
            # Google-specific verification selectors (ONLY for actual CAPTCHA challenges)
            google_verification_selectors = [
                # REMOVED: 'div[data-identifier="TL"]' - Too broad, can appear on normal pages
                # REMOVED: 'div[jsname="B34EJ"]' - Too broad, can appear on normal pages
                # REMOVED: 'div[jsname="Njthtb"]' - This is a normal password form element, not CAPTCHA
                'div[data-challenge-ui="challenge"]',
                'div[aria-label*="captcha"]',           # More specific to CAPTCHA
                'div[aria-label*="recaptcha"]',         # More specific to reCAPTCHA
                'form[data-challenge-ui]',
                'div[class*="captcha-challenge"]',      # More specific to CAPTCHA challenges
                'div[id*="captcha-challenge"]'          # More specific to CAPTCHA challenges
            ]
            
            # Cloudflare and other CAPTCHA providers
            other_captcha_selectors = [
                'div[class*="cf-challenge"]',     # Cloudflare
                'div[id*="cf-challenge"]',        # Cloudflare
                'div[class*="hcaptcha"]',         # hCaptcha
                'div[id*="hcaptcha"]',            # hCaptcha
                'iframe[src*="hcaptcha"]',        # hCaptcha iframe
                'div[class*="turnstile"]',        # Cloudflare Turnstile
                'div[id*="turnstile"]',           # Cloudflare Turnstile
                'div[class*="captcha-widget"]',   # Generic CAPTCHA widget
                'div[id*="captcha-widget"]'       # Generic CAPTCHA widget
            ]
            
            # Check for any reCAPTCHA elements (must be visible)
            for selector in recaptcha_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    # Check if element is actually visible
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 reCAPTCHA element detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 reCAPTCHA element found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 reCAPTCHA element visibility check failed: {selector}")
            
            # Check for robot checkbox elements (must be visible)
            for selector in robot_checkbox_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 'I'm not a robot' checkbox detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 Robot checkbox found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 Robot checkbox visibility check failed: {selector}")
            
            # Check for CAPTCHA image elements (must be visible)
            for selector in captcha_image_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 CAPTCHA image detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 CAPTCHA image found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 CAPTCHA image visibility check failed: {selector}")
            
            # Check for Google-specific verification elements (must be visible)
            for selector in google_verification_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 Google verification challenge detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 Google verification found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 Google verification visibility check failed: {selector}")
            
            # Check for other CAPTCHA providers (must be visible)
            for selector in other_captcha_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 Third-party CAPTCHA detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 Third-party CAPTCHA found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 Third-party CAPTCHA visibility check failed: {selector}")
            
            self.logger.debug(f"🔍 No visible CAPTCHA elements found")
            return False
            
        except Exception as e:
            log_error(e, "_detect_captcha_elements")
            return False
    
    async def _detect_two_factor_challenges(self, challenges: Dict[str, bool], page_text: str, current_url: str):
        """Detect two-factor authentication challenges"""
        try:
            two_factor_indicators = [
                '2-step verification', 'two-step verification',
                'check your phone', 'enter the code', 'verification code',
                'authenticator app', 'phone number',
                'google sent a notification', 'sent a notification',
                'verify with your phone', 'verify using your phone'
            ]
            
            two_factor_url_patterns = [
                'accounts.google.com/v3/signin/challenge/totp',
                'accounts.google.com/signin/challenge/totp',
                'accounts.google.com/v3/signin/challenge/ipp',
                'accounts.google.com/signin/challenge/ipp'
            ]
            
            text_match = any(indicator in page_text for indicator in two_factor_indicators)
            url_match = any(pattern in current_url for pattern in two_factor_url_patterns)
            
            challenges['two_factor'] = text_match or url_match
            
            if challenges['two_factor']:
                self.logger.warning(f"📱 Two-factor authentication detected - Text: {text_match}, URL: {url_match}")
                
        except Exception as e:
            log_error(e, "_detect_two_factor_challenges")
    
    async def _detect_email_verification_challenges(self, challenges: Dict[str, bool], page_text: str):
        """Detect email verification challenges"""
        try:
            email_indicators = [
                'verify your email', 'check your email',
                'confirmation email', 'email verification',
                'sent you an email', 'check your inbox'
            ]
            
            challenges['email_verification'] = any(indicator in page_text for indicator in email_indicators)
            
            if challenges['email_verification']:
                self.logger.warning("📧 Email verification detected")
                
        except Exception as e:
            log_error(e, "_detect_email_verification_challenges")
    
    async def _detect_account_blocked_challenges(self, challenges: Dict[str, bool], page_text: str):
        """Detect account blocked challenges"""
        try:
            blocked_indicators = [
                'account suspended', 'account disabled',
                'account locked', 'access denied',
                'temporarily blocked', 'account restricted'
            ]
            
            challenges['account_blocked'] = any(indicator in page_text for indicator in blocked_indicators)
            
            if challenges['account_blocked']:
                self.logger.error("🚫 Account blocked/suspended detected")
                
        except Exception as e:
            log_error(e, "_detect_account_blocked_challenges")
    
    async def _detect_unusual_activity_challenges(self, challenges: Dict[str, bool], page_text: str):
        """Detect unusual activity challenges"""
        try:
            # Get current URL to check for successful login redirects
            current_url = await self.get_current_url()
            
            # URLs that indicate successful login (NOT unusual activity)
            successful_login_urls = [
                'myaccount.google.com',
                'console.cloud.google.com',
                'accounts.google.com/ManageAccount',
                'accounts.google.com/b/0/ManageAccount'
            ]
            
            # Check if we're on a successful login page
            is_successful_login = any(url_pattern in current_url for url_pattern in successful_login_urls)
            
            if is_successful_login:
                # This is a successful login redirect, not unusual activity
                challenges['unusual_activity'] = False
                self.logger.info(f"✅ Successful login detected - URL: {current_url}")
                return
            
            # Only check for unusual activity text if we're not on a successful login page
            activity_indicators = [
                'unusual activity', 'suspicious activity',
                'security alert', 'unusual sign-in activity'
            ]
            
            challenges['unusual_activity'] = any(indicator in page_text for indicator in activity_indicators)
            
            if challenges['unusual_activity']:
                self.logger.warning("⚠️ Unusual activity detected")
                
        except Exception as e:
            log_error(e, "_detect_unusual_activity_challenges")
    
    async def _detect_speedbump_verification(self, challenges: Dict[str, bool], page_text: str, current_url: str):
        """Detect Google speedbump verification popup (গুরুত্বপূর্ণ তথ্য popup with আমি বুঝি button)"""
        try:
            # Check for speedbump URL patterns
            speedbump_url_patterns = [
                'accounts.google.com/speedbump',
                'accounts.google.com/v3/signin/speedbump',
                'accounts.google.com/signin/speedbump',
                'gaplustos'  # Common in speedbump URLs
            ]
            
            # Check for Bengali text indicators
            bengali_indicators = [
                'আমি বুঝি',  # "I understand" in Bengali
                'গুরুত্বপূর্ণ তথ্য',  # "Important information" in Bengali
                'আপনার অ্যাকাউন্ট',  # "Your account" in Bengali
                'নিরাপত্তা',  # "Security" in Bengali
                'যাচাইকরণ'  # "Verification" in Bengali
            ]
            
            # Check for English text indicators (fallback)
            english_indicators = [
                'important information',
                'account security',
                'verification required',
                'continue to your account',
                'i understand',
                'understand and continue'
            ]
            
            # URL-based detection
            url_match = any(pattern in current_url for pattern in speedbump_url_patterns)
            
            # Text-based detection (Bengali first, then English)
            bengali_text_match = any(indicator in page_text for indicator in bengali_indicators)
            english_text_match = any(indicator in page_text for indicator in english_indicators)
            
            # Combined detection
            challenges['speedbump_verification'] = url_match or bengali_text_match or english_text_match
            
            if challenges['speedbump_verification']:
                self.logger.warning(f"🚨 Speedbump verification detected - URL: {url_match}, Bengali: {bengali_text_match}, English: {english_text_match}")
                self.logger.info(f"   Current URL: {current_url}")
                
        except Exception as e:
            log_error(e, "_detect_speedbump_verification")
    
    async def handle_speedbump_verification(self) -> bool:
        """Handle speedbump verification by clicking 'আমি বুঝি' (I understand) button"""
        try:
            self.logger.info("🔄 Attempting to handle speedbump verification...")
            
            # Button selectors for "আমি বুঝি" / "I understand" button
            understand_button_selectors = [
                # Bengali text selectors
                'button:has-text("আমি বুঝি")',
                'input[value="আমি বুঝি"]',
                'a:has-text("আমি বুঝি")',
                
                # English text selectors (fallback)
                'button:has-text("I understand")',
                'button:has-text("Understand")',
                'button:has-text("Continue")',
                'input[value="I understand"]',
                'input[value="Continue"]',
                
                # Generic selectors based on common patterns
                'button[type="submit"]',
                'input[type="submit"]',
                'button[data-action="continue"]',
                'button[data-action="understand"]',
                
                # Google-specific selectors
                'div[role="button"]:has-text("আমি বুঝি")',
                'div[role="button"]:has-text("I understand")',
                'span:has-text("আমি বুঝি")',
                'span:has-text("I understand")'
            ]
            
            # Try to click the understand button
            for selector in understand_button_selectors:
                try:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        # Check if button is visible
                        if await locator.first.is_visible(timeout=2000):
                            self.logger.info(f"✅ Found understand button: {selector}")
                            await locator.first.click()
                            await self.human_delay(1, 2)
                            
                            # Wait for navigation or page change
                            try:
                                await self.page.wait_for_load_state("networkidle", timeout=10000)
                            except:
                                pass
                            
                            self.logger.info("✅ Successfully clicked understand button")
                            return True
                        else:
                            self.logger.debug(f"Button found but not visible: {selector}")
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
            self.logger.warning("⚠️ Could not find or click understand button")
            return False
            
        except Exception as e:
            log_error(e, "handle_speedbump_verification")
            return False
    
    async def handle_download(self, download_trigger_func, expected_filename: str = None) -> Optional[str]:
        """Handle file download with proper waiting"""
        try:
            # Start waiting for download
            async with self.page.expect_download() as download_info:
                await download_trigger_func()
            
            download = await download_info.value
            
            # Generate filename if not provided
            if not expected_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                suggested_filename = download.suggested_filename
                expected_filename = f"{timestamp}_{suggested_filename}"
            
            # Save download
            download_path = self.downloads_dir / expected_filename
            await download.save_as(str(download_path))
            
            self.logger.info(f"📥 File downloaded: {download_path}")
            return str(download_path)
            
        except Exception as e:
            log_error(e, "handle_download")
            return None
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.logger.info("🧹 Browser cleanup completed")
            
        except Exception as e:
            log_error(e, "cleanup")
    
    def generate_project_name(self, email: str) -> str:
        """Generate a unique project name (4-30 characters)"""
        # Extract username from email
        username = email.split('@')[0]
        
        # Clean username (remove special characters)
        clean_username = ''.join(c for c in username if c.isalnum())
        
        # Generate random suffix (6 characters)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Calculate available space for username
        # Format: "gmail-oauth-{username}-{suffix}"
        # "gmail-oauth-" = 12 chars, "-" = 1 char, suffix = 6 chars
        # Total fixed chars = 19, so username can be max 11 chars (30 - 19 = 11)
        max_username_length = 11
        clean_username = clean_username[:max_username_length]
        
        # Create project name
        project_name = f"gmail-oauth-{clean_username}-{suffix}"
        
        # Final safety check - if still too long, use shorter format
        if len(project_name) > 30:
            # Fallback to just "gmail-oauth-{suffix}" (18 chars)
            project_name = f"gmail-oauth-{suffix}"
        
        # Ensure minimum length (4 chars)
        if len(project_name) < 4:
            project_name = f"gmail-{suffix}"
        
        return project_name.lower()
    
    async def get_current_url(self) -> str:
        """Get current page URL"""
        try:
            return self.page.url
        except Exception:
            return ""
    
    async def get_page_title(self) -> str:
        """Get current page title"""
        try:
            return await self.page.title()
        except Exception:
            return ""
    
    async def save_screenshot(self, page: Page, name: str) -> Optional[str]:
        """Save screenshot for debugging"""
        try:
            screenshot_path = self.screenshots_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {str(e)}")
            return None
    
    async def write_file_async(self, file_path: Path, content: str) -> bool:
        """Write file with async support if available"""
        try:
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            else:
                # Fallback to synchronous write
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {str(e)}")
            return False