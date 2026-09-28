#!/usr/bin/env python3
"""Launcher: install deps then start the Hosa app. Usage: python run.py"""
import os
import subprocess
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hosa", "app")

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], cwd=APP_DIR)
subprocess.check_call([sys.executable, "server.py"], cwd=APP_DIR)
