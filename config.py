"""
Configuration — loads Google OAuth credentials from .env

You need to create a project in Google Cloud Console:
  1. Go to console.cloud.google.com
  2. Create OAuth 2.0 credentials (Web Application)
  3. Set redirect URI to: http://localhost:8000/auth/callback
  4. Copy client_id and client_secret into .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
