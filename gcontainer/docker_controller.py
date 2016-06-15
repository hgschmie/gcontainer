import json
import click
import urllib3.contrib.pyopenssl

from docker import Client
from docker.utils.utils import parse_repository_tag, create_host_config

from .error import GContainerException, ErrorConstants


class Docker:
    """Docker specific container code. Future other container implementations should be able to
    get away with implemnting what is present in this file and call it a day.

    Docker is nice because they have an officially supported Python API that works well.
    """

    def __init__(self, ctx):
        self.docker_socket = ctx.config.get('docker', 'socket')
        self.ctx = ctx
        self.cli = Client(base_url=self.docker_socket,
                          version='auto')

        urllib3.contrib.pyopenssl.inject_into_urllib3()

    def _parse_deploy_id(self, deploy_id):
        """Read a full deploy uri with tag and split into repository reference and tag."""

        (repo, tag) = parse_repository_tag(deploy_id)
        disable_latest_tag = self.ctx.config.get('docker', 'disable_latest_tag') == 'True'
        if (tag is None or tag == 'latest') and disable_latest_tag:
            raise GContainerException(ErrorConstants.LATEST_TAG_DISABLED)

        return repo, tag

    def _host_config(self, service_name):
        """Returns a host configuration object for use with docker commands.

        This is mostly the network mode and the binding to the folders on the file system.
        """

        res = self.ctx.fs.info_deploy(service_name)
        binds = {
            res['log']: {
                'bind': '/data/log',
                'ro': False,
                },
            res['config']: {
                'bind': '/data/config',
                'ro': True
            }
        }

        return create_host_config(binds=binds, network_mode='host')

    def _info(self, service_name):
        """Inspect a docker container through the API and return its current state."""

        container_name = "/%s" % service_name
        containers = self.cli.containers(all=True)
        for container in containers:
            names = container.get('Names')
            if container_name in names:
                return self.cli.inspect_container(service_name)

        return None

    def connected(self):
        """Returns true if the API is connected to the docker daemon."""

        try:
            self.cli.ping()
            return True
        except Exception:
            return False

    def is_running(self, service_name):
        """Returns true if the docker container for the given service name is running."""

        container_info = self._info(service_name)
        if container_info:
            return container_info['State']['Running']
        return False

    def status(self, service_name):
        """Returns a somewhat sanitized status dict for a given service."""

        status = {}
        container_info = self._info(service_name)
        if container_info:
            status = {
                'running': container_info['State']['Running'],
                'id': container_info['Id'],
                'environment': container_info['Config']['Env'],
                'image': container_info['Config']['Image'],
                'created': container_info['Created'],
                'started': container_info['State']['StartedAt'],
                }

            if not status['running']:
                status['finished'] = container_info['State']['FinishedAt']

        return status

    def pull_image(self, deploy_id):
        """Pull an image referenced by the deploy_id from a repo server and make it available for local deploy."""

        (repo, tag) = self._parse_deploy_id(deploy_id)

        msg = []
        errors = []
        allow_insecure_registry = self.ctx.config.get('docker', 'allow_insecure_registry') == 'True'
        for line in self.cli.pull(repository=repo,
                                  tag=tag,
                                  stream=True,
                                  insecure_registry=allow_insecure_registry):
            fields = json.loads(line)
            if 'status' in fields:
                msg.append(fields['status'])

            if 'error' in fields:
                errors.append(fields['error'])

            if self.ctx.raw:
                click.echo(json.dumps(fields, indent=2))

        if errors:
            raise GContainerException(ErrorConstants.IMAGE_NOT_AVAILABLE, deploy_id, errors)
        return msg

    def create_container(self, service_name, deploy_id, destroy_existing=True, environment={}):
        """Create a new container instance for the given container. If necessary, destroy an
        existing container for the same service."""

        if destroy_existing:
            self.destroy_container(service_name)

        self.cli.create_container(image=deploy_id,
                                  name=service_name,
                                  environment=environment,
                                  host_config=self._host_config(service_name))

    def destroy_container(self, service_name):
        """Remove an existing container for the given service name."""

        container_info = self._info(service_name)
        if container_info:
            self.cli.remove_container(service_name)

    def start(self, service_name):
        """Start a container for the given service name. The container must be created first."""

        container_info = self._info(service_name)
        if container_info:
            self.cli.start(service_name)

    def stop(self, service_name):
        """Stop a container for the given serivce name if it exists and is running."""
        container_info = self._info(service_name)

        result = False
        if container_info:
            self.cli.stop(service_name)
            result = container_info['State']['Running']

        return result

    def wait(self, service_name):
        """Wait for a container with the given service name to terminate. This is a blocking call
        that can be used e.g. by systemd to wait for a container to terminate."""

        container_info = self._info(service_name)
        if container_info:
            self.cli.wait(service_name)
