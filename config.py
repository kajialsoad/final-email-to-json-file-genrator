#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management System
Centralized configuration for the Gmail OAuth automation
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class BrowserConfig:
    """Browser configuration settings"""
    headless: bool = False
    stealth_mode: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    viewport_width: int = 1366
    viewport_height: int = 768
    timeout: int = 30000  # 30 seconds
    navigation_timeout: int = 60000  # 60 seconds
    slow_mo: int = 50  # Reduced for better performance
    window_position_x: int = 100  # Fixed window position
    window_position_y: int = 100  # Fixed window position
    disable_animations: bool = True  # Disable animations for stability
    force_device_scale_factor: float = 1.0  # Fixed scaling
    
@dataclass
class AutomationConfig:
    """Automation behavior settings"""
    max_retries: int = 3
    retry_delay: float = 2.0
    human_delay_min: float = 0.5
    human_delay_max: float = 2.0
    typing_delay_min: int = 50
    typing_delay_max: int = 150
    screenshot_on_error: bool = True
    screenshot_on_success: bool = False
    concurrent_limit: int = 3
    
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
    block_ads: bool = True

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
        
        # Basic arguments
        args.extend([
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-default-apps',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
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
            args.extend([
                '--disable-background-networking',
                '--disable-background-timer-throttling'
            ])
        
        # Proxy settings
        if self.security.use_proxy and self.security.proxy_url:
            args.append(f'--proxy-server={self.security.proxy_url}')
        
        return {
            'headless': self.browser.headless,
            'args': args,
            'slow_mo': self.browser.slow_mo if not self.browser.headless else 0
        }
    
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
    
    def reset_to_defaults(self):
        """Reset all configurations to defaults"""
        self.browser = BrowserConfig()
        self.automation = AutomationConfig()
        self.paths = PathConfig()
        self.ui = UIConfig()
        self.security = SecurityConfig()
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a specific file"""
        try:
            config_data = {
                'browser': asdict(self.browser),
                'automation': asdict(self.automation),
                'paths': asdict(self.paths),
                'ui': asdict(self.ui),
                'security': asdict(self.security),
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

# Apply environment overrides on import
apply_env_overrides()