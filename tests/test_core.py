"""
Tests for Core Functionality
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core import (
    generate_correlation_id,
    validate_correlation_id,
    format_correlation_id,
    generate_short_id,
    format_log_entry,
    create_log_entry,
    parse_log_line,
    filter_log_entries,
    LogSearcher,
    LogEntry
)


class TestCorrelationFunctions:
    def test_generate_correlation_id(self):
        """Test correlation ID generation"""
        correlation_id = generate_correlation_id()
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        assert len(correlation_id) == 36  # UUID4 length
        assert '-' in correlation_id  # UUID format

    def test_validate_correlation_id(self):
        """Test correlation ID validation"""
        # Valid UUID
        valid_id = generate_correlation_id()
        assert validate_correlation_id(valid_id) is True

        # Invalid IDs
        assert validate_correlation_id('invalid') is False
        assert validate_correlation_id('') is False
        assert validate_correlation_id(None) is False
        assert validate_correlation_id(123) is False

    def test_format_correlation_id(self):
        """Test correlation ID formatting"""
        full_id = generate_correlation_id()
        formatted = format_correlation_id(full_id)

        assert len(formatted) == 8
        assert formatted == full_id[:8]

        # Test invalid ID formatting
        assert format_correlation_id('invalid') == "invalid-id"

    def test_generate_short_id(self):
        """Test short ID generation"""
        short_id = generate_short_id()
        assert len(short_id) == 8
        assert isinstance(short_id, str)


class TestLogFormatting:
    def test_format_log_entry_json(self):
        """Test JSON log entry formatting"""
        entry = LogEntry(
            timestamp='2024-01-15T10:30:45Z',
            level='ERROR',
            correlation_id='test-123-456-789',
            endpoint='/api/test',
            method='POST',
            status_code=400,
            error_message='Test error'
        )

        formatted = format_log_entry(entry, 'json')
        assert 'test-123-456-789' in formatted
        assert 'ERROR' in formatted
        assert '400' in formatted

    def test_format_log_entry_human(self):
        """Test human-readable log entry formatting"""
        # Use a valid UUID for testing
        test_id = generate_correlation_id()
        entry = LogEntry(
            timestamp='2024-01-15T10:30:45Z',
            level='ERROR',
            correlation_id=test_id,
            endpoint='/api/test',
            method='POST',
            status_code=400,
            error_message='Test error'
        )

        formatted = format_log_entry(entry, 'human')
        assert '❌' in formatted  # Error emoji
        assert f'[{test_id[:8]}]' in formatted  # Short ID
        assert 'POST /api/test' in formatted
        assert 'Status: 400' in formatted

    def test_format_log_entry_compact(self):
        """Test compact log entry formatting"""
        # Use a valid UUID for testing
        test_id = generate_correlation_id()
        entry = LogEntry(
            timestamp='2024-01-15T10:30:45Z',
            level='INFO',
            correlation_id=test_id,
            endpoint='/api/test',
            method='GET',
            status_code=200
        )

        formatted = format_log_entry(entry, 'compact')
        assert '✅' in formatted  # Success emoji
        assert f'[{test_id[:8]}]' in formatted
        assert '200 GET /api/test' in formatted

    def test_create_log_entry(self):
        """Test log entry creation"""
        entry = create_log_entry(
            correlation_id='test-123',
            endpoint='/api/users',
            method='POST',
            status_code=201,
            error_message=None,
            level='INFO'
        )

        assert entry.correlation_id == 'test-123'
        assert entry.endpoint == '/api/users'
        assert entry.method == 'POST'
        assert entry.status_code == 201
        assert entry.level == 'INFO'
        assert entry.timestamp is not None

    def test_parse_log_line_json(self):
        """Test parsing JSON log lines"""
        json_log = '{"timestamp": "2024-01-15T10:30:45Z", "level": "ERROR", "correlation_id": "test-123", "endpoint": "/api/test", "method": "POST", "status_code": 400, "error_message": "Test error"}'

        entry = parse_log_line(json_log)
        assert entry is not None
        assert entry.correlation_id == 'test-123'
        assert entry.status_code == 400
        assert entry.error_message == 'Test error'

    def test_parse_log_line_middleware_format(self):
        """Test parsing middleware log format"""
        # Use a valid UUID format in the log line
        test_id = generate_correlation_id()
        log_line = f"2024-01-15 10:30:45 - api_diagnostics - ERROR - ❌ [{test_id[:8]}] POST /api/users 400 Validation failed"

        entry = parse_log_line(log_line)
        assert entry is not None
        assert test_id[:8] in entry.correlation_id
        assert entry.method == 'POST'
        assert entry.endpoint == '/api/users'
        assert entry.status_code == 400

    def test_filter_log_entries(self):
        """Test log entry filtering"""
        entries = [
            LogEntry('2024-01-15T10:30:45Z', 'ERROR', 'abc-123', '/api/users', 'POST', 400, 'Bad request'),
            LogEntry('2024-01-15T10:31:45Z', 'ERROR', 'def-456', '/api/users', 'GET', 500, 'Server error'),
            LogEntry('2024-01-15T10:32:45Z', 'INFO', 'ghi-789', '/api/posts', 'GET', 200, None)
        ]

        # Filter by correlation ID
        filtered = filter_log_entries(entries, correlation_id='abc')
        assert len(filtered) == 1
        assert filtered[0].correlation_id == 'abc-123'

        # Filter by error type
        filtered = filter_log_entries(entries, error_type='400')
        assert len(filtered) == 1
        assert filtered[0].status_code == 400

        filtered = filter_log_entries(entries, error_type='500')
        assert len(filtered) == 1
        assert filtered[0].status_code == 500

        # Filter by endpoint
        filtered = filter_log_entries(entries, endpoint='users')
        assert len(filtered) == 2

        # Filter by method
        filtered = filter_log_entries(entries, method='GET')
        assert len(filtered) == 2


class TestLogSearcher:
    @pytest.mark.asyncio
    async def test_search_by_correlation_id(self):
        """Test searching by correlation ID"""
        results = await LogSearcher.search_by_correlation_id('test-123')
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_filter_by_error_type(self):
        """Test filtering by error type"""
        results = await LogSearcher.filter_by_error_type('400')
        assert isinstance(results, list)
