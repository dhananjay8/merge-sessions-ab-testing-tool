#!/usr/bin/env python3
"""
Initialization script for A/B testing environment.
Checks dependencies and prepares experiment setup.
"""

import sys
import platform
import subprocess


def check_python_version():
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required.")
        sys.exit(1)
    print("✅ Python version OK")


def check_git():
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE)
        print("✅ Git is installed")
    except Exception:
        print("❌ Git is not installed")
        sys.exit(1)


def main():
    print("🚀 Initializing A/B Testing Environment")
    print(f"Platform: {platform.system()}")

    check_python_version()
    check_git()

    print("✅ Environment setup complete")


if __name__ == "__main__":
    main()

