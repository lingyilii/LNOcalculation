#!/usr/bin/env python3
"""
setup.py — installs the LNOcalculation command so you can run it from anywhere.

Usage:
    python setup.py install      # installs as 'LNOcalculation' command
    python setup.py uninstall    # removes the command
"""

import sys
import os
import shutil
import stat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY = os.path.join(SCRIPT_DIR, "LNOcalculation.py")


def find_scripts_dir():
    """Find the conda/python bin or Scripts directory."""
    return os.path.dirname(sys.executable)


def install():
    scripts_dir = find_scripts_dir()

    if sys.platform == "win32":
        # Create a .bat wrapper
        bat_path = os.path.join(scripts_dir, "LNOcalculation.bat")
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n"{sys.executable}" "{ENTRY}" %*\n')
        print(f"[OK] Installed: {bat_path}")
        print(f"     Command:   LNOcalculation")
    else:
        # Create a shell wrapper
        sh_path = os.path.join(scripts_dir, "LNOcalculation")
        with open(sh_path, "w") as f:
            f.write(f'#!/bin/sh\nexec "{sys.executable}" "{ENTRY}" "$@"\n')
        os.chmod(sh_path, os.stat(sh_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[OK] Installed: {sh_path}")
        print(f"     Command:   LNOcalculation")

    print()
    print("You can now open the GUI with:")
    print("    LNOcalculation")
    print()
    print("Or from Python:")
    print("    python LNOcalculation.py")


def uninstall():
    scripts_dir = find_scripts_dir()
    if sys.platform == "win32":
        target = os.path.join(scripts_dir, "LNOcalculation.bat")
    else:
        target = os.path.join(scripts_dir, "LNOcalculation")

    if os.path.exists(target):
        os.remove(target)
        print(f"[OK] Removed: {target}")
    else:
        print(f"[!] Not found: {target}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()
