#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management System
Centralized configuration for the Gmail OAuth automation
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class BrowserConfig:
    """Browser configuration settings"""
    headless: bool = False
    stealth_mode: bool = True
    viewport_width: int = 1366  # Better compatibility with Google's responsive design
    viewport_height: int = 768   # Standard laptop resolution
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  # Latest Chrome user agent
    timeout: int = 30000  # Reduced from 60000 to 30000 (30 seconds) - faster screenshot timeout
    navigation_timeout: int = 45000  # Reduced from 90000 to 45000 (45 seconds) - faster navigation
    slow_mo: int = 50  # Reduced from 100 to 50 - faster actions while still human-like
    devtools: bool = False
    disable_web_security: bool = False
    ignore_https_errors: bool = True
    window_position_x: int = 100  # X position for browser window
    window_position_y: int = 100  # Y position for browser window
    force_device_scale_factor: float = 1.0  # Device scale factor for high DPI displays
    disable_animations: bool = True  # Changed to True - disable animations for faster loading
    # Optional browser channel (e.g., "chrome", "chrome-beta", "msedge")
    browser_channel: str = ""
    # Use persistent (non-incognito) context to retain cookies/storage
    use_persistent_context: bool = True
    # Anti-detection settings
    randomize_viewport: bool = True  # Randomize viewport size slightly
    use_real_chrome_profile: bool = True  # Use real Chrome profile path
    disable_automation_flags: bool = True  # Remove automation indicators
    # Enhanced anti-detection measures
    randomize_user_agent: bool = True  # Randomize user agent from pool
    randomize_timing: bool = True  # Add random delays to actions
    use_realistic_mouse_movements: bool = True  # Simulate realistic mouse movements
    vary_typing_speed: bool = True  # Vary typing speed to appear human
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent from a pool of realistic options"""
        user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            
            # Chrome on Android (mobile)
            "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
            
            # Safari on iOS (mobile)
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
        return random.choice(user_agents) if self.randomize_user_agent else self.user_agent
    
    def get_random_viewport(self) -> tuple[int, int]:
        """Get randomized viewport dimensions"""
        if not self.randomize_viewport:
            return (self.viewport_width, self.viewport_height)
        
        # Common viewport sizes with slight randomization
        base_viewports = [
            (1366, 768), (1920, 1080), (1440, 900), (1536, 864),
            (1280, 720), (1600, 900), (1024, 768), (1280, 800)
        ]
        
        base_width, base_height = random.choice(base_viewports)
        # Add small random variation (±50 pixels)
        width = base_width + random.randint(-50, 50)
        height = base_height + random.randint(-50, 50)
        
        # Ensure minimum viable size
        width = max(width, 1024)
        height = max(height, 600)
        
        return (width, height)

@dataclass
class AutomationConfig:
    """Automation configuration settings"""
    framework: str = "playwright"  # "playwright" or "selenium"
    max_retries: int = 2  # Reduced from 3 to 2 - fewer retries for faster execution
    retry_delay: float = 1.5  # Reduced from 3.0 to 1.5 - faster retry delays
    human_delay_min: float = 0.3  # Reduced from 1.0 to 0.3 - faster human delays
    human_delay_max: float = 1.5  # Reduced from 3.0 to 1.5 - faster human delays
    typing_delay_min: int = 30  # Reduced from 50 to 30 - faster typing
    typing_delay_max: int = 80  # Reduced from 150 to 80 - faster typing
    screenshot_on_error: bool = True
    screenshot_on_success: bool = False
    concurrent_limit: int = 3
    project_creation_timeout: int = 90000  # Reduced from 180000 to 90000 (1.5 minutes)
    project_selection_timeout: int = 45000   # Reduced from 90000 to 45000 (45 seconds)
    api_enablement_timeout: int = 60000     # Reduced from 120000 to 60000 (1 minute)
    oauth_consent_timeout: int = 45000       # Reduced from 90000 to 45000 (45 seconds)
    credentials_creation_timeout: int = 60000  # Reduced from 120000 to 60000 (1 minute)
    # Human-like interaction delays
    action_delay_min: float = 0.2  # Reduced from 0.5 to 0.2 - faster actions
    action_delay_max: float = 1.0  # Reduced from 2.0 to 1.0 - faster actions
    click_delay_min: float = 0.05   # Reduced from 0.1 to 0.05 - faster clicks
    click_delay_max: float = 0.3   # Reduced from 0.5 to 0.3 - faster clicks
    form_fill_delay_min: float = 0.4  # Reduced from 0.8 to 0.4 - faster form filling
    form_fill_delay_max: float = 1.5  # Reduced from 2.5 to 1.5 - faster form filling
    # Loading and waiting configurations
    max_loading_wait: int = 30000  # Reduced from 60000 to 30000 (30 seconds)
    loading_check_interval: int = 1000  # Reduced from 2000 to 1000 - check more frequently
    # Project creation specific settings
    project_creation_max_attempts: int = 3  # Reduced from 5 to 3 - fewer attempts for faster execution
    project_verification_attempts: int = 2  # Reduced from 3 to 2 - fewer verification attempts
    create_button_wait_timeout: int = 15000  # Reduced from 30000 to 15000 (15 seconds)
    form_load_timeout: int = 25000  # Reduced from 45000 to 25000 (25 seconds)
    
    # Enhanced project creation timeouts (all significantly reduced)
    project_navigation_timeout: int = 25000  # Reduced from 45000 to 25000 (25 seconds)
    project_form_interaction_timeout: int = 30000  # Reduced from 60000 to 30000 (30 seconds)
    project_submission_timeout: int = 60000  # Reduced from 120000 to 60000 (1 minute)
    project_creation_verification_timeout: int = 90000  # Reduced from 180000 to 90000 (1.5 minutes)
    project_api_dashboard_timeout: int = 45000  # Reduced from 90000 to 45000 (45 seconds)
    project_selector_update_timeout: int = 30000  # Reduced from 60000 to 30000 (30 seconds)
    
    # Network and loading timeouts (all reduced)
    project_network_idle_timeout: int = 15000  # Reduced from 30000 to 15000 (15 seconds)
    project_dom_content_timeout: int = 10000  # Reduced from 20000 to 10000 (10 seconds)
    project_page_load_timeout: int = 25000  # Reduced from 45000 to 25000 (25 seconds)
    
    # Element interaction timeouts (all reduced)
    project_element_visible_timeout: int = 8000  # Reduced from 15000 to 8000 (8 seconds)
    project_element_clickable_timeout: int = 5000  # Reduced from 10000 to 5000 (5 seconds)
    project_element_stable_timeout: int = 3000  # Reduced from 5000 to 3000 (3 seconds)
    
    # Verification timeouts (all reduced)
    verification_initial_wait: int = 4000  # Reduced from 8000 to 4000 (4 seconds)
    verification_network_stabilization: int = 3000  # Reduced from 5000 to 3000 (3 seconds)
    verification_retry_delay: int = 2000  # Reduced from 3000 to 2000 (2 seconds)
    verification_url_change_timeout: int = 15000  # Reduced from 30000 to 15000 (15 seconds)
    verification_content_check_timeout: int = 8000  # Reduced from 15000 to 8000 (8 seconds)

@dataclass
class ProjectCreationTimeouts:
    """Centralized timeout configuration for project creation workflow"""
    # Main workflow phase timeouts (all significantly reduced)
    navigation: int = 25000  # Reduced from 45000 to 25000 - Navigating to project creation page
    form_interaction: int = 30000  # Reduced from 60000 to 30000 - Form interactions and filling
    submission: int = 60000  # Reduced from 120000 to 60000 - Project submission processing
    verification: int = 90000  # Reduced from 180000 to 90000 - Verifying project creation success
    api_dashboard: int = 45000  # Reduced from 90000 to 45000 - Accessing API dashboard
    selector_update: int = 30000  # Reduced from 60000 to 30000 - Project selector update
    
    # Network and loading timeouts (all reduced)
    network_idle: int = 15000  # Reduced from 30000 to 15000 - Network idle state
    dom_content: int = 10000  # Reduced from 20000 to 10000 - DOM content loaded
    page_load: int = 25000  # Reduced from 45000 to 25000 - Complete page load
    
    # Element interaction timeouts (all reduced)
    element_visible: int = 8000  # Reduced from 15000 to 8000 - Elements to become visible
    element_clickable: int = 5000  # Reduced from 10000 to 5000 - Elements to become clickable
    element_stable: int = 3000  # Reduced from 5000 to 3000 - Elements to stabilize
    
    # Verification phase timeouts (all reduced)
    initial_wait: int = 4000  # Reduced from 8000 to 4000 - Initial wait before verification
    network_stabilization: int = 3000  # Reduced from 5000 to 3000 - Network stabilization
    retry_delay: int = 2000  # Reduced from 3000 to 2000 - Delay between verification attempts
    url_change: int = 15000  # Reduced from 30000 to 15000 - URL changes
    content_check: int = 8000  # Reduced from 15000 to 8000 - Content verification
    
    # UI interaction timeouts (all reduced)
    create_button_wait: int = 15000  # Reduced from 30000 to 15000 - Create button to appear
    form_load: int = 25000  # Reduced from 45000 to 25000 - Project creation form to load
    
    def get_timeout(self, phase: str) -> int:
        """Get timeout for a specific phase"""
        return getattr(self, phase, 30000)  # Default to 30 seconds
    
    def get_all_timeouts(self) -> dict:
        """Get all timeout configurations as a dictionary"""
        return {
            'navigation': self.navigation,
            'form_interaction': self.form_interaction,
            'submission': self.submission,
            'verification': self.verification,
            'api_dashboard': self.api_dashboard,
            'selector_update': self.selector_update,
            'network_idle': self.network_idle,
            'dom_content': self.dom_content,
            'page_load': self.page_load,
            'element_visible': self.element_visible,
            'element_clickable': self.element_clickable,
            'element_stable': self.element_stable,
            'initial_wait': self.initial_wait,
            'network_stabilization': self.network_stabilization,
            'retry_delay': self.retry_delay,
            'url_change': self.url_change,
            'content_check': self.content_check,
            'create_button_wait': self.create_button_wait,
            'form_load': self.form_load
        }

@dataclass
class PathConfig:
    """File and directory paths"""
    output_dir: str = "output"
    reports_dir: str = "reports"
    logs_dir: str = "logs"
    screenshots_dir: str = "screenshots"
    downloads_dir: str = "downloads"
    temp_dir: str = "temp"
    
@dataclass
class UIConfig:
    """UI appearance settings"""
    theme: str = "light"  # light, dark
    window_width: int = 1000
    window_height: int = 700
    font_family: str = "Segoe UI"
    font_size: int = 10
    log_max_lines: int = 1000
    
@dataclass
class SecurityConfig:
    """Security and privacy settings"""
    clear_browser_data: bool = True
    use_proxy: bool = False
    proxy_url: str = ""
    disable_images: bool = False
    disable_javascript: bool = False
    block_ads: bool = False

@dataclass
class ApproverConfig:
    """Approver email configuration for verification handling"""
    enabled: bool = False
    approver_email: str = ""
    approver_password: str = ""
    auto_handle_verification: bool = True
    verification_timeout: int = 300  # 5 minutes
    check_interval: int = 30  # 30 seconds
    max_verification_attempts: int = 5
    handle_speedbump_popup: bool = True  # Handle "আমি বুঝি" button automatically

class ConfigManager:
    """Configuration management system"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config_dir = self.config_file.parent
        self.config_dir.mkdir(exist_ok=True)
        
        # Default configurations
        self.browser = BrowserConfig()
        self.automation = AutomationConfig()
        self.paths = PathConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self.approver = ApproverConfig()
        self.project_timeouts = ProjectCreationTimeouts()
        
        # Load existing config if available
        self.load_config()
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.paths.output_dir,
            self.paths.reports_dir,
            self.paths.logs_dir,
            self.paths.screenshots_dir,
            self.paths.downloads_dir,
            self.paths.temp_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Update configurations
                if 'browser' in data:
                    self.browser = BrowserConfig(**data['browser'])
                if 'automation' in data:
                    self.automation = AutomationConfig(**data['automation'])
                if 'paths' in data:
                    self.paths = PathConfig(**data['paths'])
                if 'ui' in data:
                    self.ui = UIConfig(**data['ui'])
                if 'security' in data:
                    self.security = SecurityConfig(**data['security'])
                if 'approver' in data:
                    self.approver = ApproverConfig(**data['approver'])
                
                return True
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
        
        return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            config_data = {
                'browser': asdict(self.browser),
                'automation': asdict(self.automation),
                'paths': asdict(self.paths),
                'ui': asdict(self.ui),
                'security': asdict(self.security),
                'approver': asdict(self.approver),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error: Failed to save config: {e}")
            return False
    
    def get_browser_args(self) -> Dict[str, Any]:
        """Get browser launch arguments"""
        args = []
        
        # Anti-detection arguments (most important)
        if self.browser.disable_automation_flags:
            args.extend([
                '--disable-blink-features=AutomationControlled',
                '--exclude-switches=enable-automation',
                '--disable-extensions-except',
                '--disable-plugins-discovery',
                '--disable-default-apps',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-infobars',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-background-networking',
                '--disable-sync',
                '--metrics-recording-only',
                '--no-report-upload',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config'
            ])
        
        # Basic arguments
        args.extend([
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--disable-plugins'
        ])
        
        # UI Stability arguments
        args.extend([
            '--disable-smooth-scrolling',  # Prevent smooth scrolling that can cause UI jumps
            '--disable-animations',  # Disable CSS animations
            '--disable-transitions',  # Disable CSS transitions
            '--disable-web-security',  # For better automation compatibility
            '--disable-features=TranslateUI',  # Disable translate popup
            '--disable-ipc-flooding-protection',  # Better automation performance
            '--disable-hang-monitor',  # Prevent hang detection
            '--disable-prompt-on-repost',  # Prevent repost prompts
            '--disable-domain-reliability',  # Disable domain reliability monitoring
            '--disable-component-extensions-with-background-pages',  # Disable background extensions
            '--disable-client-side-phishing-detection',  # Disable phishing detection
            '--disable-sync',  # Disable Chrome sync
            '--disable-default-apps',  # Disable default apps
            '--disable-popup-blocking',  # Allow popups for OAuth flow
            '--disable-translate',  # Disable translate feature
            '--no-first-run',  # Skip first run experience
            '--no-default-browser-check',  # Skip default browser check
            '--disable-infobars',  # Disable info bars
            '--disable-notifications',  # Disable notifications
            '--disable-save-password-bubble',  # Disable save password prompts
        ])
        
        # Window positioning and sizing
        if not self.browser.headless:
            args.extend([
                f'--window-position={self.browser.window_position_x},{self.browser.window_position_y}',
                f'--window-size={self.browser.viewport_width},{self.browser.viewport_height}',
                f'--force-device-scale-factor={self.browser.force_device_scale_factor}',
                '--start-maximized' if self.browser.viewport_width >= 1920 else '--start-normal',
                '--disable-gpu-sandbox',  # Better GPU performance
                '--enable-gpu-rasterization',  # Better rendering performance
            ])
        
        # Security settings
        if self.security.disable_images:
            args.append('--blink-settings=imagesEnabled=false')
        
        if self.security.block_ads:
            # Keep timer throttling off for stability, but allow networking
            args.extend([
                '--disable-background-timer-throttling'
            ])
        
        # Proxy settings
        if self.security.use_proxy and self.security.proxy_url:
            args.append(f'--proxy-server={self.security.proxy_url}')
        
        opts: Dict[str, Any] = {
            'headless': self.browser.headless,
            'args': args,
            'slow_mo': self.browser.slow_mo if not self.browser.headless else 0,
            'devtools': self.browser.devtools
        }

        # Use installed browser channel if specified (e.g., Google Chrome)
        if self.browser.browser_channel:
            opts['channel'] = self.browser.browser_channel

        return opts
    
    def get_page_options(self) -> Dict[str, Any]:
        """Get page configuration options"""
        return {
            'default_timeout': self.browser.timeout,
            'default_navigation_timeout': self.browser.navigation_timeout
        }
    
    def update_browser_config(self, **kwargs):
        """Update browser configuration"""
        for key, value in kwargs.items():
            if hasattr(self.browser, key):
                setattr(self.browser, key, value)
    
    def update_automation_config(self, **kwargs):
        """Update automation configuration"""
        for key, value in kwargs.items():
            if hasattr(self.automation, key):
                setattr(self.automation, key, value)
    
    def update_ui_config(self, **kwargs):
        """Update UI configuration"""
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
    
    def update_approver_config(self, **kwargs):
        """Update approver configuration"""
        for key, value in kwargs.items():
            if hasattr(self.approver, key):
                setattr(self.approver, key, value)
    
    def reset_to_defaults(self):
        """Reset all configurations to defaults"""
        self.browser = BrowserConfig()
        self.automation = AutomationConfig()
        self.paths = PathConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
        self.approver = ApproverConfig()
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a specific file"""
        try:
            config_data = {
                'browser': asdict(self.browser),
                'automation': asdict(self.automation),
                'paths': asdict(self.paths),
                'ui': asdict(self.ui),
                'security': asdict(self.security),
                'approver': asdict(self.approver),
                'exported_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a specific file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Update configurations
            if 'browser' in data:
                self.browser = BrowserConfig(**data['browser'])
            if 'automation' in data:
                self.automation = AutomationConfig(**data['automation'])
            if 'paths' in data:
                self.paths = PathConfig(**data['paths'])
            if 'ui' in data:
                self.ui = UIConfig(**data['ui'])
            if 'security' in data:
                self.security = SecurityConfig(**data['security'])
            if 'approver' in data:
                self.approver = ApproverConfig(**data['approver'])
            
            return True
        except Exception:
            return False
    
    def get_full_path(self, relative_path: str, path_type: str = "output") -> str:
        """Get full path for a relative path"""
        base_paths = {
            "output": self.paths.output_dir,
            "reports": self.paths.reports_dir,
            "logs": self.paths.logs_dir,
            "screenshots": self.paths.screenshots_dir,
            "downloads": self.paths.downloads_dir,
            "temp": self.paths.temp_dir
        }
        
        base_path = base_paths.get(path_type, self.paths.output_dir)
        return str(Path(base_path) / relative_path)
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.paths.output_dir,
            self.paths.reports_dir,
            self.paths.logs_dir,
            self.paths.screenshots_dir,
            self.paths.downloads_dir,
            self.paths.temp_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Global configuration instance
config = ConfigManager()

# Convenience functions
def get_config() -> ConfigManager:
    """Get the global configuration instance"""
    return config

def save_config() -> bool:
    """Save the current configuration"""
    return config.save_config()

def load_config() -> bool:
    """Load configuration from file"""
    return config.load_config()

# Environment variable overrides
def apply_env_overrides():
    """Apply environment variable overrides"""
    # Browser settings
    if os.getenv('HEADLESS'):
        config.browser.headless = os.getenv('HEADLESS').lower() == 'true'
    
    if os.getenv('STEALTH_MODE'):
        config.browser.stealth_mode = os.getenv('STEALTH_MODE').lower() == 'true'
    
    if os.getenv('TIMEOUT'):
        try:
            config.browser.timeout = int(os.getenv('TIMEOUT'))
        except ValueError:
            pass

    # Prefer a specific browser channel (e.g., chrome)
    if os.getenv('BROWSER_CHANNEL'):
        config.browser.browser_channel = os.getenv('BROWSER_CHANNEL')
    
    # Switch to persistent (non-incognito) browser context
    if os.getenv('USE_PERSISTENT_CONTEXT'):
        try:
            config.browser.use_persistent_context = os.getenv('USE_PERSISTENT_CONTEXT').lower() in ['true', '1', 'yes']
        except Exception:
            pass
    
    # Automation settings
    if os.getenv('MAX_RETRIES'):
        try:
            config.automation.max_retries = int(os.getenv('MAX_RETRIES'))
        except ValueError:
            pass
    
    if os.getenv('RETRY_DELAY'):
        try:
            config.automation.retry_delay = float(os.getenv('RETRY_DELAY'))
        except ValueError:
            pass
    
    # Path settings
    if os.getenv('OUTPUT_DIR'):
        config.paths.output_dir = os.getenv('OUTPUT_DIR')
    
    if os.getenv('LOGS_DIR'):
        config.paths.logs_dir = os.getenv('LOGS_DIR')

    # Security settings
    if os.getenv('BLOCK_ADS'):
        try:
            config.security.block_ads = os.getenv('BLOCK_ADS').lower() in ['true','1','yes']
        except Exception:
            pass

# Apply environment overrides on import
apply_env_overrides()