from .output import output, formatter
from .error import ErrorConstants, GContainerException
from .util import legal_name


class Config(object):
    """Contains all the business logic dealing with the configuration code for gcontainer."""

    @formatter('config_path')
    @output
    def create(self, ctx, service_name, config_name):
        """Create a new configuration for a service."""

        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not legal_name(config_name):
            raise GContainerException(ErrorConstants.ILLEGAL_CONFIG_NAME, config_name)

        try:
            config_path = ctx.fs.create_config(service_name, config_name)
            return {'path': config_path}
        except GContainerException as e:
            if e.error_code == ErrorConstants.PATH_EXISTS:
                raise GContainerException(ErrorConstants.CANNOT_CREATE_CONFIG, config_name, service_name)
            else:
                raise e

    @output
    def remove(self, ctx, service_name, config_name):
        """Remove a configuration for a service."""

        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not legal_name(config_name):
            raise GContainerException(ErrorConstants.ILLEGAL_CONFIG_NAME, config_name)

        try:
            return ctx.fs.remove_config(service_name, config_name)
        except GContainerException as e:
            if e.error_code == ErrorConstants.CANNOT_REMOVE_PATH:
                raise GContainerException(ErrorConstants.CANNOT_REMOVE_CONFIG, config_name, service_name)
            else:
                raise e

    @output
    def activate(self, ctx, service_name, config_name):
        """Activate a configuration for a service."""

        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not legal_name(config_name):
            raise GContainerException(ErrorConstants.ILLEGAL_CONFIG_NAME, config_name)

        return ctx.fs.select_config(service_name, config_name)

    @formatter('config_list')
    @output
    def list(self, ctx, service_name):
        """List all available configurations for a service."""

        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        configs = ctx.fs.load_configs(service_name)

        return {'configs': configs}
