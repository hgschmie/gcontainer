import fcntl
import json

import os

from .error import GContainerException, ErrorConstants
from .file_manager import FileSystemController


class DeployStatus(dict):
    """Wrapper around a dictionary that ensures that the default keys are present with default values."""

    DEPLOY_VERSION = 1

    COUNT_KEY = 'count'
    DEPLOYS_KEY = 'deploys'
    VERSION_KEY = 'version'

    def __init__(self, values={}):
        super(DeployStatus, self).__init__(values)

    @classmethod
    def __missing__(cls, key):
        if key == DeployStatus.COUNT_KEY:
            return 0
        elif key == DeployStatus.DEPLOYS_KEY:
            return {}
        elif key == DeployStatus.VERSION_KEY:
            return DeployStatus.DEPLOY_VERSION


class DeployLock():
    """Lock for the deploy region to ensure single threaded access. """

    LOCK_FILE_NAME = '.lock'

    def __init__(self, root, mode):
        self.lock_file = FileSystemController.create_path_name(root, DeployLock.LOCK_FILE_NAME)

        # create lock file if it does not exist.
        if not os.access(self.lock_file, os.F_OK):
            with open(self.lock_file, "w"):
                pass

        self.mode = mode
        self.lock_fd = None

    def __enter__(self):
        if self.lock_fd is not None:
            raise GContainerException(ErrorConstants.ANOTHER_OPERATION_IN_PROGRESS)

        if self.mode == fcntl.LOCK_EX:
            self.lock_fd = open(self.lock_file, "w")
        else:
            self.lock_fd = open(self.lock_file, "r")

        fcntl.lockf(self.lock_fd, self.mode)

    def __exit__(self, type, val, tb):
        if self.lock_fd is None:
            raise GContainerException(ErrorConstants.LOCK_UNAVAILABLE)

        self.lock_fd.close()
        return False


class DeployController:
    """Manages the list of deployments."""

    DEPLOY_FILE_NAME = 'deploy.json'

    def __init__(self, root):
        self.root = root
        self.deploy_file = FileSystemController.create_path_name(root, DeployController.DEPLOY_FILE_NAME)

        # if the deploy file does not exist, create it on the fly.
        if not os.access(self.deploy_file, os.F_OK):
            with self._create_lock(fcntl.LOCK_EX), open(self.deploy_file, 'w') as json_file:
                json.dump(DeployStatus({}), json_file, indent=2)
                json_file.flush()

    def _create_lock(self, mode):
        """Returns a new deploy lock for use in with statements."""
        return DeployLock(self.root, mode)

    def _load_deploy(self):
        """ Load the deployment file and does some very basic version checking. """

        with self._create_lock(fcntl.LOCK_SH), open(self.deploy_file, 'r') as json_file:
            file_contents = DeployStatus(json.load(json_file))
            if file_contents[DeployStatus.VERSION_KEY] != DeployStatus.DEPLOY_VERSION:
                raise GContainerException(ErrorConstants.BAD_DEPLOY_VERSION,
                                          file_contents[DeployStatus.VERSION_KEY], DeployStatus.DEPLOY_VERSION)

            return file_contents

    def load(self):
        """ Load the existing deployments as a dict. """

        # _load_deploy does the required locking.
        file_contents = self._load_deploy()
        return file_contents[DeployStatus.DEPLOYS_KEY], file_contents[DeployStatus.COUNT_KEY]

    def info(self, deploy_name):
        """ Return status for a single service. """

        # _load_deploy does the required locking.
        file_contents = self._load_deploy()
        if deploy_name not in file_contents[DeployStatus.DEPLOYS_KEY]:
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, deploy_name)

        return file_contents[DeployStatus.DEPLOYS_KEY][deploy_name]

    def exists(self, deploy_name):
        """ Check whether a given service exists. """

        # _load_deploy does the required locking.
        file_contents = self._load_deploy()
        return deploy_name in file_contents[DeployStatus.DEPLOYS_KEY]

    def add(self, service_name):
        """Add a deployment to the deployment file. The file is exclusively locked for writing. """

        with self._create_lock(fcntl.LOCK_EX):
            file_contents = self._load_deploy()
            deploys = file_contents[DeployStatus.DEPLOYS_KEY]

            if service_name in deploys:
                raise GContainerException(ErrorConstants.DEPLOY_EXISTS, service_name)

            deploy_info = {'name': service_name,
                           'running': False,
                           'enabled': False,
                           'deployment': '-'
                           }

            deploys[service_name] = deploy_info

            file_contents[DeployStatus.COUNT_KEY] += 1
            file_contents[DeployStatus.DEPLOYS_KEY] = deploys
            self._save_atomic(file_contents)

            return deploy_info

    def remove(self, deploy_name):
        """Remove a deployment from the deployment file. The file is exclusively locked for writing. """

        with self._create_lock(fcntl.LOCK_EX):
            file_contents = self._load_deploy()
            deploys = file_contents[DeployStatus.DEPLOYS_KEY]

            if deploy_name not in deploys:
                raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, deploy_name)

            del deploys[deploy_name]

            file_contents[DeployStatus.COUNT_KEY] += 1
            file_contents[DeployStatus.DEPLOYS_KEY] = deploys
            self._save_atomic(file_contents)

    def set_enabled(self, deploy_name, enabled=True):
        """Mark a deployment as enabled."""

        with self._create_lock(fcntl.LOCK_EX):
            file_contents = self._load_deploy()
            deploys = file_contents[DeployStatus.DEPLOYS_KEY]

            if deploy_name not in deploys:
                raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, deploy_name)

            deploys[deploy_name]['enabled'] = enabled

            file_contents[DeployStatus.COUNT_KEY] += 1
            file_contents[DeployStatus.DEPLOYS_KEY] = deploys
            self._save_atomic(file_contents)

    def set_running(self, deploy_name, running=True):
        """Mark a deployment as running."""

        with self._create_lock(fcntl.LOCK_EX):
            file_contents = self._load_deploy()
            deploys = file_contents[DeployStatus.DEPLOYS_KEY]

            if deploy_name not in deploys:
                raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, deploy_name)

            deploys[deploy_name]['running'] = running

            file_contents[DeployStatus.COUNT_KEY] += 1
            file_contents[DeployStatus.DEPLOYS_KEY] = deploys
            self._save_atomic(file_contents)

    def save_deploy(self, deploy_name, deploy_id='-', callback_uri=None):
        """Save deploy id."""

        with self._create_lock(fcntl.LOCK_EX):
            file_contents = self._load_deploy()
            deploys = file_contents[DeployStatus.DEPLOYS_KEY]

            if deploy_name not in deploys:
                raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, deploy_name)

            deploys[deploy_name]['deployment'] = deploy_id
            if callback_uri:
                deploys[deploy_name]['callback_uri'] = callback_uri
            elif 'callback_uri' in deploys[deploy_name]:
                del deploys[deploy_name]['callback_uri']

            file_contents[DeployStatus.COUNT_KEY] += 1
            file_contents[DeployStatus.DEPLOYS_KEY] = deploys
            self._save_atomic(file_contents)

    def _save_atomic(self, file_contents):
        """Do an atomic save and swap of the deploy file.

        This probably wants some error checking.
        """

        new_file = self.deploy_file + ".new"
        old_file = self.deploy_file + ".old"

        with open(new_file, 'w') as new_json_file:
            json.dump(file_contents, new_json_file, indent=2)

            if os.access(old_file, os.F_OK):
                os.remove(old_file)
            os.rename(self.deploy_file, old_file)
            os.rename(new_file, self.deploy_file)
