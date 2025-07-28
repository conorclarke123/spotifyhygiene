# Spotify Hygiene - Multi-User Web Application

A comprehensive web application that helps users automatically clean up their Spotify liked songs by removing tracks they haven't listened to in a configurable timeframe. Built for public use with user accounts, session tracking, and a modern dashboard interface.

## Features

### Core Functionality
- **Configurable Timeframes**: Choose from 3, 6, 9, or 12-month cleanup periods
- **Smart Analysis**: Analyzes recent listening history and top tracks to protect active songs
- **Preview Mode**: See exactly which songs will be removed before confirming
- **Safe Removal**: Conservative approach that prioritizes keeping songs you might want

### User Management
- **Spotify OAuth Integration**: Secure authentication with Spotify accounts
- **User Profiles**: Personal dashboards with profile information and preferences
- **Session History**: Track all cleanup sessions with detailed statistics
- **Settings Management**: Customize default timeframes and preferences

### Web Interface
- **Modern Dashboard**: Professional Spotify-themed interface
- **Real-time Progress**: Live updates during cleanup operations
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Statistics Tracking**: View total cleanups, songs removed, and trends

## How It Works

1. **User Registration**: Sign in with your Spotify account through secure OAuth
2. **Dashboard Access**: View your personalized dashboard with cleanup history and statistics
3. **Configure Settings**: Set your preferred cleanup timeframe and preferences
4. **Preview Analysis**: See which songs would be removed without making changes
5. **Confirm & Clean**: Review the preview and execute cleanup with real-time progress
6. **Track Results**: View detailed session results and cleanup history

## Requirements

- Python 3.11+
- PostgreSQL database
- Spotify Developer App credentials (Client ID and Client Secret)
- Internet connection
- Modern web browser for users

## Setup

### For Replit (Online)

1. **Get Spotify API Credentials**:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Set redirect URI to: `https://your-replit-app-name.replit.app/callback`
   - Note your Client ID and Client Secret

2. **Set Environment Variables** in Replit Secrets tab

3. Dependencies are automatically installed

### For Local Machine

1. **Get Spotify API Credentials**:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app (or edit existing one)
   - Set redirect URI to: `http://localhost:5000/callback`
   - Note your Client ID and Client Secret

2. **Clone/Download the Code**:
   ```bash
   git clone [repository-url]
   # OR download the files manually
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install flask requests
   ```

4. **Set Environment Variables**:
   
   **On Windows (Command Prompt):**
   ```cmd
   set SPOTIFY_CLIENT_ID=your_client_id_here
   set SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```
   
   **On Windows (PowerShell):**
   ```powershell
   $env:SPOTIFY_CLIENT_ID="your_client_id_here"
   $env:SPOTIFY_CLIENT_SECRET="your_client_secret_here"
   ```
   
   **On macOS/Linux:**
   ```bash
   export SPOTIFY_CLIENT_ID="your_client_id_here"
   export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
   ```

5. **Run the Application**:
   ```bash
   python main.py
   ```

6. **Open Browser** to `http://localhost:5000`

## Usage

1. **Run the application**:
   ```bash
   python main.py
   ```

2. **Open your browser** to `http://localhost:5000`

3. **Click "Connect to Spotify"** and log in to your account

4. **Review the songs** that will be removed

5. **Confirm** to proceed with cleanup

## Architecture

### Backend Components
```
├── webapp.py            # Main application entry point
├── app.py               # Flask app configuration and database setup
├── models.py            # Database models (User, CleanupSession, RemovedTrack)
├── routes.py            # Web routes and authentication logic
├── spotify_service.py   # Spotify API client and cleanup logic
└── requirements/dependencies managed via pyproject.toml
```

### Frontend Assets
```
├── templates/
│   ├── webapp_index.html    # Landing page with features and login
│   ├── dashboard.html       # User dashboard with cleanup controls
│   ├── settings.html        # User preferences and account settings
│   └── callback.html        # OAuth callback success page
├── static/
│   └── webapp_style.css     # Modern Spotify-themed styling
```

### Database Schema
- **Users**: Spotify profile, preferences, OAuth tokens
- **Cleanup Sessions**: History and statistics of each cleanup
- **Removed Tracks**: Track details for potential undo functionality

## Technical Details

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with automatic schema management
- **Authentication**: Spotify OAuth 2.0 with secure token storage
- **API Integration**: RESTful client with rate limiting and error handling
- **Session Management**: Server-side sessions with CSRF protection

### Frontend Technology
- **Framework**: Bootstrap 5 with custom Spotify-themed CSS
- **Responsive Design**: Mobile-first approach with modern UI components
- **Real-time Updates**: AJAX-powered dashboard with progress tracking
- **Accessibility**: WCAG compliant interface elements

### Security Features
- **Token Management**: Encrypted OAuth tokens with automatic refresh
- **State Validation**: CSRF protection for all authentication flows
- **Input Sanitization**: SQL injection prevention and XSS protection
- **Environment Adaptive**: Auto-detection of deployment environment

## Safety Features

- **6-Month Buffer**: Conservative timeframe to avoid removing recently enjoyed songs
- **Multiple Data Sources**: Checks recently played tracks AND top tracks
- **User Confirmation**: Always shows what will be removed before taking action
- **Detailed Logging**: Clear feedback about what's happening during cleanup

## Recent Updates

### Version 2.0 - Multi-User Web Application (Latest)
- Complete architectural transformation from single-user to multi-user web app
- Added PostgreSQL database with user accounts and session tracking
- Built modern dashboard interface with real-time cleanup progress
- Implemented user settings, preferences, and cleanup history
- Added preview functionality to see songs before removal
- Created responsive Spotify-themed web design

### Version 1.0 - Single-User Desktop Tool
- Fixed success detection for track removal (HTTP 200 empty responses)
- Improved error handling and progress reporting
- Added comprehensive analysis of listening history
- Implemented conservative 6-month timeframe

## Deployment

### Local Development
1. Set up PostgreSQL database
2. Configure environment variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost/spotify_hygiene
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python webapp.py`

### Production Deployment
- **Replit**: Ready for one-click deployment on Replit platform
- **Heroku**: Compatible with PostgreSQL add-on
- **Digital Ocean**: App Platform ready with database
- **AWS/GCP**: Supports containerized deployment

### Environment Variables Required
- `DATABASE_URL`: PostgreSQL connection string
- `SPOTIFY_CLIENT_ID`: From Spotify Developer Dashboard
- `SPOTIFY_CLIENT_SECRET`: From Spotify Developer Dashboard

## Limitations

- Subject to Spotify API rate limits (handled automatically)
- Requires stable internet connection during cleanup process
- Preview mode requires fetching user's complete library (can take time for large collections)

## Troubleshooting

- **Authentication Issues**: Ensure redirect URI is set correctly in Spotify app settings
- **Missing Credentials**: Verify environment variables are set properly
- **API Errors**: Check your internet connection and Spotify service status
- **Empty Results**: Make sure you have liked songs and recent listening history

## Privacy & Security

### Data Storage
- **User Profiles**: Basic Spotify profile information (name, email, profile image)
- **Session History**: Cleanup statistics and timestamps (no song details stored)
- **OAuth Tokens**: Securely encrypted and stored for seamless access
- **No Song Data**: Individual song information is never permanently stored

### Security Measures
- **HTTPS Only**: All communications encrypted in transit
- **OAuth 2.0**: Industry-standard authentication with Spotify
- **CSRF Protection**: State validation for all authentication flows
- **Database Security**: Encrypted token storage with automatic cleanup

### Data Retention
- **User Choice**: Account deletion removes all associated data
- **Session Logs**: Cleanup history retained for user convenience
- **Token Refresh**: Automatic token management with secure refresh cycle

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper testing
4. Test with your own Spotify account
5. Submit a pull request with description of changes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Comprehensive setup guides in the repository
- **Community**: Join discussions about Spotify library management