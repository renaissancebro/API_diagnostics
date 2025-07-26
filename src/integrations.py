"""
Framework Integration and Project Detection
Handles detection of different frameworks and auto-configuration
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ProjectInfo:
    type: str  # 'frontend', 'backend', 'fullstack'
    frontend: Optional[str] = None  # 'react' only
    backend: Optional[str] = None   # 'fastapi', 'flask'
    package_manager: str = 'pip'    # 'pip', 'npm'


def detect_frontend_framework(project_path: str) -> Optional[str]:
    """Check for React framework in package.json"""
    package_json_path = Path(project_path) / 'package.json'

    if not package_json_path.exists():
        return None

    try:
        with open(package_json_path) as f:
            package_data = json.load(f)

        # Combine regular and dev dependencies
        dependencies = {
            **package_data.get('dependencies', {}),
            **package_data.get('devDependencies', {})
        }

        # Check for React (most common indicators)
        if any(dep in dependencies for dep in ['react', 'react-dom', '@types/react']):
            return 'react'

    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        pass

    return None


def detect_backend_framework(project_path: str) -> Optional[str]:
    """Check for FastAPI or Flask in Python files"""
    project_dir = Path(project_path)

    # Check for Python files with framework imports
    for py_file in project_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for FastAPI first (more specific)
            if any(pattern in content for pattern in [
                'from fastapi import',
                'import fastapi',
                'FastAPI()',
                '@app.get',
                '@app.post'
            ]):
                return 'fastapi'

            # Check for Flask
            elif any(pattern in content for pattern in [
                'from flask import',
                'import flask',
                'Flask(__name__)',
                '@app.route'
            ]):
                return 'flask'

        except (UnicodeDecodeError, PermissionError, OSError):
            continue

    return None


def detect_project(project_path: str = '.') -> Optional[ProjectInfo]:
    """Detect project type and frameworks"""
    frontend = detect_frontend_framework(project_path)
    backend = detect_backend_framework(project_path)

    if not frontend and not backend:
        return None

    # Determine project type
    if frontend and backend:
        project_type = 'fullstack'
    elif frontend:
        project_type = 'frontend'
    else:
        project_type = 'backend'

    # Determine package manager
    package_manager = 'npm' if frontend else 'pip'

    return ProjectInfo(
        type=project_type,
        frontend=frontend,
        backend=backend,
        package_manager=package_manager
    )


def setup_integration(project_info: ProjectInfo, project_path: str, auto_inject: bool = False) -> List[str]:
    """Generate configuration files and optionally auto-inject monitoring code"""
    from templates import FRONTEND_TEMPLATES, BACKEND_TEMPLATES, CONFIG_TEMPLATES

    project_dir = Path(project_path)
    diagnostics_dir = project_dir / '.api-diagnostics'

    # Create generated code directory
    generated_dir = diagnostics_dir / 'generated'
    generated_dir.mkdir(exist_ok=True)

    files_created = []
    files_modified = []

    # Generate and optionally inject frontend code
    if project_info.frontend == 'react':
        interceptor_code = FRONTEND_TEMPLATES['react']['interceptor']
        interceptor_file = generated_dir / 'api-interceptor.js'
        interceptor_file.write_text(interceptor_code)
        files_created.append(str(interceptor_file))

        if auto_inject:
            # Try to inject into main React files
            react_files = _find_react_entry_files(project_dir)
            for react_file in react_files:
                if _inject_react_interceptor(react_file, interceptor_code):
                    files_modified.append(str(react_file))

    # Generate and optionally inject backend code
    if project_info.backend in ['fastapi', 'flask']:
        middleware_code = BACKEND_TEMPLATES[project_info.backend]['middleware']
        middleware_file = generated_dir / 'api_middleware.py'
        middleware_file.write_text(middleware_code)
        files_created.append(str(middleware_file))

        if auto_inject:
            # Try to inject into main app files
            app_files = _find_app_entry_files(project_dir, project_info.backend)
            for app_file in app_files:
                if _inject_backend_middleware(app_file, project_info.backend):
                    files_modified.append(str(app_file))

    # Update requirements/dependencies if auto-inject is enabled
    if auto_inject:
        if project_info.backend:
            _update_python_requirements(project_dir)
        if project_info.frontend:
            _update_package_json(project_dir)

    # Generate integration instructions
    instructions = generate_integration_instructions(project_info, auto_inject, files_modified)
    instructions_file = generated_dir / 'INTEGRATION.md'
    instructions_file.write_text(instructions)
    files_created.append(str(instructions_file))

    return files_created + files_modified


def setup_integration_automatically(project_info: ProjectInfo, project_path: str) -> dict:
    """Automatically integrate API diagnostics into the project"""
    results = {
        'success': True,
        'files_created': [],
        'files_modified': [],
        'errors': []
    }

    try:
        # Generate files and inject code
        all_files = setup_integration(project_info, project_path, auto_inject=True)

        # Separate created vs modified files
        generated_dir = Path(project_path) / '.api-diagnostics' / 'generated'
        for file_path in all_files:
            if str(generated_dir) in file_path:
                results['files_created'].append(file_path)
            else:
                results['files_modified'].append(file_path)

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))

    return results


def remove_integration(project_path: str) -> None:
    """Remove all generated integration code"""
    project_dir = Path(project_path)
    diagnostics_dir = project_dir / '.api-diagnostics'

    if diagnostics_dir.exists():
        import shutil
        shutil.rmtree(diagnostics_dir)
        print(f'Removed {diagnostics_dir}')
    else:
        print('No integration found to remove')


def generate_integration_instructions(project_info: ProjectInfo) -> str:
    """Generate step-by-step integration instructions"""
    instructions = ["# API Diagnostics Integration Instructions\n"]

    if project_info.frontend == 'react':
        instructions.extend([
            "## Frontend Setup (React)",
            "1. Copy `api-interceptor.js` to your `src/` directory",
            "2. Import it in your main App.js or index.js:",
            "   ```javascript",
            "   import './api-interceptor.js';",
            "   ```",
            "3. That's it! All fetch() calls will now include correlation IDs\n"
        ])

    if project_info.backend in ['fastapi', 'flask']:
        framework = project_info.backend.title()
        instructions.extend([
            f"## Backend Setup ({framework})",
            "1. Copy `api_middleware.py` to your project directory",
            "2. Import and add the middleware to your app:",
        ])

        if project_info.backend == 'fastapi':
            instructions.extend([
                "   ```python",
                "   from api_middleware import APIDebugMiddleware",
                "   app.add_middleware(APIDebugMiddleware)",
                "   ```"
            ])
        else:  # flask
            instructions.extend([
                "   ```python",
                "   from api_middleware import FlaskAPIDebugger",
                "   debugger = FlaskAPIDebugger(app)",
                "   ```",
                "   Or for more control:",
                "   ```python",
                "   from api_middleware import FlaskAPIDebugger",
                "   debugger = FlaskAPIDebugger()",
                "   debugger.init_app(app)",
                "   ```"
            ])

        instructions.append("3. Restart your server\n")

    instructions.extend([
        "## Usage",
        "1. Run `api-diagnostics start` to enable monitoring",
        "2. Make API calls from your frontend",
        "3. Check browser console for correlation IDs",
        "4. Search backend logs with `api-diagnostics search <correlation-id>`"
    ])

    return "\n".join(instructions)


def backup_file(file_path: str) -> str:
    """Create backup before modifying files"""
    from datetime import datetime
    import shutil

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup_{timestamp}")

    shutil.copy2(file_path, backup_path)
    return str(backup_path)


def restore_from_backup(file_path: str, backup_path: str = None) -> bool:
    """Restore file from backup"""
    import shutil

    file_path = Path(file_path)

    if backup_path:
        backup_path = Path(backup_path)
    else:
        # Find the most recent backup
        backup_pattern = f"{file_path.name}.backup_*"
        backup_files = list(file_path.parent.glob(backup_pattern))

        if not backup_files:
            return False

        # Get the most recent backup
        backup_path = max(backup_files, key=lambda p: p.stat().st_mtime)

    if not backup_path.exists():
        return False

    shutil.copy2(backup_path, file_path)
    return True


def inject_code_safely(file_path: str, code: str, position: str = 'top',
                      marker: str = None, check_existing: bool = True) -> bool:
    """Safely inject code into existing files with validation"""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist")

    # Read current file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            original_content = f.read()

    # Check if code already exists (avoid duplicates)
    if check_existing and code.strip() in original_content:
        return False  # Code already exists

    # Create marker comments for tracking injected code
    if not marker:
        marker = "api_diagnostics_injection"

    start_marker = f"# START {marker} - Auto-generated by API Diagnostics"
    end_marker = f"# END {marker}"

    # Check if our injection already exists
    if start_marker in original_content:
        return False  # Already injected

    # Prepare the code with markers
    injected_code = f"{start_marker}\n{code}\n{end_marker}\n"

    # Create backup before modifying
    backup_path = backup_file(file_path)

    try:
        # Inject code based on position
        if position == 'top':
            new_content = injected_code + original_content
        elif position == 'bottom':
            new_content = original_content + "\n" + injected_code
        elif position == 'after_imports':
            new_content = _inject_after_imports(original_content, injected_code)
        else:
            raise ValueError(f"Unknown position: {position}")

        # Validate the new content (basic syntax check for Python files)
        if file_path.suffix == '.py':
            if not _validate_python_syntax(new_content):
                # Restore from backup if syntax is invalid
                restore_from_backup(file_path, backup_path)
                return False

        # Write the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        # Restore from backup on any error
        restore_from_backup(file_path, backup_path)
        raise e


def remove_injected_code(file_path: str, marker: str = None) -> bool:
    """Remove previously injected code using markers"""
    file_path = Path(file_path)

    if not file_path.exists():
        return False

    if not marker:
        marker = "api_diagnostics_injection"

    start_marker = f"# START {marker} - Auto-generated by API Diagnostics"
    end_marker = f"# END {marker}"

    # Read current content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if injection exists
    if start_marker not in content:
        return False  # Nothing to remove

    # Create backup before modifying
    backup_path = backup_file(file_path)

    try:
        # Remove the injected code block
        lines = content.split('\n')
        new_lines = []
        skip_lines = False

        for line in lines:
            if start_marker in line:
                skip_lines = True
                continue
            elif end_marker in line:
                skip_lines = False
                continue
            elif not skip_lines:
                new_lines.append(line)

        # Write the cleaned content
        new_content = '\n'.join(new_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    except Exception as e:
        # Restore from backup on error
        restore_from_backup(file_path, backup_path)
        raise e


def _inject_after_imports(content: str, injected_code: str) -> str:
    """Inject code after import statements in Python files"""
    lines = content.split('\n')
    inject_line = 0

    # Find the last import statement
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            inject_line = i + 1
        elif stripped and not stripped.startswith('#') and inject_line > 0:
            # Found first non-import, non-comment line after imports
            break

    # Insert the injected code after imports
    lines.insert(inject_line, injected_code.rstrip())
    return '\n'.join(lines)


def _validate_python_syntax(code: str) -> bool:
    """Validate Python syntax without executing the code"""
    import ast

    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def get_backup_files(file_path: str) -> List[str]:
    """Get list of backup files for a given file"""
    file_path = Path(file_path)
    backup_pattern = f"{file_path.name}.backup_*"
    backup_files = list(file_path.parent.glob(backup_pattern))

    # Sort by modification time (newest first)
    backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return [str(p) for p in backup_files]


def clean_old_backups(file_path: str, keep_count: int = 5) -> int:
    """Clean old backup files, keeping only the most recent ones"""
    backup_files = get_backup_files(file_path)

    if len(backup_files) <= keep_count:
        return 0

    # Remove old backups
    removed_count = 0
    for backup_file in backup_files[keep_count:]:
        try:
            Path(backup_file).unlink()
            removed_count += 1
        except OSError:
            pass

    return removed_count


def _find_react_entry_files(project_dir: Path) -> List[Path]:
    """Find main React entry files for injection"""
    possible_files = [
        'src/index.js',
        'src/index.tsx',
        'src/App.js',
        'src/App.tsx',
        'index.js',
        'App.js'
    ]

    found_files = []
    for file_path in possible_files:
        full_path = project_dir / file_path
        if full_path.exists():
            found_files.append(full_path)

    return found_files


def _find_app_entry_files(project_dir: Path, framework: str) -> List[Path]:
    """Find main application files for backend injection"""
    if framework == 'fastapi':
        possible_files = [
            'main.py',
            'app.py',
            'src/main.py',
            'src/app.py',
            'api/main.py',
            'api/app.py'
        ]
    elif framework == 'flask':
        possible_files = [
            'app.py',
            'main.py',
            'src/app.py',
            'src/main.py',
            'flask_app.py',
            'application.py'
        ]
    else:
        return []

    found_files = []
    for file_path in possible_files:
        full_path = project_dir / file_path
        if full_path.exists():
            # Check if it actually contains the framework
            try:
                content = full_path.read_text()
                if framework.lower() in content.lower():
                    found_files.append(full_path)
            except (UnicodeDecodeError, PermissionError):
                continue

    return found_files


def _inject_react_interceptor(react_file: Path, interceptor_code: str) -> bool:
    """Inject React interceptor into a React file"""
    try:
        # Create a simple import statement for the interceptor
        import_code = "import './api-interceptor.js';"

        # Inject the import at the top of the file
        return inject_code_safely(
            str(react_file),
            import_code,
            position='after_imports',
            marker='react_interceptor'
        )
    except Exception:
        return False


def _inject_backend_middleware(app_file: Path, framework: str) -> bool:
    """Inject backend middleware into the main app file"""
    try:
        if framework == 'fastapi':
            middleware_code = '''
# API Diagnostics Integration
from api_middleware import APIDebugMiddleware
app.add_middleware(APIDebugMiddleware)
'''
        elif framework == 'flask':
            middleware_code = '''
# API Diagnostics Integration
from api_middleware import FlaskAPIDebugger
debugger = FlaskAPIDebugger(app)
'''
        else:
            return False

        # Inject after the app creation
        return inject_code_safely(
            str(app_file),
            middleware_code,
            position='after_imports',
            marker=f'{framework}_middleware'
        )
    except Exception:
        return False


def _update_python_requirements(project_dir: Path) -> bool:
    """Add required dependencies to requirements.txt"""
    requirements_file = project_dir / 'requirements.txt'

    # Dependencies needed for our middleware
    new_deps = [
        'uuid',  # For correlation ID generation
    ]

    try:
        if requirements_file.exists():
            current_content = requirements_file.read_text()
        else:
            current_content = ""

        # Check which dependencies are missing
        missing_deps = []
        for dep in new_deps:
            if dep not in current_content:
                missing_deps.append(dep)

        if missing_deps:
            # Add missing dependencies
            new_content = current_content
            if not new_content.endswith('\n') and new_content:
                new_content += '\n'

            new_content += '\n# API Diagnostics dependencies\n'
            for dep in missing_deps:
                new_content += f'{dep}\n'

            # Create backup and write
            if requirements_file.exists():
                backup_file(str(requirements_file))

            requirements_file.write_text(new_content)
            return True

    except Exception:
        return False

    return False


def _update_package_json(project_dir: Path) -> bool:
    """Add required dependencies to package.json"""
    package_json = project_dir / 'package.json'

    if not package_json.exists():
        return False

    try:
        import json

        # Read current package.json
        with open(package_json, 'r') as f:
            package_data = json.load(f)

        # Dependencies we might need (most are already in React projects)
        new_deps = {
            # Most React projects already have these, but just in case
        }

        # Check if we need to add any dependencies
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})

        needs_update = False
        for dep, version in new_deps.items():
            if dep not in dependencies and dep not in dev_dependencies:
                dependencies[dep] = version
                needs_update = True

        if needs_update:
            # Create backup and update
            backup_file(str(package_json))

            package_data['dependencies'] = dependencies
            with open(package_json, 'w') as f:
                json.dump(package_data, f, indent=2)

            return True

    except Exception:
        return False

    return False


def remove_integration_automatically(project_path: str) -> dict:
    """Automatically remove API diagnostics integration from the project"""
    results = {
        'success': True,
        'files_restored': [],
        'files_removed': [],
        'errors': []
    }

    project_dir = Path(project_path)

    try:
        # Remove injected code from common file locations
        possible_files = [
            # React files
            'src/index.js', 'src/index.tsx', 'src/App.js', 'src/App.tsx',
            # Backend files
            'main.py', 'app.py', 'src/main.py', 'src/app.py',
            'flask_app.py', 'application.py'
        ]

        for file_path in possible_files:
            full_path = project_dir / file_path
            if full_path.exists():
                # Try to remove different types of injections
                markers = ['react_interceptor', 'fastapi_middleware', 'flask_middleware', 'api_diagnostics_injection']
                for marker in markers:
                    if remove_injected_code(str(full_path), marker):
                        results['files_restored'].append(str(full_path))

        # Remove the .api-diagnostics directory
        diagnostics_dir = project_dir / '.api-diagnostics'
        if diagnostics_dir.exists():
            import shutil
            shutil.rmtree(diagnostics_dir)
            results['files_removed'].append(str(diagnostics_dir))

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))

    return results


def generate_integration_instructions(project_info: ProjectInfo, auto_injected: bool = False,
                                    modified_files: List[str] = None) -> str:
    """Generate updated integration instructions"""
    if modified_files is None:
        modified_files = []

    instructions = ["# API Diagnostics Integration Instructions\n"]

    if auto_injected:
        instructions.extend([
            "## ✅ Automatic Integration Complete!",
            "",
            "API Diagnostics has been automatically integrated into your project.",
            ""
        ])

        if modified_files:
            instructions.extend([
                "### Files Modified:",
                ""
            ])
            for file_path in modified_files:
                instructions.append(f"- `{file_path}`")
            instructions.append("")

        instructions.extend([
            "### Next Steps:",
            "1. Run `api-diagnostics start` to enable monitoring",
            "2. Start your application normally",
            "3. Make API calls and check browser console for correlation IDs",
            "4. Use `api-diagnostics search <correlation-id>` to find backend errors",
            "",
            "### To Remove Integration:",
            "Run `api-diagnostics clean` to automatically remove all injected code.",
            ""
        ])

    else:
        # Original manual instructions
        if project_info.frontend == 'react':
            instructions.extend([
                "## Frontend Setup (React)",
                "1. Copy `api-interceptor.js` to your `src/` directory",
                "2. Import it in your main App.js or index.js:",
                "   ```javascript",
                "   import './api-interceptor.js';",
                "   ```",
                "3. That's it! All fetch() calls will now include correlation IDs\n"
            ])

        if project_info.backend in ['fastapi', 'flask']:
            framework = project_info.backend.title()
            instructions.extend([
                f"## Backend Setup ({framework})",
                "1. Copy `api_middleware.py` to your project directory",
                "2. Import and add the middleware to your app:",
            ])

            if project_info.backend == 'fastapi':
                instructions.extend([
                    "   ```python",
                    "   from api_middleware import APIDebugMiddleware",
                    "   app.add_middleware(APIDebugMiddleware)",
                    "   ```"
                ])
            else:  # flask
                instructions.extend([
                    "   ```python",
                    "   from api_middleware import FlaskAPIDebugger",
                    "   debugger = FlaskAPIDebugger(app)",
                    "   ```"
                ])

            instructions.append("3. Restart your server\n")

        instructions.extend([
            "## Usage",
            "1. Run `api-diagnostics start` to enable monitoring",
            "2. Make API calls from your frontend",
            "3. Check browser console for correlation IDs",
            "4. Search backend logs with `api-diagnostics search <correlation-id>`"
        ])

    return "\n".join(instructions)
