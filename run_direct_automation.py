#!/usr/bin/env python3
"""
Direct automation runner - bypasses GUI and runs automation directly
"""

import asyncio
import sys
import time
from google_cloud_automation import GoogleCloudAutomation
from config import get_config

async def run_automation():
    """Run the automation directly with provided credentials"""
    
    # Get email and password from command line or use defaults
    email = "xaxunimdf56aki34XZ@taxtfre.us"
    password = "Parag6969"
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    
    print(f"🚀 Starting automation with email: {email}")
    
    # Initialize automation
    automation = GoogleCloudAutomation()
    
    # Set config values directly
    automation.config.headless = False  # Run in visible mode for debugging
    automation.config.timeout = 30000
    automation.config.wait_timeout = 10000
    
    try:
        # Initialize browser
        await automation.initialize_browser()
        print("✅ Browser initialized")
        
        # Login to Google Cloud
        success = await automation.login_to_google_cloud(email, password)
        if not success:
            print("❌ Login failed")
            return False
        
        print("✅ Login successful")
        
        # Create or select project (this is where popup handling happens)
        project_name = "oauth-test-project-" + str(int(time.time()))
        project_success = await automation.create_or_select_project(project_name)
        if not project_success:
            print("❌ Project creation/selection failed")
            return False
        
        print("✅ Project creation/selection successful")
        
        # Continue with OAuth setup
        oauth_success = await automation.setup_oauth_consent_screen()
        if not oauth_success:
            print("❌ OAuth consent screen setup failed")
            return False
        
        print("✅ OAuth consent screen setup successful")
        
        # Create OAuth credentials
        credentials_success = await automation.create_oauth_credentials()
        if not credentials_success:
            print("❌ OAuth credentials creation failed")
            return False
        
        print("✅ OAuth credentials creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Automation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            await automation.cleanup()
        except:
            pass

def main():
    """Main entry point"""
    try:
        result = asyncio.run(run_automation())
        if result:
            print("🎉 Automation completed successfully!")
        else:
            print("💥 Automation failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()