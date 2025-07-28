#!/usr/bin/env python3
"""
Multi-user Spotify Cleaner Web Application
Flask app with user authentication and database storage
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from datetime import datetime
import secrets
import requests
import urllib.parse
import base64
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(32))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize database
db = SQLAlchemy(app, model_class=Base)

# Spotify OAuth settings
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_SCOPE = "user-library-read user-library-modify user-read-recently-played user-top-read"

# Determine redirect URI based on environment
replit_domains = os.getenv("REPLIT_DOMAINS")
replit_dev_domain = os.getenv("REPLIT_DEV_DOMAIN")

if replit_domains:
    # Production deployment - use the primary domain
    domain = replit_domains.split(",")[0].strip()
    REDIRECT_URI = f"https://{domain}/callback"
elif replit_dev_domain:
    # Development on Replit - use the dev domain
    REDIRECT_URI = f"https://{replit_dev_domain}/callback"
else:
    # Local development fallback
    REDIRECT_URI = "http://localhost:5000/callback"

# Log the redirect URI for debugging
print(f"Using redirect URI: {REDIRECT_URI}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)