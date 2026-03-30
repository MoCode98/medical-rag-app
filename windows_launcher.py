#!/usr/bin/env python3
"""
Windows launcher for Medical RAG Desktop Application.
This is the main entry point for the bundled Windows .exe.
"""

import sys
from pathlib import Path

# Ensure src is in the path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the app in desktop mode
from app import run_desktop

if __name__ == "__main__":
    try:
        run_desktop()
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nApplication error: {e}")
        import traceback
        traceback.print_exc()

        # On Windows, pause so user can see error
        input("\nPress Enter to exit...")
        sys.exit(1)
