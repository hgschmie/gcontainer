import os

from file_manager import FileSystemController
from subprocess import call


class Systemd:
    """ Interface with systemd.

    TODO - This can probably talk to systemd directly through DBus. Investigate more. The current code
    is pretty ghetto and may be somewhat brittle.
    """

    SCRIPTS = {'ExecStartPre': 'exec-start-pre.sh',
               'ExecStartPost': 'exec-start-post.sh',
               'ExecStopPost': 'exec-stop-post.sh',
               }

    TEMPLATE = '''\
#
# GContainer created configuration file
#
# DO NOT MODIFY! THIS FILE WILL BE OVERWRITTEN BY GCONTAINER!
#
# Configuration file for %(name)s
#
[Unit]
Description=gcontainer deployment of '{name}'
After=docker.service

[Install]
WantedBy=multi-user.target

[Service]
Type=simple
ExecStart={gcontainer} start --block --ignore-started {name}
ExecStop={gcontainer} stop {name}
TimeoutStopSec={timeout}
'''

    def __init__(self, ctx):
        self.ctx = ctx
        self.config_dir = FileSystemController.create_path_name(ctx.config.get('systemd', 'config_dir'))
        self.gcontainer = ctx.config.get('systemd', 'gcontainer')
        self.systemctl = ctx.config.get('systemd', 'systemctl')
        self.timeout = ctx.config.get('systemd', 'timeout')

    def _config_file(self, name):
        return FileSystemController.create_path_name(self.config_dir, "%s.service" % name)

    @classmethod
    def _name(cls, name):
        return "gcontainer-%s" % name

    def enable(self, service_name):
        gcontainer_name = Systemd._name(service_name)
        config_file = self._config_file(gcontainer_name)

        if not os.access(config_file, os.F_OK):
            systemd_config = Systemd.TEMPLATE.format(name=service_name,
                                                     gcontainer=self.gcontainer,
                                                     timeout=self.timeout)

            script_dir = self.ctx.fs.info_deploy(service_name)['script']
            script_files = self.ctx.fs.load_scripts(service_name)

            for key, script_name in Systemd.SCRIPTS.iteritems():
                if script_name in script_files:
                    script_file = FileSystemController.create_path_name(script_dir, script_name)
                    os.chmod(script_file, 0755)
                    systemd_config += "%s=%s\n" % (key, script_file)

            with open(config_file, 'w', 0644) as config_file:
                config_file.write(systemd_config)
                config_file.flush()

            call([self.systemctl, 'preset', gcontainer_name])
            call([self.systemctl, '--quiet', 'enable', gcontainer_name])

    def disable(self, service_name):
        gcontainer_name = Systemd._name(service_name)
        config_file = self._config_file(gcontainer_name)

        if os.access(config_file, os.F_OK):
            call([self.systemctl, '--quiet', 'disable', gcontainer_name])
            os.unlink(config_file)
            call([self.systemctl, 'daemon-reload'])
