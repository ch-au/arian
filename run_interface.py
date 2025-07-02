#!/usr/bin/env python3
"""
Launch script for the Negotiation Configuration Interface

This script launches the Streamlit interface for configuring and running
AI negotiations. It provides a simple way to start the web interface.
"""

import subprocess
import sys
from pathlib import Path
import os

def main():
    """Launch the Streamlit interface."""
    print("🚀 Starting AI Negotiation Configuration Interface...")
    print("="*60)
    
    # Get the current directory
    current_dir = Path(__file__).parent
    interface_file = current_dir / "interface.py"
    
    # Check if interface file exists
    if not interface_file.exists():
        print("❌ Error: interface.py not found!")
        print(f"   Expected location: {interface_file}")
        return 1
    
    # Set environment variables for better Streamlit experience
    env = os.environ.copy()
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'
    env['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    env['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
    
    try:
        print("📱 Opening web interface...")
        print("   URL: http://localhost:8501")
        print("   Press Ctrl+C to stop the server")
        print("="*60)
        
        # Launch Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(interface_file)]
        subprocess.run(cmd, env=env, cwd=current_dir)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Interface stopped by user")
        return 0
    except FileNotFoundError:
        print("❌ Error: Streamlit not found!")
        print("   Please install Streamlit: pip install streamlit")
        return 1
    except Exception as e:
        print(f"❌ Error launching interface: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
