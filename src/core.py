"""
Core Business Logic for API Diagnostics
Handles correlation IDs, logging, and error processing
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LogEntry:
    timestamp: str
    level: str  # 'ERROR', 'INFO', 'DEBUG'
    correlation_id: str
    endpoint: str
    method: str
    status_code: int
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    request_body: Optional[str] = None


def generate_correlation_id() -> str:
    """Generate unique correlation ID using UUID4"""
    return str(uuid.uuid4())


def validate_correlation_id(correlation_id: str) -> bool:
    """Validate correlation ID format (must be valid UUID)"""
    if not correlation_id or not isinstance(correlation_id, str):
        return False

    try:
        # Try to parse as UUID - will raise ValueError if invalid
        uuid.UUID(correlation_id)
        return True
    except ValueError:
        return False


def format_correlation_id(correlation_id: str) -> str:
    """Format correlation ID for consistent display (first 8 chars)"""
    if not validate_correlation_id(correlation_id):
        return "invalid-id"

    return correlation_id[:8]  # Show first 8 characters for readability


def generate_short_id() -> str:
    """Generate shorter correlation ID for easier reading (8 chars)"""
    full_id = generate_correlation_id()
    return full_id[:8]


def format_log_entry(entry: LogEntry, format_type: str = 'json') -> str:
    """Format log entry for display in different formats"""
    if format_type == 'json':
        return json.dumps({
            'timestamp': entry.timestamp,
            'level': entry.level,
            'correlation_id': entry.correlation_id,
            'endpoint': entry.endpoint,
            'method': entry.method,
            'status_code': entry.status_code,
            'error_message': entry.error_message,
            'stack_trace': entry.stack_trace,
            'request_body': entry.request_body
        }, indent=2)

    elif format_type == 'human':
        short_id = format_correlation_id(entry.correlation_id)
        status_emoji = "❌" if entry.status_code >= 400 else "✅"

        lines = [
            f"{status_emoji} [{short_id}] {entry.method} {entry.endpoint}",
            f"   Status: {entry.status_code}",
            f"   Time: {entry.timestamp}",
            f"   Correlation ID: {entry.correlation_id}"
        ]

        if entry.error_message:
            lines.append(f"   Error: {entry.error_message}")

        if entry.request_body:
            lines.append(f"   Request: {entry.request_body[:100]}...")

        if entry.stack_trace:
            lines.append(f"   Stack Trace: {entry.stack_trace.split(chr(10))[0]}...")

        return "\n".join(lines)

    elif format_type == 'compact':
        short_id = format_correlation_id(entry.correlation_id)
        status_emoji = "❌" if entry.status_code >= 400 else "✅"
        return f"{status_emoji} [{short_id}] {entry.status_code} {entry.method} {entry.endpoint} - {entry.error_message or 'OK'}"

    else:
        raise ValueError(f"Unknown format type: {format_type}")


def create_log_entry(correlation_id: str, endpoint: str, method: str, status_code: int,
                    error_message: str = None, stack_trace: str = None,
                    request_body: str = None, level: str = 'INFO') -> LogEntry:
    """Create a structured log entry with current timestamp"""
    return LogEntry(
        timestamp=datetime.now().isoformat(),
        level=level,
        correlation_id=correlation_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        error_message=error_message,
        stack_trace=stack_trace,
        request_body=request_body
    )


def parse_log_line(log_line: str) -> Optional[LogEntry]:
    """Parse a log line into structured LogEntry"""
    try:
        # Try to parse as JSON first (structured logs)
        if log_line.strip().startswith('{'):
            data = json.loads(log_line.strip())
            return LogEntry(
                timestamp=data.get('timestamp', ''),
                level=data.get('level', 'INFO'),
                correlation_id=data.get('correlation_id', ''),
                endpoint=data.get('endpoint', ''),
                method=data.get('method', ''),
                status_code=data.get('status_code', 0),
                error_message=data.get('error_message'),
                stack_trace=data.get('stack_trace'),
                request_body=data.get('request_body')
            )

        # Try to parse common log formats
        import re

        # Pattern for our middleware logs: [correlation_id] METHOD endpoint STATUS
        pattern = r'\[([a-f0-9-]+)\]\s+(\w+)\s+([^\s]+)\s+(\d{3})'
        match = re.search(pattern, log_line)

        if match:
            correlation_id, method, endpoint, status_str = match.groups()
            status_code = int(status_str)

            # Extract error message if present
            error_message = None
            if 'ERROR' in log_line or status_code >= 400:
                # Try to extract error message after status code
                error_match = re.search(r'\d{3}\s+(.+)', log_line)
                if error_match:
                    error_message = error_match.group(1).strip()

            level = 'ERROR' if status_code >= 400 else 'INFO'

            return LogEntry(
                timestamp=datetime.now().isoformat(),  # Fallback timestamp
                level=level,
                correlation_id=correlation_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                error_message=error_message,
                stack_trace=None,
                request_body=None
            )

    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    return None


def filter_log_entries(entries: List[LogEntry],
                      correlation_id: str = None,
                      error_type: str = None,
                      endpoint: str = None,
                      method: str = None) -> List[LogEntry]:
    """Filter log entries by various criteria"""
    filtered = entries

    if correlation_id:
        filtered = [e for e in filtered if correlation_id.lower() in e.correlation_id.lower()]

    if error_type:
        if error_type == '400':
            filtered = [e for e in filtered if 400 <= e.status_code < 500]
        elif error_type == '500':
            filtered = [e for e in filtered if e.status_code >= 500]
        elif error_type == 'error':
            filtered = [e for e in filtered if e.status_code >= 400]

    if endpoint:
        filtered = [e for e in filtered if endpoint.lower() in e.endpoint.lower()]

    if method:
        filtered = [e for e in filtered if e.method.upper() == method.upper()]

    return filtered


def search_logs_by_correlation_id(correlation_id: str, log_paths: List[str] = None) -> List[LogEntry]:
    """Search log files for entries with specific correlation ID"""
    if not log_paths:
        log_paths = _get_default_log_paths()

    entries = []
    for log_path in log_paths:
        entries.extend(_search_file_for_correlation_id(log_path, correlation_id))

    return entries


def search_logs_by_error_type(error_type: str, log_paths: List[str] = None, limit: int = 50) -> List[LogEntry]:
    """Search log files for entries with specific error types"""
    if not log_paths:
        log_paths = _get_default_log_paths()

    entries = []
    for log_path in log_paths:
        entries.extend(_search_file_for_errors(log_path, error_type, limit))

    return sorted(entries, key=lambda x: x.timestamp, reverse=True)[:limit]


def search_logs_recent(hours: int = 24, log_paths: List[str] = None, limit: int = 100) -> List[LogEntry]:
    """Search for recent log entries"""
    if not log_paths:
        log_paths = _get_default_log_paths()

    from datetime import datetime, timedelta
    cutoff_time = datetime.now() - timedelta(hours=hours)

    entries = []
    for log_path in log_paths:
        entries.extend(_search_file_recent(log_path, cutoff_time, limit))

    return sorted(entries, key=lambda x: x.timestamp, reverse=True)[:limit]


def _get_default_log_paths() -> List[str]:
    """Get default log file paths to search"""
    from pathlib import Path

    possible_paths = [
        # Common log locations
        './logs/app.log',
        './app.log',
        './api-diagnostics.log',
        './.api-diagnostics/logs/app.log',
        # Python logging default locations
        './debug.log',
        './error.log',
        # FastAPI/Flask common locations
        './uvicorn.log',
        './gunicorn.log',
        './flask.log'
    ]

    # Only return paths that exist
    existing_paths = []
    for path_str in possible_paths:
        path = Path(path_str)
        if path.exists() and path.is_file():
            existing_paths.append(str(path))

    return existing_paths


def _search_file_for_correlation_id(log_path: str, correlation_id: str) -> List[LogEntry]:
    """Search a single log file for correlation ID"""
    from pathlib import Path

    entries = []
    log_file = Path(log_path)

    if not log_file.exists():
        return entries

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if correlation_id.lower() in line.lower():
                    entry = parse_log_line(line.strip())
                    if entry:
                        entries.append(entry)
                    else:
                        # Create a basic entry for unparseable lines that contain the correlation ID
                        entries.append(LogEntry(
                            timestamp=datetime.now().isoformat(),
                            level='INFO',
                            correlation_id=correlation_id,
                            endpoint='unknown',
                            method='unknown',
                            status_code=0,
                            error_message=f'Raw log line {line_num}: {line.strip()[:100]}...'
                        ))

    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading log file {log_path}: {e}")

    return entries


def _search_file_for_errors(log_path: str, error_type: str, limit: int) -> List[LogEntry]:
    """Search a single log file for error entries"""
    from pathlib import Path

    entries = []
    log_file = Path(log_path)

    if not log_file.exists():
        return entries

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Look for error indicators
                is_error_line = False
                if error_type == '400' and ('400' in line or 'Bad Request' in line):
                    is_error_line = True
                elif error_type == '500' and ('500' in line or 'Internal Server Error' in line or 'ERROR' in line):
                    is_error_line = True
                elif error_type == 'error' and ('ERROR' in line or 'error' in line or any(code in line for code in ['400', '401', '403', '404', '500', '502', '503'])):
                    is_error_line = True

                if is_error_line:
                    entry = parse_log_line(line)
                    if entry:
                        entries.append(entry)

                    if len(entries) >= limit:
                        break

    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading log file {log_path}: {e}")

    return entries


def _search_file_recent(log_path: str, cutoff_time, limit: int) -> List[LogEntry]:
    """Search a single log file for recent entries"""
    from pathlib import Path

    entries = []
    log_file = Path(log_path)

    if not log_file.exists():
        return entries

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                entry = parse_log_line(line)
                if entry:
                    # For now, include all parsed entries (timestamp filtering is complex)
                    entries.append(entry)

                if len(entries) >= limit:
                    break

    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading log file {log_path}: {e}")

    return entries
