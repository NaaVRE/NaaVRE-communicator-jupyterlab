from urllib.parse import urlparse
import json
import logging
import os

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import jwt
import requests
import tornado

from .utils.oauth_token import OAuthToken

logger = logging.getLogger()


class ExternalServiceHandler(APIHandler):

    @property
    def _vre_api_verify_ssl(self):
        return os.getenv('VRE_API_VERIFY_SSL', 'true').lower() != 'false'

    @staticmethod
    def domain_is_allowed(url):
        """ Verify that the URL domain is allowed

        Allowed domains are set as a comma-separated list through environment
        variable NAAVRE_ALLOWED_DOMAINS. Eg:

        NAAVRE_ALLOWED_DOMAINS="my-domain.tld"
        NAAVRE_ALLOWED_DOMAINS="my-domain.tld,my-other-domain.tld"
        NAAVRE_ALLOWED_DOMAINS="*"
        """
        allowed_domains = os.getenv('NAAVRE_ALLOWED_DOMAINS').split(',')
        if '*' in allowed_domains:
            return True
        else:
            domain = urlparse(url).netloc
            return domain in allowed_domains

    @staticmethod
    def add_auth(headers):
        """ Add OAuth token to http headers """
        token = OAuthToken.get_access_token()
        headers['Authorization'] = f'Bearer {token}'

    @tornado.web.authenticated
    def post(self):
        payload = self.get_json_body()

        try:
            query = payload['query']
        except KeyError:
            raise tornado.web.HTTPError(400, 'No query in payload')

        try:
            method = query['method']
        except KeyError:
            raise tornado.web.HTTPError(400, 'No method in query')

        try:
            url = query['url']
        except KeyError:
            raise tornado.web.HTTPError(400, 'No url in query')

        headers = query.get('headers', {})
        data = query.get('data', {})

        if not self.domain_is_allowed(url):
            raise tornado.web.HTTPError(400, 'Domain is not allowed')

        try:
            self.add_auth(headers)
        except jwt.exceptions.DecodeError:
            raise tornado.web.HTTPError(500, 'Could not decode JWT')

        req = requests.request(
            method,
            url,
            headers=headers,
            data=data,
            verify=self._vre_api_verify_ssl,
            )

        self.finish(json.dumps({
            'status_code': req.status_code,
            'reason': req.reason,
            'headers': dict(req.headers),
            'content': req.text,
            }))


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    handlers = [
        (url_path_join(base_url, "naavre-communicator", "external-service"), ExternalServiceHandler),
        ]

    web_app.add_handlers(host_pattern, handlers)
