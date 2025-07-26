# API Diagnostics

A powerful CLI tool for debugging API calls with correlation tracking. Automatically links frontend errors to exact backend code locations, making API debugging fast and efficient.

## Features

### 🔍 **Correlation Tracking**

- Unique correlation IDs for every API request
- Links frontend errors to exact backend code locations
- Enhanced browser console logging with search commands

### 🚀 **Automatic Integration**

- One-command setup: `api-diagnostics init --auto`
- Supports React, FastAPI, and Flask projects
- Safe code injection with automatic backups
- Complete removal with `api-diagnostics clean`

### 🛠️ **Developer Experience**

- Beautiful console logging with emojis and formatting
- Multiple output formats (human, JSON, compact)
- Smart log search and filtering
- Real-time error correlation

### 🔒 **Production Ready**

- Comprehensive error handling and recovery
- Syntax validation prevents breaking code
- Automatic backup and rollback system
- Extensive test coverage

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

### Quick Start (Automatic Integration)

```bash
# Automatically integrate into your project
./api-diagnostics init --auto

# Enable monitoring
./api-diagnostics start

# Your app now has correlation tracking!
# Check browser console for correlation IDs when errors occur
```

### Manual Integration

```bash
# Generate integration templates
./api-diagnostics init

# Follow instructions in .api-diagnostics/generated/INTEGRATION.md
# Then enable monitoring
./api-diagnostics start
```

### Debugging Workflow

```bash
# When you see an error in browser console with correlation ID:
./api-diagnostics search abc123-def456-ghi789

# View recent errors
./api-diagnostics errors --type 400

# View all recent activity
./api-diagnostics recent --hours 2
```

### Cleanup

```bash
# Remove all integration code
./api-diagnostics clean
```

## How It Works

1. **Frontend Interceptor** - Automatically adds correlation IDs to all API requests
2. **Backend Middleware** - Logs requests with correlation IDs and detailed error info
3. **CLI Search** - Instantly find backend errors using correlation IDs from browser console
4. **Smart Integration** - One command setup with automatic code injection

## Example Workflow

```bash
# 1. Set up in your project
./api-diagnostics init --auto

# 2. Enable monitoring
./api-diagnostics start

# 3. When you see this in browser console:
# ❌ [abc12345] 404 User not found

# 4. Find the exact backend error:
./api-diagnostics search abc12345

# Output:
# ✅ Found 1 log entries:
# ❌ [abc12345] POST /api/users
#    Status: 404
#    Error: User not found
#    File: /app/routes/users.py:45
#    Stack Trace: UserNotFoundError...
```

## Supported Frameworks

- **Frontend**: React (Vue and Angular coming soon)
- **Backend**: FastAPI, Flask (Django and Express coming soon)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/renaissancebro/API_diagnostics/issues)
- 📖 **Documentation**: See `.api-diagnostics/generated/INTEGRATION.md` after running `init`
- 💬 **Discussions**: [GitHub Discussions](https://github.com/renaissancebro/API_diagnostics/discussions)

---

**Made with ❤️ by developers, for developers**
