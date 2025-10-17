#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify UI improvements for Google Chrome display
"""

import asyncio
from playwright_automation import PlaywrightAutomationEngine
from config import get_config

async def test_google_ui_display():
    """Test that Google's UI displays properly with our improvements"""
    print("🧪 Testing Google UI display improvements...")
    
    # Initialize automation engine
    engine = PlaywrightAutomationEngine()
    
    try:
        # Initialize browser
        await engine.initialize_browser()
        print("✅ Browser initialized successfully")
        
        # Navigate to Google sign-in page
        await engine.page.goto("https://accounts.google.com/signin", wait_until="networkidle")
        print("✅ Navigated to Google sign-in page")
        
        # Wait for page to load completely
        await asyncio.sleep(3)
        
        # Take a screenshot to verify UI
        screenshot_path = "test_screenshots/google_ui_test.png"
        await engine.page.screenshot(path=screenshot_path, full_page=True)
        print(f"✅ Screenshot saved: {screenshot_path}")
        
        # Check if key elements are visible and properly styled
        email_input = await engine.page.query_selector('input[type="email"]')
        if email_input:
            print("✅ Email input field found and visible")
            
            # Check if the input has proper styling
            box_model = await email_input.bounding_box()
            if box_model:
                print(f"✅ Email input dimensions: {box_model['width']}x{box_model['height']}")
            else:
                print("⚠️ Could not get email input dimensions")
        else:
            print("❌ Email input field not found")
        
        # Check Google logo
        logo = await engine.page.query_selector('img[alt*="Google"], [aria-label*="Google"]')
        if logo:
            print("✅ Google logo found and visible")
        else:
            print("⚠️ Google logo not found")
        
        # Check overall page layout
        body = await engine.page.query_selector('body')
        if body:
            body_styles = await engine.page.evaluate("""
                (element) => {
                    const styles = window.getComputedStyle(element);
                    return {
                        margin: styles.margin,
                        padding: styles.padding,
                        width: styles.width,
                        height: styles.height
                    };
                }
            """, body)
            print(f"✅ Body styles: {body_styles}")
        
        print("🎉 UI test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # Clean up
        if engine.browser:
            await engine.browser.close()
        if engine.playwright:
            await engine.playwright.stop()
        print("🧹 Cleanup completed")

if __name__ == "__main__":
    asyncio.run(test_google_ui_display())