from .output import output, formatter
from .error import GContainerException, ErrorConstants
from .file_manager import FileSystemController
from .util import legal_name


class Service(object):
    """Contains all the business logic dealing with services themselves."""

    @formatter('status')
    @output
    def create(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.DEPLOY_EXISTS, service_name)

        deploy_dirs = ctx.fs.create_deploy(service_name)

        config_name = FileSystemController.INITIAL_CONFIG_NAME
        config_dir = ctx.fs.create_config(service_name, config_name)
        ctx.fs.select_config(service_name, config_name)

        deploy_info = ctx.deploy.add(service_name)
        docker_status = ctx.docker.status(service_name)

        return {'name': service_name,
                'config_location': config_dir,
                'log_location': deploy_dirs['log'],
                'script_location': deploy_dirs['script'],
                'running': deploy_info['running'],
                'enabled': deploy_info['enabled'],
                'deployment': deploy_info['deployment'],
                'config': config_name,
                'container_status': docker_status,
                }

    @output
    def remove(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not ctx.docker.connected():
            raise GContainerException(ErrorConstants.DOCKER_NOT_CONNECTED)

        if ctx.docker.is_running(service_name):
            raise GContainerException(ErrorConstants.SERVICE_IS_RUNNING, service_name)

        # Unhook from systemd
        ctx.systemd.disable(service_name)

        ctx.docker.destroy_container(service_name)
        ctx.deploy.remove(service_name)
        ctx.fs.remove_deploy(service_name)

    @output
    def deploy(self, ctx, service_name, deploy_id, callback_uri=None):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        ctx.docker.pull_image(deploy_id)

        ctx.deploy.save_deploy(service_name, deploy_id, callback_uri)

        deploy_info = ctx.deploy.info(service_name)

        if deploy_info['enabled']:
            ctx.systemd.enable(service_name)

    @output
    def start(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not ctx.docker.connected():
            raise GContainerException(ErrorConstants.DOCKER_NOT_CONNECTED)

        if ctx.docker.is_running(service_name):
            if not ctx.started_flag:
                raise GContainerException(ErrorConstants.SERVICE_IS_RUNNING, service_name)
        else:
            Service._start(ctx, service_name)

        if ctx.block_flag:
            ctx.docker.wait(service_name)

    @classmethod
    def _start(cls, ctx, service_name):
        deploy_info = ctx.deploy.info(service_name)

        if deploy_info['deployment'] == '-':
            raise GContainerException(ErrorConstants.NO_IMAGE_ASSIGNED, service_name)

        environment = ctx.fs.load_environment(service_name)
        ctx.docker.create_container(service_name, deploy_info['deployment'],
                                    destroy_existing=True,
                                    environment=environment)

        ctx.docker.start(service_name)

        if 'callback_uri' in deploy_info:
            ctx.callback.running(deploy_info['callback_uri'],
                                 deployment=deploy_info['deployment'],
                                 name=service_name,
                                 config=ctx.fs.current_config(service_name))

        ctx.deploy.set_running(service_name, True)

    @output
    def stop(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not ctx.docker.connected():
            raise GContainerException(ErrorConstants.DOCKER_NOT_CONNECTED)

        if not ctx.docker.is_running(service_name):
            if not ctx.stopped_flag:
                raise GContainerException(ErrorConstants.SERVICE_IS_NOT_RUNNING, service_name)
        else:
            Service._stop(ctx, service_name)

    @classmethod
    def _stop(cls, ctx, service_name):

        state = False  # did not stop a container

        deploy_info = ctx.deploy.info(service_name)
        if deploy_info:
            state = ctx.docker.stop(service_name)

            if 'callback_uri' in deploy_info:
                ctx.callback.stopped(deploy_info['callback_uri'],
                                     deployment=deploy_info['deployment'],
                                     name=service_name,
                                     config=ctx.fs.current_config(service_name))

        ctx.deploy.set_running(service_name, False)

        # Return the actual stop state (True if a container was stopped) for restart command
        return state

    @output
    def restart(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not ctx.docker.connected():
            raise GContainerException(ErrorConstants.DOCKER_NOT_CONNECTED)

        if not ctx.docker.is_running(service_name):
            raise GContainerException(ErrorConstants.SERVICE_IS_NOT_RUNNING, service_name)

        result = Service._stop(ctx, service_name)
        if result:
            Service._start(ctx, service_name)

    @output
    def enable(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        deploy_info = ctx.deploy.info(service_name)
        if deploy_info:
            ctx.deploy.set_enabled(service_name, True)

            # Defer enabling if no deployment is present. Then deploy will implictly enable
            if deploy_info['deployment'] != '-':
                ctx.systemd.enable(service_name)

    @output
    def disable(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if ctx.deploy.info(service_name):
            ctx.deploy.set_enabled(service_name, False)
            ctx.systemd.disable(service_name)

    @formatter('status')
    @output
    def status(self, ctx, service_name):
        if not legal_name(service_name):
            raise GContainerException(ErrorConstants.ILLEGAL_SERVICE_NAME, service_name)

        if not ctx.deploy.exists(service_name):
            raise GContainerException(ErrorConstants.NO_SUCH_DEPLOY, service_name)

        if not ctx.docker.connected():
            raise GContainerException(ErrorConstants.DOCKER_NOT_CONNECTED)

        deploy_dirs = ctx.fs.info_deploy(service_name)
        current_config = ctx.fs.current_config(service_name)

        deploy_info = ctx.deploy.info(service_name)
        docker_status = ctx.docker.status(service_name)

        res = {'name': service_name,
               'config_location': deploy_dirs['config'],
               'log_location': deploy_dirs['log'],
               'script_location': deploy_dirs['script'],
               'running': deploy_info['running'],
               'enabled': deploy_info['enabled'],
               'deployment': deploy_info['deployment'],
               'config': current_config,
               'container_status': docker_status,
               }

        if 'callback_uri' in deploy_info:
            res['callback_uri'] = deploy_info['callback_uri']

        return res

    @formatter('list')
    @output
    def list(self, ctx):
        if not ctx.docker.connected():
            raise GContainerException(ErrorConstants.DOCKER_NOT_CONNECTED)

        services, count = ctx.deploy.load()

        for service in services:
            docker_status = ctx.docker.status(service)
            services[service]['container_status'] = docker_status
            services[service]['config'] = ctx.fs.current_config(service)

        return {"deploys": services}
