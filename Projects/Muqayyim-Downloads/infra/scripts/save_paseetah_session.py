"""
Run this once to save your Paseetah session after manual login.

Usage:
    cd Projects/Muqayyim-Downloads
    source .venv/bin/activate
    python infra/scripts/save_paseetah_session.py

A browser window will open. Tick the reCAPTCHA, click Login.
The session will be saved to .paseetah_session.json automatically.
"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from dotenv import load_dotenv
load_dotenv()
from extractors.paseetah_extractor import save_session_interactively
asyncio.run(save_session_interactively())
