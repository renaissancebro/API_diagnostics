
# API Diagnostics Middleware for Flask - Auto-generated
import json
import logging
import time
import traceback
import uuid
from datetime import datetime
from functools import wraps
from typing import Optional

from flask import Flask, request, g, jsonify, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_diagnostics")


class FlaskAPIDebugger:
    def __init__(self, app: Flask = None, log_requests: bool = True, log_responses: bool = True):
        self.log_requests = log_requests
        self.log_responses = log_responses
        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the Flask app with API debugging middleware"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.errorhandler(Exception)(self._handle_exception)

    def _before_request(self):
        """Process incoming request"""
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        short_id = correlation_id[:8]

        # Store in Flask's g object for access throughout request
        g.correlation_id = correlation_id
        g.short_id = short_id
        g.start_time = time.time()
        g.timestamp = datetime.utcnow().isoformat()

        # Log incoming request
        if self.log_requests:
            self._log_request(correlation_id, short_id)

    def _after_request(self, response: Response):
        """Process outgoing response"""
        if not hasattr(g, 'correlation_id'):
            return response

        # Add correlation ID to response headers
        response.headers['X-Correlation-ID'] = g.correlation_id

        # Log successful response
        if self.log_responses and hasattr(g, 'start_time'):
            process_time = time.time() - g.start_time
            self._log_response(g.correlation_id, g.short_id, response, process_time)

        return response

    def _handle_exception(self, error):
        """Handle all exceptions with enhanced logging and response"""
        if not hasattr(g, 'correlation_id'):
            g.correlation_id = str(uuid.uuid4())
            g.short_id = g.correlation_id[:8]
            g.start_time = time.time()
            g.timestamp = datetime.utcnow().isoformat()

        process_time = time.time() - g.start_time if hasattr(g, 'start_time') else 0

        # Determine error type and status code
        if hasattr(error, 'code') and error.code:
            # HTTP exceptions (400, 404, etc.)
            status_code = error.code
            message = getattr(error, 'description', str(error))
            self._log_http_exception(g.correlation_id, g.short_id, error, process_time)
        else:
            # Server errors (500)
            status_code = 500
            message = "Internal server error"
            self._log_server_error(g.correlation_id, g.short_id, error, process_time)

        # Create enhanced error response
        error_response = {
            "error": True,
            "message": message,
            "correlation_id": g.correlation_id,
            "timestamp": g.timestamp,
            "endpoint": request.path
        }

        response = jsonify(error_response)
        response.status_code = status_code
        response.headers['X-Correlation-ID'] = g.correlation_id
        return response

    def _log_request(self, correlation_id: str, short_id: str):
        """Log incoming request details"""
        try:
            # Get request body for POST/PUT requests
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    if request.is_json:
                        body = json.dumps(request.get_json())[:500]  # Limit size
                    elif request.data:
                        body = request.data.decode('utf-8')[:500]
                except:
                    body = "<unable to read body>"

            logger.info(f"🔍 [{short_id}] {request.method} {request.path}")
            logger.info(f"   Correlation ID: {correlation_id}")
            logger.info(f"   Timestamp: {g.timestamp}")
            logger.info(f"   Client IP: {request.remote_addr}")
            logger.info(f"   User-Agent: {request.headers.get('User-Agent', 'unknown')}")
            if body:
                logger.info(f"   Request Body: {body}")

        except Exception as e:
            logger.error(f"Error logging request: {e}")

    def _log_response(self, correlation_id: str, short_id: str, response: Response, process_time: float):
        """Log successful response"""
        logger.info(f"✅ [{short_id}] {response.status_code} ({process_time:.3f}s)")

    def _log_http_exception(self, correlation_id: str, short_id: str, error, process_time: float):
        """Log HTTP exceptions (400, 404, etc.)"""
        status_code = getattr(error, 'code', 'unknown')
        message = getattr(error, 'description', str(error))

        logger.error(f"❌ [{short_id}] {status_code} {message} ({process_time:.3f}s)")
        logger.error(f"   Correlation ID: {correlation_id}")
        logger.error(f"   Endpoint: {request.path}")
        logger.error(f"   Method: {request.method}")

    def _log_server_error(self, correlation_id: str, short_id: str, error, process_time: float):
        """Log unexpected server errors (500)"""
        logger.error(f"🚫 [{short_id}] SERVER ERROR: {str(error)} ({process_time:.3f}s)")
        logger.error(f"   Correlation ID: {correlation_id}")
        logger.error(f"   Endpoint: {request.path}")
        logger.error(f"   Method: {request.method}")
        logger.error(f"   Stack trace: {traceback.format_exc()}")


# Helper function to get correlation ID in route handlers
def get_correlation_id() -> Optional[str]:
    """Get the correlation ID from Flask's g object"""
    return getattr(g, 'correlation_id', None)


# Decorator for individual route debugging
def debug_route(f):
    """Decorator to add extra debugging to specific routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        correlation_id = get_correlation_id()
        short_id = correlation_id[:8] if correlation_id else 'unknown'

        logger.info(f"🎯 [{short_id}] Entering route: {f.__name__}")

        try:
            result = f(*args, **kwargs)
            logger.info(f"🎯 [{short_id}] Route completed: {f.__name__}")
            return result
        except Exception as e:
            logger.error(f"🎯 [{short_id}] Route error in {f.__name__}: {str(e)}")
            raise

    return decorated_function


# Usage example:
# from flask import Flask
# from api_middleware import FlaskAPIDebugger, get_correlation_id, debug_route
#
# app = Flask(__name__)
# debugger = FlaskAPIDebugger(app)
#
# @app.route('/users/<int:user_id>')
# @debug_route
# def get_user(user_id):
#     correlation_id = get_correlation_id()
#     logger.info(f"[{correlation_id[:8]}] Processing user {user_id}")
#     return {"user_id": user_id}
