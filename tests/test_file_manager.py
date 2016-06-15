import os
import pytest
import time
import uuid

from click.testing import CliRunner

from gcontainer.context import CmdContext
from gcontainer.error import GContainerException, ErrorConstants
from gcontainer.file_manager import FileSystemController

TEST_NAME = '_folder_under_test'


@pytest.fixture
def fs_base():
    return CliRunner().isolated_filesystem()


@pytest.fixture
def ctx():
    ctx = CmdContext.init(CmdContext(), '/no-such-path', skip_root_check=True)
    ctx.config.set('layout', 'root', TEST_NAME)
    return ctx


def test_basic(fs_base, ctx):
    with fs_base:
        FileSystemController(ctx)

        for key in ('config_dir', 'log_dir', 'script_dir', 'archive_dir'):
            dir_name = FileSystemController.create_path_name(TEST_NAME, CmdContext.DefaultValues['layout'][key])
            assert os.access(dir_name, os.F_OK | os.R_OK | os.W_OK)


def test_create_remove_deploy(fs_base, ctx):
    with fs_base:
        fs = FileSystemController(ctx)
        deploy = str(uuid.uuid4())

        deploy_info = fs.create_deploy(deploy)

        for key in ('log', 'script', 'config_base'):
            assert os.access(deploy_info[key], os.F_OK | os.R_OK | os.W_OK)

        fs.remove_deploy(deploy)

        for key in ('log', 'script', 'config_base'):
            assert not os.access(deploy_info[key], os.F_OK)


def test_create_remove_config(fs_base, ctx):
        with fs_base:
            fs = FileSystemController(ctx)
            deploy = str(uuid.uuid4())
            config = str(uuid.uuid4())
            config2 = str(uuid.uuid4())

            # create deploy with two configs
            fs.create_deploy(deploy)
            fs.create_config(deploy, config)
            fs.create_config(deploy, config2)

            # select first config
            fs.select_config(deploy, config)

            deploy_info = fs.info_deploy(deploy)

            current_config = fs.current_config(deploy)
            assert config == current_config

            for key in ('config_base', 'log', 'script', 'config'):
                assert os.access(deploy_info[key], os.F_OK | os.R_OK | os.W_OK)

            # select second config and remove first config
            fs.select_config(deploy, config2)

            current_config = fs.current_config(deploy)
            assert config2 == current_config

            fs.remove_config(deploy, config)
            assert not os.access(deploy_info['config'], os.F_OK)


def test_can_not_remove_current_config(fs_base, ctx):
        with fs_base:
            fs = FileSystemController(ctx)
            deploy = str(uuid.uuid4())
            config = str(uuid.uuid4())

            fs.create_deploy(deploy)
            fs.create_config(deploy, config)
            fs.select_config(deploy, config)

            deploy_info = fs.info_deploy(deploy)

            for key in ('config_base', 'log', 'script', 'config'):
                assert os.access(deploy_info[key], os.F_OK | os.R_OK | os.W_OK)

            with pytest.raises(GContainerException) as e:
                fs.remove_config(deploy, config)

            assert e.value.error_code == ErrorConstants.CANNOT_REMOVE_ACTIVE_CONFIG.value


def test_load_environment(fs_base, ctx):
        with fs_base:
            fs = FileSystemController(ctx)
            deploy = str(uuid.uuid4())
            config = str(uuid.uuid4())
            e1 = str(uuid.uuid4())
            e2 = str(uuid.uuid4())

            fs.create_deploy(deploy)
            fs.create_config(deploy, config)
            fs.select_config(deploy, config)

            deploy_info = fs.info_deploy(deploy)

            with open(FileSystemController.create_path_name(deploy_info['config'],
                                                            FileSystemController.ENVIRONMENT_FILE_NAME),
                      'w', 0777) as fd:
                fd.write("foo=%s\nbar=%s\n" % (e1, e2))

            env = fs.load_environment(deploy)

            assert env['foo'] == e1
            assert env['bar'] == e2


def test_load_configs(fs_base, ctx):
        with fs_base:
            fs = FileSystemController(ctx)
            deploy = str(uuid.uuid4())
            config1 = str(uuid.uuid4())
            config2 = str(uuid.uuid4())
            config3 = str(uuid.uuid4())

            fs.create_deploy(deploy)
            fs.create_config(deploy, config1)
            time.sleep(0.1)
            fs.create_config(deploy, config2)
            time.sleep(0.1)
            fs.create_config(deploy, config3)
            fs.select_config(deploy, config2)

            configs = fs.load_configs(deploy)

            assert configs[0]['name'] == config1
            assert configs[1]['name'] == config2
            assert configs[2]['name'] == config3
            assert not configs[0]['current']
            assert configs[1]['current']
            assert not configs[2]['current']
