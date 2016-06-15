import requests
from requests.exceptions import RequestException


class Callback:
    """ Provides HTTP callbacks for notification. """

    def __init__(self, ctx):
        self.ctx = ctx
        self.connect_timeout = self.ctx.config.get('callback', 'connect_timeout')
        self.read_timeout = self.ctx.config.get('callback', 'read_timeout')
        self.ignore_callbacks = self.ctx.config.get('callback', 'ignore_callbacks') == 'true'

    def running(self, uri, **payload):
        """ Hit the 'running' endpoint to report service being up."""

        self._post(uri, 'running', payload)

    def stopped(self, uri, **payload):
        """ Hit the 'stopped' endpoint to report service being down."""

        self._post(uri, 'stopped', payload)

    def _post(self, uri, endpoint, payload):
        """Actual code to perform the callbacks."""

        if self.ignore_callbacks:
            return

        if not uri[-1] == '/':
            uri += '/'

        uri += endpoint

        try:
            requests.post(uri,
                          data=payload,
                          timeout=(float(self.connect_timeout), float(self.read_timeout)))
        except RequestException:
            pass  # do nothing, if the hook fails, so be it
