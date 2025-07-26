"""
Tests for Safe Code Injection System
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from integrations import (
    backup_file,
    restore_from_backup,
    inject_code_safely,
    remove_injected_code,
    get_backup_files,
    clean_old_backups
)


class TestFileInjection:
    def setup_method(self):
        """Create temporary files for testing"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create a test Python file
        self.test_py_file = self.temp_dir / 'test_app.py'
        self.test_py_file.write_text('''import os
import sys
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
''')

        # Create a test JavaScript file
        self.test_js_file = self.temp_dir / 'test_app.js'
        self.test_js_file.write_text('''import React from 'react';
import axios from';

function App() {
  return <div>Hello World</div>;
}

export default App;
''')

    def teardown_method(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_backup_file(self):
        """Test file backup functionality"""
        original_content = self.test_py_file.read_text()

        # Create backup
        backup_path = backup_file(str(self.test_py_file))

        # Verify backup exists and has same content
        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == original_content
        assert 'backup_' in backup_path

    def test_backup_nonexistent_file(self):
        """Test backup of non-existent file raises error"""
        with pytest.raises(FileNotFoundError):
            backup_file(str(self.temp_dir / 'nonexistent.py'))

    def test_inject_code_top(self):
        """Test injecting code at top of file"""
        injection_code = '''# API Diagnostics setup
from api_middleware import FlaskAPIDebugger
debugger = FlaskAPIDebugger(app)'''

        result = inject_code_safely(str(self.test_py_file), injection_code, 'top')
        assert result is True

        # Verify code was injected
        content = self.test_py_file.read_text()
        assert 'api_diagnostics_injection' in content
        assert 'FlaskAPIDebugger' in content
        assert content.startswith('# START api_diagnostics_injection')

    def test_inject_code_bottom(self):
        """Test injecting code at bottom of file"""
        injection_code = '''# API Diagnostics cleanup
print("API Diagnostics active")'''

        result = inject_code_safely(str(self.test_py_file), injection_code, 'bottom')
        assert result is True

        # Verify code was injected
        content = self.test_py_file.read_text()
        assert 'API Diagnostics cleanup' in content
        assert content.endswith('# END api_diagnostics_injection\n')

    def test_inject_code_after_imports(self):
        """Test injecting code after import statements"""
        injection_code = '''# API Diagnostics middleware
from api_middleware import FlaskAPIDebugger'''

        result = inject_code_safely(str(self.test_py_file), injection_code, 'after_imports')
        assert result is True

        # Verify code was injected after imports
        lines = self.test_py_file.read_text().split('\n')

        # Find the injection
        injection_found = False
        for i, line in enumerate(lines):
            if 'api_diagnostics_injection' in line:
                injection_found = True
                # Should be after the import statements
                assert i > 2  # After import os, sys, flask
                break

        assert injection_found

    def test_prevent_duplicate_injection(self):
        """Test that duplicate injections are prevented"""
        injection_code = '''from api_middleware import FlaskAPIDebugger'''

        # First injection should succeed
        result1 = inject_code_safely(str(self.test_py_file), injection_code, 'top')
        assert result1 is True

        # Second injection should be prevented
        result2 = inject_code_safely(str(self.test_py_file), injection_code, 'top')
        assert result2 is False

        # Verify only one injection exists
        content = self.test_py_file.read_text()
        assert content.count('api_diagnostics_injection') == 2  # START and END markers

    def test_syntax_validation_python(self):
        """Test Python syntax validation prevents invalid code injection"""
        invalid_code = '''def broken_function(
    # Missing closing parenthesis and colon'''

        # This should fail due to syntax error
        result = inject_code_safely(str(self.test_py_file), invalid_code, 'top')
        assert result is False

        # Original file should be unchanged
        content = self.test_py_file.read_text()
        assert 'broken_function' not in content

    def test_remove_injected_code(self):
        """Test removing previously injected code"""
        injection_code = '''from api_middleware import FlaskAPIDebugger
debugger = FlaskAPIDebugger(app)'''

        # Inject code
        inject_code_safely(str(self.test_py_file), injection_code, 'top')

        # Verify injection exists
        content_with_injection = self.test_py_file.read_text()
        assert 'FlaskAPIDebugger' in content_with_injection

        # Remove injection
        result = remove_injected_code(str(self.test_py_file))
        assert result is True

        # Verify injection was removed
        content_after_removal = self.test_py_file.read_text()
        assert 'FlaskAPIDebugger' not in content_after_removal
        assert 'api_diagnostics_injection' not in content_after_removal

    def test_remove_nonexistent_injection(self):
        """Test removing injection that doesn't exist"""
        result = remove_injected_code(str(self.test_py_file))
        assert result is False

    def test_restore_from_backup(self):
        """Test restoring file from backup"""
        original_content = self.test_py_file.read_text()

        # Create backup
        backup_path = backup_file(str(self.test_py_file))

        # Modify the file
        self.test_py_file.write_text('Modified content')
        assert self.test_py_file.read_text() == 'Modified content'

        # Restore from backup
        result = restore_from_backup(str(self.test_py_file), backup_path)
        assert result is True

        # Verify content was restored
        assert self.test_py_file.read_text() == original_content

    def test_get_backup_files(self):
        """Test getting list of backup files"""
        import time

        # Create multiple backups with slight delay
        backup1 = backup_file(str(self.test_py_file))
        time.sleep(1.1)  # Ensure different timestamps
        backup2 = backup_file(str(self.test_py_file))

        backup_files = get_backup_files(str(self.test_py_file))

        assert len(backup_files) == 2
        assert backup1 in backup_files or backup2 in backup_files

    def test_clean_old_backups(self):
        """Test cleaning old backup files"""
        import time

        # Create multiple backups with slight delays
        for i in range(7):
            backup_file(str(self.test_py_file))
            time.sleep(0.1)  # Small delay to ensure different timestamps

        # Should have 7 backups
        backup_files = get_backup_files(str(self.test_py_file))
        assert len(backup_files) == 7

        # Clean old backups, keep only 3
        removed_count = clean_old_backups(str(self.test_py_file), keep_count=3)
        assert removed_count == 4

        # Should now have only 3 backups
        backup_files_after = get_backup_files(str(self.test_py_file))
        assert len(backup_files_after) == 3

    def test_custom_marker(self):
        """Test using custom markers for injection tracking"""
        injection_code = '''# Custom injection'''
        custom_marker = 'my_custom_marker'

        # Inject with custom marker
        result = inject_code_safely(str(self.test_py_file), injection_code, 'top', marker=custom_marker)
        assert result is True

        # Verify custom marker is used
        content = self.test_py_file.read_text()
        assert f'START {custom_marker}' in content
        assert f'END {custom_marker}' in content

        # Remove with custom marker
        result = remove_injected_code(str(self.test_py_file), marker=custom_marker)
        assert result is True

        # Verify removal worked
        content_after = self.test_py_file.read_text()
        assert custom_marker not in content_after

    def test_javascript_file_injection(self):
        """Test injecting code into JavaScript files"""
        injection_code = '''// API Diagnostics interceptor
import { apiDiagnostics } from './api-diagnostics';'''

        result = inject_code_safely(str(self.test_js_file), injection_code, 'after_imports')
        assert result is True

        # Verify injection (no syntax validation for JS files)
        content = self.test_js_file.read_text()
        assert 'apiDiagnostics' in content
        assert 'api_diagnostics_injection' in content
