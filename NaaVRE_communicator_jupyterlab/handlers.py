from urllib.parse import urlparse
import json
import os
import random
import string

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import httpx
import jwt
import tornado

from .utils.oauth_token import OAuthToken


class ExternalServiceHandler(APIHandler):

    @property
    def _vre_api_verify_ssl(self):
        return os.getenv('VRE_API_VERIFY_SSL', 'true').lower() != 'false'

    @property
    def _naavre_log_queries(self):
        return os.getenv('NAAVRE_LOG_QUERIES', 'false').lower() == 'true'

    def domain_is_allowed(self, url):
        """ Verify that the URL domain is allowed

        Allowed domains are set as a comma-separated list through environment
        variable NAAVRE_ALLOWED_DOMAINS. Eg:

        NAAVRE_ALLOWED_DOMAINS="my-domain.tld"
        NAAVRE_ALLOWED_DOMAINS="my-domain.tld,my-other-domain.tld"
        NAAVRE_ALLOWED_DOMAINS="*"
        """
        allowed_domains = os.getenv('NAAVRE_ALLOWED_DOMAINS')
        if allowed_domains is None:
            msg = (
                'Environment variable NAAVRE_ALLOWED_DOMAINS is not set. '
                'No requests will be allowed. '
                )
            self.log.warning(msg)
            return False
        allowed_domains = allowed_domains.split(',')
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

    @staticmethod
    def _generate_log_id():
        return ''.join(random.sample(string.ascii_lowercase + string.ascii_uppercase, 10))

    def _get_query_logger(self):
        if self._naavre_log_queries:
            log_id = self._generate_log_id()
            def logger(msg, data):
                self.log.info(f'NaaVRE-communicator {log_id} {msg} {json.dumps(data)}')
        else:
            def logger(msg, data):
                pass
        return logger

    @tornado.web.authenticated
    async def post(self):
        payload = self.get_json_body()

        query_logger = self._get_query_logger()
        query_logger('query', payload)

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
            raise tornado.web.HTTPError(401, 'Could not decode JWT')

        async with httpx.AsyncClient(timeout=None, verify=self._vre_api_verify_ssl) as client:
            req = await client.request(
                method,
                url,
                headers=headers,
                json=data,
                )

        response = json.dumps({
            'status_code': req.status_code,
            'reason': req.reason_phrase,
            'headers': dict(req.headers),
            'content': req.text,
            })

        query_logger('response', response)

        await self.finish(response)

class MeHandler(APIHandler):
    @tornado.web.authenticated
    async def get(self):
        return self.finish(json.dumps(OAuthToken.get_user_info()))


def setup_handlers(web_app):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]
    handlers = [
        (url_path_join(base_url, "naavre-communicator", "external-service"), ExternalServiceHandler),
        (url_path_join(base_url, "naavre-communicator", "me"), MeHandler),
        ]

    web_app.add_handlers(host_pattern, handlers)
