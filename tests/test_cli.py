import pytest
import uuid

from click.testing import CliRunner
from gcontainer.context import CmdContext
from gcontainer import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_empty(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert result.output.startswith("Usage: main [OPTIONS] COMMAND [ARGS]...\n")
    assert not result.exception


def test_cli_help(runner):
    result = runner.invoke(cli.main, ['--help'])
    assert result.exit_code == 0
    assert result.output.startswith("Usage: main [OPTIONS] COMMAND [ARGS]...\n")
    assert not result.exception


def test_cli_mock_list(runner):
    with runner.isolated_filesystem():
        mock = MockService()
        cmd = 'list'
        CmdContext.Commands['service_group'] = mock
        result = runner.invoke(cli.main, [cmd])

        assert result.exit_code == 0
        assert not result.exception
        assert len(mock.args) == 0
        assert len(mock.cmd) == 1
        assert mock.cmd[0] == cmd


def test_cli_mock_commands_noargs(runner):
    for cmd in ('create', 'remove', 'deploy', 'start', 'stop', 'restart', 'enable', 'disable', 'status'):
        with runner.isolated_filesystem():
            mock = MockService()
            CmdContext.Commands['service_group'] = mock
            result = runner.invoke(cli.main, [cmd])

            assert result.exit_code == 2
            assert result.exception.__class__ == SystemExit
            assert len(mock.args) == 0
            assert len(mock.cmd) == 0


def test_cli_mock_commands_one_arg(runner):
    for cmd in ('create', 'remove', 'start', 'stop', 'restart', 'enable', 'disable', 'status'):
        with runner.isolated_filesystem():
            mock = MockService()
            CmdContext.Commands['service_group'] = mock
            param = str(uuid.uuid4())
            result = runner.invoke(cli.main, [cmd, param])

            assert result.exit_code == 0
            assert not result.exception
            assert len(mock.args) == 1
            assert len(mock.cmd) == 1
            assert mock.cmd[0] == cmd
            assert mock.args['service_name'] == param


def test_cli_mock_commands_two_args(runner):
    cmd = 'deploy'
    with runner.isolated_filesystem():
        mock = MockService()
        CmdContext.Commands['service_group'] = mock
        param1 = str(uuid.uuid4())
        param2 = str(uuid.uuid4())
        result = runner.invoke(cli.main, [cmd, param1, param2])

        assert result.exit_code == 0
        assert not result.exception
        assert len(mock.args) == 3
        assert len(mock.cmd) == 1
        assert mock.cmd[0] == cmd
        assert mock.args['service_name'] == param1
        assert mock.args['deploy_id'] == param2
        assert mock.args['callback_uri'] is None


def test_cli_mock_commands_deploy_callback(runner):
    cmd = 'deploy'
    with runner.isolated_filesystem():
        mock = MockService()
        CmdContext.Commands['service_group'] = mock
        param1 = str(uuid.uuid4())
        param2 = str(uuid.uuid4())
        param3 = str(uuid.uuid4())
        result = runner.invoke(cli.main, [cmd, '--callback-uri', param3, param1, param2])

        assert result.exit_code == 0
        assert not result.exception
        assert len(mock.args) == 3
        assert len(mock.cmd) == 1
        assert mock.cmd[0] == cmd
        assert mock.args['service_name'] == param1
        assert mock.args['deploy_id'] == param2
        assert mock.args['callback_uri'] == param3


def test_cli_mock_commands_start_flags(runner):
    cmd = 'start'
    with runner.isolated_filesystem():
        mock = MockService()
        CmdContext.Commands['service_group'] = mock
        param1 = str(uuid.uuid4())
        result = runner.invoke(cli.main, [cmd, '--ignore-started', '--block', param1])

        assert result.exit_code == 0
        assert not result.exception
        assert len(mock.args) == 3
        assert len(mock.cmd) == 1
        assert mock.cmd[0] == cmd
        assert mock.args['service_name'] == param1
        assert mock.args['started_flag']
        assert mock.args['block_flag']


def test_cli_mock_commands_stop_flags(runner):
    cmd = 'stop'
    with runner.isolated_filesystem():
        mock = MockService()
        CmdContext.Commands['service_group'] = mock
        param1 = str(uuid.uuid4())
        result = runner.invoke(cli.main, [cmd, '--ignore-stopped', param1])

        assert result.exit_code == 0
        assert not result.exception
        assert len(mock.args) == 2
        assert len(mock.cmd) == 1
        assert mock.cmd[0] == cmd
        assert mock.args['service_name'] == param1
        assert mock.args['stopped_flag']


def test_cli_mock_config_list(runner):
    with runner.isolated_filesystem():
        mock = MockConfig()
        cmd = 'list'
        param1 = str(uuid.uuid4())
        CmdContext.Commands['config_group'] = mock
        result = runner.invoke(cli.main, ['config', cmd, param1])

        assert result.exit_code == 0
        assert not result.exception
        assert len(mock.args) == 1
        assert len(mock.cmd) == 2
        assert mock.cmd[0] == 'config'
        assert mock.cmd[1] == cmd


def test_cli_mock_config_commands(runner):
    for cmd in ('create', 'remove', 'activate'):
        with runner.isolated_filesystem():
            mock = MockConfig()
            CmdContext.Commands['config_group'] = mock
            result = runner.invoke(cli.main, ['config', cmd])

            assert result.exit_code == 2
            assert result.exception.__class__ == SystemExit
            assert len(mock.args) == 0
            assert len(mock.cmd) == 1


def test_cli_mock_config_commands_one_arg(runner):
    for cmd in ('create', 'remove', 'activate'):
        with runner.isolated_filesystem():
            mock = MockConfig()
            CmdContext.Commands['config_group'] = mock
            param = str(uuid.uuid4())
            result = runner.invoke(cli.main, ['config', cmd, param])

            assert result.exit_code == 2
            assert result.exception.__class__ == SystemExit
            assert len(mock.args) == 0
            assert len(mock.cmd) == 1


def test_cli_mock_config_commands_two_args(runner):
    for cmd in ('create', 'remove', 'activate'):
        with runner.isolated_filesystem():
            mock = MockConfig()
            CmdContext.Commands['config_group'] = mock
            param1 = str(uuid.uuid4())
            param2 = str(uuid.uuid4())
            result = runner.invoke(cli.main, ['config', cmd, param1, param2])

            assert result.exit_code == 0
            assert not result.exception
            assert len(mock.args) == 2
            assert len(mock.cmd) == 2
            assert mock.cmd[0] == 'config'
            assert mock.cmd[1] == cmd
            assert mock.args['service_name'] == param1
            assert mock.args['config_name'] == param2


class MockService:
    def __init__(self):
        self.args = {}
        self.cmd = []

    def create(self, ctx, service_name):
        self.cmd.append('create')
        self.args['service_name'] = service_name

    def remove(self, ctx, service_name):
        self.cmd.append('remove')
        self.args['service_name'] = service_name

    def deploy(self, ctx, service_name, deploy_id, callback_uri=None):
        self.cmd.append('deploy')
        self.args['service_name'] = service_name
        self.args['deploy_id'] = deploy_id
        self.args['callback_uri'] = callback_uri

    def start(self, ctx, service_name):
        self.cmd.append('start')
        self.args['service_name'] = service_name

        if ctx.started_flag:
            self.args['started_flag'] = True

        if ctx.block_flag:
            self.args['block_flag'] = True

    def stop(self, ctx, service_name):
        self.cmd.append('stop')
        self.args['service_name'] = service_name

        if ctx.stopped_flag:
            self.args['stopped_flag'] = True

    def restart(self, ctx, service_name):
        self.cmd.append('restart')
        self.args['service_name'] = service_name

    def enable(self, ctx, service_name):
        self.cmd.append('enable')
        self.args['service_name'] = service_name

    def disable(self, ctx, service_name):
        self.cmd.append('disable')
        self.args['service_name'] = service_name

    def status(self, ctx, service_name):
        self.cmd.append('status')
        self.args['service_name'] = service_name

    def list(self, ctx):
        self.cmd.append('list')


class MockConfig:
    def __init__(self):
        self.args = {}
        self.cmd = []
        self.cmd.append('config')

    def create(self, ctx, service_name, config_name):
        self.cmd.append('create')
        self.args['service_name'] = service_name
        self.args['config_name'] = config_name

    def remove(self, ctx, service_name, config_name):
        self.cmd.append('remove')
        self.args['service_name'] = service_name
        self.args['config_name'] = config_name

    def activate(self, ctx, service_name, config_name):
        self.cmd.append('activate')
        self.args['service_name'] = service_name
        self.args['config_name'] = config_name

    def list(self, ctx, service_name):
        self.cmd.append('list')
        self.args['service_name'] = service_name
