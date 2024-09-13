import datetime
import os

import jwt
import requests


class OAuthToken:
    _access_token = os.getenv('OAUTH_ACCESS_TOKEN')
    _refresh_token = os.getenv('OAUTH_REFRESH_TOKEN')
    _verify_ssl = os.getenv('VRE_API_VERIFY_SSL', 'true').lower() != 'false'

    @classmethod
    def _load_tokens_from_env(cls):
        cls._access_token = os.getenv('OAUTH_ACCESS_TOKEN')
        cls._refresh_token = os.getenv('OAUTH_REFRESH_TOKEN')

    @classmethod
    def _parse_token(cls, token):
        return jwt.decode(token, options={"verify_signature": False})

    @classmethod
    def _token_needs_renewal(cls, token, delay=30):
        """ Check whether a token needs to be renewed

        Renewal is needed if token is already expired, or will expire within
        the next `delay` seconds.
        """
        exp = cls._parse_token(token).get('exp')
        now = datetime.datetime.now().timestamp()
        return now + delay > exp

    @classmethod
    def _get_token_endpoint(cls):
        # download openid-configuration
        refresh_token = cls._parse_token(cls._refresh_token)
        r = requests.get(
            f'{refresh_token.get("iss")}/.well-known/openid-configuration',
            verify=cls._verify_ssl,
            )
        r.raise_for_status()
        openid_configuration = r.json()
        # get token endpoint
        return openid_configuration['token_endpoint']

    @classmethod
    def _renew_tokens(cls):
        r = requests.post(
            cls._get_token_endpoint(),
            data={
                'client_id': 'naavre',
                'grant_type': 'refresh_token',
                'refresh_token': cls._refresh_token,
                },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
                },
            verify=cls._verify_ssl,
            )
        r.raise_for_status()
        new_tokens = r.json()
        cls._access_token = new_tokens['access_token']
        cls._refresh_token = new_tokens['refresh_token']

    @classmethod
    def get_access_token(cls):
        cls._load_tokens_from_env()
        if cls._token_needs_renewal(cls._access_token):
            cls._renew_tokens()
        return cls._access_token
