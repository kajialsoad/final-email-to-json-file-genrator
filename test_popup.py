#!/usr/bin/env python3
"""
Manual test script for popup detection and handling
"""

import asyncio
import logging
from google_cloud_automation import GoogleCloudAutomation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_popup_handling():
    """Test popup detection and handling manually"""
    
    # Initialize automation
    automation = GoogleCloudAutomation()
    
    # Set email and password manually
    automation.config.email = 'xaxunimdf56aki34XZ@taxtfre.us'
    automation.config.password = 'Aa123456789'
    automation.config.browser.headless = False
    
    try:
        # Initialize browser
        await automation.initialize_browser()
        
        # Login to Google Cloud Console
        await automation.login_to_google_cloud('xaxunimdf56aki34XZ@taxtfre.us', 'Aa123456789')
        
        # Navigate to project selector
        await automation.safe_navigate_with_retry("https://console.cloud.google.com/projectselector2/home")
        
        # Wait a bit for page to load
        await automation.human_delay(3, 5)
        
        # Take screenshot
        await automation.take_screenshot("manual_test_project_selector")
        
        # Test popup detection
        popup_indicators = [
            'text="Country"',
            'select[name="country"]',
            'text="Terms of Service"',
            'text="Google Cloud Platform Terms of Service"',
            'input[type="checkbox"]',
            'text="I agree to the"',
            'text="Agree and continue"',
            'button:has-text("Agree and continue")'
        ]
        
        has_popup = False
        found_indicators = []
        
        for indicator in popup_indicators:
            count = await automation.page.locator(indicator).count()
            if count > 0:
                has_popup = True
                found_indicators.append(f"{indicator} (count: {count})")
                logging.info(f"🔍 Found popup indicator: {indicator} (count: {count})")
        
        if has_popup:
            logging.info(f"🎯 AI Popup detected! Found indicators: {found_indicators}")
            
            # Handle country selection
            logging.info("🌍 Handling country selection...")
            await automation._handle_country_selection()
            await automation.human_delay(2, 3)
            
            # Handle terms of service
            logging.info("📋 Handling terms of service...")
            await automation._handle_terms_of_service()
            await automation.human_delay(2, 3)
            
            # Take screenshot after handling
            await automation.take_screenshot("manual_test_popup_handled")
            logging.info("✅ Popup handling completed")
        else:
            logging.info("❌ No popup detected")
            
            # Let's check what's actually on the page
            page_content = await automation.page.content()
            logging.info(f"Page title: {await automation.page.title()}")
            logging.info(f"Page URL: {automation.page.url}")
            
            # Check for any visible text containing "Country" or "Terms"
            country_elements = await automation.page.locator('text="Country"').all()
            terms_elements = await automation.page.locator('text="Terms"').all()
            
            logging.info(f"Country elements found: {len(country_elements)}")
            logging.info(f"Terms elements found: {len(terms_elements)}")
        
        # Keep browser open for manual inspection
        logging.info("🔍 Browser will stay open for manual inspection. Press Ctrl+C to close.")
        await asyncio.sleep(300)  # Wait 5 minutes
        
    except Exception as e:
        logging.error(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if automation.browser:
            await automation.browser.close()

if __name__ == "__main__":
    asyncio.run(test_popup_handling())