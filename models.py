#!/usr/bin/env python3
"""
Database models for multi-user Spotify Cleaner
"""

from datetime import datetime
from app import db

class User(db.Model):
    """User model for storing Spotify user information"""
    __tablename__ = 'users'
    
    id = db.Column(db.String, primary_key=True)  # Spotify user ID
    display_name = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # OAuth tokens (encrypted in production)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # User preferences
    cleanup_timeframe_months = db.Column(db.Integer, default=6)
    auto_cleanup_enabled = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    cleanup_sessions = db.relationship('CleanupSession', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.display_name} ({self.id})>'

class CleanupSession(db.Model):
    """Model for tracking cleanup sessions and results"""
    __tablename__ = 'cleanup_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    # Session details
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String, default='started')  # started, completed, failed
    
    # Results
    total_liked_songs = db.Column(db.Integer, nullable=True)
    songs_analyzed = db.Column(db.Integer, nullable=True)
    songs_removed = db.Column(db.Integer, nullable=True)
    songs_kept = db.Column(db.Integer, nullable=True)
    
    # Analysis details
    timeframe_months = db.Column(db.Integer, nullable=True)
    recent_tracks_found = db.Column(db.Integer, nullable=True)
    top_tracks_found = db.Column(db.Integer, nullable=True)
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<CleanupSession {self.id} for {self.user_id}>'

class RemovedTrack(db.Model):
    """Model for tracking removed tracks (for potential undo functionality)"""
    __tablename__ = 'removed_tracks'
    
    id = db.Column(db.Integer, primary_key=True)
    cleanup_session_id = db.Column(db.Integer, db.ForeignKey('cleanup_sessions.id'), nullable=False)
    
    # Track information
    spotify_track_id = db.Column(db.String, nullable=False)
    track_name = db.Column(db.String, nullable=False)
    artist_name = db.Column(db.String, nullable=False)
    album_name = db.Column(db.String, nullable=True)
    
    # Removal details
    removed_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_played_date = db.Column(db.DateTime, nullable=True)
    added_to_library_date = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    cleanup_session = db.relationship('CleanupSession', backref='removed_tracks')
    
    def __repr__(self):
        return f'<RemovedTrack {self.track_name} by {self.artist_name}>'