# API Diagnostics Integration Instructions

## Backend Setup (Flask)
1. Copy `api_middleware.py` to your project directory
2. Import and add the middleware to your app:
   ```python
   from api_middleware import FlaskAPIDebugger
   debugger = FlaskAPIDebugger(app)
   ```
   Or for more control:
   ```python
   from api_middleware import FlaskAPIDebugger
   debugger = FlaskAPIDebugger()
   debugger.init_app(app)
   ```
3. Restart your server

## Usage
1. Run `api-diagnostics start` to enable monitoring
2. Make API calls from your frontend
3. Check browser console for correlation IDs
4. Search backend logs with `api-diagnostics search <correlation-id>`