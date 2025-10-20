#!/usr/bin/env python3
"""
Main entry point for the AI-Powered Financial Query System.
This script can be used to run the application directly or as a package entry point.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the application."""
    try:
        print("🚀 Starting AI-Powered Financial Query System...")
        print("📝 Press Ctrl+C to stop the server")
        print("-" * 60)
        
        # Import and run streamlit directly
        print("🔄 Importing Streamlit CLI...")
        import streamlit.web.cli as stcli
        print("✅ Streamlit CLI imported successfully")
        
        # Get the path to app.py (same directory as main.py)
        current_dir = Path(__file__).parent
        app_path = current_dir / "app.py"
        
        print(f"📁 Looking for app at: {app_path}")
        
        if not app_path.exists():
            print(f"❌ Error: Application file not found at {app_path}")
            return
        
        print("✅ Application file found")
        
        # Set up streamlit arguments
        sys.argv = [
            "streamlit",
            "run",
            str(app_path)
        ]
        
        print("🚀 Launching Streamlit...")
        # Run streamlit
        stcli.main()
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
