"""
Automation Fallback Strategies Module

This module provides comprehensive fallback strategies when automation is detected
by Google Cloud Console or other Google services. It includes multiple approaches
to handle different types of automation detection scenarios.
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from playwright.async_api import Page, Browser, BrowserContext

from config import ConfigManager, get_config
from error_handler import retry_with_recovery, log_error


class DetectionType(Enum):
    """Types of automation detection"""
    CAPTCHA = "captcha"
    RECAPTCHA = "recaptcha"
    BOT_DETECTION = "bot_detection"
    RATE_LIMITING = "rate_limiting"
    SECURITY_CHECK = "security_check"
    UNUSUAL_ACTIVITY = "unusual_activity"
    ACCESS_DENIED = "access_denied"
    VERIFICATION_REQUIRED = "verification_required"


class FallbackStrategy(Enum):
    """Available fallback strategies"""
    BROWSER_RESTART = "browser_restart"
    USER_AGENT_ROTATION = "user_agent_rotation"
    DELAY_RANDOMIZATION = "delay_randomization"
    STEALTH_MODE = "stealth_mode"
    MANUAL_INTERVENTION = "manual_intervention"
    PROXY_ROTATION = "proxy_rotation"
    SESSION_RESET = "session_reset"
    BEHAVIORAL_MIMICKING = "behavioral_mimicking"


@dataclass
class FallbackResult:
    """Result of a fallback strategy execution"""
    success: bool
    strategy_used: FallbackStrategy
    detection_bypassed: bool
    error_message: Optional[str] = None
    retry_recommended: bool = False
    next_strategy: Optional[FallbackStrategy] = None


class AutomationFallbackHandler:
    """Handles fallback strategies when automation is detected"""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.detection_history: List[Dict[str, Any]] = []
        self.strategy_success_rates: Dict[FallbackStrategy, float] = {}
        self.current_browser: Optional[Browser] = None
        self.current_context: Optional[BrowserContext] = None
        self.current_page: Optional[Page] = None
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        
        # Strategy priority order (most effective first)
        self.strategy_priority = [
            FallbackStrategy.DELAY_RANDOMIZATION,
            FallbackStrategy.USER_AGENT_ROTATION,
            FallbackStrategy.BEHAVIORAL_MIMICKING,
            FallbackStrategy.SESSION_RESET,
            FallbackStrategy.STEALTH_MODE,
            FallbackStrategy.BROWSER_RESTART,
            FallbackStrategy.MANUAL_INTERVENTION
        ]
    
    async def handle_detection(
        self, 
        detection_type: DetectionType, 
        page: Page,
        context: BrowserContext,
        browser: Browser,
        max_attempts: int = 3
    ) -> FallbackResult:
        """
        Handle automation detection with appropriate fallback strategies
        
        Args:
            detection_type: Type of detection encountered
            page: Current page instance
            context: Current browser context
            browser: Current browser instance
            max_attempts: Maximum number of fallback attempts
            
        Returns:
            FallbackResult with outcome of fallback handling
        """
        self.current_page = page
        self.current_context = context
        self.current_browser = browser
        
        self.logger.warning(f"🤖 Automation detection encountered: {detection_type.value}")
        
        # Log detailed detection information
        from error_handler import error_handler
        page_url = await page.url() if page else "unknown"
        page_title = await page.title() if page else "unknown"
        user_agent = await page.evaluate('navigator.userAgent') if page else "unknown"
        
        error_handler.log_automation_detection(
            error_str=f"Automation detection triggered: {detection_type.value}",
            context_str=f"method: handle_detection, detection_type: {detection_type.value}, page_url: {page_url}, page_title: {page_title}, user_agent: {user_agent}, max_attempts: {max_attempts}",
            full_error=f"Automation detection triggered: {detection_type.value}"
        )
        
        # Record detection event
        detection_event = {
            "timestamp": time.time(),
            "detection_type": detection_type.value,
            "url": page_url,
            "page_title": page_title,
            "user_agent": user_agent,
            "strategies_attempted": []
        }
        
        # Get appropriate strategies for this detection type
        strategies = self._get_strategies_for_detection(detection_type)
        
        for attempt in range(max_attempts):
            self.logger.info(f"🔄 Fallback attempt {attempt + 1}/{max_attempts}")
            
            for strategy in strategies:
                self.logger.info(f"🛡️ Trying fallback strategy: {strategy.value}")
                
                try:
                    result = await self._execute_strategy(strategy, detection_type)
                    detection_event["strategies_attempted"].append({
                        "strategy": strategy.value,
                        "success": result.success,
                        "attempt": attempt + 1
                    })
                    
                    if result.success:
                        self.logger.info(f"✅ Fallback strategy successful: {strategy.value}")
                        
                        # Log successful strategy execution
                        error_handler.log_automation_detection(
                            error_str=f"Fallback strategy succeeded: {strategy.value}",
                            context_str=f"method: handle_detection, strategy: {strategy.value}, detection_type: {detection_type.value}, attempt: {attempt + 1}, detection_bypassed: {result.detection_bypassed}",
                            full_error=f"Fallback strategy succeeded: {strategy.value}"
                        )
                        
                        self.detection_history.append(detection_event)
                        self._update_strategy_success_rate(strategy, True)
                        return result
                    else:
                        self.logger.warning(f"❌ Fallback strategy failed: {strategy.value}")
                        
                        # Log failed strategy execution
                        error_handler.log_automation_detection(
                            error_str=f"Fallback strategy failed: {strategy.value}",
                            context_str=f"method: handle_detection, strategy: {strategy.value}, detection_type: {detection_type.value}, attempt: {attempt + 1}, error_message: {result.error_message}, retry_recommended: {result.retry_recommended}",
                            full_error=f"Fallback strategy failed: {strategy.value}"
                        )
                        
                        self._update_strategy_success_rate(strategy, False)
                        
                        if result.error_message:
                            self.logger.error(f"Error details: {result.error_message}")
                
                except Exception as e:
                    self.logger.error(f"❌ Exception in fallback strategy {strategy.value}: {str(e)}")
                    detection_event["strategies_attempted"].append({
                        "strategy": strategy.value,
                        "success": False,
                        "error": str(e),
                        "attempt": attempt + 1
                    })
            
            # Wait before next attempt
            if attempt < max_attempts - 1:
                wait_time = random.uniform(5, 15)
                self.logger.info(f"⏳ Waiting {wait_time:.1f}s before next fallback attempt...")
                await asyncio.sleep(wait_time)
        
        # All strategies failed
        self.detection_history.append(detection_event)
        self.logger.error(f"❌ All fallback strategies failed for {detection_type.value}")
        
        # Log comprehensive failure information
        error_handler.log_automation_detection(
            error_str=f"All fallback strategies failed for {detection_type.value}",
            context_str=f"method: handle_detection, detection_type: {detection_type.value}, total_attempts: {max_attempts}, strategies_attempted: {[s['strategy'] for s in detection_event['strategies_attempted']]}, page_url: {detection_event['url']}, page_title: {detection_event['page_title']}, user_agent: {detection_event['user_agent']}, detection_history_count: {len(self.detection_history)}",
            full_error=f"All fallback strategies failed for {detection_type.value}"
        )
        
        return FallbackResult(
            success=False,
            strategy_used=FallbackStrategy.MANUAL_INTERVENTION,
            detection_bypassed=False,
            error_message="All automated fallback strategies failed",
            retry_recommended=True
        )
    
    def _get_strategies_for_detection(self, detection_type: DetectionType) -> List[FallbackStrategy]:
        """Get appropriate strategies for specific detection type"""
        strategy_map = {
            DetectionType.CAPTCHA: [
                FallbackStrategy.DELAY_RANDOMIZATION,
                FallbackStrategy.SESSION_RESET,
                FallbackStrategy.BROWSER_RESTART,
                FallbackStrategy.MANUAL_INTERVENTION
            ],
            DetectionType.RECAPTCHA: [
                FallbackStrategy.BEHAVIORAL_MIMICKING,
                FallbackStrategy.USER_AGENT_ROTATION,
                FallbackStrategy.SESSION_RESET,
                FallbackStrategy.MANUAL_INTERVENTION
            ],
            DetectionType.BOT_DETECTION: [
                FallbackStrategy.STEALTH_MODE,
                FallbackStrategy.USER_AGENT_ROTATION,
                FallbackStrategy.BEHAVIORAL_MIMICKING,
                FallbackStrategy.BROWSER_RESTART
            ],
            DetectionType.RATE_LIMITING: [
                FallbackStrategy.DELAY_RANDOMIZATION,
                FallbackStrategy.SESSION_RESET,
                FallbackStrategy.BROWSER_RESTART
            ],
            DetectionType.SECURITY_CHECK: [
                FallbackStrategy.BEHAVIORAL_MIMICKING,
                FallbackStrategy.DELAY_RANDOMIZATION,
                FallbackStrategy.SESSION_RESET,
                FallbackStrategy.MANUAL_INTERVENTION
            ],
            DetectionType.UNUSUAL_ACTIVITY: [
                FallbackStrategy.DELAY_RANDOMIZATION,
                FallbackStrategy.BEHAVIORAL_MIMICKING,
                FallbackStrategy.SESSION_RESET
            ],
            DetectionType.ACCESS_DENIED: [
                FallbackStrategy.USER_AGENT_ROTATION,
                FallbackStrategy.SESSION_RESET,
                FallbackStrategy.BROWSER_RESTART,
                FallbackStrategy.MANUAL_INTERVENTION
            ],
            DetectionType.VERIFICATION_REQUIRED: [
                FallbackStrategy.DELAY_RANDOMIZATION,
                FallbackStrategy.MANUAL_INTERVENTION
            ]
        }
        
        return strategy_map.get(detection_type, [FallbackStrategy.MANUAL_INTERVENTION])
    
    async def _execute_strategy(self, strategy: FallbackStrategy, detection_type: DetectionType) -> FallbackResult:
        """Execute a specific fallback strategy"""
        try:
            if strategy == FallbackStrategy.DELAY_RANDOMIZATION:
                return await self._delay_randomization_strategy()
            elif strategy == FallbackStrategy.USER_AGENT_ROTATION:
                return await self._user_agent_rotation_strategy()
            elif strategy == FallbackStrategy.BEHAVIORAL_MIMICKING:
                return await self._behavioral_mimicking_strategy()
            elif strategy == FallbackStrategy.SESSION_RESET:
                return await self._session_reset_strategy()
            elif strategy == FallbackStrategy.STEALTH_MODE:
                return await self._stealth_mode_strategy()
            elif strategy == FallbackStrategy.BROWSER_RESTART:
                return await self._browser_restart_strategy()
            elif strategy == FallbackStrategy.MANUAL_INTERVENTION:
                return await self._manual_intervention_strategy(detection_type)
            else:
                return FallbackResult(
                    success=False,
                    strategy_used=strategy,
                    detection_bypassed=False,
                    error_message=f"Strategy {strategy.value} not implemented"
                )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=strategy,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _delay_randomization_strategy(self) -> FallbackResult:
        """Implement random delays to appear more human-like"""
        try:
            # Random delay between 3-10 seconds
            delay = random.uniform(3, 10)
            self.logger.info(f"⏳ Implementing delay randomization: {delay:.1f}s")
            await asyncio.sleep(delay)
            
            # Add some random mouse movements if page is available
            if self.current_page:
                await self._random_mouse_movements()
            
            return FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=True
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _user_agent_rotation_strategy(self) -> FallbackResult:
        """Rotate user agent to appear as different browser"""
        try:
            if not self.current_context:
                return FallbackResult(
                    success=False,
                    strategy_used=FallbackStrategy.USER_AGENT_ROTATION,
                    detection_bypassed=False,
                    error_message="No browser context available"
                )
            
            # Select random user agent
            new_user_agent = random.choice(self.user_agents)
            self.logger.info(f"🔄 Rotating user agent to: {new_user_agent[:50]}...")
            
            # Create new context with different user agent
            new_context = await self.current_browser.new_context(
                user_agent=new_user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Create new page
            new_page = await new_context.new_page()
            
            # Update current references
            await self.current_context.close()
            self.current_context = new_context
            self.current_page = new_page
            
            return FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.USER_AGENT_ROTATION,
                detection_bypassed=True
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.USER_AGENT_ROTATION,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _behavioral_mimicking_strategy(self) -> FallbackResult:
        """Mimic human behavior patterns"""
        try:
            if not self.current_page:
                return FallbackResult(
                    success=False,
                    strategy_used=FallbackStrategy.BEHAVIORAL_MIMICKING,
                    detection_bypassed=False,
                    error_message="No page available"
                )
            
            self.logger.info("🎭 Implementing behavioral mimicking...")
            
            # Random scrolling
            await self._random_scrolling()
            
            # Random mouse movements
            await self._random_mouse_movements()
            
            # Random pauses
            for _ in range(random.randint(2, 5)):
                await asyncio.sleep(random.uniform(0.5, 2.0))
                await self._random_mouse_movements()
            
            # Simulate reading behavior
            await asyncio.sleep(random.uniform(2, 5))
            
            return FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.BEHAVIORAL_MIMICKING,
                detection_bypassed=True
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.BEHAVIORAL_MIMICKING,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _session_reset_strategy(self) -> FallbackResult:
        """Reset browser session by clearing cookies and storage"""
        try:
            if not self.current_context:
                return FallbackResult(
                    success=False,
                    strategy_used=FallbackStrategy.SESSION_RESET,
                    detection_bypassed=False,
                    error_message="No browser context available"
                )
            
            self.logger.info("🔄 Resetting browser session...")
            
            # Clear cookies
            await self.current_context.clear_cookies()
            
            # Clear local storage and session storage
            if self.current_page:
                await self.current_page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            
            # Wait a bit
            await asyncio.sleep(random.uniform(2, 5))
            
            return FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.SESSION_RESET,
                detection_bypassed=True
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.SESSION_RESET,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _stealth_mode_strategy(self) -> FallbackResult:
        """Enable stealth mode to hide automation indicators"""
        try:
            if not self.current_page:
                return FallbackResult(
                    success=False,
                    strategy_used=FallbackStrategy.STEALTH_MODE,
                    detection_bypassed=False,
                    error_message="No page available"
                )
            
            self.logger.info("🥷 Enabling stealth mode...")
            
            # Hide webdriver property
            await self.current_page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Override plugins
            await self.current_page.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            # Override languages
            await self.current_page.add_init_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            return FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.STEALTH_MODE,
                detection_bypassed=True
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.STEALTH_MODE,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _browser_restart_strategy(self) -> FallbackResult:
        """Restart the entire browser instance"""
        try:
            self.logger.info("🔄 Restarting browser...")
            
            # This strategy requires external coordination
            # Return success to indicate strategy was executed
            # The calling code should handle browser restart
            
            return FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.BROWSER_RESTART,
                detection_bypassed=True,
                retry_recommended=True
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.BROWSER_RESTART,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _manual_intervention_strategy(self, detection_type: DetectionType) -> FallbackResult:
        """Handle cases requiring manual intervention"""
        try:
            self.logger.warning(f"🚨 Manual intervention required for {detection_type.value}")
            
            # Log detailed information for manual review
            if self.current_page:
                url = await self.current_page.url()
                title = await self.current_page.title()
                self.logger.info(f"📍 Current URL: {url}")
                self.logger.info(f"📄 Page Title: {title}")
            
            # Take screenshot for manual review
            if self.current_page:
                screenshot_path = f"manual_intervention_{detection_type.value}_{int(time.time())}.png"
                await self.current_page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.MANUAL_INTERVENTION,
                detection_bypassed=False,
                error_message=f"Manual intervention required for {detection_type.value}",
                retry_recommended=False
            )
        
        except Exception as e:
            return FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.MANUAL_INTERVENTION,
                detection_bypassed=False,
                error_message=str(e)
            )
    
    async def _random_mouse_movements(self):
        """Generate random mouse movements to mimic human behavior"""
        if not self.current_page:
            return
        
        try:
            # Get viewport size
            viewport = self.current_page.viewport_size
            if not viewport:
                viewport = {'width': 1920, 'height': 1080}
            
            # Generate random movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                
                await self.current_page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.5))
        
        except Exception as e:
            self.logger.debug(f"Error in random mouse movements: {str(e)}")
    
    async def _random_scrolling(self):
        """Generate random scrolling to mimic human behavior"""
        if not self.current_page:
            return
        
        try:
            # Random scroll amounts
            for _ in range(random.randint(1, 3)):
                scroll_amount = random.randint(-300, 300)
                await self.current_page.mouse.wheel(0, scroll_amount)
                await asyncio.sleep(random.uniform(0.5, 1.5))
        
        except Exception as e:
            self.logger.debug(f"Error in random scrolling: {str(e)}")
    
    def _update_strategy_success_rate(self, strategy: FallbackStrategy, success: bool):
        """Update success rate tracking for strategies"""
        if strategy not in self.strategy_success_rates:
            self.strategy_success_rates[strategy] = 0.5  # Start with neutral rate
        
        # Simple moving average update
        current_rate = self.strategy_success_rates[strategy]
        new_rate = current_rate * 0.8 + (1.0 if success else 0.0) * 0.2
        self.strategy_success_rates[strategy] = new_rate
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get statistics about strategy effectiveness"""
        return {
            "total_detections": len(self.detection_history),
            "strategy_success_rates": {
                strategy.value: rate for strategy, rate in self.strategy_success_rates.items()
            },
            "recent_detections": self.detection_history[-10:] if self.detection_history else []
        }
    
    def get_recommended_strategy(self, detection_type: DetectionType) -> FallbackStrategy:
        """Get the most effective strategy for a detection type based on history"""
        strategies = self._get_strategies_for_detection(detection_type)
        
        # Sort by success rate
        strategies_with_rates = [
            (strategy, self.strategy_success_rates.get(strategy, 0.5))
            for strategy in strategies
        ]
        strategies_with_rates.sort(key=lambda x: x[1], reverse=True)
        
        return strategies_with_rates[0][0] if strategies_with_rates else FallbackStrategy.MANUAL_INTERVENTION