#!/usr/bin/env python3
# Simple smoke test to verify Playwright launches Google Chrome via channel

import asyncio
import os

from playwright_automation import PlaywrightAutomationEngine


async def main():
    # Ensure we use Chrome stable if available
    os.environ["BROWSER_CHANNEL"] = os.environ.get("BROWSER_CHANNEL", "chrome")

    engine = PlaywrightAutomationEngine()
    ok = await engine.initialize_browser()
    if not ok:
        print("LAUNCH_OK=False")
        return

    # Print user agent to confirm browser
    ua = await engine.page.evaluate("navigator.userAgent")
    print("LAUNCH_OK=True")
    print("UserAgent:", ua)

    await engine.cleanup()


if __name__ == "__main__":
    asyncio.run(main())