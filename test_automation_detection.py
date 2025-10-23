#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Tests for Automation Detection and Recovery Mechanisms

This module contains comprehensive tests to verify the enhanced error handling
and recovery mechanisms for automation detection scenarios.
"""

import asyncio
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock, PropertyMock
from typing import Dict, Any, List

from automation_fallback_strategies import (
    AutomationFallbackHandler, 
    DetectionType, 
    FallbackStrategy, 
    FallbackResult
)
from error_handler import ErrorHandler, ErrorType, ErrorSeverity
from config import ConfigManager, get_config
from google_cloud_automation import GoogleCloudAutomation


class TestAutomationDetection:
    """Test suite for automation detection and recovery mechanisms"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing"""
        config = Mock(spec=ConfigManager)
        config.browser = Mock()
        config.browser.randomize_user_agent = True
        config.browser.use_realistic_mouse_movements = True
        config.browser.randomize_timing = True
        config.automation = Mock()
        config.automation.human_delay_min = 1.0
        config.automation.human_delay_max = 3.0
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing"""
        return Mock()
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page for testing"""
        page = AsyncMock()
        page.url.return_value = "https://console.cloud.google.com"
        page.title.return_value = "Google Cloud Console"
        page.content.return_value = "<html><body>Test content</body></html>"
        page.evaluate.return_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        page.viewport_size = {"width": 1920, "height": 1080}
        return page
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock browser context for testing"""
        context = AsyncMock()
        context.browser = Mock()
        context.browser.version = "120.0.0.0"
        return context
    
    @pytest.fixture
    def mock_browser(self):
        """Create a mock browser for testing"""
        return AsyncMock()
    
    @pytest.fixture
    def fallback_handler(self, mock_config, mock_logger):
        """Create a fallback handler instance for testing"""
        return AutomationFallbackHandler(mock_config, mock_logger)
    
    @pytest.fixture
    def error_handler(self):
        """Create an error handler instance for testing"""
        return ErrorHandler()


class TestDetectionPatterns(TestAutomationDetection):
    """Test automation detection pattern recognition"""
    
    @pytest.mark.asyncio
    async def test_captcha_detection(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test CAPTCHA detection and handling"""
        # Mock page content with CAPTCHA indicators
        mock_page.content.return_value = """
        <html>
            <body>
                <div>Please verify you're human</div>
                <div class="captcha-container">
                    <img src="captcha.png" alt="CAPTCHA">
                </div>
            </body>
        </html>
        """
        
        with patch.object(fallback_handler, '_execute_strategy') as mock_execute:
            mock_execute.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=True
            )
            
            result = await fallback_handler.handle_detection(
                DetectionType.CAPTCHA,
                mock_page,
                mock_context,
                mock_browser
            )
            
            assert result.success is True
            assert result.strategy_used == FallbackStrategy.DELAY_RANDOMIZATION
            assert result.detection_bypassed is True
    
    @pytest.mark.asyncio
    async def test_bot_detection(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test bot detection and handling"""
        mock_page.content.return_value = """
        <html>
            <body>
                <div>Automated software detected</div>
                <div>Access denied due to bot activity</div>
            </body>
        </html>
        """
        
        with patch.object(fallback_handler, '_execute_strategy') as mock_execute:
            mock_execute.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.STEALTH_MODE,
                detection_bypassed=True
            )
            
            result = await fallback_handler.handle_detection(
                DetectionType.BOT_DETECTION,
                mock_page,
                mock_context,
                mock_browser
            )
            
            assert result.success is True
            assert result.strategy_used == FallbackStrategy.STEALTH_MODE
    
    @pytest.mark.asyncio
    async def test_rate_limiting_detection(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test rate limiting detection and handling"""
        mock_page.content.return_value = """
        <html>
            <body>
                <div>Too many requests</div>
                <div>Rate limit exceeded</div>
            </body>
        </html>
        """
        
        with patch.object(fallback_handler, '_execute_strategy') as mock_execute:
            mock_execute.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=True
            )
            
            result = await fallback_handler.handle_detection(
                DetectionType.RATE_LIMITING,
                mock_page,
                mock_context,
                mock_browser
            )
            
            assert result.success is True


class TestFallbackStrategies(TestAutomationDetection):
    """Test individual fallback strategies"""
    
    @pytest.mark.asyncio
    async def test_user_agent_rotation_strategy(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test user agent rotation strategy"""
        original_user_agent = "Mozilla/5.0 (Original)"
        
        with patch.object(fallback_handler, '_user_agent_rotation_strategy') as mock_strategy:
            mock_strategy.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.USER_AGENT_ROTATION,
                detection_bypassed=True
            )
            
            result = await fallback_handler._execute_strategy(
                FallbackStrategy.USER_AGENT_ROTATION,
                DetectionType.BOT_DETECTION
            )
            
            assert result.success is True
            assert result.strategy_used == FallbackStrategy.USER_AGENT_ROTATION
    
    @pytest.mark.asyncio
    async def test_delay_randomization_strategy(self, fallback_handler):
        """Test delay randomization strategy"""
        with patch.object(fallback_handler, '_delay_randomization_strategy') as mock_strategy:
            mock_strategy.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=True
            )
            
            result = await fallback_handler._execute_strategy(
                FallbackStrategy.DELAY_RANDOMIZATION,
                DetectionType.RATE_LIMITING
            )
            
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_stealth_mode_strategy(self, fallback_handler):
        """Test stealth mode strategy"""
        with patch.object(fallback_handler, '_stealth_mode_strategy') as mock_strategy:
            mock_strategy.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.STEALTH_MODE,
                detection_bypassed=True
            )
            
            result = await fallback_handler._execute_strategy(
                FallbackStrategy.STEALTH_MODE,
                DetectionType.BOT_DETECTION
            )
            
            assert result.success is True


class TestErrorHandling(TestAutomationDetection):
    """Test error handling and logging mechanisms"""
    
    def test_error_classification(self, error_handler):
        """Test automation error classification"""
        # Test automation detection error classification
        error = Exception("Automated software detected")
        context = "page_url: https://console.cloud.google.com"
        
        error_type = error_handler.classify_error(error, context)
        assert error_type in [ErrorType.AUTOMATION_DETECTED, ErrorType.BOT_PROTECTION]
    
    def test_automation_detection_logging(self, error_handler):
        """Test automation detection logging functionality"""
        with patch.object(error_handler, 'automation_logger') as mock_logger:
            error_handler.log_automation_detection(
                error_str="Test automation detection",
                context_str="test context",
                full_error="Test automation detection error"
            )
            
            mock_logger.warning.assert_called()
    
    def test_browser_fingerprint_logging(self, error_handler):
        """Test browser fingerprint logging"""
        fingerprint_data = {
            'user_agent': 'Mozilla/5.0 Test',
            'viewport': '1920x1080',
            'platform': 'Win32',
            'hardware_concurrency': 8,
            'device_memory': 8
        }
        
        with patch.object(error_handler, 'automation_logger') as mock_logger:
            error_handler.log_browser_fingerprint_status(fingerprint_data)
            mock_logger.info.assert_called()


class TestGoogleCloudAutomationIntegration(TestAutomationDetection):
    """Test integration with Google Cloud automation"""
    
    @pytest.mark.asyncio
    async def test_automation_challenge_detection_integration(self):
        """Test automation challenge detection in Google Cloud automation"""
        with patch('google_cloud_automation.GoogleCloudAutomation.__init__', return_value=None):
            automation = GoogleCloudAutomation()
            # Manually set required attributes that would normally be set by __init__
            automation.config = Mock()
            automation.logger = Mock()
            automation.page = AsyncMock()
            automation.page.content.return_value = """
            <html>
                <body>
                    <div>Verify you're human</div>
                    <div>Unusual traffic detected</div>
                </body>
            </html>
            """
            type(automation.page).url = PropertyMock(return_value="https://accounts.google.com/signin")
            automation.page.title.return_value = "Sign in - Google Accounts"
            automation.page.evaluate.return_value = "Mozilla/5.0 Test"
            automation.context = Mock()
            automation.browser = Mock()
            automation.fallback_handler = Mock()
            automation.fallback_handler.handle_detection = AsyncMock()
            automation.fallback_handler.handle_detection.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=True
            )
            automation.logger = Mock()
            
            result = await automation._detect_and_handle_automation_challenges("test@example.com")
            
            assert result is True
            automation.fallback_handler.handle_detection.assert_called_once()


class TestEndToEndScenarios(TestAutomationDetection):
    """Test end-to-end automation detection and recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_multiple_detection_attempts(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test handling multiple detection attempts with different strategies"""
        # Simulate multiple failed attempts followed by success
        strategy_results = [
            FallbackResult(success=False, strategy_used=FallbackStrategy.DELAY_RANDOMIZATION, detection_bypassed=False),
            FallbackResult(success=False, strategy_used=FallbackStrategy.USER_AGENT_ROTATION, detection_bypassed=False),
            FallbackResult(success=True, strategy_used=FallbackStrategy.STEALTH_MODE, detection_bypassed=True)
        ]
        
        with patch.object(fallback_handler, '_execute_strategy', side_effect=strategy_results):
            result = await fallback_handler.handle_detection(
                DetectionType.BOT_DETECTION,
                mock_page,
                mock_context,
                mock_browser,
                max_attempts=1  # Only one attempt to test strategy cycling
            )
            
            assert result.success is True
            assert result.strategy_used == FallbackStrategy.STEALTH_MODE
    
    @pytest.mark.asyncio
    async def test_all_strategies_fail(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test scenario where all strategies fail"""
        with patch.object(fallback_handler, '_execute_strategy') as mock_execute:
            mock_execute.return_value = FallbackResult(
                success=False,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=False,
                error_message="Strategy failed"
            )
            
            result = await fallback_handler.handle_detection(
                DetectionType.BOT_DETECTION,
                mock_page,
                mock_context,
                mock_browser,
                max_attempts=1
            )
            
            assert result.success is False
            assert result.strategy_used == FallbackStrategy.MANUAL_INTERVENTION
            assert result.retry_recommended is True


class TestPerformanceAndReliability(TestAutomationDetection):
    """Test performance and reliability of automation detection system"""
    
    @pytest.mark.asyncio
    async def test_detection_performance(self, fallback_handler, mock_page, mock_context, mock_browser):
        """Test that detection and handling completes within reasonable time"""
        import time
        
        start_time = time.time()
        
        with patch.object(fallback_handler, '_execute_strategy') as mock_execute:
            mock_execute.return_value = FallbackResult(
                success=True,
                strategy_used=FallbackStrategy.DELAY_RANDOMIZATION,
                detection_bypassed=True
            )
            
            result = await fallback_handler.handle_detection(
                DetectionType.CAPTCHA,
                mock_page,
                mock_context,
                mock_browser
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within 10 seconds (excluding actual delays)
            assert execution_time < 10.0
            assert result.success is True
    
    def test_strategy_success_rate_tracking(self, fallback_handler):
        """Test that strategy success rates are properly tracked"""
        # Test updating success rates
        fallback_handler._update_strategy_success_rate(FallbackStrategy.DELAY_RANDOMIZATION, True)
        fallback_handler._update_strategy_success_rate(FallbackStrategy.DELAY_RANDOMIZATION, False)
        fallback_handler._update_strategy_success_rate(FallbackStrategy.DELAY_RANDOMIZATION, True)
        
        # Should have some success rate data
        assert FallbackStrategy.DELAY_RANDOMIZATION in fallback_handler.strategy_success_rates
        success_rate = fallback_handler.strategy_success_rates[FallbackStrategy.DELAY_RANDOMIZATION]
        assert 0.0 <= success_rate <= 1.0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])