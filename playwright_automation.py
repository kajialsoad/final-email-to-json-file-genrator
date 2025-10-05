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
        """Check for various challenges (CAPTCHA, 2FA, etc.)"""
        challenges = {
            'captcha': False,
            'two_factor': False,
            'email_verification': False,
            'account_blocked': False,
            'unusual_activity': False
        }
        
        try:
            page_content = await self.page.content()
            page_text = page_content.lower()
            current_url = await self.get_current_url()
            
            # PRIORITY 1: Check for 2FA FIRST (before CAPTCHA to avoid false positives)
            two_factor_indicators = [
                '2-step verification', 'two-step verification',
                'check your phone', 'verify it\'s you',
                'enter the code', 'verification code',
                'authenticator app', 'phone number',
                'google sent a notification'
            ]
            
            # Also check URL pattern for two-factor verification
            two_factor_url_patterns = [
                'accounts.google.com/v3/signin/challenge',
                'accounts.google.com/signin/challenge',
                'challenge'
            ]
            
            # Check text indicators
            text_match = any(indicator in page_text for indicator in two_factor_indicators)
            # Check URL patterns
            url_match = any(pattern in current_url for pattern in two_factor_url_patterns)
            
            challenges['two_factor'] = text_match or url_match
            
            # If two-factor is detected, return immediately to avoid false CAPTCHA detection
            if challenges['two_factor']:
                return challenges
            
            # PRIORITY 2: Check for CAPTCHA (only if not two-factor)
            captcha_indicators = [
                'captcha', 'recaptcha', 'i\'m not a robot',
                'verify you\'re human'
                # Removed 'security check' as it's too broad and causes false positives
            ]
            challenges['captcha'] = any(indicator in page_text for indicator in captcha_indicators)
            
            # PRIORITY 3: Check for email verification
            email_indicators = [
                'verify your email', 'check your email',
                'confirmation email', 'email verification'
            ]
            challenges['email_verification'] = any(indicator in page_text for indicator in email_indicators)
            
            # PRIORITY 4: Check for blocked account
            blocked_indicators = [
                'account suspended', 'account disabled',
                'account locked', 'access denied',
                'temporarily blocked'
            ]
            challenges['account_blocked'] = any(indicator in page_text for indicator in blocked_indicators)
            
            # PRIORITY 5: Check for unusual activity (but not if it's two-factor)
            activity_indicators = [
                'unusual activity', 'suspicious activity',
                'security alert'
                # Removed 'verify it\'s you' as it's handled in two-factor detection
            ]
            challenges['unusual_activity'] = any(indicator in page_text for indicator in activity_indicators)
            
        except Exception as e:
            log_error(e, "check_for_challenges")
        
        return challenges
    
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
        """Generate a unique project name"""
        # Extract username from email
        username = email.split('@')[0]
        
        # Clean username (remove special characters)
        clean_username = ''.join(c for c in username if c.isalnum())
        
        # Generate random suffix
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Create project name
        project_name = f"gmail-oauth-{clean_username}-{suffix}"
        
        # Ensure it meets Google Cloud naming requirements
        if len(project_name) > 30:
            project_name = f"gmail-oauth-{suffix}"
        
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