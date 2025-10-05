#!/usr/bin/env python3
"""
Test script for single account OAuth generation
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from oauth_credentials import OAuthCredentialsManager
from config import get_config
from error_handler import error_handler

async def test_single_account():
    """Test OAuth generation for a single account"""
    
    # Test credentials
    email = "alsoadmunna12@gmail.com"
    password = "mylovema2"
    
    print(f"🚀 Testing OAuth generation for: {email}")
    print("=" * 50)
    
    try:
        # Initialize OAuth manager
        config = get_config()
        oauth_manager = OAuthCredentialsManager(config)
        
        print("✓ OAuth manager initialized")
        
        # Generate OAuth credentials
        print(f"📧 Processing account: {email}")
        print("⏳ Starting OAuth flow...")
        
        result = await oauth_manager.generate_oauth_credentials(email, password)
        
        if result['success']:
            print("✅ OAuth generation successful!")
            print(f"📁 Output file: {result['output_file']}")
            print(f"📊 Client ID: {result['client_id'][:20]}...")
            print(f"🔑 Client Secret: {result['client_secret'][:20]}...")
            print(f"🎫 Refresh Token: {result['refresh_token'][:20]}...")
            
            # Show file contents
            if Path(result['output_file']).exists():
                print("\n📄 Generated JSON file contents:")
                print("-" * 30)
                with open(result['output_file'], 'r') as f:
                    content = f.read()
                    print(content)
            
        else:
            print("❌ OAuth generation failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if 'details' in result:
                print(f"Details: {result['details']}")
                
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Gmail OAuth Single Account Test")
    print("=" * 50)
    
    # Run the async test
    asyncio.run(test_single_account())
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()