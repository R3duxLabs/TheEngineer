# Fix Port Conflicts and Add Render Deployment

## Summary
- Fixed port conflicts between FastAPI and the main web server
- Implemented proper global variable handling using an AppState class
- Added deployment configuration for Render (render.yaml and start.sh)
- Updated documentation with deployment instructions

## Changes

### Port Configuration
- Changed FastAPI port from 8080 to 8000
- Changed main web server port from 8080 to 8888
- Updated workflow configuration in .replit file

### Global Variable Fixes
- Fixed global variable declaration in main.py using AppState class
- Removed redundant global declarations
- Fixed domain switching functionality

### Deployment Setup
- Added render.yaml for Render configuration
- Created start.sh script for deployment
- Added Procfile for web service configuration
- Updated README with deployment instructions

### Documentation
- Added troubleshooting section for port conflicts
- Documented environment variables
- Added Render deployment guide

## Testing

To test these changes:
1. Run the application with `python main.py --web`
2. Verify the web server runs on port 8888
3. Check that the FastAPI server runs on port 8000
4. Test agent switching functionality
5. Deploy to Render using the provided configuration

## Notes
- Port configuration can be overridden with environment variables
- Default ports are now 8888 (web) and 8000 (API)