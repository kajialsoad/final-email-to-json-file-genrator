#!/usr/bin/env python3
"""
Local synthetic test for Terms of Service handler
Validates checkbox detection and robust clicking of the Agree button
"""

import asyncio
from pathlib import Path
from google_cloud_automation import GoogleCloudAutomation

async def test_local_popup():
    automation = GoogleCloudAutomation()
    # Use visible browser to observe behavior; set headless to True if needed
    automation.config.browser.headless = False

    try:
        await automation.initialize_browser()
        local_uri = Path("tests/local_popup.html").resolve().as_uri()
        await automation.safe_navigate_with_retry(local_uri, wait_until="domcontentloaded")

        # Small delay
        await automation.human_delay(1, 2)
        await automation.take_screenshot("local_popup_before")

        # Run the updated Terms of Service handler
        ok = await automation._handle_terms_of_service()
        await automation.human_delay(1, 2)
        await automation.take_screenshot("local_popup_after")

        clicked = await automation.page.evaluate("window.__clickedAgreement === true")
        print(f"Handler returned: {ok}; Agree clicked: {clicked}")

        # Keep open briefly for manual inspection
        await asyncio.sleep(5)
    finally:
        if automation.browser:
            await automation.browser.close()

if __name__ == "__main__":
    asyncio.run(test_local_popup())