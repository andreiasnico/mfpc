#!/usr/bin/env python3
"""
Distributed Transaction System
Main entry point for the CLI application
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cli.interface import cli

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)