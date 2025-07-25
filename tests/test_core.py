"""
Tests for Core Functionality
"""

import pytest
from src.core import CorrelationManager, LogFormatter, LogSearcher, LogEntry


class TestCorrelationManager:
    def test_generate_id(self):
        """Test correlation ID generation"""
        correlation_id = CorrelationManager.generate_id()
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0

    def test_validate_id(self):
        """Test correlation ID validation"""
        valid_id = CorrelationManager.generate_id()
        assert CorrelationManager.validate_id(valid_id) is True
        assert CorrelationManager.validate_id('invalid') is False


class TestLogFormatter:
    def test_format_error(self):
        """Test log entry formatting"""
        entry = LogEntry(
            timestamp='2024-01-15T10:30:45Z',
            level='ERROR',
            correlation_id='test-123',
            endpoint='/api/test',
            method='POST',
            status_code=400,
            error_message='Test error'
        )

        formatted = LogFormatter.format_error(entry)
        assert 'test-123' in formatted
        assert 'ERROR' in formatted


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
