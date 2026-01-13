# Flask Migration Status

## Summary
Attempted to fix Issue #16 by migrating from `http.server.HTTPServer` to Flask. Flask was chosen because BaseHTTPRequestHandler doesn't dispatch requests properly when bundled with PyInstaller.

## What Works
- ✅ Flask installs and imports correctly
- ✅ Flask routes register (4 routes visible in app.url_map)
- ✅ Flask server starts and listens on port 5000
- ✅ Minimal Flask app works perfectly in isolation

## What Doesn't Work
- ❌ Flask returns 500 Internal Server Error for ALL routes
- ❌ Route handler functions never execute (no print statements appear)
- ❌ Error handlers don't trigger (suggests lower-level Werkzeug issue)
- ❌ No traceback or error messages in console output

## Investigation
1. Tested minimal Flask app → works perfectly
2. Moved FeedbackDB/LogCapture initialization from module level to run_server() → no change
3. Added extensive debug logging → routes register but never execute
4. Added Flask error handler → never triggers
5. Tested with debug=True → no additional output

## Hypothesis
Something in app.py's module-level code or class definitions is interfering with Flask's request handling at the Werkzeug WSGI layer. The SyncHandler class (4800+ lines) might be conflicting even though it's not instantiated.

## Next Steps
1. **Option A**: Try alternative WSGI server (waitress, cherrypy)
2. **Option B**: Extract Flask routes to separate file/module
3. **Option C**: Simplify app.py by removing SyncHandler class entirely and rewrite ALL routes as Flask
4. **Option D**: Stick with BaseHTTPRequestHandler but investigate why it doesn't work in PyInstaller

## Files Modified
- `app.py`: Added Flask imports, created basic routes, updated run_server()
- `requirements.txt`: Added flask==3.0.0

## Time Investment
- Approximately 2 hours debugging Flask routing issue
- Multiple rebuild cycles attempted
- Confirmed issue is NOT with PyInstaller bundling (routes register correctly)

## Recommendation
Given time constraints, recommend Option A (try waitress or cheroot) as quickest path forward. These are production-ready WSGI servers designed to work with PyInstaller.
