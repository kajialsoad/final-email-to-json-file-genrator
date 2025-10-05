#!/usr/bin/env python3
"""
Test script for Gmail OAuth Playwright implementation
"""

import sys
import os
import asyncio
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_imports():
    """Test basic Python imports"""
    print("Testing basic imports...")
    try:
        import json
        import logging
        import tkinter as tk
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Basic import error: {e}")
        return False

def test_core_modules():
    """Test core module imports"""
    print("\n--- Testing Core Module Imports ---")
    try:
        # Test config module
        from config import get_config, ConfigManager
        print("✓ Config module imported")
        
        # Test error handler
        from error_handler import ErrorHandler, ErrorType, error_handler
        print("✓ Error handler module imported")
        
        # Test playwright automation
        from playwright_automation import PlaywrightAutomationEngine
        print("✓ Playwright automation module imported")
        
        # Test google cloud automation
        from google_cloud_automation import GoogleCloudAutomation
        print("✓ Google Cloud automation module imported")
        
        # Test oauth credentials
        from oauth_credentials import OAuthCredentialsManager
        print("✓ OAuth credentials module imported")
        
        # Test main GUI
        from main import GmailOAuthGUI
        print("✓ Main GUI module imported")
        
        return True
    except ImportError as e:
        print(f"✗ Core module import error: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration system"""
    print("\n--- Testing Configuration System ---")
    try:
        from config import get_config, ConfigManager
        
        config = get_config()
        print(f"✓ Configuration loaded: {type(config).__name__}")
        
        # Test config manager
        config_manager = ConfigManager()
        print(f"✓ Config manager created")
        
        # Test directory creation
        config_manager.ensure_directories()
        print("✓ Directories ensured")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling system"""
    print("\n--- Testing Error Handling ---")
    try:
        from error_handler import ErrorHandler, ErrorType
        
        # Test error handler initialization
        handler = ErrorHandler()
        print(f"✓ Error handler created")
        
        # Test logging
        handler.logger.info("Test log message")
        print("✓ Logging works")
        
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def test_directory_structure():
    """Test directory structure creation"""
    print("\n--- Testing Directory Structure ---")
    try:
        from config import get_config
        
        config = get_config()
        
        # Check if directories exist or can be created
        directories = [
            config.paths.output_dir,
            config.paths.reports_dir,
            config.paths.screenshots_dir,
            config.paths.downloads_dir,
            config.paths.logs_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            if Path(directory).exists():
                print(f"✓ Directory exists: {directory}")
            else:
                print(f"✗ Directory missing: {directory}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Directory structure test failed: {e}")
        traceback.print_exc()
        return False

def test_playwright_availability():
    """Test if Playwright is available"""
    print("\n--- Testing Playwright Availability ---")
    try:
        from playwright.async_api import async_playwright
        print("✓ Playwright imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Playwright not available: {e}")
        print("  Please install with: pip install playwright")
        print("  Then run: playwright install chromium")
        return False

def main():
    """Run all tests"""
    print("Gmail OAuth Playwright Implementation - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Core Modules", test_core_modules),
        ("Configuration", test_configuration),
        ("Error Handling", test_error_handling),
        ("Directory Structure", test_directory_structure),
        ("Playwright Availability", test_playwright_availability),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation is ready.")
        print("\nTo run the application:")
        print("  python main.py")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)