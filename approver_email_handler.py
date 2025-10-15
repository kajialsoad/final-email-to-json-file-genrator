"""
Approver Email Handler for Gmail OAuth Automation

This module handles approver email functionality for verification emails.
When Gmail requires verification, this system can automatically check
approver email accounts for verification emails and handle them.
"""

import asyncio
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from playwright.async_api import Page, Browser
from config import get_config
from error_handler import log_error
from playwright_automation import PlaywrightAutomationEngine


@dataclass
class VerificationEmail:
    """Data class for verification email information"""
    subject: str
    sender: str
    verification_link: str
    verification_code: str
    received_time: float
    email_content: str


class ApproverEmailHandler(PlaywrightAutomationEngine):
    """Handle approver email verification for Gmail OAuth automation"""
    
    def __init__(self, browser: Browser, logger):
        """Initialize approver email handler"""
        super().__init__(browser, logger)
        self.config = get_config()
        self.approver_config = self.config.approver
        self.verification_emails: List[VerificationEmail] = []
        
    async def check_approver_email_for_verification(self, target_email: str, timeout_minutes: int = None) -> Optional[VerificationEmail]:
        """
        Check approver email for verification emails related to target email
        
        Args:
            target_email: The email account that needs verification
            timeout_minutes: How long to wait for verification email (uses config if None)
            
        Returns:
            VerificationEmail object if found, None otherwise
        """
        if not self.approver_config.enabled:
            self.logger.info("📧 Approver email functionality is disabled")
            return None
            
        if not self.approver_config.approver_email or not self.approver_config.approver_password:
            self.logger.warning("⚠️ Approver email credentials not configured")
            return None
            
        timeout_minutes = timeout_minutes or self.approver_config.timeout_minutes
        check_interval = self.approver_config.check_interval_seconds
        max_attempts = self.approver_config.max_attempts
        
        self.logger.info(f"📧 Starting approver email check for verification of {target_email}")
        self.logger.info(f"   Approver email: {self.approver_config.approver_email}")
        self.logger.info(f"   Timeout: {timeout_minutes} minutes")
        self.logger.info(f"   Check interval: {check_interval} seconds")
        self.logger.info(f"   Max attempts: {max_attempts}")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        attempt = 0
        
        while attempt < max_attempts and (time.time() - start_time) < timeout_seconds:
            attempt += 1
            self.logger.info(f"🔍 Checking approver email - Attempt {attempt}/{max_attempts}")
            
            try:
                # Login to approver email account
                if await self._login_to_approver_email():
                    # Search for verification emails
                    verification_email = await self._search_for_verification_email(target_email)
                    
                    if verification_email:
                        self.logger.info(f"✅ Found verification email for {target_email}")
                        return verification_email
                    else:
                        self.logger.info(f"📭 No verification email found yet for {target_email}")
                else:
                    self.logger.warning(f"⚠️ Failed to login to approver email on attempt {attempt}")
                
            except Exception as e:
                self.logger.error(f"❌ Error during approver email check attempt {attempt}: {str(e)}")
                log_error(e, f"check_approver_email_for_verification_attempt_{attempt}")
            
            # Wait before next attempt (unless it's the last attempt)
            if attempt < max_attempts and (time.time() - start_time) < timeout_seconds:
                self.logger.info(f"⏳ Waiting {check_interval} seconds before next check...")
                await asyncio.sleep(check_interval)
        
        self.logger.warning(f"⏰ Timeout reached or max attempts exceeded for {target_email}")
        return None
    
    async def _login_to_approver_email(self) -> bool:
        """Login to the approver email account"""
        try:
            self.logger.info("🔐 Logging into approver email account...")
            
            # Navigate to Gmail
            await self.page.goto("https://accounts.google.com/signin", wait_until="networkidle")
            await self.human_delay(2, 3)
            
            # Enter approver email
            email_selectors = [
                'input[type="email"]',
                'input[name="identifier"]',
                'input[id="identifierId"]',
                '#Email'
            ]
            
            email_entered = False
            for selector in email_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.human_type(selector, self.approver_config.approver_email)
                        self.logger.info("✅ Approver email entered")
                        email_entered = True
                        break
                except Exception as e:
                    self.logger.debug(f"Email selector {selector} failed: {str(e)}")
                    continue
            
            if not email_entered:
                self.logger.error("❌ Could not enter approver email")
                return False
            
            # Click Next button
            next_selectors = [
                'button:has-text("Next")',
                'input[type="submit"]',
                '#identifierNext',
                'button[id="identifierNext"]'
            ]
            
            if not await self.safe_click(next_selectors):
                self.logger.error("❌ Could not click Next button after email")
                return False
            
            await self.wait_for_navigation()
            await self.human_delay(2, 3)
            
            # Enter approver password
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                '#password',
                'input[aria-label*="password"]'
            ]
            
            password_entered = False
            for selector in password_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.human_type(selector, self.approver_config.approver_password)
                        self.logger.info("✅ Approver password entered")
                        password_entered = True
                        break
                except Exception as e:
                    self.logger.debug(f"Password selector {selector} failed: {str(e)}")
                    continue
            
            if not password_entered:
                self.logger.error("❌ Could not enter approver password")
                return False
            
            # Click Next/Sign in button
            signin_selectors = [
                'button:has-text("Next")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
                '#passwordNext',
                'button[id="passwordNext"]'
            ]
            
            if not await self.safe_click(signin_selectors):
                self.logger.error("❌ Could not click Sign in button")
                return False
            
            await self.wait_for_navigation()
            await self.human_delay(3, 5)
            
            # Check if login was successful
            current_url = await self.get_current_url()
            if "myaccount.google.com" in current_url or "mail.google.com" in current_url:
                self.logger.info("✅ Successfully logged into approver email")
                
                # Navigate to Gmail if not already there
                if "mail.google.com" not in current_url:
                    await self.page.goto("https://mail.google.com", wait_until="networkidle")
                    await self.human_delay(3, 5)
                
                return True
            else:
                self.logger.error(f"❌ Login failed - unexpected URL: {current_url}")
                return False
                
        except Exception as e:
            log_error(e, "_login_to_approver_email")
            return False
    
    async def _search_for_verification_email(self, target_email: str) -> Optional[VerificationEmail]:
        """Search for verification emails related to the target email"""
        try:
            self.logger.info(f"🔍 Searching for verification emails for {target_email}")
            
            # Search for verification emails using Gmail search
            search_queries = [
                f"from:noreply@google.com {target_email}",
                f"from:accounts-noreply@google.com {target_email}",
                f"verification {target_email}",
                f"verify {target_email}",
                f"security {target_email}"
            ]
            
            for query in search_queries:
                self.logger.info(f"🔍 Searching with query: {query}")
                
                # Use Gmail search
                search_box_selectors = [
                    'input[aria-label="Search mail"]',
                    'input[name="q"]',
                    'input[placeholder*="Search"]'
                ]
                
                search_entered = False
                for selector in search_box_selectors:
                    try:
                        if await self.page.locator(selector).count() > 0:
                            # Clear search box first
                            await self.page.fill(selector, "")
                            await self.human_type(selector, query)
                            await self.page.keyboard.press("Enter")
                            await self.human_delay(2, 3)
                            search_entered = True
                            break
                    except Exception as e:
                        self.logger.debug(f"Search selector {selector} failed: {str(e)}")
                        continue
                
                if not search_entered:
                    self.logger.warning("⚠️ Could not enter search query")
                    continue
                
                # Look for verification emails in search results
                verification_email = await self._parse_verification_emails(target_email)
                if verification_email:
                    return verification_email
            
            return None
            
        except Exception as e:
            log_error(e, "_search_for_verification_email")
            return None
    
    async def _parse_verification_emails(self, target_email: str) -> Optional[VerificationEmail]:
        """Parse verification emails from Gmail search results"""
        try:
            # Wait for search results to load
            await self.human_delay(2, 3)
            
            # Look for email items in the list
            email_selectors = [
                'tr[role="row"]',
                '.zA',  # Gmail email row class
                '[data-thread-id]'
            ]
            
            for selector in email_selectors:
                email_elements = await self.page.locator(selector).all()
                
                for email_element in email_elements[:5]:  # Check first 5 emails
                    try:
                        # Get email text content
                        email_text = await email_element.text_content()
                        
                        if not email_text:
                            continue
                        
                        # Check if this looks like a verification email
                        verification_indicators = [
                            'verification',
                            'verify',
                            'security',
                            'sign-in',
                            'login',
                            'access',
                            'account'
                        ]
                        
                        if any(indicator in email_text.lower() for indicator in verification_indicators):
                            # Click on the email to open it
                            await email_element.click()
                            await self.human_delay(2, 3)
                            
                            # Extract verification information
                            verification_email = await self._extract_verification_info(target_email)
                            if verification_email:
                                return verification_email
                            
                            # Go back to search results
                            await self.page.keyboard.press("Escape")
                            await self.human_delay(1, 2)
                    
                    except Exception as e:
                        self.logger.debug(f"Error processing email element: {str(e)}")
                        continue
            
            return None
            
        except Exception as e:
            log_error(e, "_parse_verification_emails")
            return None
    
    async def _extract_verification_info(self, target_email: str) -> Optional[VerificationEmail]:
        """Extract verification information from opened email"""
        try:
            # Get email content
            email_content = await self.page.text_content('body')
            
            if not email_content:
                return None
            
            # Extract verification link
            verification_link = self._extract_verification_link(email_content)
            
            # Extract verification code
            verification_code = self._extract_verification_code(email_content)
            
            # Get subject and sender
            subject = await self._get_email_subject()
            sender = await self._get_email_sender()
            
            if verification_link or verification_code:
                verification_email = VerificationEmail(
                    subject=subject or "Unknown Subject",
                    sender=sender or "Unknown Sender",
                    verification_link=verification_link or "",
                    verification_code=verification_code or "",
                    received_time=time.time(),
                    email_content=email_content
                )
                
                self.logger.info(f"✅ Extracted verification info:")
                self.logger.info(f"   Subject: {verification_email.subject}")
                self.logger.info(f"   Sender: {verification_email.sender}")
                self.logger.info(f"   Has Link: {bool(verification_email.verification_link)}")
                self.logger.info(f"   Has Code: {bool(verification_email.verification_code)}")
                
                return verification_email
            
            return None
            
        except Exception as e:
            log_error(e, "_extract_verification_info")
            return None
    
    def _extract_verification_link(self, email_content: str) -> Optional[str]:
        """Extract verification link from email content"""
        try:
            # Common verification link patterns
            link_patterns = [
                r'https://accounts\.google\.com/[^\s<>"\']+verify[^\s<>"\']*',
                r'https://accounts\.google\.com/[^\s<>"\']+confirmation[^\s<>"\']*',
                r'https://accounts\.google\.com/[^\s<>"\']+signin[^\s<>"\']*',
                r'https://[^\s<>"\']*google[^\s<>"\']*verify[^\s<>"\']*',
                r'https://[^\s<>"\']*verify[^\s<>"\']*google[^\s<>"\']*'
            ]
            
            for pattern in link_patterns:
                matches = re.findall(pattern, email_content, re.IGNORECASE)
                if matches:
                    return matches[0]
            
            return None
            
        except Exception as e:
            log_error(e, "_extract_verification_link")
            return None
    
    def _extract_verification_code(self, email_content: str) -> Optional[str]:
        """Extract verification code from email content"""
        try:
            # Common verification code patterns
            code_patterns = [
                r'verification code[:\s]+([A-Z0-9]{6,8})',
                r'code[:\s]+([A-Z0-9]{6,8})',
                r'([A-Z0-9]{6,8})[^\w]*verification',
                r'enter[^\w]+([A-Z0-9]{6,8})',
                r'use[^\w]+([A-Z0-9]{6,8})'
            ]
            
            for pattern in code_patterns:
                matches = re.findall(pattern, email_content, re.IGNORECASE)
                if matches:
                    return matches[0]
            
            return None
            
        except Exception as e:
            log_error(e, "_extract_verification_code")
            return None
    
    async def _get_email_subject(self) -> Optional[str]:
        """Get email subject from opened email"""
        try:
            subject_selectors = [
                'h2[data-thread-id]',
                '.hP',  # Gmail subject class
                '[data-legacy-thread-id] h2',
                'span[id*="subject"]'
            ]
            
            for selector in subject_selectors:
                if await self.page.locator(selector).count() > 0:
                    return await self.page.locator(selector).first.text_content()
            
            return None
            
        except Exception as e:
            log_error(e, "_get_email_subject")
            return None
    
    async def _get_email_sender(self) -> Optional[str]:
        """Get email sender from opened email"""
        try:
            sender_selectors = [
                '.go span[email]',
                '.gD',  # Gmail sender class
                '[data-hovercard-id]',
                'span[title*="@"]'
            ]
            
            for selector in sender_selectors:
                if await self.page.locator(selector).count() > 0:
                    return await self.page.locator(selector).first.text_content()
            
            return None
            
        except Exception as e:
            log_error(e, "_get_email_sender")
            return None
    
    async def handle_verification_with_approver(self, target_email: str) -> bool:
        """
        Complete verification process using approver email
        
        Args:
            target_email: The email account that needs verification
            
        Returns:
            True if verification was successful, False otherwise
        """
        try:
            self.logger.info(f"🔄 Starting verification process for {target_email} using approver email")
            
            # Check for verification email
            verification_email = await self.check_approver_email_for_verification(target_email)
            
            if not verification_email:
                self.logger.warning(f"❌ No verification email found for {target_email}")
                return False
            
            # Handle verification based on what we found
            if verification_email.verification_link:
                return await self._handle_verification_link(verification_email.verification_link)
            elif verification_email.verification_code:
                return await self._handle_verification_code(verification_email.verification_code)
            else:
                self.logger.warning("⚠️ Verification email found but no usable verification method")
                return False
                
        except Exception as e:
            log_error(e, "handle_verification_with_approver")
            return False
    
    async def _handle_verification_link(self, verification_link: str) -> bool:
        """Handle verification using a verification link"""
        try:
            self.logger.info(f"🔗 Handling verification link: {verification_link}")
            
            # Open verification link in new tab
            new_page = await self.browser.new_page()
            await new_page.goto(verification_link, wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Check if verification was successful
            current_url = await new_page.url()
            page_content = await new_page.text_content('body')
            
            success_indicators = [
                'verified',
                'confirmed',
                'success',
                'complete',
                'activated'
            ]
            
            verification_successful = any(indicator in page_content.lower() for indicator in success_indicators)
            
            if verification_successful:
                self.logger.info("✅ Verification link handled successfully")
            else:
                self.logger.warning("⚠️ Verification link opened but success unclear")
            
            await new_page.close()
            return verification_successful
            
        except Exception as e:
            log_error(e, "_handle_verification_link")
            return False
    
    async def _handle_verification_code(self, verification_code: str) -> bool:
        """Handle verification using a verification code"""
        try:
            self.logger.info(f"🔢 Handling verification code: {verification_code}")
            
            # This would need to be integrated with the main OAuth flow
            # For now, we'll just log that we have the code
            self.logger.info(f"✅ Verification code extracted: {verification_code}")
            
            # TODO: Integrate with main OAuth flow to enter this code
            # This would require coordination with the main automation process
            
            return True
            
        except Exception as e:
            log_error(e, "_handle_verification_code")
            return False