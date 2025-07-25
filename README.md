# API Diagnostics

A debugging tool for backend developers working with frontend API calls. Helps quickly identify and trace 400/500 errors from browser dev tools back to specific code locations and backend issues.

## Features

- Enhanced error logging with stack traces
- Request/response correlation tracking
- Automatic error categorization (400 vs 500)
- Source code location mapping
- Integration with browser dev tools

## Project Structure

```
api-diagnostics/
├── src/
│   ├── commands.py          # All CLI commands (init, start, search, etc.)
│   ├── core.py             # Correlation IDs, logging, main logic
│   ├── integrations.py     # Project detection & framework setup
│   └── templates.py        # Code that gets injected into projects
├── tests/
│   └── test_core.py        # Start with testing core functionality
├── specs/                  # Design documentation
│   ├── design.md
│   ├── requirements.md
│   └── tasks.md
├── api-diagnostics         # CLI entry point script
├── requirements.txt
├── setup.py
└── README.md
```

## Architecture

**File Responsibilities:**

- **`commands.py`** - CLI interface using Click library
- **`core.py`** - Pure business logic (correlation IDs, logging)
- **`integrations.py`** - Framework detection and project setup
- **`templates.py`** - Code templates for injection into projects

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd api-diagnostics

# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x api-diagnostics
```

## Usage

```bash
# Initialize in any project
./api-diagnostics init

# Start monitoring
./api-diagnostics start

# Search logs by correlation ID
./api-diagnostics search abc123-def456-ghi789

# Check status
./api-diagnostics status
```
