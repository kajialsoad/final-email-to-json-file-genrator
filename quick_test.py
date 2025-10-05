#!/usr/bin/env python3
"""
Quick test script for OAuth generation
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def quick_test():
    """Quick test of OAuth generation"""
    
    email = "alsoadmunna12@gmail.com"
    password = "mylovema2"
    
    print(f"Testing OAuth for: {email}")
    
    try:
        from oauth_credentials import OAuthCredentialsManager
        from config import get_config
        
        oauth_manager = OAuthCredentialsManager()
        
        print("Initializing browser...")
        await oauth_manager.initialize_browser()
        
        print("Starting OAuth flow...")
        result = await oauth_manager.complete_oauth_setup(email, password)
        
        if result['success']:
            print("✅ Success!")
            print(f"Steps completed: {result['steps_completed']}")
            print(f"Files created: {result['files_created']}")
            print(f"Duration: {result.get('duration', 0):.2f} seconds")
        else:
            print("❌ Failed!")
            print(f"Steps completed: {result['steps_completed']}")
            print(f"Errors: {result['errors']}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())