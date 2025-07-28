#!/usr/bin/env python3
"""
Spotify API service for multi-user web application
Handles Spotify API interactions with proper token management
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class SpotifyService:
    """Service class for Spotify API interactions"""
    
    def __init__(self, access_token: str, refresh_token: str = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://api.spotify.com/v1"
        self.headers = {"Authorization": f"Bearer {access_token}"}
    
    def make_request(self, endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Spotify API with rate limiting"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers, params=params)
                elif method == "DELETE":
                    if endpoint == "/me/tracks" and data and "ids" in data:
                        delete_params = {"ids": ",".join(data["ids"])}
                        response = requests.delete(url, headers=self.headers, params=delete_params)
                    else:
                        response = requests.delete(url, headers=self.headers, json=data)
                elif method == "PUT":
                    response = requests.put(url, headers=self.headers, json=data)
                else:
                    response = requests.post(url, headers=self.headers, json=data)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    logging.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code == 200:
                    # For DELETE requests, empty response is success
                    if method == "DELETE" and not response.text.strip():
                        return {"success": True}
                    try:
                        return response.json()
                    except ValueError:
                        if method == "DELETE":
                            return {"success": True}
                        logging.error(f"Invalid JSON response: {response.text}")
                        return None
                
                elif response.status_code == 401:
                    logging.error("Token expired or invalid")
                    # TODO: Implement token refresh
                    return None
                
                else:
                    logging.error(f"API error {response.status_code}: {response.text}")
                    return None
                    
            except requests.RequestException as e:
                logging.error(f"Request failed: {e}")
                if attempt == 2:
                    return None
                time.sleep(1)
        
        return None
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get current user's profile"""
        return self.make_request("/me")
    
    def get_liked_songs(self, limit: int = 50) -> List[Dict]:
        """Get all user's liked songs"""
        songs = []
        offset = 0
        
        while True:
            params = {"limit": limit, "offset": offset}
            response = self.make_request("/me/tracks", params=params)
            
            if not response or not response.get('items'):
                break
            
            songs.extend(response['items'])
            
            if len(response['items']) < limit:
                break
            
            offset += limit
            logging.info(f"Fetched {len(songs)} songs so far...")
        
        return songs
    
    def get_recently_played(self, limit: int = 50) -> List[Dict]:
        """Get recently played tracks"""
        params = {"limit": limit}
        response = self.make_request("/me/player/recently-played", params=params)
        return response.get('items', []) if response else []
    
    def get_top_tracks(self, time_range: str = "short_term", limit: int = 50) -> List[Dict]:
        """Get user's top tracks"""
        params = {"time_range": time_range, "limit": limit}
        response = self.make_request("/me/top/tracks", params=params)
        return response.get('items', []) if response else []
    
    def remove_tracks_from_liked(self, track_ids: List[str]) -> bool:
        """Remove tracks from liked songs"""
        # Spotify API allows max 50 tracks per request
        batch_size = 50
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            data = {"ids": batch}
            
            response = self.make_request("/me/tracks", method="DELETE", data=data)
            if not response or not response.get('success'):
                logging.error(f"Failed to remove batch: {batch}")
                return False
            
            logging.info(f"Successfully removed {len(batch)} tracks")
        
        return True
    
    def analyze_and_cleanup(self, timeframe_months: int = 6) -> Dict:
        """Analyze liked songs and perform cleanup"""
        logging.info("Starting cleanup analysis...")
        
        # Get all liked songs
        liked_songs = self.get_liked_songs()
        total_liked = len(liked_songs)
        logging.info(f"Found {total_liked} liked songs")
        
        if not liked_songs:
            return {
                'total_liked_songs': 0,
                'songs_analyzed': 0,
                'songs_removed': 0,
                'songs_kept': 0,
                'removed_tracks': []
            }
        
        # Get recent activity
        recently_played = self.get_recently_played()
        short_term_top = self.get_top_tracks("short_term")
        medium_term_top = self.get_top_tracks("medium_term")
        
        # Create set of recently active track IDs
        active_track_ids = set()
        
        # Add recently played tracks
        for item in recently_played:
            active_track_ids.add(item['track']['id'])
        
        # Add top tracks
        for track in short_term_top + medium_term_top:
            active_track_ids.add(track['id'])
        
        logging.info(f"Found {len(active_track_ids)} tracks with recent activity")
        
        # Analyze liked songs
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=timeframe_months * 30)
        tracks_to_remove = []
        
        for item in liked_songs:
            track = item['track']
            added_at_str = item['added_at'].replace('Z', '+00:00')
            added_at = datetime.fromisoformat(added_at_str).replace(tzinfo=None)
            
            # Skip if track is in recent activity
            if track['id'] in active_track_ids:
                continue
            
            # Remove if added more than timeframe ago
            if added_at < cutoff_date:
                tracks_to_remove.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'added_at': added_at
                })
        
        logging.info(f"Identified {len(tracks_to_remove)} tracks for removal")
        
        # Remove tracks
        removed_count = 0
        if tracks_to_remove:
            track_ids = [track['id'] for track in tracks_to_remove]
            if self.remove_tracks_from_liked(track_ids):
                removed_count = len(tracks_to_remove)
        
        return {
            'total_liked_songs': total_liked,
            'songs_analyzed': len(liked_songs),
            'songs_removed': removed_count,
            'songs_kept': total_liked - removed_count,
            'recent_tracks_found': len(recently_played),
            'top_tracks_found': len(short_term_top) + len(medium_term_top),
            'removed_tracks': tracks_to_remove[:removed_count]
        }
    
    def preview_cleanup(self, timeframe_months: int = 6) -> Dict:
        """Preview what would be removed without actually removing"""
        logging.info("Generating cleanup preview...")
        
        # Get all liked songs
        liked_songs = self.get_liked_songs()
        total_liked = len(liked_songs)
        
        if not liked_songs:
            return {
                'total_liked_songs': 0,
                'tracks_to_remove': [],
                'tracks_to_keep': 0
            }
        
        # Get recent activity
        recently_played = self.get_recently_played()
        short_term_top = self.get_top_tracks("short_term")
        medium_term_top = self.get_top_tracks("medium_term")
        
        # Create set of recently active track IDs
        active_track_ids = set()
        
        for item in recently_played:
            active_track_ids.add(item['track']['id'])
        
        for track in short_term_top + medium_term_top:
            active_track_ids.add(track['id'])
        
        # Analyze liked songs
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=timeframe_months * 30)
        tracks_to_remove = []
        
        for item in liked_songs:
            track = item['track']
            added_at_str = item['added_at'].replace('Z', '+00:00')
            added_at = datetime.fromisoformat(added_at_str).replace(tzinfo=None)
            
            # Skip if track is in recent activity
            if track['id'] in active_track_ids:
                continue
            
            # Mark for removal if added more than timeframe ago
            if added_at < cutoff_date:
                tracks_to_remove.append({
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'added_at': added_at.isoformat(),
                    'preview_image': track['album']['images'][0]['url'] if track['album']['images'] else None
                })
        
        return {
            'total_liked_songs': total_liked,
            'tracks_to_remove': tracks_to_remove,
            'tracks_to_keep': total_liked - len(tracks_to_remove),
            'recent_activity_count': len(active_track_ids)
        }