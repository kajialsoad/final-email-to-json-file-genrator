"""
Automation Factory for selecting between Playwright and Selenium frameworks
"""

from typing import Union
from config import get_config, ConfigManager
from google_cloud_automation import GoogleCloudAutomation
from selenium_automation import SeleniumAutomation

class AutomationFactory:
    """Factory class for creating automation instances based on framework selection"""
    
    @staticmethod
    def create_automation(config: ConfigManager = None) -> Union[GoogleCloudAutomation, SeleniumAutomation]:
        """
        Create automation instance based on framework configuration
        
        Args:
            config: Configuration manager containing framework selection
            
        Returns:
            Automation instance (either Playwright GoogleCloudAutomation or SeleniumAutomation)
        """
        cfg = config or get_config()
        framework = cfg.automation.framework.lower()
        
        if framework == "selenium":
            return SeleniumAutomation(cfg)
        elif framework == "playwright":
            return GoogleCloudAutomation()
        else:
            # Default to Playwright if unknown framework
            return GoogleCloudAutomation()
    
    @staticmethod
    def get_available_frameworks() -> list:
        """Get list of available automation frameworks"""
        return ["playwright", "selenium"]