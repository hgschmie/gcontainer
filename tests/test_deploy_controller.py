import json
import os
import pytest
import uuid

from click.testing import CliRunner

from gcontainer.deploy_controller import DeployController, DeployStatus
from gcontainer.file_manager import FileSystemController


@pytest.fixture
def root():
    return CliRunner().isolated_filesystem()


def test_basic(root):
    with root:
        DeployController('')

        deploy_file = FileSystemController.create_path_name('', DeployController.DEPLOY_FILE_NAME)
        assert os.access(deploy_file, os.F_OK | os.R_OK | os.W_OK)

        with open(deploy_file) as fd:
            contents = DeployStatus(json.load(fd))

            assert contents[DeployStatus.COUNT_KEY] == 0
            assert len(contents[DeployStatus.DEPLOYS_KEY]) == 0
            assert contents[DeployStatus.VERSION_KEY] == DeployStatus.DEPLOY_VERSION


def test_create(root):
    with root:
        deploy = DeployController('')
        deploy_name = str(uuid.uuid4())

        assert not deploy.exists(deploy_name)

        deploy.add(deploy_name)

        with open(FileSystemController.create_path_name('', DeployController.DEPLOY_FILE_NAME)) as fd:
            contents = DeployStatus(json.load(fd))

            assert contents[DeployStatus.COUNT_KEY] == 1
            assert len(contents[DeployStatus.DEPLOYS_KEY]) == 1
            assert contents[DeployStatus.VERSION_KEY] == DeployStatus.DEPLOY_VERSION

            assert len(contents[DeployStatus.DEPLOYS_KEY][deploy_name]) == 4
            assert contents[DeployStatus.DEPLOYS_KEY][deploy_name]['name'] == deploy_name
            assert not contents[DeployStatus.DEPLOYS_KEY][deploy_name]['running']
            assert not contents[DeployStatus.DEPLOYS_KEY][deploy_name]['enabled']
            assert contents[DeployStatus.DEPLOYS_KEY][deploy_name]['deployment'] == '-'

        assert deploy.exists(deploy_name)

        info = deploy.info(deploy_name)

        assert info['name'] == deploy_name
        assert not info['running']
        assert not info['enabled']
        assert info['deployment'] == '-'
        assert 'callback_uri' not in info


def test_remove(root):
    with root:
        deploy = DeployController('')
        deploy_name = str(uuid.uuid4())

        assert not deploy.exists(deploy_name)

        deploy.add(deploy_name)

        assert deploy.exists(deploy_name)

        deploy.remove(deploy_name)

        assert not deploy.exists(deploy_name)


def test_flags(root):
    with root:
        deploy = DeployController('')
        deploy_name = str(uuid.uuid4())

        assert not deploy.exists(deploy_name)
        deploy.add(deploy_name)
        assert deploy.exists(deploy_name)

        info = deploy.info(deploy_name)
        assert not info['running']
        assert not info['enabled']

        deploy.set_running(deploy_name, True)
        info = deploy.info(deploy_name)
        assert info['running']
        assert not info['enabled']

        deploy.set_enabled(deploy_name, True)
        info = deploy.info(deploy_name)
        assert info['running']
        assert info['enabled']

        deploy.set_running(deploy_name, False)
        info = deploy.info(deploy_name)
        assert not info['running']
        assert info['enabled']

        deploy.set_enabled(deploy_name, False)
        info = deploy.info(deploy_name)
        assert not info['running']
        assert not info['enabled']


def test_deploy(root):
    with root:
        deploy = DeployController('')
        deploy_name = str(uuid.uuid4())
        deploy1 = str(uuid.uuid4())
        deploy2 = str(uuid.uuid4())
        callback = str(uuid.uuid4())

        assert not deploy.exists(deploy_name)
        deploy.add(deploy_name)
        assert deploy.exists(deploy_name)

        info = deploy.info(deploy_name)
        assert info['deployment'] == '-'
        assert 'callback_uri' not in info

        # deploy with callback
        deploy.save_deploy(deploy_name, deploy1, callback_uri=callback)
        info = deploy.info(deploy_name)
        assert info['deployment'] == deploy1
        assert info['callback_uri'] == callback

        # deploy without callback, removing existing callback
        deploy.save_deploy(deploy_name, deploy2, callback_uri=None)
        info = deploy.info(deploy_name)
        assert info['deployment'] == deploy2
        assert 'callback_uri' not in info
