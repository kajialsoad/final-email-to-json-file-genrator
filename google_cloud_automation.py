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
        """Handle challenges that appear AFTER password entry - always close browser and generate report"""
        try:
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
            
            # Handle unusual activity after password
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
        """Handle email verification with proper browser cleanup and error flow"""
        try:
            self.logger.warning(f"📧 {verification_type.replace('_', ' ').title()} detected!")
            self.logger.info("📋 Verification Handling Flow:")
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
        """Create a new project or select existing one"""
        try:
            self.logger.info(f"🏗️ Creating/selecting project: {project_name}")
            
            # Navigate to project selector
            await self.page.goto("https://console.cloud.google.com/projectselector2")
            await self.wait_for_navigation()
            await self.take_screenshot("05_project_selector")
            
            # Try to find existing project first
            try:
                project_link = f'a:has-text("{project_name}")'
                if await self.page.locator(project_link).count() > 0:
                    await self.safe_click(project_link)
                    self.logger.info(f"✅ Selected existing project: {project_name}")
                    return True
            except Exception:
                pass
            
            # Create new project
            create_project_selectors = [
                'button:has-text("Create Project")',
                'a:has-text("Create Project")',
                '[data-value="create_project"]',
                'button[aria-label*="Create"]'
            ]
            
            if not await self.safe_click(create_project_selectors):
                raise Exception("Could not find Create Project button")
            
            await self.wait_for_navigation()
            await self.take_screenshot("06_create_project_form")
            
            # Enter project name
            project_name_selectors = [
                'input[name="name"]',
                'input[id="name"]',
                'input[placeholder*="project name"]',
                'input[aria-label*="Project name"]'
            ]
            
            name_entered = False
            for selector in project_name_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.human_type(selector, project_name)
                    name_entered = True
                    break
                except Exception:
                    continue
            
            if not name_entered:
                raise Exception("Could not find project name input field")
            
            # Click create button
            create_selectors = [
                'button:has-text("Create")',
                'button[type="submit"]',
                'input[type="submit"]',
                '[data-value="create"]'
            ]
            
            if not await self.safe_click(create_selectors):
                raise Exception("Could not find Create button")
            
            # Wait for project creation
            await asyncio.sleep(5)
            await self.wait_for_navigation()
            
            # Verify project creation
            await self.take_screenshot("07_project_created")
            self.logger.info(f"✅ Project created successfully: {project_name}")
            return True
            
        except Exception as e:
            log_error(e, "project_creation", additional_data={'project_name': project_name})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot(f"error_project_creation_{project_name}")
            raise
    
    @retry_async(context="gmail_api_enable")
    async def enable_gmail_api(self) -> bool:
        """Enable Gmail API for the current project"""
        try:
            self.logger.info("📧 Enabling Gmail API...")
            
            # Navigate to Gmail API page
            await self.page.goto(self.gmail_api_url)
            await self.wait_for_navigation()
            await self.take_screenshot("08_gmail_api_page")
            
            # Check if API is already enabled
            if await self._check_api_enabled():
                self.logger.info("✅ Gmail API is already enabled")
                return True
            
            # Click enable button
            enable_selectors = [
                'button:has-text("Enable")',
                'button:has-text("ENABLE")',
                '[data-value="enable"]',
                'button[aria-label*="Enable"]'
            ]
            
            if not await self.safe_click(enable_selectors):
                raise Exception("Could not find Enable button for Gmail API")
            
            # Wait for API to be enabled
            await asyncio.sleep(10)
            await self.wait_for_navigation()
            
            # Verify API is enabled
            if await self._check_api_enabled():
                self.logger.info("✅ Gmail API enabled successfully")
                return True
            else:
                raise Exception("Gmail API enable verification failed")
                
        except Exception as e:
            log_error(e, "gmail_api_enable")
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("error_gmail_api_enable")
            raise
    
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