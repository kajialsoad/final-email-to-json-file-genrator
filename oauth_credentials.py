#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth Credentials Manager
Handles OAuth credential creation, JSON download, and file organization
"""

import asyncio
import json
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from google_cloud_automation import GoogleCloudAutomation
from automation_factory import AutomationFactory
from error_handler import retry_async, log_error, ErrorType, ErrorSeverity
from email_reporter import email_reporter
from config import get_config

class OAuthCredentialsManager(GoogleCloudAutomation):
    """Manages OAuth credential creation and JSON file handling with framework selection"""
    
    def __init__(self):
        # Initialize Playwright-based automation context
        super().__init__()
        self.config = get_config()
        # Create framework-specific automation instance (for Selenium path)
        self.automation = AutomationFactory.create_automation(self.config)
        self.current_project_id = None
        self.current_email = None
        # Use logger from underlying automation if available, else default
        self.logger = getattr(self.automation, 'logger', self.logger)
        
    @retry_async(context="oauth_credentials_creation")
    async def create_oauth_credentials(self, credential_name: str = None) -> Dict[str, Any]:
        """Create OAuth 2.0 client credentials"""
        try:
            if not credential_name:
                credential_name = f"OAuth_Client_{int(time.time())}"
            
            self.logger.info(f"🔑 Creating OAuth credentials: {credential_name}")
            
            # Navigate to credentials page
            await self.page.goto("https://console.cloud.google.com/apis/credentials")
            await self.wait_for_navigation()
            await self.take_screenshot("11_credentials_page")
            
            # Click Create Credentials
            create_creds_selectors = [
                'button:has-text("Create Credentials")',
                'button:has-text("CREATE CREDENTIALS")',
                '[data-value="create_credentials"]',
                'button[aria-label*="Create credentials"]'
            ]
            
            if not await self.safe_click(create_creds_selectors):
                raise Exception("Could not find Create Credentials button")
            
            await self.human_delay(1, 2)
            
            # Select OAuth client ID
            oauth_selectors = [
                'a:has-text("OAuth client ID")',
                'div:has-text("OAuth client ID")',
                '[data-value="oauth_client_id"]'
            ]
            
            if not await self.safe_click(oauth_selectors):
                raise Exception("Could not find OAuth client ID option")
            
            await self.wait_for_navigation()
            await self.take_screenshot("12_oauth_form")
            
            # Select application type (Desktop application)
            app_type_selectors = [
                'select[name="applicationType"]',
                'mat-select[formcontrolname="applicationType"]',
                'input[value="DESKTOP"]'
            ]
            
            for selector in app_type_selectors:
                try:
                    if 'select' in selector:
                        await self.page.select_option(selector, "DESKTOP")
                    elif 'mat-select' in selector:
                        await self.safe_click(selector)
                        await self.human_delay(1, 2)
                        await self.safe_click('mat-option:has-text("Desktop application")')
                    else:
                        await self.safe_click(selector)
                    break
                except Exception:
                    continue
            
            # Enter credential name
            name_selectors = [
                'input[name="name"]',
                'input[formcontrolname="name"]',
                'input[aria-label*="Name"]',
                'input[placeholder*="name"]'
            ]
            
            name_entered = False
            for selector in name_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    await self.page.fill(selector, "")  # Clear existing text
                    await self.human_type(selector, credential_name)
                    name_entered = True
                    break
                except Exception:
                    continue
            
            if not name_entered:
                self.logger.warning("Could not find name field, proceeding without custom name")
            
            # Click Create button
            create_selectors = [
                'button:has-text("Create")',
                'button:has-text("CREATE")',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            if not await self.safe_click(create_selectors):
                raise Exception("Could not find Create button for OAuth credentials")
            
            await self.wait_for_navigation()
            await self.take_screenshot("13_credentials_created")
            
            # Wait for credentials to be created
            await asyncio.sleep(3)
            
            self.logger.info("✅ OAuth credentials created successfully")
            return {
                'success': True,
                'credential_name': credential_name,
                'message': 'OAuth credentials created successfully'
            }
            
        except Exception as e:
            log_error(e, "oauth_credentials_creation", additional_data={'credential_name': credential_name})
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot(f"error_oauth_creation_{credential_name}")
            raise
    
    @retry_async(context="json_download")
    async def download_json_file(self) -> Dict[str, Any]:
        """Download the OAuth credentials JSON file"""
        try:
            self.logger.info("📥 Downloading OAuth JSON file...")
            
            # Look for download button
            download_selectors = [
                'button:has-text("Download JSON")',
                'button:has-text("DOWNLOAD JSON")',
                'a:has-text("Download")',
                'button[aria-label*="Download"]',
                '[data-value="download"]'
            ]
            
            download_clicked = False
            for selector in download_selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        await self.safe_click(selector)
                        download_clicked = True
                        break
                except Exception:
                    continue
            
            if not download_clicked:
                # Try alternative approach - look for existing credentials and download
                await self._find_and_download_existing_credential()
            
            # Wait for download to complete
            await asyncio.sleep(5)
            
            # Find the downloaded file
            downloaded_file = await self._find_downloaded_json()
            
            if downloaded_file:
                self.logger.info(f"✅ JSON file downloaded: {downloaded_file}")
                return {
                    'success': True,
                    'file_path': downloaded_file,
                    'message': 'JSON file downloaded successfully'
                }
            else:
                raise Exception("Could not locate downloaded JSON file")
                
        except Exception as e:
            log_error(e, "json_download")
            if self.config.automation.screenshot_on_error:
                await self.take_screenshot("error_json_download")
            raise
    
    async def _find_and_download_existing_credential(self):
        """Find existing OAuth credential and download it"""
        try:
            # Look for existing OAuth credentials in the table
            credential_rows = await self.page.locator('tr').all()
            
            for row in credential_rows:
                # Check if this row contains an OAuth client
                if await row.locator('text="OAuth 2.0 Client IDs"').count() > 0:
                    # Look for download button in this row
                    download_btn = row.locator('button[aria-label*="Download"]')
                    if await download_btn.count() > 0:
                        await download_btn.click()
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def _find_downloaded_json(self) -> Optional[str]:
        """Find the most recently downloaded JSON file"""
        try:
            downloads_dir = Path(self.config.paths.downloads_dir)
            
            # Look for JSON files in downloads directory
            json_files = list(downloads_dir.glob("*.json"))
            
            if not json_files:
                return None
            
            # Find the most recent file
            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            
            # Verify it's a valid OAuth JSON file
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    if 'installed' in data or 'web' in data:
                        return str(latest_file)
            except Exception:
                pass
            
            return None
            
        except Exception:
            return None
    
    @retry_async(context="json_organization")
    async def organize_json_file(self, source_path: str, email: str) -> Dict[str, Any]:
        """Rename and move JSON file to organized location"""
        try:
            self.logger.info(f"📁 Organizing JSON file for {email}")
            
            # Create organized filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_email = email.replace('@', '_').replace('.', '_')
            new_filename = f"oauth_credentials_{safe_email}_{timestamp}.json"
            
            # Create output directory
            output_dir = Path(self.config.paths.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Move and rename file
            source = Path(source_path)
            destination = output_dir / new_filename
            
            if source.exists():
                source.rename(destination)
                
                self.logger.info(f"✅ JSON file organized: {destination}")
                return {
                    'success': True,
                    'original_path': source_path,
                    'new_path': str(destination),
                    'filename': new_filename,
                    'message': 'JSON file organized successfully'
                }
            else:
                raise Exception(f"Source file not found: {source_path}")
                
        except Exception as e:
            log_error(e, "json_organization", additional_data={'source_path': source_path, 'email': email})
            raise
    
    async def complete_oauth_setup(self, email: str, password: str, project_name: str = None) -> Dict[str, Any]:
        """Complete the entire OAuth setup process for a single account"""
        result = {
            'success': False,
            'email': email,
            'steps_completed': [],
            'errors': [],
            'files_created': [],
            'screenshots': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            self.current_email = email
            self.logger.info(f"Starting complete OAuth setup for {email}")
            
            # Branch by selected framework
            framework = self.config.automation.framework.lower()
            if framework == "selenium":
                # Use Selenium flow integrated from test driver
                try:
                    # Default project name if not provided
                    if not project_name:
                        project_name = self._generate_project_name(email)
                    self.logger.info("🌐 Initializing Selenium browser...")
                    # Initialize and run Selenium flow in automation instance
                    selenium_result = await self.automation.create_oauth_client(email, password, project_name)
                    if selenium_result.get('success'):
                        result['steps_completed'].append("selenium_flow_completed")
                        # Attempt to locate downloaded JSON and organize it
                        downloaded_path = await self._find_downloaded_json()
                        if downloaded_path:
                            organize_result = await self.organize_json_file(downloaded_path, email)
                            if organize_result.get('success'):
                                result['files_created'].append(organize_result.get('new_path'))
                        result['success'] = True
                        result['end_time'] = datetime.now()
                        self.logger.info("✅ Selenium OAuth setup completed successfully")
                        return result
                    else:
                        error_msg = selenium_result.get('error', 'Selenium flow failed')
                        result['errors'].append(error_msg)
                        result['end_time'] = datetime.now()
                        return result
                except Exception as e:
                    result['errors'].append(f"Selenium flow error: {str(e)}")
                    result['end_time'] = datetime.now()
                    return result
            
            # Playwright flow below
            # Step 0: Initialize browser first
            try:
                self.logger.info("🌐 Initializing browser...")
                if not await self.initialize_browser():
                    raise Exception("Failed to initialize browser")
                result['steps_completed'].append("browser_initialization")
                self.logger.info("✅ Step 0: Browser initialization completed")
            except Exception as e:
                result['errors'].append(f"Browser initialization failed: {str(e)}")
                raise
            
            # Generate project name if not provided (use unified generator)
            if not project_name:
                project_name = self.generate_project_name(email)
            
            self.current_project_id = project_name
            
            # Step 1: Login to Google Cloud
            try:
                login_success = await self.login_to_google_cloud(email, password)
                if login_success:
                    result['steps_completed'].append("login")
                    self.logger.info("✅ Step 1: Login completed")
                else:
                    # Login returned False - likely email verification required
                    result['steps_completed'].append("verification_required")
                    result['errors'].append("Email verification required - webdriver closed for this email")
                    self.logger.info("📧 Email verification required - skipping to next email")
                    
                    # Mark as verification case (not a failure)
                    result['verification_required'] = True
                    result['success'] = False
                    result['end_time'] = datetime.now()
                    return result
            except Exception as e:
                result['errors'].append(f"Login failed: {str(e)}")
                raise
            
            # Step 2: Create/Select Project
            try:
                await self.create_or_select_project(project_name)
                result['steps_completed'].append("project_creation")
                self.logger.info("✅ Step 2: Project creation completed")
            except Exception as e:
                result['errors'].append(f"Project creation failed: {str(e)}")
                raise
            
            # Step 3: Enable Gmail API
            try:
                await self.enable_gmail_api()
                result['steps_completed'].append("gmail_api")
                self.logger.info("✅ Step 3: Gmail API enabled")
            except Exception as e:
                result['errors'].append(f"Gmail API enable failed: {str(e)}")
                raise
            
            # Step 4: Setup OAuth Consent Screen with complete workflow
            try:
                await self.setup_oauth_consent_screen(email)
                result['steps_completed'].append("oauth_consent")
                self.logger.info("✅ Step 4: OAuth consent screen configured")
            except Exception as e:
                result['errors'].append(f"OAuth consent setup failed: {str(e)}")
                raise
            
            # Step 5: Create OAuth Credentials and Download JSON
            try:
                await self.create_oauth_credentials(email)
                result['steps_completed'].append("oauth_credentials")
                self.logger.info("✅ Step 5: OAuth credentials created and JSON downloaded")
            except Exception as e:
                result['errors'].append(f"OAuth credentials creation failed: {str(e)}")
                raise
            
            # Step 6: File Explorer Integration and JSON Renaming
            try:
                file_explorer_success = await self.handle_file_explorer_and_rename(email)
                if file_explorer_success:
                    result['steps_completed'].append("file_explorer_integration")
                    result['files_created'].append(f"{email}.json")
                    self.logger.info("✅ Step 6: File Explorer integration and JSON renaming completed")
                else:
                    # Fallback to original rename method
                    self.logger.info("🔄 Falling back to alternative JSON rename method...")
                    rename_success = await self.rename_downloaded_json(email)
                    if rename_success:
                        result['steps_completed'].append("json_rename_fallback")
                        result['files_created'].append(f"{email.replace('@', '_').replace('.', '_')}.json")
                        self.logger.info("✅ Step 6: JSON file renamed (fallback method)")
                    else:
                        self.logger.warning("⚠️ JSON file rename failed, but continuing...")
            except Exception as e:
                self.logger.warning(f"⚠️ File Explorer integration failed: {str(e)}, trying fallback...")
                try:
                    # Fallback to original rename method
                    rename_success = await self.rename_downloaded_json(email)
                    if rename_success:
                        result['steps_completed'].append("json_rename_fallback")
                        result['files_created'].append(f"{email.replace('@', '_').replace('.', '_')}.json")
                        self.logger.info("✅ Step 6: JSON file renamed (fallback method)")
                except Exception as fallback_error:
                    self.logger.warning(f"⚠️ Fallback rename also failed: {str(fallback_error)}, but continuing...")
                    result['errors'].append(f"JSON rename failed: {str(e)}, fallback also failed: {str(fallback_error)}")
            
            # Mark as successful
            result['success'] = True
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
            
            # Save success report
            try:
                success_screenshot = await self.take_screenshot(f"success_{email.replace('@', '_')}")
                email_reporter.save_success_report(
                    email=email,
                    oauth_data={
                        'project_name': project_name,
                        'steps_completed': result['steps_completed'],
                        'files_created': result['files_created'],
                        'duration': result['duration']
                    },
                    screenshot_path=success_screenshot,
                    additional_data={
                        'automation_version': 'playwright_enhanced',
                        'completion_time': result['end_time'].isoformat()
                    }
                )
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to save success report: {str(e)}")
            
            self.logger.info(f"🎉 OAuth setup completed successfully for {email}")
            return result
            
        except Exception as e:
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
            
            # Save error report
            try:
                error_screenshot = await self.take_screenshot(f"error_{email.replace('@', '_')}")
                email_reporter.save_error_report(
                    email=email,
                    error_type="oauth_setup_failure",
                    error_message=str(e),
                    screenshot_path=error_screenshot,
                    additional_data={
                        'steps_completed': result['steps_completed'],
                        'project_name': project_name,
                        'duration': result['duration'],
                        'automation_version': 'playwright_enhanced'
                    }
                )
            except Exception as report_error:
                self.logger.warning(f"⚠️ Failed to save error report: {str(report_error)}")
            
            log_error(e, "complete_oauth_setup", additional_data={
                'email': email,
                'steps_completed': result['steps_completed'],
                'project_name': project_name
            })
            
            self.logger.error(f"❌ OAuth setup failed for {email}: {str(e)}")
            raise
        
        finally:
            # Cleanup browser resources
            try:
                await self.cleanup()
            except Exception:
                pass
    
    def _generate_project_name(self, email: str) -> str:
        """Generate a unique project name based on email (4-30 characters)"""
        # Extract username from email
        username = email.split('@')[0]
        # Clean username for project name
        clean_username = re.sub(r'[^a-zA-Z0-9]', '', username)
        
        # Generate a shorter timestamp (last 6 digits)
        timestamp = str(int(time.time()))[-6:]
        
        # Calculate available space for username
        # Format: "gmail-oauth-{username}-{timestamp}"
        # "gmail-oauth-" = 12 chars, "-" = 1 char, timestamp = 6 chars
        # Total fixed chars = 19, so username can be max 11 chars (30 - 19 = 11)
        max_username_length = 11
        clean_username = clean_username[:max_username_length]
        
        # Create project name
        project_name = f"gmail-oauth-{clean_username}-{timestamp}"
        
        # Final safety check - if still too long, use shorter format
        if len(project_name) > 30:
            # Fallback to just "gmail-oauth-{timestamp}" (18 chars)
            project_name = f"gmail-oauth-{timestamp}"
        
        # Ensure minimum length (4 chars)
        if len(project_name) < 4:
            project_name = f"gmail-{timestamp}"
        
        return project_name.lower()
    
    async def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive report of OAuth setup results"""
        try:
            report = {
                'summary': {
                    'total_accounts': len(results),
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0.0
                },
                'details': [],
                'errors': [],
                'files_created': [],
                'generated_at': datetime.now().isoformat()
            }
            
            for result in results:
                if result['success']:
                    report['summary']['successful'] += 1
                else:
                    report['summary']['failed'] += 1
                
                report['details'].append({
                    'email': result['email'],
                    'success': result['success'],
                    'steps_completed': result['steps_completed'],
                    'errors': result['errors'],
                    'files_created': result['files_created'],
                    'duration': result.get('duration', 0)
                })
                
                # Collect all errors
                report['errors'].extend(result['errors'])
                
                # Collect all files created
                report['files_created'].extend(result['files_created'])
            
            # Calculate success rate
            if report['summary']['total_accounts'] > 0:
                report['summary']['success_rate'] = (
                    report['summary']['successful'] / 
                    report['summary']['total_accounts'] * 100
                )
            
            return report
            
        except Exception as e:
            log_error(e, "report_generation")
            raise