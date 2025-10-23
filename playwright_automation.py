#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Automation Engine
Core automation engine with stealth mode and anti-detection features
"""

import asyncio
import random
import string
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
import time
import logging
import traceback
import os
import re

# Optional imports with fallbacks
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError
from config import get_config
from error_handler import error_handler, ErrorType, retry_async, log_error

class PlaywrightAutomationEngine:
    """Core Playwright automation engine with advanced features"""
    
    def __init__(self):
        self.config = get_config()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.session_id = str(uuid.uuid4())[:8]
        self.user_data_dir: Optional[Path] = None
        
        # Create directories
        self.screenshots_dir = Path(self.config.paths.screenshots_dir)
        self.downloads_dir = Path(self.config.paths.downloads_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = error_handler.logger
        
    @retry_async(context="browser_initialization")
    async def initialize_browser(self) -> bool:
        """Initialize Playwright browser with enhanced anti-detection"""
        try:
            self.logger.info("🚀 Initializing browser with enhanced anti-detection...")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Get randomized configuration
            user_agent = self.config.browser.get_random_user_agent()
            viewport_width, viewport_height = self.config.browser.get_random_viewport()
            
            self.logger.info(f"🎭 Using randomized user agent: {user_agent[:50]}...")
            self.logger.info(f"📐 Using randomized viewport: {viewport_width}x{viewport_height}")
            
            # Enhanced Chrome browser arguments based on test driver configuration
            browser_config = self.config.get_browser_args()
            
            # Chrome-specific arguments from test driver with additional anti-detection
            chrome_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                f'--window-size={viewport_width},{viewport_height}',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-extensions-file-access-check',
                '--disable-extensions-http-throttling',
                '--disable-extensions-https-throttling',
                '--disable-features=VizDisplayCompositor',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-field-trial-config',
                '--disable-back-forward-cache',
                '--disable-component-cloud-policy',
                '--disable-client-side-phishing-detection',
                '--no-zygote',
                '--disable-gpu-sandbox',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-features=TranslateUI',
                '--enable-features=NetworkService,NetworkServiceInProcess',
                '--force-color-profile=srgb',
                '--metrics-recording-only',
                '--use-mock-keychain'
            ]
            
            # Update browser config with Chrome-specific arguments
            browser_config['args'] = chrome_args
            
            # Add Chrome-specific experimental options equivalent
            browser_config['ignore_default_args'] = ['--enable-automation']
            
            # Context options with enhanced stealth
            context_options = {
                'viewport': {'width': viewport_width, 'height': viewport_height},
                'user_agent': user_agent,
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
                'permissions': ['geolocation', 'notifications'],
                'color_scheme': 'light',
                'reduced_motion': 'no-preference',
                'forced_colors': 'none',
                'accept_downloads': True,
                'ignore_https_errors': self.config.browser.ignore_https_errors,
                'java_script_enabled': True,
                'bypass_csp': True,
                'screen': {
                    'width': viewport_width + random.randint(100, 300),
                    'height': viewport_height + random.randint(100, 300)
                },
                'device_scale_factor': self.config.browser.force_device_scale_factor + random.uniform(-0.1, 0.1),
                'has_touch': False,
                'is_mobile': False
            }
            
            # Downloads path is handled separately in browser launch options
            
            # Initialize browser based on context type
            if self.config.browser.use_persistent_context and self.user_data_dir:
                # Persistent context with user data
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    **browser_config,
                    **context_options
                )
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            else:
                # Standard ephemeral context (Playwright default)
                self.browser = await self.playwright.chromium.launch(**browser_config)
                self.context = await self.browser.new_context(**context_options)
                self.page = await self.context.new_page()
            
            # Apply stealth mode
            if self.config.browser.stealth_mode and HAS_STEALTH:
                await stealth_async(self.context)
            elif self.config.browser.stealth_mode and not HAS_STEALTH:
                self.logger.warning("Stealth mode requested but playwright-stealth not installed")
            
            # Configure page timeouts
            page_options = self.config.get_page_options()
            self.page.set_default_timeout(page_options['default_timeout'])
            self.page.set_default_navigation_timeout(page_options['default_navigation_timeout'])
            
            # Apply UI stability settings
            await self._apply_ui_stability_settings()
            
            # Add enhanced stealth measures
            await self._apply_enhanced_stealth_measures()
            
            self.logger.info("✅ Browser initialized successfully with enhanced anti-detection")
            return True
            
        except Exception as e:
            log_error(e, "browser_initialization")
            raise

    async def _apply_enhanced_stealth_measures(self):
        """Apply enhanced stealth measures to avoid detection"""
        try:
            # Generate randomized fingerprint values
            random_hardware_concurrency = random.choice([2, 4, 6, 8, 12, 16])
            random_device_memory = random.choice([2, 4, 8, 16, 32])
            random_max_touch_points = random.choice([0, 1, 5, 10])
            random_platform = random.choice(['Win32', 'MacIntel', 'Linux x86_64'])
            
            # Remove webdriver property and other automation indicators (Chrome-specific)
            await self.page.add_init_script(f"""
                // Remove webdriver property completely
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                }});
                
                // Remove automation-related properties
                delete navigator.__proto__.webdriver;
                
                // Mock chrome runtime to appear as real Chrome
                window.chrome = {{
                    runtime: {{
                        onConnect: null,
                        onMessage: null
                    }},
                    loadTimes: function() {{
                        return {{
                            requestTime: Date.now() / 1000,
                            startLoadTime: Date.now() / 1000,
                            commitLoadTime: Date.now() / 1000,
                            finishDocumentLoadTime: Date.now() / 1000,
                            finishLoadTime: Date.now() / 1000,
                            firstPaintTime: Date.now() / 1000,
                            firstPaintAfterLoadTime: 0,
                            navigationType: "Other"
                        }};
                    }},
                    csi: function() {{
                        return {{
                            startE: Date.now(),
                            onloadT: Date.now(),
                            pageT: Date.now(),
                            tran: 15
                        }};
                    }},
                    app: {{
                        isInstalled: false
                    }}
                }};
                
                // Remove automation extension traces
                if (window.navigator.chrome && window.navigator.chrome.runtime && window.navigator.chrome.runtime.onConnect) {{
                    delete window.navigator.chrome.runtime.onConnect;
                }}
                
                // Override automation detection methods
                Object.defineProperty(window, 'outerHeight', {{
                    get: () => window.innerHeight,
                }});
                Object.defineProperty(window, 'outerWidth', {{
                    get: () => window.innerWidth,
                }});
                
                // Randomize hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {{
                    get: () => {random_hardware_concurrency},
                }});
                
                // Randomize device memory
                Object.defineProperty(navigator, 'deviceMemory', {{
                    get: () => {random_device_memory},
                }});
                
                // Randomize max touch points
                Object.defineProperty(navigator, 'maxTouchPoints', {{
                    get: () => {random_max_touch_points},
                }});
                
                // Randomize platform
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{random_platform}',
                }});
                
                // Mock plugins with realistic data
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => [
                        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                        {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
                    ],
                }});
                
                // Mock languages with slight variation
                const languages = [
                    ['en-US', 'en'],
                    ['en-US', 'en', 'es'],
                    ['en-GB', 'en'],
                    ['en-US', 'en', 'fr']
                ];
                Object.defineProperty(navigator, 'languages', {{
                    get: () => languages[Math.floor(Math.random() * languages.length)],
                }});
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({{ state: Notification.permission }}) :
                        originalQuery(parameters)
                );
                
                // Mock connection with realistic values
                Object.defineProperty(navigator, 'connection', {{
                    get: () => ({{
                        effectiveType: ['slow-2g', '2g', '3g', '4g'][Math.floor(Math.random() * 4)],
                        rtt: 50 + Math.floor(Math.random() * 100),
                        downlink: 1 + Math.random() * 10,
                        saveData: Math.random() > 0.8
                    }}),
                }});
                
                // Mock battery with realistic values
                Object.defineProperty(navigator, 'getBattery', {{
                    get: () => () => Promise.resolve({{
                        charging: Math.random() > 0.5,
                        chargingTime: Math.random() > 0.5 ? 0 : Math.floor(Math.random() * 7200),
                        dischargingTime: Math.random() > 0.5 ? Infinity : Math.floor(Math.random() * 28800),
                        level: 0.2 + Math.random() * 0.8
                    }}),
                }});
                
                // Mock media devices
                Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {{
                    get: () => () => Promise.resolve([
                        {{ deviceId: 'default', kind: 'audioinput', label: 'Default - Microphone' }},
                        {{ deviceId: 'default', kind: 'audiooutput', label: 'Default - Speaker' }},
                        {{ deviceId: 'default', kind: 'videoinput', label: 'Default - Camera' }}
                    ]),
                }});
                
                // Randomize canvas fingerprint
                const getContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {{
                    if (type === '2d') {{
                        const context = getContext.call(this, type);
                        const originalFillText = context.fillText;
                        context.fillText = function(text, x, y, maxWidth) {{
                            // Add slight randomization to text rendering
                            const noise = Math.random() * 0.1;
                            return originalFillText.call(this, text, x + noise, y + noise, maxWidth);
                        }};
                        return context;
                    }}
                    return getContext.call(this, type);
                }};
                
                // Randomize WebGL fingerprint
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                    // Randomize specific WebGL parameters
                    if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                        const vendors = ['Intel Inc.', 'NVIDIA Corporation', 'AMD', 'Qualcomm'];
                        return vendors[Math.floor(Math.random() * vendors.length)];
                    }}
                    if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                        const renderers = [
                            'Intel Iris OpenGL Engine',
                            'NVIDIA GeForce GTX 1060',
                            'AMD Radeon Pro 560',
                            'Adreno (TM) 640'
                        ];
                        return renderers[Math.floor(Math.random() * renderers.length)];
                    }}
                    return getParameter.call(this, parameter);
                }};
                
                // Mock screen properties with slight randomization
                const screenWidth = screen.width + Math.floor(Math.random() * 20) - 10;
                const screenHeight = screen.height + Math.floor(Math.random() * 20) - 10;
                
                Object.defineProperty(screen, 'width', {{
                    get: () => screenWidth,
                }});
                Object.defineProperty(screen, 'height', {{
                    get: () => screenHeight,
                }});
                Object.defineProperty(screen, 'availWidth', {{
                    get: () => screenWidth - Math.floor(Math.random() * 10),
                }});
                Object.defineProperty(screen, 'availHeight', {{
                    get: () => screenHeight - Math.floor(Math.random() * 10),
                }});
                
                // Add noise to performance.now()
                const originalNow = performance.now;
                performance.now = function() {{
                    return originalNow.call(this) + Math.random() * 0.1;
                }};
                
                // Mock gamepad API
                Object.defineProperty(navigator, 'getGamepads', {{
                    get: () => () => [null, null, null, null],
                }});
            """)
            
            # Add realistic mouse movement patterns
            if self.config.browser.use_realistic_mouse_movements:
                await self.page.add_init_script("""
                    // Override mouse events to add slight randomization
                    const originalAddEventListener = EventTarget.prototype.addEventListener;
                    EventTarget.prototype.addEventListener = function(type, listener, options) {
                        if (type === 'mousemove') {
                            const wrappedListener = function(event) {
                                // Add slight delay to mouse movements
                                setTimeout(() => listener.call(this, event), Math.random() * 5);
                            };
                            return originalAddEventListener.call(this, type, wrappedListener, options);
                        }
                        return originalAddEventListener.call(this, type, listener, options);
                    };
                """)
            
            # Log fingerprint data for debugging
            fingerprint_data = {
                'user_agent': self.page.context.browser.version if hasattr(self.page.context, 'browser') else 'unknown',
                'viewport': f"{self.page.viewport_size['width']}x{self.page.viewport_size['height']}" if self.page.viewport_size else 'unknown',
                'platform': random_platform,
                'hardware_concurrency': random_hardware_concurrency,
                'device_memory': random_device_memory,
                'max_touch_points': random_max_touch_points,
                'webgl_vendor': 'randomized',
                'webgl_renderer': 'randomized'
            }
            
            from error_handler import error_handler
            error_handler.log_browser_fingerprint_status(fingerprint_data)
            
            self.logger.debug("✅ Enhanced stealth measures applied with comprehensive fingerprint randomization")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to apply some stealth measures: {str(e)}")
            # Log the error for automation detection debugging
            from error_handler import error_handler
            error_handler.log_automation_detection(
                error_str=f"Stealth measures failed: {str(e)}",
                context_str="method: _apply_enhanced_stealth_measures, error_type: stealth_failure",
                full_error=str(e)
            )

    async def human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Enhanced human-like delay with randomization"""
        if min_seconds is None:
            min_seconds = self.config.automation.human_delay_min
        if max_seconds is None:
            max_seconds = self.config.automation.human_delay_max
            
        # Add extra randomization if enabled
        if self.config.browser.randomize_timing:
            # Occasionally add longer pauses (5% chance)
            if random.random() < 0.05:
                min_seconds *= 2
                max_seconds *= 2
            # Sometimes add shorter pauses (10% chance)
            elif random.random() < 0.1:
                min_seconds *= 0.5
                max_seconds *= 0.5
        
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def enhanced_click(self, selector: str, timeout: int = None) -> bool:
        """Enhanced click with human-like behavior"""
        try:
            if timeout is None:
                timeout = self.config.automation.create_button_wait_timeout
                
            # Wait for element
            await self.page.wait_for_selector(selector, timeout=timeout)
            element = self.page.locator(selector)
            
            # Scroll into view if needed
            await element.scroll_into_view_if_needed()
            
            # Add pre-click delay
            if self.config.browser.randomize_timing:
                await asyncio.sleep(random.uniform(
                    self.config.automation.click_delay_min,
                    self.config.automation.click_delay_max
                ))
            
            # Hover before clicking (more human-like)
            if self.config.browser.use_realistic_mouse_movements:
                await element.hover()
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Click with force if needed
            await element.click(force=True)
            
            # Add post-click delay
            await self.human_delay(0.2, 0.8)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Enhanced click failed for {selector}: {str(e)}")
            return False

    async def enhanced_fill(self, selector: str, text: str, timeout: int = None) -> bool:
        """Enhanced form filling with human-like typing"""
        try:
            if timeout is None:
                timeout = self.config.automation.form_load_timeout
                
            # Wait for element
            await self.page.wait_for_selector(selector, timeout=timeout)
            element = self.page.locator(selector)
            
            # Scroll into view and focus
            await element.scroll_into_view_if_needed()
            await element.click()
            
            # Clear existing content
            await element.fill("")
            
            # Add form fill delay
            if self.config.browser.randomize_timing:
                await asyncio.sleep(random.uniform(
                    self.config.automation.form_fill_delay_min,
                    self.config.automation.form_fill_delay_max
                ))
            
            # Type with human-like speed if enabled
            if self.config.browser.vary_typing_speed:
                for char in text:
                    await element.type(char)
                    # Random delay between characters
                    await asyncio.sleep(random.uniform(0.05, 0.15))
            else:
                await element.fill(text)
            
            # Verify the text was entered
            entered_value = await element.input_value()
            return text in entered_value or entered_value == text
            
        except Exception as e:
            self.logger.debug(f"Enhanced fill failed for {selector}: {str(e)}")
            return False

    async def _apply_ui_stability_settings(self):
        """Apply UI stability settings to prevent jumping and displacement while preserving Google UI"""
        try:
            # Disable smooth scrolling and animations while preserving Google's native styling
            await self.page.add_init_script("""
                (function(){
                    // Safely set scroll behavior once DOM is ready
                    try {
                        const setScroll = () => {
                            const root = document.documentElement || document.getElementsByTagName('html')[0];
                            if (root && root.style) root.style.scrollBehavior = 'auto';
                        };
                        if (document.readyState === 'loading') {
                            document.addEventListener('DOMContentLoaded', setScroll, { once: true });
                        } else {
                            setScroll();
                        }
                    } catch (e) {}
                    
                    // Apply improved CSS that preserves Google's UI styling
                    try {
                        const style = document.createElement('style');
                        style.textContent = `
                            /* Disable only problematic animations, preserve layout */
                            * {
                                animation-duration: 0.01s !important;
                                animation-delay: 0s !important;
                                transition-duration: 0.01s !important;
                                transition-delay: 0s !important;
                                scroll-behavior: auto !important;
                            }
                            
                            /* Preserve Google's native padding and margins */
                            body {
                                overflow-x: hidden !important;
                                position: relative !important;
                            }
                            
                            /* Stabilize viewport without breaking Google's layout */
                            html {
                                overflow-x: hidden !important;
                                scroll-behavior: auto !important;
                            }
                            
                            /* Disable only transform animations that cause jumps */
                            * {
                                will-change: auto !important;
                            }
                            
                            /* Ensure Google's containers maintain their styling */
                            [role="main"], .main, #main, .content, .container {
                            }
                            
                            /* Fix specific Google UI elements */
                            .gb_g, .gb_h, .gb_i, .gb_j {
                            }
                            
                            /* Ensure forms maintain proper spacing */
                            form, input, button, .form-control {
                            }
                            
                            /* Prevent layout shifts while maintaining Google's design */
                            img, iframe, video {
                                max-width: 100% !important;
                                height: auto !important;
                            }
                        `;
                        try { (document.head || document.documentElement).appendChild(style); } catch (e) {}
                    } catch (e) {}
                    
                    // Preserve Google's native styling without touching null elements
                    setTimeout(() => {
                        try {
                            const googleElements = document.querySelectorAll('[class*="gb_"], [class*="google"], [id*="google"]');
                            googleElements.forEach(el => {
                                const computedStyle = window.getComputedStyle(el);
                                if (computedStyle.padding || computedStyle.margin) {
                                    // Don't override if Google has set these
                                }
                            });
                        } catch (e) {}
                    }, 1000);
                })();
            """)
            
            self.logger.info("✅ Improved UI stability settings applied - preserving Google UI")
            
        except Exception as e:
            self.logger.warning(f"Failed to apply UI stability settings: {e}")

    async def _apply_stealth_measures(self):
        """Apply additional stealth and anti-detection measures"""
        try:
            # Override webdriver property (most important)
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
            """)
            
            # Remove automation indicators
            await self.page.add_init_script("""
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
            """)
            
            # Override chrome runtime
            await self.page.add_init_script("""
                if (!window.chrome) {
                    window.chrome = {};
                }
                if (!window.chrome.runtime) {
                    window.chrome.runtime = {
                        onConnect: undefined,
                        onMessage: undefined,
                        connect: function() { return { postMessage: function() {}, onMessage: { addListener: function() {} } }; }
                    };
                }
            """)
            
            # Override plugins with realistic data
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        return {
                            0: { name: "Chrome PDF Plugin", filename: "internal-pdf-viewer" },
                            1: { name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai" },
                            2: { name: "Native Client", filename: "internal-nacl-plugin" },
                            length: 3
                        };
                    },
                    configurable: true
                });
            """)
            
            # Override languages
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                    configurable: true
                });
            """)
            
            # Override permissions
            await self.page.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # Override screen properties to match viewport
            await self.page.add_init_script(f"""
                Object.defineProperty(screen, 'width', {{
                    get: () => {self.config.browser.viewport_width}
                }});
                Object.defineProperty(screen, 'height', {{
                    get: () => {self.config.browser.viewport_height}
                }});
                Object.defineProperty(screen, 'availWidth', {{
                    get: () => {self.config.browser.viewport_width}
                }});
                Object.defineProperty(screen, 'availHeight', {{
                    get: () => {self.config.browser.viewport_height - 40}
                }});
            """)
            
            # Override automation detection methods
            await self.page.add_init_script("""
                // Override common automation detection
                window.outerHeight = window.innerHeight;
                window.outerWidth = window.innerWidth;
                
                // Mock realistic mouse movements
                let mouseX = Math.floor(Math.random() * window.innerWidth);
                let mouseY = Math.floor(Math.random() * window.innerHeight);
                
                Object.defineProperty(window, 'screenX', { get: () => 0 });
                Object.defineProperty(window, 'screenY', { get: () => 0 });
                
                // Override toString methods
                const originalToString = Function.prototype.toString;
                Function.prototype.toString = function() {
                    if (this === navigator.webdriver) {
                        return 'function webdriver() { [native code] }';
                    }
                    return originalToString.call(this);
                };
            """)
            
            self.logger.info("✅ Enhanced stealth measures applied")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to apply some stealth measures: {str(e)}")
    
    async def human_delay(self, min_delay: float = None, max_delay: float = None):
        """Add human-like delay"""
        min_delay = min_delay or self.config.automation.human_delay_min
        max_delay = max_delay or self.config.automation.human_delay_max
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def human_type(self, selector: str, text: str, clear_first: bool = True) -> bool:
        """Type text with human-like timing"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=10000)
            
            if clear_first:
                await element.click()
                await self.page.keyboard.press('Control+a')
                await asyncio.sleep(0.1)
            
            # Type with random delays
            for char in text:
                await element.type(char)
                delay = random.randint(
                    self.config.automation.typing_delay_min,
                    self.config.automation.typing_delay_max
                )
                await asyncio.sleep(delay / 1000)
            
            return True
            
        except Exception as e:
            log_error(e, f"human_type: {selector}")
            return False
    
    async def safe_click(self, selector: str, timeout: int = 10000) -> bool:
        """Safely click an element with multiple attempts"""
        selectors = [selector] if isinstance(selector, str) else selector
        
        for sel in selectors:
            try:
                # Wait for element
                element = await self.page.wait_for_selector(sel, timeout=timeout)
                
                # Scroll into view
                await element.scroll_into_view_if_needed()
                await self.human_delay(0.2, 0.5)
                
                # Click
                await element.click()
                await self.human_delay(0.5, 1.0)
                
                return True
                
            except Exception as e:
                self.logger.debug(f"Click attempt failed for {sel}: {str(e)}")
                continue
        
        return False
    
    async def wait_for_navigation(self, timeout: int = 15000) -> bool:
        """Wait for page navigation to complete with faster timeout"""
        try:
            # Use faster domcontentloaded first, then try networkidle with shorter timeout
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout // 2)
            try:
                await self.page.wait_for_load_state('networkidle', timeout=timeout // 2)
            except Exception:
                # If networkidle fails, continue anyway - page might be functional
                self.logger.debug("NetworkIdle timeout - continuing with domcontentloaded")
            
            await self.human_delay(0.5, 1)  # Reduced delay
            return True
        except Exception as e:
            log_error(e, "wait_for_navigation")
            return False
    
    async def take_screenshot(self, name: str = None, full_page: bool = False) -> str:
        """Take screenshot for debugging with optimized timeout"""
        try:
            # Check if page is initialized
            if self.page is None:
                self.logger.warning("⚠️ Cannot take screenshot - page is None (browser not initialized)")
                return ""
            
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"screenshot_{self.session_id}_{timestamp}"
            
            # Ensure .png extension
            if not name.endswith('.png'):
                name += '.png'
            
            screenshot_path = self.screenshots_dir / name
            
            # Use fast screenshot with timeout to prevent 60-second delays
            await asyncio.wait_for(
                self.page.screenshot(
                    path=str(screenshot_path),
                    full_page=full_page,
                    timeout=10000  # 10 seconds max for screenshot
                ),
                timeout=12  # Overall timeout of 12 seconds
            )
            
            self.logger.debug(f"📸 Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except asyncio.TimeoutError:
            self.logger.warning(f"⚠️ Screenshot timeout for {name} - skipping")
            return ""
        except Exception as e:
            log_error(e, "take_screenshot")
            return ""
    
    async def execute_with_retry(self, func, *args, max_retries: int = None, **kwargs) -> Any:
        """Execute function with retry logic"""
        max_retries = max_retries or self.config.automation.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = self.config.automation.retry_delay * (2 ** attempt)
                    self.logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    log_error(e, f"execute_with_retry: {func.__name__}")
        
        raise last_error
    
    async def check_for_challenges(self) -> Dict[str, bool]:
        """Enhanced challenge detection with improved CAPTCHA and reCAPTCHA detection"""
        challenges = {
            'captcha': False,
            'two_factor': False,
            'email_verification': False,
            'account_blocked': False,
            'unusual_activity': False,
            'recaptcha': False,
            'speedbump_verification': False
        }
        
        try:
            page_content = await self.page.content()
            page_text = page_content.lower()
            current_url = await self.get_current_url()
            
            # PRIORITY 1: Enhanced CAPTCHA/reCAPTCHA Detection (check first as it's most common)
            await self._detect_captcha_challenges(challenges, page_text, current_url)
            
            # If CAPTCHA is detected, return immediately to handle it
            if challenges['captcha'] or challenges['recaptcha']:
                return challenges
            
            # PRIORITY 2: Check for 2FA (after CAPTCHA to avoid conflicts)
            await self._detect_two_factor_challenges(challenges, page_text, current_url)
            
            # If two-factor is detected, return immediately to avoid false positives
            if challenges['two_factor']:
                return challenges
            
            # PRIORITY 3: Check for email verification
            await self._detect_email_verification_challenges(challenges, page_text)
            
            # PRIORITY 4: Check for blocked account
            await self._detect_account_blocked_challenges(challenges, page_text)
            
            # PRIORITY 5: Check for unusual activity
            await self._detect_unusual_activity_challenges(challenges, page_text)
            
            # PRIORITY 6: Check for speedbump verification (Google's "আমি বুঝি" popup)
            await self._detect_speedbump_verification(challenges, page_text, current_url)
            
        except Exception as e:
            log_error(e, "check_for_challenges")
        
        return challenges
    
    async def _detect_captcha_challenges(self, challenges: Dict[str, bool], page_text: str, current_url: str):
        """Enhanced CAPTCHA and reCAPTCHA detection with strict validation"""
        try:
            # Normal password page URLs that should NOT be considered CAPTCHA
            normal_password_urls = [
                'accounts.google.com/v3/signin/identifier',
                'accounts.google.com/signin/identifier',
                'accounts.google.com/v3/signin/password',
                'accounts.google.com/signin/password',
                'accounts.google.com/signin/v2/identifier',
                'accounts.google.com/signin/v2/password',
                'accounts.google.com/v3/signin/challenge/pwd',  # Normal password challenge page
                'accounts.google.com/signin/challenge/pwd'      # Normal password challenge page
            ]
            
            # Check if this is a normal password page
            is_normal_password_page = any(url_pattern in current_url for url_pattern in normal_password_urls)
            
            # Text-based CAPTCHA indicators (more specific)
            captcha_text_indicators = [
                'i\'m not a robot', 'im not a robot',
                'verify you\'re human', 'verify youre human',
                'confirm you\'re not a robot', 'confirm youre not a robot',
                'prove you\'re human', 'prove youre human'
            ]
            
            # Strong CAPTCHA text indicators (these alone can trigger detection)
            strong_captcha_indicators = [
                'recaptcha', 'captcha'
            ]
            
            # URL-based CAPTCHA indicators (specific challenge URLs only)
            captcha_url_patterns = [
                'accounts.google.com/v3/signin/challenge/recaptcha',
                'accounts.google.com/signin/challenge/recaptcha',
                'accounts.google.com/v3/signin/challenge/captcha',
                'accounts.google.com/signin/challenge/captcha'
            ]
            
            # Check different types of indicators
            text_captcha_detected = any(indicator in page_text.lower() for indicator in captcha_text_indicators)
            strong_text_detected = any(indicator in page_text.lower() for indicator in strong_captcha_indicators)
            url_captcha_detected = any(pattern in current_url for pattern in captcha_url_patterns)
            
            # Element-based detection for reCAPTCHA
            element_captcha_detected = await self._detect_captcha_elements()
            
            # Detailed logging for debugging
            self.logger.info(f"🔍 CAPTCHA Detection Analysis:")
            self.logger.info(f"   Current URL: {current_url}")
            self.logger.info(f"   Is normal password page: {is_normal_password_page}")
            self.logger.info(f"   Text indicators found: {text_captcha_detected}")
            self.logger.info(f"   Strong text indicators found: {strong_text_detected}")
            self.logger.info(f"   URL patterns found: {url_captcha_detected}")
            self.logger.info(f"   Element detection: {element_captcha_detected}")
            
            # STRICT DETECTION LOGIC:
            # 1. If it's a normal password page, don't detect CAPTCHA unless very strong evidence
            # 2. Require multiple indicators OR strong single indicator
            if is_normal_password_page:
                # For normal password pages, require very strong evidence
                captcha_detected = (element_captcha_detected and (strong_text_detected or url_captcha_detected))
                self.logger.info(f"   Normal password page - strict check: {captcha_detected}")
            else:
                # For other pages, require at least 2 indicators OR 1 strong indicator
                indicator_count = sum([text_captcha_detected, url_captcha_detected, element_captcha_detected])
                captcha_detected = (indicator_count >= 2) or strong_text_detected or url_captcha_detected
                self.logger.info(f"   Other page - indicator count: {indicator_count}, detected: {captcha_detected}")
            
            # Set challenge flags
            challenges['captcha'] = captcha_detected
            challenges['recaptcha'] = captcha_detected and (element_captcha_detected or 'recaptcha' in page_text.lower())
            
            if challenges['captcha'] or challenges['recaptcha']:
                self.logger.warning(f"🤖 CAPTCHA/reCAPTCHA CONFIRMED - Text: {text_captcha_detected}, Strong: {strong_text_detected}, URL: {url_captcha_detected}, Element: {element_captcha_detected}")
            else:
                self.logger.info(f"✅ No CAPTCHA detected - continuing with normal flow")
                
        except Exception as e:
            log_error(e, "_detect_captcha_challenges")
    
    async def _detect_captcha_elements(self) -> bool:
        """Detect CAPTCHA elements on the page with enhanced selectors"""
        try:
            # Enhanced reCAPTCHA element selectors
            recaptcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[title*="recaptcha"]',
                'iframe[title*="reCAPTCHA"]',
                'iframe[name*="recaptcha"]',
                '.g-recaptcha',
                '#g-recaptcha',
                '[data-sitekey]',
                'div[class*="recaptcha"]',
                'div[id*="recaptcha"]',
                'div[data-recaptcha]',
                'script[src*="recaptcha"]',
                'div.recaptcha-checkbox-border',
                'div.recaptcha-checkbox-checkmark',
                'div[role="presentation"][style*="recaptcha"]'
            ]
            
            # Enhanced "I'm not a robot" checkbox selectors
            robot_checkbox_selectors = [
                'input[type="checkbox"][aria-label*="not a robot"]',
                'input[type="checkbox"][aria-label*="not robot"]',
                'input[type="checkbox"][title*="not a robot"]',
                'input[type="checkbox"][title*="not robot"]',
                'span:has-text("I\'m not a robot")',
                'span:has-text("Im not a robot")',
                'span:has-text("I am not a robot")',
                'label:has-text("I\'m not a robot")',
                'label:has-text("Im not a robot")',
                'label:has-text("I am not a robot")',
                'div:has-text("I\'m not a robot")',
                'div:has-text("Im not a robot")',
                '.recaptcha-checkbox',
                '#recaptcha-checkbox',
                '.recaptcha-checkbox-border',
                '.recaptcha-checkbox-checkmark',
                'div[role="checkbox"][aria-label*="not a robot"]',
                'div[role="checkbox"][aria-label*="not robot"]'
            ]
            
            # Enhanced CAPTCHA image selectors
            captcha_image_selectors = [
                'img[src*="captcha"]',
                'img[alt*="captcha"]',
                'img[alt*="CAPTCHA"]',
                'img[title*="captcha"]',
                'img[title*="CAPTCHA"]',
                'canvas[id*="captcha"]',
                'canvas[class*="captcha"]',
                'div[class*="captcha-image"]',
                'div[id*="captcha-image"]',
                'div[class*="captcha-container"]',
                'div[id*="captcha-container"]',
                'img[src*="challenge"]',
                'img[alt*="challenge"]',
                'div[class*="challenge-image"]'
            ]
            
            # Google-specific verification selectors (ONLY for actual CAPTCHA challenges)
            google_verification_selectors = [
                # REMOVED: 'div[data-identifier="TL"]' - Too broad, can appear on normal pages
                # REMOVED: 'div[jsname="B34EJ"]' - Too broad, can appear on normal pages
                # REMOVED: 'div[jsname="Njthtb"]' - This is a normal password form element, not CAPTCHA
                'div[data-challenge-ui="challenge"]',
                'div[aria-label*="captcha"]',           # More specific to CAPTCHA
                'div[aria-label*="recaptcha"]',         # More specific to reCAPTCHA
                'form[data-challenge-ui]',
                'div[class*="captcha-challenge"]',      # More specific to CAPTCHA challenges
                'div[id*="captcha-challenge"]'          # More specific to CAPTCHA challenges
            ]
            
            # Cloudflare and other CAPTCHA providers
            other_captcha_selectors = [
                'div[class*="cf-challenge"]',     # Cloudflare
                'div[id*="cf-challenge"]',        # Cloudflare
                'div[class*="hcaptcha"]',         # hCaptcha
                'div[id*="hcaptcha"]',            # hCaptcha
                'iframe[src*="hcaptcha"]',        # hCaptcha iframe
                'div[class*="turnstile"]',        # Cloudflare Turnstile
                'div[id*="turnstile"]',           # Cloudflare Turnstile
                'div[class*="captcha-widget"]',   # Generic CAPTCHA widget
                'div[id*="captcha-widget"]'       # Generic CAPTCHA widget
            ]
            
            # Check for any reCAPTCHA elements (must be visible)
            for selector in recaptcha_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    # Check if element is actually visible
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 reCAPTCHA element detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 reCAPTCHA element found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 reCAPTCHA element visibility check failed: {selector}")
            
            # Check for robot checkbox elements (must be visible)
            for selector in robot_checkbox_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 'I'm not a robot' checkbox detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 Robot checkbox found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 Robot checkbox visibility check failed: {selector}")
            
            # Check for CAPTCHA image elements (must be visible)
            for selector in captcha_image_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 CAPTCHA image detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 CAPTCHA image found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 CAPTCHA image visibility check failed: {selector}")
            
            # Check for Google-specific verification elements (must be visible)
            for selector in google_verification_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 Google verification challenge detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 Google verification found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 Google verification visibility check failed: {selector}")
            
            # Check for other CAPTCHA providers (must be visible)
            for selector in other_captcha_selectors:
                locator = self.page.locator(selector)
                if await locator.count() > 0:
                    try:
                        if await locator.first.is_visible(timeout=1000):
                            self.logger.info(f"🔍 Third-party CAPTCHA detected (visible): {selector}")
                            return True
                        else:
                            self.logger.debug(f"🔍 Third-party CAPTCHA found but not visible: {selector}")
                    except:
                        self.logger.debug(f"🔍 Third-party CAPTCHA visibility check failed: {selector}")
            
            self.logger.debug(f"🔍 No visible CAPTCHA elements found")
            return False
            
        except Exception as e:
            log_error(e, "_detect_captcha_elements")
            return False
    
    async def _detect_two_factor_challenges(self, challenges: Dict[str, bool], page_text: str, current_url: str):
        """Detect two-factor authentication challenges"""
        try:
            two_factor_indicators = [
                '2-step verification', 'two-step verification',
                'check your phone', 'enter the code', 'verification code',
                'authenticator app', 'phone number',
                'google sent a notification', 'sent a notification',
                'verify with your phone', 'verify using your phone'
            ]
            
            two_factor_url_patterns = [
                'accounts.google.com/v3/signin/challenge/totp',
                'accounts.google.com/signin/challenge/totp',
                'accounts.google.com/v3/signin/challenge/ipp',
                'accounts.google.com/signin/challenge/ipp'
            ]
            
            text_match = any(indicator in page_text for indicator in two_factor_indicators)
            url_match = any(pattern in current_url for pattern in two_factor_url_patterns)
            
            challenges['two_factor'] = text_match or url_match
            
            if challenges['two_factor']:
                self.logger.warning(f"📱 Two-factor authentication detected - Text: {text_match}, URL: {url_match}")
                
        except Exception as e:
            log_error(e, "_detect_two_factor_challenges")
    
    async def _detect_email_verification_challenges(self, challenges: Dict[str, bool], page_text: str):
        """Detect email verification challenges"""
        try:
            email_indicators = [
                'verify your email', 'check your email',
                'confirmation email', 'email verification',
                'sent you an email', 'check your inbox'
            ]
            
            challenges['email_verification'] = any(indicator in page_text for indicator in email_indicators)
            
            if challenges['email_verification']:
                self.logger.warning("📧 Email verification detected")
                
        except Exception as e:
            log_error(e, "_detect_email_verification_challenges")
    
    async def _detect_account_blocked_challenges(self, challenges: Dict[str, bool], page_text: str):
        """Detect account blocked challenges"""
        try:
            blocked_indicators = [
                'account suspended', 'account disabled',
                'account locked', 'access denied',
                'temporarily blocked', 'account restricted'
            ]
            
            challenges['account_blocked'] = any(indicator in page_text for indicator in blocked_indicators)
            
            if challenges['account_blocked']:
                self.logger.error("🚫 Account blocked/suspended detected")
                
        except Exception as e:
            log_error(e, "_detect_account_blocked_challenges")
    
    async def _detect_unusual_activity_challenges(self, challenges: Dict[str, bool], page_text: str):
        """Detect unusual activity challenges"""
        try:
            # Get current URL to check for successful login redirects
            current_url = await self.get_current_url()
            
            # URLs that indicate successful login (NOT unusual activity)
            successful_login_urls = [
                'myaccount.google.com',
                'console.cloud.google.com',
                'accounts.google.com/ManageAccount',
                'accounts.google.com/b/0/ManageAccount'
            ]
            
            # Check if we're on a successful login page
            is_successful_login = any(url_pattern in current_url for url_pattern in successful_login_urls)
            
            if is_successful_login:
                # This is a successful login redirect, not unusual activity
                challenges['unusual_activity'] = False
                self.logger.info(f"✅ Successful login detected - URL: {current_url}")
                return
            
            # Only check for unusual activity text if we're not on a successful login page
            activity_indicators = [
                'unusual activity', 'suspicious activity',
                'security alert', 'unusual sign-in activity'
            ]
            
            challenges['unusual_activity'] = any(indicator in page_text for indicator in activity_indicators)
            
            if challenges['unusual_activity']:
                self.logger.warning("⚠️ Unusual activity detected")
                
        except Exception as e:
            log_error(e, "_detect_unusual_activity_challenges")

    async def _detect_speedbump_verification(self, challenges: Dict[str, bool], page_text: str, current_url: str):
        """Detect Google speedbump verification popup (গুরুত্বপূর্ণ তথ্য popup with আমি বুঝি button)"""
        try:
            # Check for speedbump URL patterns
            speedbump_url_patterns = [
                'accounts.google.com/speedbump',
                'accounts.google.com/v3/signin/speedbump',
                'accounts.google.com/signin/speedbump',
                'gaplustos'  # Common in speedbump URLs
            ]
            
            # Check for Bengali text indicators
            bengali_indicators = [
                'আমি বুঝি',  # "I understand" in Bengali
                'গুরুত্বপূর্ণ তথ্য',  # "Important information" in Bengali
                'আপনার অ্যাকাউন্ট',  # "Your account" in Bengali
                'নিরাপত্তा',  # "Security" in Bengali
                'যাচাইকরণ'  # "Verification" in Bengali
            ]
            
            # Check for English text indicators (fallback)
            english_indicators = [
                'important information',
                'account security',
                'verification required',
                'continue to your account',
                'i understand',
                'understand and continue'
            ]
            
            # URL-based detection
            url_match = any(pattern in current_url for pattern in speedbump_url_patterns)
            
            # Text-based detection (Bengali first, then English)
            bengali_text_match = any(indicator in page_text for indicator in bengali_indicators)
            english_text_match = any(indicator in page_text for indicator in english_indicators)
            
            # Combined detection
            challenges['speedbump_verification'] = url_match or bengali_text_match or english_text_match
            
            if challenges['speedbump_verification']:
                self.logger.warning(f"🚨 Speedbump verification detected - URL: {url_match}, Bengali: {bengali_text_match}, English: {english_text_match}")
                self.logger.info(f"   Current URL: {current_url}")
                
        except Exception as e:
            log_error(e, "_detect_speedbump_verification")
    
    async def handle_speedbump_verification(self) -> bool:
        """Handle speedbump verification by clicking 'আমি বুঝি' (I understand) button"""
        try:
            self.logger.info("🔄 Attempting to handle speedbump verification...")
            
            # Button selectors for "আমি বুঝি" / "I understand" button
            understand_button_selectors = [
                # Bengali text selectors
                'button:has-text("আমি বুঝি")',
                'input[value="আমি বুঝি"]',
                'a:has-text("আমি বুঝি")',
                
                # English text selectors (fallback)
                'button:has-text("I understand")',
                'button:has-text("Understand")',
                'button:has-text("Continue")',
                'input[value="I understand"]',
                'input[value="Continue"]',
                
                # Generic selectors based on common patterns
                'button[type="submit"]',
                'input[type="submit"]',
                'button[data-action="continue"]',
                'button[data-action="understand"]',
                
                # Google-specific selectors
                'div[role="button"]:has-text("আমি বুঝি")',
                'div[role="button"]:has-text("I understand")',
                'span:has-text("আমি বুঝি")',
                'span:has-text("I understand")'
            ]
            
            # Try to click the understand button
            for selector in understand_button_selectors:
                try:
                    locator = self.page.locator(selector)
                    if await locator.count() > 0:
                        # Check if button is visible
                        if await locator.first.is_visible(timeout=2000):
                            self.logger.info(f"✅ Found understand button: {selector}")
                            await locator.first.click()
                            await self.human_delay(1, 2)
                            
                            # Wait for navigation or page change
                            try:
                                await self.page.wait_for_load_state("networkidle", timeout=10000)
                            except:
                                pass
                            
                            self.logger.info("✅ Successfully clicked understand button")
                            return True
                        else:
                            self.logger.debug(f"Button found but not visible: {selector}")
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
            self.logger.warning("⚠️ Could not find or click understand button")
            return False
            
        except Exception as e:
            log_error(e, "handle_speedbump_verification")
            return False
    
    async def handle_download(self, download_trigger_func, expected_filename: str = None) -> Optional[str]:
        """Handle file download with proper waiting"""
        try:
            # Start waiting for download
            async with self.page.expect_download() as download_info:
                await download_trigger_func()
            
            download = await download_info.value
            
            # Generate filename if not provided
            if not expected_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                suggested_filename = download.suggested_filename
                expected_filename = f"{timestamp}_{suggested_filename}"
            
            # Save download
            download_path = self.downloads_dir / expected_filename
            await download.save_as(str(download_path))
            
            self.logger.info(f"📥 File downloaded: {download_path}")
            return str(download_path)
            
        except Exception as e:
            log_error(e, "handle_download")
            return None
    
    async def wait_for_loading_complete(self, timeout: int = None) -> bool:
        """Enhanced loading detection with multiple strategies"""
        if timeout is None:
            timeout = self.config.automation.loading_detection_timeout
            
        self.logger.info("🔄 Waiting for page loading to complete...")
        
        try:
            # Strategy 1: Wait for network idle
            await self.page.wait_for_load_state('networkidle', timeout=timeout // 3)
            self.logger.debug("✅ Network idle detected")
            
            # Strategy 2: Wait for DOM content loaded
            await self.page.wait_for_load_state('domcontentloaded', timeout=timeout // 3)
            self.logger.debug("✅ DOM content loaded")
            
            # Strategy 3: Check for common loading indicators
            loading_selectors = [
                '[data-testid="loading"]',
                '.loading',
                '.spinner',
                '[aria-label*="Loading"]',
                '[aria-label*="loading"]',
                '.progress-bar',
                '.loading-spinner',
                '.mat-progress-spinner',
                '.mat-spinner',
                'mat-progress-spinner',
                'mat-spinner',
                '[role="progressbar"]',
                '.cfc-loading',
                '.p6n-loading',
                '.gb_g', # Google loading indicator
                '.VfPpkd-Bz112c-LgbsSe', # Material Design loading
            ]
            
            # Wait for loading indicators to disappear
            for selector in loading_selectors:
                try:
                    # Check if loading indicator exists
                    if await self.page.locator(selector).count() > 0:
                        self.logger.debug(f"⏳ Waiting for loading indicator to disappear: {selector}")
                        await self.page.wait_for_selector(selector, state='detached', timeout=timeout // 6)
                        self.logger.debug(f"✅ Loading indicator disappeared: {selector}")
                except Exception:
                    # Loading indicator might not exist or already gone
                    continue
            
            # Strategy 4: Wait for JavaScript execution to stabilize
            await self._wait_for_js_stability()
            
            # Strategy 5: Additional delay for UI stabilization
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            self.logger.info("✅ Page loading completed successfully")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Loading detection timeout or error: {str(e)}")
            # Even if loading detection fails, continue with a reasonable delay
            await asyncio.sleep(3.0)
            return False

    async def _wait_for_js_stability(self, max_attempts: int = 5) -> bool:
        """Wait for JavaScript execution to stabilize"""
        try:
            for attempt in range(max_attempts):
                # Check if page is still executing JavaScript
                is_stable = await self.page.evaluate("""
                    () => {
                        // Check for common indicators of ongoing JS execution
                        const hasActiveRequests = window.fetch && window.fetch.activeRequests > 0;
                        const hasActiveTimers = window.setTimeout && window.setTimeout.activeCount > 0;
                        const hasActiveAnimations = document.getAnimations && document.getAnimations().length > 0;
                        
                        // Check for React/Angular loading states
                        const hasReactLoading = window.React && document.querySelector('[data-reactroot]') && 
                                              document.querySelector('.loading, .spinner, [aria-busy="true"]');
                        const hasAngularLoading = window.angular && document.querySelector('[ng-app]') &&
                                                document.querySelector('.loading, .spinner, [aria-busy="true"]');
                        
                        return !hasActiveRequests && !hasActiveTimers && !hasActiveAnimations && 
                               !hasReactLoading && !hasAngularLoading;
                    }
                """)
                
                if is_stable:
                    self.logger.debug("✅ JavaScript execution stabilized")
                    return True
                
                await asyncio.sleep(0.5)
            
            self.logger.debug("⚠️ JavaScript stability check timed out")
            return False
            
        except Exception as e:
            self.logger.debug(f"⚠️ JavaScript stability check failed: {str(e)}")
            return False

    async def wait_for_project_creation_complete(self, timeout: int = None) -> bool:
        """Enhanced waiting for project creation with multiple verification strategies"""
        if timeout is None:
            timeout = self.config.automation.project_creation_timeout
            
        self.logger.info("🏗️ Waiting for project creation to complete...")
        start_time = time.time()
        
        try:
            # Strategy 1: Wait for loading indicators to disappear
            await self.wait_for_loading_complete(timeout // 4)
            
            # Strategy 2: Look for success indicators
            success_indicators = [
                # Project dashboard elements
                '[data-testid="project-dashboard"]',
                '[aria-label*="Project dashboard"]',
                '.project-dashboard',
                
                # Navigation elements that appear after project creation
                '[data-testid="navigation"]',
                '.console-nav',
                '.p6n-nav',
                
                # Project selector elements
                '[data-testid="project-selector"]',
                '.project-selector',
                '.cfc-project-selector',
                
                # APIs & Services page elements
                '[href*="/apis/dashboard"]',
                '[data-testid="apis-dashboard"]',
                'text=APIs & services',
                'text=API Library',
                
                # Billing or other setup pages
                'text=Billing',
                'text=Enable billing',
                
                # Generic success indicators
                '.success-message',
                '[data-testid="success"]',
                '[aria-label*="Success"]',
                
                # Google Cloud Console specific elements
                '.console-header',
                '.cfc-header',
                '.p6n-header'
            ]
            
            # Wait for any success indicator to appear
            success_detected = False
            for indicator in success_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=timeout // 8)
                    self.logger.info(f"✅ Success indicator found: {indicator}")
                    success_detected = True
                    break
                except Exception:
                    continue
            
            # Strategy 3: Check URL changes that indicate successful creation
            current_url = self.page.url
            if any(pattern in current_url.lower() for pattern in [
                '/dashboard', '/apis', '/billing', '/iam', '/compute', '/storage'
            ]):
                self.logger.info(f"✅ URL indicates successful project creation: {current_url}")
                success_detected = True
            
            # Strategy 4: Wait for page title to change
            try:
                await self.page.wait_for_function(
                    "document.title && document.title.length > 0 && !document.title.includes('Loading')",
                    timeout=timeout // 6
                )
                title = await self.page.title()
                if title and 'loading' not in title.lower():
                    self.logger.info(f"✅ Page title indicates completion: {title}")
                    success_detected = True
            except Exception:
                pass
            
            # Strategy 5: Final stability check
            if success_detected:
                await self._wait_for_js_stability()
                await asyncio.sleep(random.uniform(2.0, 4.0))  # Additional stabilization
                
                elapsed_time = time.time() - start_time
                self.logger.info(f"✅ Project creation completed successfully in {elapsed_time:.1f}s")
                return True
            
            # If no success indicators found, wait a bit more and check again
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 10:
                self.logger.info("⏳ No immediate success indicators, waiting longer...")
                await asyncio.sleep(min(10, remaining_time))
                return await self._verify_project_creation_success()
            
            self.logger.warning("⚠️ Project creation verification timed out")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error during project creation verification: {str(e)}")
            return False

    async def _verify_project_creation_success(self) -> bool:
        """Final verification that project creation was successful"""
        try:
            # Check if we're on a project-related page
            current_url = self.page.url
            
            # Look for project-specific elements
            project_elements = [
                '[data-testid*="project"]',
                '.project-info',
                '.project-header',
                'text=Project ID',
                'text=Project Number',
                '[aria-label*="project"]'
            ]
            
            for element in project_elements:
                if await self.page.locator(element).count() > 0:
                    self.logger.info(f"✅ Project element found: {element}")
                    return True
            
            # Check URL patterns
            if any(pattern in current_url.lower() for pattern in [
                'console.cloud.google.com',
                '/project',
                '/dashboard',
                '/apis'
            ]):
                self.logger.info("✅ URL indicates we're in a project context")
                return True
            
            # Check page title
            title = await self.page.title()
            if title and any(keyword in title.lower() for keyword in [
                'console', 'dashboard', 'project', 'google cloud'
            ]):
                self.logger.info(f"✅ Page title indicates project context: {title}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Project verification check failed: {str(e)}")
            return False

    async def wait_for_element_stable(self, selector: str, timeout: int = 30) -> bool:
        """Wait for an element to be stable (not moving or changing)"""
        try:
            # First wait for element to exist
            await self.page.wait_for_selector(selector, timeout=timeout)
            
            # Then wait for it to be stable
            element = self.page.locator(selector)
            
            # Check element position stability
            for _ in range(5):  # Check 5 times with delays
                try:
                    box1 = await element.bounding_box()
                    await asyncio.sleep(0.2)
                    box2 = await element.bounding_box()
                    
                    if box1 and box2:
                        # Check if position is stable
                        if (abs(box1['x'] - box2['x']) < 1 and 
                            abs(box1['y'] - box2['y']) < 1 and
                            abs(box1['width'] - box2['width']) < 1 and
                            abs(box1['height'] - box2['height']) < 1):
                            self.logger.debug(f"✅ Element stable: {selector}")
                            return True
                except Exception:
                    continue
            
            # If position checks fail, just ensure element is visible and enabled
            await element.wait_for(state='visible', timeout=5)
            if await element.is_enabled():
                return True
                
            return False
            
        except Exception as e:
            self.logger.debug(f"Element stability check failed for {selector}: {str(e)}")
            return False

    async def enhanced_create_button_click(self, button_text: str = "Create", timeout: int = None, context: str = "button") -> bool:
        """Enhanced create button detection and clicking with comprehensive fallback strategies"""
        if timeout is None:
            timeout = self.config.automation.create_button_wait_timeout
            
        self.logger.info(f"🔍 Looking for {button_text} button with enhanced detection...")
        
        # Strategy 1: Primary selectors with exact and partial text matching
        primary_selectors = [
            f'button:has-text("{button_text}")',
            f'button:has-text("{button_text.upper()}")',
            f'button:has-text("{button_text.lower()}")',
            f'button:visible:has-text("{button_text}")',
            f'[role="button"]:has-text("{button_text}")',
            f'button[aria-label*="{button_text}"]',
            f'button[aria-label*="{button_text.lower()}"]',
            f'input[type="submit"][value*="{button_text}"]',
            f'button[type="submit"]:has-text("{button_text}")',
        ]
        
        # Strategy 2: Material Design and framework-specific selectors
        material_selectors = [
            f'button.mat-raised-button:has-text("{button_text}")',
            f'button.mat-button:has-text("{button_text}")',
            f'button.mat-flat-button:has-text("{button_text}")',
            f'button.mat-stroked-button:has-text("{button_text}")',
            f'button.mdc-button:has-text("{button_text}")',
            f'.VfPpkd-LgbsSe:has-text("{button_text}")',  # Google Material Design
            f'.VfPpkd-Bz112c:has-text("{button_text}")',
        ]
        
        # Strategy 3: CSS class-based selectors
        class_selectors = [
            f'button[class*="{button_text.lower()}"]',
            f'button[class*="submit"]',
            f'button[class*="primary"]',
            f'button[class*="action"]',
            f'.{button_text.lower()}-button',
            f'.{button_text.lower()}-btn',
            f'.btn-{button_text.lower()}',
            f'.button-{button_text.lower()}',
        ]
        
        # Strategy 4: Data attribute selectors
        data_selectors = [
            f'button[data-testid*="{button_text.lower()}"]',
            f'button[data-action*="{button_text.lower()}"]',
            f'button[data-cy*="{button_text.lower()}"]',
            f'[data-testid*="{button_text.lower()}-button"]',
            f'[data-testid*="submit"]',
            f'[data-action="submit"]',
        ]
        
        # Combine all selector strategies
        all_selectors = primary_selectors + material_selectors + class_selectors + data_selectors
        
        # Strategy 5: Try each selector with stability checking
        for i, selector in enumerate(all_selectors):
            try:
                self.logger.debug(f"🔍 Trying selector {i+1}/{len(all_selectors)}: {selector}")
                
                # Wait for element to exist
                await self.page.wait_for_selector(selector, timeout=timeout // len(all_selectors))
                
                # Check if element is stable
                if await self.wait_for_element_stable(selector, timeout=5):
                    element = self.page.locator(selector)
                    
                    # Ensure element is visible and enabled
                    await element.wait_for(state='visible', timeout=3)
                    if await element.is_enabled():
                        # Scroll element into view
                        await element.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        
                        # Try clicking
                        await element.click()
                        self.logger.info(f"✅ {button_text} button clicked successfully with: {selector}")
                        return True
                        
            except Exception as e:
                self.logger.debug(f"Selector failed: {selector} - {str(e)}")
                continue
        
        # Strategy 6: Fuzzy text matching fallback
        self.logger.info(f"🔄 Trying fuzzy text matching for {button_text} button...")
        try:
            # Find all buttons and check their text content
            all_buttons = await self.page.locator('button, [role="button"], input[type="submit"]').all()
            
            for button in all_buttons:
                try:
                    # Get button text content
                    text_content = await button.text_content()
                    inner_text = await button.inner_text()
                    aria_label = await button.get_attribute('aria-label')
                    value = await button.get_attribute('value')
                    
                    # Check all text sources
                    texts_to_check = [text_content, inner_text, aria_label, value]
                    
                    for text in texts_to_check:
                        if text and button_text.lower() in text.lower():
                            if await button.is_visible() and await button.is_enabled():
                                await button.scroll_into_view_if_needed()
                                await asyncio.sleep(0.5)
                                await button.click()
                                self.logger.info(f"✅ {button_text} button clicked using fuzzy matching: '{text}'")
                                return True
                                
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Fuzzy matching failed: {str(e)}")
        
        # Strategy 7: Frame-aware search
        self.logger.info(f"🔄 Searching for {button_text} button in frames...")
        try:
            for frame in self.page.frames:
                try:
                    # Try primary selectors in each frame
                    for selector in primary_selectors[:5]:  # Use top 5 selectors
                        try:
                            element = frame.locator(selector)
                            if await element.count() > 0:
                                await element.first.scroll_into_view_if_needed()
                                await asyncio.sleep(0.5)
                                await element.first.click()
                                self.logger.info(f"✅ {button_text} button clicked in frame with: {selector}")
                                return True
                        except Exception:
                            continue
                except Exception:
                    continue
        except Exception as e:
            self.logger.debug(f"Frame search failed: {str(e)}")
        
        # Strategy 8: JavaScript-based fallback
        self.logger.info(f"🔄 Trying JavaScript-based {button_text} button detection...")
        try:
            button_found = await self.page.evaluate(f"""
                () => {{
                    const buttonText = '{button_text}';
                    
                    // Find all clickable elements
                    const clickableElements = document.querySelectorAll('button, [role="button"], input[type="submit"], a');
                    
                    for (const element of clickableElements) {{
                        const text = element.textContent || element.innerText || element.value || element.getAttribute('aria-label') || '';
                        
                        if (text.toLowerCase().includes(buttonText.toLowerCase())) {{
                            // Check if element is visible and not disabled
                            const rect = element.getBoundingClientRect();
                            const isVisible = rect.width > 0 && rect.height > 0 && 
                                            window.getComputedStyle(element).visibility !== 'hidden' &&
                                            window.getComputedStyle(element).display !== 'none';
                            
                            if (isVisible && !element.disabled) {{
                                element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                setTimeout(() => element.click(), 500);
                                return true;
                            }}
                        }}
                    }}
                    return false;
                }}
            """)
            
            if button_found:
                await asyncio.sleep(1.0)  # Wait for the click to process
                self.logger.info(f"✅ {button_text} button clicked using JavaScript fallback")
                return True
                
        except Exception as e:
            self.logger.debug(f"JavaScript fallback failed: {str(e)}")
        
        # Strategy 9: Force click on any submit-type element
        self.logger.info(f"🔄 Trying force click on submit elements...")
        try:
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:last-of-type',  # Often the primary action button
                '.primary-button',
                '.submit-button',
                '.action-button'
            ]
            
            for selector in submit_selectors:
                try:
                    element = self.page.locator(selector)
                    if await element.count() > 0:
                        await element.first.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await element.first.click()
                        self.logger.info(f"✅ Submit element clicked with: {selector}")
                        return True
                except Exception:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Force submit click failed: {str(e)}")
        
        self.logger.error(f"❌ Could not find or click {button_text} button after trying all strategies")
        return False

    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            # Remove the temporary persistent profile after run if requested
            try:
                if self.user_data_dir and getattr(self.config.security, 'clear_browser_data', True):
                    import shutil
                    shutil.rmtree(self.user_data_dir, ignore_errors=True)
            except Exception:
                pass
            
            self.logger.info("🧹 Browser cleanup completed")
            
        except Exception as e:
            log_error(e, "cleanup")
    
    def generate_project_name(self, email: str) -> str:
        """Generate a unique project name (4-30 characters)"""
        # Extract username from email
        username = email.split('@')[0]
        
        # Clean username (remove special characters)
        clean_username = ''.join(c for c in username if c.isalnum())
        
        # Generate random suffix (6 characters)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Calculate available space for username
        # Format: "gmail-oauth-{username}-{suffix}"
        # "gmail-oauth-" = 12 chars, "-" = 1 char, suffix = 6 chars
        # Total fixed chars = 19, so username can be max 11 chars (30 - 19 = 11)
        max_username_length = 11
        clean_username = clean_username[:max_username_length]
        
        # Create project name
        project_name = f"gmail-oauth-{clean_username}-{suffix}"
        
        # Final safety check - if still too long, use shorter format
        if len(project_name) > 30:
            # Fallback to just "gmail-oauth-{suffix}" (18 chars)
            project_name = f"gmail-oauth-{suffix}"
        
        # Ensure minimum length (4 chars)
        if len(project_name) < 4:
            project_name = f"gmail-{suffix}"
        
        return project_name.lower()
    
    async def get_current_url(self) -> str:
        """Get current page URL"""
        try:
            return self.page.url
        except Exception:
            return ""
    
    async def get_page_title(self) -> str:
        """Get current page title"""
        try:
            return await self.page.title()
        except Exception:
            return ""
    
    async def save_screenshot(self, page: Page, name: str) -> Optional[str]:
        """Save screenshot for debugging"""
        try:
            screenshot_path = self.screenshots_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {str(e)}")
            return None
    
    async def write_file_async(self, file_path: Path, content: str) -> bool:
        """Write file with async support if available"""
        try:
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            else:
                # Fallback to synchronous write
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {str(e)}")
            return False