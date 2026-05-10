#!/usr/bin/env python3
"""
LNO Calculator - Entry Point
Run directly: python LNOcalculation.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lno_gui import main

if __name__ == "__main__":
    main()
