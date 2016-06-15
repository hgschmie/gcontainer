import shutil
import iso8601
import os
import os.path

from datetime import datetime
from .error import ErrorConstants, GContainerException
from .util import parse_environment


class FileSystemController:
    """ Controls all accesses to the file system from gcontainer."""

    CURRENT_CONFIG_NAME = '_CURRENT'
    INITIAL_CONFIG_NAME = 'initial'
    ENVIRONMENT_FILE_NAME = '.startup-env.conf'

    ISO_8601_FORMAT = '%FT%T.%fZ'

    def __init__(self, ctx):
        self.root = FileSystemController._create_folder(ctx.config.get('layout', 'root'))

        self.config_dir = FileSystemController._create_folder(self.root, ctx.config.get('layout', 'config_dir'))
        self.log_dir = FileSystemController._create_folder(self.root, ctx.config.get('layout', 'log_dir'))
        self.script_dir = FileSystemController._create_folder(self.root, ctx.config.get('layout', 'script_dir'))
        self.archive_dir = FileSystemController._create_folder(self.root, ctx.config.get('layout', 'archive_dir'))

    @classmethod
    def create_path_name(cls, base, path=None):
        """Creates a path name relative to the given base or absolute if it starts with a separator."""

        dir_name = os.path.abspath(base)
        if path is not None and len(path) > 0:
            if path[0] == os.sep:
                dir_name = os.path.abspath(path)
            else:
                dir_name = os.path.abspath(os.path.join(dir_name, path))

        return dir_name

    @classmethod
    def _create_folder(cls, base, path=None, fail_if_exists=False):
        """ Create a folder on the file system, either relative to given base path or absolute."""

        path_name = FileSystemController.create_path_name(base, path)

        if not os.access(path_name, os.F_OK):
            os.makedirs(path_name, 0755)
        elif fail_if_exists:
            raise GContainerException(ErrorConstants.PATH_EXISTS, path_name)

        if not os.access(path_name, os.R_OK | os.W_OK | os.X_OK):
            raise GContainerException(ErrorConstants.FOLDER_NOT_ACCESSIBLE, path_name)

        return path_name

    @classmethod
    def _remove_folder(cls, base, path=None, fail_if_not_exists=False):
        """ Remove a folder on the file system, either relative to given base path or absolute."""

        path_name = FileSystemController.create_path_name(base, path)

        if os.access(path_name, os.F_OK):
            try:
                shutil.rmtree(path_name)
            except (IOError, OSError):
                raise GContainerException(ErrorConstants.CANNOT_REMOVE_FOLDER, path_name)

        elif fail_if_not_exists:
            raise GContainerException(ErrorConstants.PATH_NOT_EXISTS, path_name)

        return path_name

    @classmethod
    def _load_dir(cls, dir_name):
        """Load a local directory. Only consider file names that start with an alphanumeric character.

        Returns its result ordered by mtime.
        """

        keys = filter(lambda x: x[0].isalnum(), os.listdir(dir_name))
        names = {}
        for key in keys:
            file_name = FileSystemController.create_path_name(dir_name, key)
            stat = os.stat(file_name)
            names[key] = {'name': key,
                          'mtime': datetime.fromtimestamp(stat.st_mtime).strftime(FileSystemController.ISO_8601_FORMAT),
                          'current': False
                          }

        return names

    def _current_config_dir(self, service_name):
        """Return the location of the current configuration for the given service name."""

        config_dir = FileSystemController.create_path_name(self.config_dir, service_name)
        current_config = self.current_config(service_name)
        return FileSystemController.create_path_name(config_dir, current_config)

    def create_deploy(self, service_name):
        """ Creates all pieces necessary for a new deploy on the file system."""

        res = {}
        errors = []
        for name, folder in {'config_base': self.config_dir,
                             'log': self.log_dir,
                             'script': self.script_dir}.iteritems():
            try:
                res[name] = FileSystemController._create_folder(folder, service_name)
            except (IOError, OSError, GContainerException) as e:
                errors.append(e)

        if errors:
            raise GContainerException(ErrorConstants.CANNOT_CREATE_DEPLOY, service_name)

        return res

    def remove_deploy(self, service_name):
        """Removes everything from the file system that is related to a deploy."""

        errors = []
        for name, folder in {'config': self.config_dir, 'log': self.log_dir, 'script': self.script_dir}.iteritems():
            try:
                FileSystemController._remove_folder(folder, service_name)
            except GContainerException as e:
                errors.append(e)

        if errors:
            raise GContainerException(ErrorConstants.CANNOT_REMOVE_DEPLOY, service_name)

    def info_deploy(self, service_name):
        """Return information about a deploy location, most importantly the various pathes for config, log and scripts.
        """

        res = {}
        for name, folder in {'config_base': self.config_dir,
                             'log': self.log_dir,
                             'script': self.script_dir}.iteritems():
            res[name] = FileSystemController.create_path_name(folder, service_name)

        res['config'] = self._current_config_dir(service_name)

        return res

    def create_config(self, service_name, config_name):
        """Create a new configuration folder for the given service. """

        service_dir = FileSystemController.create_path_name(self.config_dir, service_name)
        try:
            config_dir = FileSystemController._create_folder(service_dir, config_name, fail_if_exists=True)
            return config_dir
        except (IOError, OSError, GContainerException):
            raise GContainerException(ErrorConstants.CANNOT_CREATE_CONFIG, config_name, service_name)

    def remove_config(self, service_name, config_name):
        """Remove a configuration location for the given service. The configuration location must not be the
            currently selected configuration.
        """

        current = self.current_config(service_name)

        if config_name == current or config_name == FileSystemController.CURRENT_CONFIG_NAME:
            raise GContainerException(ErrorConstants.CANNOT_REMOVE_ACTIVE_CONFIG, current)

        service_dir = FileSystemController.create_path_name(self.config_dir, service_name)

        try:
            FileSystemController._remove_folder(service_dir, config_name, fail_if_not_exists=True)
        except GContainerException:
            raise GContainerException(ErrorConstants.CANNOT_REMOVE_CONFIG, config_name, service_name)

    def select_config(self, service_name, config_name):
        """Select an existing configuration location as the current configuration."""

        service_dir = FileSystemController.create_path_name(self.config_dir, service_name)

        current_dir = FileSystemController.create_path_name(service_dir, FileSystemController.CURRENT_CONFIG_NAME)
        config_dir = FileSystemController.create_path_name(service_dir, config_name)

        if not os.access(config_dir, os.F_OK):
            raise GContainerException(ErrorConstants.NO_SUCH_CONFIG, config_name, service_name)

        if os.access(current_dir, os.F_OK):
            os.unlink(current_dir)
        os.symlink(config_name, current_dir)

    def current_config(self, service_name):
        """Return the name of the currently selected configuration."""

        service_dir = FileSystemController.create_path_name(self.config_dir, service_name)

        current_dir = FileSystemController.create_path_name(service_dir, FileSystemController.CURRENT_CONFIG_NAME)

        if not os.access(current_dir, os.F_OK):
            raise GContainerException(ErrorConstants.NO_SUCH_CONFIG, '<current config>', service_name)

        return os.readlink(current_dir)

    def load_environment(self, service_name):
        """Load the environment file located in the current configuration directory."""

        current_config_dir = self._current_config_dir(service_name)
        environment_file = FileSystemController.create_path_name(current_config_dir,
                                                                 FileSystemController.ENVIRONMENT_FILE_NAME)

        lines = []
        if os.access(environment_file, os.F_OK | os.R_OK):
            with open(environment_file, 'r') as env_file:
                for line in env_file:
                    lines.append(line.strip())

        return parse_environment(lines)

    def load_configs(self, service_name):
        """List the name of all configurations for a service. The service must exist."""

        service_dir = FileSystemController.create_path_name(self.config_dir, service_name)
        contents = self._load_dir(service_dir)

        current = self.current_config(service_name)

        if current not in contents:
            raise GContainerException(ErrorConstants.NO_SUCH_CONFIG, '<current config>', service_name)

        contents[current]['current'] = True

        configs = sorted(contents.values(), key=lambda config: iso8601.parse_date(config['mtime']))

        return configs

    def load_scripts(self, service_name):
        """List the name of all script files for a service. The service must exist."""

        service_dir = FileSystemController.create_path_name(self.script_dir, service_name)
        contents = self._load_dir(service_dir)
        return contents.keys()
