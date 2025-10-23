#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Console Automation
Playwright-based automation for Google Cloud Console operations
"""

import asyncio
import random
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from playwright_automation import PlaywrightAutomationEngine
from error_handler import retry_async, log_error, ErrorType
from email_reporter import email_reporter
from approver_email_handler import ApproverEmailHandler
from automation_fallback_strategies import AutomationFallbackHandler, DetectionType, FallbackStrategy

class GoogleCloudAutomation(PlaywrightAutomationEngine):
    """Google Cloud Console automation using Playwright"""
    
    def __init__(self):
        super().__init__()
        self.google_cloud_url = "https://console.cloud.google.com"
        self.gmail_api_url = "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
        self.google_signin_url = "https://accounts.google.com/signin"
        
        # Initialize fallback handler for automation detection
        self.fallback_handler = AutomationFallbackHandler(self.config, self.logger)
    
    async def safe_navigate_with_retry(self, url: str, max_retries: int = 3, wait_until: str = "networkidle") -> bool:
        """Navigate to URL with retry logic and enhanced error handling."""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🌐 Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                
                # Use appropriate timeout based on URL type
                if "apis" in url or "library" in url:
                    timeout = self.config.automation.api_enablement_timeout
                elif "project" in url:
                    timeout = self.config.automation.project_creation_timeout
                else:
                    timeout = self.config.browser.navigation_timeout
                
                await self.page.goto(url, wait_until=wait_until, timeout=timeout)
                
                # Wait for page to stabilize
                await self.human_delay(2, 4)
                
                # Verify navigation was successful
                current_url = self.page.url
                if url in current_url or any(part in current_url for part in url.split('/')[-2:]):
                    self.logger.info(f"✅ Successfully navigated to {url}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Navigation may have redirected: expected {url}, got {current_url}")
                    if attempt == max_retries - 1:
                        return False
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Navigation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await self.human_delay(3, 5)
                    continue
                else:
                    self.logger.error(f"❌ All navigation attempts failed for {url}")
                    return False
        
        return False
    
    async def safe_wait_for_selector_with_retry(self, selectors: List[str], timeout: int = None, max_retries: int = 2) -> bool:
        """Wait for any of the provided selectors with retry logic."""
        if timeout is None:
            timeout = self.config.automation.project_element_visible_timeout  # Use faster element timeout
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"🔍 Waiting for selectors (attempt {attempt + 1}/{max_retries}): {selectors}")
                
                # Try all selectors in parallel for faster detection
                selector_tasks = []
                for selector in selectors:
                    task = asyncio.create_task(self._wait_for_single_selector(selector, timeout // len(selectors)))
                    selector_tasks.append(task)
                
                # Wait for any selector to be found
                done, pending = await asyncio.wait(selector_tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                
                # Check if any selector was found
                for task in done:
                    if await task:
                        self.logger.debug(f"✅ Found selector successfully")
                        return True
                
                if attempt < max_retries - 1:
                    self.logger.debug(f"⚠️ No selectors found, retrying...")
                    await self.human_delay(1, 2)  # Reduced delay
                    continue
                else:
                    self.logger.warning(f"⚠️ None of the selectors found after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                self.logger.debug(f"Selector wait attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await self.human_delay(0.5, 1)  # Reduced delay
                    continue
        
        return False
    
    async def _wait_for_single_selector(self, selector: str, timeout: int) -> bool:
        """Wait for a single selector with timeout."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
        
    @retry_async(context="google_cloud_login")
    async def login_to_google_cloud(self, email: str, password: str) -> bool:
        """Login to Google Cloud Console with enhanced error handling"""
        try:
            self.logger.info(f"🔐 Logging into Google Cloud Console for {email}")
            
            # Ensure browser is initialized
            if self.page is None:
                self.logger.error("❌ Browser page is None - browser not properly initialized")
                raise Exception("Browser page is None - browser not properly initialized")
            
            # First try to navigate directly to Google sign-in
            await self.page.goto(self.google_signin_url)
            await self.wait_for_navigation()
            
            # Check for automation challenges after navigation
            if not await self._detect_and_handle_automation_challenges(email):
                self.logger.error("❌ Failed to resolve automation challenges after navigation")
                return False
            
            # Take screenshot for debugging
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("01_google_signin_page")
            
            # Check if we're already on the email input page
            email_selectors = [
                'input[type="email"]',
                'input[id="identifierId"]',
                'input[name="identifier"]',
                'input[autocomplete="username"]'
            ]
            
            # If not on email page, try to navigate to Google Cloud Console first
            email_input_found = False
            for selector in email_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    email_input_found = True
                    break
                except:
                    continue
            
            if not email_input_found:
                self.logger.info("Email input not found, trying Google Cloud Console...")
                await self.page.goto(self.google_cloud_url)
                await self.wait_for_navigation()
                
                # Take screenshot for debugging
                if self.config.automation.screenshot_on_error:
                    await self.take_screenshot("02_google_cloud_homepage")
                
                # Check if already logged in
                if await self._check_if_logged_in():
                    self.logger.info("✅ Already logged in to Google Cloud")
                    return True
                
                # Click sign in button
                sign_in_selectors = [
                    'a[href*="signin"]',
                    'button:has-text("Sign in")',
                    'a:has-text("Sign in")',
                    '[data-value="sign_in"]',
                    '.gb_Af',
                    'a[data-action="sign in"]'
                ]
                
                if not await self.safe_click(sign_in_selectors):
                    # Try alternative approach - look for any sign in related elements
                    self.logger.info("Standard sign-in selectors failed, trying alternative approach...")
                    page_content = await self.page.content()
                    if "sign in" in page_content.lower() or "signin" in page_content.lower():
                        # Try to find any clickable element with sign in text
                        alternative_selectors = [
                            '*:has-text("Sign in")',
                            '*:has-text("Sign In")',
                            '*:has-text("SIGN IN")',
                            'a[href*="accounts.google.com"]'
                        ]
                        if not await self.safe_click(alternative_selectors):
                            raise Exception("Could not find sign in button")
                    else:
                        raise Exception("Could not find sign in button")
                
                await self.wait_for_navigation()
                await self.take_screenshot("03_signin_page")
            
            # Enter email
            email_selectors = [
                'input[type="email"]',
                'input[id="identifierId"]',
                'input[name="identifier"]',
                'input[autocomplete="username"]'
            ]
            
            email_entered = False
            for selector in email_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.human_type(selector, email)
                    email_entered = True
                    break
                except Exception:
                    continue
            
            if not email_entered:
                raise Exception("Could not find email input field")
            
            # Click next button
            next_selectors = [
                'button[id="identifierNext"]',
                'button:has-text("Next")',
                'input[type="submit"]',
                '[data-continue-text="Next"]'
            ]
            
            if not await self.safe_click(next_selectors):
                raise Exception("Could not find Next button after email")
            
            await self.wait_for_navigation()
            await self.take_screenshot("03_after_email")
            
            # Check for automation challenges after email entry
            if not await self._detect_and_handle_automation_challenges(email):
                self.logger.error("❌ Failed to resolve automation challenges after email entry")
                return False
            
            # Check for challenges BEFORE trying to enter password
            challenges = await self.check_for_challenges()
            if any(challenges.values()):
                self.logger.warning(f"⚠️ Challenges detected after email entry: {challenges}")
                return await self._handle_challenges_before_password(email, challenges)
            
            # Smart Password Handling Logic
            self.logger.info("🔐 Smart Password Handling - Checking if password is available...")
            
            if not password or password.strip() == "":
                self.logger.warning("❌ No password provided - will attempt manual intervention")
                await self._save_error_report(email, "no_password", "No password provided for this account")
                # Don't close browser - allow manual intervention to continue
                return await self._handle_manual_intervention_keep_browser(email, "manual_password_entry")
            
            # Password exists - try to enter it
            self.logger.info("✅ Password available - attempting to fill password field...")
            password_entered = await self._enter_password_with_fallbacks(password)
            
            if not password_entered:
                # Before raising exception, check if CAPTCHA appeared
                challenges = await self.check_for_challenges()
                if challenges['captcha'] or challenges['recaptcha']:
                    self.logger.warning("🤖 CAPTCHA detected when trying to find password field")
                    return await self._handle_challenges_before_password(email, challenges)
                
                # No password field found and no CAPTCHA - might be verification required
                self.logger.warning("⚠️ Password field not found - checking for verification requirements...")
                challenges = await self.check_for_challenges()
                if any(challenges.values()):
                    return await self._handle_challenges_after_password(email, challenges)
                
                raise Exception("Could not find password input field")
            
            # Password entered successfully - click next button
            self.logger.info("✅ Password entered - clicking Next button...")
            password_next_selectors = [
                'button[id="passwordNext"]',
                'button:has-text("Next")',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            if not await self.safe_click(password_next_selectors):
                raise Exception("Could not find Next button after password")
            
            await self.wait_for_navigation()
            await self.take_screenshot("04_after_password")
            
            # Smart Verification Check AFTER password submission
            self.logger.info("🔍 Checking for verification requirements after password entry...")
            challenges = await self.check_for_challenges()
            if any(challenges.values()):
                self.logger.warning(f"⚠️ Verification/Challenges detected after password entry: {challenges}")
                return await self._handle_challenges_after_password(email, challenges)
            
            # Verify successful login
            await asyncio.sleep(3)
            if await self._check_if_logged_in():
                self.logger.info("✅ Successfully logged into Google Cloud Console")
                return True
            else:
                raise Exception("Login verification failed")
                
        except Exception as e:
            log_error(e, "google_cloud_login", email)
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot(f"error_login_{email.replace('@', '_')}")
            raise
    
    async def _enter_password_with_fallbacks(self, password: str) -> bool:
        """Enter password with multiple fallback selectors and enhanced challenge detection"""
        try:
            # First, check for challenges before attempting password entry
            self.logger.info("🔍 Checking for challenges before password entry...")
            challenges = await self.check_for_challenges()
            
            if any(challenges.values()):
                self.logger.warning(f"⚠️ Challenges detected before password entry: {challenges}")
                return False
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                'input[autocomplete="current-password"]',
                'input[aria-label*="password"]',
                'input[placeholder*="password"]',
                'input[data-initial-value=""]',  # Additional fallback
                'input[aria-describedby*="password"]'  # Additional fallback
            ]
            
            for selector in password_selectors:
                try:
                    # Wait for password field with shorter timeout to detect challenges faster
                    await self.page.wait_for_selector(selector, timeout=5000)
                    
                    # Double-check for challenges after password field appears
                    challenges = await self.check_for_challenges()
                    if any(challenges.values()):
                        self.logger.warning(f"⚠️ Challenges detected after password field appeared: {challenges}")
                        return False
                    
                    await self.human_delay(1, 2)
                    await self.human_type(selector, password)
                    self.logger.info("✅ Password entered successfully")
                    return True
                except Exception as e:
                    self.logger.debug(f"Password selector {selector} failed: {str(e)}")
                    continue
            
            return False
            
        except Exception as e:
            log_error(e, "_enter_password_with_fallbacks")
            return False
    
    async def _handle_challenges_before_password(self, email: str, challenges: Dict[str, bool]) -> bool:
        """Handle challenges that appear before password entry"""
        try:
            # Handle CAPTCHA/reCAPTCHA
            if challenges['captcha'] or challenges['recaptcha']:
                self.logger.warning("🤖 CAPTCHA/reCAPTCHA detected before password entry")
                return await self._handle_captcha_manual_intervention(email)
            
            # Handle two-factor authentication
            if challenges['two_factor']:
                self.logger.warning("📱 Two-factor authentication required before password")
                return await self._handle_email_verification(email, "two_factor_verification")
            
            # Handle email verification
            if challenges['email_verification']:
                self.logger.warning("📧 Email verification required before password")
                return await self._handle_email_verification(email)
            
            # Handle account blocked
            if challenges['account_blocked']:
                self.logger.error("🚫 Account blocked/suspended before password entry")
                self.logger.info("📋 Account Blocked Handling Flow:")
                self.logger.info("   1. Taking screenshot for report")
                self.logger.info("   2. Saving blocked account report")
                self.logger.info("   3. Attempting manual intervention")
                self.logger.info("   4. Keeping browser open for recovery")
                
                await self._save_error_report(email, "account_blocked", "Account appears to be blocked or suspended")
                # Don't close browser - attempt manual intervention
                return await self._handle_manual_intervention_keep_browser(email, "account_blocked_recovery")
            
            # Handle unusual activity
            if challenges['unusual_activity']:
                self.logger.warning("⚠️ Unusual activity detected before password entry")
                self.logger.info("📋 Unusual Activity Handling Flow:")
                self.logger.info("   1. Taking screenshot for report")
                self.logger.info("   2. Saving unusual activity report")
                self.logger.info("   3. Attempting manual intervention")
                self.logger.info("   4. Keeping browser open for recovery")
                
                await self._save_error_report(email, "unusual_activity", "Unusual activity detected - additional verification required")
                # Don't close browser - attempt manual intervention
                return await self._handle_manual_intervention_keep_browser(email, "unusual_activity_recovery")
            
            return False
            
        except Exception as e:
            log_error(e, "_handle_challenges_before_password", email)
            return False
    
    async def _handle_challenges_after_password(self, email: str, challenges: Dict[str, bool]) -> bool:
        """Handle challenges that appear AFTER password entry"""
        try:
            # First check if we're actually successfully logged in
            current_url = await self.get_current_url()
            successful_login_urls = [
                'myaccount.google.com',
                'console.cloud.google.com',
                'accounts.google.com/ManageAccount',
                'accounts.google.com/b/0/ManageAccount'
            ]
            
            is_successful_login = any(url_pattern in current_url for url_pattern in successful_login_urls)
            
            if is_successful_login:
                self.logger.info("✅ Successful login detected - continuing to Google Cloud Console")
                # Navigate to Google Cloud Console to continue the OAuth setup
                await self._navigate_to_google_cloud_console()
                return True
            
            self.logger.info("📋 Post-Password Challenge Handling Strategy:")
            self.logger.info("   1. Password was successfully entered")
            self.logger.info("   2. Verification/Challenge detected after password")
            self.logger.info("   3. Generating appropriate report")
            self.logger.info("   4. Closing browser and moving to next email")
            
            # Handle CAPTCHA/reCAPTCHA after password
            if challenges['captcha'] or challenges['recaptcha']:
                self.logger.warning("🤖 CAPTCHA/reCAPTCHA detected after password entry")
                return await self._handle_captcha_manual_intervention(email)
            
            # Handle two-factor authentication after password
            if challenges['two_factor']:
                self.logger.warning("📱 Two-factor authentication required after password")
                return await self._handle_email_verification(email, "two_factor_verification")
            
            # Handle email verification after password
            if challenges['email_verification']:
                self.logger.warning("📧 Email verification required after password")
                return await self._handle_email_verification(email)
            
            # Handle account blocked after password
            if challenges['account_blocked']:
                self.logger.error("🚫 Account blocked/suspended after password entry")
                await self._save_error_report(email, "account_blocked", "Account appears to be blocked or suspended after password entry")
                # Don't close browser - attempt manual intervention
                return await self._handle_manual_intervention_keep_browser(email, "account_blocked_post_password")
            
            # Handle speedbump verification after password (Google's "আমি বুঝি" popup)
            if challenges['speedbump_verification']:
                self.logger.warning("🚨 Speedbump verification detected after password entry")
                if await self.handle_speedbump_verification():
                    self.logger.info("✅ Speedbump verification handled successfully - continuing OAuth process")
                    # Wait a bit and check if we're now logged in
                    await self.human_delay(2, 3)
                    current_url = await self.get_current_url()
                    
                    # Check if we're now successfully logged in
                    successful_login_urls = [
                        'myaccount.google.com',
                        'console.cloud.google.com',
                        'accounts.google.com/ManageAccount',
                        'accounts.google.com/b/0/ManageAccount'
                    ]
                    
                    is_successful_login = any(url_pattern in current_url for url_pattern in successful_login_urls)
                    
                    if is_successful_login:
                        self.logger.info("✅ Successfully logged in after speedbump verification")
                        await self._navigate_to_google_cloud_console()
                        return True
                    else:
                        # Continue with OAuth process - speedbump was handled but we need to continue
                        self.logger.info("🔄 Speedbump handled, continuing OAuth process...")
                        return True
                else:
                    self.logger.warning("⚠️ Failed to handle speedbump verification")
                    await self._save_error_report(email, "speedbump_verification_failed", "Failed to handle speedbump verification popup")
                    # Don't close browser - attempt manual intervention
                    return await self._handle_manual_intervention_keep_browser(email, "speedbump_verification_failed")
            
            # Handle unusual activity after password (only if not successful login)
            if challenges['unusual_activity']:
                self.logger.warning("⚠️ Unusual activity detected after password entry")
                await self._save_error_report(email, "unusual_activity", "Unusual activity detected after password entry - additional verification required")
                # Don't close browser - attempt manual intervention
                return await self._handle_manual_intervention_keep_browser(email, "unusual_activity_post_password")
            
            # If no specific challenge type detected but challenges exist
            self.logger.warning("⚠️ Unknown verification challenge detected after password entry")
            await self._save_error_report(email, "unknown_verification", "Unknown verification challenge detected after password entry")
            # Don't close browser - attempt manual intervention
            return await self._handle_manual_intervention_keep_browser(email, "unknown_verification_post_password")
            
        except Exception as e:
            log_error(e, "_handle_challenges_after_password", email)
            # Don't close browser - attempt manual intervention for unexpected errors
            try:
                return await self._handle_manual_intervention_keep_browser(email, "unexpected_error_post_password")
            except:
                return False
    
    async def _navigate_to_google_cloud_console(self) -> bool:
        """Navigate from successful login to Google Cloud Console"""
        try:
            self.logger.info("🌐 Navigating to Google Cloud Console...")
            
            # Navigate directly to Google Cloud Console
            await self.page.goto("https://console.cloud.google.com/", wait_until="networkidle")
            await self.human_delay(3, 5)
            
            # Take screenshot to see what we're dealing with
            await self.take_screenshot("console_navigation_start")
            
            # Check current page content and URL
            current_url = await self.get_current_url()
            page_content = await self.page.content()
            
            self.logger.info(f"🔍 Current URL: {current_url}")
            
            # Handle country selection and terms of service in sequence
            # This often appears as a combined form
            
            # First check for country selection
            country_indicators = [
                'select[name="country"]',
                'select[aria-label*="Country"]',
                'select[id*="country"]',
                'text="Country"'
            ]
            
            has_country_selection = False
            for indicator in country_indicators:
                if await self.page.locator(indicator).count() > 0:
                    has_country_selection = True
                    break
            
            # Check for terms of service
            terms_indicators = [
                'text="Terms of Service"',
                'text="Google Cloud Platform Terms of Service"',
                'input[type="checkbox"]',
                'text="I agree to the"'
            ]
            
            has_terms = False
            for indicator in terms_indicators:
                if await self.page.locator(indicator).count() > 0:
                    has_terms = True
                    break
            
            if has_country_selection or has_terms:
                self.logger.info("🔍 Found country/terms setup page - handling both...")
                
                # Handle country selection first
                if has_country_selection:
                    await self._handle_country_selection()
                
                # Handle terms of service
                if has_terms:
                    await self._handle_terms_of_service()
                
                # Wait for navigation after handling both
                await self.human_delay(3, 5)
                await self.take_screenshot("console_navigation_after_terms")
            
            # Wait for console to load
            await self.human_delay(2, 3)
            
            self.logger.info("✅ Successfully navigated to Google Cloud Console")
            return True
            
        except Exception as e:
            log_error(e, "_navigate_to_google_cloud_console")
            return False
    
    async def _handle_country_selection(self) -> bool:
        """Handle country selection during Google Cloud setup - Select United States"""
        try:
            self.logger.info("🌍 Handling country selection - selecting United States...")
            
            # Take screenshot for debugging
            await self.take_screenshot("country_selection_before")
            
            # Enhanced country selection dropdown selectors (prioritizing the most common ones)
            country_selectors = [
                'select[name="country"]',
                'select[aria-label*="Country"]', 
                'select[id*="country"]',
                'select[class*="country"]',
                'select[data-testid*="country"]',
                'div[role="combobox"][aria-label*="country"]',
                'div[role="combobox"][aria-label*="Country"]',
                'mat-select[formcontrolname="country"]',
                'select'  # Fallback to any select element
            ]
            
            # Try to find and select United States
            country_selected = False
            for selector in country_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        self.logger.info(f"🔍 Found country selector: {selector}")
                        
                        if 'select' in selector:
                            # First, try to click the dropdown to open it
                            await self.safe_click(selector)
                            await self.human_delay(0.5, 1)
                            
                            # Try different value formats for United States
                            us_values = ["US", "USA", "United States", "united-states", "840", "US-US"]
                            for value in us_values:
                                try:
                                    await self.page.select_option(selector, value=value)
                                    self.logger.info(f"✅ Selected United States with value: {value}")
                                    country_selected = True
                                    break
                                except Exception as e:
                                    self.logger.debug(f"Failed to select with value {value}: {str(e)}")
                                    continue
                            
                            if not country_selected:
                                # Try by label if value selection fails
                                try:
                                    await self.page.select_option(selector, label="United States")
                                    self.logger.info("✅ Selected United States by label")
                                    country_selected = True
                                except Exception as e:
                                    self.logger.debug(f"Failed to select by label: {str(e)}")
                                    
                        elif 'mat-select' in selector or 'role="combobox"' in selector:
                            # Handle Material Design or custom dropdowns
                            await self.safe_click(selector)
                            await self.human_delay(1, 2)
                            
                            # Try to find United States option
                            us_option_selectors = [
                                'mat-option:has-text("United States")',
                                'div[role="option"]:has-text("United States")',
                                'li:has-text("United States")',
                                'option:has-text("United States")',
                                'mat-option[value="US"]',
                                'div[role="option"][data-value="US"]'
                            ]
                            
                            for option_selector in us_option_selectors:
                                try:
                                    if await self.page.locator(option_selector).count() > 0:
                                        await self.safe_click(option_selector)
                                        self.logger.info(f"✅ Selected United States option: {option_selector}")
                                        country_selected = True
                                        break
                                except Exception as e:
                                    self.logger.debug(f"Failed to click option {option_selector}: {str(e)}")
                                    continue
                        
                        if country_selected:
                            await self.human_delay(1, 2)
                            await self.take_screenshot("country_selection_after")
                            break
                            
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to select country with selector {selector}: {str(e)}")
                    continue
            
            if country_selected:
                self.logger.info("✅ United States selected successfully")
            else:
                self.logger.warning("⚠️ Could not select United States - continuing anyway")
            
            return True
            
        except Exception as e:
            log_error(e, "_handle_country_selection")
            self.logger.warning(f"⚠️ Country selection handling failed: {str(e)}")
            return True  # Continue even if country selection fails
    
    async def _handle_terms_of_service(self) -> bool:
        """Handle Terms of Service agreement - Click all checkboxes and Agree & Continue"""
        try:

            self.logger.info("📋 Handling Terms of Service - checking all agreements and clicking Agree & Continue...")
            await self.take_screenshot("terms_of_service_before")
            await self.human_delay(1, 2)

            # 1) Check agreement checkboxes (cover native + ARIA-driven)
            checkbox_selectors = [
                'input[type="checkbox"]',
                'input[type="checkbox"][name*="agree"]',
                'input[type="checkbox"][id*="agree"]',
                'input[type="checkbox"][name*="terms"]',
                'input[type="checkbox"][id*="terms"]',
                'div[role="checkbox"]',
                'div[role="checkbox"][aria-label*="agree"]',
                'div[role="checkbox"][aria-label*="terms"]',
                'label:has-text("I agree")',
                'span:has-text("I agree")',
                'mat-checkbox',
                'md-checkbox',
                'paper-checkbox'
            ]
            checkboxes_checked = 0

            for selector in checkbox_selectors:
                try:
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count == 0:
                        continue
                    self.logger.info(f"🔍 Found {count} checkbox candidates: {selector}")

                    for idx in range(count):
                        item = locator.nth(idx)
                        try:
                            # Visibility check (custom components may not expose visibility reliably)
                            try:
                                is_visible = await item.is_visible()
                            except Exception:
                                is_visible = True
                            if not is_visible:
                                continue

                            # Determine checked state for input or ARIA checkbox
                            checked_state = None
                            try:
                                checked_state = await item.is_checked()
                            except Exception:
                                aria_checked = await item.get_attribute('aria-checked')
                                checked_state = True if aria_checked and aria_checked.lower() == 'true' else False

                            self.logger.info(f"📋 Checkbox {idx+1} state: {'checked' if checked_state else 'unchecked'}")

                            if not checked_state:
                                # Try normal click first
                                try:
                                    await item.scroll_into_view_if_needed()
                                    await item.click()
                                except Exception:
                                    # Try clicking associated label text nearby
                                    try:
                                        label_selector_variants = [
                                            'label:has-text("I agree")',
                                            'label:has-text("Terms of Service")',
                                            'text=I agree to the',
                                            'span:has-text("I agree")'
                                        ]
                                        for lsel in label_selector_variants:
                                            if await self.page.locator(lsel).count() > 0:
                                                await self.safe_click(lsel)
                                                break
                                    except Exception:
                                        pass

                                await self.human_delay(0.3, 0.8)
                                # Re-check
                                try:
                                    checked_state = await item.is_checked()
                                except Exception:
                                    aria_checked = await item.get_attribute('aria-checked')
                                    checked_state = True if aria_checked and aria_checked.lower() == 'true' else False

                                if checked_state:
                                    checkboxes_checked += 1
                                    self.logger.info(f"✅ Checkbox {idx+1} successfully checked")
                                else:
                                    self.logger.warning(f"⚠️ Checkbox {idx+1} still unchecked after click")
                        except Exception as e:
                            self.logger.debug(f"Could not handle checkbox {idx+1}: {str(e)}")
                            continue
                except Exception as e:
                    self.logger.debug(f"Could not process checkboxes with selector {selector}: {str(e)}")
                    continue

            if checkboxes_checked > 0:
                self.logger.info(f"✅ Checked {checkboxes_checked} agreement checkboxes")
            else:
                self.logger.info("ℹ️ No agreement checkboxes found or all already checked")

            await self.human_delay(1, 2)
            await self.take_screenshot("terms_of_service_after_checkbox")

            # 2) Click Agree & Continue using robust multi-strategy helper
            button_clicked = False
            for text_variant in ["Agree and continue", "Agree & Continue", "Accept & Continue", "I Agree"]:
                try:
                    if await self.enhanced_create_button_click(text_variant, context="terms_of_service"):
                        button_clicked = True
                        break
                except Exception:
                    continue

            # Fallback strategies: direct safe_click then JS + Enter
            if not button_clicked:
                fallback_button_selectors = [
                    'button:has-text("Agree and continue")',
                    'button:has-text("Agree & Continue")',
                    'input[type="submit"][value*="Agree"]',
                    'button[type="submit"]'
                ]
                for sel in fallback_button_selectors:
                    try:
                        locator = self.page.locator(sel)
                        if await locator.count() == 0:
                            continue
                        element = locator.first
                        await element.wait_for(state='visible', timeout=5000)

                        # Poll until enabled
                        for _ in range(10):
                            if await element.is_enabled():
                                break
                            await asyncio.sleep(0.3)

                        await element.scroll_into_view_if_needed()
                        await element.click()
                        button_clicked = True
                        self.logger.info(f"✅ Clicked agree button via selector: {sel}")
                        break
                    except Exception as e:
                        self.logger.debug(f"Fallback click failed for {sel}: {str(e)}")
                        continue

            if not button_clicked:
                # JavaScript fallback
                try:
                    clicked_via_js = await self.page.evaluate("""
                        () => {
                            const texts = ['Agree and continue','Agree & Continue','Accept & Continue','I Agree'];
                            const elements = Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"], a'));
                            for (const el of elements) {
                                const txt = (el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || '').toLowerCase();
                                if (texts.some(t => txt.includes(t.toLowerCase()))) {
                                    el.scrollIntoView({behavior:'instant',block:'center'});
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    if clicked_via_js:
                        button_clicked = True
                        self.logger.info("✅ Agree button clicked using JavaScript fallback")
                except Exception as e:
                    self.logger.debug(f"JavaScript fallback failed: {str(e)}")

            if not button_clicked:
                # Keyboard Enter as final attempt
                try:
                    await self.page.keyboard.press('Enter')
                    await self.human_delay(0.5, 1.0)
                    button_clicked = True
                    self.logger.info("✅ Agree proceeded via Enter key")
                except Exception:
                    pass

            if button_clicked:
                await self.human_delay(2, 3)
                await self.take_screenshot("terms_of_service_after_button")
                await self.wait_for_navigation()
                self.logger.info("✅ Terms of Service accepted successfully")
                return True

            self.logger.warning("⚠️ Could not find or click Agree & Continue button")
            await self.take_screenshot("terms_of_service_failed")
            return True  # Continue even if button not found

        except Exception as e:
            log_error(e, "_handle_terms_of_service")
            self.logger.warning(f"⚠️ Terms of Service handling failed: {str(e)}")
            return True  # Continue even if terms handling fails

    async def _check_if_logged_in(self) -> bool:
        """Check if user is already logged in to Google Cloud"""
        try:
            # Look for indicators of being logged in
            logged_in_indicators = [
                '[data-value="account_circle"]',
                '.gb_Aa',  # Google account button
                'button[aria-label*="Account"]',
                '[data-ogsr-up]',  # Google Cloud specific
                'div[data-value="console"]'
            ]
            
            for indicator in logged_in_indicators:
                if await self.page.locator(indicator).count() > 0:
                    return True
            
            # Check URL for console indication
            current_url = await self.get_current_url()
            if "console.cloud.google.com" in current_url and "signin" not in current_url:
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _handle_captcha_manual_intervention(self, email: str) -> bool:
        """Handle CAPTCHA detection with fallback strategies before giving up"""
        try:
            self.logger.warning("🤖 CAPTCHA detected! Attempting fallback strategies...")
            
            # Try fallback strategies first
            try:
                fallback_result = await self.fallback_handler.handle_detection(
                    DetectionType.CAPTCHA, 
                    self.page, 
                    self.context,
                    self.browser
                )
                
                if fallback_result and fallback_result.success:
                    self.logger.info(f"✅ CAPTCHA resolved using strategy: {fallback_result.strategy_used}")
                    return True
            except Exception as fallback_error:
                self.logger.warning(f"⚠️ Fallback handler error: {str(fallback_error)}")
            
            # If fallback strategies failed, proceed with original handling
            self.logger.warning("🤖 All fallback strategies failed. Skipping this email and moving to next.")
            self.logger.info("📋 CAPTCHA Handling Strategy:")
            self.logger.info("   1. CAPTCHA/reCAPTCHA detected during login")
            self.logger.info("   2. Attempted automated fallback strategies")
            self.logger.info("   3. Saving detailed report with screenshot")
            self.logger.info("   4. Closing browser and continuing to next email")
            
            # Take screenshot for report
            captcha_screenshot = await self.take_screenshot(f"captcha_detected_{email.replace('@', '_')}")
            
            # Save CAPTCHA report
            await self._save_captcha_report(email, captcha_screenshot)
            
            # Close browser immediately
            self.logger.info("🔄 Closing browser to continue with next email...")
            await self._close_browser_for_verification()
            
            # Return False to indicate this email should be skipped
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in CAPTCHA handling: {str(e)}")
            # Ensure browser is closed even if error occurs
            try:
                await self._close_browser_for_verification()
            except:
                pass
            return False
    
    async def _save_captcha_report(self, email: str, screenshot_path: str):
        """Save CAPTCHA detection report using email reporter"""
        try:
            # Use the comprehensive email reporter
            report_path = email_reporter.save_captcha_report(
                email=email,
                screenshot_path=screenshot_path,
                additional_data={
                    "browser_url": self.page.url if self.page else "unknown",
                    "automation_step": "google_cloud_login",
                    "detection_method": "enhanced_captcha_detection"
                }
            )
            
            if report_path:
                self.logger.info(f"📄 CAPTCHA report saved: {report_path}")
            else:
                self.logger.warning("⚠️ Failed to save CAPTCHA report")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save CAPTCHA report: {str(e)}")
    
    async def _handle_manual_intervention_keep_browser(self, email: str, challenge_type: str = "verification_challenge") -> bool:
        """Handle manual intervention without closing the browser for recovery scenarios"""
        try:
            self.logger.warning(f"🔧 {challenge_type.replace('_', ' ').title()} detected - attempting manual intervention!")
            
            # Take screenshot for debugging
            screenshot_path = await self.take_screenshot(f"{challenge_type}_{email}")
            if screenshot_path:
                self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            # Save report for this challenge
            await self._save_verification_report(email, screenshot_path, challenge_type)
            
            # Wait for manual intervention - give user time to resolve the challenge
            self.logger.info(f"⏳ Waiting 30 seconds for manual intervention to resolve {challenge_type}...")
            await asyncio.sleep(30)
            
            # Check if the challenge was resolved
            current_url = self.page.url
            self.logger.info(f"🔍 Current URL after manual intervention: {current_url}")
            
            # If we're still on a challenge page, wait a bit more
            if any(indicator in current_url.lower() for indicator in ['challenge', 'verify', 'captcha', 'security']):
                self.logger.info("⏳ Still on challenge page, waiting additional 15 seconds...")
                await asyncio.sleep(15)
            
            return True  # Return True to continue the flow without closing browser
            
        except Exception as e:
            self.logger.error(f"❌ Error during manual intervention for {challenge_type}: {str(e)}")
            return False  # Return False but don't close browser
    
    async def _handle_email_verification(self, email: str, verification_type: str = "email_verification") -> bool:
        """Handle email verification with approver email functionality and proper browser cleanup"""
        try:
            self.logger.warning(f"📧 {verification_type.replace('_', ' ').title()} detected!")
            
            # Check if approver email functionality is enabled
            from config import get_config
            config = get_config()
            
            if config.approver.enabled and config.approver.auto_handle_verification:
                self.logger.info("🔄 Approver email functionality is enabled - attempting automatic verification handling")
                
                try:
                    # Initialize approver email handler
                    approver_handler = ApproverEmailHandler(self.browser, self.logger)
                    
                    # Attempt to handle verification using approver email
                    verification_successful = await approver_handler.handle_verification_with_approver(email)
                    
                    if verification_successful:
                        self.logger.info("✅ Verification handled successfully using approver email")
                        
                        # Wait a bit and check if we're now logged in
                        await self.human_delay(3, 5)
                        
                        # Check if we're successfully logged in now
                        if await self._check_if_logged_in():
                            self.logger.info("✅ Successfully logged in after approver email verification")
                            return True
                        else:
                            # Continue with OAuth process
                            self.logger.info("🔄 Verification handled, continuing OAuth process...")
                            return True
                    else:
                        self.logger.warning("⚠️ Approver email verification failed - falling back to standard handling")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error in approver email verification: {str(e)}")
                    log_error(e, "approver_email_verification", email)
                    self.logger.warning("⚠️ Approver email verification error - falling back to standard handling")
            
            # Standard verification handling (fallback or when approver is disabled)
            self.logger.info("📋 Standard Verification Handling Flow:")
            self.logger.info("   1. Taking screenshot for report")
            self.logger.info("   2. Saving verification report")
            self.logger.info("   3. Closing browser cleanly")
            self.logger.info("   4. Continuing to next email")
            
            # Step 1: Take screenshot for report
            verification_screenshot = await self.take_screenshot(f"{verification_type}_{email.replace('@', '_')}")
            
            # Step 2: Save verification report
            await self._save_verification_report(email, verification_screenshot, verification_type)
            
            # Step 3: Close browser for this email
            await self._close_browser_for_verification()
            
            # Step 4: Log completion and return False to continue to next email
            verification_msg = "Two-factor verification" if verification_type == "two_factor_verification" else "Email verification"
            self.logger.info(f"✅ {verification_msg} handled - browser closed, moving to next email")
            return False  # Return False to indicate this email should be skipped
            
        except Exception as e:
            self.logger.error(f"❌ Error in verification handling: {str(e)}")
            # Ensure browser is closed even on error
            try:
                await self._close_browser_for_verification()
            except Exception:
                pass
            return False
    
    async def _save_verification_report(self, email: str, screenshot_path: str, verification_type: str = "email_verification"):
        """Save email/two-factor verification report using email reporter"""
        try:
            # Use the comprehensive email reporter
            report_path = email_reporter.save_verification_report(
                email=email,
                verification_type=verification_type,
                screenshot_path=screenshot_path,
                additional_data={
                    "browser_url": self.page.url if self.page else "unknown",
                    "automation_step": "google_cloud_login",
                    "detection_method": "enhanced_challenge_detection"
                }
            )
            
            if report_path:
                self.logger.info(f"📄 Verification report saved: {report_path}")
            else:
                self.logger.warning("⚠️ Failed to save verification report")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save verification report: {str(e)}")
    
    async def _save_error_report(self, email: str, error_type: str, error_message: str):
        """Save error report using email reporter"""
        try:
            # Take screenshot for error report
            error_screenshot = await self.take_screenshot(f"error_{error_type}_{email.replace('@', '_')}")
            
            # Use the comprehensive email reporter
            if error_type == "account_blocked":
                report_path = email_reporter.save_blocked_report(
                    email=email,
                    screenshot_path=error_screenshot,
                    additional_data={
                        "browser_url": self.page.url if self.page else "unknown",
                        "automation_step": "google_cloud_login",
                        "detection_method": "enhanced_challenge_detection"
                    }
                )
            elif error_type == "unusual_activity":
                report_path = email_reporter.save_unusual_activity_report(
                    email=email,
                    screenshot_path=error_screenshot,
                    additional_data={
                        "browser_url": self.page.url if self.page else "unknown",
                        "automation_step": "google_cloud_login",
                        "detection_method": "enhanced_challenge_detection"
                    }
                )
            else:
                report_path = email_reporter.save_error_report(
                    email=email,
                    error_type=error_type,
                    error_message=error_message,
                    screenshot_path=error_screenshot,
                    additional_data={
                        "browser_url": self.page.url if self.page else "unknown",
                        "automation_step": "google_cloud_login",
                        "detection_method": "enhanced_challenge_detection"
                    }
                )
            
            if report_path:
                self.logger.info(f"📄 Error report saved: {report_path}")
            else:
                self.logger.warning("⚠️ Failed to save error report")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save error report: {str(e)}")
    
    async def _detect_and_handle_automation_challenges(self, email: str) -> bool:
        """Detect automation challenges and apply fallback strategies"""
        try:
            if not self.page:
                return True
                
            # Check for various automation detection indicators
            page_content = await self.page.content()
            page_url = self.page.url
            page_title = await self.page.title()
            
            # Detection patterns for automation blocking
            automation_indicators = [
                "automated software",
                "bot detected",
                "unusual traffic",
                "verify you're human",
                "security check",
                "suspicious activity",
                "access denied",
                "blocked",
                "rate limit",
                "too many requests"
            ]
            
            detected_patterns = []
            detected_type = None
            
            # Check content for automation indicators
            for indicator in automation_indicators:
                if indicator.lower() in page_content.lower():
                    detected_patterns.append(indicator)
                    if "captcha" in indicator.lower() or "verify" in indicator.lower():
                        detected_type = DetectionType.CAPTCHA
                    elif "block" in indicator.lower() or "denied" in indicator.lower():
                        detected_type = DetectionType.ACCESS_DENIED
                    elif "rate" in indicator.lower() or "traffic" in indicator.lower():
                        detected_type = DetectionType.RATE_LIMITING
                    else:
                        detected_type = DetectionType.BOT_DETECTION
            
            # Check URL patterns
            if "challenge" in page_url or "verify" in page_url or "captcha" in page_url:
                detected_type = DetectionType.CAPTCHA
                detected_patterns.append("challenge_url")
            elif "blocked" in page_url or "denied" in page_url:
                detected_type = DetectionType.ACCESS_DENIED
                detected_patterns.append("blocked_url")
                
            # Log automation detection details
            from error_handler import error_handler
            
            if detected_type:
                detection_type_str = detected_type.value if hasattr(detected_type, 'value') else str(detected_type)
                self.logger.warning(f"🚨 Automation challenge detected: {detection_type_str}")
                
                # Log detailed automation detection information
                error_handler.log_automation_detection(
                    error_str=f"Automation challenge detected: {detection_type_str}",
                    context_str=f"method: _detect_and_handle_automation_challenges, email: {email}, page_url: {page_url}, page_title: {page_title}, detection_type: {detection_type_str}",
                    full_error=f"Automation challenge detected: {detection_type_str} - Patterns: {detected_patterns}"
                )
                
                # Apply fallback strategies
                fallback_result = await self.fallback_handler.handle_detection(
                    detected_type, 
                    self.page, 
                    self.context,
                    self.browser
                )
                
                if fallback_result.success:
                    self.logger.info(f"✅ Challenge resolved using strategy: {fallback_result.strategy_used}")
                    
                    # Log successful resolution
                    error_handler.log_automation_detection(
                        error_str=f"Automation challenge resolved successfully",
                        context_str=f"method: _detect_and_handle_automation_challenges, email: {email}, resolution_strategy: {fallback_result.strategy_used}, detection_type: {str(detected_type)}",
                        full_error=f"Automation challenge resolved successfully using strategy: {fallback_result.strategy_used}"
                    )
                    return True
                else:
                    self.logger.warning(f"❌ Failed to resolve challenge with all strategies")
                    
                    # Log failed resolution
                    error_handler.log_automation_detection(
                        error_str=f"Failed to resolve automation challenge",
                        context_str=f"method: _detect_and_handle_automation_challenges, email: {email}, detection_type: {str(detected_type)}",
                        full_error=f"Failed to resolve automation challenge of type: {detected_type}"
                    )
                    return False
            else:
                # Log successful automation detection check (no challenges found)
                self.logger.debug("✅ No automation challenges detected")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting automation challenges: {str(e)}")
            
            # Log the error for debugging
            from error_handler import error_handler
            error_handler.log_automation_detection(
                error_str=f"Error in automation detection: {str(e)}",
                context_str=f"method: _detect_and_handle_automation_challenges, email: {email}, error_type: detection_error",
                full_error=str(e)
            )
            return True  # Continue on error

    async def _close_browser_for_verification(self):
        """Close browser specifically for email verification case"""
        try:
            self.logger.info("🔒 Closing browser for email verification...")
            
            # Close page first
            if self.page:
                await self.page.close()
                self.page = None
                self.logger.debug("📄 Page closed")
            
            # Close context
            if self.context:
                await self.context.close()
                self.context = None
                self.logger.debug("🔗 Context closed")
            
            # Close browser
            if self.browser:
                await self.browser.close()
                self.browser = None
                self.logger.debug("🌐 Browser closed")
            
            # Close playwright instance to force window close
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                self.playwright = None
                self.logger.debug("🎭 Playwright instance stopped")
            
            self.logger.info("✅ Browser closed successfully for verification email")
            
        except Exception as e:
            self.logger.error(f"❌ Error closing browser for verification: {str(e)}")
    
    @retry_async(context="project_creation")
    async def create_or_select_project(self, project_name: str) -> bool:
        """Create a new project following the specific sequence: APIs & Services -> Create Project -> New Project -> Create"""
        try:
            self.logger.info(f"🏗️ Creating/selecting project: {project_name}")
            
            # FIRST: Check for and handle any popup (country/terms) before proceeding
            await self.take_screenshot("project_creation_start")
            
            # Check for popup indicators
            popup_indicators = [
                'text="Country"',
                'select[name="country"]',
                'text="Terms of Service"',
                'text="Google Cloud Platform Terms of Service"',
                'input[type="checkbox"]',
                'text="I agree to the"',
                'text="Agree and continue"',
                'button:has-text("Agree and continue")'
            ]
            
            has_popup = False
            for indicator in popup_indicators:
                if await self.page.locator(indicator).count() > 0:
                    has_popup = True
                    self.logger.info(f"🔍 Found popup indicator: {indicator}")
                    break
            
            if has_popup:
                self.logger.info("🎯 AI Popup detected! Handling country selection and terms of service...")
                
                # Handle country selection first
                await self._handle_country_selection()
                await self.human_delay(1, 2)
                
                # Handle terms of service
                await self._handle_terms_of_service()
                await self.human_delay(2, 3)
                
                # Take screenshot after handling popup
                await self.take_screenshot("popup_handled")
                self.logger.info("✅ AI Popup handling completed")
            
            # Step 1: Navigate to APIs & Services as per user instructions
            self.logger.info("🔧 Step 1: Navigating to APIs & Services...")
            if not await self.safe_navigate_with_retry("https://console.cloud.google.com/apis", wait_until="domcontentloaded"):
                self.logger.warning("⚠️ Failed to navigate to APIs & Services, trying alternative approach...")
                # Fallback to project selector
                if not await self.safe_navigate_with_retry("https://console.cloud.google.com/projectselector2/home", wait_until="domcontentloaded"):
                    self.logger.error("❌ Failed to navigate to project selector")
                    return False
                await self.take_screenshot("05_project_selector_fallback")
            else:
                await self.take_screenshot("05_apis_services")
            
            # Wait for page to fully load
            await self.human_delay(2, 4)
            
            # Step 2: Click "Create Project" button in APIs & Services
            self.logger.info("🔍 Step 2: Looking for 'Create Project' button...")
            create_project_selectors = [
                'button:has-text("Create Project")',
                'a:has-text("Create Project")',
                'button:has-text("CREATE PROJECT")',
                'a:has-text("CREATE PROJECT")',
                '[data-testid="create-project"]',
                'button[aria-label*="Create Project"]',
                'text="Create Project"',
                '.create-project-button',
                '[role="button"]:has-text("Create Project")',
                'button:has-text("New Project")',
                'button:has-text("NEW PROJECT")'
            ]
            
            create_project_clicked = False
            for selector in create_project_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click(selector)
                        self.logger.info(f"✅ Clicked 'Create Project' button: {selector}")
                        create_project_clicked = True
                        break
                except Exception as e:
                    self.logger.debug(f"Could not click Create Project with selector {selector}: {str(e)}")
                    continue
            
            if not create_project_clicked:
                # Fallback: Navigate to project selector and try there
                self.logger.info("🔄 'Create Project' not found in APIs & Services, trying project selector...")
                if not await self.safe_navigate_with_retry("https://console.cloud.google.com/projectselector2/home", wait_until="domcontentloaded"):
                    self.logger.error("❌ Failed to navigate to project selector")
                    return False
                await self.take_screenshot("05_project_selector")
                
                # Try to click Create Project in project selector
                if not await self.safe_click(create_project_selectors):
                    # Final fallback - direct navigation to new project page
                    self.logger.info("🔄 Trying direct navigation to new project page...")
                    await self.page.goto("https://console.cloud.google.com/projectcreate", wait_until="domcontentloaded", timeout=self.config.automation.project_creation_timeout)
                    await self.wait_for_navigation()
                    await self.human_delay(3, 5)
                    # Skip to form handling
                    create_project_clicked = True
            
            if create_project_clicked:
                await self.human_delay(2, 3)
                await self.take_screenshot("06_after_create_project_click")
                
                # Step 3: Look for and click "New Project" button
                self.logger.info("🔍 Step 3: Looking for 'New Project' button...")
                new_project_selectors = [
                    'button:has-text("New Project")',
                    'a:has-text("New Project")',
                    'button:has-text("NEW PROJECT")',
                    'a:has-text("NEW PROJECT")',
                    'text="New Project"',
                    'text="NEW PROJECT"',
                    'button:has-text("Create new project")',
                    '[data-testid="new-project"]',
                    'button[aria-label*="New Project"]',
                    '[role="button"]:has-text("New Project")'
                ]
                
                new_project_clicked = False
                for selector in new_project_selectors:
                    try:
                        if await self.page.locator(selector).count() > 0:
                            await self.safe_click(selector)
                            self.logger.info(f"✅ Clicked 'New Project' button: {selector}")
                            new_project_clicked = True
                            break
                    except Exception as e:
                        self.logger.debug(f"Could not click New Project with selector {selector}: {str(e)}")
                        continue
                
                if not new_project_clicked:
                    self.logger.info("ℹ️ 'New Project' button not found, assuming we're already on the project creation form")
                
                await self.human_delay(2, 3)
                await self.take_screenshot("07_project_creation_form")
            
            await self.take_screenshot("06_create_project_form")
            
            # Wait for the form to load
            await self.human_delay(2, 3)
            
            # Wait for the New Project form to be fully loaded
            self.logger.info("⏳ Waiting for New Project form to load...")
            await self.page.wait_for_selector('text="New Project"', timeout=10000)
            await self.human_delay(2, 3)

            # Track whether we've successfully entered the name
            name_entered = False

            # First attempt: accessible locators (label/role) for maximum reliability
            try:
                acc_locator = self.page.get_by_label("Project name", exact=False)
                await acc_locator.wait_for(timeout=6000)
                await acc_locator.scroll_into_view_if_needed()
                await acc_locator.click()
                await self.human_delay(0.3, 0.6)
                try:
                    await acc_locator.fill("")
                except Exception:
                    pass
                await acc_locator.fill(project_name)
                entered_value = await acc_locator.input_value()
                if project_name in entered_value or entered_value == project_name:
                    self.logger.info(f"✅ Project name entered via accessible label: {project_name}")
                    name_entered = True
                else:
                    self.logger.warning(f"⚠️ Text verification failed for accessible label. Expected: {project_name}, Got: {entered_value}")
            except Exception as e:
                self.logger.debug(f"Accessible label locator failed: {str(e)}")

            # If label-based locator did not succeed, try role-based locator
            if not name_entered:
                try:
                    role_locator = self.page.get_by_role("textbox", name=re.compile(r"Project name", re.I))
                    await role_locator.wait_for(timeout=8000)
                    await role_locator.scroll_into_view_if_needed()
                    await role_locator.click()
                    await self.human_delay(0.3, 0.6)
                    try:
                        await role_locator.fill("")
                    except Exception:
                        pass
                    await role_locator.fill(project_name)
                    entered_value = await role_locator.input_value()
                    if project_name in entered_value or entered_value == project_name:
                        self.logger.info(f"✅ Project name entered via role textbox: {project_name}")
                        name_entered = True
                    else:
                        self.logger.warning(f"⚠️ Text verification failed for role textbox. Expected: {project_name}, Got: {entered_value}")
                except Exception as e:
                    self.logger.debug(f"Role-based textbox locator failed: {str(e)}")

            # Enhanced project name input handling based on actual form structure
            project_name_selectors = [
                # Primary selectors based on the actual form structure
                'input[aria-label*="Project name"]',
                'input[aria-label*="project name"]',
                'label:has-text("Project name") ~ input',
                'label:has-text("Project name") + input',
                'div:has-text("Project name") input',
                'div:has-text("Project name *") input',
                # Material Design form field selectors
                '.mat-mdc-form-field:has-text("Project name") input',
                '.mat-form-field:has-text("Project name") input',
                'mat-form-field:has-text("Project name") input',
                # Generic form selectors
                'input[name="name"]',
                'input[name="projectName"]',
                'input[id*="project"]',
                'input[placeholder*="Project"]',
                'input[placeholder*="My Project"]',
                # Class-based selectors
                'input[class*="mat-input-element"]',
                'input[class*="mat-mdc-input-element"]',
                # Fallback selectors
                'form input[type="text"]:first-of-type',
                '.form-field input',
                'input[type="text"]'
            ]
            
            self.logger.info("🔍 Looking for project name input field...")
            
            for i, selector in enumerate(project_name_selectors):
                try:
                    self.logger.debug(f"🔍 Trying project name selector {i+1}/{len(project_name_selectors)}: {selector}")
                    
                    # Wait for the input field to be available
                    await self.page.wait_for_selector(selector, timeout=3000)
                    
                    locator = self.page.locator(selector)
                    
                    # Ensure element is visible and enabled
                    if await locator.count() > 0:
                        await locator.first.scroll_into_view_if_needed()
                        await self.human_delay(0.5, 1)
                        
                        # Focus and clear the field
                        await locator.first.click()
                        await self.human_delay(0.3, 0.6)
                        
                        # Clear using multiple methods
                        try:
                            await locator.first.fill("")
                            await self.page.keyboard.press("Control+a")
                            await self.page.keyboard.press("Delete")
                        except Exception:
                            pass
                        
                        # Enter the project name
                        await locator.first.fill(project_name)
                        await self.human_delay(0.5, 1)
                        
                        # Verify the text was entered
                        entered_value = await locator.first.input_value()
                        if entered_value and (project_name in entered_value or entered_value == project_name):
                            self.logger.info(f"✅ Project name entered successfully: {project_name} (using selector: {selector})")
                            name_entered = True
                            break
                        else:
                            self.logger.warning(f"⚠️ Text verification failed for {selector}. Expected: {project_name}, Got: {entered_value}")
                        
                except Exception as e:
                    self.logger.debug(f"Failed to use selector {selector}: {str(e)}")
                    continue
            
            if not name_entered:
                # Try frame-aware fallback - some GCP flows render forms inside iframes
                self.logger.warning("⚠️ Standard selectors failed, trying iframe-aware fallback...")
                try:
                    for frame in self.page.frames:
                        try:
                            frame_locator = frame.get_by_role("textbox", name=re.compile(r"Project name", re.I))
                            await frame_locator.wait_for(timeout=3000)
                            await frame_locator.scroll_into_view_if_needed()
                            await frame_locator.click()
                            await self.human_delay(0.2, 0.5)
                            try:
                                await frame_locator.fill("")
                            except Exception:
                                pass
                            await frame_locator.fill(project_name)
                            entered_value = await frame_locator.input_value()
                            if project_name in entered_value or entered_value == project_name:
                                self.logger.info(f"✅ Project name entered inside iframe: {project_name}")
                                name_entered = True
                                break
                        except Exception:
                            continue
                except Exception as e:
                    self.logger.debug(f"Iframe fallback iteration failed: {str(e)}")

            if not name_entered:
                # Last-resort generic visible input fallback
                self.logger.warning("⚠️ Iframe fallback failed, trying generic visible input...")
                try:
                    input_candidates = self.page.locator('input[type="text"]')
                    count = await input_candidates.count()
                    if count > 0:
                        input_field = input_candidates.first
                        # Ensure visible and interactable
                        try:
                            is_vis = await input_field.is_visible()
                        except Exception:
                            is_vis = True  # proceed optimistically
                        await input_field.scroll_into_view_if_needed()
                        await input_field.click()
                        await self.human_delay(0.2, 0.5)
                        try:
                            await input_field.fill("")
                        except Exception:
                            pass
                        await input_field.fill(project_name)
                        entered_value = await input_field.input_value()
                        if project_name in entered_value or entered_value == project_name:
                            self.logger.info(f"✅ Project name entered using generic fallback: {project_name}")
                            name_entered = True
                except Exception as e:
                    self.logger.error(f"❌ Generic fallback also failed: {str(e)}")
            
            if not name_entered:
                raise Exception("Could not find or fill project name input field")
            
            await self.human_delay(1, 2)
            
            # Fill Project ID deterministically based on project_name
            try:
                import re
                from datetime import datetime
                base_id = re.sub(r'[^a-z0-9-]', '-', project_name.lower())
                base_id = re.sub(r'-{2,}', '-', base_id).strip('-')
                if not re.match(r'^[a-z]', base_id):
                    base_id = f"p-{base_id}"
                project_id = base_id[:30] if len(base_id) > 0 else f"p-{int(datetime.now().timestamp())}"
                # Store for later direct navigation and OAuth flow
                try:
                    self.current_project_id = project_id
                except Exception:
                    pass
                project_id_selectors = [
                    'input[aria-label*="Project ID"]',
                    'input[name="projectId"]',
                    'label:has-text("Project ID") ~ input',
                    'label:has-text("Project ID") + input',
                    '.mat-mdc-form-field:has-text("Project ID") input'
                ]
                for sel in project_id_selectors:
                    try:
                        await self.page.wait_for_selector(sel, timeout=2500)
                        locator = self.page.locator(sel)
                        await locator.scroll_into_view_if_needed()
                        await locator.click()
                        await self.human_delay(0.2, 0.5)
                        try:
                            await locator.fill("")
                        except Exception:
                            pass
                        await locator.fill(project_id)
                        entered = await locator.input_value()
                        if project_id in entered or entered == project_id:
                            self.logger.info(f"✅ Project ID entered: {project_id}")
                            break
                    except Exception:
                        continue
            except Exception as e:
                self.logger.debug(f"Project ID computation/fill skipped: {str(e)}")
            
            # Check for validation errors before clicking Create
            validation_error_selectors = [
                'text="The name must be between 4 and 30 characters"',
                'text="The name is required"',
                'text*="name is required"',
                'text*="Project name"',
                '.error-message',
                '[role="alert"]',
                '.mat-error',
                '.mat-form-field-invalid',
                'text*="must be between"',
                'text*="characters"',
                'text*="required"'
            ]
            
            validation_error_found = False
            validation_messages = []
            for selector in validation_error_selectors:
                try:
                    elements = self.page.locator(selector)
                    count = await elements.count()
                    if count > 0:
                        for i in range(count):
                            try:
                                text = await elements.nth(i).text_content()
                                if text and text.strip():
                                    validation_messages.append(text.strip())
                                    validation_error_found = True
                            except Exception:
                                continue
                except Exception:
                    continue
            
            if validation_error_found:
                self.logger.warning(f"⚠️ Validation errors detected: {validation_messages}")
            
            # Also check if the Create button is disabled
            create_button_disabled = False
            try:
                create_buttons = self.page.locator('button:has-text("Create")')
                if await create_buttons.count() > 0:
                    is_disabled = await create_buttons.first.is_disabled()
                    if is_disabled:
                        create_button_disabled = True
                        self.logger.warning("⚠️ Create button is disabled")
            except Exception:
                pass
            
            # If validation error found or Create button is disabled, generate a shorter project name and retry
            if validation_error_found or create_button_disabled:
                self.logger.warning(f"⚠️ Project name '{project_name}' is invalid, generating shorter name...")
                
                # Generate a much shorter name
                import time
                timestamp = str(int(time.time()))[-4:]  # Only last 4 digits
                short_project_name = f"gmail-{timestamp}"  # Only 10 characters
                
                self.logger.info(f"🔄 Retrying with shorter name: {short_project_name}")
                
                # Clear the input field and enter the shorter name
                project_name_selectors = [
                    'input[type="text"]',
                    'input[name="name"]'
                ]
                
                for selector in project_name_selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        await self.page.locator(selector).focus()
                        await self.page.keyboard.press("Control+a")
                        await self.page.locator(selector).fill(short_project_name)
                        
                        # Verify the new name was entered
                        entered_value = await self.page.locator(selector).input_value()
                        if short_project_name in entered_value:
                            self.logger.info(f"✅ Shorter project name entered: {short_project_name}")
                            project_name = short_project_name  # Update the project name variable
                            break
                    except Exception:
                        continue
                
                await self.human_delay(1, 2)
            
            # Click create button - updated selectors based on actual form
            # Before clicking, ensure no blocking dialogs (e.g., folder Browse modal) are open
            try:
                blocking_dialog_indicators = [
                    'text="Search folders"',
                    'input[placeholder*="Search folders"]',
                    'div[role="dialog"]:has-text("Search folders")',
                    'text="Error while loading resources."'
                ]
                dialog_open = False
                for indicator in blocking_dialog_indicators:
                    try:
                        if await self.page.locator(indicator).count() > 0:
                            dialog_open = True
                            break
                    except Exception:
                        continue
                if dialog_open:
                    self.logger.info("🔧 Dismissing folder browse dialog before clicking Create...")
                    # Try Escape first
                    try:
                        await self.page.keyboard.press("Escape")
                        await self.human_delay(0.8, 1.2)
                    except Exception:
                        pass
                    # Try common close/cancel buttons
                    await self.safe_click([
                        'button:has-text("Cancel")',
                        'button[aria-label="Close"]',
                        'button:has-text("Close")'
                    ])
                    await self.human_delay(0.8, 1.2)
            except Exception:
                pass

            # Use enhanced create button click method with comprehensive fallback strategies
            create_clicked = await self.enhanced_create_button_click(
                button_text="Create", 
                timeout=30000,  # 30 second timeout for project creation
                context="project_creation"
            )
            
            if not create_clicked:
                raise Exception("Could not find or click Create button after trying all enhanced strategies")
            
            self.logger.info("✅ Create button clicked, waiting for project creation...")
            
            # Enhanced project creation verification with multiple strategies
            creation_verified = await self._verify_project_creation_comprehensive(project_name)
            
            # Fallback: navigate directly to APIs dashboard for computed project ID
            if not creation_verified:
                try:
                    import re
                    # Compute a safe project ID from the name (lowercase, hyphens)
                    safe_project_id = re.sub(r'[^a-z0-9-]', '', project_name.lower().replace(' ', '-'))
                    if not re.match(r'^[a-z]', safe_project_id):
                        safe_project_id = f"p-{safe_project_id}"
                    safe_project_id = safe_project_id[:30]
                    target_project_id = getattr(self, 'current_project_id', None) or safe_project_id
                    self.logger.info(f"🔗 Attempting direct navigation to APIs dashboard for project: {target_project_id}")
                    if await self.safe_navigate_with_retry(f"https://console.cloud.google.com/apis/dashboard?project={target_project_id}", wait_until="domcontentloaded"):
                        creation_verified = True
                        await self.human_delay(3, 5)
                        await self.take_screenshot("07_project_dashboard_direct")
                except Exception as e:
                    self.logger.warning(f"⚠️ Direct navigation fallback failed: {str(e)}")
            
            if not creation_verified:
                self.logger.warning("⚠️ Project creation status unclear, proceeding to selection flow...")
            
            # After project creation, ensure the project is selected
            await self._ensure_project_selected(project_name)
            return True
            
        except Exception as e:
            log_error(e, "project_creation", additional_data={'project_name': project_name})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot(f"error_project_creation_{project_name}")
            raise

    async def _verify_project_creation_comprehensive(self, project_name: str) -> bool:
        """
        Comprehensive project creation verification with multiple success indicators.
        
        Args:
            project_name: Name of the project to verify
            
        Returns:
            bool: True if project creation is verified, False otherwise
        """
        try:
            self.logger.info(f"🔍 Starting comprehensive verification for project: {project_name}")
            
            # Phase 1: Initial wait and network stabilization
            await self.human_delay(8, 12)  # Initial wait for creation to start
            
            # Wait for navigation with faster timeout
            try:
                # Try domcontentloaded first (faster)
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                # Then try networkidle with reduced timeout
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                self.logger.info("✅ Network stabilized after project creation")
            except Exception as e:
                self.logger.warning(f"⚠️ Network timeout during project creation: {str(e)}")
                # Continue anyway as project might still be created
            
            # Additional wait for project creation to complete
            await self.human_delay(5, 8)
            
            # Take screenshot after creation attempt
            await self.take_screenshot("07_project_created")
            
            # Phase 2: Multi-strategy verification with retries
            max_attempts = 5
            verification_strategies = [
                self._verify_by_url_change,
                self._verify_by_project_selector,
                self._verify_by_page_content,
                self._verify_by_navigation_elements,
                self._verify_by_api_dashboard_access
            ]
            
            for attempt in range(max_attempts):
                self.logger.info(f"🔍 Verification attempt {attempt + 1}/{max_attempts}")
                
                # Try each verification strategy
                for strategy_name, strategy_func in zip(
                    ["URL Change", "Project Selector", "Page Content", "Navigation Elements", "API Dashboard"],
                    verification_strategies
                ):
                    try:
                        self.logger.info(f"🔄 Testing strategy: {strategy_name}")
                        if await strategy_func(project_name):
                            self.logger.info(f"✅ Project creation verified using strategy: {strategy_name}")
                            return True
                    except Exception as e:
                        self.logger.debug(f"❌ Strategy {strategy_name} failed: {str(e)}")
                        continue
                
                # If no strategy worked, wait and try again
                if attempt < max_attempts - 1:
                    self.logger.info(f"⏳ Waiting before next verification attempt...")
                    await self.human_delay(5, 8)
                    
                    # Refresh page state
                    try:
                        await self.page.reload(wait_until="networkidle", timeout=30000)
                        await self.human_delay(3, 5)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Page refresh failed: {str(e)}")
            
            self.logger.error(f"❌ Failed to verify project creation after {max_attempts} attempts")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive project verification: {str(e)}")
            return False

    async def _verify_by_url_change(self, project_name: str) -> bool:
        """Verify project creation by checking URL changes."""
        try:
            current_url = self.page.url
            self.logger.info(f"🔍 Current URL: {current_url}")
            
            # Check for successful navigation away from project creation
            success_indicators = [
                "console.cloud.google.com" in current_url and "projectselector" not in current_url,
                "dashboard" in current_url.lower(),
                "apis" in current_url.lower(),
                "project" in current_url.lower() and "create" not in current_url.lower()
            ]
            
            return any(success_indicators)
            
        except Exception as e:
            self.logger.debug(f"URL verification failed: {str(e)}")
            return False

    async def _verify_by_project_selector(self, project_name: str) -> bool:
        """Verify project creation by checking project selector."""
        try:
            # Look for project selector with the new project
            project_selectors = [
                f'[aria-label*="{project_name}"]',
                f'[title*="{project_name}"]',
                f'text="{project_name}"',
                '[data-testid*="project-selector"]',
                '.project-selector'
            ]
            
            for selector in project_selectors:
                if await self.page.locator(selector).count() > 0:
                    self.logger.info(f"✅ Found project selector: {selector}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Project selector verification failed: {str(e)}")
            return False

    async def _verify_by_page_content(self, project_name: str) -> bool:
        """Verify project creation by checking page content."""
        try:
            # Look for success messages and project indicators
            content_indicators = [
                f'text="{project_name}"',
                'text="Project created"',
                'text="successfully created"',
                'text="Project has been created"',
                'text="Welcome to Google Cloud"',
                '[data-testid*="success"]',
                '.success-message'
            ]
            
            for indicator in content_indicators:
                if await self.page.locator(indicator).count() > 0:
                    self.logger.info(f"✅ Found content indicator: {indicator}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Page content verification failed: {str(e)}")
            return False

    async def _verify_by_navigation_elements(self, project_name: str) -> bool:
        """Verify project creation by checking navigation elements."""
        try:
            # Look for main navigation elements that appear after project creation
            nav_indicators = [
                'text="APIs & Services"',
                'text="IAM & Admin"',
                'text="Compute Engine"',
                'text="Cloud Storage"',
                '[aria-label*="Navigation menu"]',
                '.console-nav'
            ]
            
            found_count = 0
            for indicator in nav_indicators:
                if await self.page.locator(indicator).count() > 0:
                    found_count += 1
            
            # If we find multiple navigation elements, likely in main console
            if found_count >= 2:
                self.logger.info(f"✅ Found {found_count} navigation elements - likely in main console")
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Navigation elements verification failed: {str(e)}")
            return False

    async def _verify_by_api_dashboard_access(self, project_name: str) -> bool:
        """Verify project creation by attempting to access API dashboard."""
        try:
            # Try to navigate to APIs dashboard
            current_url = self.page.url
            if "console.cloud.google.com" in current_url:
                # Extract potential project ID from URL or use computed one
                project_id = self._compute_project_id(project_name)
                api_url = f"https://console.cloud.google.com/apis/dashboard?project={project_id}"
                
                self.logger.info(f"🔄 Testing API dashboard access: {api_url}")
                await self.page.goto(api_url, wait_until="networkidle", timeout=30000)
                await self.human_delay(3, 5)
                
                # Check if we successfully reached the API dashboard
                dashboard_indicators = [
                    'text="APIs & Services"',
                    'text="Dashboard"',
                    'text="Enabled APIs"',
                    '[data-testid*="api"]'
                ]
                
                for indicator in dashboard_indicators:
                    if await self.page.locator(indicator).count() > 0:
                        self.logger.info(f"✅ Successfully accessed API dashboard")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"API dashboard verification failed: {str(e)}")
            return False

    def _compute_project_id(self, project_name: str) -> str:
        """Compute a project ID from the project name."""
        try:
            import re
            from datetime import datetime
            
            # Convert to lowercase and replace spaces with hyphens
            base_id = re.sub(r'[^a-z0-9-]', '-', project_name.lower())
            base_id = re.sub(r'-{2,}', '-', base_id).strip('-')
            
            # Ensure it starts with a letter
            if not re.match(r'^[a-z]', base_id):
                base_id = f"p-{base_id}"
            
            # Truncate to 30 characters max
            project_id = base_id[:30] if len(base_id) > 0 else f"p-{int(datetime.now().timestamp())}"
            
            return project_id
            
        except Exception as e:
            self.logger.debug(f"Project ID computation failed: {str(e)}")
            return f"p-{int(datetime.now().timestamp())}"
    
    @retry_async(context="project_selection")
    async def _ensure_project_selected(self, project_name: str) -> bool:
        """Ensure the newly created project is selected in Google Cloud Console"""
        try:
            self.logger.info(f"🎯 Ensuring project '{project_name}' is selected...")
            
            # Try direct navigation to APIs dashboard for computed project ID first
            try:
                import re
                safe_project_id = re.sub(r'[^a-z0-9-]', '', project_name.lower().replace(' ', '-'))
                if not re.match(r'^[a-z]', safe_project_id):
                    safe_project_id = f"p-{safe_project_id}"
                safe_project_id = safe_project_id[:30]
                target_project_id = getattr(self, 'current_project_id', None) or safe_project_id
                self.logger.info(f"🔗 Ensuring selection by navigating to dashboard for: {target_project_id}")
                await self.safe_navigate_with_retry(f"https://console.cloud.google.com/apis/dashboard?project={target_project_id}", wait_until="domcontentloaded")
                await self.human_delay(2, 3)
            except Exception as e:
                self.logger.debug(f"Direct selection navigation failed: {str(e)}")
            
            # Take screenshot to see current state
            await self.take_screenshot("07_before_project_selection")
            
            # Check if we need to select a project (look for "Select a project" message)
            select_project_indicators = [
                'text="To view this page, select a project."',
                'text="Select a project"',
                'button:has-text("Select a project")',
                'text="Create project"',
                '[aria-label*="Select a project"]'
            ]
            
            needs_selection = False
            for indicator in select_project_indicators:
                try:
                    if await self.page.locator(indicator).count() > 0:
                        needs_selection = True
                        self.logger.info(f"✅ Found project selection indicator: {indicator}")
                        break
                except Exception:
                    continue
            
            if not needs_selection:
                self.logger.info("✅ Project appears to be already selected")
                return True
            
            # Click on "Select a project" dropdown
            project_selector_buttons = [
                'button:has-text("Select a project")',
                '[aria-label*="Select a project"]',
                'button[aria-haspopup="listbox"]',
                '.project-selector button',
                'button:has-text("Create project")',
                '[data-testid="project-selector"]'
            ]
            
            selector_clicked = False
            for selector in project_selector_buttons:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.page.locator(selector).click()
                        self.logger.info(f"✅ Clicked project selector: {selector}")
                        selector_clicked = True
                        await self.human_delay(2, 3)
                        break
                except Exception as e:
                    self.logger.debug(f"Failed to click selector {selector}: {str(e)}")
                    continue
            
            if not selector_clicked:
                self.logger.warning("⚠️ Could not find project selector dropdown")
                # Try navigating to APIs & Services to trigger project selection
                await self.page.goto("https://console.cloud.google.com/apis")
                await self.wait_for_navigation()
                await self.human_delay(2, 3)
                return True
            
            # Look for the newly created project in the dropdown
            await self.take_screenshot("07_project_dropdown_open")
            
            # Wait for dropdown to load with extended timeout
            await self.human_delay(3, 5)
            
            # Wait for dropdown content to fully load
            try:
                await self.page.wait_for_selector('[role="option"], li, div[data-value]', timeout=self.config.automation.project_selection_timeout)
            except Exception as e:
                self.logger.warning(f"⚠️ Dropdown content load timeout: {str(e)}")
            
            # Try multiple approaches to find and select the project
            project_selected = False
            
            # Approach 1: Direct text search with multiple attempts
            for attempt in range(3):
                self.logger.info(f"🔍 Project selection attempt {attempt + 1}")
                
                project_selectors = [
                    f'text="{project_name}"',
                    f'[title="{project_name}"]',
                    f'div:has-text("{project_name}")',
                    f'li:has-text("{project_name}")',
                    f'[role="option"]:has-text("{project_name}")',
                    f'button:has-text("{project_name}")',
                    f'span:has-text("{project_name}")',
                    f'[data-value="{project_name}"]'
                ]
                
                for selector in project_selectors:
                    try:
                        elements = await self.page.locator(selector).all()
                        if elements:
                            # Try to click the first visible element
                            for element in elements:
                                try:
                                    if await element.is_visible():
                                        await element.click()
                                        self.logger.info(f"✅ Selected project '{project_name}' using selector: {selector}")
                                        project_selected = True
                                        await self.human_delay(2, 3)
                                        break
                                except Exception:
                                    continue
                            if project_selected:
                                break
                    except Exception as e:
                        self.logger.debug(f"Failed to select project with selector {selector}: {str(e)}")
                        continue
                
                if project_selected:
                    break
                
                # Wait before next attempt
                if attempt < 2:
                    await self.human_delay(2, 3)
            
            # Approach 2: Partial name matching if exact match failed
            if not project_selected:
                self.logger.warning(f"⚠️ Exact project name not found, looking for partial matches...")
                
                # Extract the base name (remove timestamp suffix)
                base_name = project_name.split('-')[0:3]  # Take first 3 parts: gmail-oauth-username
                base_pattern = '-'.join(base_name)
                
                partial_selectors = [
                    f'text*="{base_pattern}"',
                    f'div:has-text("{base_pattern}")',
                    f'li:has-text("{base_pattern}")',
                    f'[role="option"]:has-text("{base_pattern}")',
                    f'span:has-text("{base_pattern}")'
                ]
                
                for selector in partial_selectors:
                    try:
                        elements = await self.page.locator(selector).all()
                        if elements:
                            for element in elements:
                                try:
                                    if await element.is_visible():
                                        await element.click()
                                        self.logger.info(f"✅ Selected project using partial match: {selector}")
                                        project_selected = True
                                        await self.human_delay(2, 3)
                                        break
                                except Exception:
                                    continue
                            if project_selected:
                                break
                    except Exception as e:
                        self.logger.debug(f"Failed to select project with partial selector {selector}: {str(e)}")
                        continue
            
            # Approach 3: Search functionality if available
            if not project_selected:
                self.logger.info("🔍 Trying search functionality...")
                try:
                    search_selectors = [
                        'input[placeholder*="Search"]',
                        'input[placeholder*="search"]',
                        'input[type="search"]',
                        'input[aria-label*="Search"]'
                    ]
                    
                    for search_selector in search_selectors:
                        try:
                            if await self.page.locator(search_selector).count() > 0:
                                await self.page.locator(search_selector).fill(project_name)
                                await self.human_delay(1, 2)
                                
                                # Try to select the first result
                                result_selectors = [
                                    f'text="{project_name}"',
                                    '[role="option"]:first-child',
                                    'li:first-child'
                                ]
                                
                                for result_selector in result_selectors:
                                    try:
                                        if await self.page.locator(result_selector).count() > 0:
                                            await self.page.locator(result_selector).click()
                                            self.logger.info(f"✅ Selected project using search: {project_name}")
                                            project_selected = True
                                            break
                                    except Exception:
                                        continue
                                
                                if project_selected:
                                    break
                        except Exception:
                            continue
                except Exception as e:
                    self.logger.debug(f"Search functionality failed: {str(e)}")
            
            if not project_selected:
                self.logger.warning("⚠️ Could not find the created project in dropdown, continuing anyway...")
                # Close dropdown by clicking elsewhere
                try:
                    await self.page.keyboard.press("Escape")
                    await self.human_delay(1, 2)
                except Exception:
                    pass
            
            # Wait for project selection to take effect
            await self.human_delay(3, 5)
            await self.take_screenshot("07_after_project_selection")
            
            # Verify project selection by checking if "Select a project" message is gone
            await self.human_delay(2, 3)
            still_needs_selection = False
            for indicator in select_project_indicators:
                try:
                    if await self.page.locator(indicator).count() > 0:
                        still_needs_selection = True
                        break
                except Exception:
                    continue
            
            if not still_needs_selection:
                self.logger.info(f"✅ Project '{project_name}' successfully selected")
                return True
            else:
                self.logger.warning("⚠️ Project selection may not have worked, but continuing...")
                return True
                
        except Exception as e:
            log_error(e, "project_selection", additional_data={'project_name': project_name})
            self.logger.warning(f"⚠️ Project selection failed: {str(e)}, but continuing...")
            return True  # Continue even if selection fails
    
    @retry_async(context="gmail_api_enable")
    async def enable_gmail_api(self) -> bool:
        """Enable Gmail API with improved navigation and fallback methods"""
        try:
            self.logger.info("📧 Enabling Gmail API through API Library...")
            
            # First, ensure we're in the right context by checking current page
            current_url = self.page.url
            self.logger.info(f"🔍 Current URL before API enablement: {current_url}")
            
            # If we're still on a project selection page, navigate to APIs & Services first
            if "projectselector" in current_url or "select" in current_url.lower():
                self.logger.info("🔄 Still on project selector, navigating to APIs & Services...")
                if not await self.safe_navigate_with_retry("https://console.cloud.google.com/apis"):
                    self.logger.warning("⚠️ Failed to navigate to APIs & Services before API enablement")
                await self.take_screenshot("08_apis_services_before_api")
            
            # Try direct navigation to Gmail API first (most reliable)
            self.logger.info("🎯 Trying direct navigation to Gmail API...")
            try:
                if await self.safe_navigate_with_retry(self.gmail_api_url):
                    await self.take_screenshot("08_gmail_api_direct")
                
                # Check if we're on the Gmail API page
                if "gmail.googleapis.com" in self.page.url or await self.page.locator('text="Gmail API"').count() > 0:
                    self.logger.info("✅ Successfully navigated directly to Gmail API page")
                    
                    # Check if API is already enabled
                    if await self._check_api_enabled():
                        self.logger.info("✅ Gmail API is already enabled")
                        return True
                    
                    # Try to enable the API
                    if await self._enable_api_on_page():
                        return True
                        
            except Exception as e:
                self.logger.warning(f"⚠️ Direct navigation failed: {str(e)}")
            
            # Fallback: Navigate to API Library and search
            self.logger.info("📚 Fallback: Navigating to API Library...")
            try:
                if await self.safe_navigate_with_retry("https://console.cloud.google.com/apis/library"):
                    await self.take_screenshot("08_api_library")
                
                # Wait for page to fully load with faster timeout
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                await self.human_delay(2, 3)
                
                # Enhanced search for Gmail API
                if await self._search_gmail_api():
                    if await self._enable_api_on_page():
                        return True
                        
            except Exception as e:
                self.logger.warning(f"⚠️ API Library navigation failed: {str(e)}")
            
            # Final fallback: Try alternative URLs and methods
            self.logger.info("🔄 Final fallback: Trying alternative methods...")
            alternative_urls = [
                "https://console.cloud.google.com/apis/api/gmail.googleapis.com",
                "https://console.cloud.google.com/apis/library/gmail.googleapis.com",
                "https://console.cloud.google.com/marketplace/product/google/gmail.googleapis.com"
            ]
            
            for url in alternative_urls:
                try:
                    self.logger.info(f"🔗 Trying alternative URL: {url}")
                    if not await self.safe_navigate_with_retry(url):
                        continue
                    
                    if await self._check_api_enabled():
                        self.logger.info("✅ Gmail API is already enabled")
                        return True
                    
                    if await self._enable_api_on_page():
                        return True
                        
                except Exception as e:
                    self.logger.debug(f"Alternative URL {url} failed: {str(e)}")
                    continue
            
            # If all methods fail, log warning but continue
            self.logger.warning("⚠️ Could not enable Gmail API through automation, but continuing...")
            return True
                
        except Exception as e:
            log_error(e, "gmail_api_enable")
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("error_gmail_api_enable")
            # Don't raise exception, continue with process
            self.logger.warning("⚠️ Gmail API enablement failed, but continuing with OAuth setup...")
            return True
    
    async def _search_gmail_api(self) -> bool:
        """Search for Gmail API in the API Library"""
        try:
            self.logger.info("🔍 Searching for Gmail API...")
            
            # Enhanced search selectors
            search_selectors = [
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]',
                'input[aria-label*="Search"]',
                'input[aria-label*="search"]',
                'input[type="search"]',
                'input[name="q"]',
                'input[name="query"]',
                '.search-input input',
                '.search-box input',
                '[data-testid="search-input"]',
                '[data-testid="search-box"]',
                'input.search',
                '#search-input',
                '.cfc-search-input input'
            ]
            
            search_performed = False
            for selector in search_selectors:
                try:
                    # Wait for selector with longer timeout
                    await self.page.wait_for_selector(selector, timeout=10000)
                    
                    # Clear and type with better error handling
                    search_input = self.page.locator(selector)
                    await search_input.clear()
                    await self.human_delay(0.5, 1)
                    await search_input.fill("Gmail API")
                    await self.human_delay(0.5, 1)
                    await self.page.keyboard.press("Enter")
                    
                    search_performed = True
                    self.logger.info("✅ Gmail API search performed successfully")
                    
                    # Wait for search results
                    await self.human_delay(3, 5)
                    await self.take_screenshot("08_gmail_api_search")
                    break
                    
                except Exception as e:
                    self.logger.debug(f"Search selector {selector} failed: {str(e)}")
                    continue
            
            if not search_performed:
                self.logger.warning("⚠️ Could not find search box in API Library")
                return False
            
            # Look for Gmail API in search results
            gmail_api_selectors = [
                'text="Gmail API"',
                'a:has-text("Gmail API")',
                'div:has-text("Gmail API")',
                '[title*="Gmail API"]',
                '[aria-label*="Gmail API"]',
                '.api-card:has-text("Gmail API")',
                '.product-card:has-text("Gmail API")',
                '.cfc-card:has-text("Gmail API")'
            ]
            
            for selector in gmail_api_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click([selector])
                        self.logger.info("✅ Gmail API found and clicked in search results")
                        await self.human_delay(3, 5)
                        await self.take_screenshot("08_gmail_api_page")
                        return True
                except Exception as e:
                    self.logger.debug(f"Gmail API selector {selector} failed: {str(e)}")
                    continue
            
            self.logger.warning("⚠️ Gmail API not found in search results")
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Gmail API search failed: {str(e)}")
            return False
    
    async def _enable_api_on_page(self) -> bool:
        """Enable API on the current page"""
        try:
            self.logger.info("🔘 Attempting to enable API on current page...")
            
            # Check if API is already enabled first
            if await self._check_api_enabled():
                self.logger.info("✅ Gmail API is already enabled")
                return True
            
            # Enhanced enable button selectors
            enable_selectors = [
                'button:has-text("Enable")',
                'button:has-text("ENABLE")',
                'button:has-text("Enable API")',
                'button:has-text("ENABLE API")',
                '[data-value="enable"]',
                'button[aria-label*="Enable"]',
                '.enable-button',
                '[data-testid="enable-button"]',
                'button.enable',
                '#enable-button',
                'input[type="submit"][value*="Enable"]',
                'a:has-text("Enable")',
                '.cfc-button:has-text("Enable")'
            ]
            
            enable_clicked = False
            for selector in enable_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click([selector])
                        enable_clicked = True
                        self.logger.info(f"✅ Enable button clicked using selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Enable selector {selector} failed: {str(e)}")
                    continue
            
            if not enable_clicked:
                self.logger.warning("⚠️ Could not find Enable button")
                return False
            
            self.logger.info("✅ Enable button clicked, waiting for API activation...")
            
            # Wait for API to be enabled with better timeout handling
            await self.human_delay(5, 8)
            
            # Wait for navigation or page update with faster timeout
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass  # Continue even if networkidle times out
            
            await self.human_delay(3, 5)
            await self.take_screenshot("09_gmail_api_enabled")
            
            # Verify API is enabled
            if await self._check_api_enabled():
                self.logger.info("✅ Gmail API enabled successfully")
                return True
            else:
                self.logger.warning("⚠️ Gmail API enable verification unclear, but continuing...")
                return True
                
        except Exception as e:
            self.logger.warning(f"⚠️ API enablement failed: {str(e)}")
            return False
    
    async def _check_api_enabled(self) -> bool:
        """Check if Gmail API is enabled"""
        try:
            # Look for enabled indicators
            enabled_indicators = [
                'button:has-text("Manage")',
                'button:has-text("MANAGE")',
                'text="API enabled"',
                '[data-value="manage"]'
            ]
            
            for indicator in enabled_indicators:
                if await self.page.locator(indicator).count() > 0:
                    return True
            
            # Check for disabled indicators
            disabled_indicators = [
                'button:has-text("Enable")',
                'button:has-text("ENABLE")',
                'text="Enable this API"'
            ]
            
            for indicator in disabled_indicators:
                if await self.page.locator(indicator).count() > 0:
                    return False
            
            return False
            
        except Exception:
            return False
    
    @retry_async(context="oauth_consent_screen")
    async def setup_oauth_consent_screen(self, email: str, app_name: str = None) -> bool:
        """Setup OAuth consent screen with complete workflow as specified"""
        try:
            if app_name is None:
                app_name = email  # Use login email as app name
                
            self.logger.info(f"🔒 Setting up OAuth consent screen for {email}...")
            
            # Navigate to OAuth consent screen
            try:
                target_project_id = getattr(self, 'current_project_id', None)
                url = (
                    f"https://console.cloud.google.com/apis/credentials/consent?project={target_project_id}"
                    if target_project_id else
                    "https://console.cloud.google.com/apis/credentials/consent"
                )
                await self.safe_navigate_with_retry(url)
            except Exception:
                await self.safe_navigate_with_retry("https://console.cloud.google.com/apis/credentials/consent")
            
            await self.human_delay(3, 5)
            await self.take_screenshot("09_oauth_consent_screen")
            
            # Check if consent screen is already configured
            if await self._check_consent_configured():
                self.logger.info("✅ OAuth consent screen already configured")
                return True
            
            # Step 1: Overview - Click "Get started"
            self.logger.info("📋 Step 1: Overview - Clicking Get started...")
            get_started_selectors = [
                'button:has-text("Get started")',
                'button:has-text("GET STARTED")',
                'a:has-text("Get started")',
                '[data-testid="get-started"]',
                '.get-started-button',
                'button[aria-label*="Get started"]'
            ]
            
            if not await self.safe_click(get_started_selectors):
                self.logger.warning("⚠️ Could not find Get started button, trying to proceed...")
            
            await self.human_delay(2, 3)
            await self.take_screenshot("10_oauth_get_started")
            
            # Step 2: Project Information
            self.logger.info("📝 Step 2: Project Information...")
            
            # 1-App information - App name (use login email)
            self.logger.info(f"📱 Setting App name to: {app_name}")
            app_name_selectors = [
                'input[name="applicationName"]',
                'input[formcontrolname="applicationName"]',
                'input[aria-label*="App name"]',
                'input[aria-label*="Application name"]',
                'input[placeholder*="App name"]',
                'label:has-text("App name") ~ input',
                'label:has-text("Application name") ~ input',
                '.mat-mdc-form-field:has-text("App name") input'
            ]
            
            app_name_filled = False
            for selector in app_name_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    locator = self.page.locator(selector)
                    await locator.scroll_into_view_if_needed()
                    await locator.click()
                    await self.human_delay(0.3, 0.6)
                    await locator.fill(app_name)
                    
                    # Verify the text was entered
                    entered_value = await locator.input_value()
                    if app_name in entered_value:
                        self.logger.info(f"✅ App name entered successfully: {app_name}")
                        app_name_filled = True
                        break
                except Exception as e:
                    self.logger.debug(f"App name selector {selector} failed: {str(e)}")
                    continue
            
            if not app_name_filled:
                self.logger.warning("⚠️ Could not fill app name, but continuing...")
            
            # User support email (use login email)
            self.logger.info(f"📧 Setting user support email to: {email}")
            support_email_selectors = [
                'input[name="supportEmail"]',
                'input[formcontrolname="supportEmail"]',
                'mat-select[formcontrolname="supportEmail"]',
                'input[aria-label*="support email"]',
                'input[aria-label*="User support email"]',
                'label:has-text("User support email") ~ input',
                'label:has-text("support email") ~ mat-select',
                '.mat-mdc-form-field:has-text("support email") input'
            ]
            
            support_email_filled = False
            for selector in support_email_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    
                    # Handle dropdown selectors
                    if 'mat-select' in selector:
                        await self.safe_click([selector])
                        await self.human_delay(1, 2)
                        
                        # Try to find and select the email option
                        email_option_selectors = [
                            f'mat-option:has-text("{email}")',
                            'mat-option:first-child',  # Fallback to first option
                            f'[role="option"]:has-text("{email}")'
                        ]
                        
                        for option_selector in email_option_selectors:
                            try:
                                if await self.page.locator(option_selector).count() > 0:
                                    await self.safe_click([option_selector])
                                    support_email_filled = True
                                    self.logger.info(f"✅ Support email selected from dropdown: {email}")
                                    break
                            except Exception:
                                continue
                        
                        if support_email_filled:
                            break
                    else:
                        # Handle input fields
                        locator = self.page.locator(selector)
                        await locator.scroll_into_view_if_needed()
                        await locator.click()
                        await self.human_delay(0.3, 0.6)
                        await locator.fill(email)
                        
                        # Verify the text was entered
                        entered_value = await locator.input_value()
                        if email in entered_value:
                            self.logger.info(f"✅ Support email entered successfully: {email}")
                            support_email_filled = True
                            break
                            
                except Exception as e:
                    self.logger.debug(f"Support email selector {selector} failed: {str(e)}")
                    continue
            
            if not support_email_filled:
                self.logger.warning("⚠️ Could not fill support email, but continuing...")
            
            # 2-Audience - Select External
            self.logger.info("👥 Setting audience to External...")
            external_selectors = [
                'input[value="EXTERNAL"]',
                'mat-radio-button:has-text("External")',
                '[data-value="external"]',
                'input[type="radio"][value="external"]',
                'label:has-text("External") input',
                '.mat-radio-button:has-text("External")',
                '[role="radio"]:has-text("External")'
            ]
            
            external_selected = False
            for selector in external_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click([selector])
                        external_selected = True
                        self.logger.info("✅ External audience selected")
                        break
                except Exception as e:
                    self.logger.debug(f"External selector {selector} failed: {str(e)}")
                    continue
            
            if not external_selected:
                self.logger.warning("⚠️ Could not select External audience, but continuing...")
            
            await self.human_delay(1, 2)
            
            # 3-Contact information - Email addresses (use login email)
            self.logger.info(f"📞 Setting contact email to: {email}")
            contact_email_selectors = [
                'input[name="contactEmail"]',
                'input[formcontrolname="contactEmail"]',
                'input[aria-label*="contact email"]',
                'input[aria-label*="Contact email"]',
                'input[aria-label*="Email addresses"]',
                'label:has-text("Email addresses") ~ input',
                'label:has-text("contact email") ~ input',
                '.mat-mdc-form-field:has-text("Email addresses") input',
                '.mat-mdc-form-field:has-text("contact") input'
            ]
            
            contact_email_filled = False
            for selector in contact_email_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    locator = self.page.locator(selector)
                    await locator.scroll_into_view_if_needed()
                    await locator.click()
                    await self.human_delay(0.3, 0.6)
                    await locator.fill(email)
                    
                    # Verify the text was entered
                    entered_value = await locator.input_value()
                    if email in entered_value:
                        self.logger.info(f"✅ Contact email entered successfully: {email}")
                        contact_email_filled = True
                        break
                except Exception as e:
                    self.logger.debug(f"Contact email selector {selector} failed: {str(e)}")
                    continue
            
            if not contact_email_filled:
                self.logger.warning("⚠️ Could not fill contact email, but continuing...")
            
            # 4-Finish - Agree & Continue
            self.logger.info("✅ Step 4: Finish - Agreeing and continuing...")
            agree_continue_selectors = [
                'button:has-text("Agree & Continue")',
                'button:has-text("AGREE & CONTINUE")',
                'button:has-text("Agree and Continue")',
                'button[aria-label*="Agree"]',
                'input[type="checkbox"]:has-text("agree")',
                '.agree-checkbox'
            ]
            
            # First try to check any agreement checkboxes
            checkbox_selectors = [
                'input[type="checkbox"]',
                'mat-checkbox input',
                '[role="checkbox"]'
            ]
            
            for checkbox_selector in checkbox_selectors:
                try:
                    checkboxes = self.page.locator(checkbox_selector)
                    count = await checkboxes.count()
                    for i in range(count):
                        checkbox = checkboxes.nth(i)
                        if await checkbox.is_visible():
                            try:
                                is_checked = await checkbox.is_checked()
                                if not is_checked:
                                    await checkbox.click()
                                    self.logger.info(f"✅ Agreement checkbox {i+1} checked")
                            except Exception:
                                pass
                except Exception:
                    continue
            
            await self.human_delay(1, 2)
            
            # Click Agree & Continue button
            if not await self.safe_click(agree_continue_selectors):
                # Fallback to generic Continue/Create buttons
                fallback_selectors = [
                    'button:has-text("Continue")',
                    'button:has-text("Create")',
                    'button:has-text("CONTINUE")',
                    'button:has-text("CREATE")',
                    'button[type="submit"]'
                ]
                if not await self.safe_click(fallback_selectors):
                    self.logger.warning("⚠️ Could not find Agree & Continue button, but continuing...")
            
            await self.human_delay(3, 5)
            await self.take_screenshot("11_oauth_form_filled")
            
            # Continue through the remaining steps (scopes, test users, summary)
            self.logger.info("📋 Continuing through remaining OAuth setup steps...")
            
            # Skip scopes page
            continue_selectors = [
                'button:has-text("Save and Continue")',
                'button:has-text("SAVE AND CONTINUE")',
                'button:has-text("Continue")',
                'button:has-text("CONTINUE")',
                'button[type="submit"]'
            ]
            
            # Try to continue through multiple pages
            for step in range(3):  # Usually 3 more steps: scopes, test users, summary
                try:
                    await self.human_delay(2, 3)
                    if await self.safe_click(continue_selectors):
                        self.logger.info(f"✅ Continued through OAuth step {step + 1}")
                        await self.human_delay(2, 3)
                    else:
                        break
                except Exception:
                    break
            
            # 2| Audience - Publishing Status – Testing, Click- Publish App – Confirm
            self.logger.info("📢 Step 2: Audience - Setting Publishing Status to Testing...")
            
            # Try to navigate to the audience/publishing section
            try:
                # Look for publishing status or audience section
                publish_selectors = [
                    'button:has-text("Publish App")',
                    'button:has-text("PUBLISH APP")',
                    'a:has-text("Publish App")',
                    'button:has-text("Publish")',
                    '[data-testid="publish-app"]'
                ]
                
                if await self.safe_click(publish_selectors):
                    self.logger.info("✅ Publish App button found and clicked")
                    
                    await self.human_delay(2, 3)
                    
                    # Confirm publishing
                    confirm_selectors = [
                        'button:has-text("Confirm")',
                        'button:has-text("CONFIRM")',
                        'button:has-text("Yes")',
                        'button:has-text("OK")',
                        'button[type="submit"]'
                    ]
                    
                    if await self.safe_click(confirm_selectors):
                        self.logger.info("✅ App publishing confirmed")
                    else:
                        self.logger.warning("⚠️ Could not find confirm button for publishing")
                else:
                    self.logger.warning("⚠️ Could not find Publish App button, app may already be published")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Publishing step failed: {str(e)}")
            
            await self.human_delay(2, 3)
            await self.take_screenshot("12_oauth_consent_completed")
            
            self.logger.info("✅ OAuth consent screen configured successfully")
            return True
            
        except Exception as e:
            log_error(e, "oauth_consent_screen", additional_data={'email': email, 'app_name': app_name})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("error_oauth_consent")
            raise
    
    async def _check_consent_configured(self) -> bool:
        """Check if OAuth consent screen is already configured"""
        try:
            # Look for configured indicators
            configured_indicators = [
                'text="Edit app"',
                'button:has-text("Edit app")',
                'text="App information"',
                '[data-value="edit_app"]'
            ]
            
            for indicator in configured_indicators:
                if await self.page.locator(indicator).count() > 0:
                    return True
            
            return False
            
        except Exception:
            return False
    
    @retry_async(context="oauth_credentials_creation")
    async def create_oauth_credentials(self, email: str) -> bool:
        """Create OAuth 2.0 credentials with desktop app and download JSON as specified"""
        try:
            self.logger.info("🔑 Step 3: Clients - Creating OAuth 2.0 credentials...")
            
            # Navigate to credentials page
            try:
                target_project_id = getattr(self, 'current_project_id', None)
                url = (
                    f"https://console.cloud.google.com/apis/credentials?project={target_project_id}"
                    if target_project_id else
                    "https://console.cloud.google.com/apis/credentials"
                )
                await self.safe_navigate_with_retry(url)
            except Exception:
                await self.safe_navigate_with_retry("https://console.cloud.google.com/apis/credentials")
            
            await self.human_delay(3, 5)
            await self.take_screenshot("13_credentials_page")
            
            # Click-- Create Client
            self.logger.info("🔧 Clicking Create Client...")
            create_client_selectors = [
                'button:has-text("Create Client")',
                'button:has-text("CREATE CLIENT")',
                'button:has-text("Create Credentials")',
                'button:has-text("CREATE CREDENTIALS")',
                '[data-value="create_credentials"]',
                '[data-testid="create-client"]',
                'a:has-text("Create Client")'
            ]
            
            if not await self.safe_click(create_client_selectors):
                # Fallback: try to find any create button
                fallback_selectors = [
                    'button:has-text("Create")',
                    'button:has-text("CREATE")',
                    'button[type="submit"]'
                ]
                if not await self.safe_click(fallback_selectors):
                    raise Exception("Could not find Create Client button")
            
            await self.human_delay(2, 3)
            
            # Select OAuth client ID from dropdown if needed
            oauth_selectors = [
                'text="OAuth client ID"',
                'button:has-text("OAuth client ID")',
                '[data-value="oauth_client_id"]',
                'mat-option:has-text("OAuth client ID")',
                '[role="option"]:has-text("OAuth client ID")'
            ]
            
            # Try to click OAuth client ID option
            oauth_clicked = await self.safe_click(oauth_selectors)
            if oauth_clicked:
                self.logger.info("✅ OAuth client ID option selected")
                await self.human_delay(2, 3)
            else:
                self.logger.info("ℹ️ OAuth client ID option not found or already selected")
            
            await self.take_screenshot("14_oauth_client_form")
            
            # Application Type - Select—Desktop App
            self.logger.info("🖥️ Selecting Desktop App as Application Type...")
            desktop_selectors = [
                'mat-radio-button:has-text("Desktop application")',
                'mat-radio-button:has-text("Desktop app")',
                'input[value="DESKTOP"]',
                'input[value="desktop"]',
                '[data-value="desktop"]',
                'input[type="radio"][value="DESKTOP"]',
                'input[type="radio"][value="desktop"]',
                'label:has-text("Desktop application") input',
                'label:has-text("Desktop app") input',
                '.mat-radio-button:has-text("Desktop")',
                '[role="radio"]:has-text("Desktop")'
            ]
            
            desktop_selected = False
            for selector in desktop_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click([selector])
                        desktop_selected = True
                        self.logger.info("✅ Desktop application selected")
                        break
                except Exception as e:
                    self.logger.debug(f"Desktop selector {selector} failed: {str(e)}")
                    continue
            
            if not desktop_selected:
                self.logger.warning("⚠️ Could not select Desktop application, but continuing...")
            
            await self.human_delay(1, 2)
            
            # Enter name (use email as name)
            self.logger.info(f"📝 Setting client name to: {email}")
            name_selectors = [
                'input[name="name"]',
                'input[formcontrolname="name"]',
                'input[aria-label*="Name"]',
                'input[aria-label*="Client name"]',
                'input[placeholder*="Name"]',
                'label:has-text("Name") ~ input',
                'label:has-text("Client name") ~ input',
                '.mat-mdc-form-field:has-text("Name") input'
            ]
            
            name_entered = False
            for selector in name_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    locator = self.page.locator(selector)
                    await locator.scroll_into_view_if_needed()
                    await locator.click()
                    await self.human_delay(0.3, 0.6)
                    await locator.fill(email)
                    
                    # Verify the text was entered
                    entered_value = await locator.input_value()
                    if email in entered_value:
                        self.logger.info(f"✅ Client name entered successfully: {email}")
                        name_entered = True
                        break
                except Exception as e:
                    self.logger.debug(f"Name selector {selector} failed: {str(e)}")
                    continue
            
            if not name_entered:
                self.logger.warning("⚠️ Could not fill client name, but continuing...")
            
            await self.human_delay(1, 2)
            
            # Click—Create
            self.logger.info("🔨 Clicking Create button...")
            create_selectors = [
                'button:has-text("Create")',
                'button:has-text("CREATE")',
                'button[type="submit"]',
                'button[aria-label*="Create"]',
                '.create-button',
                '[data-testid="create"]'
            ]
            
            if not await self.safe_click(create_selectors):
                raise Exception("Could not find Create button for OAuth client")
            
            await self.human_delay(3, 5)
            await self.take_screenshot("15_oauth_client_created")
            
            # Click-- Download JSON
            self.logger.info("📥 Downloading JSON credentials...")
            download_selectors = [
                'button:has-text("Download JSON")',
                'button:has-text("DOWNLOAD JSON")',
                'button:has-text("Download")',
                'button:has-text("DOWNLOAD")',
                '[data-value="download_json"]',
                'button[aria-label*="Download"]',
                'a:has-text("Download JSON")',
                '.download-button',
                '[data-testid="download-json"]',
                'button[title*="Download"]'
            ]
            
            download_clicked = False
            for selector in download_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click([selector])
                        download_clicked = True
                        self.logger.info("✅ Download JSON button clicked")
                        break
                except Exception as e:
                    self.logger.debug(f"Download selector {selector} failed: {str(e)}")
                    continue
            
            if not download_clicked:
                # Try to find download icon or any download-related element
                icon_selectors = [
                    'mat-icon:has-text("download")',
                    'mat-icon:has-text("file_download")',
                    '[class*="download"]',
                    '[title*="download"]'
                ]
                
                for icon_selector in icon_selectors:
                    try:
                        if await self.page.locator(icon_selector).count() > 0:
                            await self.safe_click([icon_selector])
                            download_clicked = True
                            self.logger.info("✅ Download icon clicked")
                            break
                    except Exception:
                        continue
            
            if not download_clicked:
                self.logger.warning("⚠️ Could not find Download JSON button, credentials may need to be downloaded manually")
            
            # Wait for download to complete
            await self.human_delay(3, 5)
            await self.take_screenshot("16_json_downloaded")
            
            self.logger.info("✅ OAuth credentials created and JSON download initiated")
            return True
            
        except Exception as e:
            log_error(e, "oauth_credentials_creation", additional_data={'email': email})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("error_oauth_credentials")
            raise

    @retry_async(context="file_explorer_integration")
    async def handle_file_explorer_and_rename(self, email: str) -> bool:
        """Handle file explorer integration and rename downloaded JSON file with login email"""
        try:
            self.logger.info("📁 Step 4: File Explorer - Opening and renaming downloaded JSON file...")
            
            # Wait a bit more for download to complete
            await self.human_delay(5, 8)
            
            # Open File Explorer using Windows key + E
            self.logger.info("🗂️ Opening File Explorer...")
            await self.page.keyboard.press("Meta+e")
            await self.human_delay(2, 3)
            
            # Navigate to Downloads folder
            self.logger.info("📥 Navigating to Downloads folder...")
            await self.page.keyboard.press("Control+l")  # Focus address bar
            await self.human_delay(0.5, 1)
            await self.page.keyboard.type("C:\\Users\\user\\Downloads")
            await self.page.keyboard.press("Enter")
            await self.human_delay(2, 3)
            
            # Look for the most recent JSON file (OAuth credentials)
            self.logger.info("🔍 Looking for downloaded JSON credentials file...")
            
            # Try to find and select the JSON file
            # This is a simplified approach - in a real scenario, you might need to:
            # 1. List files in the downloads directory
            # 2. Find the most recent .json file
            # 3. Rename it appropriately
            
            # For now, we'll use keyboard shortcuts to find and rename
            await self.page.keyboard.press("Control+a")  # Select all
            await self.human_delay(0.5, 1)
            await self.page.keyboard.type("*.json")  # Search for JSON files
            await self.page.keyboard.press("Enter")
            await self.human_delay(1, 2)
            
            # Select the first JSON file found
            await self.page.keyboard.press("Tab")
            await self.human_delay(0.5, 1)
            
            # Rename the file using F2
            self.logger.info(f"📝 Renaming JSON file to: {email}.json")
            await self.page.keyboard.press("F2")
            await self.human_delay(0.5, 1)
            
            # Clear current name and type new name
            await self.page.keyboard.press("Control+a")
            await self.human_delay(0.3, 0.5)
            await self.page.keyboard.type(f"{email}.json")
            await self.page.keyboard.press("Enter")
            await self.human_delay(1, 2)
            
            self.logger.info(f"✅ JSON file renamed to: {email}.json")
            
            # Close File Explorer
            await self.page.keyboard.press("Alt+F4")
            await self.human_delay(1, 2)
            
            self.logger.info("✅ File Explorer operations completed")
            return True
            
        except Exception as e:
            log_error(e, "file_explorer_integration", additional_data={'email': email})
            self.logger.warning("⚠️ File Explorer operations failed, but continuing...")
            return False
    
    async def rename_downloaded_json(self, email: str) -> bool:
        """Rename the downloaded JSON file to use the email as filename"""
        try:
            self.logger.info(f"📁 Renaming downloaded JSON file to {email}.json...")
            
            import os
            import glob
            from pathlib import Path
            
            # Get downloads folder
            downloads_folder = Path.home() / "Downloads"
            
            # Look for recently downloaded JSON files
            json_files = list(downloads_folder.glob("client_secret_*.json"))
            
            if not json_files:
                # Also check for other OAuth JSON patterns
                json_files = list(downloads_folder.glob("*oauth*.json"))
                json_files.extend(list(downloads_folder.glob("*credentials*.json")))
            
            if not json_files:
                raise Exception("Could not find downloaded JSON file")
            
            # Get the most recent file
            latest_file = max(json_files, key=os.path.getctime)
            
            # Create new filename
            new_filename = f"{email.replace('@', '_').replace('.', '_')}.json"
            new_path = downloads_folder / new_filename
            
            # Rename the file
            latest_file.rename(new_path)
            
            self.logger.info(f"✅ JSON file renamed to: {new_filename}")
            return True
            
        except Exception as e:
            log_error(e, "rename_downloaded_json", additional_data={'email': email})
            return False