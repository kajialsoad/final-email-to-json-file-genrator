#!/usr/bin/env python3
# Simple Selenium smoke test to verify Chrome + ChromeDriver automation

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def main():
    opts = Options()
    # Basic stability/anti-detection tweaks
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    # Optional: reduce Chrome automation flags visibility
    opts.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    opts.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    try:
        driver.get("https://www.google.com/chrome/")
        title = driver.title
        ua = driver.execute_script("return navigator.userAgent")
        print("SELENIUM_OK=True")
        print("Title:", title)
        print("UserAgent:", ua)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()