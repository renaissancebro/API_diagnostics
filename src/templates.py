"""
Code Templates for Framework Integration
Contains code snippets that get injected into projects
"""

FRONTEND_TEMPLATES = {
    'react': {
        'interceptor': '''
// API Diagnostics Interceptor - Auto-generated
import { v4 as uuidv4 } from 'uuid';

const originalFetch = window.fetch;
window.fetch = async function(url, options = {}) {
  const correlationId = uuidv4();

  // Add correlation ID to headers
  const headers = {
    ...options.headers,
    'X-Correlation-ID': correlationId
  };

  console.log('[API-DIAGNOSTICS] Request:', {
    correlationId,
    url,
    method: options.method || 'GET',
    timestamp: new Date().toISOString()
  });

  try {
    const response = await originalFetch(url, { ...options, headers });

    if (!response.ok) {
      console.error('[API-DIAGNOSTICS] Error Response:', {
        correlationId,
        url,
        status: response.status,
        statusText: response.statusText,
        timestamp: new Date().toISOString()
      });
    }

    return response;
  } catch (error) {
    console.error('[API-DIAGNOSTICS] Network Error:', {
      correlationId,
      url,
      error: error.message,
      timestamp: new Date().toISOString()
    });
    throw error;
  }
};
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
import logging
import time
import traceback
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_diagnostics")

class APIDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start_time = time.time()

        # Log incoming request
        logger.info(f"[{correlation_id}] {request.method} {request.url}")

        try:
            response = await call_next(request)

            # Log successful response
            process_time = time.time() - start_time
            logger.info(f"[{correlation_id}] Response: {response.status_code} ({process_time:.3f}s)")

            return response

        except Exception as e:
            # Log error with stack trace
            process_time = time.time() - start_time
            logger.error(f"[{correlation_id}] ERROR: {str(e)} ({process_time:.3f}s)")
            logger.error(f"[{correlation_id}] Stack trace: {traceback.format_exc()}")
            raise
'''
    },

    'flask': {
        'middleware': '''
# API Diagnostics Middleware for Flask - Auto-generated
import logging
import time
import traceback
import uuid
from flask import request, g

logger = logging.getLogger("api_diagnostics")

def before_request():
    g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    g.start_time = time.time()
    logger.info(f"[{g.correlation_id}] {request.method} {request.url}")

def after_request(response):
    if hasattr(g, 'correlation_id') and hasattr(g, 'start_time'):
        process_time = time.time() - g.start_time
        logger.info(f"[{g.correlation_id}] Response: {response.status_code} ({process_time:.3f}s)")
    return response

def handle_exception(e):
    if hasattr(g, 'correlation_id') and hasattr(g, 'start_time'):
        process_time = time.time() - g.start_time
        logger.error(f"[{g.correlation_id}] ERROR: {str(e)} ({process_time:.3f}s)")
        logger.error(f"[{g.correlation_id}] Stack trace: {traceback.format_exc()}")
    raise
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
