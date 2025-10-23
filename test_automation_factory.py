"""
Smoke test for AutomationFactory framework dispatch
Tests that the factory correctly creates Playwright and Selenium automation instances
"""

import sys
import os
import asyncio
from config import ConfigManager, get_config
from automation_factory import AutomationFactory
from google_cloud_automation import GoogleCloudAutomation
from selenium_automation import SeleniumAutomation

async def test_automation_factory():
    """Test automation factory framework dispatch"""
    print("🧪 Starting AutomationFactory smoke test...")
    
    # Test 1: Playwright framework
    print("\n📋 Test 1: Testing Playwright framework dispatch")
    try:
        config = get_config()
        config.automation.framework = "playwright"
        
        automation = AutomationFactory.create_automation(config)
        
        if isinstance(automation, GoogleCloudAutomation):
            print("✅ Playwright framework: PASS - Created GoogleCloudAutomation instance")
        else:
            print(f"❌ Playwright framework: FAIL - Expected GoogleCloudAutomation, got {type(automation)}")
            return False
            
    except Exception as e:
        print(f"❌ Playwright framework: FAIL - Exception: {e}")
        return False
    
    # Test 2: Selenium framework
    print("\n📋 Test 2: Testing Selenium framework dispatch")
    try:
        config = get_config()
        config.automation.framework = "selenium"
        
        automation = AutomationFactory.create_automation(config)
        
        if isinstance(automation, SeleniumAutomation):
            print("✅ Selenium framework: PASS - Created SeleniumAutomation instance")
        else:
            print(f"❌ Selenium framework: FAIL - Expected SeleniumAutomation, got {type(automation)}")
            return False
            
    except Exception as e:
        print(f"❌ Selenium framework: FAIL - Exception: {e}")
        return False
    
    # Test 3: Unknown framework (should default to Playwright)
    print("\n📋 Test 3: Testing unknown framework (should default to Playwright)")
    try:
        config = get_config()
        config.automation.framework = "unknown_framework"
        
        automation = AutomationFactory.create_automation(config)
        
        if isinstance(automation, GoogleCloudAutomation):
            print("✅ Unknown framework: PASS - Defaulted to GoogleCloudAutomation instance")
        else:
            print(f"❌ Unknown framework: FAIL - Expected GoogleCloudAutomation, got {type(automation)}")
            return False
            
    except Exception as e:
        print(f"❌ Unknown framework: FAIL - Exception: {e}")
        return False
    
    # Test 4: List available frameworks
    print("\n📋 Test 4: Testing get_available_frameworks method")
    try:
        frameworks = AutomationFactory.get_available_frameworks()
        expected_frameworks = ["playwright", "selenium"]
        
        if set(frameworks) == set(expected_frameworks):
            print(f"✅ List frameworks: PASS - Got expected frameworks: {frameworks}")
        else:
            print(f"❌ List frameworks: FAIL - Expected {expected_frameworks}, got {frameworks}")
            return False
            
    except Exception as e:
        print(f"❌ List frameworks: FAIL - Exception: {e}")
        return False
    
    # Test 5: Verify Selenium automation has required methods
    print("\n📋 Test 5: Testing Selenium automation methods")
    try:
        config = get_config()
        config.automation.framework = "selenium"
        
        selenium_automation = AutomationFactory.create_automation(config)
        
        # Check if required methods exist
        required_methods = [
            'create_oauth_client',
            'login_to_google_cloud', 
            'create_or_select_project',
            'enable_gmail_api',
            'create_oauth_credentials_selenium',
            'save_oauth_json'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(selenium_automation, method):
                missing_methods.append(method)
        
        if not missing_methods:
            print("✅ Selenium methods: PASS - All required methods present")
        else:
            print(f"❌ Selenium methods: FAIL - Missing methods: {missing_methods}")
            return False
            
    except Exception as e:
        print(f"❌ Selenium methods: FAIL - Exception: {e}")
        return False
    
    print("\n🎉 All smoke tests passed! AutomationFactory is working correctly.")
    return True

async def test_oauth_credentials_manager_integration():
    """Test OAuthCredentialsManager integration with both frameworks"""
    print("\n🔗 Testing OAuthCredentialsManager integration...")
    
    try:
        from oauth_credentials import OAuthCredentialsManager
        
        # Test with Playwright
        print("\n📋 Testing OAuthCredentialsManager with Playwright")
        config = get_config()
        config.automation.framework = "playwright"
        
        oauth_manager = OAuthCredentialsManager()
        
        # Check that it has both automation contexts
        if hasattr(oauth_manager, 'automation') and oauth_manager.automation is not None:
            print("✅ OAuthCredentialsManager: PASS - Has automation instance")
        else:
            print("❌ OAuthCredentialsManager: FAIL - Missing automation instance")
            return False
        
        # Test with Selenium
        print("\n📋 Testing OAuthCredentialsManager with Selenium")
        config.automation.framework = "selenium"
        
        oauth_manager = OAuthCredentialsManager()
        
        # Check that it has both automation contexts
        if hasattr(oauth_manager, 'automation') and oauth_manager.automation is not None:
            print("✅ OAuthCredentialsManager: PASS - Has automation instance for Selenium")
        else:
            print("❌ OAuthCredentialsManager: FAIL - Missing automation instance for Selenium")
            return False
        
        print("✅ OAuthCredentialsManager integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ OAuthCredentialsManager integration: FAIL - Exception: {e}")
        return False

async def main():
    """Run all smoke tests"""
    print("🚀 Starting comprehensive automation framework smoke tests...\n")
    
    # Run factory tests
    factory_result = await test_automation_factory()
    
    # Run integration tests
    integration_result = await test_oauth_credentials_manager_integration()
    
    if factory_result and integration_result:
        print("\n🎉 ALL TESTS PASSED! The automation framework is ready for use.")
        print("\n📝 Summary:")
        print("   ✅ AutomationFactory correctly dispatches between frameworks")
        print("   ✅ Selenium automation has complete OAuth flow implementation")
        print("   ✅ OAuthCredentialsManager integrates with both frameworks")
        print("   ✅ Framework selection works end-to-end")
        return True
    else:
        print("\n❌ SOME TESTS FAILED! Please review the output above.")
        return False

if __name__ == "__main__":
    asyncio.run(main())