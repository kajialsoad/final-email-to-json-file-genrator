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
            
            # Wait for password field and enter password (do this BEFORE checking for challenges)
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            password_entered = False
            for selector in password_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    await self.human_delay(1, 2)
                    await self.human_type(selector, password)
                    password_entered = True
                    self.logger.info("✅ Password entered successfully")
                    break
                except Exception as e:
                    self.logger.debug(f"Password selector {selector} failed: {str(e)}")
                    continue
            
            if not password_entered:
                raise Exception("Could not find password input field")
            
            # Click password next button
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
            
            # Now check for challenges after password submission
            challenges = await self.check_for_challenges()
            if any(challenges.values()):
                self.logger.warning(f"⚠️ Challenges detected: {challenges}")
                
                # Handle CAPTCHA with manual intervention
                if challenges['captcha']:
                    return await self._handle_captcha_manual_intervention(email)
                
                if challenges['account_blocked']:
                    raise Exception("Account appears to be blocked or suspended")
                
                if challenges['two_factor']:
                    self.logger.warning("⚠️ Two-factor authentication required")
                    # Handle as verification email - save report and close browser
                    return await self._handle_email_verification(email, "two_factor_verification")
                
                if challenges['email_verification']:
                    self.logger.warning("⚠️ Email verification required")
                    return await self._handle_email_verification(email)
            
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
        """Handle CAPTCHA with manual intervention - keep browser open"""
        try:
            self.logger.warning("🤖 CAPTCHA detected! Manual intervention required.")
            self.logger.info("📋 CAPTCHA Handling Instructions:")
            self.logger.info("   1. Browser will stay open for manual CAPTCHA solving")
            self.logger.info("   2. Please solve the CAPTCHA manually in the browser")
            self.logger.info("   3. After solving, the automation will continue automatically")
            
            # Take screenshot for report
            captcha_screenshot = await self.take_screenshot(f"captcha_detected_{email.replace('@', '_')}")
            
            # Save CAPTCHA report
            await self._save_captcha_report(email, captcha_screenshot)
            
            # Wait for CAPTCHA to be solved (check every 5 seconds)
            max_wait_time = 300  # 5 minutes maximum wait
            wait_interval = 5    # Check every 5 seconds
            elapsed_time = 0
            
            self.logger.info("⏳ Waiting for CAPTCHA to be solved manually...")
            
            while elapsed_time < max_wait_time:
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
                
                # Check if CAPTCHA is still present
                challenges = await self.check_for_challenges()
                if not challenges['captcha']:
                    self.logger.info("✅ CAPTCHA solved! Continuing automation...")
                    
                    # Continue with login verification
                    await asyncio.sleep(3)
                    if await self._check_if_logged_in():
                        self.logger.info("✅ Successfully logged into Google Cloud Console")
                        return True
                    else:
                        # Try to continue the login process
                        await self.wait_for_navigation()
                        await asyncio.sleep(2)
                        if await self._check_if_logged_in():
                            return True
                
                # Show progress
                remaining_time = max_wait_time - elapsed_time
                self.logger.info(f"⏳ Still waiting for CAPTCHA... ({remaining_time}s remaining)")
            
            # Timeout reached
            self.logger.error("⏰ CAPTCHA solving timeout reached (5 minutes)")
            raise Exception("CAPTCHA solving timeout - manual intervention took too long")
            
        except Exception as e:
            self.logger.error(f"❌ Error in CAPTCHA manual intervention: {str(e)}")
            raise
    
    async def _save_captcha_report(self, email: str, screenshot_path: str):
        """Save CAPTCHA detection report"""
        try:
            from datetime import datetime
            import json
            from pathlib import Path
            
            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Create CAPTCHA report
            report = {
                "timestamp": datetime.now().isoformat(),
                "email": email,
                "event": "captcha_detected",
                "screenshot": screenshot_path,
                "status": "manual_intervention_required",
                "message": "CAPTCHA detected during login process - manual solving required"
            }
            
            # Save report file
            report_filename = f"captcha_report_{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 CAPTCHA report saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save CAPTCHA report: {str(e)}")
    
    async def _handle_email_verification(self, email: str, verification_type: str = "email_verification") -> bool:
        """Handle email/two-factor verification - save report and close webdriver for this email"""
        try:
            if verification_type == "two_factor_verification":
                self.logger.warning("📱 Two-factor verification detected! Handling gracefully...")
                self.logger.info("📋 Two-Factor Verification Handling:")
            else:
                self.logger.warning("📧 Email verification detected! Handling gracefully...")
                self.logger.info("📋 Email Verification Handling:")
            
            self.logger.info("   1. Saving verification report")
            self.logger.info("   2. Closing webdriver for this email")
            self.logger.info("   3. Will continue with next email")
            
            # Take screenshot for report
            screenshot_prefix = "two_factor_detected" if verification_type == "two_factor_verification" else "verification_detected"
            verification_screenshot = await self.take_screenshot(f"{screenshot_prefix}_{email.replace('@', '_')}")
            
            # Save verification report
            await self._save_verification_report(email, verification_screenshot, verification_type)
            
            # Close browser for this email
            await self._close_browser_for_verification()
            
            # Return False to indicate this email needs verification (skip to next)
            verification_msg = "Two-factor verification" if verification_type == "two_factor_verification" else "Email verification"
            self.logger.info(f"✅ {verification_msg} handled - moving to next email")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in verification handling: {str(e)}")
            return False
    
    async def _save_verification_report(self, email: str, screenshot_path: str, verification_type: str = "email_verification"):
        """Save email/two-factor verification report"""
        try:
            from datetime import datetime
            import json
            from pathlib import Path
            
            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Create verification report based on type
            if verification_type == "two_factor_verification":
                event = "two_factor_verification_required"
                message = "Two-factor verification required - please check your phone and verify manually"
                report_prefix = "two_factor_report"
            else:
                event = "email_verification_required"
                message = "Email verification required - please check email and verify manually"
                report_prefix = "verification_report"
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "email": email,
                "event": event,
                "verification_type": verification_type,
                "screenshot": screenshot_path,
                "status": "verification_pending",
                "message": message,
                "action_taken": "webdriver_closed_for_this_email",
                "next_action": "continue_with_next_email"
            }
            
            # Save report file
            report_filename = f"{report_prefix}_{email.replace('@', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = reports_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Verification report saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save verification report: {str(e)}")
    
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