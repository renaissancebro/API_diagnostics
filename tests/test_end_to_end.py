"""
End-to-End Integration Tests
"""

import pytest
import tempfile
import subprocess
import json
from pathlib import Path

class TestEndToEnd:
    def setup_method(self):
        """Create temporary test project"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create a simple Flask app
        self.flask_app = self.temp_dir / 'app.py'
        self.flask_app.write_text('''
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/error')
def error():
    raise Exception('Test error')

if __name__ == '__main__':
    app.run()
''')

    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_full_workflow(self):
        """Test complete workflow from init to search"""
        # Change to test directory
        original_cwd = Path.cwd()
        import os
        os.chdir(self.temp_dir)

        try:
            # Test init command
            result = subprocess.run([
                str(original_cwd / 'api-diagnostics'), 'init', '--auto'
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert 'Automatic integration complete' in result.stdout

            # Verify files were created
            assert (self.temp_dir / '.api-diagnostics').exists()
            assert (self.temp_dir / '.api-diagnostics' / 'generated' / 'api_middleware.py').exists()

            # Test status command
            result = subprocess.run([
                str(original_cwd / 'api-diagnostics'), 'status'
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert 'STOPPED' in result.stdout

            # Test start command
            result = subprocess.run([
                str(original_cwd / 'api-diagnostics'), 'start'
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert 'monitoring started' in result.stdout

            # Test clean command
            result = subprocess.run([
                str(original_cwd / 'api-diagnostics'), 'clean'
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert 'Integration removed successfully' in result.stdout

            # Verify cleanup
            assert not (self.temp_dir / '.api-diagnostics').exists()

        finally:
            os.chdir(original_cwd)

    def test_error_handling(self):
        """Test error handling for various scenarios"""
        original_cwd = Path.cwd()
        import os
        os.chdir(self.temp_dir)

        try:
            # Test init in directory without supported frameworks
            empty_dir = self.temp_dir / 'empty'
            empty_dir.mkdir()

            result = subprocess.run([
                str(original_cwd / 'api-diagnostics'), 'init', str(empty_dir)
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert 'No supported frameworks detected' in result.stdout

            # Test search with no logs
            result = subprocess.run([
                str(original_cwd / 'api-diagnostics'), 'search', 'nonexistent-id'
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert 'No log entries found' in result.stdout

        finally:
            os.chdir(original_cwd)

    def test_help_system(self):
        """Test help and documentation"""
        original_cwd = Path.cwd()

        # Test main help
        result = subprocess.run([
            str(original_cwd / 'api-diagnostics'), '--help'
        ], capture_output=True, text=True)

        assert result.returncode == 0
        assert 'API Diagnostics' in result.stdout
        assert 'init' in result.stdout
        assert 'search' in result.stdout

        # Test command-specific help
        result = subprocess.run([
            str(original_cwd / 'api-diagnostics'), 'init', '--help'
        ], capture_output=True, text=True)

        assert result.returncode == 0
        assert '--auto' in result.stdout
