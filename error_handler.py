#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Error Handling and Logging System
Advanced error handling, retry mechanisms, and detailed logging
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import functools
from functools import wraps

# Optional imports with fallbacks
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

class ErrorType(Enum):
    """Error type enumeration"""
    BROWSER_INIT = "browser_initialization"
    LOGIN_FAILED = "login_failed"
    CAPTCHA_DETECTED = "captcha_detected"
    TWO_FACTOR_AUTH = "two_factor_authentication"
    EMAIL_VERIFICATION = "email_verification"
    ACCOUNT_BLOCKED = "account_blocked"
    PROJECT_CREATION = "project_creation"
    API_ENABLE = "api_enable"
    OAUTH_CONSENT = "oauth_consent"
    CREDENTIALS_CREATION = "credentials_creation"
    FILE_DOWNLOAD = "file_download"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTOMATION_DETECTED = "automation_detected"
    BOT_PROTECTION = "bot_protection"
    RATE_LIMITED = "rate_limited"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorHandler:
    """Advanced error handling and logging system"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Error tracking
        self.error_counts = {}
        self.error_history = []
        
        # Enhanced retry configuration with specialized project creation handling
        self.retry_config = {
            ErrorType.NETWORK_ERROR: {'max_retries': 5, 'delay': 2, 'backoff': 2},
            ErrorType.TIMEOUT_ERROR: {'max_retries': 3, 'delay': 5, 'backoff': 1.5},
            ErrorType.BROWSER_INIT: {'max_retries': 3, 'delay': 3, 'backoff': 1},
            ErrorType.LOGIN_FAILED: {'max_retries': 2, 'delay': 10, 'backoff': 1},
            # Enhanced project creation retry with more attempts and longer delays
            ErrorType.PROJECT_CREATION: {'max_retries': 5, 'delay': 8, 'backoff': 1.3, 'max_delay': 30},
            ErrorType.API_ENABLE: {'max_retries': 4, 'delay': 4, 'backoff': 1.2},
            ErrorType.OAUTH_CONSENT: {'max_retries': 3, 'delay': 6, 'backoff': 1.2},
            ErrorType.CREDENTIALS_CREATION: {'max_retries': 4, 'delay': 4, 'backoff': 1.2},
            ErrorType.FILE_DOWNLOAD: {'max_retries': 5, 'delay': 2, 'backoff': 1.5},
            # Automation detection retry with longer delays and fewer attempts
            ErrorType.AUTOMATION_DETECTED: {'max_retries': 2, 'delay': 30, 'backoff': 2, 'max_delay': 120},
            ErrorType.BOT_PROTECTION: {'max_retries': 1, 'delay': 60, 'backoff': 1, 'max_delay': 60},
            ErrorType.RATE_LIMITED: {'max_retries': 3, 'delay': 15, 'backoff': 2, 'max_delay': 60},
            ErrorType.SUSPICIOUS_ACTIVITY: {'max_retries': 1, 'delay': 45, 'backoff': 1, 'max_delay': 45}
        }
        
        # Context-specific retry configurations for different project creation scenarios
        self.context_retry_config = {
            'project_creation': {
                'max_retries': 5,
                'delay': 8,
                'backoff': 1.3,
                'max_delay': 30,
                'verification_retries': 3,
                'verification_delay': 5
            },
            'project_verification': {
                'max_retries': 3,
                'delay': 5,
                'backoff': 1.2,
                'max_delay': 15
            },
            'project_selection': {
                'max_retries': 4,
                'delay': 3,
                'backoff': 1.5,
                'max_delay': 20
            }
        }
        
        # Non-retryable errors (require manual intervention)
        self.non_retryable_errors = {
            ErrorType.CAPTCHA_DETECTED,
            ErrorType.TWO_FACTOR_AUTH,
            ErrorType.EMAIL_VERIFICATION,
            ErrorType.ACCOUNT_BLOCKED
        }
        
        # Automation detection patterns for enhanced logging
        self.automation_detection_patterns = [
            "automation", "bot", "webdriver", "selenium", "playwright",
            "automated", "script", "robot", "suspicious activity",
            "unusual activity", "rate limit", "too many requests",
            "blocked", "protection", "security", "verification required",
            "human verification", "prove you're not a robot"
        ]
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Main logger
        self.logger = logging.getLogger('gmail_oauth_automation')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for detailed logs
        detailed_log_file = self.log_dir / f"detailed_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(detailed_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # File handler for errors only
        error_log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Specialized automation detection logger
        automation_log_file = self.log_dir / f"automation_detection_{datetime.now().strftime('%Y%m%d')}.log"
        self.automation_logger = logging.getLogger('automation_detection')
        self.automation_logger.setLevel(logging.DEBUG)
        self.automation_logger.handlers.clear()
        
        automation_handler = logging.FileHandler(automation_log_file, encoding='utf-8')
        automation_handler.setLevel(logging.DEBUG)
        automation_formatter = logging.Formatter(
            '%(asctime)s - AUTOMATION_DETECTION - %(levelname)s - %(message)s'
        )
        automation_handler.setFormatter(automation_formatter)
        self.automation_logger.addHandler(automation_handler)
        self.automation_logger.propagate = False
        
        # Console handler with optional color support
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        if HAS_COLORLOG:
            color_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
        
    def classify_error(self, error: Exception, context: str = "") -> ErrorType:
        """Classify error type based on exception and context"""
        error_str = str(error).lower()
        context_str = context.lower()
        
        # Check for automation detection patterns first
        automation_detected = any(pattern in error_str or pattern in context_str 
                                for pattern in self.automation_detection_patterns)
        
        if automation_detected:
            # Log automation detection
            self.log_automation_detection(error_str, context_str, str(error))
            
            # Classify specific automation detection types
            if any(pattern in error_str for pattern in ["rate limit", "too many requests"]):
                return ErrorType.RATE_LIMITED
            elif any(pattern in error_str for pattern in ["bot", "robot", "human verification"]):
                return ErrorType.BOT_PROTECTION
            elif any(pattern in error_str for pattern in ["suspicious activity", "unusual activity"]):
                return ErrorType.SUSPICIOUS_ACTIVITY
            else:
                return ErrorType.AUTOMATION_DETECTED
        
        # Browser initialization errors
        if "browser" in error_str or "webdriver" in error_str or "playwright" in error_str:
            return ErrorType.BROWSER_INIT
        
        # Network errors
        if any(keyword in error_str for keyword in ["network", "connection", "dns", "resolve"]):
            return ErrorType.NETWORK_ERROR
        
        # Timeout errors
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorType.TIMEOUT_ERROR
        
        # Login related errors
        if "login" in context.lower() or "signin" in context.lower():
            if "captcha" in error_str or "recaptcha" in error_str:
                return ErrorType.CAPTCHA_DETECTED
            elif "verification" in error_str or "verify" in error_str:
                if "phone" in error_str or "sms" in error_str or "code" in error_str:
                    return ErrorType.TWO_FACTOR_AUTH
                else:
                    return ErrorType.EMAIL_VERIFICATION
            elif "blocked" in error_str or "suspended" in error_str or "disabled" in error_str:
                return ErrorType.ACCOUNT_BLOCKED
            else:
                return ErrorType.LOGIN_FAILED
        
        # Project creation errors
        if "project" in context.lower():
            return ErrorType.PROJECT_CREATION
        
        # API enable errors
        if "api" in context.lower() and "enable" in context.lower():
            return ErrorType.API_ENABLE
        
        # OAuth consent errors
        if "oauth" in context.lower() and "consent" in context.lower():
            return ErrorType.OAUTH_CONSENT
        
        # Credentials creation errors
        if "credential" in context.lower():
            return ErrorType.CREDENTIALS_CREATION
        
        # File download errors
        if "download" in context.lower():
            return ErrorType.FILE_DOWNLOAD
        
        return ErrorType.UNKNOWN_ERROR
    
    def get_error_severity(self, error_type: ErrorType) -> ErrorSeverity:
        """Determine error severity"""
        critical_errors = {
            ErrorType.BROWSER_INIT,
            ErrorType.ACCOUNT_BLOCKED
        }
        
        high_errors = {
            ErrorType.LOGIN_FAILED,
            ErrorType.PROJECT_CREATION,
            ErrorType.CREDENTIALS_CREATION
        }
        
        medium_errors = {
            ErrorType.CAPTCHA_DETECTED,
            ErrorType.TWO_FACTOR_AUTH,
            ErrorType.EMAIL_VERIFICATION,
            ErrorType.API_ENABLE,
            ErrorType.OAUTH_CONSENT
        }
        
        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in high_errors:
            return ErrorSeverity.HIGH
        elif error_type in medium_errors:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def log_error(self, error: Exception, context: str = "", email: str = "", 
                  additional_data: Dict[str, Any] = None):
        """Log error with comprehensive details"""
        error_type = self.classify_error(error, context)
        severity = self.get_error_severity(error_type)
        
        # Track error counts
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Create error record
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type.value,
            'severity': severity.value,
            'email': email,
            'context': context,
            'error_message': str(error),
            'error_class': error.__class__.__name__,
            'traceback': traceback.format_exc(),
            'count': self.error_counts[error_type],
            'additional_data': additional_data or {}
        }
        
        # Add to history
        self.error_history.append(error_record)
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"🚨 CRITICAL ERROR [{error_type.value}] {email}: {str(error)}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"❌ HIGH ERROR [{error_type.value}] {email}: {str(error)}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"⚠️ MEDIUM ERROR [{error_type.value}] {email}: {str(error)}")
        else:
            self.logger.info(f"ℹ️ LOW ERROR [{error_type.value}] {email}: {str(error)}")
        
        # Log detailed information at debug level
        self.logger.debug(f"Error details: {json.dumps(error_record, indent=2)}")
        
        return error_record
    
    def should_retry(self, error_type: ErrorType, attempt: int, context: str = "") -> bool:
        """Determine if error should be retried with context-specific handling"""
        if error_type in self.non_retryable_errors:
            return False
        
        # Check for context-specific configuration first
        if context and context in self.context_retry_config:
            config = self.context_retry_config[context]
        else:
            config = self.retry_config.get(error_type, {'max_retries': 1})
        
        return attempt < config['max_retries']
    
    def get_retry_delay(self, error_type: ErrorType, attempt: int, context: str = "") -> float:
        """Calculate retry delay with exponential backoff and max delay limits"""
        # Check for context-specific configuration first
        if context and context in self.context_retry_config:
            config = self.context_retry_config[context]
        else:
            config = self.retry_config.get(error_type, {'delay': 1, 'backoff': 1})
        
        base_delay = config['delay']
        backoff = config.get('backoff', 1)
        max_delay = config.get('max_delay', 60)  # Default max delay of 60 seconds
        
        # Calculate delay with exponential backoff
        calculated_delay = base_delay * (backoff ** attempt)
        
        # Apply max delay limit
        return min(calculated_delay, max_delay)
    
    def retry_async(self, error_types: List[ErrorType] = None, context: str = ""):
        """Decorator for async functions with retry logic"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_error = None
                
                for attempt in range(10):  # Max 10 attempts total
                    try:
                        return await func(*args, **kwargs)
                    
                    except Exception as e:
                        error_type = self.classify_error(e, context)
                        last_error = e
                        
                        # Log the error
                        email = kwargs.get('email', args[1] if len(args) > 1 else '')
                        self.log_error(e, context, email, {'attempt': attempt + 1})
                        
                        # Check if we should retry
                        if not self.should_retry(error_type, attempt, context):
                            self.logger.error(f"❌ No more retries for {error_type.value} in context '{context}'")
                            break
                        
                        # Calculate delay
                        delay = self.get_retry_delay(error_type, attempt, context)
                        self.logger.info(f"🔄 Retrying in {delay:.1f}s (attempt {attempt + 2}) for {error_type.value} in context '{context}'")
                        
                        await asyncio.sleep(delay)
                
                # If we get here, all retries failed
                raise last_error
            
            return wrapper
        return decorator
    
    def retry_with_recovery(self, context: str = "", recovery_actions: List[Callable] = None):
        """Enhanced retry decorator with recovery actions for critical workflows like project creation"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_error = None
                recovery_actions_list = recovery_actions or []
                
                # Get context-specific configuration
                config = self.context_retry_config.get(context, self.retry_config.get(ErrorType.PROJECT_CREATION, {}))
                max_retries = config.get('max_retries', 3)
                
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    
                    except Exception as e:
                        error_type = self.classify_error(e, context)
                        last_error = e
                        
                        # Log the error with enhanced context
                        email = kwargs.get('email', args[1] if len(args) > 1 else '')
                        additional_data = {
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'context': context,
                            'recovery_actions_available': len(recovery_actions_list)
                        }
                        self.log_error(e, context, email, additional_data)
                        
                        # Don't retry on last attempt
                        if attempt >= max_retries - 1:
                            self.logger.error(f"❌ Final attempt failed for {error_type.value} in context '{context}'")
                            break
                        
                        # Execute recovery actions before retry
                        if recovery_actions_list and attempt < len(recovery_actions_list):
                            try:
                                self.logger.info(f"🔧 Executing recovery action {attempt + 1} for {context}")
                                await recovery_actions_list[attempt](*args, **kwargs)
                            except Exception as recovery_error:
                                self.logger.warning(f"⚠️ Recovery action failed: {str(recovery_error)}")
                        
                        # Calculate delay
                        delay = self.get_retry_delay(error_type, attempt, context)
                        self.logger.info(f"🔄 Retrying in {delay:.1f}s (attempt {attempt + 2}/{max_retries}) for {error_type.value}")
                        
                        await asyncio.sleep(delay)
                
                # If we get here, all retries failed
                self.logger.critical(f"🚨 All retry attempts exhausted for {context}")
                raise last_error
            
            return wrapper
        return decorator
    
    def log_automation_detection(self, error_str: str, context_str: str, full_error: str):
        """Log detailed automation detection information"""
        detection_info = {
            'timestamp': datetime.now().isoformat(),
            'error_message': error_str,
            'context': context_str,
            'full_error': full_error,
            'detected_patterns': [pattern for pattern in self.automation_detection_patterns 
                                if pattern in error_str or pattern in context_str],
            'browser_fingerprint_active': True,  # This would be set based on actual config
            'user_agent_rotation_active': True,  # This would be set based on actual config
        }
        
        # Log to automation detection file
        self.automation_logger.warning(f"AUTOMATION DETECTED: {json.dumps(detection_info, indent=2)}")
        
        # Also log to main logger with special marker
        self.logger.warning(f"🤖 AUTOMATION DETECTION: {error_str} | Context: {context_str}")
        
        # Log recommendations
        recommendations = self._get_automation_detection_recommendations(detection_info['detected_patterns'])
        self.automation_logger.info(f"RECOMMENDATIONS: {json.dumps(recommendations, indent=2)}")
    
    def _get_automation_detection_recommendations(self, detected_patterns: List[str]) -> List[str]:
        """Get recommendations based on detected automation patterns"""
        recommendations = []
        
        if any(pattern in detected_patterns for pattern in ["webdriver", "selenium", "playwright"]):
            recommendations.append("Consider enhancing browser fingerprint randomization")
            recommendations.append("Verify webdriver property is properly hidden")
        
        if any(pattern in detected_patterns for pattern in ["bot", "robot"]):
            recommendations.append("Increase delays between actions")
            recommendations.append("Add more realistic mouse movements")
            recommendations.append("Consider rotating user agents more frequently")
        
        if any(pattern in detected_patterns for pattern in ["rate limit", "too many requests"]):
            recommendations.append("Implement longer delays between requests")
            recommendations.append("Consider using proxy rotation")
            recommendations.append("Reduce automation frequency")
        
        if any(pattern in detected_patterns for pattern in ["suspicious activity", "unusual activity"]):
            recommendations.append("Review and enhance behavioral patterns")
            recommendations.append("Add more human-like interaction delays")
            recommendations.append("Consider manual intervention")
        
        if not recommendations:
            recommendations.append("Review automation detection patterns and enhance stealth measures")
        
        return recommendations
    
    def log_browser_fingerprint_status(self, fingerprint_data: Dict[str, Any]):
        """Log current browser fingerprint status for debugging"""
        fingerprint_info = {
            'timestamp': datetime.now().isoformat(),
            'user_agent': fingerprint_data.get('user_agent', 'unknown'),
            'viewport': fingerprint_data.get('viewport', 'unknown'),
            'platform': fingerprint_data.get('platform', 'unknown'),
            'languages': fingerprint_data.get('languages', 'unknown'),
            'hardware_concurrency': fingerprint_data.get('hardware_concurrency', 'unknown'),
            'device_memory': fingerprint_data.get('device_memory', 'unknown'),
            'webgl_vendor': fingerprint_data.get('webgl_vendor', 'unknown'),
            'webgl_renderer': fingerprint_data.get('webgl_renderer', 'unknown')
        }
        
        self.automation_logger.info(f"BROWSER_FINGERPRINT: {json.dumps(fingerprint_info, indent=2)}")
    
    def create_error_summary(self) -> Dict[str, Any]:
        """Create error summary report"""
        total_errors = len(self.error_history)
        
        if total_errors == 0:
            return {
                'total_errors': 0,
                'error_types': {},
                'severity_breakdown': {},
                'recent_errors': []
            }
        
        # Count by type
        type_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            error_type = error['error_type']
            severity = error['severity']
            
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Get recent errors (last 10)
        recent_errors = self.error_history[-10:] if len(self.error_history) > 10 else self.error_history
        
        return {
            'total_errors': total_errors,
            'error_types': type_counts,
            'severity_breakdown': severity_counts,
            'recent_errors': recent_errors,
            'most_common_error': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        }
    
    def export_error_report(self, file_path: str = None) -> str:
        """Export detailed error report"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.log_dir / f"error_report_{timestamp}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.create_error_summary(),
            'detailed_errors': self.error_history,
            'retry_configuration': {k.value: v for k, v in self.retry_config.items()}
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"📊 Error report exported: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export error report: {str(e)}")
            return ""
    
    def clear_error_history(self):
        """Clear error history and counts"""
        self.error_history.clear()
        self.error_counts.clear()
        self.logger.info("🧹 Error history cleared")

# Global error handler instance
error_handler = ErrorHandler()

# Convenience functions
def log_error(error: Exception, context: str = "", email: str = "", 
              additional_data: Dict[str, Any] = None):
    """Convenience function to log errors"""
    return error_handler.log_error(error, context, email, additional_data)

def retry_async(error_types: List[ErrorType] = None, context: str = ""):
    """Convenience decorator for retry logic"""
    return error_handler.retry_async(error_types, context)

def retry_with_recovery(context: str = "", recovery_actions: List[Callable] = None):
    """Convenience decorator for enhanced retry logic with recovery actions"""
    return error_handler.retry_with_recovery(context, recovery_actions)

def get_error_summary():
    """Get error summary"""
    return error_handler.create_error_summary()

def export_error_report(file_path: str = None):
    """Export error report"""
    return error_handler.export_error_report(file_path)