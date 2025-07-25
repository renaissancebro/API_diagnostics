# API Diagnostics Design Document

## Overview

A plug-and-play CLI debugging tool that helps backend developers trace frontend API errors back to specific code locations. The system can be easily integrated into any existing project and generates unique correlation IDs for each request with enhanced error logging and stack traces.

## Architecture

### High-Level Components

```
Frontend (Browser)          Backend (FastAPI)           Logs
┌─────────────────┐        ┌──────────────────┐        ┌─────────────┐
│ API Interceptor │───────▶│ Logging Middleware│───────▶│ Enhanced    │
│ - Adds headers  │        │ - Generates ID    │        │ Error Logs  │
│ - Logs requests │        │ - Catches errors  │        │ - Correlation│
│ - Shows errors  │        │ - Formats logs    │        │ - Stack trace│
└─────────────────┘        └──────────────────┘        └─────────────┘
```

### What is Middleware?

Middleware is code that runs BEFORE your actual API endpoint. Think of it like a filter:

- Every request passes through middleware first
- It can modify the request, add information, or catch errors
- Then it passes the request to your actual API function
- If there's an error, middleware catches it and can format it nicely

## Components and Interfaces

### 1. CLI Tool & Auto-Integration

**Purpose**: Command-line tool that automatically integrates with existing projects

**Interface**:

```bash
# Install globally
npm install -g api-diagnostics

# Initialize in any project
api-diagnostics init

# Start monitoring
api-diagnostics start
```

**Auto-Integration Features**:

- Detects project type (React, Vue, FastAPI, Express, etc.)
- Automatically injects frontend interceptor code
- Adds backend middleware with minimal configuration
- Works with existing code without modifications

**Responsibilities**:

- Project detection and auto-configuration
- Code injection for frontend/backend integration
- Log monitoring and formatting
- CLI interface for starting/stopping diagnostics

### 2. Backend Logging Middleware (FastAPI)

**Purpose**: Intercepts all API requests to log them and handle errors

**How it works**:

```python
# This runs BEFORE your API endpoint
@app.middleware("http")
async def logging_middleware(request, call_next):
    # 1. Extract correlation ID from headers
    # 2. Log the incoming request
    # 3. Call your actual API endpoint
    # 4. If error occurs, catch it and format nicely
    # 5. Return response
```

**Responsibilities**:

- Extract correlation ID from request headers
- Log all requests with timestamp and details
- Catch exceptions and format error responses
- Add stack trace information to error logs

### 3. Enhanced Error Logger

**Purpose**: Creates structured, searchable log entries

**Log Format**:

```
[2024-01-15 10:30:45] ERROR correlation_id=abc123 endpoint=/api/users method=POST
Status: 400 - Validation Error
Error: Missing required field 'email'
Stack Trace: /app/routes/users.py:45
Request Body: {"name": "John"}
```

## Data Models

### Correlation ID

- **Format**: UUID4 string (e.g., "abc123-def456-ghi789")
- **Generated**: Frontend before each request
- **Passed**: Via HTTP header `X-Correlation-ID`
- **Used**: Backend logging and error tracking

### Error Response Format

```json
{
  "error": true,
  "message": "Validation failed",
  "details": "Missing required field 'email'",
  "correlation_id": "abc123-def456-ghi789",
  "timestamp": "2024-01-15T10:30:45Z",
  "endpoint": "/api/users"
}
```

### Log Entry Structure

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "ERROR",
  "correlation_id": "abc123-def456-ghi789",
  "endpoint": "/api/users",
  "method": "POST",
  "status_code": 400,
  "error_message": "Missing required field 'email'",
  "stack_trace": "/app/routes/users.py:45",
  "request_body": "{\"name\": \"John\"}"
}
```

## Data Flow

1. **CLI Initialization**:

   - Developer runs `api-diagnostics init` in project
   - Tool detects project structure and framework
   - Automatically configures integration files

2. **Frontend Request**:

   - User action triggers API call
   - Auto-injected interceptor generates correlation ID
   - Request sent with correlation ID in headers

3. **Backend Processing**:

   - Middleware extracts correlation ID
   - Logs incoming request with ID
   - Passes request to actual API endpoint
   - If error occurs, middleware catches it

4. **Error Handling**:

   - Middleware formats error with correlation ID
   - Logs detailed error information
   - Returns structured error response to frontend

5. **Frontend Error Display**:

   - Receives error response with correlation ID
   - Displays user-friendly error message
   - Logs detailed error info to browser console

6. **Debugging**:
   - Developer sees error in browser console with correlation ID
   - Searches backend logs using correlation ID
   - Finds exact error location and details

## Error Handling

### 400 Errors (Client Errors)

- Validation failures
- Missing required fields
- Invalid data formats
- Log with request details and validation errors

### 500 Errors (Server Errors)

- Database connection issues
- Unhandled exceptions
- Service unavailable
- Log with full stack trace and system state

## Testing Strategy

### Unit Tests

- Test correlation ID generation
- Test middleware error catching
- Test log formatting functions

### Integration Tests

- Test full request/response cycle with correlation IDs
- Test error propagation from backend to frontend
- Test log searching and filtering

### Manual Testing

- Trigger various error scenarios
- Verify correlation IDs appear in both frontend and backend logs
- Test log searching functionality
