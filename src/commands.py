"""
CLI Commands for API Diagnostics Tool
Handles user interaction and command parsing
"""

import click
from pathlib import Path


@click.group()
def cli():
    """API Diagnostics - Debug API calls with correlation tracking"""
    pass


@cli.command()
@click.argument('project_path', default='.')
def init(project_path):
    """Initialize API diagnostics in a project"""
    import json
    from integrations import detect_project, setup_integration

    project_dir = Path(project_path)

    # Check if directory exists
    if not project_dir.exists():
        click.echo(f"Error: Directory {project_path} does not exist")
        return

    # Detect project frameworks
    click.echo("🔍 Detecting project frameworks...")
    project_info = detect_project(project_path)

    if project_info:
        click.echo(f"   Project type: {project_info.type}")
        if project_info.frontend:
            click.echo(f"   Frontend: {project_info.frontend}")
        if project_info.backend:
            click.echo(f"   Backend: {project_info.backend}")
        click.echo(f"   Package manager: {project_info.package_manager}")
    else:
        click.echo("   ⚠️  No supported frameworks detected (React, FastAPI, Flask)")
        click.echo("   Continuing with basic setup...")

    # Create config directory
    config_dir = project_dir / '.api-diagnostics'
    config_dir.mkdir(exist_ok=True)  # Creates directory, doesn't fail if exists

    # Create config file with detected info
    config_content = {
        "enabled": False,
        "log_level": "ERROR",
        "project_info": {
            "type": project_info.type if project_info else "unknown",
            "frontend": project_info.frontend if project_info else None,
            "backend": project_info.backend if project_info else None,
            "package_manager": project_info.package_manager if project_info else "pip"
        }
    }

    config_file = config_dir / 'config.json'
    config_file.write_text(json.dumps(config_content, indent=2))

    # Generate integration code if frameworks detected
    if project_info:
        click.echo("🔧 Generating integration code...")
        try:
            files_created = setup_integration(project_info, project_path)
            click.echo("   Generated files:")
            for file_path in files_created:
                click.echo(f"   - {file_path}")
        except Exception as e:
            click.echo(f"   ⚠️  Error generating code: {e}")

    click.echo(f'✅ Initialized API diagnostics in {project_path}')
    click.echo(f'   Created: {config_dir}')
    click.echo(f'   Config: {config_file}')

    if project_info:
        click.echo(f'   📖 See .api-diagnostics/generated/INTEGRATION.md for setup instructions')


@cli.command()
def start():
    """Start monitoring API calls"""
    config_dir = Path('.api-diagnostics')

    if not config_dir.exists():
        click.echo("❌ Not initialized. Run 'api-diagnostics init' first")
        return

    # Update config to enabled
    config_file = config_dir / 'config.json'
    if config_file.exists(): # why does .exists work on a variable
        import json
        config = json.loads(config_file.read_text())
        config['enabled'] = True
        config_file.write_text(json.dumps(config, indent=2))

    click.echo('✅ API monitoring started')
    click.echo('   Correlation tracking is now active')


@cli.command()
def stop():
    """Stop monitoring API calls"""
    config_dir = Path('.api-diagnostics')

    if not config_dir.exists():
        click.echo("❌ Not initialized. Run 'api-diagnostics init' first")
        return

    # Update config to disabled
    config_file = config_dir / 'config.json'
    if config_file.exists():
        import json
        config = json.loads(config_file.read_text())
        config['enabled'] = False
        config_file.write_text(json.dumps(config, indent=2))

    click.echo('⏹️  API monitoring stopped')


@cli.command()
@click.argument('correlation_id')
@click.option('--format', 'output_format', default='human', type=click.Choice(['human', 'json', 'compact']), help='Output format')
@click.option('--logs', help='Comma-separated list of log file paths to search')
def search(correlation_id, output_format, logs):
    """Search logs by correlation ID"""
    from core import search_logs_by_correlation_id, format_log_entry, validate_correlation_id

    # Validate correlation ID format
    if not validate_correlation_id(correlation_id):
        # Try to find partial matches if it's not a full UUID
        if len(correlation_id) < 8:
            click.echo(f"⚠️  Correlation ID too short. Please provide at least 8 characters.")
            return

    # Parse log paths if provided
    log_paths = None
    if logs:
        log_paths = [path.strip() for path in logs.split(',')]

    click.echo(f'🔍 Searching for correlation ID: {correlation_id}')
    if log_paths:
        click.echo(f'   Log files: {", ".join(log_paths)}')
    else:
        click.echo('   Searching default log locations...')

    # Search for entries
    entries = search_logs_by_correlation_id(correlation_id, log_paths)

    if not entries:
        click.echo('❌ No log entries found with that correlation ID')
        click.echo('\n💡 Tips:')
        click.echo('   - Make sure your application is logging with correlation IDs')
        click.echo('   - Check if log files exist in the current directory')
        click.echo('   - Try searching with just the first 8 characters of the ID')
        return

    click.echo(f'\n✅ Found {len(entries)} log entries:')
    click.echo('=' * 60)

    for i, entry in enumerate(entries, 1):
        formatted = format_log_entry(entry, output_format)
        click.echo(f'\n[{i}] {formatted}')

        if i < len(entries):
            click.echo('-' * 40)


@cli.command()
def status():
    """Show current monitoring status"""
    config_dir = Path('.api-diagnostics')

    if not config_dir.exists():
        click.echo("❌ Not initialized")
        click.echo("   Run 'api-diagnostics init' to get started")
        return

    config_file = config_dir / 'config.json'
    if config_file.exists():
        import json
        config = json.loads(config_file.read_text())
        status = "🟢 ACTIVE" if config.get('enabled') else "🔴 STOPPED"
        click.echo(f"Status: {status}")
        click.echo(f"Log Level: {config.get('log_level', 'ERROR')}")
    else:
        click.echo("❌ Configuration file missing")


@cli.command()
@click.option('--type', 'error_type', default='error', type=click.Choice(['400', '500', 'error']), help='Error type to search for')
@click.option('--format', 'output_format', default='human', type=click.Choice(['human', 'json', 'compact']), help='Output format')
@click.option('--limit', default=20, help='Maximum number of entries to show')
@click.option('--logs', help='Comma-separated list of log file paths to search')
def errors(error_type, output_format, limit, logs):
    """Search logs for error entries"""
    from core import search_logs_by_error_type, format_log_entry

    # Parse log paths if provided
    log_paths = None
    if logs:
        log_paths = [path.strip() for path in logs.split(',')]

    click.echo(f'🔍 Searching for {error_type} errors (limit: {limit})')
    if log_paths:
        click.echo(f'   Log files: {", ".join(log_paths)}')
    else:
        click.echo('   Searching default log locations...')

    # Search for error entries
    entries = search_logs_by_error_type(error_type, log_paths, limit)

    if not entries:
        click.echo(f'❌ No {error_type} errors found in logs')
        return

    click.echo(f'\n✅ Found {len(entries)} error entries:')
    click.echo('=' * 60)

    for i, entry in enumerate(entries, 1):
        formatted = format_log_entry(entry, output_format)
        click.echo(f'\n[{i}] {formatted}')

        if i < len(entries):
            click.echo('-' * 40)


@cli.command()
@click.option('--hours', default=24, help='Number of hours to look back')
@click.option('--format', 'output_format', default='compact', type=click.Choice(['human', 'json', 'compact']), help='Output format')
@click.option('--limit', default=50, help='Maximum number of entries to show')
@click.option('--logs', help='Comma-separated list of log file paths to search')
def recent(hours, output_format, limit, logs):
    """Show recent log entries"""
    from core import search_logs_recent, format_log_entry

    # Parse log paths if provided
    log_paths = None
    if logs:
        log_paths = [path.strip() for path in logs.split(',')]

    click.echo(f'🔍 Searching for entries from the last {hours} hours (limit: {limit})')
    if log_paths:
        click.echo(f'   Log files: {", ".join(log_paths)}')
    else:
        click.echo('   Searching default log locations...')

    # Search for recent entries
    entries = search_logs_recent(hours, log_paths, limit)

    if not entries:
        click.echo('❌ No recent log entries found')
        return

    click.echo(f'\n✅ Found {len(entries)} recent entries:')
    click.echo('=' * 60)

    for i, entry in enumerate(entries, 1):
        formatted = format_log_entry(entry, output_format)
        click.echo(f'\n[{i}] {formatted}')

        if i < len(entries):
            click.echo('-' * 40)


@cli.command()
def clean():
    """Remove all integration code"""
    from integrations import remove_integration

    click.echo('🧹 Cleaning up API diagnostics integration...')
    try:
        remove_integration('.')
        click.echo('✅ Integration removed successfully')
    except Exception as e:
        click.echo(f'❌ Error removing integration: {e}')


if __name__ == '__main__':
    cli()
