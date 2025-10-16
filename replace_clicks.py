#!/usr/bin/env python3
"""
Script to replace all .click() calls with safe_click() in google_cloud_automation.py
"""

import re

def replace_clicks_in_file(file_path):
    """Replace all .click() calls with safe_click() in the given file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match various click() patterns
    patterns = [
        # Pattern 1: await element.click()
        (r'await\s+([^.]+)\.click\(\)', r'await self.safe_click(\1)'),
        # Pattern 2: await self.page.locator(...).click()
        (r'await\s+(self\.page\.locator\([^)]+\))\.click\(\)', r'await self.safe_click(\1)'),
        # Pattern 3: await locator.click()
        (r'await\s+([a-zA-Z_][a-zA-Z0-9_]*)\.click\(\)', r'await self.safe_click(\1)'),
    ]
    
    original_content = content
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")
        return True
    else: