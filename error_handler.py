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
        
        # Retry configuration
        self.retry_config = {
            ErrorType.NETWORK_ERROR: {'max_retries': 5, 'delay': 2, 'backoff': 2},
            ErrorType.TIMEOUT_ERROR: {'max_retries': 3, 'delay': 5, 'backoff': 1.5},
            ErrorType.BROWSER_INIT: {'max_retries': 3, 'delay': 3, 'backoff': 1},
            ErrorType.LOGIN_FAILED: {'max_retries': 2, 'delay': 10, 'backoff': 1},
            ErrorType.PROJECT_CREATION: {'max_retries': 3, 'delay': 5, 'backoff': 1.5},
            ErrorType.API_ENABLE: {'max_retries': 3, 'delay': 3, 'backoff': 1},
            ErrorType.OAUTH_CONSENT: {'max_retries': 2, 'delay': 5, 'backoff': 1},
            ErrorType.CREDENTIALS_CREATION: {'max_retries': 3, 'delay': 3, 'backoff': 1},
            ErrorType.FILE_DOWNLOAD: {'max_retries': 5, 'delay': 2, 'backoff': 1.5}
        }
        
        # Non-retryable errors
        self.non_retryable_errors = {
            ErrorType.CAPTCHA_DETECTED,
            ErrorType.TWO_FACTOR_AUTH,
            ErrorType.EMAIL_VERIFICATION,
            ErrorType.ACCOUNT_BLOCKED
        }
        
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
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if error should be retried"""
        if error_type in self.non_retryable_errors:
            return False
        
        config = self.retry_config.get(error_type, {'max_retries': 1})
        return attempt < config['max_retries']
    
    def get_retry_delay(self, error_type: ErrorType, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        config = self.retry_config.get(error_type, {'delay': 1, 'backoff': 1})
        base_delay = config['delay']
        backoff = config.get('backoff', 1)
        
        return base_delay * (backoff ** attempt)
    
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
                        if not self.should_retry(error_type, attempt):
                            self.logger.error(f"❌ No more retries for {error_type.value}")
                            break
                        
                        # Calculate delay
                        delay = self.get_retry_delay(error_type, attempt)
                        self.logger.info(f"🔄 Retrying in {delay:.1f}s (attempt {attempt + 2})")
                        
                        await asyncio.sleep(delay)
                
                # If we get here, all retries failed
                raise last_error
            
            return wrapper
        return decorator
    
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

def get_error_summary():
    """Get error summary"""
    return error_handler.create_error_summary()

def export_error_report(file_path: str = None):
    """Export error report"""
    return error_handler.export_error_report(file_path)