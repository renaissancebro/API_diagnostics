"""
Code Templates for Framework Integration
Contains code snippets that get injected into projects
"""

FRONTEND_TEMPLATES = {
    'react': {
        'interceptor': '''
// API Diagnostics Interceptor - Auto-generated
// This code automatically adds correlation IDs to all fetch() calls

(function() {
  'use strict';

  // Generate UUID4 (no external dependencies)
  function generateCorrelationId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  // Format correlation ID for display (first 8 chars)
  function formatCorrelationId(id) {
    return id.substring(0, 8);
  }

  // Enhanced console logging
  function logRequest(correlationId, url, method, timestamp) {
    console.group(`🔍 [${formatCorrelationId(correlationId)}] ${method} ${url}`);
    console.log('Full Correlation ID:', correlationId);
    console.log('Timestamp:', timestamp);
    console.log('Method:', method);
    console.log('URL:', url);
    console.groupEnd();
  }

  function logError(correlationId, url, status, statusText, timestamp) {
    console.group(`❌ [${formatCorrelationId(correlationId)}] ${status} ${statusText}`);
    console.error('Full Correlation ID:', correlationId);
    console.error('URL:', url);
    console.error('Status:', status, statusText);
    console.error('Timestamp:', timestamp);
    console.error('🔧 Search backend logs with: api-diagnostics search', correlationId);
    console.groupEnd();
  }

  function logNetworkError(correlationId, url, error, timestamp) {
    console.group(`🚫 [${formatCorrelationId(correlationId)}] Network Error`);
    console.error('Full Correlation ID:', correlationId);
    console.error('URL:', url);
    console.error('Error:', error.message);
    console.error('Timestamp:', timestamp);
    console.error('🔧 Search backend logs with: api-diagnostics search', correlationId);
    console.groupEnd();
  }

  // Store original fetch
  const originalFetch = window.fetch;

  // Override fetch with correlation tracking
  window.fetch = async function(url, options = {}) {
    const correlationId = generateCorrelationId();
    const timestamp = new Date().toISOString();
    const method = options.method || 'GET';

    // Add correlation ID to headers
    const headers = {
      ...options.headers,
      'X-Correlation-ID': correlationId
    };

    // Log outgoing request
    logRequest(correlationId, url, method, timestamp);

    try {
      const response = await originalFetch(url, { ...options, headers });

      if (!response.ok) {
        logError(correlationId, url, response.status, response.statusText, timestamp);
      } else {
        console.log(`✅ [${formatCorrelationId(correlationId)}] ${response.status} ${response.statusText}`);
      }

      return response;
    } catch (error) {
      logNetworkError(correlationId, url, error, timestamp);
      throw error;
    }
  };

  console.log('🔍 API Diagnostics interceptor loaded - all fetch() calls will include correlation IDs');
})();
'''
    },

    'vue': {
        'interceptor': '''
// API Diagnostics Interceptor for Vue - Auto-generated
// TODO: Vue-specific interceptor implementation
'''
    }
}

BACKEND_TEMPLATES = {
    'fastapi': {
        'middleware': '''
# API Diagnostics Middleware - Auto-generated
import json
import logging
import time
import traceback
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_diagnostics")


class APIDebugMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses

    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        short_id = correlation_id[:8]  # For readable logs

        # Store correlation ID in request state for access in route handlers
        request.state.correlation_id = correlation_id

        start_time = time.time()
        timestamp = datetime.utcnow().isoformat()

        # Log incoming request
        if self.log_requests:
            await self._log_request(correlation_id, short_id, request, timestamp)

        try:
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Log successful response
            if self.log_responses:
                process_time = time.time() - start_time
                await self._log_response(correlation_id, short_id, request, response, process_time)

            return response

        except HTTPException as e:
            # Handle FastAPI HTTP exceptions (400, 404, etc.)
            process_time = time.time() - start_time
            await self._log_http_exception(correlation_id, short_id, request, e, process_time)

            # Create enhanced error response
            error_response = JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.detail,
                    "correlation_id": correlation_id,
                    "timestamp": timestamp,
                    "endpoint": str(request.url.path)
                },
                headers={"X-Correlation-ID": correlation_id}
            )
            return error_response

        except Exception as e:
            # Handle unexpected server errors (500)
            process_time = time.time() - start_time
            await self._log_server_error(correlation_id, short_id, request, e, process_time)

            # Create enhanced error response
            error_response = JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "correlation_id": correlation_id,
                    "timestamp": timestamp,
                    "endpoint": str(request.url.path)
                },
                headers={"X-Correlation-ID": correlation_id}
            )
            return error_response

    async def _log_request(self, correlation_id: str, short_id: str, request: Request, timestamp: str):
        """Log incoming request details"""
        try:
            # Try to read request body for POST/PUT requests
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = body_bytes.decode('utf-8')[:500]  # Limit body size in logs
                except:
                    body = "<unable to read body>"

            logger.info(f"🔍 [{short_id}] {request.method} {request.url.path}")
            logger.info(f"   Correlation ID: {correlation_id}")
            logger.info(f"   Timestamp: {timestamp}")
            logger.info(f"   Client IP: {request.client.host if request.client else 'unknown'}")
            logger.info(f"   User-Agent: {request.headers.get('user-agent', 'unknown')}")
            if body:
                logger.info(f"   Request Body: {body}")

        except Exception as e:
            logger.error(f"Error logging request: {e}")

    async def _log_response(self, correlation_id: str, short_id: str, request: Request,
                          response: Response, process_time: float):
        """Log successful response"""
        logger.info(f"✅ [{short_id}] {response.status_code} ({process_time:.3f}s)")

    async def _log_http_exception(self, correlation_id: str, short_id: str, request: Request,
                                exception: HTTPException, process_time: float):
        """Log HTTP exceptions (400, 404, etc.)"""
        logger.error(f"❌ [{short_id}] {exception.status_code} {exception.detail} ({process_time:.3f}s)")
        logger.error(f"   Correlation ID: {correlation_id}")
        logger.error(f"   Endpoint: {request.url.path}")
        logger.error(f"   Method: {request.method}")

    async def _log_server_error(self, correlation_id: str, short_id: str, request: Request,
                              error: Exception, process_time: float):
        """Log unexpected server errors (500)"""
        logger.error(f"🚫 [{short_id}] SERVER ERROR: {str(error)} ({process_time:.3f}s)")
        logger.error(f"   Correlation ID: {correlation_id}")
        logger.error(f"   Endpoint: {request.url.path}")
        logger.error(f"   Method: {request.method}")
        logger.error(f"   Stack trace: {traceback.format_exc()}")


# Helper function to get correlation ID in route handlers
def get_correlation_id(request: Request) -> Optional[str]:
    """Get the correlation ID from request state"""
    return getattr(request.state, 'correlation_id', None)


# Usage example:
# from fastapi import FastAPI
# from api_middleware import APIDebugMiddleware
#
# app = FastAPI()
# app.add_middleware(APIDebugMiddleware)
'''
    },

    'flask': {
        'middleware': '''
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
'''
    }
}

CONFIG_TEMPLATES = {
    'api_diagnostics_config': '''
{
  "enabled": true,
  "log_level": "ERROR",
  "log_path": "./logs/api-diagnostics.log",
  "frameworks": {
    "frontend": "auto-detect",
    "backend": "auto-detect"
  }
}
'''
}
