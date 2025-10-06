#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Reporter System
Comprehensive reporting system for Gmail OAuth automation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

class EmailReporter:
    """Comprehensive email reporting system with organized folder structure"""
    
    def __init__(self, base_reports_dir: str = "reports"):
        self.base_reports_dir = Path(base_reports_dir)
        self.logger = logging.getLogger(__name__)
        self._setup_report_directories()
    
    def _setup_report_directories(self):
        """Create organized report directory structure"""
        try:
            # Main reports directory
            self.base_reports_dir.mkdir(exist_ok=True)
            
            # Subdirectories for different report types
            self.subdirs = {
                'captcha': self.base_reports_dir / 'captcha',
                'verification': self.base_reports_dir / 'verification',
                'two_factor': self.base_reports_dir / 'two_factor',
                'success': self.base_reports_dir / 'success',
                'errors': self.base_reports_dir / 'errors',
                'blocked': self.base_reports_dir / 'blocked',
                'unusual_activity': self.base_reports_dir / 'unusual_activity'
            }
            
            # Create all subdirectories
            for subdir in self.subdirs.values():
                subdir.mkdir(exist_ok=True)
            
            self.logger.info(f"📁 Report directories created: {self.base_reports_dir}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create report directories: {str(e)}")
    
    def save_captcha_report(self, email: str, screenshot_path: str = None, 
                           additional_data: Dict[str, Any] = None) -> str:
        """Save CAPTCHA detection report"""
        return self._save_report(
            report_type='captcha',
            email=email,
            event='captcha_detected',
            status='manual_intervention_required',
            message='CAPTCHA/reCAPTCHA detected during login process - manual solving required',
            screenshot_path=screenshot_path,
            additional_data=additional_data
        )
    
    def save_verification_report(self, email: str, verification_type: str = 'email_verification',
                               screenshot_path: str = None, additional_data: Dict[str, Any] = None) -> str:
        """Save email verification report"""
        if verification_type == 'two_factor_verification':
            return self._save_report(
                report_type='two_factor',
                email=email,
                event='two_factor_verification_required',
                status='verification_pending',
                message='Two-factor verification required - please check your phone and verify manually',
                screenshot_path=screenshot_path,
                additional_data=additional_data
            )
        else:
            return self._save_report(
                report_type='verification',
                email=email,
                event='email_verification_required',
                status='verification_pending',
                message='Email verification required - please check email and verify manually',
                screenshot_path=screenshot_path,
                additional_data=additional_data
            )
    
    def save_success_report(self, email: str, oauth_data: Dict[str, Any] = None,
                          screenshot_path: str = None, additional_data: Dict[str, Any] = None) -> str:
        """Save successful OAuth setup report"""
        return self._save_report(
            report_type='success',
            email=email,
            event='oauth_setup_completed',
            status='success',
            message='OAuth setup completed successfully',
            screenshot_path=screenshot_path,
            additional_data={
                'oauth_data': oauth_data,
                **(additional_data or {})
            }
        )
    
    def save_error_report(self, email: str, error_type: str, error_message: str,
                         screenshot_path: str = None, additional_data: Dict[str, Any] = None) -> str:
        """Save error report"""
        return self._save_report(
            report_type='errors',
            email=email,
            event=f'error_{error_type}',
            status='failed',
            message=error_message,
            screenshot_path=screenshot_path,
            additional_data=additional_data
        )
    
    def save_blocked_report(self, email: str, screenshot_path: str = None,
                          additional_data: Dict[str, Any] = None) -> str:
        """Save account blocked report"""
        return self._save_report(
            report_type='blocked',
            email=email,
            event='account_blocked',
            status='blocked',
            message='Account appears to be blocked, suspended, or restricted',
            screenshot_path=screenshot_path,
            additional_data=additional_data
        )
    
    def save_unusual_activity_report(self, email: str, screenshot_path: str = None,
                                   additional_data: Dict[str, Any] = None) -> str:
        """Save unusual activity report"""
        return self._save_report(
            report_type='unusual_activity',
            email=email,
            event='unusual_activity_detected',
            status='security_challenge',
            message='Unusual activity detected - additional verification required',
            screenshot_path=screenshot_path,
            additional_data=additional_data
        )
    
    def _save_report(self, report_type: str, email: str, event: str, status: str,
                    message: str, screenshot_path: str = None, 
                    additional_data: Dict[str, Any] = None) -> str:
        """Save a report with the specified parameters"""
        try:
            timestamp = datetime.now()
            
            # Create report data
            report = {
                "timestamp": timestamp.isoformat(),
                "email": email,
                "event": event,
                "status": status,
                "message": message,
                "report_type": report_type,
                "screenshot": screenshot_path,
                "action_taken": self._get_action_taken(report_type),
                "next_action": self._get_next_action(report_type),
                "additional_data": additional_data or {}
            }
            
            # Generate filename
            safe_email = email.replace('@', '_').replace('.', '_')
            timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_report_{safe_email}_{timestamp_str}.json"
            
            # Save to appropriate subdirectory
            report_dir = self.subdirs.get(report_type, self.base_reports_dir / 'errors')
            report_path = report_dir / filename
            
            # Write report file
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 {report_type.title()} report saved: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save {report_type} report for {email}: {str(e)}")
            return ""
    
    def _get_action_taken(self, report_type: str) -> str:
        """Get the action taken based on report type"""
        actions = {
            'captcha': 'browser_kept_open_for_manual_solving',
            'verification': 'webdriver_closed_for_this_email',
            'two_factor': 'webdriver_closed_for_this_email',
            'success': 'oauth_credentials_saved',
            'errors': 'error_logged_and_reported',
            'blocked': 'webdriver_closed_for_this_email',
            'unusual_activity': 'manual_intervention_required'
        }
        return actions.get(report_type, 'unknown_action')
    
    def _get_next_action(self, report_type: str) -> str:
        """Get the next action based on report type"""
        actions = {
            'captcha': 'wait_for_manual_captcha_solving',
            'verification': 'continue_with_next_email',
            'two_factor': 'continue_with_next_email',
            'success': 'continue_with_next_email',
            'errors': 'continue_with_next_email',
            'blocked': 'continue_with_next_email',
            'unusual_activity': 'wait_for_manual_intervention'
        }
        return actions.get(report_type, 'unknown_next_action')
    
    def get_report_summary(self) -> Dict[str, Any]:
        """Get a summary of all reports"""
        try:
            summary = {
                'total_reports': 0,
                'by_type': {},
                'by_status': {},
                'latest_reports': []
            }
            
            # Count reports by type
            for report_type, report_dir in self.subdirs.items():
                if report_dir.exists():
                    report_files = list(report_dir.glob('*.json'))
                    summary['by_type'][report_type] = len(report_files)
                    summary['total_reports'] += len(report_files)
            
            # Get latest reports (last 10)
            all_reports = []
            for report_dir in self.subdirs.values():
                if report_dir.exists():
                    for report_file in report_dir.glob('*.json'):
                        try:
                            with open(report_file, 'r', encoding='utf-8') as f:
                                report_data = json.load(f)
                                report_data['file_path'] = str(report_file)
                                all_reports.append(report_data)
                        except Exception:
                            continue
            
            # Sort by timestamp and get latest
            all_reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            summary['latest_reports'] = all_reports[:10]
            
            # Count by status
            for report in all_reports:
                status = report.get('status', 'unknown')
                summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate report summary: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Clean up reports older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = 0
            for report_dir in self.subdirs.values():
                if report_dir.exists():
                    for report_file in report_dir.glob('*.json'):
                        try:
                            # Check file modification time
                            file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                report_file.unlink()
                                deleted_count += 1
                        except Exception:
                            continue
            
            self.logger.info(f"🧹 Cleaned up {deleted_count} old reports (older than {days_to_keep} days)")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup old reports: {str(e)}")
            return 0

# Global reporter instance
email_reporter = EmailReporter()