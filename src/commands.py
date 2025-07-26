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
    from integrations import detect_project

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

    click.echo(f'✅ Initialized API diagnostics in {project_path}')
    click.echo(f'   Created: {config_dir}')
    click.echo(f'   Config: {config_file}')


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
def search(correlation_id):
    """Search logs by correlation ID"""
    # TODO: Search logs by correlation ID
    click.echo(f'Searching for correlation ID: {correlation_id}')


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
def clean():
    """Remove all integration code"""
    # TODO: Remove all integration code
    click.echo('Cleaning up integration...')


if __name__ == '__main__':
    cli()
