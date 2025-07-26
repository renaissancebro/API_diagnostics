# API Diagnostics - Development Notes

## The Big Picture: How This Tool Works

### What We're Building

A CLI tool that automatically adds debugging superpowers to any web project. When you get a 400/500 error, instead of hunting through logs, you get instant correlation between frontend errors and backend code locations.

### The Complete Flow (User Perspective)

1. **Developer has a project** (React frontend + FastAPI backend)
2. **Runs `api-diagnostics init`** in their project folder
3. **Tool detects frameworks** automatically ("Oh, this is React + FastAPI")
4. **Tool injects monitoring code** into their existing files
5. **Developer runs `api-diagnostics start`** to enable monitoring
6. **Developer clicks button in their app** → API call fails with 400 error
7. **Enhanced error appears in browser console** with correlation ID `abc123`
8. **Developer runs `api-diagnostics search abc123`**
9. **Tool shows exact backend file/line** where error occurred

### The Technical Flow (How Code Works)

```
User clicks button → Frontend interceptor adds correlation ID →
Backend middleware catches error → Both log with same ID →
Developer searches by ID → Finds exact error location
```

## Key Python Concepts You Need

### 1. pathlib.Path - Modern File Handling

```python
from pathlib import Path

# Create path objects (like file/folder references)
project_dir = Path('.')                    # Current directory
config_file = project_dir / 'config.json' # Join paths with /
package_json = Path('package.json')        # Specific file

# Check if things exist
if config_file.exists():                   # Does file exist?
    print("Config found!")

if project_dir.is_dir():                   # Is it a directory?
    print("It's a folder!")

# Read/write files easily
content = config_file.read_text()          # Read entire file
config_file.write_text('{"enabled": true}') # Write to file

# Create directories
logs_dir = Path('logs')
logs_dir.mkdir(exist_ok=True)              # Create if doesn't exist

# Find files recursively
for py_file in project_dir.rglob('*.py'):  # All .py files in subdirs
    print(f"Found Python file: {py_file}")
```

### 2. JSON Handling

```python
import json

# Read JSON file
with open('package.json') as f:
    data = json.load(f)                    # Parse JSON to Python dict

# Or with pathlib
data = json.loads(Path('package.json').read_text())

# Access nested data
dependencies = data.get('dependencies', {})  # Get deps or empty dict
if 'react' in dependencies:
    print("This is a React project!")

# Write JSON
config = {"enabled": True, "log_level": "ERROR"}
Path('config.json').write_text(json.dumps(config, indent=2))
```

### 3. Click CLI Framework

```python
import click

@click.group()                             # Main command group
def cli():
    """My CLI tool description"""
    pass

@cli.command()                             # Subcommand
@click.argument('project_path', default='.')  # Required argument with default
def init(project_path):
    """Initialize the tool"""
    click.echo(f"Setting up in {project_path}")  # Print to user

@cli.command()
@click.option('--verbose', is_flag=True)   # Optional flag
def start(verbose):
    """Start monitoring"""
    if verbose:
        click.echo("Verbose mode enabled")
```

## How Each Component Works

### 1. Framework Detection (src/integrations.py)

**Goal**: Figure out what kind of project this is

**Process**:

1. Look for `package.json` → Check dependencies for React/Vue
2. Look for `*.py` files → Check imports for FastAPI/Flask
3. Return project info: "React + FastAPI project"

**Key functions**:

- `detect_frontend_framework()` - Checks package.json
- `detect_backend_framework()` - Checks Python imports
- `detect_project()` - Combines both

### 2. Code Injection (src/templates.py)

**Goal**: Add monitoring code to existing project files

**Process**:

1. Read template code (JavaScript interceptor, Python middleware)
2. Inject into existing files safely
3. Create backup files first

**Templates**:

- Frontend: JavaScript that wraps fetch() calls
- Backend: Python middleware that logs requests

### 3. CLI Commands (src/commands.py)

**Goal**: User interface for the tool

**Commands**:

- `init` - Detect project, create config, inject code
- `start` - Enable monitoring
- `search` - Find logs by correlation ID
- `status` - Show if monitoring is active

### 4. Core Logic (src/core.py)

**Goal**: Handle correlation IDs and log processing

**Functions**:

- Generate unique IDs for each request
- Format log entries consistently
- Search logs by correlation ID

## The Missing Pieces (Why It's Confusing)

### 1. File Detection Logic

```python
# How do you know it's a React project?
def detect_react(project_path):
    package_json = Path(project_path) / 'package.json'

    if not package_json.exists():
        return False

    # Read and parse JSON
    data = json.loads(package_json.read_text())

    # Check both regular and dev dependencies
    all_deps = {
        **data.get('dependencies', {}),
        **data.get('devDependencies', {})
    }

    return 'react' in all_deps
```

### 2. Code Injection Process

```python
# How do you safely add code to existing files?
def inject_monitoring_code(file_path, code_to_add):
    # 1. Backup original file
    backup_path = Path(f"{file_path}.backup")
    original_content = Path(file_path).read_text()
    backup_path.write_text(original_content)

    # 2. Add our code at the top
    new_content = code_to_add + "\n\n" + original_content
    Path(file_path).write_text(new_content)
```

### 3. Configuration Management

```python
# How do you store tool settings?
def save_config(project_path, config):
    config_dir = Path(project_path) / '.api-diagnostics'
    config_dir.mkdir(exist_ok=True)

    config_file = config_dir / 'config.json'
    config_file.write_text(json.dumps(config, indent=2))
```

## Common Patterns You'll Use

### 1. Check if something exists before using it

```python
config_dir = Path('.api-diagnostics')
if not config_dir.exists():
    click.echo("Not initialized. Run 'init' first")
    return
```

### 2. Try/except for file operations

```python
try:
    data = json.loads(Path('package.json').read_text())
except (FileNotFoundError, json.JSONDecodeError):
    click.echo("Invalid or missing package.json")
    return
```

### 3. Iterate through files

```python
for py_file in Path('.').rglob('*.py'):
    content = py_file.read_text()
    if 'from fastapi import' in content:
        return 'fastapi'
```

## Next Steps for Task 2.1

1. **Complete `detect_backend_framework()`**:

   - Find all .py files in project
   - Read each file and check for framework imports
   - Return 'fastapi', 'flask', 'django', or None

2. **Test the detection**:

   - Create a simple test project with FastAPI
   - Run your detection function
   - Make sure it correctly identifies FastAPI

3. **Handle edge cases**:
   - What if no package.json exists?
   - What if Python files can't be read?
   - What if multiple frameworks are detected?

The key insight: **This is all just file reading and pattern matching**. You're looking for clues in files to determine what kind of project it is, then acting accordingly.

## Framework Detection - Detailed Breakdown

### Frontend Detection (React)

**Which file to look in:** `package.json` (always in project root)

**What package.json looks like:**

```json
{
  "name": "my-react-app",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "typescript": "^4.9.0"
  }
}
```

**Why this works:** Every React project MUST have these packages to function. It's like checking if someone has a driver's license to know they can drive.

**The detection logic:**

```python
# Read the JSON file
package_data = json.load(file)

# Get both types of dependencies
all_deps = {
    **package_data.get('dependencies', {}),      # Runtime dependencies
    **package_data.get('devDependencies', {})   # Development dependencies
}

# Check if any React packages exist
react_packages = ['react', 'react-dom', '@types/react']
if any(pkg in all_deps for pkg in react_packages):
    return 'react'
```

### Backend Detection (FastAPI/Flask)

**Which files to look in:** ALL `.py` files in the project (using glob)

**What FastAPI files look like:**

```python
# main.py or app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/users/")
def create_user(user: User):
    return user
```

**What Flask files look like:**

```python
# app.py or main.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/users', methods=['POST'])
def create_user():
    return jsonify({"status": "created"})
```

**The detection patterns I look for:**

- FastAPI: `from fastapi import`, `FastAPI()`, `@app.get`, `@app.post`
- Flask: `from flask import`, `Flask(__name__)`, `@app.route`

## The glob Function - Finding Files in Python

### What is glob?

`glob` finds files that match a pattern. Think of it like a search function for your file system.

### Basic glob patterns:

```python
from pathlib import Path

project_dir = Path('.')

# Find all Python files in current directory only
py_files = list(project_dir.glob('*.py'))
# Result: ['main.py', 'app.py', 'config.py']

# Find all Python files in ALL subdirectories (recursive)
all_py_files = list(project_dir.rglob('*.py'))
# Result: ['main.py', 'src/app.py', 'tests/test_main.py', 'utils/helpers.py']

# Find all JSON files
json_files = list(project_dir.glob('*.json'))
# Result: ['package.json', 'config.json']

# Find files in specific subdirectory
src_files = list(project_dir.glob('src/*.py'))
# Result: ['src/main.py', 'src/utils.py']
```

### Common glob patterns:

- `*.py` - All Python files
- `*.json` - All JSON files
- `**/*.py` - All Python files in any subdirectory
- `src/*.py` - Python files only in src folder
- `test_*.py` - Files starting with "test\_"

### How I used rglob in the detection:

```python
# This finds EVERY .py file in the project, no matter how deep
for py_file in project_dir.rglob('*.py'):
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if this file has FastAPI imports
        if 'from fastapi import' in content:
            return 'fastapi'

    except (UnicodeDecodeError, PermissionError):
        continue  # Skip files we can't read
```

### Why rglob instead of glob?

- `glob('*.py')` - Only finds files in current directory
- `rglob('*.py')` - Finds files in current directory AND all subdirectories

**Example project structure:**

```
my-project/
├── main.py              # glob finds this
├── config.py            # glob finds this
├── src/
│   ├── app.py          # only rglob finds this
│   └── models.py       # only rglob finds this
└── tests/
    └── test_app.py     # only rglob finds this
```

### Practical glob examples:

```python
from pathlib import Path

project = Path('.')

# Find all requirements files
req_files = list(project.rglob('requirements*.txt'))
# Finds: requirements.txt, requirements-dev.txt, etc.

# Find all test files
test_files = list(project.rglob('test_*.py'))
# Finds: test_main.py, tests/test_app.py, etc.

# Find all config files
config_files = list(project.rglob('config.*'))
# Finds: config.json, config.yaml, src/config.py, etc.

# Check if any files match
if any(project.rglob('*.py')):
    print("This is a Python project!")
```

### Error handling with glob:

```python
for py_file in project_dir.rglob('*.py'):
    try:
        content = py_file.read_text(encoding='utf-8')
        # Process the file
    except UnicodeDecodeError:
        # Skip binary files or files with weird encoding
        continue
    except PermissionError:
        # Skip files we don't have permission to read
        continue
    except OSError:
        # Skip any other file system errors
        continue
```

The key insight: **glob is like a smart search that finds files matching patterns**. Instead of manually checking every folder, you tell it "find all .py files everywhere" and it does the work for you!

## Classes vs Functions - When to Use What

### The Question: Why did I use `ProjectDetector` class?

**Honest answer:** I could have just used simple functions. Let me show you both approaches:

### Approach 1: Class-based (what I did)

```python
class ProjectDetector:
    @staticmethod
    def detect_project(path):
        # detection logic
        pass

    @staticmethod
    def detect_frontend_framework(path):
        # frontend detection
        pass

# Usage
project_info = ProjectDetector.detect_project('.')
```

### Approach 2: Simple functions (probably better here)

```python
def detect_project(path):
    # detection logic
    pass

def detect_frontend_framework(path):
    # frontend detection
    pass

# Usage
project_info = detect_project('.')
```

### When to Use Classes vs Functions

#### Use **Functions** when:

- You have independent operations
- No shared state between operations
- Simple input → output transformations
- **This detection code fits here!**

#### Use **Classes** when:

- You need to store data (state) between method calls
- You have related methods that work on the same data
- You need multiple instances with different configurations

### Real Examples:

#### Good use of Functions (like our detection):

```python
# Each function is independent, just processes input and returns result
def detect_react_project(path):
    package_json = Path(path) / 'package.json'
    if package_json.exists():
        data = json.loads(package_json.read_text())
        deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
        return 'react' in deps
    return False

def detect_fastapi_project(path):
    for py_file in Path(path).rglob('*.py'):
        content = py_file.read_text()
        if 'from fastapi import' in content:
            return True
    return False

# Usage - simple and clear
is_react = detect_react_project('.')
is_fastapi = detect_fastapi_project('.')
```

#### Good use of Classes (when you need state):

```python
class LogSearcher:
    def __init__(self, log_path, correlation_id):
        self.log_path = log_path
        self.correlation_id = correlation_id
        self.cached_results = None  # Store results between calls

    def search(self):
        if self.cached_results is None:
            # Do expensive search operation
            self.cached_results = self._search_logs()
        return self.cached_results

    def filter_by_error_type(self, error_type):
        results = self.search()  # Uses cached results
        return [r for r in results if r.status_code.startswith(error_type)]

# Usage - the class remembers the log_path and correlation_id
searcher = LogSearcher('/var/log/app.log', 'abc123')
all_results = searcher.search()
errors_400 = searcher.filter_by_error_type('400')
```

### Dataclasses - When to Use Them

#### What is a dataclass?

A simple way to create a class that just holds data (like a fancy dictionary).

#### Instead of this (messy):

```python
# Using a dictionary - easy to make mistakes
project_info = {
    'type': 'fullstack',
    'frontend': 'react',
    'backend': 'fastapi',
    'package_manager': 'npm'
}

# Easy to make typos
if project_info['frontned'] == 'react':  # Oops! Typo
    print("React project")
```

#### Use this (clean):

```python
from dataclasses import dataclass

@dataclass
class ProjectInfo:
    type: str
    frontend: str = None
    backend: str = None
    package_manager: str = 'pip'

# Usage - IDE can catch typos
project_info = ProjectInfo(
    type='fullstack',
    frontend='react',
    backend='fastapi',
    package_manager='npm'
)

# IDE will warn you about typos
if project_info.frontend == 'react':  # IDE knows this field exists
    print("React project")
```

### Better Approach for Our Detection Code

**Instead of the class I created, this would be cleaner:**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProjectInfo:
    type: str
    frontend: Optional[str] = None
    backend: Optional[str] = None
    package_manager: str = 'pip'

def detect_frontend_framework(project_path: str) -> Optional[str]:
    """Check for React in package.json"""
    package_json = Path(project_path) / 'package.json'
    if not package_json.exists():
        return None

    try:
        data = json.loads(package_json.read_text())
        deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
        if any(pkg in deps for pkg in ['react', 'react-dom', '@types/react']):
            return 'react'
    except (json.JSONDecodeError, FileNotFoundError):
        pass

    return None

def detect_backend_framework(project_path: str) -> Optional[str]:
    """Check for FastAPI/Flask in Python files"""
    for py_file in Path(project_path).rglob('*.py'):
        try:
            content = py_file.read_text(encoding='utf-8')
            if any(pattern in content for pattern in ['from fastapi import', 'FastAPI()']):
                return 'fastapi'
            elif any(pattern in content for pattern in ['from flask import', 'Flask(__name__)']):
                return 'flask'
        except (UnicodeDecodeError, PermissionError):
            continue
    return None

def detect_project(project_path: str = '.') -> Optional[ProjectInfo]:
    """Detect project type and frameworks"""
    frontend = detect_frontend_framework(project_path)
    backend = detect_backend_framework(project_path)

    if not frontend and not backend:
        return None

    if frontend and backend:
        project_type = 'fullstack'
    elif frontend:
        project_type = 'frontend'
    else:
        project_type = 'backend'

    package_manager = 'npm' if frontend else 'pip'

    return ProjectInfo(
        type=project_type,
        frontend=frontend,
        backend=backend,
        package_manager=package_manager
    )

# Usage - simple and clear
project_info = detect_project('.')
if project_info and project_info.frontend == 'react':
    print("Found React project!")
```

### Summary:

- **Functions**: Use for independent operations (like our detection)
- **Classes**: Use when you need to store state or have related methods
- **Dataclasses**: Use instead of dictionaries when you want structure and type safety

**For our detection code, simple functions + dataclass would be cleaner than the class approach I used.**
