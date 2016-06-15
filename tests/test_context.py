from ConfigParser import SafeConfigParser
from click.testing import CliRunner

from gcontainer.callback import Callback
from gcontainer.deploy_controller import DeployController
from gcontainer.docker_controller import Docker
from gcontainer.file_manager import FileSystemController
from gcontainer.context import CmdContext
from gcontainer.output import print_errors
from gcontainer.systemd import Systemd


def test_ctor():
    ctx = CmdContext(True, True, True)

    assert ctx.json
    assert ctx.verbose
    assert ctx.raw

    assert ctx.service_group == CmdContext.Commands['service_group']
    assert ctx.config_group == CmdContext.Commands['config_group']


def test_init():
    runner = CliRunner()

    with runner.isolated_filesystem():
        ctx = CmdContext.init(CmdContext(), '/no-such-path', skip_root_check=True)

        assert ctx.format_function == print_errors
        assert ctx.config.__class__ == SafeConfigParser
        assert ctx.fs.__class__ == FileSystemController
        assert ctx.deploy.__class__ == DeployController
        assert ctx.docker.__class__ == Docker
        assert ctx.systemd.__class__ == Systemd
        assert ctx.callback.__class__ == Callback

        assert ctx.cmd == CmdContext.Commands['service_group']
