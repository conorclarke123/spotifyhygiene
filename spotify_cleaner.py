#!/usr/bin/env python3
"""
Spotify Liked Songs Cleaner
Core functionality for analyzing and removing old liked songs
"""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class SpotifyLikedSongsCleaner:
    """Main class for cleaning Spotify liked songs based on listening history"""
    
    def __init__(self, client_id: str, client_secret: str, access_token: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://api.spotify.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.six_months_ago = datetime.now() - timedelta(days=180)
        
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        token_url = "https://accounts.spotify.com/api/token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                print("🔄 Access token refreshed successfully")
                return True
            else:
                print(f"❌ Failed to refresh token: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error refreshing token: {str(e)}")
            return False
    
    def make_spotify_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make a request to Spotify API with rate limiting and token refresh"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):  # Retry up to 3 times
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers)
                elif method == "DELETE":
                    # For DELETE requests to /me/tracks, use query parameters instead of JSON body
                    if endpoint == "/me/tracks" and data and "ids" in data:
                        params = {"ids": ",".join(data["ids"])}
                        response = requests.delete(url, headers=self.headers, params=params)
                    else:
                        response = requests.delete(url, headers=self.headers, json=data)
                elif method == "PUT":
                    response = requests.put(url, headers=self.headers, json=data)
                else:
                    response = requests.post(url, headers=self.headers, json=data)
                
                if response.status_code == 401:  # Unauthorized
                    print("🔄 Token expired, refreshing...")
                    if self.refresh_access_token():
                        continue  # Retry with new token
                    else:
                        return None
                
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 1))
                    print(f"⏳ Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code == 200:
                    # For DELETE requests, empty response is success
                    if method == "DELETE" and not response.text.strip():
                        return {"success": True}
                    try:
                        return response.json()
                    except ValueError:
                        # Empty response on successful DELETE
                        if method == "DELETE":
                            return {"success": True}
                        print(f"❌ Invalid JSON response: {response.text}")
                        return None
                
                elif response.status_code == 204:  # No content (successful DELETE)
                    return {"success": True}
                
                else:
                    print(f"❌ API request failed: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                print(f"❌ Request error (attempt {attempt + 1}): {str(e)}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None
        
        return None
    
    def get_user_profile(self) -> Optional[Dict]:
        """Get current user's profile"""
        return self.make_spotify_request("/me")
    
    def get_liked_songs(self) -> List[Dict]:
        """Get all liked songs from user's library"""
        print("📋 Fetching liked songs...")
        liked_songs = []
        offset = 0
        limit = 50
        
        while True:
            endpoint = f"/me/tracks?limit={limit}&offset={offset}"
            response = self.make_spotify_request(endpoint)
            
            if not response:
                break
            
            items = response.get("items", [])
            if not items:
                break
            
            liked_songs.extend(items)
            print(f"   Fetched {len(liked_songs)} songs so far...")
            
            if len(items) < limit:
                break
            
            offset += limit
            time.sleep(0.1)  # Small delay to be respectful
        
        print(f"✅ Found {len(liked_songs)} liked songs total")
        return liked_songs
    
    def get_recently_played_tracks(self) -> List[Dict]:
        """Get recently played tracks (last 50)"""
        print("🎵 Fetching recently played tracks...")
        endpoint = "/me/player/recently-played?limit=50"
        response = self.make_spotify_request(endpoint)
        
        if response:
            tracks = response.get("items", [])
            print(f"✅ Found {len(tracks)} recently played tracks")
            return tracks
        
        return []
    
    def get_top_tracks(self, time_range: str = "medium_term") -> List[Dict]:
        """Get user's top tracks (medium_term = ~6 months)"""
        print(f"🔥 Fetching top tracks ({time_range})...")
        endpoint = f"/me/top/tracks?limit=50&time_range={time_range}"
        response = self.make_spotify_request(endpoint)
        
        if response:
            tracks = response.get("items", [])
            print(f"✅ Found {len(tracks)} top tracks")
            return tracks
        
        return []
    
    def analyze_listening_activity(self) -> set:
        """Analyze recent listening activity and return set of recently played track IDs"""
        print("\n🔍 Analyzing recent listening activity...")
        recently_played_ids = set()
        
        # Get recently played tracks
        recent_tracks = self.get_recently_played_tracks()
        for item in recent_tracks:
            track = item.get("track", {})
            if track.get("id"):
                recently_played_ids.add(track["id"])
        
        # Get top tracks from different time ranges
        for time_range in ["short_term", "medium_term"]:  # 4 weeks, ~6 months
            top_tracks = self.get_top_tracks(time_range)
            for track in top_tracks:
                if track.get("id"):
                    recently_played_ids.add(track["id"])
        
        print(f"✅ Identified {len(recently_played_ids)} tracks with recent activity")
        return recently_played_ids
    
    def remove_track_from_liked(self, track_id: str) -> bool:
        """Remove a track from liked songs"""
        endpoint = "/me/tracks"
        data = {"ids": [track_id]}
        
        response = self.make_spotify_request(endpoint, method="DELETE", data=data)
        return response is not None and response.get("success", False)
    
    def clean_liked_songs(self):
        """Main function to clean liked songs"""
        print("\n🧹 Starting cleanup process...")
        
        # Get user profile
        user = self.get_user_profile()
        if not user:
            print("❌ Failed to get user profile")
            return
        
        print(f"👤 Logged in as: {user.get('display_name', 'Unknown')}")
        
        # Get all liked songs
        liked_songs = self.get_liked_songs()
        if not liked_songs:
            print("❌ No liked songs found or failed to fetch")
            return
        
        # Analyze recent listening activity
        recently_played_ids = self.analyze_listening_activity()
        
        # Find songs not played recently
        print(f"\n📊 Analyzing {len(liked_songs)} liked songs...")
        songs_to_remove = []
        
        for item in liked_songs:
            track = item.get("track", {})
            track_id = track.get("id")
            track_name = track.get("name", "Unknown")
            artists = ", ".join([artist.get("name", "Unknown") for artist in track.get("artists", [])])
            added_at = item.get("added_at", "")
            
            # Check if track was recently played
            if track_id not in recently_played_ids:
                # Check if the song was added more than 6 months ago
                try:
                    added_date = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                    if added_date.replace(tzinfo=None) < self.six_months_ago:
                        songs_to_remove.append({
                            "id": track_id,
                            "name": track_name,
                            "artists": artists,
                            "added_at": added_at
                        })
                except:
                    # If we can't parse the date, include it for removal
                    songs_to_remove.append({
                        "id": track_id,
                        "name": track_name,
                        "artists": artists,
                        "added_at": added_at
                    })
        
        print(f"\n📋 Found {len(songs_to_remove)} songs to potentially remove:")
        print("   (Not played recently AND added more than 6 months ago)")
        
        if not songs_to_remove:
            print("🎉 No songs need to be removed! Your liked songs are all recent.")
            return
        
        # Show preview of songs to be removed
        print(f"\n📝 Songs that will be removed:")
        print("-" * 80)
        for i, song in enumerate(songs_to_remove[:10], 1):  # Show first 10
            print(f"{i:2d}. {song['name']} - {song['artists']}")
        
        if len(songs_to_remove) > 10:
            print(f"    ... and {len(songs_to_remove) - 10} more songs")
        
        # Ask for confirmation
        print(f"\n⚠️  This will remove {len(songs_to_remove)} songs from your liked songs.")
        confirmation = input("Do you want to proceed? (yes/no): ").lower().strip()
        
        if confirmation not in ["yes", "y"]:
            print("❌ Operation cancelled by user.")
            return
        
        # Remove songs
        print(f"\n🗑️  Removing {len(songs_to_remove)} songs...")
        removed_count = 0
        failed_count = 0
        
        for i, song in enumerate(songs_to_remove, 1):
            print(f"   Removing {i}/{len(songs_to_remove)}: {song['name']} - {song['artists']}")
            
            if self.remove_track_from_liked(song["id"]):
                removed_count += 1
            else:
                failed_count += 1
                print(f"   ❌ Failed to remove: {song['name']}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        # Summary
        print(f"\n📊 Cleanup Summary:")
        print(f"   ✅ Successfully removed: {removed_count} songs")
        if failed_count > 0:
            print(f"   ❌ Failed to remove: {failed_count} songs")
        print(f"   📋 Total liked songs processed: {len(liked_songs)}")
        print(f"   💾 Remaining liked songs: {len(liked_songs) - removed_count}")
