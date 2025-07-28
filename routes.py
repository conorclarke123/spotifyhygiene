#!/usr/bin/env python3
"""
Web routes for multi-user Spotify Cleaner
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_SCOPE, REDIRECT_URI
from models import User, CleanupSession, RemovedTrack
from spotify_service import SpotifyService
import secrets
import urllib.parse
import requests
import base64
from datetime import datetime, timedelta
import logging

@app.route('/')
def index():
    """Main landing page"""
    user_id = session.get('user_id')
    user = None
    recent_sessions = []
    
    if user_id:
        user = User.query.get(user_id)
        if user:
            recent_sessions = CleanupSession.query.filter_by(
                user_id=user_id
            ).order_by(CleanupSession.started_at.desc()).limit(5).all()
    
    return render_template('webapp_index.html', user=user, recent_sessions=recent_sessions)

@app.route('/login')
def login():
    """Initiate Spotify OAuth login"""
    # Generate state parameter for security
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    auth_params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SPOTIFY_SCOPE,
        'state': state,
        'show_dialog': 'true'
    }
    
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(auth_params)
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handle Spotify OAuth callback"""
    error = request.args.get('error')
    if error:
        flash(f"Authorization failed: {error}", 'error')
        return redirect(url_for('index'))
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state parameter
    if state != session.get('oauth_state'):
        flash("Invalid state parameter. Please try again.", 'error')
        return redirect(url_for('index'))
    
    if not code:
        flash("No authorization code received", 'error')
        return redirect(url_for('index'))
    
    # Exchange code for tokens
    try:
        token_data = exchange_code_for_tokens(code)
        user_info = get_spotify_user_info(token_data['access_token'])
        
        # Create or update user
        user = User.query.get(user_info['id'])
        if not user:
            user = User(
                id=user_info['id'],
                display_name=user_info.get('display_name'),
                email=user_info.get('email'),
                profile_image_url=user_info.get('images', [{}])[0].get('url') if user_info.get('images') else None
            )
            db.session.add(user)
        
        # Update tokens and user info
        user.access_token = token_data['access_token']
        user.refresh_token = token_data.get('refresh_token')
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        user.last_login = datetime.utcnow()
        user.display_name = user_info.get('display_name')
        user.email = user_info.get('email')
        
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        flash(f"Welcome back, {user.display_name}!", 'success')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logging.error(f"OAuth callback error: {e}")
        flash("Authentication failed. Please try again.", 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    # Get user's cleanup history
    cleanup_sessions = CleanupSession.query.filter_by(
        user_id=user_id
    ).order_by(CleanupSession.started_at.desc()).limit(10).all()
    
    # Calculate stats
    total_cleanups = CleanupSession.query.filter_by(user_id=user_id, status='completed').count()
    total_removed = db.session.query(db.func.sum(CleanupSession.songs_removed)).filter_by(
        user_id=user_id, status='completed'
    ).scalar() or 0
    
    return render_template('dashboard.html', 
                         user=user, 
                         cleanup_sessions=cleanup_sessions,
                         total_cleanups=total_cleanups,
                         total_removed=total_removed)

@app.route('/cleanup/start', methods=['POST'])
def start_cleanup():
    """Start a new cleanup session"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get timeframe from request
    timeframe_months = request.json.get('timeframe_months', user.cleanup_timeframe_months)
    
    try:
        # Create cleanup session
        session_record = CleanupSession(
            user_id=user_id,
            timeframe_months=timeframe_months,
            status='started'
        )
        db.session.add(session_record)
        db.session.commit()
        
        # Initialize Spotify service
        spotify_service = SpotifyService(user.access_token, user.refresh_token)
        
        # Start the cleanup process
        result = spotify_service.analyze_and_cleanup(timeframe_months)
        
        # Update session with results
        session_record.completed_at = datetime.utcnow()
        session_record.status = 'completed'
        session_record.total_liked_songs = result['total_liked_songs']
        session_record.songs_analyzed = result['songs_analyzed']
        session_record.songs_removed = result['songs_removed']
        session_record.songs_kept = result['songs_kept']
        session_record.recent_tracks_found = result.get('recent_tracks_found', 0)
        session_record.top_tracks_found = result.get('top_tracks_found', 0)
        
        # Save removed tracks for potential undo
        for track in result.get('removed_tracks', []):
            removed_track = RemovedTrack(
                cleanup_session_id=session_record.id,
                spotify_track_id=track['id'],
                track_name=track['name'],
                artist_name=track['artist'],
                album_name=track.get('album'),
                last_played_date=track.get('last_played'),
                added_to_library_date=track.get('added_at')
            )
            db.session.add(removed_track)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_record.id,
            'result': result
        })
        
    except Exception as e:
        logging.error(f"Cleanup error: {e}")
        if 'session_record' in locals():
            session_record.status = 'failed'
            session_record.error_message = str(e)
            session_record.completed_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'error': str(e)}), 500

@app.route('/cleanup/preview', methods=['POST'])
def preview_cleanup():
    """Preview what would be removed without actually removing"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    timeframe_months = request.json.get('timeframe_months', user.cleanup_timeframe_months)
    
    try:
        spotify_service = SpotifyService(user.access_token, user.refresh_token)
        preview = spotify_service.preview_cleanup(timeframe_months)
        return jsonify(preview)
        
    except Exception as e:
        logging.error(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """User settings page"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Update user preferences
        user.cleanup_timeframe_months = int(request.form.get('cleanup_timeframe_months', 6))
        user.auto_cleanup_enabled = bool(request.form.get('auto_cleanup_enabled'))
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', user=user)

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

def exchange_code_for_tokens(code):
    """Exchange authorization code for access tokens"""
    token_url = "https://accounts.spotify.com/api/token"
    
    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    
    return response.json()

def get_spotify_user_info(access_token):
    """Get user information from Spotify"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    response.raise_for_status()
    return response.json()