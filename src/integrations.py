"""
Framework Integration and Project Detection
Handles detection of different frameworks and auto-configuration
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
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


class ProjectConfigurator:
    @staticmethod
    def setup_integration(project_info: ProjectInfo, project_path: str) -> None:
        """Generate configuration files and inject code"""
        # TODO: Generate configuration files
        # TODO: Inject middleware code
        # TODO: Setup frontend interceptors
        print(f'Setting up integration for: {project_info}')

    @staticmethod
    def remove_integration(project_path: str) -> None:
        """Remove all injected code"""
        # TODO: Remove all injected code
        # TODO: Restore original files from backup
        print('Removing integration...')


class FileManager:
    @staticmethod
    def backup_file(file_path: str) -> None:
        """Create backup before modifying files"""
        # TODO: Create backup before modifying files
        pass

    @staticmethod
    def inject_code(file_path: str, code: str, position: str = 'top') -> None:
        """Safely inject code into existing files"""
        # TODO: Safely inject code into existing files
        pass

    @staticmethod
    def restore_from_backup(file_path: str) -> None:
        """Restore file from backup"""
        # TODO: Restore file from backup
        pass
