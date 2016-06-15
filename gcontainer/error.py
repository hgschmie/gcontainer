from enum import Enum


class GContainerException(Exception):
    def __init__(self, code, *args):

        msg = code.template % args
        super(GContainerException, self).__init__(msg)

        self.error_code = code.value


class ErrorConstants(Enum):
    # General purpose error messages
    NO_ERROR = 0
    GENERAL_ERROR = 1
    OS_ERROR = 2
    MUST_RUN_AS_ROOT = 3

    # file system manager error codes
    PATH_EXISTS = 100
    PATH_NOT_EXISTS = 101
    FOLDER_NOT_ACCESSIBLE = 102
    CANNOT_REMOVE_PATH = 103
    CANNOT_REMOVE_ACTIVE_CONFIG = 104
    CANNOT_CREATE_CONFIG = 105
    CANNOT_REMOVE_CONFIG = 106
    CANNOT_CREATE_DEPLOY = 107
    CANNOT_REMOVE_DEPLOY = 108
    NO_SUCH_CONFIG = 109

    # deployer error codes
    BAD_DEPLOY_VERSION = 200
    NO_SUCH_DEPLOY = 201
    DEPLOY_EXISTS = 202
    ANOTHER_OPERATION_IN_PROGRESS = 203
    LOCK_UNAVAILABLE = 204

    # docker error codes
    DOCKER_NOT_CONNECTED = 300
    SERVICE_IS_RUNNING = 301
    SERVICE_IS_NOT_RUNNING = 302
    LATEST_TAG_DISABLED = 303
    IMAGE_NOT_AVAILABLE = 304
    NO_IMAGE_ASSIGNED = 305

    # config error codes
    ILLEGAL_CONFIG_NAME = 400
    ILLEGAL_SERVICE_NAME = 401

    @property
    def template(self):
        _templates = {
            ErrorConstants.GENERAL_ERROR: 'General Error appears. He hands you an exception.',
            ErrorConstants.MUST_RUN_AS_ROOT: 'This tool must be executed as superuser.',
            ErrorConstants.PATH_EXISTS: "path '%s' already exists.",
            ErrorConstants.PATH_NOT_EXISTS: "path '%s' does not exist.",
            ErrorConstants.FOLDER_NOT_ACCESSIBLE: "cannot access folder '%s'.",
            ErrorConstants.CANNOT_REMOVE_PATH: "cannot remove path '%s'.",
            ErrorConstants.CANNOT_REMOVE_ACTIVE_CONFIG: "cannot remove active config '%s'",
            ErrorConstants.CANNOT_CREATE_CONFIG: "cannot create configuration '%s' for deploy '%s'.",
            ErrorConstants.CANNOT_REMOVE_CONFIG: "cannot remove configuration '%s' for deploy '%s'.",
            ErrorConstants.CANNOT_CREATE_DEPLOY: "cannot create deploy '%s'.",
            ErrorConstants.CANNOT_REMOVE_DEPLOY: "cannot remove deploy '%s'.",
            ErrorConstants.NO_SUCH_CONFIG: "no such configuration: '%s' for service '%s'.",
            ErrorConstants.NO_SUCH_DEPLOY: "no such deploy: '%s'.",
            ErrorConstants.DEPLOY_EXISTS: "deploy '%s' already exists.",
            ErrorConstants.ANOTHER_OPERATION_IN_PROGRESS: "another exclusive operation is in progress.",
            ErrorConstants.LOCK_UNAVAILABLE: "could not acquire deployment lock.",
            ErrorConstants.BAD_DEPLOY_VERSION: "deploy file version is %s, only version %s is supported.",
            ErrorConstants.DOCKER_NOT_CONNECTED: "docker daemon not available.",
            ErrorConstants.SERVICE_IS_RUNNING: "service '%s' is running.",
            ErrorConstants.SERVICE_IS_NOT_RUNNING: "Service '%s' is not running.",
            ErrorConstants.LATEST_TAG_DISABLED: "'latest' tag is disabled and can not be used for a deploy.",
            ErrorConstants.IMAGE_NOT_AVAILABLE: "docker image '%s' not available (%s).",
            ErrorConstants.NO_IMAGE_ASSIGNED: "no docker image assigned for '%s'.",
            ErrorConstants.ILLEGAL_CONFIG_NAME: "configuration name '%s' is illegal.",
            ErrorConstants.ILLEGAL_SERVICE_NAME: "service name '%s' is illegal.",
        }

        if self in _templates:
            return _templates[self]
        return ""
