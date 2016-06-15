import sys
import json

import click

from gcontainer.error import ErrorConstants, GContainerException


def output(f):
    """Decorator to capture method output and transform into the required output format."""

    def output_wrapper(*args, **kwargs):
        # By convention, the context is the first argument (after self/cls).
        ctx = args[1]

        exit_code = 0
        result = error_wrapper(f, ctx, *args, **kwargs) or {}

        if 'error_code' not in result:
            result['error_code'] = ErrorConstants.NO_ERROR.value
        elif result['error_code'] != ErrorConstants.NO_ERROR.value:
            exit_code = 1
            if 'msg' not in result:
                result['msg'] = ErrorConstants.GENERAL_ERROR.value

        if ctx.raw:
            click.echo(result)
        else:
            res = ctx.format_function(result, ctx=ctx)
            if res is not None:
                click.echo(res)

        return exit_code

    return output_wrapper


def error_wrapper(f, ctx, *args, **kwargs):
    """Wrap methods into error processing to ensure that the responses are always formatted correctly."""

    if ctx.raw:
        return f(*args, **kwargs)
    else:
        try:
            return f(*args, **kwargs)

        except (OSError, IOError) as e:
            result = {
                'error_code': ErrorConstants.OS_ERROR.value,
                'strerror': e.strerror,
                'errno': e.errno,
                'filename': e.filename,
                'msg': str(e)
            }

        except GContainerException as e:
            result = {
                'error_code': e.error_code,
                'msg': e.message
            }

        except Exception as e:
            result = {
                'msg': e.message
            }

            if hasattr(e, 'error_code'):
                result['error_code'] = e.error_code
            else:
                result['error_code'] = ErrorConstants.GENERAL_ERROR.value

        res = ctx.format_function(result, ctx=ctx)
        if res is not None:
            click.echo(res)

        sys.exit(1)


def _has_error_code(res):
    """Returns true if the passed in result has an error code > 0."""

    if res and 'error_code' in res:
        return res['error_code'] > 0

    return False


def print_errors(res, ctx):
    """Print an error message if necesasry. This is a formatter function."""

    if _has_error_code(res):
        return res.get('msg', '')
    return None


def print_json(res, ctx):
    """Print a result as JSON. This is a formatter function."""

    return json.dumps(res)


def _service_status(res, ctx):
    """Print output of the main status or create commands as text. This is a formatter function."""

    if _has_error_code(res):
        return print_errors(res, ctx)

    template = '''\
name:              {name}
config-location:   {config_location}
log-location:      {log_location}
script-location:   {script_location}
running:           {running}
enabled:           {enabled}
container-running: {container_running}
deployment:        {deployment}
config:            {config}'''

    result = template.format(name=res['name'],
                             config_location=res['config_location'],
                             log_location=res['log_location'],
                             script_location=res['script_location'],
                             running=res['running'],
                             enabled=res['enabled'],
                             container_running=res['container_status'].get('running', False),
                             deployment=res['deployment'],
                             config=res['config'])

    if 'callback_uri' in res:
        result += "\ncallback-uri:      {callback_uri}".format(callback_uri=res['callback_uri'])

    return result


def _service_list(res, ctx):
    """Print output of the main list command as text. This is a formatter function."""

    if _has_error_code(res):
        return print_errors(res, ctx)

    max_len = {'name': 10,
               'flags': 5,
               'deployment': 20,
               'config': 10}

    deploys = res['deploys'].values()
    if len(deploys) == 0:
        return ""

    for deploy in deploys:
        for key in ('name', 'deployment', 'config'):
            max_len[key] = max(len(deploy.get(key, '')), max_len.get(key, 0))

    lines = []
    header = " ".join(("ID".ljust(max_len['name'], ' '),
                       "FLAGS",
                       'DEPLOY'.ljust(max_len['deployment'], ' '),
                       'CONFIG'.ljust(max_len['config'], ' ')))
    lines.append(header)

    for deploy in res['deploys'].values():
        line = " ".join((deploy['name'].ljust(max_len['name'], ' '),
                         _build_flags(deploy).ljust(max_len['flags'], ' '),
                         deploy['deployment'].ljust(max_len['deployment'], ' '),
                         deploy['config'].ljust(max_len['config'], ' ')))
        lines.append(line)

    return "\n".join(lines)


def _build_flags(deploy):
    """Build the list of flags for the text output of the list command."""

    flags = ['R' if deploy['running'] else 'S',
             'E' if deploy['enabled'] else 'D']

    if 'running' in deploy['container_status']:
        flags.append('r' if deploy['container_status']['running'] else 's')
    else:
        flags.append('-')

    flags.append('C' if 'callback_uri' in deploy else '-')

    return "".join(flags)


def _config_list(res, ctx):
    """Print output of the config list command as text. This is a formatter function."""

    if _has_error_code(res):
        return print_errors(res, ctx)

    lines = []
    for config in res['configs']:
        line = '* ' if config['current'] else '  '

        if ctx.verbose:
            line += config['mtime'] + ' '

        line += config['name']
        lines.append(line)

    return "\n".join(lines)


def _config_path(res, ctx):
    """Print output of config commands that return a path. This is a formatter function."""

    if _has_error_code(res):
        return print_errors(res, ctx)

    return res['path']


_formatter_functions = {'status': _service_status,
                        'list': _service_list,
                        'config_list': _config_list,
                        'config_path': _config_path,
                        }


def formatter(formatter_name):
    """Chooses a specific formatter for text output unless json is selected."""

    def _formatter_decorator(f):
        def _formatter_wrapper(*wrapper_args, **wrapper_kwargs):
            ctx = wrapper_args[1]
            if not ctx.json and formatter_name in _formatter_functions:
                ctx.format_function = _formatter_functions[formatter_name]
            return f(*wrapper_args, **wrapper_kwargs)

        return _formatter_wrapper

    return _formatter_decorator
