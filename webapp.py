#!/usr/bin/env python3
"""
Multi-user Spotify Hygiene Web Application
Complete Flask app with all routes and models
"""

from app import app, db
import models
import routes

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)