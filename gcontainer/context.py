import os

from ConfigParser import SafeConfigParser

from .callback import Callback
from .config import Config
from .deploy_controller import DeployController
from .docker_controller import Docker
from .error import GContainerException, ErrorConstants
from .file_manager import FileSystemController
from .output import print_errors, print_json
from .service import Service
from .systemd import Systemd


class CmdContext(object):
    """ Context for global option flags collection."""

    Commands = {'service_group': Service(),
                'config_group': Config()}

    # to guarantee that a section and/or setting exists, add a default value here
    DefaultValues = {
        'general': {
            'require_root': 'true',
        },
        'layout': {
            # The root of the gcontainer data tree.
            'root': '/data/gcontainer',
            'config_dir': 'config',
            'log_dir': 'log',
            'script_dir': 'script',
            'archive_dir': 'archive',
            },
        'docker': {
            'socket': 'unix://var/run/docker.sock',
            'disable_latest_tag': 'true',
            'allow_insecure_registry': 'false',
            },
        'systemd': {
            'config_dir': '/etc/systemd/system',
            'gcontainer': '/usr/bin/gcontainer',
            'systemctl': '/usr/bin/systemctl',
            'timeout': '30s'
        },
        'callback': {
            'connect_timeout': '1',
            'read_timeout': '5',
            'ignore_callbacks': 'false',
        }
    }

    DefaultConfigFiles = [
        FileSystemController.create_path_name(os.path.expanduser('~'), '.gcontainer.conf'),
        '/usr/local/etc/gcontainer.conf',
        '/etc/gcontainer.conf',
    ]

    def __init__(self, json_flag=False, verbose_flag=False, raw_flag=False):
        self.json = json_flag
        self.verbose = verbose_flag
        self.raw = raw_flag

        for name, group in CmdContext.Commands.iteritems():
            self.__setattr__(name, group)

    @classmethod
    def _load_configuration(cls, config_file=None):
        """Check the configuration files and load the global 'config' object from them."""
        config = SafeConfigParser()
        # add the defaults first
        for section, settings in CmdContext.DefaultValues.items():
            config.add_section(section)
            for option, value in settings.items():
                config.set(section, option, value)
                # read the config files

        config_files = []
        if config_file:
            config_files.append(config_file)
        else:
            config_files.extend(CmdContext.DefaultConfigFiles)

        for config_file in config_files:
            if os.access(config_file, os.F_OK | os.R_OK):
                config.read(config_file)
                return config

        return config

    @classmethod
    def init(cls, ctx, config_path, skip_root_check=False):
        if ctx.json:
            # default formatter for JSON
            ctx.format_function = print_json
        else:
            ctx.format_function = print_errors

        ctx.config = CmdContext._load_configuration(config_path)

        if not skip_root_check:
            require_root = ctx.config.get('general', 'require_root') == 'true'
            if require_root and os.getuid() != 0:
                raise GContainerException(ErrorConstants.MUST_RUN_AS_ROOT)

        ctx.fs = FileSystemController(ctx)
        ctx.deploy = DeployController(ctx.fs.root)
        ctx.docker = Docker(ctx)
        ctx.systemd = Systemd(ctx)
        ctx.callback = Callback(ctx)

        # default commmands are in Service, this may change depending on subgroups.
        ctx.cmd = ctx.service_group

        return ctx
