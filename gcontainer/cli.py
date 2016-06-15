import click

from .context import CmdContext
from .output import error_wrapper


@click.group()
@click.version_option()
@click.option('--json', is_flag=True, help='Output is formatted as JSON.')
@click.option('--verbose', is_flag=True, help='Verbose output.')
@click.option('--config', type=click.Path(dir_okay=False), help='Configuration file to use.')
@click.option('--raw', is_flag=True, help='Disable any output formatting.\nUse only for gcontainer tool debugging.')
@click.pass_context
def main(ctx, config, json=False, verbose=False, raw=False):
    """G Container Management tool.

    Manages containers on G hosts."""

    # prep stuff for actual command
    ctx_obj = CmdContext(json, verbose, raw)

    # Use the error wrapper to catch any init errors in the controllers
    ctx.obj = error_wrapper(CmdContext.init, ctx_obj, *[ctx_obj, config])


@main.group("config")
@click.pass_obj
def config_group(ctx):
    """Container configuration related commands."""

    # Config subcommands are in Config
    ctx.cmd = ctx.config_group


@config_group.command("create")
@click.argument('service_name')
@click.argument("config_name")
@click.pass_obj
def config_create(ctx, service_name, config_name):
    """Create a new service config."""
    ctx.cmd.create(ctx, service_name, config_name)


@config_group.command("remove")
@click.argument('service_name')
@click.argument("config_name")
@click.pass_obj
def config_remove(ctx, service_name, config_name):
    """Remove an existing service config."""
    ctx.cmd.remove(ctx, service_name, config_name)


@config_group.command("activate")
@click.argument('service_name')
@click.argument("config_name")
@click.pass_obj
def config_activate(ctx, service_name, config_name):
    """Activate an existing service config."""
    ctx.cmd.activate(ctx, service_name, config_name)


@config_group.command("list")
@click.argument('service_name')
@click.pass_obj
def config_list(ctx, service_name):
    """List all available service configs."""
    ctx.cmd.list(ctx, service_name)


@main.command("create")
@click.argument('service_name')
@click.pass_obj
def service_create(ctx, service_name):
    """Create a new service."""
    ctx.cmd.create(ctx, service_name)


@main.command("remove")
@click.argument('service_name')
@click.pass_obj
def service_remove(ctx, service_name):
    """Remove an existing service."""
    ctx.cmd.remove(ctx, service_name)


@main.command("deploy")
@click.option('--callback-uri', help='Callback URI when this service changes state.')
@click.argument('service_name')
@click.argument('deploy_id')
@click.pass_obj
def service_deploy(ctx, service_name, deploy_id, callback_uri=None):
    """Deploy an existing service."""
    ctx.cmd.deploy(ctx, service_name, deploy_id, callback_uri=callback_uri)


@main.command("start")
@click.option('--block', is_flag=True, help='If true, blocks until the container exists.')
@click.option('--ignore-started', is_flag=True, help='If true, ignore an already running container.')
@click.argument('service_name')
@click.pass_obj
def service_start(ctx, block, ignore_started, service_name):
    """Start a deployed service."""
    ctx.block_flag = block
    ctx.started_flag = ignore_started
    ctx.cmd.start(ctx, service_name)


@main.command("stop")
@click.option('--ignore-stopped', is_flag=True, help='If true, ignore an already stopped container.')
@click.argument('service_name')
@click.pass_obj
def service_stop(ctx, ignore_stopped, service_name):
    """Stop a deployed service."""
    ctx.stopped_flag = ignore_stopped
    ctx.cmd.stop(ctx, service_name)


@main.command("restart")
@click.argument('service_name')
@click.pass_obj
def service_restart(ctx, service_name):
    """Restart a deployed service if it is running."""
    ctx.cmd.restart(ctx, service_name)


@main.command("enable")
@click.argument('service_name')
@click.pass_obj
def service_enable(ctx, service_name):
    """Enable a deployed service for autostart."""
    ctx.cmd.enable(ctx, service_name)


@main.command("disable")
@click.argument('service_name')
@click.pass_obj
def service_disable(ctx, service_name):
    """Disable a deployed service for autostart."""
    ctx.cmd.disable(ctx, service_name)


@main.command("status")
@click.argument('service_name')
@click.pass_obj
def service_status(ctx, service_name):
    """Display status of an installed service."""
    ctx.cmd.status(ctx, service_name)


@main.command("list")
@click.pass_obj
def service_list(ctx):
    """List all installed services."""
    ctx.cmd.list(ctx)
