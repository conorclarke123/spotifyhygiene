# Spotify Liked Songs Cleaner

## Overview

A multi-user web application that helps users clean up their Spotify liked songs by removing tracks they haven't listened to in a configurable timeframe (3-12 months). The application has evolved from a single-user desktop tool to a full-featured web application with user accounts, database storage, session tracking, and a modern dashboard interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Interface**: Flask-based web server serving HTML templates with Bootstrap CSS framework
- **Authentication Flow**: Browser-based OAuth2 flow with callback handling
- **User Experience**: Simple, Spotify-themed interface with progress indicators and confirmation dialogs

### Backend Architecture
- **Main Application**: Python CLI application (`main.py`) that orchestrates the cleaning process
- **Authentication Server**: Flask web server (`auth_server.py`) handling OAuth2 callbacks
- **Core Logic**: Spotify API client (`spotify_cleaner.py`) for data analysis and song removal
- **Threading**: Multi-threaded approach separating web server from main application logic

### Authentication Flow
- **OAuth2 Implementation**: Uses Spotify's authorization code flow
- **Token Management**: Handles both access tokens and refresh tokens
- **Environment Detection**: Automatically adapts redirect URIs for Replit vs local development
- **Security**: Uses secure state parameters and token-based authentication

## Key Components

### 1. Main Application (`main.py`)
- **Purpose**: Entry point and orchestration of the cleaning process
- **Responsibilities**: 
  - Environment validation
  - Server startup
  - User interaction and confirmation
  - Process coordination

### 2. Authentication Server (`auth_server.py`)
- **Purpose**: Handles Spotify OAuth2 authentication flow
- **Key Features**:
  - Dynamic redirect URI configuration (Replit vs localhost)
  - State parameter validation for security
  - Token exchange and management
  - Web-based callback handling

### 3. Spotify Cleaner (`spotify_cleaner.py`)
- **Purpose**: Core business logic for analyzing and cleaning liked songs
- **Key Features**:
  - Spotify Web API integration
  - Token refresh mechanism
  - Listening history analysis (6-month window)
  - Safe song removal with user confirmation

### 4. Web Templates
- **Purpose**: User interface for authentication flow
- **Design**: Spotify-themed Bootstrap interface
- **Features**: Responsive design, auto-close functionality, error handling

## Data Flow

1. **Initialization**: Application starts and validates environment variables
2. **Authentication**: 
   - Flask server starts on background thread
   - Browser opens to Spotify authorization URL
   - User grants permissions
   - Callback handler exchanges code for tokens
3. **Analysis**:
   - Fetch user's liked songs (paginated)
   - Retrieve recent listening history
   - Identify songs not played in last 6 months
4. **Confirmation**: Present removal candidates to user for approval
5. **Cleanup**: Remove confirmed songs via Spotify API
6. **Completion**: Report results and cleanup

## External Dependencies

### Core Dependencies
- **Flask**: Web server for OAuth callback handling
- **Requests**: HTTP client for Spotify API communication
- **Python Standard Library**: Threading, datetime, urllib, secrets

### Spotify Web API Integration
- **Endpoints Used**:
  - `/me/tracks` - Liked songs management
  - `/me/player/recently-played` - Recent listening history
  - `/me/top/tracks` - Top tracks analysis
- **Scopes Required**:
  - `user-library-read` - Read liked songs
  - `user-library-modify` - Remove liked songs
  - `user-read-recently-played` - Access listening history
  - `user-top-read` - Access top tracks

### Frontend Assets
- **Bootstrap 5.1.3**: CSS framework via CDN
- **Font Awesome 6.0.0**: Icons via CDN
- **Custom CSS**: Spotify-themed styling

## Deployment Strategy

### Environment Configuration
- **Development**: Uses `localhost:5000` for OAuth callbacks
- **Replit Production**: Automatically detects and uses Replit domain from `REPLIT_DOMAINS` environment variable
- **Credentials**: Requires `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` environment variables

### Runtime Architecture
- **Multi-threaded**: Web server runs on daemon thread
- **Port Management**: Uses Flask's default port (5000) with auto-discovery
- **Process Lifecycle**: Main thread handles user interaction while web server handles callbacks

### Security Considerations
- **State Parameter**: Prevents CSRF attacks in OAuth flow
- **Token Security**: Access tokens stored in memory only
- **Scope Limitation**: Requests minimal required permissions
- **Local Server**: Authentication server only runs during auth flow

### Error Handling
- **Token Refresh**: Automatic refresh token handling
- **API Rate Limits**: Built-in retry mechanisms
- **User Feedback**: Clear error messages and progress indicators
- **Graceful Degradation**: Handles missing environment variables and API failures