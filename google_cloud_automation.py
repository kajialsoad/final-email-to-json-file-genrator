#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Cloud Console Automation
Playwright-based automation for Google Cloud Console operations
"""

import asyncio
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from playwright_automation import PlaywrightAutomationEngine
from error_handler import retry_async, log_error, ErrorType
from email_reporter import email_reporter
from approver_email_handler import ApproverEmailHandler

class GoogleCloudAutomation(PlaywrightAutomationEngine):
    """Google Cloud Console automation using Playwright"""
    
    def __init__(self):
        super().__init__()
        self.google_cloud_url = "https://console.cloud.google.com"
        self.gmail_api_url = "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
        self.google_signin_url = "https://accounts.google.com/signin"
        
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
            
            # Check for challenges BEFORE trying to enter password
            challenges = await self.check_for_challenges()
            if any(challenges.values()):
                self.logger.warning(f"⚠️ Challenges detected after email entry: {challenges}")
                return await self._handle_challenges_before_password(email, challenges)
            
            # Smart Password Handling Logic
            self.logger.info("🔐 Smart Password Handling - Checking if password is available...")
            
            if not password or password.strip() == "":
                self.logger.warning("❌ No password provided - closing browser and generating report")
                await self._save_error_report(email, "no_password", "No password provided for this account")
                await self._close_browser_for_verification()
                return False
            
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
                self.logger.info("   3. Closing browser cleanly")
                self.logger.info("   4. Continuing to next email")
                
                await self._save_error_report(email, "account_blocked", "Account appears to be blocked or suspended")
                await self._close_browser_for_verification()
                self.logger.info("✅ Account blocked handled - browser closed, moving to next email")
                return False
            
            # Handle unusual activity
            if challenges['unusual_activity']:
                self.logger.warning("⚠️ Unusual activity detected before password entry")
                self.logger.info("📋 Unusual Activity Handling Flow:")
                self.logger.info("   1. Taking screenshot for report")
                self.logger.info("   2. Saving unusual activity report")
                self.logger.info("   3. Closing browser cleanly")
                self.logger.info("   4. Continuing to next email")
                
                await self._save_error_report(email, "unusual_activity", "Unusual activity detected - additional verification required")
                await self._close_browser_for_verification()
                self.logger.info("✅ Unusual activity handled - browser closed, moving to next email")
                return False
            
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
                await self._close_browser_for_verification()
                self.logger.info("✅ Account blocked handled - browser closed, moving to next email")
                return False
            
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
                    await self._close_browser_for_verification()
                    self.logger.info("✅ Speedbump verification failed - browser closed, moving to next email")
                    return False
            
            # Handle unusual activity after password (only if not successful login)
            if challenges['unusual_activity']:
                self.logger.warning("⚠️ Unusual activity detected after password entry")
                await self._save_error_report(email, "unusual_activity", "Unusual activity detected after password entry - additional verification required")
                await self._close_browser_for_verification()
                self.logger.info("✅ Unusual activity handled - browser closed, moving to next email")
                return False
            
            # If no specific challenge type detected but challenges exist
            self.logger.warning("⚠️ Unknown verification challenge detected after password entry")
            await self._save_error_report(email, "unknown_verification", "Unknown verification challenge detected after password entry")
            await self._close_browser_for_verification()
            self.logger.info("✅ Unknown verification handled - browser closed, moving to next email")
            return False
            
        except Exception as e:
            log_error(e, "_handle_challenges_after_password", email)
            # Ensure browser is closed even if error occurs
            try:
                await self._close_browser_for_verification()
            except:
                pass
            return False
    
    async def _navigate_to_google_cloud_console(self) -> bool:
        """Navigate from successful login to Google Cloud Console"""
        try:
            self.logger.info("🌐 Navigating to Google Cloud Console...")
            
            # Navigate directly to Google Cloud Console
            await self.page.goto("https://console.cloud.google.com/", wait_until="networkidle")
            await self.human_delay(3, 5)
            
            # Check if we need to handle country selection or terms
            current_url = await self.get_current_url()
            
            # Handle country selection if present
            if "country" in current_url.lower() or await self.page.locator('select[name="country"]').count() > 0:
                await self._handle_country_selection()
            
            # Handle terms of service if present
            if "terms" in current_url.lower() or await self.page.locator('text="Terms of Service"').count() > 0:
                await self._handle_terms_of_service()
            
            # Wait for console to load
            await self.human_delay(2, 3)
            
            self.logger.info("✅ Successfully navigated to Google Cloud Console")
            return True
            
        except Exception as e:
            log_error(e, "_navigate_to_google_cloud_console")
            return False
    
    async def _handle_country_selection(self) -> bool:
        """Handle country selection during Google Cloud setup"""
        try:
            self.logger.info("🌍 Handling country selection...")
            
            # Look for country selection dropdown
            country_selectors = [
                'select[name="country"]',
                'select[aria-label*="Country"]',
                'select[data-testid*="country"]'
            ]
            
            for selector in country_selectors:
                if await self.page.locator(selector).count() > 0:
                    # Select United States
                    await self.page.select_option(selector, value="US")
                    self.logger.info("✅ Selected United States as country")
                    break
            
            # Look for continue button
            continue_selectors = [
                'button:has-text("Continue")',
                'button:has-text("Agree & Continue")',
                'input[type="submit"]'
            ]
            
            if await self.safe_click(continue_selectors):
                await self.wait_for_navigation()
                self.logger.info("✅ Country selection completed")
                return True
            
            return False
            
        except Exception as e:
            log_error(e, "_handle_country_selection")
            return False
    
    async def _handle_terms_of_service(self) -> bool:
        """Handle Terms of Service agreement"""
        try:
            self.logger.info("📋 Handling Terms of Service...")
            
            # Look for agree checkbox or button
            agree_selectors = [
                'input[type="checkbox"][name*="agree"]',
                'input[type="checkbox"][id*="agree"]',
                'button:has-text("Agree & Continue")',
                'button:has-text("I Agree")',
                'button:has-text("Accept")'
            ]
            
            # First try to find and check agreement checkbox
            for selector in agree_selectors:
                if "checkbox" in selector and await self.page.locator(selector).count() > 0:
                    await self.page.check(selector)
                    self.logger.info("✅ Agreed to terms checkbox")
                    break
            
            # Then click continue/agree button
            button_selectors = [
                'button:has-text("Agree & Continue")',
                'button:has-text("Continue")',
                'button:has-text("I Agree")',
                'button:has-text("Accept")'
            ]
            
            if await self.safe_click(button_selectors):
                await self.wait_for_navigation()
                self.logger.info("✅ Terms of Service accepted")
                return True
            
            return False
            
        except Exception as e:
            log_error(e, "_handle_terms_of_service")
            return False

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
        """Handle CAPTCHA detection - save report and close browser to continue to next email"""
        try:
            self.logger.warning("🤖 CAPTCHA detected! Skipping this email and moving to next.")
            self.logger.info("📋 CAPTCHA Handling Strategy:")
            self.logger.info("   1. CAPTCHA/reCAPTCHA detected during login")
            self.logger.info("   2. Saving detailed report with screenshot")
            self.logger.info("   3. Closing browser and continuing to next email")
            
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
        """Create a new project or select existing one following APIs & Services navigation"""
        try:
            self.logger.info(f"🏗️ Creating/selecting project: {project_name}")
            
            # Navigate directly to APIs & Services as per user instructions
            self.logger.info("🔧 Navigating to APIs & Services...")
            await self.page.goto("https://console.cloud.google.com/apis")
            await self.wait_for_navigation()
            await self.human_delay(3, 5)
            await self.take_screenshot("05_apis_services")
            
            # Skip country selection and terms handling - go straight to project creation
            # Look for "Create Project" button in APIs & Services section
            create_project_selectors = [
                'button:has-text("Create Project")',
                'a:has-text("Create Project")',
                'button:has-text("CREATE PROJECT")',
                'a:has-text("CREATE PROJECT")',
                '[data-testid="create-project"]',
                'button[aria-label*="Create Project"]',
                'text="Create Project"',
                '.create-project-button',
                '[role="button"]:has-text("Create Project")'
            ]
            
            self.logger.info("🔍 Looking for Create Project button in APIs & Services...")
            
            # Wait for the page to fully load
            await self.human_delay(2, 4)
            
            # Try to click Create Project button
            if not await self.safe_click(create_project_selectors):
                # If not found in APIs & Services, try the project selector approach
                self.logger.info("🔄 Create Project not found in APIs & Services, trying project selector...")
                await self.page.goto("https://console.cloud.google.com/projectselector2/home")
                await self.wait_for_navigation()
                await self.human_delay(2, 3)
                await self.take_screenshot("05_project_selector")
                
                # Try to find existing project first
                try:
                    project_selectors = [
                        f'text="{project_name}"',
                        f'[title="{project_name}"]',
                        f'div:has-text("{project_name}")'
                    ]
                    
                    for selector in project_selectors:
                        if await self.page.locator(selector).count() > 0:
                            await self.safe_click([selector])
                            self.logger.info(f"✅ Selected existing project: {project_name}")
                            return True
                except Exception:
                    pass
                
                # Look for "NEW PROJECT" button in project selector
                new_project_selectors = [
                    'button:has-text("NEW PROJECT")',
                    'a:has-text("NEW PROJECT")',
                    'button:has-text("Create Project")',
                    'a:has-text("Create Project")',
                    '[data-testid="create-project"]',
                    'button[aria-label*="Create"]',
                    'text="NEW PROJECT"'
                ]
                
                if not await self.safe_click(new_project_selectors):
                    # Final fallback - direct navigation to new project page
                    self.logger.info("🔄 Trying direct navigation to new project page...")
                    await self.page.goto("https://console.cloud.google.com/projectcreate")
                    await self.wait_for_navigation()
                    await self.human_delay(3, 5)
            
            await self.take_screenshot("06_create_project_form")
            
            # Wait for the form to load
            await self.human_delay(2, 3)
            
            # Wait for the New Project form to be fully loaded
            self.logger.info("⏳ Waiting for New Project form to load...")
            await self.page.wait_for_selector('text="New Project"', timeout=10000)
            await self.human_delay(2, 3)
            
            # Enter project name - updated selectors based on actual form structure
            project_name_selectors = [
                'input[type="text"]',  # Most likely selector based on screenshot
                'input[name="projectId"]',
                'input[name="name"]',
                'input[id*="project"]',
                'input[placeholder*="project"]',
                'input[aria-label*="Project name"]',
                'input[aria-label*="project name"]',
                'form input[type="text"]',
                '.form-field input',
                'div:has-text("Project name") + * input'
            ]
            
            self.logger.info("🔍 Looking for project name input field...")
            
            name_entered = False
            for selector in project_name_selectors:
                try:
                    # Wait for the input field to be available
                    await self.page.wait_for_selector(selector, timeout=5000)
                    
                    # Focus on the input field first
                    await self.page.locator(selector).focus()
                    await self.human_delay(0.5, 1)
                    
                    # Select all existing text and replace it
                    await self.page.keyboard.press("Control+a")
                    await self.human_delay(0.3, 0.5)
                    
                    # Type the new project name
                    await self.human_type(selector, project_name)
                    await self.human_delay(0.5, 1)
                    
                    # Verify the text was entered
                    entered_value = await self.page.locator(selector).input_value()
                    if project_name in entered_value or entered_value == project_name:
                        self.logger.info(f"✅ Project name entered successfully: {project_name}")
                        name_entered = True
                        break
                    else:
                        self.logger.warning(f"⚠️ Text verification failed for {selector}. Expected: {project_name}, Got: {entered_value}")
                        
                except Exception as e:
                    self.logger.debug(f"Failed to use selector {selector}: {str(e)}")
                    continue
            
            if not name_entered:
                # Try a more aggressive approach - find any visible input field
                self.logger.warning("⚠️ Standard selectors failed, trying fallback approach...")
                try:
                    # Look for any visible input field on the page
                    inputs = await self.page.locator('input[type="text"]:visible').all()
                    if inputs:
                        input_field = inputs[0]  # Take the first visible text input
                        await input_field.focus()
                        await self.page.keyboard.press("Control+a")
                        await input_field.fill(project_name)
                        self.logger.info(f"✅ Project name entered using fallback method: {project_name}")
                        name_entered = True
                except Exception as e:
                    self.logger.error(f"❌ Fallback method also failed: {str(e)}")
            
            if not name_entered:
                raise Exception("Could not find or fill project name input field")
            
            await self.human_delay(1, 2)
            
            # Check for validation errors before clicking Create
            validation_error_selectors = [
                'text="The name must be between 4 and 30 characters"',
                '.error-message',
                '[role="alert"]',
                '.mat-error',
                'text*="must be between"',
                'text*="characters"'
            ]
            
            validation_error_found = False
            for selector in validation_error_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        validation_error_found = True
                        self.logger.warning(f"⚠️ Validation error detected: {selector}")
                        break
                except Exception:
                    continue
            
            # If validation error found, generate a shorter project name and retry
            if validation_error_found:
                self.logger.warning(f"⚠️ Project name '{project_name}' is invalid, generating shorter name...")
                
                # Generate a much shorter name
                import time
                timestamp = str(int(time.time()))[-4:]  # Only last 4 digits
                short_project_name = f"gmail-{timestamp}"  # Only 10 characters
                
                self.logger.info(f"🔄 Retrying with shorter name: {short_project_name}")
                
                # Clear the input field and enter the shorter name
                project_name_selectors = [
                    'input[type="text"]',
                    'input[name="projectId"]',
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
            create_selectors = [
                'button:has-text("Create")',  # Exact match from screenshot
                'button:has-text("CREATE")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button:visible:has-text("Create")',
                'button.mat-raised-button:has-text("Create")',
                'button.mat-button:has-text("Create")',
                '[role="button"]:has-text("Create")',
                'button[aria-label*="Create"]'
            ]
            
            self.logger.info("🔍 Looking for Create button...")
            
            create_clicked = False
            for selector in create_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.locator(selector).click()
                    self.logger.info(f"✅ Create button clicked using selector: {selector}")
                    create_clicked = True
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to click Create button with selector {selector}: {str(e)}")
                    continue
            
            if not create_clicked:
                # Fallback - try to find any button with "Create" text
                try:
                    create_buttons = await self.page.locator('button:has-text("Create")').all()
                    if create_buttons:
                        await create_buttons[0].click()
                        self.logger.info("✅ Create button clicked using fallback method")
                        create_clicked = True
                except Exception as e:
                    self.logger.error(f"❌ Fallback Create button click failed: {str(e)}")
            
            if not create_clicked:
                raise Exception("Could not find or click Create button")
            
            self.logger.info("✅ Create button clicked, waiting for project creation...")
            
            # Wait for project creation - this can take some time
            await self.human_delay(5, 8)
            await self.wait_for_navigation()
            
            # Take screenshot after creation attempt
            await self.take_screenshot("07_project_created")
            
            # Verify project creation by checking URL or page content
            current_url = self.page.url
            if "console.cloud.google.com" in current_url and "projectselector" not in current_url:
                self.logger.info(f"✅ Project created successfully: {project_name}")
                
                # After project creation, we need to select the project if we're on APIs & Services page
                await self._ensure_project_selected(project_name)
                return True
            else:
                # Additional verification - look for project name in the interface
                project_indicators = [
                    f'text="{project_name}"',
                    f'[title*="{project_name}"]'
                ]
                
                for indicator in project_indicators:
                    if await self.page.locator(indicator).count() > 0:
                        self.logger.info(f"✅ Project created and verified: {project_name}")
                        await self._ensure_project_selected(project_name)
                        return True
                
                self.logger.warning("⚠️ Project creation status unclear, but continuing...")
                await self._ensure_project_selected(project_name)
                return True
            
        except Exception as e:
            log_error(e, "project_creation", additional_data={'project_name': project_name})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot(f"error_project_creation_{project_name}")
            raise
    
    @retry_async(context="project_selection")
    async def _ensure_project_selected(self, project_name: str) -> bool:
        """Ensure the newly created project is selected in Google Cloud Console"""
        try:
            self.logger.info(f"🎯 Ensuring project '{project_name}' is selected...")
            
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
            
            # Wait for dropdown to load
            await self.human_delay(1, 2)
            
            # Try to find and click the project
            project_selectors = [
                f'text="{project_name}"',
                f'[title="{project_name}"]',
                f'div:has-text("{project_name}")',
                f'li:has-text("{project_name}")',
                f'[role="option"]:has-text("{project_name}")',
                f'button:has-text("{project_name}")'
            ]
            
            project_selected = False
            for selector in project_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.page.locator(selector).click()
                        self.logger.info(f"✅ Selected project '{project_name}' using selector: {selector}")
                        project_selected = True
                        await self.human_delay(2, 3)
                        break
                except Exception as e:
                    self.logger.debug(f"Failed to select project with selector {selector}: {str(e)}")
                    continue
            
            if not project_selected:
                # Try to find any project that contains part of our project name
                self.logger.warning(f"⚠️ Exact project name not found, looking for partial matches...")
                
                # Extract the base name (remove timestamp suffix)
                base_name = project_name.split('-')[0:3]  # Take first 3 parts: gmail-oauth-username
                base_pattern = '-'.join(base_name)
                
                partial_selectors = [
                    f'text*="{base_pattern}"',
                    f'div:has-text("{base_pattern}")',
                    f'li:has-text("{base_pattern}")'
                ]
                
                for selector in partial_selectors:
                    try:
                        if await self.page.locator(selector).count() > 0:
                            await self.page.locator(selector).click()
                            self.logger.info(f"✅ Selected project using partial match: {selector}")
                            project_selected = True
                            await self.human_delay(2, 3)
                            break
                    except Exception as e:
                        self.logger.debug(f"Failed to select project with partial selector {selector}: {str(e)}")
                        continue
            
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
                await self.page.goto("https://console.cloud.google.com/apis", wait_until="networkidle", timeout=30000)
                await self.human_delay(3, 5)
                await self.take_screenshot("08_apis_services_before_api")
            
            # Try direct navigation to Gmail API first (most reliable)
            self.logger.info("🎯 Trying direct navigation to Gmail API...")
            try:
                await self.page.goto(self.gmail_api_url, wait_until="networkidle", timeout=30000)
                await self.human_delay(3, 5)
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
                await self.page.goto("https://console.cloud.google.com/apis/library", wait_until="networkidle", timeout=30000)
                await self.human_delay(3, 5)
                await self.take_screenshot("08_api_library")
                
                # Wait for page to fully load
                await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
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
                    await self.page.goto(url, wait_until="networkidle", timeout=30000)
                    await self.human_delay(2, 3)
                    
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
            
            # Wait for navigation or page update
            try:
                await self.page.wait_for_load_state("networkidle", timeout=30000)
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
    async def setup_oauth_consent_screen(self, app_name: str = "Gmail OAuth App") -> bool:
        """Setup OAuth consent screen"""
        try:
            self.logger.info("🔒 Setting up OAuth consent screen...")
            
            # Navigate to OAuth consent screen
            await self.page.goto("https://console.cloud.google.com/apis/credentials/consent")
            await self.wait_for_navigation()
            await self.take_screenshot("09_oauth_consent")
            
            # Check if consent screen is already configured
            if await self._check_consent_configured():
                self.logger.info("✅ OAuth consent screen already configured")
                return True
            
            # Select External user type (if not already selected)
            external_selectors = [
                'input[value="EXTERNAL"]',
                'mat-radio-button:has-text("External")',
                '[data-value="external"]'
            ]
            
            await self.safe_click(external_selectors)
            await self.human_delay(1, 2)
            
            # Click Create button
            create_selectors = [
                'button:has-text("Create")',
                'button:has-text("CREATE")',
                'button[type="submit"]'
            ]
            
            if not await self.safe_click(create_selectors):
                raise Exception("Could not find Create button for OAuth consent")
            
            await self.wait_for_navigation()
            await self.take_screenshot("10_oauth_form")
            
            # Fill in app name
            app_name_selectors = [
                'input[name="applicationName"]',
                'input[formcontrolname="applicationName"]',
                'input[aria-label*="App name"]'
            ]
            
            for selector in app_name_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.human_type(selector, app_name)
                    break
                except Exception:
                    continue
            
            # Fill in user support email (use current user's email)
            support_email_selectors = [
                'input[name="supportEmail"]',
                'input[formcontrolname="supportEmail"]',
                'mat-select[formcontrolname="supportEmail"]'
            ]
            
            # Try to select current user's email from dropdown
            for selector in support_email_selectors:
                try:
                    await self.safe_click(selector)
                    await self.human_delay(1, 2)
                    # Select first option (usually current user)
                    await self.safe_click('mat-option:first-child')
                    break
                except Exception:
                    continue
            
            # Save and continue
            save_selectors = [
                'button:has-text("Save and Continue")',
                'button:has-text("SAVE AND CONTINUE")',
                'button[type="submit"]'
            ]
            
            if not await self.safe_click(save_selectors):
                raise Exception("Could not find Save and Continue button")
            
            await self.wait_for_navigation()
            
            # Skip scopes page
            await self.safe_click('button:has-text("Save and Continue")')
            await self.wait_for_navigation()
            
            # Skip test users page
            await self.safe_click('button:has-text("Save and Continue")')
            await self.wait_for_navigation()
            
            # Final save
            await self.safe_click('button:has-text("Back to Dashboard")')
            await self.wait_for_navigation()
            
            self.logger.info("✅ OAuth consent screen configured successfully")
            return True
            
        except Exception as e:
            log_error(e, "oauth_consent_screen", additional_data={'app_name': app_name})
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
        """Create OAuth 2.0 credentials and download JSON"""
        try:
            self.logger.info("🔑 Creating OAuth 2.0 credentials...")
            
            # Navigate to credentials page
            await self.page.goto("https://console.cloud.google.com/apis/credentials")
            await self.wait_for_navigation()
            await self.take_screenshot("11_credentials_page")
            
            # Click Create Credentials
            create_cred_selectors = [
                'button:has-text("Create Credentials")',
                'button:has-text("CREATE CREDENTIALS")',
                '[data-value="create_credentials"]'
            ]
            
            if not await self.safe_click(create_cred_selectors):
                raise Exception("Could not find Create Credentials button")
            
            await self.human_delay(1, 2)
            
            # Select OAuth client ID
            oauth_selectors = [
                'text="OAuth client ID"',
                'button:has-text("OAuth client ID")',
                '[data-value="oauth_client_id"]'
            ]
            
            if not await self.safe_click(oauth_selectors):
                raise Exception("Could not find OAuth client ID option")
            
            await self.wait_for_navigation()
            await self.take_screenshot("12_oauth_form")
            
            # Select Desktop application
            desktop_selectors = [
                'mat-radio-button:has-text("Desktop application")',
                'input[value="DESKTOP"]',
                '[data-value="desktop"]'
            ]
            
            if not await self.safe_click(desktop_selectors):
                raise Exception("Could not find Desktop application option")
            
            await self.human_delay(1, 2)
            
            # Enter name (use email as name)
            name_selectors = [
                'input[name="name"]',
                'input[formcontrolname="name"]',
                'input[aria-label*="Name"]'
            ]
            
            name_entered = False
            for selector in name_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.human_type(selector, email)
                    name_entered = True
                    break
                except Exception:
                    continue
            
            if not name_entered:
                self.logger.warning("Could not find name field, using default")
            
            # Click Create
            create_selectors = [
                'button:has-text("Create")',
                'button:has-text("CREATE")',
                'button[type="submit"]'
            ]
            
            if not await self.safe_click(create_selectors):
                raise Exception("Could not find Create button")
            
            await self.wait_for_navigation()
            await self.take_screenshot("13_credentials_created")
            
            # Download JSON
            download_selectors = [
                'button:has-text("Download JSON")',
                'button:has-text("DOWNLOAD JSON")',
                '[data-value="download_json"]',
                'button[aria-label*="Download"]'
            ]
            
            if not await self.safe_click(download_selectors):
                raise Exception("Could not find Download JSON button")
            
            # Wait for download to complete
            await self.human_delay(3, 5)
            
            self.logger.info("✅ OAuth credentials created and JSON downloaded")
            return True
            
        except Exception as e:
            log_error(e, "oauth_credentials_creation", additional_data={'email': email})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("error_oauth_credentials")
            raise
    
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