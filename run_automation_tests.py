#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automation Detection Test Runner

This script runs comprehensive tests for the automation detection and recovery
mechanisms, generating detailed reports and coverage analysis.
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class AutomationTestRunner:
    """Test runner for automation detection system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results_dir = self.project_root / "test_results"
        self.test_results_dir.mkdir(exist_ok=True)
        
        # Test categories
        self.test_categories = {
            "unit": "Unit tests for individual components",
            "integration": "Integration tests for component interactions", 
            "e2e": "End-to-end tests for complete workflows",
            "performance": "Performance and reliability tests",
            "automation": "Tests related to automation detection",
            "fallback": "Tests for fallback strategies",
            "error_handling": "Tests for error handling mechanisms"
        }
    
    def install_test_dependencies(self) -> bool:
        """Install required test dependencies"""
        print("[INFO] Installing test dependencies...")
        
        dependencies = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-html>=3.1.0",
            "pytest-json-report>=1.5.0",
            "pytest-timeout>=2.1.0",
            "pytest-mock>=3.10.0"
        ]
        
        try:
            for dep in dependencies:
                print(f"  Installing {dep}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], capture_output=True, text=True, check=True)
                
            print("[SUCCESS] Test dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install dependencies: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def run_test_category(self, category: str) -> Dict[str, Any]:
        """Run tests for a specific category"""
        print(f"\n[TEST] Running {category} tests...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.test_results_dir / f"{category}_report_{timestamp}.html"
        json_report_file = self.test_results_dir / f"{category}_report_{timestamp}.json"
        coverage_file = self.test_results_dir / f"{category}_coverage_{timestamp}.xml"
        
        cmd = [
            sys.executable, "-m", "pytest",
            "test_automation_detection.py",
            f"-m", category,
            "--html", str(report_file),
            "--self-contained-html",
            "--json-report", f"--json-report-file={json_report_file}",
            "--cov=automation_fallback_strategies",
            "--cov=error_handler", 
            "--cov=google_cloud_automation",
            "--cov-report=xml:" + str(coverage_file),
            "--cov-report=term-missing",
            "-v",
            "--tb=short"
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            end_time = time.time()
            
            # Parse JSON report if available
            test_results = {}
            if json_report_file.exists():
                with open(json_report_file, 'r') as f:
                    test_results = json.load(f)
            
            return {
                "category": category,
                "success": result.returncode == 0,
                "duration": end_time - start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "report_file": str(report_file),
                "json_report_file": str(json_report_file),
                "coverage_file": str(coverage_file),
                "test_results": test_results
            }
            
        except Exception as e:
            return {
                "category": category,
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories"""
        print("[START] Starting comprehensive automation detection tests...")
        
        # Install dependencies first
        if not self.install_test_dependencies():
            return {"success": False, "error": "Failed to install test dependencies"}
        
        overall_start_time = time.time()
        results = {}
        
        # Run tests for each category
        for category in self.test_categories.keys():
            category_result = self.run_test_category(category)
            results[category] = category_result
            
            if category_result["success"]:
                print(f"[PASS] {category} tests passed")
            else:
                print(f"[FAIL] {category} tests failed")
        
        overall_duration = time.time() - overall_start_time
        
        # Generate summary report
        summary = self.generate_summary_report(results, overall_duration)
        
        return {
            "success": all(result["success"] for result in results.values()),
            "duration": overall_duration,
            "category_results": results,
            "summary": summary
        }
    
    def generate_summary_report(self, results: Dict[str, Any], total_duration: float) -> Dict[str, Any]:
        """Generate a comprehensive summary report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary = {
            "timestamp": timestamp,
            "total_duration": total_duration,
            "categories_tested": len(results),
            "categories_passed": sum(1 for r in results.values() if r["success"]),
            "categories_failed": sum(1 for r in results.values() if not r["success"]),
            "overall_success": all(r["success"] for r in results.values()),
            "category_details": {}
        }
        
        for category, result in results.items():
            summary["category_details"][category] = {
                "description": self.test_categories[category],
                "success": result["success"],
                "duration": result.get("duration", 0),
                "test_count": self._extract_test_count(result),
                "passed_count": self._extract_passed_count(result),
                "failed_count": self._extract_failed_count(result)
            }
        
        # Save summary to file
        summary_file = self.test_results_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate markdown report
        self.generate_markdown_report(summary, summary_file.with_suffix('.md'))
        
        return summary
    
    def _extract_test_count(self, result: Dict[str, Any]) -> int:
        """Extract total test count from result"""
        test_results = result.get("test_results", {})
        return test_results.get("summary", {}).get("total", 0)
    
    def _extract_passed_count(self, result: Dict[str, Any]) -> int:
        """Extract passed test count from result"""
        test_results = result.get("test_results", {})
        return test_results.get("summary", {}).get("passed", 0)
    
    def _extract_failed_count(self, result: Dict[str, Any]) -> int:
        """Extract failed test count from result"""
        test_results = result.get("test_results", {})
        return test_results.get("summary", {}).get("failed", 0)
    
    def generate_markdown_report(self, summary: Dict[str, Any], output_file: Path):
        """Generate a markdown test report"""
        content = f"""# Automation Detection Test Report

**Generated:** {summary['timestamp']}  
**Total Duration:** {summary['total_duration']:.2f} seconds  
**Overall Result:** {'[PASS] PASSED' if summary['overall_success'] else '[FAIL] FAILED'}

## Summary

- **Categories Tested:** {summary['categories_tested']}
- **Categories Passed:** {summary['categories_passed']}
- **Categories Failed:** {summary['categories_failed']}

## Test Categories

"""
        
        for category, details in summary['category_details'].items():
            status_icon = "[PASS]" if details['success'] else "[FAIL]"
            content += f"""### [{status_icon}] {category.title()} Tests

**Description:** {details['description']}  
**Duration:** {details['duration']:.2f} seconds  
**Tests:** {details['passed_count']}/{details['test_count']} passed

"""
        
        content += f"""## Test Results Location

All detailed test reports and coverage files are saved in:
`{self.test_results_dir}`

## Next Steps

"""
        
        if summary['overall_success']:
            content += """[PASS] All automation detection tests passed successfully!

The enhanced error handling and recovery mechanisms are working correctly:
- Automation detection patterns are properly identified
- Fallback strategies are executing as expected
- Error logging and classification is functioning
- Integration with Google Cloud automation is working

"""
        else:
            content += """[FAIL] Some tests failed. Please review the detailed reports and address any issues:

1. Check the HTML reports for detailed test failure information
2. Review the coverage reports to ensure adequate test coverage
3. Fix any failing tests before deploying the automation system
4. Re-run tests after making fixes

"""
        
        with open(output_file, 'w') as f:
            f.write(content)
        
        print(f"Markdown report saved to: {output_file}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of test results"""
        print("\n" + "="*60)
        print("AUTOMATION DETECTION TEST SUMMARY")
        print("="*60)
        
        summary = results["summary"]
        
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"Overall Result: {'PASSED' if summary['overall_success'] else 'FAILED'}")
        print(f"Categories: {summary['categories_passed']}/{summary['categories_tested']} passed")
        
        print("\nCategory Results:")
        for category, details in summary['category_details'].items():
            status = "PASS" if details['success'] else "FAIL"
            print(f"  [{status}] {category:15} - {details['passed_count']:2}/{details['test_count']:2} tests ({details['duration']:.1f}s)")
        
        print(f"\nReports saved to: {self.test_results_dir}")
        print("="*60)


def main():
    """Main entry point for test runner"""
    runner = AutomationTestRunner()
    
    try:
        results = runner.run_all_tests()
        runner.print_summary(results)
        
        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)
        
    except KeyboardInterrupt:
        print("\n[WARNING] Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()